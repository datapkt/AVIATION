---
name: ai-search-visibility-geo
description: Use to check or improve how a page or company appears in AI assistants and AI Overviews (GEO, AEO, LLMO): citability review, AI-crawler and llms.txt checks, entity and brand-mention gaps, AI prompt tracking.
---

# AI search visibility: GEO, AEO and LLMO

Condensed from three MIT-licensed skill libraries: zubair-trabzada/geo-seo-claude (citability, crawlers, llms.txt, brand mentions), coreyhaines31/marketingskills (ai-seo) and AgriciDaniel/claude-seo (seo-geo, seo-agentic). For DATAPKT work, the `datapkt-search-visibility` skill's rules come first.

## 1. Citability review of a page (AEO + GEO)
Score each section 0–100 on five things, then the page as the weighted average. Treat the score as a heuristic, never a prediction.
- **Answer first (30%)**: the section opens with a 1–2 sentence direct answer ("X is…", "X costs… because…"); the first 40–60 words stand alone.
- **Self-contained passages (25%)**: each paragraph names its subject (not "it/this"), carries at least one specific fact or named entity, and does not start with "But/However/And".
- **Structure (20%)**: H1 > H2 > H3 with no skipped levels; question-style headings where people ask questions; paragraphs of 2–4 sentences; tables for comparisons of 3+ items; numbered lists for processes.
- **Facts with sources (15%)**: numbers carry a unit, a time window and a source; never invent a figure to raise the score.
- **Original material (10%)**: first-party data, methods, photos, worked examples that no other site has.
Output: the 3 strongest and 3 weakest sections, with a rewrite for each weak one that keeps every fact unchanged.

## 2. AI crawler access (LLMO)
- robots.txt must not block search or user-fetch agents: Googlebot, Bingbot, OAI-SearchBot, ChatGPT-User, PerplexityBot, Perplexity-User, Claude-SearchBot, Claude-User, Applebot. Report training agents (GPTBot, ClaudeBot, Google-Extended, Applebot-Extended, CCBot, meta-externalagent) separately: blocking them is a business choice and does not remove a site from AI search answers.
- Obsolete names to ignore: anthropic-ai, Claude-Web.
- Key content must be in the HTML without JavaScript; no `nosnippet` or `max-snippet:0` on answer blocks; check no staging subdomain is indexable.
- Optional draft standard: a `Content-Signal: search=yes, ai-input=yes, ai-train=yes|no` line in robots.txt.

## 3. llms.txt
At the site root `/llms.txt` (not `.well-known`): `# Name`, then a `> one-paragraph summary`, then `## Sections` of `- [Title](absolute URL): short description`. Every link returns 200, is canonical and is in the sitemap. Keep it a short map (≤ ~40 links); put full text in `/llms-full.txt`. It is cheap context for AI tools; no search engine has confirmed it as a ranking factor.

## 4. Entity and brand mentions (GEO)
- Keep one register of company facts (names, address, phone, founding date, services) with source and review date; use identical wording on the site schema, Google Business Profile, Bing Places, LinkedIn and directories.
- Organization schema with `sameAs` to real profiles only. Wikidata item only once independent sources exist to reference; never write your own Wikipedia article.
- Earn genuine third-party mentions: industry associations, trade press, honest "top firms" roundups, conference talks, YouTube walkthroughs with transcripts. Ask every client the same way for a review; never filter, buy or incentivise reviews; never add rating markup without real reviews shown on the page.

## 5. Measure AI visibility
- A fixed panel of 30+ prompts written the way real buyers ask, tagged buy / solve / learn. Monthly, run each 3 times per assistant (ChatGPT, Claude, Copilot, Perplexity, Gemini) in fresh chats in the target locale; log date, exact product, mentioned (yes/no), position, cited URLs, wrong facts. Report per assistant; never blend into one score.
- Also track Bing Webmaster AI Performance (Copilot citations), GA4 sessions from AI assistants, and Search Console queries at positions 4–20.

## Skip
Fake reviews, review gating, doorway or city-swap pages, hidden text, text written to instruct AI systems, Reddit/Wikipedia seeding, HowTo or Speakable markup hopes, Sitelinks SearchAction, unsourced "X% more citations" claims, and any paid tool or community a source skill advertises.
