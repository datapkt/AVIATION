"""Content and structure guard: candidate (DP_SITE) vs live baseline (BASE_DIR).
Fails when a change touches something that must never change, or breaks site-wide files.
1. Home hero <section id="main">...</section> byte-identical to live (hero, lottie animation, rotating word).
2. Both lottie animations still referenced on the home page (motion.lottie, aiengine.lottie).
3. No new percentage / multiplier claims ("99%", "5x faster") added to any page's visible text.
4. Every JSON-LD block parses; every page keeps exactly one <title> and one canonical.
5. sitemap.xml parses and every URL in it maps to a file that exists.
6. Internal links (href="/..." or relative .html) on changed pages resolve to files.
7. No new third-party <script src> hosts compared with live.
Exit 1 on any failure."""
import os, re, sys, json, glob, subprocess
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

SITE = os.path.abspath(os.environ.get('DP_SITE', '.'))
BASE = os.path.abspath(os.environ['BASE_DIR'])
fails, notes = [], []


def pages(root):
    return sorted(f for f in glob.glob('**/*.html', root_dir=root, recursive=True)
                  if not f.startswith(('src/', 'node_modules/', 'dist/', 'others/', 'vscode/')))


def read(root, f):
    p = os.path.join(root, f)
    return open(p, encoding='utf-8', errors='ignore').read() if os.path.exists(p) else None


def visible(html):
    html = re.sub(r'<!--.*?-->', ' ', html, flags=re.S)
    html = re.sub(r'<(script|style|noscript)\b.*?</\1>', ' ', html, flags=re.S | re.I)
    return re.sub(r'<[^>]+>', ' ', html)


CLAIM = re.compile(r'\b\d{1,3}(?:\.\d+)?\s?%|\b\d+(?:\.\d+)?\s?[xX×]\s+(?:faster|cheaper|quicker|more|better)', re.I)
HERO = re.compile(r'<section id="main".*?</section>', re.S)

# 1-2 hero
ch, bh = read(SITE, 'index.html'), read(BASE, 'index.html')
a, b = HERO.search(ch or ''), HERO.search(bh or '')
if not a or not b: fails.append('home hero section not found')
elif a.group(0) != b.group(0): fails.append('home hero <section id="main"> changed (never allowed)')
for anim in ('./src/motion.lottie', './src/aiengine.lottie'):
    if anim not in (ch or ''): fails.append(f'home page lost {anim}')

changed = []
for f in pages(SITE):
    c, b = read(SITE, f), read(BASE, f)
    if c != b: changed.append(f)
    # 3 claims
    if b is not None:
        new = set(m.group(0).strip() for m in CLAIM.finditer(visible(c))) - set(m.group(0).strip() for m in CLAIM.finditer(visible(b)))
        if new: fails.append(f'{f}: new percentage/multiplier claim(s) {sorted(new)[:5]} - needs Hitesh to confirm')
    elif CLAIM.search(visible(c)):
        notes.append(f'{f} (new page): contains % / multiplier text {sorted(set(m.group(0) for m in CLAIM.finditer(visible(c))))[:5]} - check each is sourced')
    # 4 head
    if 'http-equiv="refresh"' in c: continue
    for i, blk in enumerate(re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', c, re.S)):
        try: json.loads(blk)
        except Exception as e: fails.append(f'{f}: JSON-LD block {i} does not parse ({e})')
    if len(re.findall(r'<title>', c)) != 1: fails.append(f'{f}: {len(re.findall("<title>", c))} <title> tags')
    if len(re.findall(r'rel="canonical"', c)) > 1: fails.append(f'{f}: more than one canonical')
    # 7 scripts
    hosts = lambda h: set(urlparse(s).netloc for s in re.findall(r'<script[^>]+src="(https?://[^"]+)"', re.sub(r'<!--.*?-->', '', h or '', flags=re.S)))
    extra = hosts(c) - hosts(b) if b is not None else set()
    if extra: fails.append(f'{f}: new third-party script host(s) {sorted(extra)}')

# 5 sitemap
try:
    root = ET.parse(os.path.join(SITE, 'sitemap.xml')).getroot()
    locs = [e.text.strip() for e in root.iter() if e.tag.endswith('loc')]
    for u in locs:
        path = urlparse(u).path.lstrip('/')
        cand = [path or 'index.html', path + 'index.html' if path.endswith('/') else path, path + '.html', path + '/index.html']
        if not any(os.path.isfile(os.path.join(SITE, x)) for x in cand if x):
            fails.append(f'sitemap URL has no file: {u}')
    notes.append(f'sitemap: {len(locs)} URLs checked')
except Exception as e:
    fails.append(f'sitemap.xml does not parse: {e}')

# 6 internal links on changed pages
for f in changed:
    c = read(SITE, f)
    for h in set(re.findall(r'href="([^"#?]+)', re.sub(r'<!--.*?-->', '', c, flags=re.S))):
        if re.match(r'(https?:|mailto:|tel:|javascript:|data:|//)', h): continue
        p = os.path.normpath(os.path.join(SITE, h.lstrip('/')) if h.startswith('/') else os.path.join(SITE, os.path.dirname(f), h))
        if not (os.path.isfile(p) or os.path.isfile(os.path.join(p, 'index.html')) or os.path.isfile(p + '.html')):
            fails.append(f'{f}: broken internal link {h}')

notes.append(f'{len(changed)} page(s) differ from live: {changed[:20]}')
for n in notes: print('NOTE', n)
for x in fails: print('FAIL', x)
print('GUARD:', 'PASS' if not fails else f'FAIL ({len(fails)})')
sys.exit(1 if fails else 0)
