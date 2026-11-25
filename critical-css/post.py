"""Minify critical CSS and drop custom properties that nothing in the critical CSS or the page's own inline CSS uses."""
import re


def minify(css):
    out, q, i = [], None, 0
    while i < len(css):
        ch = css[i]
        if q:
            out.append(ch)
            if ch == '\\': out.append(css[i + 1]); i += 2; continue
            if ch == q: q = None
            i += 1; continue
        if ch in '"\'':
            q = ch; out.append(ch); i += 1; continue
        if ch in ':;{},' and i + 1 < len(css) and css[i + 1] == ' ' and not (ch == ':' and out and _in_selector(out)):
            out.append(ch); i += 1
            while i < len(css) and css[i] == ' ': i += 1
            continue
        if ch == ' ' and i + 1 < len(css) and css[i + 1] in '{}':
            i += 1; continue
        out.append(ch); i += 1
    s = ''.join(out)
    return s.replace(';}', '}')


def _in_selector(out):
    # a ':' followed by space only occurs in declarations and @media conditions; selectors never have ': '
    return False


def custom_decls(css):
    """yield (start, end, name, value) of custom property declarations inside rule bodies."""
    res, i, n = [], 0, len(css)
    for m in re.finditer(r'(?<=[{;])--[\w-]+:', css):
        name = m.group(0)[:-1]; j = m.end(); depth = 0; q = None
        while j < n:
            c = css[j]
            if q:
                if c == '\\': j += 2; continue
                if c == q: q = None
            elif c in '"\'': q = c
            elif c in '([': depth += 1
            elif c in ')]': depth -= 1
            elif depth == 0 and c in ';}': break
            j += 1
        res.append((m.start(), j, name, css[m.end():j]))
    return res


def prune_vars(css, page_inline_css):
    decls = custom_decls(css)
    mask = list(css)
    for s, e, _, _ in decls:
        for k in range(s, e): mask[k] = ' '
    base = ''.join(mask) + page_inline_css
    used = set(re.findall(r'var\(\s*(--[\w-]+)', base))
    vals = {}
    for _, _, name, v in decls: vals.setdefault(name, []).append(v)
    todo = list(used)
    while todo:
        nm = todo.pop()
        for v in vals.get(nm, []):
            for r in re.findall(r'var\(\s*(--[\w-]+)', v):
                if r not in used: used.add(r); todo.append(r)
    out, last = [], 0
    for s, e, name, _ in decls:
        if name in used: continue
        out.append(css[last:s]); last = e + (1 if e < len(css) and css[e] == ';' else 0)
    out.append(css[last:])
    css = ''.join(out)
    css = css.replace(';}', '}')
    prev = None
    while prev != css:
        prev = css
        css = re.sub(r'(?<=[{}])[^{}@]+\{\}', '', css)
        css = re.sub(r'^[^{}@]+\{\}', '', css)
        css = re.sub(r'@(media|supports)[^{}]*\{\}', '', css)
    return css
