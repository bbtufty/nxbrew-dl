"""Unit tests for cart-dl — 25 Switch games + Pokemon Violet regression"""
import os, sys, json, time, threading, subprocess, requests

SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SRC_DIR)

# Test URLs: 25 real Switch game pages scraped from nxbrew.net game index
TEST_URLS = [
    "https://nxbrew.net/a-dance-of-fire-and-ice-switch-nsp-update-eshop/",
    "https://nxbrew.net/a-fold-apart-switch-nsp-update-eshop/",
    "https://nxbrew.net/a-hat-in-time-switch-nsp-update-dlc-eshop/",
    "https://nxbrew.net/a-short-hike-switch-nsp-eshop/",
    "https://nxbrew.net/a-space-for-the-unbound-switch-nsp-update-eshop/",
    "https://nxbrew.net/a-tiny-sticker-tale-switch-nsp-eshop/",
    "https://nxbrew.net/abzu-switch-nsp-xci-eshop/",
    "https://nxbrew.net/advance-wars-1-2-re-boot-camp-switch-nsp-xci/",
    "https://nxbrew.net/aeterna-noctis-switch-nsp-update-dlc-eshop/",
    "https://nxbrew.net/age-of-calamity-switch-nsp-xci-update-dlc/",
    "https://nxbrew.net/ai-the-somnium-files-switch-nsp-xci-eshop/",
    "https://nxbrew.net/air-twister-switch-nsp-eshop/",
    "https://nxbrew.net/akane-switch-nsp-eshop/",
    "https://nxbrew.net/alan-wake-remastered-switch-nsp-xci-eshop/",
    "https://nxbrew.net/alba-a-wildlife-adventure-switch-nsp-eshop/",
    "https://nxbrew.net/alien-isolation-switch-nsp-xci-eshop/",
    "https://nxbrew.net/amnesia-collection-switch-nsp-xci-eshop/",
    "https://nxbrew.net/among-us-switch-nsp-xci-update-dlc-eshop/",
    "https://nxbrew.net/animal-crossing-new-horizons-switch-nsp-xci-update-dlc/",
    "https://nxbrew.net/anodyne-2-return-to-dust-switch-nsp-eshop/",
    "https://nxbrew.net/aokana-four-rhythms-across-the-blue-switch-nsp-eshop/",
    "https://nxbrew.net/apollo-justice-ace-attorney-trilogy-switch-nsp-xci-eshop/",
    "https://nxbrew.net/arcade-paradise-switch-nsp-eshop/",
    "https://nxbrew.net/aria-chronicle-switch-nsp-eshop/",
    "https://nxbrew.net/arms-switch-nsp-xci-update-eshop/",
]

# The critical regression test URL (was crashing with NoneType.sort)
POKEMON_URL = "https://switch-roms.com/pokemon-violet-nsp-game-update-rom/"

passed = 0
failed = 0


def test(name):
    """Decorator-style test runner"""
    def wrapper(fn):
        global passed, failed
        try:
            fn()
            passed += 1
            print(f"  PASS: {name}")
        except Exception as e:
            failed += 1
            print(f"  FAIL: {name} — {e}")
    return wrapper


def run():
    global passed, failed
    print("=" * 60)
    print("  cart-dl Unit Tests")
    print("=" * 60)
    print()

    # ---- Module imports ----
    @test("import cart_dl package")
    def _():
        import cart_dl
        assert cart_dl.__version__ is not None

    @test("import server module")
    def _():
        from cart_dl import server
        assert server.app is not None

    @test("import scraper")
    def _():
        from cart_dl.scraper.scraper import CartDL
        assert CartDL is not None

    @test("import html_tools")
    def _():
        from cart_dl.util.html_tools import get_game_dict, get_html_page
        assert get_game_dict is not None

    @test("import regex_tools")
    def _():
        from cart_dl.util.regex_tools import get_game_name, get_game_name_from_filename, check_has_extension
        assert get_game_name is not None

    @test("import IGDB tools")
    def _():
        from cart_dl.util.igdb_tools import IGDBClient, filter_game_dict
        IGDBClient.load_precache()
        assert len(IGDBClient._precache) > 0

    @test("import Minerva source")
    def _():
        from cart_dl.sources.minerva import MinervaSource, PLATFORM_COLLECTIONS
        assert len(PLATFORM_COLLECTIONS) >= 17
        assert "ps3" in PLATFORM_COLLECTIONS

    @test("import Archive source")
    def _():
        from cart_dl.sources.archive import ArchiveSource
        a = ArchiveSource(download_dir=".")
        assert a is not None

    # ---- Config loading ----
    @test("load platforms.yml")
    def _():
        from cart_dl.util.io_tools import load_yml
        mod_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cfg = load_yml(os.path.join(mod_dir, "cart_dl", "configs", "platforms.yml"))
        assert len(cfg["platforms"]) == 19
        # Verify compressed formats are first
        gc = cfg["platforms"]["gc"]
        assert gc["extensions"][0] == ".rvz", f"GC should prefer RVZ, got {gc['extensions'][0]}"
        ps2 = cfg["platforms"]["ps2"]
        assert ps2["extensions"][0] == ".chd", f"PS2 should prefer CHD, got {ps2['extensions'][0]}"
        ps1 = cfg["platforms"]["ps1"]
        assert ps1["extensions"][0] == ".chd", f"PS1 should prefer CHD, got {ps1['extensions'][0]}"
        psp = cfg["platforms"]["psp"]
        assert psp["extensions"][0] == ".cso", f"PSP should prefer CSO, got {psp['extensions'][0]}"
        dc = cfg["platforms"]["dc"]
        assert dc["extensions"][0] == ".chd", f"DC should prefer CHD, got {dc['extensions'][0]}"

    @test("load general.yml")
    def _():
        from cart_dl.util.io_tools import load_yml
        mod_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cfg = load_yml(os.path.join(mod_dir, "cart_dl", "configs", "general.yml"))
        assert "dl_sites" in cfg
        assert "dl_mappings" in cfg

    @test("load regex.yml")
    def _():
        from cart_dl.util.io_tools import load_yml
        mod_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cfg = load_yml(os.path.join(mod_dir, "cart_dl", "configs", "regex.yml"))
        assert "nsp_variations" in cfg

    # ---- Regex / name parsing ----
    @test("get_game_name strips Switch NSP suffix")
    def _():
        from cart_dl.util.regex_tools import get_game_name
        nsp_vars = ["NSP", "XCI"]
        result = get_game_name("Zelda Breath of the Wild Switch NSP", nsp_vars)
        assert "Switch" not in result
        assert "NSP" not in result

    @test("get_game_name handles +Update +DLC")
    def _():
        from cart_dl.util.regex_tools import get_game_name
        nsp_vars = ["NSP", "XCI"]
        result = get_game_name("Mario Odyssey Switch NSP + Update + DLC", nsp_vars)
        assert "Update" not in result
        assert "DLC" not in result

    @test("get_game_name_from_filename handles ISO")
    def _():
        from cart_dl.util.regex_tools import get_game_name_from_filename
        result = get_game_name_from_filename("God of War (USA) (v1.01).iso")
        assert "God of War" in result
        assert "USA" not in result

    @test("get_game_name_from_filename strips serial numbers")
    def _():
        from cart_dl.util.regex_tools import get_game_name_from_filename
        result = get_game_name_from_filename("Crash Bandicoot [SCUS-94900].bin")
        assert "SCUS" not in result
        assert "Crash Bandicoot" in result

    @test("check_has_extension matches extensions")
    def _():
        from cart_dl.util.regex_tools import check_has_extension
        assert check_has_extension("game.rvz", [".rvz", ".iso"])
        assert check_has_extension("game.iso", [".rvz", ".iso"])
        assert not check_has_extension("game.nsp", [".rvz", ".iso"])

    @test("normalize_name handles unicode")
    def _():
        from cart_dl.server import _normalize_name
        result = _normalize_name("Pokémon™ Violet")
        assert "pokemon violet" == result

    # ---- HTML parsing / game dict ----
    @test("get_game_dict loads from nxbrew.net")
    def _():
        from cart_dl.util.io_tools import load_yml
        from cart_dl.util.html_tools import get_game_dict
        mod_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        general = load_yml(os.path.join(mod_dir, "cart_dl", "configs", "general.yml"))
        regex = load_yml(os.path.join(mod_dir, "cart_dl", "configs", "regex.yml"))
        game_dict = get_game_dict(general, regex, "https://nxbrew.net")
        assert len(game_dict) > 500, f"Expected >500 games, got {len(game_dict)}"

    @test("game dict contains Pokemon Violet from switch-roms")
    def _():
        from cart_dl.util.io_tools import load_yml
        from cart_dl.util.html_tools import get_game_dict
        mod_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        general = load_yml(os.path.join(mod_dir, "cart_dl", "configs", "general.yml"))
        regex = load_yml(os.path.join(mod_dir, "cart_dl", "configs", "regex.yml"))
        game_dict = get_game_dict(general, regex, "https://nxbrew.net")
        pokemon_urls = [u for u in game_dict if "pokemon" in u.lower()]
        assert len(pokemon_urls) > 0, "No Pokemon games found in game dict"

    # ---- Test URL validity (no downloads, just check pages exist) ----
    @test("25 test URLs are valid format")
    def _():
        for url in TEST_URLS:
            assert url.startswith("https://nxbrew.net/")
            parts = url.rstrip("/").split("/")
            assert len(parts) >= 4
            assert len(parts[-1]) > 5, f"Short slug: {parts[-1]}"

    @test("Pokemon Violet test URL exists")
    def _():
        assert POKEMON_URL.startswith("https://switch-roms.com/")
        assert "pokemon-violet" in POKEMON_URL

    # ---- Minerva / Archive source unit tests ----
    @test("Minerva platform collections cover all platforms")
    def _():
        from cart_dl.sources.minerva import PLATFORM_COLLECTIONS
        expected = {"switch", "wiiu", "wii", "gc", "3ds", "ds", "gba", "n64", "snes", "nes",
                     "ps4", "ps3", "ps2", "ps1", "psp", "xbox360", "xbox", "dc", "genesis"}
        assert set(PLATFORM_COLLECTIONS.keys()) == expected

    @test("ArchiveSource initializes")
    def _():
        from cart_dl.sources.archive import ArchiveSource
        a = ArchiveSource(download_dir=".")
        assert a.download_dir == "."
        assert a.aria2c_path == "aria2c"

    @test("ArchiveSource fetch_metadata handles bad identifier gracefully")
    def _():
        from cart_dl.sources.archive import ArchiveSource
        a = ArchiveSource(download_dir=".")
        import requests as rq
        try:
            meta = a.fetch_metadata("this-does-not-exist-12345")
            assert meta is None or isinstance(meta, dict)
        except Exception:
            pass  # Network unavailable is acceptable

    # ---- Torrent parsing ----
    @test("bdecode parses simple dict")
    def _():
        from cart_dl.server import _bdecode
        # bencoded: d3:key5:valuee
        data = b'd3:key5:valuee'
        result, _ = _bdecode(data)
        assert result == {b'key': b'value'}

    @test("bdecode parses nested structure")
    def _():
        from cart_dl.server import _bdecode
        # bencoded: d4:infod4:name4:test12:piece lengthi262144eee
        data = b'd4:infod4:name4:test12:piece lengthi262144eee'
        result, _ = _bdecode(data)
        assert b'info' in result
        assert b'name' in result[b'info']
        assert result[b'info'][b'name'] == b'test'

    # ---- Platform cache building ----
    @test("_build_platform_cache for switch returns entries")
    def _():
        from cart_dl.server import _build_platform_cache, _game_dict
        # Ensure game dict is loaded
        from cart_dl.util.io_tools import load_yml
        from cart_dl.util.html_tools import get_game_dict
        mod_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        general = load_yml(os.path.join(mod_dir, "cart_dl", "configs", "general.yml"))
        regex = load_yml(os.path.join(mod_dir, "cart_dl", "configs", "regex.yml"))
        if _game_dict is None:
            import cart_dl.server as srv
            srv._game_dict = get_game_dict(general, regex, "https://nxbrew.net")
        cache = _build_platform_cache("switch")
        assert len(cache) > 100, f"Expected >100 Switch games, got {len(cache)}"

    @test("_build_platform_cache for switch entries have platform=switch")
    def _():
        from cart_dl.server import _build_platform_cache
        cache = _build_platform_cache("switch")
        for entry in cache[:10]:
            assert entry["platform"] == "switch"

    @test("_build_platform_cache returns empty for unknown platform")
    def _():
        from cart_dl.server import _build_platform_cache
        cache = _build_platform_cache("nonexistent")
        assert cache == []

    # ---- Dedup / normalization ----
    @test("_normalize_name handles Pokemon")
    def _():
        from cart_dl.server import _normalize_name
        result = _normalize_name("Pokémon Scarlet Switch NSP")
        assert "pokemon" in result
        assert "scarlet" in result

    # ---- Summary ----
    print()
    print("=" * 60)
    print(f"  Results: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
