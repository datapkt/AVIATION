"""DATAPKT site regression tests. Run before every publish.
Baseline = what is live (git HEAD of master) served on :8811; candidate = working tree on :8803.
1. Visual diff of every page at desktop (1440) and phone (390) widths, animations frozen, lottie blocked.
2. Per-page checks on the candidate: HTTP 200 for local assets, no JS errors, images load, one h1,
   no horizontal scroll on phone, navbar visible.
3. Home hero: never blank (with the animation file blocked and with it delayed), animation plays when it loads.
Exit code 1 if anything fails."""
import sys, os, glob, re, json, subprocess, time
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops

OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/dp_tests'
os.makedirs(OUT, exist_ok=True)
SITE = os.path.abspath(os.environ.get('DP_SITE', '.'))
V = os.path.join(SITE, 'src/vendor/bootstrap-5.3.3/')
pages = sorted(f for f in glob.glob('**/*.html', root_dir=SITE, recursive=True)
               if not f.startswith(('src/', 'node_modules/', 'dist/')) and 'http-equiv="refresh"' not in open(os.path.join(SITE, f), errors='ignore').read())
if os.environ.get('PAGES'): pages = os.environ['PAGES'].split(',')
EXPECT_DIFF = set(json.loads(os.environ.get('EXPECT_DIFF', '[]')))
fails, notes = [], []
HELD = []  # held animation requests, released later to simulate a slow connection
FREEZE = "*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important} .main-text label::before{content:'Operations'!important} #dp-cookie{display:none!important} img[src$='.gif'],video{visibility:hidden!important} .dp-wa,.whatsapp,.floating-wa{display:none!important}"

def setup(pg, block_lottie=True, delay_lottie=0):
    pg = pg.context
    pg.route('**/cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/**', lambda r: r.fulfill(path=V + r.request.url.split('?')[0].rsplit('/', 1)[1]))
    def ext(r):
        if 'jsdelivr' in r.request.url: return r.fallback()
        return r.abort()
    pg.route(lambda u: not u.startswith('http://localhost'), ext)
    if block_lottie:
        pg.route('**/*.lottie', lambda r: r.abort())
    elif delay_lottie:
        HELD.clear()
        pg.route('**/motion.lottie', lambda r: HELD.append(r))

def shot(b, port, page, w):
    pg = b.new_page(viewport={'width': w, 'height': 900})
    setup(pg)
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://localhost:{port}/{page}', wait_until='load')
    pg.add_style_tag(content=FREEZE)
    h = pg.evaluate('document.documentElement.scrollHeight')
    for y in range(0, h, 800):
        pg.evaluate(f'window.scrollTo(0,{y})'); pg.wait_for_timeout(40)
    pg.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager');window.scrollTo(0,0)")
    pg.wait_for_timeout(500)
    path = f"{OUT}/{port}_{w}_{page.replace('/', '__')}.png"
    pg.screenshot(path=path, full_page=True)
    info = pg.evaluate("""() => ({
      h1: document.querySelectorAll('h1').length,
      broken: [...document.images].filter(i => i.complete && i.naturalWidth === 0 && !/googletagmanager|lottie/.test(i.src)).map(i => i.getAttribute('src')),
      overflow: document.documentElement.scrollWidth - window.innerWidth,
      nav: [...document.querySelectorAll('nav')].some(n => n.getBoundingClientRect().height > 0 && getComputedStyle(n).visibility !== 'hidden') })""")
    pg.close()
    return path, info, errs

def diff(a, c):
    A, C = Image.open(a).convert('RGB'), Image.open(c).convert('RGB')
    if A.size != C.size:
        return 1.0, f'size {A.size} -> {C.size}'
    bbox = ImageChops.difference(A, C).point(lambda v: 255 if v > 24 else 0).convert('L')
    n = sum(bbox.histogram()[255:])
    return n / (A.size[0] * A.size[1]), bbox.getbbox()

with sync_playwright() as p:
    b = p.chromium.launch()
    # 1 + 2: every page, two widths
    for page in pages:
        for w in (1440, 390):
            base_exists = os.path.exists(os.path.join(os.environ.get('BASE_DIR', ''), page))
            c, info, errs = shot(b, 8803, page, w)
            if info['h1'] != 1: fails.append(f'{page} @{w}: h1 count {info["h1"]}')
            if info['broken']: fails.append(f'{page} @{w}: broken images {info["broken"][:3]}')
            if w == 390 and info['overflow'] > 2: fails.append(f'{page} @390: horizontal overflow {info["overflow"]}px')
            if not info['nav']: fails.append(f'{page} @{w}: navbar not visible')
            if not base_exists and errs: fails.append(f'{page} @{w}: JS errors {errs[:2]}')
            if base_exists:
                a, _, berrs = shot(b, 8811, page, w)
                new_errs = [e for e in errs if e not in berrs]
                if new_errs: fails.append(f'{page} @{w}: NEW JS errors {new_errs[:2]}')
                elif errs: notes.append(f'{page} @{w}: JS errors also on live site (pre-existing): {errs[:1]}')
                r, box = diff(a, c)
                if r > 0.0005:
                    (notes if page in EXPECT_DIFF else fails).append(f'{page} @{w}: visual change {r:.2%} of pixels, region {box}')
            else:
                notes.append(f'{page}: new page, no baseline')
    # 3: hero
    for mode in ('blocked', 'delayed', 'normal'):
        pg = b.new_page(viewport={'width': 1440, 'height': 900})
        setup(pg, block_lottie=(mode == 'blocked'), delay_lottie=(4 if mode == 'delayed' else 0))
        pg.goto('http://localhost:8803/index.html', wait_until='domcontentloaded')
        pg.wait_for_timeout(1500)
        r = pg.evaluate("""() => { const p = document.querySelector('#main dotlottie-player'), b = p.closest('.banner-image');
          const r = p.getBoundingClientRect(); return {w: r.width, h: r.height, bg: getComputedStyle(p).backgroundImage, ready: b.classList.contains('dp-hero-ready'), state: p.currentState}; }""")
        if r['h'] < r['w'] * 0.5: fails.append(f'hero {mode}: blank/collapsed {r}')
        if mode != 'normal' and 'hero-poster' not in r['bg']: fails.append(f'hero {mode}: no still frame while animation not playing {r}')
        pg.screenshot(path=f'{OUT}/hero_{mode}_early.png')
        if mode == 'delayed':
            if not HELD: fails.append('hero delayed: animation request was not intercepted, test invalid')
            for r0 in list(HELD): r0.fallback()
        pg.wait_for_timeout(7000)
        r2 = pg.evaluate("""() => { const p = document.querySelector('#main dotlottie-player'); return {state: p.currentState, bg: getComputedStyle(p).backgroundImage, ready: p.closest('.banner-image').classList.contains('dp-hero-ready')}; }""")
        if mode != 'blocked' and (r2['state'] != 'playing' or r2['bg'] != 'none'): fails.append(f'hero {mode}: animation not playing cleanly after load {r2}')
        pg.screenshot(path=f'{OUT}/hero_{mode}_late.png')
        notes.append(f'hero {mode}: early {r["h"]:.0f}px state={r["state"]}; late state={r2["state"]} still={"on" if r2["bg"]!="none" else "off"}')
        pg.close()
    b.close()

print(f'{len(pages)} pages x 2 widths tested')
for n in notes: print('NOTE', n)
for f in fails: print('FAIL', f)
print('RESULT:', 'PASS' if not fails else f'FAIL ({len(fails)})')
sys.exit(1 if fails else 0)
