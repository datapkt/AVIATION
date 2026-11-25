// node css.js parse <root> > rules.json   |   node css.js emit <root> keep.json > crit.json
const fs = require('fs'), path = require('path'), postcss = require('postcss');
const SHEETS = ['src/vendor/bootstrap-5.3.3/bootstrap.min.css', 'src/css/style.css', 'dist/main.css', 'src/css/seo.css'];
const [, , mode, root, keepFile] = process.argv;
function splitSel(sel) { const out = []; let d = 0, cur = '', q = null;
  for (const ch of sel) { if (q) { cur += ch; if (ch === q) q = null; continue; }
    if (ch === '"' || ch === "'") { q = ch; cur += ch; continue; }
    if (ch === '(' || ch === '[') d++; if (ch === ')' || ch === ']') d--;
    if (ch === ',' && d === 0) { out.push(cur.trim()); cur = ''; } else cur += ch; }
  if (cur.trim()) out.push(cur.trim()); return out; }
const asts = SHEETS.map(s => postcss.parse(fs.readFileSync(path.join(root, s), 'utf8'), {from: s}));
// assign ids in document order
const rules = [];
asts.forEach((ast, si) => ast.walkRules(r => {
  if (r.parent && r.parent.type === 'atrule' && /keyframes$/i.test(r.parent.name)) return;
  r._id = rules.length; rules.push({id: r._id, sheet: si, parts: splitSel(r.selector.replace(/\/\*[\s\S]*?\*\//g, ''))});
}));
if (mode === 'parse') { fs.writeFileSync(process.env.OUT, JSON.stringify(rules)); } else {
const keepAll = JSON.parse(fs.readFileSync(keepFile, 'utf8'));
const out = {};
for (const [page, keep] of Object.entries(keepAll)) {
  const K = new Set(keep); // entries "id|k"
  let css = '';
  const anims = new Set(); const kf = [];
  asts.forEach((ast0, si) => {
    const ast = ast0.clone(); let ids = [];
    // clone loses _id; re-walk original in parallel order
    ast0.walkRules(r => { if (!(r.parent && r.parent.type === 'atrule' && /keyframes$/i.test(r.parent.name))) ids.push(r._id); });
    let n = 0;
    ast.walkRules(r => {
      if (r.parent && r.parent.type === 'atrule' && /keyframes$/i.test(r.parent.name)) return;
      const id = ids[n++]; const parts = splitSel(r.selector.replace(/\/\*[\s\S]*?\*\//g, ''));
      const full = parts.some((_, k) => K.has(id + '|' + k));
      const kept = parts.filter((_, k) => K.has(id + '|' + k) || K.has(id + '|' + k + '|d'));
      if (!kept.length) { r.remove(); return; }
      r.selector = kept.join(',');
      if (!full) { r.walkDecls(d => { if (d.prop.toLowerCase() !== 'display') d.remove(); }); if (!r.nodes.length) { r.remove(); return; } }
      r.walkDecls(d => { if (/^(-webkit-|-moz-|-o-)?animation(-name)?$/i.test(d.prop))
        d.value.split(',').forEach(v => v.trim().split(/\s+/).forEach(t => anims.add(t))); });
    });
    ast.walkComments(c => c.remove());
    ast.walkAtRules(a => { if (/^(charset|import|page)$/i.test(a.name)) a.remove(); });
    // remove empty at-rules repeatedly
    let changed = true;
    while (changed) { changed = false; ast.walkAtRules(a => { if (/keyframes$/i.test(a.name) || a.name === 'font-face') return;
      if (a.nodes && a.nodes.length === 0) { a.remove(); changed = true; } }); }
    ast.walkAtRules(a => { if (/keyframes$/i.test(a.name)) { kf.push(a); } });
    // urls -> root-absolute
    const base = '/' + path.posix.dirname(SHEETS[si]) + '/';
    ast.walkDecls(d => { d.value = d.value.replace(/url\(\s*(["']?)([^"')]+)\1\s*\)/g, (m, q, u) => {
      if (/^(data:|#|https?:|\/)/.test(u)) return m; return 'url("' + new URL(u, 'http://x' + base).pathname + '")'; }); });
    ast.walk(nd => { if (nd.raws) { nd.raws.before = ''; nd.raws.after = ''; nd.raws.between = nd.type === 'decl' ? ':' : ''; nd.raws.semicolon = false; if (nd.type === 'atrule') nd.raws.afterName = nd.params ? ' ' : ''; } });
    let txt = ast.toString();
    css += txt;
  });
  // keyframes not referenced: drop
  for (const a of kf) { const t = a.toString(); if (!anims.has(a.params.trim())) css = css.split(t).join(''); }
  out[page] = css;
}
fs.writeFileSync(process.env.OUT, JSON.stringify(out));
}
