import os
from urllib.parse import urljoin, urlparse

from curl_cffi import requests
from bs4 import BeautifulSoup

from .regex_tools import get_game_name, check_has_filetype, parse_languages

# Known nxbrew domains and their preferred impersonation profiles
DOMAIN_IMPERSONATION = {
    "nxbrew.me": "safari15_5",
    "nxbrew.net": "chrome",
}

# Alternative domains with known game indices
ALTERNATIVE_INDICES = [
    ("https://nxbrew.me", "games/"),
    ("https://nswgame.com", "list-all-game-switch/"),
    ("https://switch-roms.com", "post-sitemap.xml"),
    ("https://www.ziperto.com", "category/nintendo-switch-nsp/"),
]

# URL patterns used by various sites
NSWGAME_URL_PATTERN = "nintendo-switch-nsp-xci-nsz-download-free"
SWITCH_ROMS_URL_PATTERN = "switch-roms.com"


def _get_impersonation(url):
    """Auto-select impersonation profile based on domain"""
    hostname = urlparse(url).hostname or ""
    for domain, imp in DOMAIN_IMPERSONATION.items():
        if domain in hostname:
            return imp
    return "chrome"


def get_html_page(
    url,
    cache=False,
    cache_filename="index.html",
    impersonate=None,
):
    """Get an HTML page as a soup

    Args:
        url (string): URL
        cache (bool): If True, will save the game index as a cache. Defaults to False
        cache_filename (string): Filename to cache file to. Defaults to "index.html"
        impersonate (str): Browser type to impersonate. If None, auto-selects based on domain
    """

    if impersonate is None:
        impersonate = _get_impersonation(url)

    if not cache:
        r = requests.get(url, impersonate=impersonate)
        soup = BeautifulSoup(r.content, "html.parser")
    else:
        if not os.path.exists(cache_filename):
            r = requests.get(url, impersonate=impersonate)
            with open(cache_filename, mode="wb") as f:
                f.write(r.content)
            r = r.content
        else:
            with open(cache_filename, mode="rb") as f:
                r = f.read()
        soup = BeautifulSoup(r, "html.parser")

    return soup


def _parse_nswgame_index(soup, base_url, general_config, regex_config, game_dict):
    """Parse nswgame.com list-all-game-switch page"""
    nsp_xci_variations = regex_config["nsp_variations"] + regex_config["xci_variations"]
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if NSWGAME_URL_PATTERN not in href:
            continue
        long_name = a.get_text(strip=True)
        if not long_name or long_name in general_config["forbidden_titles"]:
            continue
        if not href.startswith("http"):
            href = urljoin(base_url, href)
        if href in game_dict:
            continue
        short_name = get_game_name(long_name, nsp_xci_variations=nsp_xci_variations)
        remaining_name = long_name.replace(short_name, "")
        has_nsp = check_has_filetype(remaining_name, regex_config["nsp_variations"])
        has_xci = check_has_filetype(remaining_name, regex_config["xci_variations"])
        has_update = check_has_filetype(remaining_name, regex_config["update_variations"])
        has_dlc = check_has_filetype(remaining_name, regex_config["dlc_variations"])
        game_dict[href] = {
            "long_name": long_name, "short_name": short_name, "url": href,
            "has_nsp": has_nsp, "has_xci": has_xci,
            "has_update": has_update, "has_dlc": has_dlc,
        }


def _parse_sitemap_xml(soup, base_url, general_config, regex_config, game_dict):
    """Parse WordPress post-sitemap.xml for game URLs

    Args:
        soup (BeautifulSoup): Parsed XML
        base_url (str): Base URL for resolving relative links
        general_config (dict): General configuration
        regex_config (dict): Regex configuration
        game_dict (dict): Existing game dict to merge into
    """
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(str(soup))
        ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [u.text for u in root.findall('.//ns:url/ns:loc', ns) if u.text]
    except Exception:
        return

    nsp_xci_variations = regex_config["nsp_variations"] + regex_config["xci_variations"]
    for url in urls:
        if url in game_dict or url.rstrip("/") == base_url.rstrip("/"):
            continue
        # Derive game name from URL slug
        slug = url.rstrip("/").split("/")[-1].replace("-", " ")
        long_name = slug
        short_name = get_game_name(long_name, nsp_xci_variations=nsp_xci_variations)
        remaining_name = long_name.replace(short_name, "")
        has_nsp = check_has_filetype(remaining_name, regex_config["nsp_variations"])
        has_xci = check_has_filetype(remaining_name, regex_config["xci_variations"])
        has_update = check_has_filetype(remaining_name, regex_config["update_variations"])
        has_dlc = check_has_filetype(remaining_name, regex_config["dlc_variations"])
        game_dict[url] = {
            "long_name": long_name,
            "short_name": short_name,
            "url": url,
            "has_nsp": has_nsp,
            "has_xci": has_xci,
            "has_update": has_update,
            "has_dlc": has_dlc,
        }
    """Parse nswgame.com list-all-game-switch page

    Args:
        soup (BeautifulSoup): Parsed page
        base_url (str): Base URL for the site
        general_config (dict): General configuration
        regex_config (dict): Regex configuration
        game_dict (dict): Existing game dict to merge into
    """
    nsp_xci_variations = regex_config["nsp_variations"] + regex_config["xci_variations"]

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if NSWGAME_URL_PATTERN not in href:
            continue
        long_name = a.get_text(strip=True)
        if not long_name or long_name in general_config["forbidden_titles"]:
            continue
        if not href.startswith("http"):
            href = urljoin(base_url, href)
        if href in game_dict:
            continue
        short_name = get_game_name(long_name, nsp_xci_variations=nsp_xci_variations)
        remaining_name = long_name.replace(short_name, "")
        has_nsp = check_has_filetype(remaining_name, regex_config["nsp_variations"])
        has_xci = check_has_filetype(remaining_name, regex_config["xci_variations"])
        has_update = check_has_filetype(remaining_name, regex_config["update_variations"])
        has_dlc = check_has_filetype(remaining_name, regex_config["dlc_variations"])
        game_dict[href] = {
            "long_name": long_name,
            "short_name": short_name,
            "url": href,
            "has_nsp": has_nsp,
            "has_xci": has_xci,
            "has_update": has_update,
            "has_dlc": has_dlc,
        }


def _parse_ziperto_index(soup, base_url, general_config, regex_config, game_dict):
    """Parse ziperto.com category pages (article-based blog listings)"""
    nsp_xci_variations = regex_config["nsp_variations"] + regex_config["xci_variations"]
    articles = soup.find_all("article") or soup.find_all("div", class_="post")
    for article in articles:
        link = article.find("a", href=True)
        if not link:
            continue
        href = link["href"]
        if "/category/" in href or "/page/" in href or "#" in href:
            continue
        if not href.startswith("http"):
            href = urljoin(base_url, href)
        if href in game_dict:
            continue
        long_name = link.get_text(strip=True) or article.get_text(strip=True)[:120]
        if not long_name or long_name in general_config["forbidden_titles"]:
            continue
        short_name = get_game_name(long_name, nsp_xci_variations=nsp_xci_variations)
        remaining_name = long_name.replace(short_name, "")
        has_nsp = check_has_filetype(remaining_name, regex_config["nsp_variations"])
        has_xci = check_has_filetype(remaining_name, regex_config["xci_variations"])
        has_update = check_has_filetype(remaining_name, regex_config["update_variations"])
        has_dlc = check_has_filetype(remaining_name, regex_config["dlc_variations"])
        game_dict[href] = {
            "long_name": long_name, "short_name": short_name, "url": href,
            "has_nsp": has_nsp, "has_xci": has_xci,
            "has_update": has_update, "has_dlc": has_dlc,
        }


def _parse_li_entries(soup, base_url, general_config, regex_config, game_dict):
    """Parse game entries from <ul><li><a> format (old site structure)

    Args:
        soup (BeautifulSoup): Parsed page
        base_url (str): Base URL for resolving relative links
        general_config (dict): General configuration
        regex_config (dict): Regex configuration
        game_dict (dict): Existing game dict to merge into
    """
    nsp_xci_variations = regex_config["nsp_variations"] + regex_config["xci_variations"]

    # Look for a ul with many game links inside entry-content or #content
    entry = soup.find("div", class_="entry-content") or soup.find("div", class_="entry") or soup.find(id="content")
    if entry is None:
        return

    for ul in entry.find_all("ul"):
        items = ul.find_all("li")
        if len(items) < 10:
            continue
        for item in items:
            a = item.find("a")
            if a is None:
                continue
            long_name = item.get_text(strip=True)
            if long_name in general_config["forbidden_titles"]:
                continue
            short_name = get_game_name(long_name, nsp_xci_variations=nsp_xci_variations)
            game_url = a.get("href")
            if game_url and not game_url.startswith("http"):
                game_url = urljoin(base_url, game_url)
            if game_url in game_dict:
                continue
            remaining_name = long_name.replace(short_name, "")
            has_nsp = check_has_filetype(remaining_name, regex_config["nsp_variations"])
            has_xci = check_has_filetype(remaining_name, regex_config["xci_variations"])
            has_update = check_has_filetype(remaining_name, regex_config["update_variations"])
            has_dlc = check_has_filetype(remaining_name, regex_config["dlc_variations"])
            game_dict[game_url] = {
                "long_name": long_name,
                "short_name": short_name,
                "url": game_url,
                "has_nsp": has_nsp,
                "has_xci": has_xci,
                "has_update": has_update,
                "has_dlc": has_dlc,
            }
        break


def _parse_az_listing(soup, general_config, regex_config, game_dict):
    """Parse game entries from AlphaListing format (new site structure)

    Args:
        soup (BeautifulSoup): Parsed page
        general_config (dict): General configuration
        regex_config (dict): Regex configuration
        game_dict (dict): Existing game dict to merge into
    """
    nsp_xci_variations = regex_config["nsp_variations"] + regex_config["xci_variations"]

    az_listing = soup.find("div", class_="az-listing")
    if az_listing is None:
        return False

    for letter_section in az_listing.find_all("div", class_="letter-section"):
        for ul in letter_section.find_all("ul", class_="az-columns"):
            for item in ul.find_all("li"):
                a = item.find("a")
                if a is None:
                    continue
                long_name = a.get_text(strip=True)
                if long_name in general_config["forbidden_titles"]:
                    continue
                short_name = get_game_name(long_name, nsp_xci_variations=nsp_xci_variations)
                game_url = a.get("href")
                if game_url in game_dict:
                    continue
                remaining_name = long_name.replace(short_name, "")
                has_nsp = check_has_filetype(remaining_name, regex_config["nsp_variations"])
                has_xci = check_has_filetype(remaining_name, regex_config["xci_variations"])
                has_update = check_has_filetype(remaining_name, regex_config["update_variations"])
                has_dlc = check_has_filetype(remaining_name, regex_config["dlc_variations"])
                game_dict[game_url] = {
                    "long_name": long_name,
                    "short_name": short_name,
                    "url": game_url,
                    "has_nsp": has_nsp,
                    "has_xci": has_xci,
                    "has_update": has_update,
                    "has_dlc": has_dlc,
                }
    return True


def get_game_dict(
    general_config,
    regex_config,
    source_url,
):
    """Download the game index from primary and alternative domains

    Args:
        general_config (dict): General configuration
        regex_config (dict): Regex configuration
        source_url (string): Primary ROM source URL
    """

    game_dict = {}

    nsp_xci_variations = regex_config["nsp_variations"] + regex_config["xci_variations"]

    # 1. Try primary domain: {source_url}/game-index/ (AlphaListing format)
    url = urljoin(source_url, "game-index/")
    game_html = get_html_page(url, cache=True, cache_filename="game_index_primary.html")

    if not _parse_az_listing(game_html, general_config, regex_config, game_dict):
        # Fallback: old easyindex-index format
        index = game_html.find("div", {"id": "easyindex-index"})
        if index is None:
            # Try li entries in entry-content
            _parse_li_entries(game_html, source_url, general_config, regex_config, game_dict)
        else:
            for item in index.find_all("li"):
                long_name = item.text
                if long_name in general_config["forbidden_titles"]:
                    continue
                short_name = get_game_name(long_name, nsp_xci_variations=nsp_xci_variations)
                game_url = item.find("a").get("href")
                if game_url in game_dict:
                    continue
                remaining_name = long_name.replace(short_name, "")
                has_nsp = check_has_filetype(remaining_name, regex_config["nsp_variations"])
                has_xci = check_has_filetype(remaining_name, regex_config["xci_variations"])
                has_update = check_has_filetype(remaining_name, regex_config["update_variations"])
                has_dlc = check_has_filetype(remaining_name, regex_config["dlc_variations"])
                game_dict[game_url] = {
                    "long_name": long_name,
                    "short_name": short_name,
                    "url": game_url,
                    "has_nsp": has_nsp,
                    "has_xci": has_xci,
                    "has_update": has_update,
                    "has_dlc": has_dlc,
                }

    # 2. Try alternative domains with known index paths
    for alt_domain, alt_path in ALTERNATIVE_INDICES:
        alt_url = urljoin(alt_domain, alt_path)
        alt_html = get_html_page(alt_url, cache=True, cache_filename=f"game_index_alt_{urlparse(alt_domain).hostname}.html")
        if "nswgame" in alt_domain:
            _parse_nswgame_index(alt_html, alt_domain, general_config, regex_config, game_dict)
        elif "switch-roms.com" in alt_domain:
            _parse_sitemap_xml(alt_html, alt_domain, general_config, regex_config, game_dict)
        elif "ziperto" in alt_domain:
            _parse_ziperto_index(alt_html, alt_domain, general_config, regex_config, game_dict)
        else:
            _parse_li_entries(alt_html, alt_domain, general_config, regex_config, game_dict)

    return game_dict


def get_languages(soup, lang_dict):
    """Parse languages from a soup

    Args:
        soup (bs4.BeautifulSoup): soup object to find languages in
        lang_dict (dict): Dictionary of languages
    """

    # Parse out languages, find the <strong> tag with language in it,
    # and then find the next_sibling
    strong_tag = soup.findAll("strong")
    for s in strong_tag:
        if "language" in s.text.lower():
            lang_str = s.next_sibling.text
            langs = parse_languages(
                lang_str,
                lang_dict=lang_dict,
            )
            return langs
    return []


def get_thumb_url(soup):
    """Parse thumbnail URL from a soup

    Args:
        soup (bs4.BeautifulSoup): soup object to find languages in
    """

    img = soup.find("meta", {"property": "og:image"})
    if img is None:
        return ""
    return img["content"]
