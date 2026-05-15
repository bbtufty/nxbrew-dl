"""Live download test — uses TestClient to simulate real download requests"""
import os, sys, time

SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SRC_DIR)

from fastapi.testclient import TestClient
from cart_dl.server import app, _games_cache, _minerva_file_cache, _archive_file_cache, _minerva_ready, ALL_PLATFORMS

client = TestClient(app)

def run():
    print("=" * 60)
    print("  cart-dl Live Download Tests")
    print("=" * 60)
    print()

    # Step 1: Trigger cache build
    print("  [1] Loading game caches...")
    r = client.get('/api/games?limit=1')
    data = r.json()
    print(f"  Total games: {data['total']}")
    print()

    # Step 2: Show available platforms with game counts
    print("  [2] Platform availability:")
    r = client.get('/api/platforms')
    platforms = r.json()['platforms']
    for p in platforms:
        status = "+" if p['count'] > 0 else "-"
        print(f"    {status} {p['display']:25s} {p['count']:>6} games  methods={p['download_methods']}")
    print()

    # Step 3: Pick test games from different platforms
    print("  [3] Selecting test games...")
    test_games = []
    
    # Switch - pick first game
    r = client.get('/api/games?platform=switch&limit=1')
    sw = r.json()['games']
    if sw:
        test_games.append(('switch', sw[0]))
        print(f"    Switch: {sw[0]['name'][:60]}")
    
    # PS2 - pick first game
    r = client.get('/api/games?platform=ps2&limit=1')
    ps2 = r.json()['games']
    if ps2:
        test_games.append(('ps2', ps2[0]))
        print(f"    PS2:    {ps2[0]['name'][:60]}")
    
    # PS3 - pick first game
    r = client.get('/api/games?platform=ps3&limit=1')
    ps3 = r.json()['games']
    if ps3:
        test_games.append(('ps3', ps3[0]))
        print(f"    PS3:    {ps3[0]['name'][:60]}")
    
    # N64 - pick first game
    r = client.get('/api/games?platform=n64&limit=1')
    n64 = r.json()['games']
    if n64:
        test_games.append(('n64', n64[0]))
        print(f"    N64:    {n64[0]['name'][:60]}")
    
    # GBA - pick first game
    r = client.get('/api/games?platform=gba&limit=1')
    gba = r.json()['games']
    if gba:
        test_games.append(('gba', gba[0]))
        print(f"    GBA:    {gba[0]['name'][:60]}")
    
    print(f"\n  Selected {len(test_games)} games for download test")
    print()

    # Step 4: Show URL schemes
    print("  [4] URL scheme analysis:")
    for pk, game in test_games:
        url = game['url']
        scheme = url.split(':')[0] if ':' in url else 'http'
        print(f"    {pk:10s} -> {scheme:10s} -> {url[:80]}")
    print()

    # Step 5: Test download endpoint for each game
    print("  [5] Testing download endpoint...")
    for pk, game in test_games:
        url = game['url']
        name = game['name'][:50]
        
        # Reset download state
        client.post('/api/download/reset')
        
        # Trigger download
        r = client.post('/api/download', json={"games": [url]})
        status_code = r.status_code
        result = r.json() if r.status_code == 200 else r.text
        
        print(f"    {pk:10s} [{status_code}] {result}")
        
        # Wait a moment for download to start
        time.sleep(1)
        
        # Check download status
        r = client.get('/api/download/status')
        state = r.json()
        logs = state.get('log', [])
        for log in logs[-5:]:
            print(f"      {log}")
        print()

    # Step 6: Test multi-platform download
    print("  [6] Multi-platform download test...")
    urls = [g['url'] for _, g in test_games[:3]]  # First 3 games
    client.post('/api/download/reset')
    r = client.post('/api/download', json={"games": urls})
    print(f"    Status: {r.status_code} {r.json()}")
    
    time.sleep(2)
    r = client.get('/api/download/status')
    state = r.json()
    print(f"    Running: {state['running']}")
    print(f"    Progress: {state['current']}/{state['total']}")
    print(f"    Current game: {state['game']}")
    print(f"    Log entries: {len(state['log'])}")
    for log in state['log'][-10:]:
        print(f"      {log}")
    print()

    # Step 7: Test HTTP source modules directly
    print("  [7] Testing HTTP source modules...")
    
    # CoolROM
    try:
        from cart_dl.sources.http.coolrom import CoolROMSource
        cr = CoolROMSource()
        slug = cr.get_platform_slug('ps2')
        print(f"    CoolROM PS2 slug: {slug}")
    except Exception as e:
        print(f"    CoolROM error: {e}")
    
    # Vimm
    try:
        from cart_dl.sources.http.vimm import VimmSource
        vs = VimmSource()
        slug = vs.get_platform_slug('ps2')
        print(f"    Vimm PS2 slug: {slug}")
    except Exception as e:
        print(f"    Vimm error: {e}")
    
    # NoPayStation
    try:
        from cart_dl.sources.http.nopaystation import NoPayStationSource
        nps = NoPayStationSource()
        games = nps.list_games('ps3')
        print(f"    NoPayStation PS3 games: {len(games)} entries")
        if games:
            name, entry = games[0]
            print(f"      First: {name[:60]}")
            print(f"      PKG URL: {entry.get('pkg_url', 'N/A')[:80]}")
    except Exception as e:
        print(f"    NoPayStation error: {e}")
    
    print()

    # Step 8: Summary
    print("=" * 60)
    print("  Download test complete")
    print("=" * 60)

if __name__ == "__main__":
    run()
