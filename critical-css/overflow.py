import sys
from playwright.sync_api import sync_playwright
JS="""() => { const W=document.documentElement.clientWidth; const out=[]; for (const e of document.querySelectorAll('body *')) { const r=e.getBoundingClientRect(); if (r.right>W+1 && r.width>0) { if (!out.some(o=>o.el.contains(e))) out.push({el:e, d:e.tagName+'.'+(e.className+'').slice(0,40)+' w='+Math.round(r.width)+' top='+Math.round(r.top)}); } } return [innerWidth, document.documentElement.scrollWidth, out.slice(0,12).map(o=>o.d)]; }"""
with sync_playwright() as p:
    b=p.chromium.launch()
    for page in sys.argv[1:]:
        c=b.new_context(viewport={'width':412,'height':823}, device_scale_factor=1.75, is_mobile=True, has_touch=True)
        c.route(lambda u: not u.startswith('http://localhost'), lambda r: r.abort())
        c.route(lambda u: u.split('?')[0].endswith('.css'), lambda r: None)
        pg=c.new_page(); pg.goto(f'http://localhost:{8832}/{page}', wait_until='domcontentloaded'); pg.wait_for_timeout(500)
        print(page, pg.evaluate(JS), flush=True); c.close()
    import os; os._exit(0)
