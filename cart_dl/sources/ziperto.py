from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

ZIPERTO_BASE = "https://www.ziperto.com"
CATEGORIES = {
    "switch": f"{ZIPERTO_BASE}/category/nintendo-switch-nsp/",
}

def discover_games(platform="switch", max_pages=5):
    """Scrape Ziperto category pages for game URLs"""
    games = {}
    base = CATEGORIES.get(platform, "")
    if not base:
        return games

    for page in range(1, max_pages + 1):
        url = f"{base}/page/{page}/" if page > 1 else base
        try:
            r = requests.get(url, impersonate="chrome", timeout=15)
            if r.status_code != 200:
                break
            soup = BeautifulSoup(r.content, "html.parser")
            articles = soup.find_all("article") or soup.find_all("div", class_="post")
            if not articles:
                break
            for article in articles:
                link = article.find("a", href=True)
                if not link:
                    continue
                href = link["href"]
                if "/category/" in href or "/page/" in href:
                    continue
                if not href.startswith("http"):
                    href = urljoin(ZIPERTO_BASE, href)
                title = link.get_text(strip=True) or article.get_text(strip=True)[:100]
                games[href] = {"title": title, "platform": platform}
        except Exception:
            break
    return games


def parse_download_links(game_url):
    """Extract download links from a Ziperto game page"""
    links = {"base_game_nsp": [], "update": [], "dlc": [], "base_game_xci": []}
    try:
        r = requests.get(game_url, impersonate="chrome", timeout=15)
        soup = BeautifulSoup(r.content, "html.parser")
        entry = soup.find("div", class_="entry-content") or soup.find("article")
        if not entry:
            return links

        for a in entry.find_all("a", href=True):
            href = a["href"]
            if any(s in href.lower() for s in ["twitter", "facebook", "#comment", "javascript"]):
                continue
            text = a.get_text(strip=True).lower()
            url_lower = href.lower()
            dl_key = "base_game_nsp"
            if "dlc" in url_lower or "dlc" in text:
                dl_key = "dlc"
            elif "update" in url_lower or "update" in text:
                dl_key = "update"
            elif "xci" in url_lower or "xci" in text:
                dl_key = "base_game_xci"

            site = None
            for s in ["1fichier", "frdl", "gofile", "datanodes", "hexload", "hexupload", "megaup", "mixdrop", "mediafire"]:
                if s in url_lower:
                    site = s.title().replace("Fichier", "Fichier").replace("Frdl", "FreeDL").replace("Gofile", "GoFile").replace("Datanodes", "DataNodes").replace("Megaup", "MegaUp").replace("Mixdrop", "MixDrop").replace("Mediafire", "MediaFire")
                    break
            if site:
                found = False
                for entry_info in links[dl_key]:
                    if site in entry_info:
                        entry_info[site].append(href)
                        found = True
                if not found:
                    links[dl_key].append({site: [href], "full_name": dl_key.replace("_", " ").title()})
    except Exception:
        pass
    return links
