import copy
import random
import re
import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests

from .regex_tools import parse_languages

ANCHOR_URL = (
    "https://www.google.com/recaptcha/api2/anchor?"
    "ar=1&k=6Lcr1ncUAAAAAH3cghg6cOTPGARa8adOf-y9zv2x&"
    "co=aHR0cHM6Ly9vdW8ucHJlc3M6NDQz&"
    "hl=en&"
    "v=pCoGBhjs9s8EhFOHJFe8cqis&"
    "size=invisible&"
    "cb=ahgyd1gkfkhe"
)


def get_dl_dict(
    soup,
    dl_sites,
    dl_mappings,
    regions=None,
    languages=None,
    regionless_titles=None,
    implied_languages=None,
):
    """For a particular page, parse out download links

    Will look through the page to find various links
    (base game, DLC, updates) per download site and
    add them to a dictionary

    Args:
        soup (bs4.BeautifulSoup): soup object to parse
        dl_sites (list): List of download sites in preference order
        dl_mappings (dict): Dictionary of mappings for download types
        regions (list): list of regions potentially parse. Defaults
            to None, which will use an empty list
        languages (dict): list of languages potentially parse. Defaults
            to None, which will use an empty dict
        regionless_titles (list): list of titles that have no region info.
            Defaults to None, which will use an empty list
        implied_languages (dict): Dictionary of mappings from regions
            to implied languages. Defaults to None, which will use
            an empty dict
    """

    if regions is None:
        regions = []

    if regionless_titles is None:
        regionless_titles = []

    if implied_languages is None:
        implied_languages = {}

    dl_dict = {}

    # Find the strong tags, then start hunting

    strong_tag = soup.findAll("strong")

    # Find the tag
    found_tag = None
    for s in strong_tag:
        if "download links" in s.text.lower():
            found_tag = s
            break

    if found_tag is None:
        raise ValueError("No download links found")


def get_dl_dict_nswgame(soup, dl_sites, dl_mappings):
    """Parse download links from nswgame.com game pages

    nswgame pages have links scattered in <a> tags. We extract and categorize
    by file type based on URL text patterns.

    Args:
        soup (bs4.BeautifulSoup): soup object to parse
        dl_sites (list): List of download sites
        dl_mappings (dict): Dictionary of download type mappings
    """
    dl_dict = {"release_1": {"regions": ["All"], "languages": ["All"]}}

    host_patterns = {
        "1Fichier": ["1fichier"],
        "FreeDL": ["frdl"],
        "MegaUp": ["megaup"],
        "GoFile": ["gofile"],
        "DataNodes": ["datanodes"],
        "HexLoad": ["hexload"],
        "HexUpload": ["hexupload"],
        "MixDrop": ["mixdrop"],
    }

    entry = soup.find("div", class_="entry-content") or soup.find("article")
    if entry is None:
        entry = soup

    seen = set()
    for a in entry.find_all("a", href=True):
        href = a["href"]
        url_lower = href.lower()

        if any(s in url_lower for s in ["twitter.com", "facebook.com", "#comment", "wp-login", "share=", "whatsapp"]):
            continue

        for site_name, patterns in host_patterns.items():
            if any(p in url_lower for p in patterns):
                # Categorize by URL patterns
                dl_key = "base_game_nsp"
                full_name = "Base Game NSP"

                if "dlc" in url_lower or "(dlc)" in url_lower:
                    dl_key = "dlc"
                    full_name = "DLC"
                elif "update" in url_lower or "(update" in url_lower:
                    dl_key = "update"
                    full_name = "Update"
                elif "xci" in url_lower and "nsp" not in url_lower:
                    dl_key = "base_game_xci"
                    full_name = "Base Game XCI"

                if dl_key not in dl_dict["release_1"]:
                    dl_dict["release_1"][dl_key] = []

                # Check if this is a new file type group or site
                found = False
                for info in dl_dict["release_1"][dl_key]:
                    if site_name in info:
                        info[site_name].append(href)
                        found = True
                        break

                if not found:
                    dl_dict["release_1"][dl_key].append({
                        "full_name": full_name,
                        site_name: [href],
                    })
                break

    return dl_dict


def get_dl_dict_switchroms(soup, base_url, dl_sites, dl_mappings):
    """Parse download links from switch-roms.com game pages"""
    from curl_cffi import requests as cffi_req

    dl_dict = {"release_1": {"regions": ["All"], "languages": ["All"]}}
    download_links = soup.select("a.download-line") or soup.select("a.download-line.s-button")
    if not download_links:
        return dl_dict

    for a in download_links:
        href = a.get("href", "")
        if not href or "/download/" not in href:
            continue
        text = a.get_text(strip=True).lower()
        dl_key = "base_game_nsp"
        full_name = "Base Game NSP"
        if "dlc" in text: dl_key = "dlc"; full_name = "DLC"
        elif "update" in text: dl_key = "update"; full_name = "Update"  
        elif "xci" in text and "nsp" not in text: dl_key = "base_game_xci"; full_name = "Base Game XCI"

        dl_page_url = href if href.startswith("http") else urljoin(base_url, href)
        try:
            r = cffi_req.get(dl_page_url, impersonate="chrome", timeout=10)
            soup2 = BeautifulSoup(r.content, "html.parser")
            file_link = soup2.select_one("div.download-btn a") or soup2.find("a", href=lambda h: h and "datadock" in h)
            if file_link:
                actual_url = file_link.get("href", "")
                if actual_url and not actual_url.startswith("#"):
                    if dl_key not in dl_dict["release_1"]:
                        dl_dict["release_1"][dl_key] = []
                    found = False
                    for entry in dl_dict["release_1"][dl_key]:
                        if "DataDock" in entry:
                            entry["DataDock"].append(actual_url); found = True
                    if not found:
                        dl_dict["release_1"][dl_key].append({"full_name": full_name, "DataDock": [actual_url]})
        except Exception:
            pass

    return dl_dict


def get_dl_dict_ziperto(soup, dl_sites, dl_mappings):
    """Parse download links from ziperto.com game pages"""
    dl_dict = {"release_1": {"regions": ["All"], "languages": ["All"]}}
    entry = soup.find("div", class_="entry-content") or soup.find("article")
    if not entry:
        return dl_dict

    for a in entry.find_all("a", href=True):
        href = a["href"]
        if any(s in href.lower() for s in ["twitter", "facebook", "#comment", "javascript"]):
            continue
        url_lower = href.lower()
        text = a.get_text(strip=True).lower()

        # Determine file type
        dl_key = "base_game_nsp"
        if "dlc" in url_lower or "dlc" in text: dl_key = "dlc"
        elif "update" in url_lower or "update" in text: dl_key = "update"
        elif "xci" in url_lower or "xci" in text: dl_key = "base_game_xci"

        # Determine host
        site = None
        for s, sn in [("1fichier","1Fichier"),("frdl","FreeDL"),("gofile","GoFile"),
                       ("datanodes","DataNodes"),("hexload","HexLoad"),("hexupload","HexUpload"),
                       ("megaup","MegaUp"),("mixdrop","MixDrop"),("mediafire","MediaFire")]:
            if s in url_lower: site = sn; break
        if not site:
            continue

        if dl_key not in dl_dict["release_1"]:
            dl_dict["release_1"][dl_key] = []
        found = False
        for ei in dl_dict["release_1"][dl_key]:
            if site in ei: ei[site].append(href); found = True
        if not found:
            dl_dict["release_1"][dl_key].append({"full_name": dl_key.replace("_"," ").title(), site: [href]})

    return dl_dict


def get_dl_dict(
    soup,
    dl_sites,
    dl_mappings,
    regions=None,
    languages=None,
    regionless_titles=None,
    implied_languages=None,
):
    """For a particular page, parse out download links"""

    if regions is None:
        regions = []
    if regionless_titles is None:
        regionless_titles = []
    if implied_languages is None:
        implied_languages = {}

    dl_dict = {}

    # Find the strong tags, then start hunting
    strong_tag = soup.findAll("strong")
    found_tag = None
    for s in strong_tag:
        if "download links" in s.text.lower():
            found_tag = s
            break
    if found_tag is None:
        raise ValueError("No download links found")

    tag = found_tag.find_next("p")

    # Keep looping over to keep finding regions
    still_hunting = True
    release_number = 1

    while still_hunting:

        current_release = f"release_{release_number}"
        dl_dict[current_release] = {}

        # We may find a region here, so change the current region and then start looping over tags
        parsed_regions = parse_regions(tag, regions)

        if len(parsed_regions) > 0:

            # Parse out languages
            parsed_languages = parse_language_tag(tag, languages)

            # If we haven't found anything, use implied languages
            if len(parsed_languages) == 0:
                for region in parsed_regions:
                    if region in implied_languages:
                        parsed_languages.append(implied_languages[region])

            # If we still don't have anything, just assign all languages here
            if len(parsed_languages) == 0:
                parsed_languages = ["All"]

            tag = tag.find_next("p")

        # Alternatively, we might find something that looks like a region title,
        # but doesn't contain any useful info

        elif any([n in tag.text for n in regionless_titles]):

            parsed_regions = ["All"]
            parsed_languages = ["All"]
            tag = tag.find_next("p")

        else:
            parsed_regions = ["All"]
            parsed_languages = ["All"]

        dl_dict[current_release]["regions"] = parsed_regions
        dl_dict[current_release]["languages"] = parsed_languages

        # We are within a region now, so search for "Base Game/Update/DLC" here.
        # Keep looping until we don't find anything. Keep things in list form
        # so that we can potentially have multiples within each region
        still_hunting_dl = True

        while still_hunting_dl:
            found_anything_dl = False

            for dl_mapping in dl_mappings:

                tag_no_brackets = tag.text.split("(")[0]

                tag_names = dl_mappings[dl_mapping]["tag_names"]

                if any([n in tag_no_brackets for n in tag_names]):

                    if dl_mapping in ["Base Game", "DLC", "Update"]:
                        tag, parsed_dict = parse_dl_tags(
                            tag,
                            dict_key=dl_mapping.lower(),
                            dl_sites=dl_sites,
                            dl_mappings=dl_mappings,
                        )
                    else:
                        raise ValueError(
                            f"Name should contain one of: {', '.join(dl_mappings.keys())}. Got {tag.text}"
                        )

                    # If we don't have an empty dictionary, add things in now
                    if len(parsed_dict) > 0:

                        # Get out the key, and append to the full dictionary
                        parsed_keys = list(parsed_dict.keys())

                        for parsed_key in parsed_keys:
                            if parsed_key not in dl_dict[current_release]:
                                dl_dict[current_release][parsed_key] = []

                            # Strip any extraneous whitespace
                            parsed_dict[parsed_key]["full_name"] = parsed_dict[
                                parsed_key
                            ]["full_name"].strip()

                            dl_dict[current_release][parsed_key].append(
                                parsed_dict[parsed_key]
                            )

                    found_anything_dl = True

            # If we haven't found anything, jump out here
            if not found_anything_dl:
                still_hunting_dl = False

        # If we don't have anything useful in here, delete the release and leave
        dl_keys = []
        for dl_mapping in dl_mappings:
            dl_keys.extend(list(dl_mappings[dl_mapping]["dl_tags"].keys()))

        if not any([n in dl_dict[current_release] for n in dl_keys]):
            del dl_dict[current_release]
            still_hunting = False

        release_number += 1

    return dl_dict


def parse_regions(tag, regions):
    """Parse regions from tag

    Args:
        tag (bs4.Tag): tag object to parse
        regions (list): list of regions potentially parse
    """
    parsed_regions = []

    for region in regions:
        if region.lower() in tag.text.lower():
            parsed_regions.append(region)

    return parsed_regions


def parse_language_tag(tag, languages=None):
    """From a soup tag, find things in square brackets and parse as potential languages

    Args:
        tag (bs4.Tag): tag object to parse
        languages (dict): Dictionary of languages potentially parse
    """

    # Figure out if we have anything here. It should be between square brackets
    t = tag.text

    reg = re.findall(r"\[(.*?)\]", t)

    # Loop over everything, and if we match then return
    parsed_languages = []
    for r in reg:
        parsed_languages = parse_languages(
            r,
            lang_dict=languages,
        )
        if len(parsed_languages) > 0:
            break

    return parsed_languages


def parse_dl_tags(
    tag,
    dict_key,
    dl_sites,
    dl_mappings,
):
    """Parse out links for games, updates, and DLC

    These can either be spread out over paragraphs or inline,
    so we distinguish between those cases here

    Args:
        tag (bs4.Tag): starting tag object
        dict_key (str): key to distinguish different file types
        dl_sites (list): list of DL sites to look for in links
        dl_mappings (dict): Dictionary of names to map to download types
    """

    link_dict = {}

    t = tag.text

    # Start by distinguishing whether we're a base game or something else
    if dict_key == "base game":
        if "NSP" in t and "XCI" not in t:
            link_dict_key = "base_game_nsp"
        elif "XCI" in t and "NSP" not in t:
            link_dict_key = "base_game_xci"
        elif "NSP" not in t and "XCI" not in t:
            link_dict_key = "base_game_undefined"
        elif "NSP" in t and "XCI" in t:
            raise ValueError(f"Name {t} implies both NSP *and* XCI!")
        else:
            raise ValueError(f"Unsure how to parse Base Game name: {t}")
    else:
        link_dict_key = copy.deepcopy(dict_key)

    link_dict[link_dict_key] = {}
    link_dict[link_dict_key]["full_name"] = t

    # Loop until we're no longer finding links
    finding_links = True
    while finding_links:
        found_site = False
        tag = tag.find_next("p")
        t = tag.text

        site = None
        for site in dl_sites:
            if site in t:
                link_dict[link_dict_key][site] = []
                found_site = True
                break

        if found_site:
            # Find all the hrefs
            href = tag.find_all("a", href=True)

            # There can be inline tags, where the link is the download site name
            found_inline = False

            for h in href:
                ht = h.text

                for inline_site in dl_sites:
                    if inline_site in ht:

                        if inline_site not in link_dict[link_dict_key]:
                            link_dict[link_dict_key][inline_site] = []

                        link_dict[link_dict_key][inline_site].append(h["href"])

                        found_inline = True
                        break

            # Otherwise, parse out the text and go from there
            if not found_inline:

                for h in href:
                    ht = h.text

                    # If there's some weird phantom link, skip
                    if ht == "":
                        continue

                    # There's an edge case here where the "base game" can actually have everything in there
                    found_all_in_one = False

                    for dl_mapping in dl_mappings:

                        tag_names = dl_mappings[dl_mapping]["tag_names"]

                        if any([n in ht for n in tag_names]):

                            if dl_mapping not in link_dict:
                                link_dict[dl_mapping.lower()] = {}
                                link_dict[dl_mapping.lower()]["full_name"] = ht
                                link_dict[dl_mapping.lower()][site] = []
                            link_dict[dl_mapping.lower()][site].append(h["href"])

                            found_all_in_one = True
                            break

                    # If we just have a link, put that in now
                    if not found_all_in_one:
                        link_dict[link_dict_key][site].append(h["href"])

        else:
            finding_links = False

    # Finally, hunt through to the next tag WITHOUT a link in
    found_links = True
    while found_links:
        links = tag.find_all("a", href=True)
        if len(links) == 0:
            found_links = False
        else:
            tag = tag.find_next("p", href=False)

    # If we only have a name in here, then clear out the dictionary and leave
    if len(link_dict[link_dict_key]) == 1:
        link_dict = {}

    return tag, link_dict


def RecaptchaV3():
    """Pass Recaptcha test"""

    url_base = "https://www.google.com/recaptcha/"
    post_data = "v={}&reason=q&c={}&k={}&co={}"
    client = requests.Session()
    client.headers.update({"content-type": "application/x-www-form-urlencoded"})
    matches = re.findall(r"([api2|enterprise]+)/anchor\?(.*)", ANCHOR_URL)[0]
    url_base += matches[0] + "/"
    params = matches[1]
    res = client.get(url_base + "anchor", params=params)
    token = re.findall(r'"recaptcha-token" value="(.*?)"', res.text)[0]
    params = dict(pair.split("=") for pair in params.split("&"))
    post_data = post_data.format(params["v"], token, params["k"], params["co"])
    res = client.post(url_base + "reload", params=f'k={params["k"]}', data=post_data)
    answer = re.findall(r'"rresp","(.*?)"', res.text)[0]
    return answer


def bypass_ouo(
    url,
    logger=None,
    impersonate=None,
    n_retry=0,
    max_retries=2,
):
    if n_retry >= max_retries:
        raise ValueError("Max retries exceeded!")
    if impersonate is None:
        impersonate = random.choice(["safari15_5", "chrome120", "edge101"])

    client = cffi_requests.Session()
    client.headers.update(
        {
            "authority": "ouo.io",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "cache-control": "max-age=0",
            "referer": "http://www.google.com/ig/adde?moduleurl=",
            "upgrade-insecure-requests": "1",
        }
    )

    tempurl = url.replace("ouo.press", "ouo.io")
    p = urlparse(tempurl)
    temp_url_id = tempurl.split("/")[-1]
    res = client.get(tempurl, impersonate=impersonate)

    # If we get a weird response, try again
    status_code = res.status_code
    if status_code not in [200, 302]:

        if logger is not None:
            logger.warning(f"Received status code {status_code}. Waiting then retrying")
        else:
            print(f"Received status code {status_code}. Waiting then retrying")

        time.sleep(2)
        alternate_imp = random.choice(["safari15_5", "chrome120", "edge101"])
        bypassed_url = bypass_ouo(
            url,
            logger=logger,
            impersonate=alternate_imp,
            n_retry=n_retry + 1,
        )
        return bypassed_url

    next_url = f"{p.scheme}://{p.hostname}/go/{temp_url_id}"

    for _ in range(2):

        if res.headers.get("Location"):
            break

        bs4 = BeautifulSoup(res.content, "lxml")
        inputs = None
        try:
            inputs = bs4.form.findAll("input", {"name": re.compile(r"token$")})
        except AttributeError:
            pass

        if inputs is None:
            if logger is not None:
                logger.warning(f"Page load error. Waiting then retrying")
            else:
                print(f"Page load error. Waiting then retrying")
            time.sleep(2)
            alternate_imp = random.choice(["safari15_5", "chrome120", "edge101"])
            bypassed_url = bypass_ouo(
                url,
                logger=logger,
                impersonate=alternate_imp,
                n_retry=n_retry + 1,
            )
            return bypassed_url

    next_url = f"{p.scheme}://{p.hostname}/go/{temp_url_id}"

    for _ in range(2):

        if res.headers.get("Location"):
            break

        bs4 = BeautifulSoup(res.content, "lxml")

        # Try and find the token
        inputs = None
        try:
            inputs = bs4.form.findAll("input", {"name": re.compile(r"token$")})
        except AttributeError:
            pass

        # Catch problems here
        if inputs is None:

            if logger is not None:
                logger.warning(f"Page load error. Waiting then retrying")
            else:
                print(f"Page load error. Waiting then retrying")

            time.sleep(10)
            bypassed_url = bypass_ouo(
                url,
                logger=logger,
                impersonate=impersonate,
                n_retry=n_retry + 1,
            )
            return bypassed_url

        data = {i.get("name"): i.get("value") for i in inputs}
        data["x-token"] = RecaptchaV3()

        h = {"content-type": "application/x-www-form-urlencoded"}

        # Catch any rejections
        res = client.post(
            next_url,
            data=data,
            headers=h,
            allow_redirects=False,
            impersonate=impersonate,
        )

        status_code = res.status_code
        if status_code not in [200, 302]:

            if logger is not None:
                logger.warning(
                    f"Received status code {status_code}. Waiting then retrying"
                )
            else:
                print(f"Received status code {status_code}. Waiting then retrying")

            time.sleep(10)
            bypassed_url = bypass_ouo(
                url,
                logger=logger,
                impersonate=impersonate,
                n_retry=n_retry + 1,
            )
            return bypassed_url

        next_url = f"{p.scheme}://{p.hostname}/xreallcygo/{temp_url_id}"

    return res.headers.get("Location")

def bypass_1link(
    url,
    logger=None,
    impersonate=None,
    n_retry=0,
    max_retries=3,
):
    """Bypass 1link url

    Args:
        url (str): URL to bypass
        logger (logging.Logger): Logger to use. Defaults to None,
            which will not log anything
        impersonate (str): Type of browser to impersonate. Defaults
            to None, which will choose randomly from a selection
        n_retry (int): Current retry. Defaults to 0
        max_retries (int): Maximum number of retries. Defaults to 5
    """

    if n_retry >= max_retries:
        raise ValueError("Max retries exceeded!")

    if impersonate is None:
        impersonate = random.choice(["chrome120", "safari15_5", "edge101"])

    client = cffi_requests.Session()
    client.headers.update(
        {
            "authority": "ouo.io",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "cache-control": "max-age=0",
            "referer": "http://www.google.com/ig/adde?moduleurl=",
            "upgrade-insecure-requests": "1",
        }
    )

    res = client.get(url, impersonate=impersonate)

    # If we get a weird response, try again
    status_code = res.status_code
    if status_code not in [200, 302, 307]:

        if logger is not None:
            logger.warning(f"Received status code {status_code}. Waiting then retrying")
        else:
            print(f"Received status code {status_code}. Waiting then retrying")

        time.sleep(2)
        bypassed_url = bypass_1link(
            url,
            logger=logger,
            impersonate=impersonate,
            n_retry=n_retry + 1,
        )
        return bypassed_url

    # Parse soup, pull out the download link from the button
    bs4 = BeautifulSoup(res.content, "lxml")
    dl_link = bs4.find_all("a", attrs={"id": "download"})[0]
    next_url = dl_link["href"]

    # If we're now redirecting through to OUO, then do that here
    if "ouo" in next_url:
        link = bypass_ouo(next_url,
                          logger=logger,
                          impersonate=impersonate,
                          n_retry=n_retry,
                          max_retries=max_retries,
                          )

    # Otherwise work as normal
    else:

        # Get that next URL, disallowing redirects
        res = client.get(next_url, impersonate=impersonate, allow_redirects=False)

        # If we get a weird response, try again
        status_code = res.status_code
        if status_code not in [200, 302, 307]:

            if logger is not None:
                logger.warning(f"Received status code {status_code}. Waiting then retrying")
            else:
                print(f"Received status code {status_code}. Waiting then retrying")

            time.sleep(10)
            bypassed_url = bypass_1link(
                url,
                logger=logger,
                impersonate=impersonate,
                n_retry=n_retry + 1,
            )
            return bypassed_url

        link = res.headers.get("Location")

    return link
