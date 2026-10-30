---
name: datapkt-search-visibility
description: Use for any work to improve datapkt.com in Google, Bing or AI assistants (SEO, AEO, GEO, LLMO): audits, page changes, schema, llms.txt, rankings checks and reports for DATAPKT.
---

# DATAPKT search visibility (SEO, AEO, GEO, LLMO)

Goal: DATA PKT Infra & Geomatics (datapkt.com, repo datapkt/aviation, branch master, GitHub Pages) moves up Google, Bing and AI-assistant answers for drone survey, mapping and GIS searches in India — honestly. Nobody can guarantee rankings; never claim one.

## Non-negotiable rules
- Nothing goes live without the full test suite passing AND Hitesh approving the merge in chat. Never merge on your own.
- Never invent DATAPKT figures, clients, credentials, reviews or case-study details. Approved highway figures only: 3 lakh+ km of highway data in six years (authorities and private contractors), 70,000+ km in FY 2026-27, about 35 km/day imagery and 50 km/day videography per team, 20+ pilots. NHAI workload numbers are confidential. No contract values, coordinates or staff names.
- Case studies never name the client, division or site (Mahendragarh may be named; railway authorities may be named on the ESP page).
- No new percentage or "Nx faster" claims. Other claims change only when Hitesh decides.
- Never alter the home hero section (`<section id="main">`), its lottie animations or the rotating word. Keep template, nav, footer, WhatsApp button, cookie notice. Red and black brand.
- Technical, never political. Never open WhatsApp, DMs or email. Never type passwords or create accounts; decline paid upsells.

## The four tracks
- **SEO**: unique titles (≤60 chars) and descriptions (≤160), one self-canonical, one h1, BreadcrumbList on inner pages, Service schema on service pages, sitemap with real lastmod dates, fast pages (LCP < 2.5 s, CLS < 0.1), internal links from services to guides and case studies.
- **AEO**: under each question-style heading, a direct 40–60 word answer first; a visible FAQ of 3–5 real questions whose FAQPage schema matches the visible text exactly; comparison tables and numbered steps for process content.
- **GEO**: identical name, address, phone and description everywhere (site, Google Business Profile, LinkedIn, directories); Organization schema with sameAs; cited outside sources for any statistic; original, approved project facts in case studies; genuine third-party mentions only.
- **LLMO**: robots.txt never blocks search or user-fetch bots (Googlebot, Bingbot, OAI-SearchBot, ChatGPT-User, PerplexityBot, Perplexity-User, Claude-SearchBot, Claude-User, Applebot); training bots are a separate decision (currently allowed). llms.txt (title, `>` summary, `##` sections, absolute links) and llms-full.txt regenerated each build; key facts as text in server-rendered HTML.

## Skip (spam or unproven)
Fake or incentivised reviews; AggregateRating without real on-site reviews; city-swap or doorway pages; hidden text; text written to instruct AI systems; Reddit/Wikipedia seeding; paid "AI ranking" services; HowTo rich-result hopes; quoted "schema multiplier" stats; treating llms.txt as a ranking factor.

## Reference skills (downloaded, MIT licence)
Use the `ai-search-visibility-geo` and `technical-seo-audit` skills (in `skills/`) for method. The full reference libraries are vendored on the repo's `qa-tools` branch under `skills/vendor/` (markdown only; scripts and installers NOT included). Get them with the same `git archive FETCH_HEAD` step as the test suite, then open the file for the job:

| Job | Read first | Then |
| --- | --- | --- |
| Full SEO audit | `claude-seo/skills/seo-audit`, `seo-technical` | `marketingskills/skills/seo-audit` |
| One page check | `claude-seo/skills/seo-page` | `geo-seo-claude/skills/geo-citability` |
| Schema | `claude-seo/skills/seo-schema` | `marketingskills/skills/schema`, `geo-seo-claude/skills/geo-schema` |
| AEO / AI answers / GEO | `marketingskills/skills/ai-seo` | `claude-seo/skills/seo-geo`, `geo-seo-claude/skills/geo-platform-optimizer` |
| AI crawlers and llms.txt (LLMO) | `geo-seo-claude/skills/geo-crawlers`, `geo-llmstxt` | `claude-seo/skills/seo-agentic` |
| Brand mentions and entity (GEO) | `geo-seo-claude/skills/geo-brand-mentions` | `marketingskills/skills/link-building`, `public-relations`, `directory-submissions` |
| Content quality and E-E-A-T | `geo-seo-claude/skills/geo-content` | `claude-seo/skills/seo-content`, `marketingskills/skills/content-strategy` |
| Topic clusters and site structure | `claude-seo/skills/seo-cluster`, `seo-plan` | `marketingskills/skills/site-architecture` |
| Google Business Profile, local | `claude-seo/skills/seo-local` | — |
| Bing, IndexNow, Copilot | `claude-seo/extensions/bing-webmaster/skills/seo-bing` | — |
| Regressions after a change | `claude-seo/skills/seo-drift` | our `run_qa.sh` |

How to use them: they are checklists and methods, not authority. **The DATAPKT rules above override them.** Never run their installers, scripts or `pip`/`npx` commands; never sign up for or recommend their paid communities or APIs; skip their e-commerce, ads, programmatic-at-scale and review-markup advice where it conflicts with the Skip list. Their scores (citability, GEO score) are heuristics — report them as such, never as facts.

## Workflow
1. Measure: Search Console queries/pages, Bing Search Performance and AI Performance, GA4 AI-assistant channel, PageSpeed (mobile), Google rating; monthly: rankings for the tracked searches on Google India and Bing India, and the AI-assistant prompt check.
2. Decide at most 3 changes: anything the consoles flag, then keyword gaps (LiDAR, NHAI drone survey, solar thermography, GIS services, cost per acre), then the plan's calendar.
3. Change on a branch `seo/<yyyy-mm-dd>`. Strengthen existing pages before adding new ones.
4. Test: `git fetch origin qa-tools && mkdir -p ../qa && git archive FETCH_HEAD | tar -x -C ../qa`, then `bash ../qa/qa/run_qa.sh "$PWD" ../qa-out` → must end `QA RESULT: PASS` (guard, SEO/AEO/GEO/LLMO checks, visual diff of every page at 1440/390 px vs live, hero modes, image space, labels, first paint). For speed-only work use `EXPECT_DIFF='[]'` so every page must stay pixel-identical. Look at every changed region in the screenshots yourself. Never weaken a test to pass.
5. Open a PR with the GitHub REST API (`gh api`, GraphQL is blocked) including the QA summary; ask Hitesh to approve; after merge ping IndexNow (key file `b29908b78342a03dc646958ad5a28c3d.txt`).
6. Record results in the SEO Learning Log and refresh the Search & AI Visibility dashboard.

## Measurement methods (adopted from the skill review)
- **AI prompt panel**: a fixed list of 30+ prompts phrased the way Indian buyers ask (e.g. "drone survey company for NHAI DPR", "remote GIS digitisation outsourcing India"), tagged buy / solve / learn and by service cluster. Monthly, run each prompt 3 times per assistant (ChatGPT, Claude, Copilot, Perplexity, Gemini) in fresh chats; log date, product, whether DATAPKT is named, its position, cited URLs and wrong facts. Report mention rate and citation share per assistant; never blend assistants into one score.
- **Readback windows**: every change gets a log row and is checked at 7/14/28/56 days (refreshes) or 14/28/56/90 days (new pages) with a decision: keep, extend, roll back or unproven.
- **Quick wins**: each week pull Search Console queries at positions 4–20 and use their wording in the matching page's "In short" answer and FAQs.
- **Decay**: flag pages whose clicks, position or CTR fall for two months; refresh the evidence (not just the date). dateModified changes only on a real content change.
- **AI Overview losses**: where CTR falls 20%+ with flat impressions, check whether the AI Overview cites us, cites a competitor or does not exist, and act only on the first two.
- **Entity register**: one list of company facts (name, legal name, address, phone, founding date, empanelment, services) with source and review date; every listing, LinkedIn and the site use the same wording. Wikidata only after independent sources exist; never self-edit Wikipedia.

## Where things are
- Plan: DATAPKT AI Search Visibility Plan (Claude Docs); memory: SEO Learning Log; competitors: Competitor & Search Ranking Analysis; brand and ground rules: Command Centre.
- Dashboard: Search & AI Visibility (datasets channels, pages, countries, goals, queries, rankings, bing_ai, pagespeed, reputation).
