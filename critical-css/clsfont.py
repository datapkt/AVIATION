"""CLS trace under mobile emulation + throttling with a REAL web-font swap: the system Montserrat is hidden via
FONTCONFIG_FILE (set by caller) and fonts.googleapis/gstatic are served from a local Montserrat TTF after DELAY ms.
usage: FONTCONFIG_FILE=... python3 clsfont.py <port> <page>...
env: DELAY (font ms), WAIT, NOFONT=1 (abort web font: isolate CSS-caused shifts), NOTHROTTLE=1, CSSDELAY/IMGDELAY (ms, serialised).
Pair with serve_chunk.js to stream the HTML slowly: that exposes shifts from late <style> blocks in <body>."""
import sys, json, os, time, threading
from playwright.sync_api import sync_playwright
FONT = '/usr/share/fonts/truetype/google-fonts/ofl/montserrat/Montserrat[wght].ttf'
DELAY = int(os.environ.get('DELAY', '1200')); WAIT = int(os.environ.get('WAIT', '4000'))
CSS = "@font-face{font-family:'Montserrat';font-style:normal;font-weight:400 800;font-display:swap;src:url(https://fonts.gstatic.com/s/montserrat/m.ttf) format('truetype')}"
INIT = """window.__ls=[];new PerformanceObserver(l=>{for(const e of l.getEntries())window.__ls.push({v:+e.value.toFixed(5),t:Math.round(e.startTime),s:e.sources.map(s=>{const n=s.node;let d=n?(n.nodeType===1?(n.tagName+(n.id?'#'+n.id:'')+(n.className&&typeof n.className=='string'?'.'+n.className.trim().split(/\\s+/).join('.'):'')):('#text:'+(n.textContent||'').trim().slice(0,30)+' in '+(n.parentElement&&(n.parentElement.tagName+'.'+n.parentElement.className)))):'?';return {n:d.slice(0,120),p:[s.previousRect.x,s.previousRect.y,s.previousRect.width,s.previousRect.height].map(Math.round),c:[s.currentRect.x,s.currentRect.y,s.currentRect.width,s.currentRect.height].map(Math.round)}})})}).observe({type:'layout-shift',buffered:true});
document.fonts&&document.fonts.addEventListener('loadingdone',()=>window.__fontT=Math.round(performance.now()));"""
port = sys.argv[1]
fontbody = open(FONT, 'rb').read()
with sync_playwright() as p:
    b = p.chromium.launch()
    for page in sys.argv[2:]:
        c = b.new_context(viewport={'width': 412, 'height': 823}, device_scale_factor=1.75, is_mobile=True, has_touch=True)
        def ext(r):
            u = r.request.url
            if os.environ.get('NOFONT'): r.abort()
            elif 'fonts.googleapis.com/css' in u:
                time.sleep(0.15); r.fulfill(status=200, headers={'Content-Type': 'text/css', 'Access-Control-Allow-Origin': '*'}, body=CSS)
            elif 'fonts.gstatic.com' in u:
                time.sleep(DELAY / 1000); r.fulfill(status=200, headers={'Content-Type': 'font/ttf', 'Access-Control-Allow-Origin': '*'}, body=fontbody)
            else: r.abort()
        c.route(lambda u: not u.startswith('http://localhost'), ext)
        CD = int(os.environ.get('CSSDELAY', '0'))
        if CD:
            def slow(r):
                time.sleep(CD / 1000); r.continue_()
            c.route(lambda u: u.startswith('http://localhost') and u.split('?')[0].endswith('.css'), slow)
        IMD = int(os.environ.get('IMGDELAY', '0'))
        if IMD:
            def slowi(r):
                time.sleep(IMD / 1000); r.continue_()
            c.route(lambda u: u.startswith('http://localhost') and u.split('?')[0].lower().endswith(('.webp','.jpg','.png','.jpeg','.svg','.gif','.avif')), slowi)
        c.add_init_script(INIT)
        pg = c.new_page(); cdp = c.new_cdp_session(pg)
        if not os.environ.get('NOTHROTTLE'): cdp.send('Network.enable'); cdp.send('Network.emulateNetworkConditions', {'offline': False, 'latency': 150, 'downloadThroughput': 1.6*1024*1024/8, 'uploadThroughput': 750*1024/8})
        if not os.environ.get('NOTHROTTLE'): cdp.send('Emulation.setCPUThrottlingRate', {'rate': 4})
        pg.goto(f'http://localhost:{port}/{page}', wait_until='load'); pg.wait_for_timeout(WAIT); fcp = pg.evaluate("Math.round((performance.getEntriesByName('first-contentful-paint')[0]||{}).startTime||-1)")
        ls = pg.evaluate('window.__ls'); ft = pg.evaluate('window.__fontT')
        print(page, 'CLS', round(sum(e['v'] for e in ls), 4), 'fontT', ft, 'FCP', fcp, json.dumps(ls), flush=True)
        c.close()
    b.close()
