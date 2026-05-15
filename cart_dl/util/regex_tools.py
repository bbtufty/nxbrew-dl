import re
import os


def get_game_name(
    f,
    nsp_xci_variations,
):
    """Get game name, which is normally up to "Switch NSP", but there are some edge cases

    Args:
        f (str): Name
        nsp_xci_variations (list): List of potential NSP/XCI name variations
    """

    # Strip ™ and ® symbols that can appear in titles before regex matching
    f = f.replace('\u2122', '').replace('\u00AE', '')

    # Search for "Switch" (with optional NSP/XCI variations), "Cloud Version", "eShop",
    # "Switch +, "+ Update", "+ DLC", and "Nintendo Switch" (used by some sites like switch-roms.com)
    # re.IGNORECASE handles "SWITCH" all-caps variants from nxbrew.me
    regex_str = (
        r"^.*?"
        r"(?="
        f"(?:\\s?Swi(?:tc|ct)h)?\\s(?:\\(?{'|'.join(nsp_xci_variations)})\\)?"
        "|"
        r"(?:\s[-|\u2013]\sCloud Version)"
        "|"
        r"(?:\(eShop\))"
        "|"
        r"(?:\s?Switch\s\+)"
        "|"
        r"(?:\s?\+\sUpdate)"
        "|"
        r"(?:\s?\+\sDLC)"
        "|"
        r"(?:\s?Switch\s+Download)"
        "|"
        r"(?:\snintendo\sswitch)"
        ")"
    )

    reg = re.findall(regex_str, f, re.IGNORECASE)

    # If we find something, then pull that out
    if len(reg) > 0:
        f = reg[0]

    return f


def get_game_name_from_filename(filename):
    """Extract clean game name from a filename (platform-agnostic)

    Handles patterns like:
      - "Game Name (USA) (Rev 1).iso"
      - "Game Name [SLUS-12345].bin"
      - "Game Name (v1.01).pkg"
      - "001 - Game Name.n64"

    Args:
        filename (str): Filename with or without path
    """
    name = os.path.basename(filename)
    name = os.path.splitext(name)[0]
    
    # Remove region tags in parentheses or brackets
    name = re.sub(r'\s*\((?:USA|EUR|JAP|JPN|ASIA|KOR|World|Region Free|Demo|Proto|Beta|Unl|Sample)\)\s*', ' ', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\[(?:USA|EUR|JAP|JPN|ASIA|KOR|World)\]?\s*', ' ', name, flags=re.IGNORECASE)
    
    # Remove revision/version tags
    name = re.sub(r'\s*\(Rev\s*\d+\)\s*', ' ', name)
    name = re.sub(r'\s*\(v[\d.]+\)\s*', ' ', name)
    name = re.sub(r'\s*\(Disc\s*\d+\)\s*', ' ', name)
    
    # Remove serial numbers like [SLUS-12345] or (SLUS-12345)
    name = re.sub(r'\s*[\[\(][A-Z]{2,4}[-_]\d{3,6}[\]\)]\s*', ' ', name)
    
    # Remove leading track numbers
    name = re.sub(r'^\d{2,3}\s*[-–—]\s*', '', name)
    
    # Clean up whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Handle No-Intro style naming: trim after first occurrence of country/region
    # e.g. "Game Name (USA) (En,Fr,De)" -> "Game Name"
    return name


def check_has_extension(filename, extensions):
    """Check if a filename has any of the given extensions
    
    Args:
        filename (str): Filename
        extensions (list): List of extensions including dot (e.g. ['.iso', '.pkg'])
    """
    name_lower = filename.lower()
    return any(name_lower.endswith(ext.lower()) for ext in extensions)


def check_has_filetype(
    f,
    search_str,
):
    """Check whether the game has an associated filetype

    Args:
        f (str): Name of the file
        search_str (list): List of potential values to check for
    """

    regex_str = "|".join(search_str)

    reg = re.findall(regex_str, f)

    if len(reg) > 0:
        return True
    else:
        return False


def parse_languages(
    f,
    lang_dict=None,
):
    """Parse languages out of a string

    Args:
        f (str): String pattern to match
        lang_dict (dict): Dictionary of languages
    """

    if lang_dict is None:
        return []

    long_langs = list(lang_dict.keys())
    short_langs = [lang_dict[l] for l in long_langs]

    f_split = f.split(",")

    langs = []
    for fs in f_split:

        # Strip any leading whitespace
        fs = fs.strip()

        for i, short_lang in enumerate(short_langs):

            # Do a first pass where we check against short languages
            short_match = re.match(short_lang, fs, flags=re.NOFLAG)
            if short_match:
                langs.append(long_langs[i])

                # If we do have a short match, move on
                continue

            # Do a first pass where we check against short languages
            long_match = re.match(long_langs[i], fs, flags=re.NOFLAG)
            if long_match:
                langs.append(long_langs[i])

    return langs
