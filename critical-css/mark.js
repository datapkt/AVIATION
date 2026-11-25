(args) => { const rules = args.rules, extra = args.extra || [];
  const vh = innerHeight, MARGIN = 120;
  const DYN = /:(hover|focus|focus-visible|focus-within|active|visited)\b/;
  const PSEUDO_EL = /::?(before|after|first-letter|first-line|marker|placeholder|selection|backdrop|file-selector-button|-webkit-[a-z-]+|-moz-[a-z-]+|-ms-[a-z-]+)(\([^)]*\))?/g;
  const qual = new Set([document.documentElement]), hid = new Set();
  const walkEl = (el) => { for (const e of el.children) { const cs = getComputedStyle(e);
      if (cs.display === 'none') { hid.add(e); continue; }
      const r = e.getBoundingClientRect();
      if (r.top < vh + MARGIN || cs.position === 'fixed' || cs.position === 'sticky' || cs.display === 'contents') qual.add(e);
      walkEl(e); } };
  walkEl(document.documentElement);
  const all = document.querySelectorAll('body *');
  for (const i of extra) { let e = all[i]; while (e) { qual.add(e); hid.delete(e); e = e.parentElement; } }
  const used = [];
  for (const r of rules) {
    if (!r.parts.every(p => { try { return CSS.supports('selector(' + p + ')'); } catch (e) { return false; } })) continue;
    r.parts.forEach((part, k) => {
      if (DYN.test(part)) return;
      let s = part.replace(PSEUDO_EL, '').trim(); if (!s || /[>+~]$/.test(s)) s = (s || '') + '*';
      let els; try { els = document.querySelectorAll(s); } catch (e) { return; }
      let d = false; for (const el of els) { if (qual.has(el)) { used.push(r.id + '|' + k); d = false; break; } if (hid.has(el)) d = true; }
      if (d) used.push(r.id + '|' + k + '|d');
    });
  }
  return used;
}
