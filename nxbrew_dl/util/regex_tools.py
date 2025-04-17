import re


def get_game_name(
    f,
    nsp_xci_variations,
):
    """Get game name, which is normally up to "Switch NSP", but there are some edge cases

    Args:
        f (str): Name
        nsp_xci_variations (list): List of potential NSP/XCI name variations
    """

    # This is a little fiddly, the default is something like [Name] Switch NSP/XCI or whatever, but there's also
    # various other possibilities. Search for "Switch" (with optional NSP/XCI variations), "Cloud Version", "eShop",
    # "Switch +, "+ Update", and "+ DLC"
    regex_str = (
        r"^.*?"
        r"(?="
        f"(?:\\s?Swi(?:tc|ct)h)?\\s(?:\\(?{'|'.join(nsp_xci_variations)})\\)?"
        "|"
        r"(?:\\s[-|–]\\sCloud Version)"
        "|"
        r"(?:\(eShop\))"
        "|"
        r"(?:\\s?Switch\\s\+)"
        "|"
        r"(?:\\s?\+\\sUpdate)"
        "|"
        r"(?:\\s?\+\\sDLC)"
        ")"
    )

    reg = re.findall(regex_str, f)

    # If we find something, then pull that out
    if len(reg) > 0:
        f = reg[0]

    return f


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
