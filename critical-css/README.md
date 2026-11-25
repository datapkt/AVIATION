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
