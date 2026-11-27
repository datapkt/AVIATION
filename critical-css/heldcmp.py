"""Compare element boxes in the first viewport: critical-only (4 sheets held) vs final, mobile emulation 412x823,
no freeze (cookie banner / WhatsApp included). usage: python3 heldcmp.py <port> <page>..."""
import sys, json
from playwright.sync_api import sync_playwright
JS = """() => { const out={}; const all=[...document.querySelectorAll('body *')];
 all.forEach((e,i)=>{const r=e.getBoundingClientRect(); if(r.width||r.height) out[i]=[Math.round(r.x),Math.round(r.y+scrollY),Math.round(r.width),Math.round(r.height),getComputedStyle(e).fontFamily.slice(0,12)+'|'+e.tagName+(e.id?'#'+e.id:'')+'.'+(typeof e.className=='string'?e.className:'').trim().split(/\\s+/).join('.')]}); return [all.length,out]; }"""
port = sys.argv[1]
with sync_playwright() as p:
    b = p.chromium.launch()
    for page in sys.argv[2:]:
        res = []
        for hold in (True, False):
            c = b.new_context(viewport={'width': 412, 'height': 823}, device_scale_factor=1.75, is_mobile=True, has_touch=True)
            c.route(lambda u: not u.startswith('http://localhost'), lambda r: r.abort())
            c.route('**/*.lottie', lambda r: r.abort())
            if hold: c.route(lambda u: u.split('?')[0].endswith('.css'), lambda r: None)
            import os
            if hold and os.environ.get('HOLDIMG'): c.route(lambda u: u.split('?')[0].lower().endswith(('.webp','.jpg','.png','.jpeg','.svg','.gif','.avif')), lambda r: None)
            pg = c.new_page(); pg.goto(f'http://localhost:{port}/{page}', wait_until='domcontentloaded' if hold else 'load')
            pg.wait_for_timeout(2500); res.append(pg.evaluate(JS)); pg.close(); c.unroute_all(behavior='ignoreErrors'); c.close()
        (na, A), (nb, B) = res
        diffs = []
        for k, a in A.items():
            bb = B.get(k)
            if not bb: diffs.append(('gone', a)); continue
            if a[1] > 1100 and bb[1] > 1100: continue
            if any(abs(a[j] - bb[j]) > 1 for j in range(4)): diffs.append((a, bb[:4]))
        for k, bb in B.items():
            if k not in A and bb[1] < 1100: diffs.append(('new', bb))
        print(page, na, nb, len(diffs))
        for d in diffs[:25]: print('  ', d)
    b.close()
