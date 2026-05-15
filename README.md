# cart-dl

[![](https://img.shields.io/pypi/v/cart-dl.svg?label=PyPI&style=flat-square)](https://pypi.org/pypi/cart-dl/)
[![](https://img.shields.io/pypi/pyversions/cart-dl.svg?label=Python&color=yellow&style=flat-square)](https://pypi.org/pypi/cart-dl/)
[![Docs](https://readthedocs.org/projects/cart-dl/badge/?version=latest&style=flat-square)](https://cart-dl.readthedocs.io/en/latest/)
[![Actions](https://img.shields.io/github/actions/workflow/status/bbtufty/cart-dl/build.yaml?branch=main&style=flat-square)](https://github.com/bbtufty/cart-dl/actions)
[![License](https://img.shields.io/badge/license-GNUv3-blue.svg?label=License&style=flat-square)](LICENSE)

cart-dl is intended to be an easy-to-user interface to download ROMs, DLC and update files for NSP. It does so via
a GUI interface, allowing users to download items in bulk and keeping things up-to-date.

As of now, this is in extremely early development. It will parse and download many ROMs, and by default will only
grab ROMs from either the USA or Europe (USA preferred) that are marked as having English language releases.

## Installation

We recommend using the executable version. You can grab the latest release from the [releases page](https://github.com/bbtufty/cart-dl/releases). Place the 
.exe wherever you want, and double-click to load.

Alternatively, you can install via pip:
```shell
pip install cart-dl
```
Or download the latest from GitHub:
```shell
git clone https://github.com/bbtufty/cart-dl.git
cd cart-dl
pip install -e . -r requirements.txt
```
If you use these versions, you can then run from the terminal as:
```shell
cart-dl
```

## 

To get things set up, see the [documentation](https://cart-dl.readthedocs.io/en/latest/).

We encourage users to open [issues](https://github.com/bbtufty/cart-dl/issues>) as and where they find them.

## Recent Fixes (2026-05-14)

### Cloudflare/Anti-Bot Bypass
The scraper now uses `curl_cffi` with TLS fingerprint impersonation instead of plain `requests`. This bypasses Cloudflare and adblock detection on CartDL domains. Impersonation profiles are auto-selected per domain:
- `CartDL.net` → Chrome
- `CartDL.me` → Safari 15.5

### Multi-Domain Game Index Aggregation
The site migrated from `CartDL.me` to `CartDL.net`, but not all games were migrated. The scraper now aggregates games from both:
- Primary: `{CartDL_url}/game-index/` (AlphaListing plugin format, ~1293 games)
- Alternative: `CartDL.me/games/` (entry-content list format, ~168 additional games)
- **Total: ~1,461 games**

### Updated Index Parsing
The CartDL.net site replaced its old `div#easyindex-index > li` structure with a WordPress AlphaListing plugin (`div.az-listing > div.letter-section > ul.az-columns > li > a`). The parser now supports both formats with automatic fallback.

### Known Limitations
- `CartDL.me` uses JavaScript-obfuscated download buttons (`onclick="downloadFile(n)"`) - individual game pages on this domain cannot be scraped. Only games hosted on `CartDL.net` support full end-to-end download.
- URL validation in the GUI now uses `curl_cffi` with impersonation for connectivity checks.

### Configuration
Set `source_url` in `config.yml` to your primary ROM source (e.g. `https://nxbrew.net`).

## IGDB Integration (NEW)

The app can optionally enrich and filter the game library using [IGDB](https://www.igdb.com/) ratings and metadata. This helps build a quality library by excluding shovelware, visual novels, and low-rated games.

### Setup
1. Create a Twitch Developer application at https://dev.twitch.tv/console/apps
2. Copy your **Client ID** and **Client Secret**
3. Enter them in the cart-dl GUI under "IGDB Filtering"
4. Click **Refresh** to re-scrape with IGDB enrichment

### Filtering Options
| Setting | Default | Description |
|---------|---------|-------------|
| Min Rating | 50/100 | Exclude games below this IGDB rating |
| Exclude Visual Novels | On | Filter out visual novel genre |
| Exclude Shovelware | On | Filter out puzzle, quiz, board game, educational shovelware |
| Switch Only | On | Only show games confirmed to have a Switch release on IGDB |

### Rating Column
A **Rating** column shows each game's IGDB score (0-100) color-coded:
- 🟢 Green: 80+
- 🟠 Orange: 60-79
- 🔴 Red: Below 60
- ⚪ Grey: Not found on IGDB

Results are cached in `igdb_cache.json` to avoid repeated API calls.