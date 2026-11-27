# Critical CSS generator for datapkt.com inner pages

Added 25 Nov 2026 (PR #59). Each inner page (not index.html) carries `<style id="dp-critical">` with its above-the-fold rules, and loads the 4 stylesheets (bootstrap.min.css, src/css/style.css, dist/main.css, src/css/seo.css) with rel=preload plus a loader that applies all four at once.

**Regenerate whenever** any of those 4 CSS files changes, or a page's above-the-fold markup changes, or a new inner page is added. Otherwise the QA step FIRST PAINT fails.

Steps (from a checkout of the site):
1. `npm i postcss playwright` in this folder
2. `python3 gen3.py out.json pages.txt` (pages.txt = one page path per line) to compute the per-page critical rules at 360/390/768/1440/1920 px and 360-430 px mobile emulation
3. `python3 apply.py out.json` to write them into the pages
4. `python3 cls.py <pages>` and `python3 overflow.py <pages>` to check for zero layout shift and no mobile overflow
5. Run the full QA with `EXPECT_DIFF='[]' bash qa/run_qa.sh <site> <out>`: every page must stay pixel-identical, and FIRST PAINT must pass

Read each script's header before running it; paths may need adjusting to the checkout location.

## Layout-shift checks beyond cls.py (added PR58, 28 Nov 2026)

`cls.py` loads the HTML in one piece, so it misses shifts that only happen when the HTML arrives in chunks (as on a real phone). PR57 caused CLS 0.041 on highways-and-roadways.html that way: a `<style>` block near the end of `<body>` set `button{margin:10px}`; the critical CSS had it, but the full sheets (bootstrap `button{margin:0}`) applied before the parser reached that block, so the navbar shrank and grew back. Fix used: a copy of the page's body `<style>` blocks in `<head>` right after the 4 stylesheet links (`<style id="dp-late">`), so the cascade is the same at every loading stage.

- `serve_chunk.js`: static server that streams .html in pieces (`CHUNK`, `PAUSE`) and can delay .css (`CSSDELAY`). Example: `CSSDELAY=500 PAUSE=250 node serve_chunk.js <site> 8835`
- `clsfont.py`: layout-shift trace in 412x823 mobile emulation with sources. `NOFONT=1 NOTHROTTLE=1 python3 clsfont.py 8835 <pages>` isolates CSS-caused shifts. Without `NOFONT` it also serves Montserrat from the local system TTF after `DELAY` ms; set `FONTCONFIG_FILE` to a fontconfig file that rejects the family Montserrat (use a `<rejectfont><pattern>` on family; a glob on the file path does not work because the file name contains `[wght]`), otherwise the system copy is used and no swap happens.
- `heldcmp.py`: compares element boxes in the first screen, critical-only (4 sheets held) vs final, at 412x823 mobile, with cookie banner and WhatsApp button included (the QA first-paint check hides those). `HOLDIMG=1` also holds images.

Note: if a page has `<style>` blocks inside `<body>`, check it with serve_chunk.js + clsfont.py after any critical-CSS change.
