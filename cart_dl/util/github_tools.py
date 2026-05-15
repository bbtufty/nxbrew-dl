import requests


def check_github_version():
    """Check for new versions"""

    url = "https://git.johagan.au/api/v1/repos/jack/cart-dl/releases/latest"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        version = data.get("tag_name", "0.0.0").lstrip("v")
        github_url = data.get("html_url", "")
        return version, github_url
    except Exception:
        return "0.0.0", ""
