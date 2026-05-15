"""Vimm's Lair HTTP source for ROM listings"""
import os, re
from urllib.parse import quote

from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_req

VIMM_BASE = "https://vimm.net"

PLATFORM_MAP = {
    "ps3": "PS3",
    "ps2": "PS2",
    "ps1": "PlayStation",
    "psp": "PS Portable",
    "n64": "Nintendo 64",
    "snes": "Super Nintendo",
    "nes": "NES",
    "genesis": "Genesis",
    "dc": "Dreamcast",
    "gba": "Game Boy Adv",
    "ds": "Nintendo DS",
    "3ds": "Nintendo 3DS",
    "wii": "Wii",
    "gc": "GameCube",
    "xbox": "Xbox",
    "xbox360": "Xbox 360",
    "saturn": "Saturn",
}


class VimmSource:
    """Vimm's Lair scraper — Redump-synced vault with .7z downloads"""

    def __init__(self, download_dir="."):
        self.download_dir = download_dir
        self._page_cache = {}
        self._session = cffi_req.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })

    def get_platform_slug(self, platform_key):
        return PLATFORM_MAP.get(platform_key)

    def fetch_page(self, url):
        if url in self._page_cache:
            return self._page_cache[url]
        try:
            r = self._session.get(url, impersonate="chrome", timeout=30)
            if r.status_code != 200:
                return None
            self._page_cache[url] = r.text
            return r.text
        except Exception:
            return None

    def list_games(self, platform_key):
        """Fetch game list from Vimm's vault for a platform"""
        slug = self.get_platform_slug(platform_key)
        if not slug:
            return []

        vault_url = f"{VIMM_BASE}/vault/{slug}"
        html = self.fetch_page(vault_url)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        entries = []

        # Find all vault links: /vault/{numeric_id}
        for a in soup.find_all("a", href=re.compile(r"^/vault/\d+$")):
            href = a.get("href", "")
            name = a.get_text(strip=True)
            if name and len(name) > 2:
                url = f"{VIMM_BASE}{href}"
                entries.append((name, url))

        return entries

    def get_download_link(self, game_url):
        """Get the actual .7z download link from a Vimm game page
        
        Vimm uses a form-based download:
        1. Parse mediaId from hidden input
        2. Get form action URL
        3. Construct: https:{action}?mediaId={id}
        """
        html = self.fetch_page(game_url)
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")
        
        # Find mediaId hidden input
        media_id_input = soup.find("input", {"name": "mediaId"})
        if not media_id_input:
            return None
        media_id = media_id_input.get("value", "")

        # Find download form
        dl_form = soup.find("form", {"id": "dl_form"})
        if not dl_form:
            return None
        action = dl_form.get("action", "")

        if media_id and action:
            return f"https:{action}?mediaId={media_id}"

        return None
