# DATAPKT website QA tools

This branch is not deployed. It holds the regression suite that must pass before any change to datapkt.com is merged.

```
git clone --depth 50 https://github.com/datapkt/aviation site && cd site
git fetch origin qa-tools && mkdir -p ../qa && git archive FETCH_HEAD | tar -x -C ../qa
git checkout -b seo/<date>          # make the changes
bash ../qa/qa/run_qa.sh "$PWD" ../qa-out     # must end with: QA RESULT: PASS
# speed or other work that must not change how any page looks:
EXPECT_DIFF='[]' bash ../qa/qa/run_qa.sh "$PWD" ../qa-out
```

Suites (all must PASS):
- `guard.py` — home hero byte-identical to live, both lottie animations present, no new % / "Nx faster" claims, JSON-LD parses, one title, sitemap URLs exist, internal links on changed pages resolve, no new third-party script hosts.
- `search_checks.py` — SEO / AEO / GEO / LLMO rules: titles, descriptions, canonicals, h1, schema per page type, FAQ schema matches visible text, robots.txt (search vs training bots), llms.txt, sitemap, orphans, review markup, nosnippet. WARN lines are improvements, FAIL lines block.
- `run_tests.py` — every page at 1440 px and 390 px compared pixel-by-pixel with live; pages not changed must be identical; one h1, no broken images, no phone overflow, navbar visible, no new JS errors; home hero never blank with the animation blocked, delayed or normal.
- `phase1_checks.py` — images keep reserved space while loading, rendered image sizes unchanged, one `<main>`, form fields and iframes named.
- `first_paint.py` — (home page) with every stylesheet held back, the first screen already looks like the final render (critical CSS).

Pre-existing JS errors on live (reported as NOTE, not FAIL): highways `$ is not defined`; photogrammetry `offsetTop` of null.
