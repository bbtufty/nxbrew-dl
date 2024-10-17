import os
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .regex_tools import get_game_name, check_has_filetype, parse_languages


def get_html_page(
    url,
    cache=False,
    cache_filename="index.html",
):
    """Get an HTML page as a soup

    Args:
        url (string): URL
        cache (bool): If True, will save the game index as a cache. Defaults to False
        cache_filename (string): Filename to cache file to. Defaults to "index.html"
    """

    if not cache:
        r = requests.get(url)
        soup = BeautifulSoup(r.content, "html.parser")
    else:
        if not os.path.exists(cache_filename):
            r = requests.get(url)
            with open(cache_filename, mode="wb") as f:
                f.write(r.content)
            r = r.content
        else:
            with open(cache_filename, mode="rb") as f:
                r = f.read()
        soup = BeautifulSoup(r, "html.parser")

    return soup


def get_game_dict(
    general_config,
    regex_config,
    nxbrew_url,
):
    """Download the game index, and parse relevant info out of it

    Args:
        general_config (dict): General configuration
        regex_config (dict): Regex configuration
        nxbrew_url (string): NXBrew URL
    """

    game_dict = {}

    url = urljoin(nxbrew_url, "Index/game-index/games/")

    # Load in the HTML
    game_html = get_html_page(url,
                              cache_filename="game_index.html",
                              )
    index = game_html.find("div", {"id": "easyindex-index"})

    nsp_xci_variations = regex_config["nsp_variations"] + regex_config["xci_variations"]
    for item in index.find_all("li"):

        # Get the long name, the short name, and the URL
        long_name = item.text

        # If there are any forbidden titles, skip them here
        if long_name in general_config["forbidden_titles"]:
            continue

        short_name = get_game_name(long_name, nsp_xci_variations=nsp_xci_variations)
        url = item.find("a").get("href")

        if url in game_dict:
            raise ValueError(f"Duplicate URLs found: {url}")

        # Pull out whether NSP/XCI, and whether it has updates/DLCs
        remaining_name = long_name.replace(short_name, "")
        has_nsp = check_has_filetype(remaining_name, regex_config["nsp_variations"])
        has_xci = check_has_filetype(remaining_name, regex_config["xci_variations"])
        has_update = check_has_filetype(
            remaining_name, regex_config["update_variations"]
        )
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
