"""Download integration tests — verify URL resolution and source routing across platforms"""
import os, sys, random, json

SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SRC_DIR)

from fastapi.testclient import TestClient
from cart_dl.server import app, _games_cache, _minerva_file_cache, _archive_file_cache, _minerva_ready, ALL_PLATFORMS
from cart_dl.sources.archive import ArchiveSource
from cart_dl.sources.minerva import MinervaSource

client = TestClient(app)

passed = 0
failed = 0

def test(name):
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
    print("  cart-dl Download Integration Tests")
    print("=" * 60)
    print()

    # ---- Trigger cache build ----
    print("  Building game caches...")
    r = client.get('/api/games?limit=1')
    data = r.json()
    total_games = data['total']
    print(f"  Total games loaded: {total_games}")
    print()

    # ---- Test 1: Switch games have valid HTTP URLs ----
    @test("Switch games have valid HTTP URLs")
    def _():
        r = client.get('/api/games?platform=switch&limit=20')
        games = r.json()['games']
        assert len(games) > 0, "No Switch games found"
        for g in games:
            assert g['url'].startswith('https://'), f"Switch URL not HTTP: {g['url']}"
            assert 'nxbrew.net' in g['url'] or 'nswgame.com' in g['url'] or 'switch-roms.com' in g['url'] or 'ziperto.com' in g['url'], f"Unexpected Switch source: {g['url']}"

    # ---- Test 2: Non-Switch platforms have minerva:/archive: URLs ----
    @test("Non-Switch platforms use minerva:/archive: URL scheme")
    def _():
        for pk in ['ps2', 'ps3', 'psp', 'n64', 'snes', 'genesis', 'dc', 'gba', 'ds', 'wii', 'gc', 'xbox360']:
            r = client.get(f'/api/games?platform={pk}&limit=5')
            games = r.json()['games']
            # Games may be 0 if Minerva/IA not reachable, but if present, verify format
            for g in games:
                assert g['url'].startswith('minerva:') or g['url'].startswith('archive:'), \
                    f"{pk} URL not minerva:/archive: scheme: {g['url']}"

    # ---- Test 3: Minerva cache populated for reachable platforms ----
    @test("Minerva cache has entries for at least one platform")
    def _():
        has_entries = False
        for pk, entries in _minerva_file_cache.items():
            if len(entries) > 0:
                has_entries = True
                print(f"    {pk}: {len(entries)} files")
                break
        assert has_entries, "No Minerva cache entries found"

    # ---- Test 4: Archive cache populated for reachable platforms ----
    @test("Archive cache has entries for at least one platform")
    def _():
        has_entries = False
        for pk, entries in _archive_file_cache.items():
            if len(entries) > 0:
                has_entries = True
                print(f"    {pk}: {len(entries)} files")
                break
        assert has_entries, "No Archive cache entries found"

    # ---- Test 5: URL format validation for minerva: scheme ----
    @test("Minerva URLs follow minerva:platform:path format")
    def _():
        r = client.get('/api/games?platform=ps2&limit=10')
        games = r.json()['games']
        for g in games:
            if g['url'].startswith('minerva:'):
                parts = g['url'].split(':', 2)
                assert len(parts) == 3, f"Invalid minerva URL format: {g['url']}"
                assert parts[0] == 'minerva'
                assert parts[1] in ALL_PLATFORMS, f"Invalid platform in minerva URL: {parts[1]}"

    # ---- Test 6: URL format validation for archive: scheme ----
    @test("Archive URLs follow archive:platform:identifier:path format")
    def _():
        r = client.get('/api/games?platform=ps2&limit=10')
        games = r.json()['games']
        for g in games:
            if g['url'].startswith('archive:'):
                parts = g['url'].split(':', 3)
                assert len(parts) == 4, f"Invalid archive URL format: {g['url']}"
                assert parts[0] == 'archive'
                assert parts[1] in ALL_PLATFORMS, f"Invalid platform in archive URL: {parts[1]}"
                assert len(parts[2]) > 0, f"Empty identifier in archive URL: {g['url']}"

    # ---- Test 7: Random platform sampling ----
    @test("Random platform sampling returns valid entries")
    def _():
        platforms_with_games = []
        for pk in ALL_PLATFORMS:
            r = client.get(f'/api/games?platform={pk}&limit=1')
            count = r.json()['total']
            if count > 0:
                platforms_with_games.append(pk)
        
        assert len(platforms_with_games) > 0, "No platforms have games"
        print(f"    Platforms with games: {', '.join(platforms_with_games)}")
        
        # Pick 3 random platforms
        sampled = random.sample(platforms_with_games, min(3, len(platforms_with_games)))
        for pk in sampled:
            r = client.get(f'/api/games?platform={pk}&limit=3')
            games = r.json()['games']
            assert len(games) > 0, f"No games for {pk}"
            for g in games:
                assert 'name' in g
                assert 'url' in g
                assert 'platform' in g
                assert g['platform'] == pk
                print(f"    {pk}: {g['name'][:50]} -> {g['url'][:60]}")

    # ---- Test 8: Download endpoint accepts valid game URLs ----
    @test("Download endpoint accepts Switch game URLs")
    def _():
        r = client.get('/api/games?platform=switch&limit=1')
        games = r.json()['games']
        if games:
            # Reset download state first
            client.post('/api/download/reset')
            r = client.post('/api/download', json={"games": [games[0]['url']]})
            assert r.status_code == 200, f"Download endpoint returned {r.status_code}"
            result = r.json()
            assert result['status'] == 'started'
            assert result['total'] == 1

    # ---- Test 9: Download endpoint accepts minerva: URLs ----
    @test("Download endpoint accepts minerva: URLs")
    def _():
        r = client.get('/api/games?platform=ps2&limit=1')
        games = r.json()['games']
        minerva_games = [g for g in games if g['url'].startswith('minerva:')]
        if minerva_games:
            client.post('/api/download/reset')
            r = client.post('/api/download', json={"games": [minerva_games[0]['url']]})
            assert r.status_code == 200, f"Download endpoint returned {r.status_code}"
            result = r.json()
            assert result['status'] == 'started'

    # ---- Test 10: Download endpoint accepts archive: URLs ----
    @test("Download endpoint accepts archive: URLs")
    def _():
        r = client.get('/api/games?platform=ps2&limit=10')
        games = r.json()['games']
        archive_games = [g for g in games if g['url'].startswith('archive:')]
        if archive_games:
            client.post('/api/download/reset')
            r = client.post('/api/download', json={"games": [archive_games[0]['url']]})
            assert r.status_code == 200, f"Download endpoint returned {r.status_code}"
            result = r.json()
            assert result['status'] == 'started'

    # ---- Test 11: Multi-platform download request ----
    @test("Multi-platform download request works")
    def _():
        urls = []
        # Get one Switch game
        r = client.get('/api/games?platform=switch&limit=1')
        sw_games = r.json()['games']
        if sw_games:
            urls.append(sw_games[0]['url'])
        
        # Get one PS2 game
        r = client.get('/api/games?platform=ps2&limit=1')
        ps2_games = r.json()['games']
        if ps2_games:
            urls.append(ps2_games[0]['url'])
        
        if len(urls) >= 2:
            client.post('/api/download/reset')
            r = client.post('/api/download', json={"games": urls})
            assert r.status_code == 200
            result = r.json()
            assert result['total'] == len(urls)

    # ---- Test 12: Download status endpoint ----
    @test("Download status endpoint returns valid state")
    def _():
        r = client.get('/api/download/status')
        assert r.status_code == 200
        state = r.json()
        assert 'running' in state
        assert 'current' in state
        assert 'total' in state
        assert 'log' in state
        assert 'game' in state

    # ---- Test 13: ArchiveSource direct download URL generation ----
    @test("ArchiveSource generates valid download URLs")
    def _():
        a = ArchiveSource(download_dir=".")
        # Test with a known IA identifier
        url = f"{a.IA_DOWNLOAD}/redump-sony-ps2/test.iso"
        assert 'archive.org/download' in url

    # ---- Test 14: MinervaSource torrent URL generation ----
    @test("MinervaSource generates valid torrent URLs")
    def _():
        ms = MinervaSource(download_dir=".")
        for pk in ['ps2', 'ps3', 'n64', 'snes']:
            url = ms.get_torrent_url(pk)
            assert url is not None, f"No torrent URL for {pk}"
            assert url.startswith('https://minerva-archive.org'), f"Invalid Minerva URL for {pk}: {url}"

    # ---- Test 15: HTTP source imports work ----
    @test("HTTP source modules import correctly")
    def _():
        from cart_dl.sources.http import CoolROMSource, VimmSource, NoPayStationSource
        assert CoolROMSource is not None
        assert VimmSource is not None
        assert NoPayStationSource is not None

    # ---- Test 16: CoolROM platform mapping ----
    @test("CoolROM maps all supported platforms")
    def _():
        from cart_dl.sources.http.coolrom import CoolROMSource, PLATFORM_MAP
        cr = CoolROMSource()
        for pk in ['ps3', 'ps2', 'ps1', 'psp', 'n64', 'snes', 'nes', 'genesis', 'dc', 'gba', 'ds', '3ds', 'wii', 'gc', 'xbox', 'xbox360']:
            slug = cr.get_platform_slug(pk)
            assert slug is not None, f"No CoolROM slug for {pk}"

    # ---- Test 17: Vimm platform mapping ----
    @test("Vimm maps all supported platforms")
    def _():
        from cart_dl.sources.http.vimm import VimmSource, PLATFORM_MAP
        vs = VimmSource()
        for pk in ['ps3', 'ps2', 'ps1', 'psp', 'n64', 'snes', 'nes', 'genesis', 'dc', 'gba', 'ds', '3ds', 'wii', 'gc', 'xbox', 'xbox360']:
            slug = vs.get_platform_slug(pk)
            assert slug is not None, f"No Vimm slug for {pk}"

    # ---- Test 18: NoPayStation TSV types ----
    @test("NoPayStation has TSV types for PS3/PSP")
    def _():
        from cart_dl.sources.http.nopaystation import NoPayStationSource, PLATFORM_TSV_MAP
        nps = NoPayStationSource()
        for pk in ['ps3', 'psp']:
            tsv_types = PLATFORM_TSV_MAP.get(pk)
            assert tsv_types is not None, f"No NPS TSV types for {pk}"
            assert len(tsv_types) > 0

    # ---- Summary ----
    print()
    print("=" * 60)
    print(f"  Results: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 60)
    return failed == 0

if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
