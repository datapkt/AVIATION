---
name: technical-seo-audit
description: Use for a technical and on-page SEO audit of a website or a single page: crawlability, indexing, metadata, schema, internal links, Core Web Vitals, images, sitemap, with a prioritised fix list.
---

# Technical and on-page SEO audit

Condensed from MIT-licensed skills: AgriciDaniel/claude-seo (seo-audit, seo-technical, seo-page, seo-schema, seo-sitemap, seo-local, seo-drift) and coreyhaines31/marketingskills (seo-audit, schema, site-architecture). For DATAPKT work, the `datapkt-search-visibility` skill's rules come first. Follow Google's and Bing's own documentation where a source skill disagrees.

## Scope first
Full site (every indexable page) or one URL? Static site or CMS? Which pages earn money (services, contact)? Fix those first.

## Checks, with the rule used
**Crawl and index**
- Every sitemap URL returns 200, is not a redirect, has no `noindex`, and its canonical equals itself; every indexable page is in the sitemap; `lastmod` is the real last content change.
- robots.txt allows search engines and lists the sitemap; a random missing URL returns 404, not 200.
- http → https and www → apex each redirect in one 301 hop; no indexable staging copies.

**On-page**
- One `<title>` (about 50–60 characters, unique) and one meta description (about 120–160, unique) per page, matching the H1's topic.
- Exactly one H1; headings never skip a level.
- One self-referencing absolute canonical.
- Open Graph title, description, URL (= canonical) and image (absolute, 1200 px wide).

**Structured data**
- Every JSON-LD block parses. Home: Organization (or a subtype) with name, url, logo, address, telephone, sameAs; WebSite. Services: Service with `provider` pointing to the Organization `@id`. Articles: headline, image, datePublished ≤ dateModified, author, publisher. Inner pages: BreadcrumbList.
- FAQPage only where the questions are visible on the page, word for word; expect no rich result from it. No HowTo, Speakable or SearchAction for a site without search; no AggregateRating without visible real reviews.
- Name, address and phone in schema match the visible footer on every page.

**Links and structure**
- No orphan pages; services link to related guides and case studies and back; descriptive anchor text; no broken internal links.

**Performance and media**
- Core Web Vitals targets: LCP < 2.5 s, INP < 200 ms, CLS < 0.1 (field data from Search Console first, Lighthouse second).
- Every image has alt text (empty only if decorative), width and height, modern format, lazy loading below the fold; the LCP image is preloaded, never lazy.
- Render-blocking CSS/JS: defer what the first screen does not need, but measure — moving work after first paint can raise Total Blocking Time.

**Local (businesses with an office)**
- Google Business Profile and Bing Places complete, same name/address/phone as the site; categories and services filled; reviews answered.

**After every change (drift)**
- Compare title, description, canonical, robots meta, H1 and schema with the previous version; a lost canonical, new noindex or removed H1/schema is a blocker.

## Report
Order fixes by impact × effort: Critical (blocks indexing or breaks pages), High (money pages, schema errors, slow LCP), Medium, Low. For each: page, issue, rule, evidence, fix. Never report a guess as a measurement; say which tool or file each finding came from.
