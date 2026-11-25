"""Iterative per-page critical CSS: mark above-fold rules at 5 viewports, apply, then check the held (critical-only)
page in mobile emulation for horizontal overflow; overflowing elements (and ancestors) get their rules added; repeat."""
import sys, json, os, subprocess, shutil
from playwright.sync_api import sync_playwright
GEN, CHK = 8821, 8832
T = '/home/claude/fp-tools'
JS = open(f'{T}/mark.js').read()
subprocess.check_call(['node', f'{T}/css.js', 'parse', '/home/claude/fp-base'], cwd=T, env=dict(os.environ, OUT=f'{T}/rules.json'))
rules = json.load(open(f'{T}/rules.json'))
OVF = """() => { const W=document.documentElement.clientWidth, all=[...document.querySelectorAll('body *')]; const out=[];
  all.forEach((e,i)=>{const r=e.getBoundingClientRect(); if(r.width>0 && (r.right>W+1 || r.left< -1) && getComputedStyle(e).position!=='fixed') out.push(i)}); return [innerWidth, out]; }"""
VPS = ((360, 740), (390, 844), (768, 1024), (1440, 900), (1920, 1080))
MOB = ((360, 740), (390, 844), (412, 823), (430, 932))
pages = open(sys.argv[2]).read().split()
result = {}
with sync_playwright() as p:
    b = p.chromium.launch()
    def ctx(w, h, mob, port):
        c = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1.75 if mob else 1, is_mobile=mob, has_touch=mob)
        c.route(lambda u: not u.startswith(f'http://localhost:{port}'), lambda r: r.abort()); return c
    for page in pages:
        extra = set(); it = 0
        while True:
            it += 1; k = set()
            for vp in [(w, h, False) for w, h in VPS] + [(w, h, True) for w, h in MOB]:
                c = ctx(vp[0], vp[1], vp[2], GEN); pg = c.new_page()
                pg.goto(f'http://localhost:{GEN}/{page}', wait_until='load'); pg.wait_for_timeout(300)
                k |= set(pg.evaluate(JS, {'rules': rules, 'extra': sorted(extra)})); c.close()
            json.dump({page: sorted(k)}, open(f'{T}/keep1.json', 'w'))
            subprocess.check_call(['node', f'{T}/css.js', 'emit', '/home/claude/fp-base', f'{T}/keep1.json'], cwd=T, env=dict(os.environ, OUT=f'{T}/crit1.json'))
            shutil.copy(f'/home/claude/fp-base/{page}', f'/home/claude/fp-wt/{page}')
            subprocess.check_call(['python3', f'{T}/apply.py', f'{T}/crit1.json'], stdout=subprocess.DEVNULL)
            new = set(); widths = []
            for w, h in MOB:
                c = ctx(w, h, True, CHK)
                c.route(lambda u: u.split('?')[0].endswith('.css'), lambda r: None)
                pg = c.new_page(); pg.goto(f'http://localhost:{CHK}/{page}', wait_until='domcontentloaded'); pg.wait_for_timeout(400)
                iw, idx = pg.evaluate(OVF); widths.append(iw); new |= set(idx)
                pg.close(); c.unroute_all(behavior='ignoreErrors'); c.close()
            if not (new - extra) or it >= 4:
                break
            extra |= new
        css = json.load(open(f'{T}/crit1.json'))[page]
        result[page] = css
        print(page, 'iter', it, 'extra', len(extra), 'held widths', widths, 'unresolved', len(new - extra) if it >= 4 else 0, flush=True)
    b.close()
json.dump(result, open(sys.argv[1], 'w'))
