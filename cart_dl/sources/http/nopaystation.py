"""NoPayStation HTTP source — TSV-based PKG listings with direct download links"""
import csv, io, os, re
from urllib.parse import quote

from curl_cffi import requests as cffi_req

NPS_BASE = "https://nopaystation.com"
NPS_TSV_URL = "https://nopaystation.com/tsv"

# TSV file types available on NPS
TSV_TYPES = {
    "ps3_games": "PS3_GAMES.tsv",
    "ps3_dlc": "PS3_DLCS.tsv",
    "ps3_themes": "PS3_THEMES.tsv",
    "ps3_avatars": "PS3_AVATARS.tsv",
    "ps3_demos": "PS3_DEMOS.tsv",
    "psp_games": "PSP_GAMES.tsv",
    "psp_dlc": "PSP_DLCS.tsv",
    "psp_themes": "PSP_THEMES.tsv",
    "psp_updates": "PSP_UPDATES.tsv",
    "psp_demos": "PSP_DEMOS.tsv",
    "psv_games": "PSV_GAMES.tsv",
    "psv_dlc": "PSV_DLCS.tsv",
    "psv_themes": "PSV_THEMES.tsv",
    "psv_updates": "PSV_UPDATES.tsv",
    "psv_demos": "PSV_DEMOS.tsv",
}

# Map platform keys to NPS TSV types
PLATFORM_TSV_MAP = {
    "ps3": ["ps3_games", "ps3_dlc", "ps3_demos"],
    "psp": ["psp_games", "psp_dlc", "psp_demos"],
    "psv": ["psv_games", "psv_dlc", "psv_demos"],
}


class NoPayStationSource:
    """NoPayStation scraper — direct PKG downloads from TSV listings
    
    TSV columns:
    - Title ID (e.g., NPUB30001)
    - Region (US, EU, JP, etc.)
    - Name
    - PKG direct link
    - RAP (license key)
    - Content ID
    - Last Modification Date
    - Download .RAP file
    - File Size
    - SHA256
    """

    def __init__(self, download_dir="."):
        self.download_dir = download_dir
        self._tsv_cache = {}  # tsv_type -> list of entries
        self._game_index = {}  # (platform, name_norm) -> entry

    def _fetch_tsv(self, tsv_type):
        """Fetch and parse a TSV file from NoPayStation"""
        if tsv_type in self._tsv_cache:
            return self._tsv_cache[tsv_type]

        tsv_filename = TSV_TYPES.get(tsv_type)
        if not tsv_filename:
            return []

        url = f"{NPS_TSV_URL}/{tsv_filename}"
        try:
            r = cffi_req.get(url, impersonate="chrome", timeout=60)
            if r.status_code != 200:
                return []

            # Parse TSV
            entries = []
            reader = csv.reader(io.StringIO(r.text), delimiter="\t")
            headers = next(reader, None)  # Skip header row
            if not headers:
                return []

            for row in reader:
                if len(row) < 4:
                    continue
                title_id = row[0].strip()
                region = row[1].strip()
                name = row[2].strip()
                pkg_url = row[3].strip()
                rap = row[4].strip() if len(row) > 4 else ""
                content_id = row[5].strip() if len(row) > 5 else ""
                file_size = row[8].strip() if len(row) > 8 else ""
                sha256 = row[9].strip() if len(row) > 9 else ""

                # Skip entries with MISSING download links
                if pkg_url == "MISSING" or not pkg_url:
                    continue

                entries.append({
                    "title_id": title_id,
                    "region": region,
                    "name": name,
                    "pkg_url": pkg_url,
                    "rap": rap,
                    "content_id": content_id,
                    "file_size": file_size,
                    "sha256": sha256,
                })

            self._tsv_cache[tsv_type] = entries
            return entries
        except Exception:
            return []

    def list_games(self, platform_key):
        """Fetch all games for a platform from NPS TSV files"""
        tsv_types = PLATFORM_TSV_MAP.get(platform_key, [])
        if not tsv_types:
            return []

        entries = []
        for tsv_type in tsv_types:
            games = self._fetch_tsv(tsv_type)
            for g in games:
                entries.append((g["name"], g))

        return entries

    def find_game(self, platform_key, game_name):
        """Find a game by name, returning the best matching entry"""
        tsv_types = PLATFORM_TSV_MAP.get(platform_key, [])
        if not tsv_types:
            return None

        name_norm = game_name.lower().replace(" ", "").replace("-", "").replace("_", "")

        for tsv_type in tsv_types:
            games = self._fetch_tsv(tsv_type)
            for g in games:
                g_norm = g["name"].lower().replace(" ", "").replace("-", "").replace("_", "")
                # Remove common suffixes for matching
                g_clean = re.sub(r'\s*\(.*?\)', '', g["name"]).strip().lower()
                g_clean_norm = g_clean.replace(" ", "").replace("-", "").replace("_", "")
                
                if name_norm in g_clean_norm or g_clean_norm in name_norm:
                    return g

        return None

    def get_download_link(self, game_entry):
        """Get the direct PKG download link from a game entry"""
        if isinstance(game_entry, dict):
            return game_entry.get("pkg_url")
        return None

    def get_rap_link(self, game_entry):
        """Get the RAP (license) download link if available"""
        if isinstance(game_entry, dict):
            rap = game_entry.get("rap", "")
            if rap and rap not in ("MISSING", "NOT REQUIRED"):
                content_id = game_entry.get("content_id", "")
                if content_id:
                    return f"{NPS_BASE}/rap/{content_id}.rap"
        return None
