import os, sys, json, time, webbrowser, threading, re, unicodedata
from pathlib import Path
from urllib.parse import quote, unquote

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse

from .util.io_tools import load_yml, save_yml
from .util.html_tools import get_game_dict
from .util.igdb_tools import IGDBClient, filter_game_dict, DEFAULT_MIN_RATING
from .scraper.scraper import CartDL

app = FastAPI(title="cart-dl", version="0.9.0")

# Prefer config from exe directory, fall back to cwd
_exe_dir = os.path.dirname(os.path.abspath(sys.executable)) if getattr(sys, 'frozen', False) else os.getcwd()
CONFIG_FILE = os.path.join(_exe_dir, "config.yml")
if not os.path.exists(CONFIG_FILE):
    CONFIG_FILE = os.path.join(os.getcwd(), "config.yml")
MOD_DIR = os.path.dirname(__file__)

general_config = load_yml(os.path.join(MOD_DIR, "configs", "general.yml"))
regex_config = load_yml(os.path.join(MOD_DIR, "configs", "regex.yml"))
platforms_config = load_yml(os.path.join(MOD_DIR, "configs", "platforms.yml"))
ALL_PLATFORMS = platforms_config.get("platforms", {})
MINERVA_BASE = platforms_config.get("minerva_base", "https://minerva-archive.org")
MINERVA_ASSETS = platforms_config.get("minerva_assets", f"{MINERVA_BASE}/assets/Minerva_Myrient_v0.3")

IGDBClient.load_precache()

_game_dict = None
_games_cache = {}  # platform -> cache list
_download_state = {"running": False, "current": 0, "total": 0, "game": "", "log": []}
_server_start_time = time.time()
_minerva_file_cache = {}  # platform -> [(name, path, size), ...]
_archive_file_cache = {}  # platform -> [(name, path, size, identifier), ...]
_minerva_ready = False


def get_user_config():
    if os.path.exists(CONFIG_FILE):
        return load_yml(CONFIG_FILE)
    return {}


def save_user_config(config):
    save_yml(CONFIG_FILE, config)


@app.get("/", response_class=HTMLResponse)
async def index():
    template = Path(os.path.join(MOD_DIR, "templates", "index.html"))
    if template.exists():
        return template.read_text(encoding="utf-8")
    return HTMLResponse("<h1>cart-dl server running</h1>")


def _normalize_name(name):
    """Normalize game name for dedup comparison"""
    n = name.replace('\u2122', '').replace('\u00AE', '')
    n = unicodedata.normalize('NFKD', n)
    n = n.encode('ascii', 'ignore').decode('ascii')
    n = n.lower().strip()
    n = re.sub(r'[^\w\s]', '', n)
    n = re.sub(r'\s+(switch\s+download|switch\s+download\s+\w*|download\s+guide|nintendo\s+switch\s+\w*|rom(\s+nsp\s+xci)?|nsp\s+xci|update\s+\+?\s*dlc)\b.*', '', n)
    n = re.sub(r'\s+', ' ', n)
    return n.strip()


def _preload_sources(platforms=None):
    """Pre-parse Minerva directory listings and IA file listings for specific platforms"""
    global _minerva_file_cache, _archive_file_cache, _minerva_ready
    from .sources.archive import ArchiveSource
    from .sources.minerva import MinervaSource

    if platforms is None:
        platforms = list(ALL_PLATFORMS.keys())

    ia = ArchiveSource(download_dir=".")
    ms = MinervaSource(download_dir=".")

    for platform_key in platforms:
        platform_data = ALL_PLATFORMS.get(platform_key, {})

        # Minerva directory listing (new API — no more collection torrents)
        if platform_key not in _minerva_file_cache:
            try:
                files = ms.list_files(platform_key)
                if files:
                    _minerva_file_cache[platform_key] = files
            except Exception:
                pass

        # Internet Archive collections
        if platform_key not in _archive_file_cache:
            archive_sources = platform_data.get("sources", {}).get("archive", [])
            for src in archive_sources:
                if src.get("name") != "ia":
                    continue
                identifier = src.get("identifier", "")
                if not identifier:
                    continue
                try:
                    files = ia.list_files(identifier)
                    if not files:
                        continue
                    entries = []
                    for name, path, size in files:
                        entries.append((name.strip(), path, size, identifier))
                    _archive_file_cache[platform_key] = entries
                except Exception:
                    pass

    _minerva_ready = True


def _bdecode(data, idx=0):
    """Minimal bencode decoder for .torrent files"""
    if data[idx:idx+1] == b'd':
        idx += 1; d = {}
        while data[idx:idx+1] != b'e':
            k, idx = _bdecode(data, idx)
            v, idx = _bdecode(data, idx)
            d[k] = v
        return d, idx + 1
    elif data[idx:idx+1] == b'l':
        idx += 1; lst = []
        while data[idx:idx+1] != b'e':
            v, idx = _bdecode(data, idx); lst.append(v)
        return lst, idx + 1
    elif data[idx:idx+1] == b'i':
        end = data.index(b'e', idx)
        return int(data[idx+1:end]), end + 1
    else:
        colon = data.index(b':', idx)
        n = int(data[idx:colon])
        start = colon + 1
        return data[start:start+n], start + n


def _parse_torrent_files(torrent_data):
    """Parse file list from torrent data, skip .pad files"""
    t, _ = _bdecode(torrent_data)
    info = t.get(b'info', {})
    files = []
    if b'files' in info:
        for f in info[b'files']:
            path = b'/'.join(f[b'path']).decode('utf-8', errors='replace')
            size = f.get(b'length', 0)
            if path.startswith('.pad/'):
                continue
            files.append((path, size))
    else:
        name = info.get(b'name', b'').decode('utf-8', errors='replace')
        size = info.get(b'length', 0)
        files.append((name, size))
    return files


def _build_platform_cache(platform_key):
    """Build game cache for a specific platform"""
    global _game_dict, _games_cache, _minerva_file_cache
    platform_data = ALL_PLATFORMS.get(platform_key)
    if not platform_data:
        return []

    entries = []

    # For Switch, use the existing HTTP scraping system
    if platform_key == "switch":
        cfg = get_user_config()
        source_url = cfg.get("source_url", "https://nxbrew.net")
        primary_domain = source_url.split("//")[-1].split("/")[0]
        if _game_dict is None:
            _game_dict = get_game_dict(general_config, regex_config, source_url)
        igdb = IGDBClient(
            client_id=cfg.get("igdb_client_id") or None,
            client_secret=cfg.get("igdb_client_secret") or None,
        )
        filtered = filter_game_dict(_game_dict.copy(), igdb, {
            "igdb_min_rating": cfg.get("igdb_min_rating", DEFAULT_MIN_RATING),
            "igdb_exclude_vn": cfg.get("igdb_exclude_vn", True),
            "igdb_exclude_shovelware": cfg.get("igdb_exclude_shovelware", True),
            "igdb_switch_only": cfg.get("igdb_switch_only", True),
            "igdb_exclude_multi_platform": cfg.get("igdb_exclude_multi_platform", False),
        })
        dedup = {}
        for url, info in filtered.items():
            name = info.get("short_name", info.get("long_name", ""))
            norm = _normalize_name(name)
            entry = {
                "name": name,
                "search_name": _normalize_name(name),
                "long_name": info.get("long_name", ""),
                "url": url,
                "rating": info.get("igdb_rating"),
                "has_nsp": info.get("has_nsp", False),
                "has_xci": info.get("has_xci", False),
                "has_update": info.get("has_update", False),
                "has_dlc": info.get("has_dlc", False),
                "igdb_match": info.get("igdb_match", False),
                "other_platforms": info.get("igdb_other_platforms", []),
                "platform": "switch",
                "alt_urls": [],
            }
            if norm not in dedup:
                dedup[norm] = entry
            else:
                existing = dedup[norm]
                existing["alt_urls"].append(url)
                existing_is_primary = primary_domain in existing["url"]
                new_is_primary = primary_domain in url
                if new_is_primary and not existing_is_primary:
                    existing["alt_urls"].append(existing["url"])
                    existing["url"] = url
                    existing["name"] = name
                    existing["long_name"] = info.get("long_name", "")
                elif not existing_is_primary and not new_is_primary:
                    if info.get("igdb_match") and not existing.get("igdb_match"):
                        existing["alt_urls"].append(existing["url"])
                        existing["url"] = url
                        existing["name"] = name
                        existing["long_name"] = info.get("long_name", "")
        entries = list(dedup.values())
    else:
        # For non-Switch platforms, merge Minerva + IA file listings
        # Prefer compressed formats (lower index = better)
        preferred = [e.lower() for e in platform_data.get("preferred_extensions", [])]
        all_exts = [e.lower() for e in platform_data.get("extensions", [])]
        # Minerva distributes everything as .zip — add it as valid extension
        minerva_exts = all_exts + [".zip"]
        seen = {}
        candidates = {}  # norm -> {ext: (name, path, size, source, identifier)}

        # Helper: score an extension (lower = better)
        def ext_score(ext):
            ext = ext.lower()
            try:
                return preferred.index(ext)
            except ValueError:
                try:
                    return len(preferred) + all_exts.index(ext)
                except ValueError:
                    return 999

        # Process Minerva files
        for name, path, size in _minerva_file_cache.get(platform_key, []):
            norm = _normalize_name(name)
            if not norm:
                continue
            ext = os.path.splitext(path)[1].lower()
            if ext not in minerva_exts:
                continue
            if norm not in candidates:
                candidates[norm] = {}
            es = ext_score(ext)
            if ext not in candidates[norm] or es < ext_score(candidates[norm].get("_best_ext", "")):
                candidates[norm][ext] = (name, path, size, "minerva", None)
                candidates[norm]["_best_ext"] = ext

        # Process IA files
        for name, path, size, identifier in _archive_file_cache.get(platform_key, []):
            norm = _normalize_name(name)
            if not norm:
                continue
            ext = os.path.splitext(path)[1].lower()
            if ext not in all_exts:
                continue
            if norm not in candidates:
                candidates[norm] = {}
            es = ext_score(ext)
            if ext not in candidates[norm] or es < ext_score(candidates[norm].get("_best_ext", "")):
                candidates[norm][ext] = (name, path, size, "archive", identifier)
                candidates[norm]["_best_ext"] = ext

        # Build entries: pick best format per game
        for norm, cands in candidates.items():
            best_ext = cands.pop("_best_ext", None)
            if best_ext and best_ext in cands:
                name, path, size, source, identifier = cands[best_ext]
                ext = os.path.splitext(path)[1].lower()
                if source == "minerva":
                    url = f"minerva:{platform_key}:{quote(path)}"
                else:
                    url = f"archive:{platform_key}:{identifier}:{quote(path)}"
                entry = {
                    "name": name,
                    "search_name": _normalize_name(name),
                    "long_name": path,
                    "url": url,
                    "rating": None,
                    "has_nsp": False,
                    "has_xci": False,
                    "has_base": ext in all_exts,
                    "has_update": False,
                    "has_dlc": False,
                    "igdb_match": False,
                    "other_platforms": [],
                    "platform": platform_key,
                    "alt_urls": [],
                    "minerva_path": path if source == "minerva" else None,
                    "minerva_size": size,
                }
                entries.append(entry)
    entries.sort(key=lambda g: g["rating"] or 0, reverse=True)
    return entries


def _build_game_cache():
    """Build the sorted game cache for ALL platforms (Switch primary)"""
    global _games_cache
    # Lazy load: only preload sources for platforms not yet cached
    uncached = [pk for pk in ALL_PLATFORMS if pk not in _games_cache]
    if uncached:
        _preload_sources(uncached)
    for platform_key in uncached:
        if platform_key not in _games_cache:
            _games_cache[platform_key] = _build_platform_cache(platform_key)


@app.get("/api/games")
async def api_games(request: Request, offset: int = 0, limit: int = 100, sort: str = "rating", order: str = "desc"):
    """Paginated game list. Builds cache on first call. Supports ?platform= filter."""
    global _games_cache
    if not _games_cache:
        _build_game_cache()

    # Platform filter: comma-separated list, default to all
    platform_filter = request.query_params.get("platform", "")
    if platform_filter:
        requested = set(p.strip() for p in platform_filter.split(",") if p.strip() in ALL_PLATFORMS)
    else:
        requested = set(ALL_PLATFORMS.keys())

    # Merge games from requested platforms
    games = []
    for pk in requested:
        if pk in _games_cache:
            games.extend(_games_cache[pk])

    # Server-side search
    q = request.query_params.get("q", "").lower()
    if q:
        games = [g for g in games if q in g.get("search_name", g["name"].lower()) or q in g.get("long_name", "").lower()]

    # Sort
    reverse = order == "desc"
    if sort == "name":
        games = sorted(games, key=lambda g: g["name"].lower(), reverse=reverse)
    elif sort == "rating":
        games = sorted(games, key=lambda g: g["rating"] or 0, reverse=reverse)

    total = len(games)
    page = games[offset:offset + limit]

    return JSONResponse({"total": total, "offset": offset, "limit": limit, "games": page})


@app.get("/api/platforms")
async def api_platforms():
    """Return available platforms with game counts"""
    global _games_cache
    if not _games_cache:
        _build_game_cache()
    platforms = []
    for pk, pdata in ALL_PLATFORMS.items():
        platforms.append({
            "key": pk,
            "display": pdata.get("display", pk),
            "count": len(_games_cache.get(pk, [])),
            "download_methods": pdata.get("download_methods", []),
        })
    return JSONResponse({"platforms": platforms, "minerva_ready": _minerva_ready})


@app.post("/api/games/refresh")
async def api_refresh(request: Request):
    global _game_dict, _games_cache, _minerva_file_cache, _archive_file_cache, _minerva_ready

    async def generate():
        global _game_dict, _games_cache, _minerva_file_cache, _archive_file_cache, _minerva_ready
        yield {"event": "status", "data": "scraping"}
        _game_dict = get_game_dict(general_config, regex_config, get_user_config().get("source_url", "https://nxbrew.net"))
        yield {"event": "status", "data": json.dumps({"scraped": len(_game_dict)})}
        yield {"event": "status", "data": "minerva"}
        _minerva_file_cache = {}
        _archive_file_cache = {}
        _minerva_ready = False
        _preload_sources()  # Full reload on explicit refresh
        yield {"event": "status", "data": "enriching"}
        IGDBClient.load_precache()
        _games_cache = {}  # force rebuild of all platform caches
        yield {"event": "status", "data": "done"}

    return EventSourceResponse(generate())


@app.post("/api/download")
async def api_download(request: Request):
    global _download_state
    body = await request.json()
    game_urls = body.get("games", [])
    if not game_urls:
        raise HTTPException(400, "No games specified")
    if _download_state["running"]:
        if time.time() - _download_state.get("_started", 0) > 60:
            _download_state = {"running": False, "current": 0, "total": 0, "game": "", "log": []}
        else:
            raise HTTPException(409, "Download already in progress")

    _download_state = {"running": True, "current": 0, "total": len(game_urls), "game": "", "log": [], "_started": time.time()}
    cfg = get_user_config()

    def worker():
        global _download_state, _games_cache
        dead_hosts = set()
        shared_jd = None

        # Pre-connect JDownloader once (for HTTP-based downloads)
        try:
            import myjdapi
            jd = myjdapi.Myjdapi()
            jd.set_app_key("nxbrewdl")
            jd.connect(cfg["jd_user"], cfg["jd_pass"])
            shared_jd = jd.get_device(cfg["jd_device"])
            _download_state["log"].append("JD2: connected")
        except Exception as e:
            _download_state["log"].append(f"JD2: FAILED - {e}")

        for i, url in enumerate(game_urls):
            game_name = url.split("/")[-2].replace("-", " ").title() if not url.startswith("minerva:") else url.split(":")[-1].split("/")[-1]
            _download_state["log"].append(f"[{i+1}/{len(game_urls)}] {game_name}")
            _download_state["current"] = i + 1
            _download_state["game"] = game_name

            # Archive.org download path
            if url.startswith("archive:"):
                _download_state["log"].append(f"  IA download...")
                try:
                    parts = url.split(":", 3)  # archive:platform:identifier:path
                    platform_key = parts[1]
                    identifier = parts[2] if len(parts) > 2 else ""
                    file_path = unquote(parts[3]) if len(parts) > 3 else ""
                    from .sources.archive import ArchiveSource
                    a_src = ArchiveSource(download_dir=cfg.get("download_dir", "."))
                    out_dir = os.path.join(cfg.get("download_dir", "."), platform_key.upper())
                    rc = a_src.download_file(identifier, file_path, out_dir)
                    if rc == 0:
                        _download_state["log"].append(f"  IA download started: {os.path.basename(file_path)}")
                    else:
                        # Fallback to direct HTTP
                        result_path = a_src.download_file_direct(identifier, file_path, out_dir)
                        if result_path:
                            _download_state["log"].append(f"  IA direct OK: {os.path.basename(result_path)}")
                        else:
                            _download_state["log"].append(f"  IA FAIL (rc={rc})")
                except Exception as e:
                    _download_state["log"].append(f"  IA FAIL: {str(e)[:120]}")
                continue

            # Minerva download path (new API — per-file torrents)
            if url.startswith("minerva:"):
                _download_state["log"].append(f"  Minerva download...")
                try:
                    parts = url.split(":", 2)  # minerva:platform:path
                    platform_key = parts[1]
                    file_path = unquote(parts[2]) if len(parts) > 2 else ""
                    from .sources.minerva import MinervaSource
                    ms = MinervaSource(download_dir=cfg.get("download_dir", "."))
                    rom_url = ms.get_rom_page_url(file_path)
                    # Fetch ROM page to get magnet/torrent link
                    from curl_cffi import requests as cffi_req
                    r = cffi_req.get(rom_url, impersonate="chrome", timeout=30, allow_redirects=True)
                    if r.status_code == 200:
                        import re
                        # Extract magnet link from page
                        magnet_match = re.search(r'id="magnet"[^>]*href="([^"]+)"', r.text)
                        if magnet_match:
                            magnet_link = magnet_match.group(1)
                            out_dir = os.path.join(cfg.get("download_dir", "."), platform_key.upper())
                            os.makedirs(out_dir, exist_ok=True)
                            import subprocess
                            cmd = ["aria2c", "--dir", out_dir, "--seed-time=0", magnet_link]
                            result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
                            _download_state["log"].append(f"  aria2c magnet: {result.returncode}")
                        else:
                            _download_state["log"].append(f"  Minerva: no magnet link found")
                    else:
                        _download_state["log"].append(f"  Minerva: page fetch failed ({r.status_code})")
                except Exception as e:
                    _download_state["log"].append(f"  Minerva FAIL: {str(e)[:120]}")
                continue

            # HTTP download path (existing logic)
            # Find alt_urls from cache
            alt_urls = [url]
            if _games_cache:
                for pk in _games_cache:
                    for g in _games_cache[pk]:
                        if g["url"] == url and g.get("alt_urls"):
                            alt_urls.extend(g["alt_urls"])
                            break

            downloaded = False
            for alt_url in alt_urls:
                src = alt_url.split("/")[2] if "//" in alt_url else "?"
                try:
                    import threading as thr
                    result = {"ok": False, "error": "timeout"}
                    def run_dl():
                        try:
                            cfg_copy = dict(cfg)
                            cfg_copy["log_dir"] = None
                            nx = CartDL(to_download={game_name: alt_url}, user_config=cfg_copy,
                                       jd_device=shared_jd, dead_hosts=dead_hosts)
                            nx.run()
                            result["ok"] = True
                        except Exception as e:
                            result["error"] = str(e)[:120]
                    t = thr.Thread(target=run_dl, daemon=True)
                    t.start()
                    t.join(timeout=30)
                    if t.is_alive():
                        _download_state["log"].append(f"  TIMEOUT ({src})")
                    elif result["ok"]:
                        _download_state["log"].append(f"  OK ({src})")
                        downloaded = True
                        break
                    else:
                        _download_state["log"].append(f"  FAIL ({src}): {result['error']}")
                except Exception as e:
                    _download_state["log"].append(f"  FAIL ({src}): {str(e)[:120]}")
            if not downloaded:
                _download_state["log"].append(f"  ALL SOURCES FAILED")
        _download_state["running"] = False

    threading.Thread(target=worker, daemon=True).start()
    return JSONResponse({"status": "started", "total": len(game_urls)})


@app.get("/api/download/status")
async def api_download_status():
    return JSONResponse(_download_state)


@app.post("/api/download/reset")
async def api_download_reset():
    global _download_state
    _download_state = {"running": False, "current": 0, "total": 0, "game": "", "log": []}
    return JSONResponse({"status": "reset"})


@app.get("/api/config")
async def api_config():
    cfg = get_user_config()
    safe = {}
    for k, v in cfg.items():
        if any(s in k.lower() for s in ["pass", "secret", "token"]):
            safe[k] = "***" if v else ""
        else:
            safe[k] = v
    safe["has_jd"] = bool(cfg.get("jd_user") and cfg.get("jd_pass"))
    safe["has_igdb"] = bool(cfg.get("igdb_client_id") and cfg.get("igdb_client_secret"))
    return JSONResponse(safe)


@app.post("/api/config")
async def api_config_save(request: Request):
    body = await request.json()
    cfg = get_user_config()
    cfg.update(body)
    save_user_config(cfg)
    return JSONResponse({"status": "ok"})


@app.get("/api/health")
async def api_health():
    cfg = get_user_config()
    total_games = sum(len(v) for v in _games_cache.values()) if _games_cache else 0
    return JSONResponse({
        "status": "ok",
        "uptime": round(time.time() - _server_start_time),
        "games_loaded": total_games,
        "games_raw": len(_game_dict) if _game_dict else 0,
        "precache_size": len(IGDBClient._precache) if IGDBClient._precache else 0,
        "source_url": cfg.get("source_url", ""),
        "has_jd": bool(cfg.get("jd_user")),
        "minerva_ready": _minerva_ready,
        "platforms": len(ALL_PLATFORMS),
    })


def run_server(host="127.0.0.1", port=8765, open_browser=True):
    if open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(f"http://{host}:{port}")).start()
    uvicorn.run(app, host=host, port=port, log_level="warning")
