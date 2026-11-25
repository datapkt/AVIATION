import sys, json, re, os, gzip
sys.path.insert(0, '/home/claude/fp-tools')
from post import minify, prune_vars
WT = '/home/claude/fp-wt'
crit = json.load(open(sys.argv[1]))
LOADER = "<script>function dpCss(l){if(dpCss.d)return;l.dpOk=(l.dpOk||0)+1;var L=document.querySelectorAll('link[data-dp-css]'),i,m=9;if(L.length<4)return;for(i=0;i<L.length;i++)m=Math.min(m,L[i].dpOk||0);if(m==1&&!dpCss.s){dpCss.s=1;for(i=0;i<L.length;i++){L[i].media='not all';L[i].rel='stylesheet'}}else if(m==2){dpCss.d=1;for(i=0;i<L.length;i++)L[i].media='all'}}(function(){var r=document.createElement('link').relList;if(!(r&&r.supports&&r.supports('preload')))document.addEventListener('DOMContentLoaded',function(){var L=document.querySelectorAll('link[data-dp-css]'),i;dpCss.d=1;for(i=0;i<L.length;i++){L[i].rel='stylesheet';L[i].media='all'}})})()</script>"
LINK = re.compile(r'<link\b[^>]*>')
HREFS = ('bootstrap.min.css', 'src/css/style.css', 'dist/main.css', 'src/css/seo.css')
report = []
for page, css in crit.items():
    path = os.path.join(WT, page); html = open(path, encoding='utf-8').read()
    assert page != 'index.html'
    if 'dp-critical' in html: continue
    inline = ' '.join(re.findall(r'<style[^>]*>(.*?)</style>', html, re.S) + re.findall(r'style="([^"]*)"', html))
    c = prune_vars(minify(css), inline)
    bi = html.find('<body')
    body_css = [m.group(1).strip() for m in re.finditer(r'<style[^>]*>(.*?)</style>', html, re.S) if m.start() > bi]
    if body_css: c += minify(re.sub(r'/\*.*?\*/', '', ' '.join(body_css), flags=re.S).replace('\n', ' ').replace('  ', ' '))
    assert '</style' not in c
    com = [(m.start(), m.end()) for m in re.finditer(r'<!--.*?-->', html, re.S)]
    links = [m for m in LINK.finditer(html) if not any(a <= m.start() < b for a, b in com) and 'stylesheet' in m.group(0) and any(h in m.group(0) for h in HREFS)]
    assert len(links) == 4, (page, len(links))
    order = [next(h for h in HREFS if h in m.group(0)) for m in links]
    assert order == list(HREFS), (page, order)
    out, last = [], 0
    for k, m in enumerate(links):
        href = re.search(r'href="([^"]+)"', m.group(0)).group(1)
        out.append(html[last:m.start()])
        if k == 0: out.append(f'<style id="dp-critical">{c}</style>{LOADER}\n  ')
        out.append(f'<link rel="preload" as="style" href="{href}" data-dp-css onload="dpCss(this)" onerror="dpCss(this)">'
                   f'<noscript><link rel="stylesheet" href="{href}"></noscript>')
        last = m.end()
    out.append(html[last:])
    open(path, 'w', encoding='utf-8').write(''.join(out))
    report.append((page, len(c), len(gzip.compress(c.encode()))))
for r in report: print(*r)
