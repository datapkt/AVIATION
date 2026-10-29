"""First-paint check for pages with inline critical CSS (<style id="dp-critical">).
For each such page, at phone (390x844) and laptop (1440x900):
  A. every non-blocking stylesheet (link[data-dp-css]) is held and never delivered -> what the visitor sees first;
  B. normal load -> final render.
The first screen in A must match B (<= 0.3% of pixels differ), so there is no flash of unstyled or shifted content.
Also checks: in A the page is not blank, the nav and h1 are visible, and the hero box already has its size.
Pages without the inline block are skipped. Exit 1 on failure."""
import os, sys, glob
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops

SITE = os.path.abspath(os.environ.get('DP_SITE', '.'))
OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/dp_tests'
os.makedirs(OUT, exist_ok=True)
PORT = int(os.environ.get('DP_PORT', '8803'))
LIMIT = 0.003
FREEZE = ("*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}"
          " .main-text label::before{content:'Operations'!important} #dp-cookie{display:none!important}"
          " img[src$='.gif'],video{visibility:hidden!important} .dp-wa,.whatsapp,.floating-wa{display:none!important}")
pages = sorted(f for f in glob.glob('**/*.html', root_dir=SITE, recursive=True)
               if not f.startswith(('src/', 'node_modules/', 'dist/', 'others/', 'vscode/'))
               and 'id="dp-critical"' in open(os.path.join(SITE, f), errors='ignore').read())
fails, held = [], []


def open_page(b, page, w, h, hold):
    c = b.new_context(viewport={'width': w, 'height': h})
    c.route(lambda u: not u.startswith(f'http://localhost:{PORT}'), lambda r: r.abort())
    c.route('**/*.lottie', lambda r: r.abort())
    if hold:
        c.route(lambda u: u.split('?')[0].endswith('.css'), lambda r: held.append(r))
    pg = c.new_page()
    pg.goto(f'http://localhost:{PORT}/{page}', wait_until='domcontentloaded' if hold else 'load')
    pg.add_style_tag(content=FREEZE)
    pg.wait_for_timeout(1500)
    return c, pg


with sync_playwright() as p:
    b = p.chromium.launch()
    for page in pages:
        for w, h in ((360, 740), (390, 844), (768, 1024), (1440, 900), (1920, 1080)):
            held.clear()
            ca, a = open_page(b, page, w, h, True)
            n_held = len(held)
            info = a.evaluate("""() => { const vis = e => e && e.getBoundingClientRect().height > 0 && getComputedStyle(e).visibility !== 'hidden';
               const navs = [...document.querySelectorAll('nav')].some(vis); const hero = document.querySelector('#main');
               return {nav: navs, h1: vis(document.querySelector('h1')), hero: hero ? hero.getBoundingClientRect().height : -1,
                       loaded: [...document.querySelectorAll('link[data-dp-css]')].filter(l => l.sheet && l.media === 'all').length}; }""")
            pa = f"{OUT}/firstpaint_held_{w}_{page.replace('/', '__')}.png"; a.screenshot(path=pa)
            ca.unroute_all(behavior='ignoreErrors'); ca.close()
            cb, bpg = open_page(b, page, w, h, False)
            pb = f"{OUT}/firstpaint_final_{w}_{page.replace('/', '__')}.png"; bpg.screenshot(path=pb)
            cb.close()
            if n_held == 0: fails.append(f'{page} @{w}: no stylesheet was held - test invalid')
            if info['loaded']: fails.append(f'{page} @{w}: held stylesheets reported as applied - test invalid')
            if not info['nav']: fails.append(f'{page} @{w}: nav not visible on first paint')
            if not info['h1']: fails.append(f'{page} @{w}: h1 not visible on first paint')
            if info['hero'] == 0: fails.append(f'{page} @{w}: hero has no height on first paint')
            A, B = Image.open(pa).convert('RGB'), Image.open(pb).convert('RGB')
            d = ImageChops.difference(A, B).point(lambda v: 255 if v > 24 else 0).convert('L')
            r = sum(d.histogram()[255:]) / (A.size[0] * A.size[1])
            msg = f'{page} @{w}: first paint vs final differ {r:.3%} (held {n_held} css), region {d.getbbox()}'
            (fails if r > LIMIT else []).append(msg); print(('FAIL ' if r > LIMIT else 'OK   ') + msg)
    b.close()
if not pages: print('NOTE no page has inline critical CSS; nothing to check')
for f in fails: print('FAIL', f)
print('FIRST PAINT:', 'PASS' if not fails else f'FAIL ({len(fails)})')
sys.exit(1 if fails else 0)
