"""Minerva Archive source — NEW API (post-Myrient shutdown March 2026)

Minerva now uses a SQLite database (hashes.db) with per-file torrents.
We query the directory listing API to find files, then construct magnet links
or download individual torrent files.

Directory structure: https://minerva-archive.org/browse/{collection}/{subcollection}/
ROM page: https://minerva-archive.org/rom/?name={encoded_path}
Torrent: /assets/{rom.torrents}
Magnet: rom.magnet + trackers + so={rom.so_id}
"""
import os, re, urllib.parse
from urllib.parse import quote

from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_req

MINERVA_BASE = "https://minerva-archive.org"

# Mapping from platform keys to Minerva directory paths
PLATFORM_DIRS = {
    "switch": "No-Intro/Nintendo - Nintendo Switch",
    "wiiu": "Redump/Nintendo - Wii U - WUX",
    "wii": "Redump/Nintendo - Wii - NKit RVZ [zstd-19-128k]",
    "gc": "Redump/Nintendo - GameCube - NKit RVZ [zstd-19-128k]",
    "3ds": "No-Intro/Nintendo - Nintendo 3DS (Decrypted)",
    "ds": "No-Intro/Nintendo - Nintendo DS (Decrypted)",
    "gba": "No-Intro/Nintendo - Game Boy Advance",
    "n64": "No-Intro/Nintendo - Nintendo 64 (BigEndian)",
    "snes": "No-Intro/Nintendo - Super Nintendo Entertainment System",
    "nes": "No-Intro/Nintendo - Nintendo Entertainment System (Headered)",
    "ps4": "Redump/Sony - PlayStation 4",
    "ps3": "Redump/Sony - PlayStation 3",
    "ps2": "Redump/Sony - PlayStation 2",
    "ps1": "Redump/Sony - PlayStation",
    "psp": "Redump/Sony - PlayStation Portable",
    "xbox360": "Redump/Microsoft - Xbox 360",
    "xbox": "Redump/Microsoft - Xbox",
    "dc": "Redump/Sega - Dreamcast",
    "genesis": "No-Intro/Sega - Mega Drive - Genesis",
}

# Legacy collections kept for backward compatibility
PLATFORM_COLLECTIONS = PLATFORM_DIRS.copy()


class MinervaSource:
    """Minerva Archive source — directory listing + per-file torrents"""

    def __init__(self, download_dir, aria2c_path="aria2c.exe"):
        self.download_dir = download_dir
        self.aria2c_path = aria2c_path
        self._page_cache = {}
        self._file_cache = {}  # platform -> [(name, path, size), ...]

    def get_platform_dir(self, platform):
        return PLATFORM_DIRS.get(platform)

    def get_torrent_url(self, platform):
        """Legacy method — returns None since old collection torrents are gone"""
        return None

    def fetch_torrent(self, platform):
        """Legacy method — returns None since old collection torrents are gone"""
        return None

    def _fetch_page(self, url):
        if url in self._page_cache:
            return self._page_cache[url]
        try:
            r = cffi_req.get(url, impersonate="chrome", timeout=30)
            if r.status_code != 200:
                return None
            self._page_cache[url] = r.text
            return r.text
        except Exception:
            return None

    def list_files(self, platform):
        """List files in a Minerva collection by scraping directory listing"""
        if platform in self._file_cache:
            return self._file_cache[platform]

        dir_path = self.get_platform_dir(platform)
        if not dir_path:
            return []

        url = f"{MINERVA_BASE}/browse/{dir_path}/"
        html = self._fetch_page(url)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        entries = []

        for a in soup.find_all("a", href=re.compile(r"^/rom\?name=")):
            href = a.get("href", "")
            name = a.get_text(strip=True)
            if name and len(name) > 2:
                # Decode the path from the href
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                file_path = parsed.get("name", [""])[0]
                entries.append((name, file_path, 0))

        self._file_cache[platform] = entries
        return entries

    def find_file(self, game_name, platform, extensions=None):
        """Find a file in a Minerva collection by game name"""
        files = self.list_files(platform)
        if not files:
            return None, None

        search = game_name.lower().replace(" ", "").replace("-", "").replace("_", "")
        for name, path, size in files:
            name_norm = name.lower().replace(" ", "").replace("-", "").replace("_", "")
            if search in name_norm or name_norm in search:
                if extensions:
                    ext = os.path.splitext(path)[1].lower()
                    if ext not in extensions:
                        continue
                return name, path

        return None, None

    def get_rom_page_url(self, file_path):
        """Get the ROM page URL for a file"""
        encoded = quote(file_path, safe="")
        return f"{MINERVA_BASE}/rom/?name={encoded}"

    def parse_torrent_files(self, torrent_data):
        """Legacy method — kept for backward compatibility"""
        from .minerva_legacy import bdecode
        t, _ = bdecode(torrent_data)
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

    def download_file(self, torrent_data, file_path, output_dir):
        """Legacy method — kept for backward compatibility"""
        import subprocess, tempfile
        tmp = tempfile.NamedTemporaryFile(suffix='.torrent', delete=False)
        tmp.write(torrent_data)
        tmp.close()
        os.makedirs(output_dir, exist_ok=True)
        cmd = [self.aria2c_path, '--dir', output_dir, '--select-file', file_path, tmp.name]
        subprocess.run(cmd, capture_output=True)
        os.unlink(tmp.name)
