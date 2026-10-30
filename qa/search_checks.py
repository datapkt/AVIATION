"""SEO / AEO / GEO / LLMO checks for the static site (DP_SITE). Built from a review of public agent skills
(coreyhaines31/marketingskills, kubical-ai/aeo-geo-optimization, piiiico/aeo-skill, sanity-io/agent-toolkit,
dirnbauer/webconsulting-skills, vudovn/ag-kit; all MIT except dirnbauer content CC-BY-SA) with the spam and
unproven advice removed. Offline: reads files only.
FAIL = must fix before merge. WARN = worth improving, does not block.
Exit 1 if any FAIL."""
import os, re, sys, json, glob, html
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

SITE_DIR = os.path.abspath(os.environ.get('DP_SITE', '.'))
ORIGIN = 'https://datapkt.com'
fails, warns, info = [], [], []
F = lambda m: fails.append(m); W = lambda m: warns.append(m)


def read(p):
    return open(os.path.join(SITE_DIR, p), encoding='utf-8', errors='ignore').read()


def url_to_file(u):
    p = urlparse(u).path.lstrip('/')
    for c in (p or 'index.html', p + 'index.html' if p.endswith('/') else None, p + '.html'):
        if c and os.path.isfile(os.path.join(SITE_DIR, c)): return c
    return None


def strip_tags(s):
    s = re.sub(r'<!--.*?-->', ' ', s, flags=re.S)
    s = re.sub(r'<(script|style|noscript)\b.*?</\1>', ' ', s, flags=re.S | re.I)
    return ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', s)).split())


pages = sorted(f for f in glob.glob('**/*.html', root_dir=SITE_DIR, recursive=True)
               if not f.startswith(('src/', 'node_modules/', 'dist/', 'others/', 'vscode/')))
live = [p for p in pages if 'http-equiv="refresh"' not in read(p) and p not in ('404.html', 'thank-you.html')]

# ---- LLMO: robots.txt (purpose-based policy: search and user-fetch bots must never be blocked)
rb = read('robots.txt') if os.path.exists(os.path.join(SITE_DIR, 'robots.txt')) else ''
if f'Sitemap: {ORIGIN}/sitemap.xml' not in rb: F('robots.txt: no Sitemap line')
groups, cur = {}, []
for line in rb.splitlines():
    line = line.split('#')[0].strip()
    if not line: cur = [] if cur and groups.get(cur[-1]) else cur; continue
    k, _, v = line.partition(':'); k, v = k.strip().lower(), v.strip()
    if k == 'user-agent':
        cur.append(v.lower()); groups.setdefault(v.lower(), [])
    elif k in ('allow', 'disallow') and cur:
        for ua in cur: groups[ua].append((k, v))
        if k: pass
def blocked_root(ua):
    rules = groups.get(ua.lower(), groups.get('*', []))
    return any(k == 'disallow' and v == '/' for k, v in rules)
SEARCH_BOTS = ['Googlebot', 'Bingbot', 'OAI-SearchBot', 'ChatGPT-User', 'PerplexityBot', 'Perplexity-User', 'Claude-SearchBot', 'Claude-User', 'Applebot', 'DuckDuckBot']
TRAIN_BOTS = ['GPTBot', 'ClaudeBot', 'Google-Extended', 'Applebot-Extended', 'meta-externalagent', 'CCBot']
for b in SEARCH_BOTS:
    if blocked_root(b): F(f'robots.txt blocks search/user bot {b}')
info.append('training bots ' + ', '.join(f'{b}={"blocked" if blocked_root(b) else "allowed"}' for b in TRAIN_BOTS))

# ---- LLMO: llms.txt structure and links
if os.path.exists(os.path.join(SITE_DIR, 'llms.txt')):
    ll = read('llms.txt'); lines = [l for l in ll.splitlines() if l.strip()]
    if not lines[0].startswith('# '): F('llms.txt: first line must be "# Name"')
    if not any(l.startswith('> ') for l in lines[1:4]): F('llms.txt: summary "> ..." must follow the title')
    if '## ' not in ll: F('llms.txt: no "## " sections')
    links = re.findall(r'\]\((https?://[^)]+)\)', ll)
    for u in links:
        if u.startswith(ORIGIN) and not u.endswith('.txt') and not url_to_file(u): F(f'llms.txt link has no page: {u}')
    if len(links) > 60: W(f'llms.txt has {len(links)} links (keep it a short map)')
    key = ['gis-mapping-services.html', 'case-studies/', 'insights/', 'drone-survey-cost.html', 'thermal-survey.html', 'lidar-survey.html']
    for k in key:
        if k not in ll: W(f'llms.txt does not link {k}')
else:
    F('llms.txt missing')
if not os.path.exists(os.path.join(SITE_DIR, 'llms-full.txt')) or os.path.getsize(os.path.join(SITE_DIR, 'llms-full.txt')) < 10000:
    F('llms-full.txt missing or under 10 KB')

# ---- SEO: sitemap
try:
    locs = [(e.find('{*}loc').text.strip(), (e.find('{*}lastmod').text.strip() if e.find('{*}lastmod') is not None else ''))
            for e in ET.parse(os.path.join(SITE_DIR, 'sitemap.xml')).getroot()]
except Exception as e:
    locs = []; F(f'sitemap.xml does not parse: {e}')
in_sitemap = set()
for u, lm in locs:
    f = url_to_file(u)
    if not f: F(f'sitemap URL has no file: {u}'); continue
    in_sitemap.add(f)
    t = read(f)
    if 'http-equiv="refresh"' in t: F(f'sitemap lists a redirect page: {u}')
    if re.search(r'<meta[^>]+noindex', t): F(f'sitemap lists a noindex page: {u}')
    if lm and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', lm): F(f'sitemap lastmod not ISO date: {u} {lm}')
for p in live:
    if p not in in_sitemap and not p.startswith(('privacy',)): W(f'page not in sitemap: {p}')

# ---- per page
titles, descs = {}, {}
org_ids = set()
for p in live:
    t = read(p); body = re.sub(r'<!--.*?-->', '', t.split('</head>', 1)[-1], flags=re.S)
    canon = re.findall(r'<link rel="canonical" href="([^"]+)"', t)
    exp = ORIGIN + '/' + ('' if p == 'index.html' else (p[:-10] if p.endswith('/index.html') else p))
    if len(canon) != 1: F(f'{p}: {len(canon)} canonical tags')
    elif canon[0] != exp: W(f'{p}: canonical {canon[0]} (expected {exp})')
    ti = re.search(r'<title>(.*?)</title>', t, re.S); ti = html.unescape(ti.group(1).strip()) if ti else ''
    de = re.search(r'<meta name="description" content="([^"]*)"', t); de = html.unescape(de.group(1)) if de else ''
    if not ti: F(f'{p}: no title')
    elif not 25 <= len(ti) <= 65: W(f'{p}: title {len(ti)} chars')
    if not de: F(f'{p}: no meta description')
    elif not 70 <= len(de) <= 165: W(f'{p}: description {len(de)} chars')
    titles.setdefault(ti, []).append(p); descs.setdefault(de, []).append(p)
    h1 = len(re.findall(r'<h1[\s>]', body))
    if h1 != 1: F(f'{p}: {h1} h1')
    for m in re.finditer(r'<img\b[^>]*>', re.sub(r'<!--.*?-->', '', body, flags=re.S)):
        if not re.search(r'\balt="', m.group(0)) and 'role="presentation"' not in m.group(0) and 'aria-hidden' not in m.group(0):
            W(f'{p}: image without alt {re.search(r"src=\"([^\"]+)", m.group(0)).group(1) if "src=" in m.group(0) else ""}'[:140]); break
    for k in ('og:title', 'og:description', 'og:image', 'og:url'):
        if f'property="{k}"' not in t: W(f'{p}: missing {k}')
    # schema
    blocks = re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', t, re.S)
    types, nodes = set(), []
    for b in blocks:
        try: d = json.loads(b)
        except Exception as e: F(f'{p}: JSON-LD does not parse'); continue
        for n in (d.get('@graph', [d]) if isinstance(d, dict) else d):
            nodes.append(n); ty = n.get('@type'); types |= set(ty if isinstance(ty, list) else [ty])
    for n in nodes:
        ty = n.get('@type'); ty = ty if isinstance(ty, list) else [ty]
        if 'Organization' in ty: org_ids.add(n.get('@id'))
        if 'FAQPage' in ty:
            vis = strip_tags(body).lower()
            for q in n.get('mainEntity', []):
                if ' '.join(html.unescape(q.get('name', '')).split()).lower()[:60] not in vis:
                    F(f'{p}: FAQ question not visible on page: {q.get("name", "")[:60]}')
        if set(ty) & {'Article', 'BlogPosting'}:
            for k in ('headline', 'datePublished', 'dateModified', 'author', 'publisher', 'image'):
                if k not in n: W(f'{p}: {ty[0]} missing {k}')
            if n.get('dateModified', '') < n.get('datePublished', ''): F(f'{p}: dateModified before datePublished')
    if p != 'index.html' and 'BreadcrumbList' not in types: W(f'{p}: no BreadcrumbList')
    if p == 'index.html':
        need = {'Organization', 'WebSite'}
        if not need <= types: F(f'index.html: missing {need - types}')
    # AEO: answer-first paragraph after question headings
    for m in re.finditer(r'<h([23])[^>]*>([^<]*(?:<(?!/h)[^<]*)*)</h\1>\s*(?:<div[^>]*>\s*)?<p[^>]*>(.*?)</p>', body, re.S):
        hd = strip_tags(m.group(2))
        if hd.endswith('?') or re.match(r'(What|How|Why|When|Which|Is|Can|Does|Do) ', hd):
            n_words = len(strip_tags(m.group(3)).split())
            if n_words < 15 or n_words > 110: W(f'{p}: answer under "{hd[:50]}" is {n_words} words (aim 40-60)')
for ti, ps in titles.items():
    if len(ps) > 1: F(f'duplicate title on {ps}')
for de, ps in descs.items():
    if len(ps) > 1: F(f'duplicate meta description on {ps}')
if len(org_ids - {None}) > 1: F(f'more than one Organization @id: {org_ids}')

# ---- GEO: entity consistency in visible text
idx = strip_tags(read('index.html'))
for must in ('DATA PKT', 'Gurugram'):
    if must not in idx: F(f'home page visible text lacks "{must}"')
first_p = re.search(r'<p[^>]*>(.*?)</p>', read('index.html').split('</head>', 1)[-1], re.S)
for p in live:
    vt = strip_tags(read(p))
    if '8448559100' not in vt.replace(' ', '').replace('-', '') and '84485 59100' not in vt: W(f'{p}: phone number not in visible text')

# ---- extra checks (from the claude-seo / geo-seo-claude / NotFair review)
keyf = [f for f in os.listdir(SITE_DIR) if re.fullmatch(r'[A-Za-z0-9-]{8,128}\.txt', f) and f not in ('robots.txt', 'llms.txt')]
if not any(open(os.path.join(SITE_DIR, k)).read().strip() == k[:-4] for k in keyf): W('no IndexNow key file /<key>.txt whose body equals the key')
if not os.path.exists(os.path.join(SITE_DIR, '404.html')): W('no 404.html (GitHub Pages serves it with HTTP 404)')
inlinks = {p: 0 for p in live}
for p in live:
    t = re.sub(r'<!--.*?-->', '', read(p), flags=re.S)
    for h in set(re.findall(r'href="([^"#?]+)', t)):
        if h.startswith(('http', 'mailto:', 'tel:', 'javascript:')):
            if not h.startswith(ORIGIN): continue
            h = h[len(ORIGIN):]
        q = os.path.normpath(os.path.join(os.path.dirname(p), h) if not h.startswith('/') else h.lstrip('/'))
        for c in (q, q + '/index.html', q + '.html', q.rstrip('/') + '/index.html'):
            if c in inlinks and c != p: inlinks[c] += 1; break
for p, n in inlinks.items():
    if n == 0 and p != 'index.html': W(f'orphan page (no internal links to it): {p}')
for p in live:
    t = read(p); body = re.sub(r'<!--.*?-->', '', t.split('</head>', 1)[-1], flags=re.S)
    if re.search(r'"(aggregateRating|AggregateRating|Review)"', t) and not re.search(r'class="[^"]*review', body):
        F(f'{p}: review/rating schema without visible reviews')
    for bad in ('SpeakableSpecification', 'HowTo', 'SearchAction'):
        if f'"{bad}"' in t: W(f'{p}: {bad} schema (retired or not applicable here)')
    for m in re.finditer(r'<img\b[^>]*>', body):
        tag = m.group(0)
        if 'width=' not in tag or 'height=' not in tag:
            W(f'{p}: image without width/height (layout shift): {(re.search(r"src=\"([^\"]+)", tag) or [None, ""])[1][:70]}'); break
if os.path.exists(os.path.join(SITE_DIR, 'llms.txt')):
    for u in re.findall(r'\]\((https://datapkt\.com/[^)]*)\)', read('llms.txt')):
        f_ = url_to_file(u)
        if f_ and f_ not in in_sitemap and not u.endswith('.txt'): W(f'llms.txt links a page not in the sitemap: {u}')

for p in live:
    t = read(p)
    if re.search(r'nosnippet|max-snippet:0|data-nosnippet', t): F(f'{p}: nosnippet / max-snippet:0 blocks answers being quoted')
    lv = [int(x) for x in re.findall(r'<h([1-6])[\s>]', re.sub(r'<!--.*?-->', '', t.split('</head>', 1)[-1], flags=re.S))]
    for a, b in zip(lv, lv[1:]):
        if b > a + 1: W(f'{p}: heading jumps h{a} -> h{b}'); break
    if not re.search(r'href="(mailto:|tel:|/contact\.html|contact\.html)', t): W(f'{p}: no contact link')

for i in info: print('INFO', i)
for w in warns: print('WARN', w)
for f in fails: print('FAIL', f)
print(f'SEARCH CHECKS: {len(live)} pages, {len(warns)} warnings,', 'PASS' if not fails else f'FAIL ({len(fails)})')
sys.exit(1 if fails else 0)
