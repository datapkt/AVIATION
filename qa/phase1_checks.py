"""Phase 1 checks: baseline (:8811, live) vs candidate (:8803).
1. Space reservation: with image downloads blocked, count <img> that collapse to 0 px
   height at phone width. Candidate must collapse fewer (never more) than baseline.
2. Rendered size: with images loaded, every image's rendered box must be the same
   in baseline and candidate (proves width/height attributes changed nothing visually).
3. Landmarks/labels: exactly one <main>; form fields named; map iframe titled; logo links named.
"""
import glob, os, sys, json
from playwright.sync_api import sync_playwright

SITE = os.path.abspath(os.environ.get('DP_SITE', '.'))
V = os.path.join(SITE, 'src/vendor/bootstrap-5.3.3/')
pages = sorted(f for f in glob.glob('**/*.html', root_dir=SITE, recursive=True)
               if not f.startswith(('src/', 'node_modules/', 'dist/', 'others/', 'vscode/'))
               and 'http-equiv="refresh"' not in open(os.path.join(SITE, f), errors='ignore').read())
if os.environ.get('PAGES'): pages = os.environ['PAGES'].split(',')

fails = []


def ctx(b, w, block_images):
    c = b.new_context(viewport={'width': w, 'height': 900})
    c.route('**/cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/**', lambda r: r.fulfill(path=V + r.request.url.split('?')[0].rsplit('/', 1)[1]))
    c.route(lambda u: not u.startswith('http://localhost') and 'jsdelivr' not in u, lambda r: r.abort())
    c.route('**/*.lottie', lambda r: r.abort())
    if block_images:
        HELD = []  # never answered: images stay in the 'still loading' state
        c.route(lambda u: u.split('?')[0].lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg')), lambda r: HELD.append(r))
    return c


JS_BOXES = """() => [...document.images].map(i => { const r = i.getBoundingClientRect();
  const cs = getComputedStyle(i); return [i.getAttribute('src'), Math.round(r.width), Math.round(r.height), cs.display !== 'none' && cs.visibility !== 'hidden'] })"""
JS_A11Y = """() => ({
  mains: document.querySelectorAll('main,[role=main]').length,
  unnamedFields: [...document.querySelectorAll('input:not([type=hidden]):not([type=submit]):not([aria-hidden=true]),textarea,select')]
     .filter(e => !(e.labels && e.labels.length) && !e.getAttribute('aria-label') && !e.getAttribute('aria-labelledby')).map(e => e.id || e.name),
  untitledFrames: [...document.querySelectorAll('iframe')].filter(f => !f.title).length,
  unnamedLinks: [...document.querySelectorAll('a[href]')].filter(a => !a.textContent.trim() && !a.getAttribute('aria-label')
     && !a.querySelector('img[alt]:not([alt=""]),[aria-label],svg title')).map(a => a.getAttribute('href')).slice(0, 5) })"""

with sync_playwright() as p:
    b = p.chromium.launch()
    totals = {'base_collapsed': 0, 'cand_collapsed': 0, 'size_mismatch': 0}
    for page in pages:
        res = {}
        for port in (8811, 8803):
            # 1. blocked images, phone width
            c = ctx(b, 390, True); pg = c.new_page()
            pg.goto(f'http://localhost:{port}/{page}', wait_until='domcontentloaded'); pg.wait_for_timeout(1200)
            boxes = pg.evaluate(JS_BOXES)
            collapsed = sum(1 for s, w, h, vis in boxes if vis and h == 0)
            a11y = pg.evaluate(JS_A11Y) if port == 8803 else None
            c.close()
            # 2. loaded images, desktop + phone rendered sizes
            sizes = []
            for w in (1440, 390):
                c = ctx(b, w, False); pg = c.new_page()
                pg.goto(f'http://localhost:{port}/{page}', wait_until='load')
                pg.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager')")
                pg.wait_for_timeout(800)
                sizes.append(pg.evaluate(JS_BOXES)); c.close()
            res[port] = (collapsed, sizes, a11y)
        bc, bs, _ = res[8811]; cc, cs, a = res[8803]
        if not os.path.exists(os.path.join(os.environ.get('BASE_DIR', ''), page)):
            bc, bs = cc, cs   # new page: nothing live to compare with; landmark/label checks below still apply
        totals['base_collapsed'] += bc; totals['cand_collapsed'] += cc
        if cc > bc:
            fails.append(f'{page}: more collapsed images than live ({cc} > {bc})')
        for wi, (bl, cl) in enumerate(zip(bs, cs)):
            if len(bl) != len(cl):
                fails.append(f'{page}: image count differs at width {(1440, 390)[wi]}'); continue
            for x, y in zip(bl, cl):
                if x[3] and (abs(x[1] - y[1]) > 1 or abs(x[2] - y[2]) > 1):
                    totals['size_mismatch'] += 1
                    fails.append(f'{page} @{(1440, 390)[wi]}: {x[0]} live {x[1]}x{x[2]} vs new {y[1]}x{y[2]}')
        if a['mains'] != 1: fails.append(f'{page}: {a["mains"]} main landmarks')
        if a['unnamedFields']: fails.append(f'{page}: unnamed form fields {a["unnamedFields"]}')
        if a['untitledFrames']: fails.append(f'{page}: {a["untitledFrames"]} iframe(s) without title')
        if a['unnamedLinks']: fails.append(f'{page}: links without a name {a["unnamedLinks"]}')
        print(f'{page}: collapsed live {bc} -> new {cc}; main {a["mains"]}', flush=True)
    b.close()
print(json.dumps(totals))
print('\n'.join(fails) if fails else 'PHASE 1 CHECKS: PASS')
sys.exit(1 if fails else 0)
