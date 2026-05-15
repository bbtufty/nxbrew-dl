"""CoolROM HTTP source for ROM listings"""
import os, re
from urllib.parse import quote

from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_req

COOLROM_BASE = "https://coolrom.com"

PLATFORM_MAP = {
    "ps3": "ps3",
    "ps2": "ps2",
    "ps1": "psx",
    "psp": "psp",
    "n64": "nintendo64",
    "snes": "snes",
    "nes": "nes",
    "genesis": "sega",
    "dc": "dreamcast",
    "gba": "gba",
    "ds": "nds",
    "3ds": "3ds",
    "wii": "wii",
    "gc": "gcube",
    "xbox": "xbox",
    "xbox360": "xbox360",
}


class CoolROMSource:
    """CoolROM scraper — parse alphabetical game listings"""

    def __init__(self, download_dir="."):
        self.download_dir = download_dir
        self._page_cache = {}

    def get_platform_slug(self, platform_key):
        return PLATFORM_MAP.get(platform_key)

    def fetch_page(self, url):
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

    def list_games(self, platform_key):
        """Fetch all games for a platform by iterating A-Z pages"""
        slug = self.get_platform_slug(platform_key)
        if not slug:
            return []

        entries = []
        letters = ["#"] + [chr(c) for c in range(ord("A"), ord("Z") + 1)]

        for letter in letters:
            url = f"{COOLROM_BASE}/roms/{slug}/{letter}/"
            html = self.fetch_page(url)
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            # Find game links in the format: /roms/ps3/game-name/
            for a in soup.find_all("a", href=re.compile(rf"^/roms/{slug}/[^/]+/$")):
                href = a.get("href", "")
                name = a.get_text(strip=True)
                if name and len(name) > 2:
                    # Extract region from adjacent text if available
                    url = f"{COOLROM_BASE}{href}"
                    entries.append((name, url))

        return entries

    def get_download_link(self, game_url):
        """Get the actual download link from a game page"""
        html = self.fetch_page(game_url)
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")
        # CoolROM uses a form with id='b1' or similar for download
        # The download link is typically in a form action or a specific button
        form = soup.find("form", id=re.compile(r"^b\d+$"))
        if form:
            action = form.get("action", "")
            if action:
                return f"{COOLROM_BASE}{action}"

        # Alternative: look for download button links
        for a in soup.find_all("a"):
            href = a.get("href", "")
            if "download" in href.lower() or "dl" in href.lower():
                return f"{COOLROM_BASE}{href}" if href.startswith("/") else href

        return None
