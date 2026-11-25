import sys, json
from playwright.sync_api import sync_playwright
INIT="""window.__ls=[];new PerformanceObserver(l=>{for(const e of l.getEntries())window.__ls.push({v:e.value,t:Math.round(e.startTime),hr:e.hadRecentInput,s:e.sources.map(s=>({n:(s.node&&(s.node.id||s.node.className||s.node.tagName))+'',p:[s.previousRect.y,s.previousRect.height,s.previousRect.x],c:[s.currentRect.y,s.currentRect.height,s.currentRect.x]}))})}).observe({type:'layout-shift',buffered:true});"""
with sync_playwright() as p:
    b=p.chromium.launch()
    for port in (8832,):
      for page in sys.argv[1:]:
        c=b.new_context(viewport={'width':412,'height':823}, device_scale_factor=1.75, is_mobile=True, has_touch=True)
        c.route(lambda u: not u.startswith('http://localhost'), lambda r: r.abort())
        c.add_init_script(INIT)
        pg=c.new_page(); cdp=c.new_cdp_session(pg)
        cdp.send('Network.enable'); cdp.send('Network.emulateNetworkConditions',{'offline':False,'latency':150,'downloadThroughput':1.6*1024*1024/8,'uploadThroughput':750*1024/8})
        cdp.send('Emulation.setCPUThrottlingRate',{'rate':4})
        pg.goto(f'http://localhost:{port}/{page}', wait_until='load'); pg.wait_for_timeout(1500)
        print(port, page, json.dumps(pg.evaluate('window.__ls')))
        c.close()
    b.close()
