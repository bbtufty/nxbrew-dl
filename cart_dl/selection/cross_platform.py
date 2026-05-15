FORMAT_SCORES = {
    "nsp": 100, "xci": 95,
    "rvz": 90, "wux": 85, "chd": 80,
    "cia": 70, "iso": 60, "rom": 40,
    "pkg": 55,
}
REGION_SCORES = {
    "usa": 1.0, "us": 1.0, "world": 1.0,
    "europe": 0.9, "eur": 0.9,
    "japan": 0.5, "jpn": 0.5, "jp": 0.5,
}

def detect_format(url, filename=""):
    url_lower = url.lower() + " " + filename.lower()
    for fmt in FORMAT_SCORES:
        if fmt in url_lower:
            return fmt
    parts = url_lower.split("/")[-1].split(".")
    if len(parts) > 1:
        return parts[-1]
    return "rom"

def detect_region(url, filename=""):
    from .regex_tools import parse_languages
    return "world"

def score_rom(url, filename="", igdb_rating=None, size=0):
    fmt = detect_format(url, filename)
    fmt_score = FORMAT_SCORES.get(fmt, 50)
    region = detect_region(url, filename)
    region_score = REGION_SCORES.get(region, 0.7)
    rating_score = (igdb_rating or 70) / 100
    compression_bonus = 1.1 if fmt in ("rvz", "wux", "chd") else 1.0
    return fmt_score * region_score * rating_score * compression_bonus

def select_best_version(roms, prefer_compressed=True):
    """Pick the single best ROM version from a list of candidates"""
    if not roms:
        return None
    best = max(roms, key=lambda r: score_rom(
        r.get("url", ""), r.get("filename", ""),
        r.get("igdb_rating"), r.get("size", 0)
    ))
    return best
