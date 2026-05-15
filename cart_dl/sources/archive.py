"""Internet Archive source for ROM collections"""
import os, re, json, time, subprocess, tempfile
from urllib.parse import quote, unquote

from curl_cffi import requests as cffi_req

IA_BASE = "https://archive.org"
IA_METADATA = f"{IA_BASE}/metadata"
IA_DOWNLOAD = f"{IA_BASE}/download"


class ArchiveSource:
    """Internet Archive ROM source — search collections, list files, download"""

    def __init__(self, download_dir, aria2c_path="aria2c", cache_dir=None):
        self.download_dir = download_dir
        self.aria2c_path = aria2c_path
        self.cache_dir = cache_dir
        self.file_cache = {}  # collection_identifier -> [(name, path, size), ...]
        self._meta_cache = {}  # identifier -> metadata dict

    def get_collection_identifier(self, platform_data):
        """Get the IA collection identifier for a platform"""
        sources = platform_data.get("sources", {}).get("archive", [])
        for src in sources:
            if src.get("name") == "ia":
                return src.get("identifier")
        return None

    def fetch_metadata(self, identifier):
        """Fetch file listing from Internet Archive metadata API"""
        if identifier in self._meta_cache:
            return self._meta_cache[identifier]
        try:
            url = f"{IA_METADATA}/{identifier}"
            r = cffi_req.get(url, impersonate="chrome", timeout=30)
            if r.status_code != 200:
                return None
            meta = r.json()
            self._meta_cache[identifier] = meta
            return meta
        except Exception:
            return None

    def list_files(self, identifier):
        """List all files in an IA collection item"""
        if identifier in self.file_cache:
            return self.file_cache[identifier]
        meta = self.fetch_metadata(identifier)
        if not meta:
            return []
        files = meta.get("files", [])
        entries = []
        for f in files:
            name = f.get("name", "")
            size = int(f.get("size", 0))
            if name.endswith("/"):
                continue
            # Extract clean game name
            basename = os.path.basename(name)
            name_no_ext = os.path.splitext(basename)[0]
            name_no_ext = re.sub(r'\s*\(.*?\)', '', name_no_ext)
            name_no_ext = re.sub(r'\s*\[.*?\]', '', name_no_ext)
            entries.append((name_no_ext.strip(), name, size))
        self.file_cache[identifier] = entries
        return entries

    def search_files(self, identifier, query, extensions=None):
        """Search files in a collection by game name"""
        files = self.list_files(identifier)
        query_norm = query.lower().replace(" ", "").replace("-", "").replace("_", "")
        results = []
        for name, path, size in files:
            name_norm = name.lower().replace(" ", "").replace("-", "").replace("_", "")
            if query_norm in name_norm:
                ext = os.path.splitext(path)[1].lower()
                if extensions and ext not in extensions:
                    continue
                results.append((name, path, size, ext))
        return results

    def find_best_file(self, identifier, game_name, preferred_extensions, all_extensions):
        """Find the best matching file preferring compressed formats

        Args:
            identifier: IA collection identifier
            game_name: Game name to search for
            preferred_extensions: Ordered list of preferred (compressed) extensions
            all_extensions: All valid extensions for the platform

        Returns:
            (path, size, download_url) or (None, 0, None)
        """
        results = self.search_files(identifier, game_name, all_extensions)
        if not results:
            return None, 0, None

        # Score by extension preference (lower index = more preferred)
        def score_ext(ext):
            try:
                return preferred_extensions.index(ext)
            except ValueError:
                try:
                    return len(preferred_extensions) + all_extensions.index(ext)
                except ValueError:
                    return 999

        results.sort(key=lambda r: (score_ext(r[3]), r[2]))  # sort by ext pref, then size

        best = results[0]
        path = best[1]
        size = best[2]
        download_url = f"{IA_DOWNLOAD}/{identifier}/{quote(path)}"
        return path, size, download_url

    def download_file(self, identifier, file_path, output_dir):
        """Download a specific file from IA via aria2c"""
        os.makedirs(output_dir, exist_ok=True)
        download_url = f"{IA_DOWNLOAD}/{identifier}/{quote(file_path)}"
        cmd = [
            self.aria2c_path,
            "--dir", output_dir,
            "--out", os.path.basename(file_path),
            "--check-integrity=true",
            "--continue=true",
            "--max-connection-per-server=4",
            "--split=4",
            download_url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        return result.returncode

    def download_file_direct(self, identifier, file_path, output_dir):
        """Download via direct HTTP (fallback)"""
        os.makedirs(output_dir, exist_ok=True)
        download_url = f"{IA_DOWNLOAD}/{identifier}/{quote(file_path)}"
        output_path = os.path.join(output_dir, os.path.basename(file_path))
        r = cffi_req.get(download_url, impersonate="chrome", stream=True, timeout=7200)
        if r.status_code == 200:
            with open(output_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            return output_path
        return None
