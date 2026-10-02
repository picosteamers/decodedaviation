# CLAUDE.md

Guidance for Claude Code when working in this repo.

## What this is

**Aviation Safety / "FlightCase"** — a real-data aviation-accident case database.
Plain static HTML/CSS/JS, no framework, no build step at deploy time. A home
page lists recent cases; each case gets its own page under `/cases/`.

Originally scaffolded from a Claude Design project (a `.dc.html` mockup
called "FlightCase"). The first case built from that mockup (`LAX07FA258`,
a Raytheon A36 Bonanza accident) is a **real** NTSB case, not a fictional
demo — it's kept and treated the same as every other case.

Not deployed yet. `git remote -v` is empty on purpose — the user will create
the GitHub repo and connect Netlify themselves. Commit locally; never push
or set up a remote unless explicitly asked.

## The one hard rule: sourcing

Every fact on a case page must trace back to an NTSB source
(`ntsb.gov` / `data.ntsb.gov`, CAROL), not aviation-safety.net, Wikipedia,
or news coverage. Those secondary sources are fine for *finding* a lead
(an NTSB case number, a rough description) but never as the cited source
for a fact that goes in `data/cases/*.json`.

- `narrative` and `probable_cause` should be **verbatim** text extracted
  from the official NTSB report PDF (fetch it, extract text with PyMuPDF or
  similar — don't paraphrase, don't trust a summarizer tool on the raw PDF
  bytes without cross-checking).
- If a report is only `preliminary`, there is no `probable_cause` yet —
  leave it `null`. Don't invent one.
- If a case is too recent for NTSB to have published anything
  (`report_status: "pending"`), say so plainly in `notes`, mark which
  fields (if any) are sourced from news instead of NTSB, and leave
  `ntsb_number` null rather than trusting a number from a non-NTSB
  aggregator (see `PENDING-chatsworth-newschopper4-2026-09-15.json` for
  how this was handled).
- `LAX07FA258.json` predates this standard — its narrative is a close
  paraphrase cross-checked against AOPA ASI, not a verbatim PDF extraction.
  It's flagged as such in its own `notes` field. If it's ever revisited,
  upgrade it to the same standard as the rest.
- Watch for mismatched docket documents: a search result or generic URL
  pattern can point to the wrong case's photos/PDF. Always confirm the
  NTSB number appears on the actual fetched page/PDF before using it —
  this has already caught one real mix-up (see git history around the
  Kobe Bryant case's photos).
- Names of people involved (pilots, passengers, celebrities) are often
  *not* in the NTSB report itself — it says "the pilot," "the passenger."
  Public figures' names can go in editorial copy (the `page` block) since
  they're genuinely public-interest and already public record, but don't
  misattribute a name to the NTSB document as if it said it.

## Site structure (URLs are final — don't change them)

```
/                           index.html — home page
/cases/<ntsb-lower>/        a case page (directory + index.html, clean URL)
/assets/                    shared styles.css, script.js, img/
/data/cases/<NTSB>.json     source-of-truth data per case (public, also serves as "show your work")
/scripts/                   authoring-time tools (not run at deploy; output is committed static HTML)
/sitemap.xml, /robots.txt   generated once a domain is chosen (see below) — not committed until then
```

Case URLs are the NTSB number, lowercased, as the directory name
(`/cases/dca20ma059/`), matching the one external reference implementation
we found for this exact design (`aviation-safety-explorer.aviaai.chatgpt.site/cases/lax07fa258/`).
This was a deliberate choice over a descriptive slug: it never needs
editorial judgment, it's exactly what someone searching the case number
would type, and it can never go stale. **Do not rename these directories
or switch to `.html` files at the root** — once this is live, that would
break every indexed URL.

## Data pipeline — how a case goes from research to a live page

1. **Research** → `data/cases/<NTSB-NUMBER>.json` (uppercase filename,
   matching the case number as NTSB writes it). This is the full schema:
   research fields at the top level, editorial/display fields nested under
   `"page"`. A file with no `"page"` key has data but no page yet — that's
   a valid, expected intermediate state (9 of the 12 cases here are
   currently like this).

   Top-level (research) fields: `ntsb_number`, `date`, `location` (`city`,
   `state`, `lat`, `lon`), `aircraft` (`type`, `registration`), `operator`,
   `flight_type`, `occupants`, `fatalities`, `injuries` (`serious`, `minor`),
   `report_status` (`final` | `preliminary` | `pending`), `narrative`,
   `probable_cause`, `phase_of_flight`, `weather`, `links` (`report`,
   `docket`), `sources_checked` (array of URLs actually fetched), `notes`
   (caveats, what's verbatim vs. not, anything uncertain).

   `page` fields (only once someone has actually written the page copy):
   `title`, `subtitle`, `datetime_text`, `badge_outcome` + `_sub`,
   `badge_casualty` + `_sub`, `status_meta`, `summary` (the mobile teaser
   paragraph), `facts` (`location_value`/`_sub`, `route_label`/`_value`/`_sub`,
   `phase_value`/`_sub`, `operation`, `damage`, `weather_value`/`_sub`),
   `narrative_excerpt` + `narrative_is_excerpt` (bool — long verbatim
   narratives get trimmed to the dramatic core for the page; say so),
   `contributing_factors` (array), `safety_takeaways` (array, written fresh
   per case — never copy another case's takeaways), `aircraft_card`
   (`photo`, `alt`, `caption`, `name`, `sub`, `specs` as `[[label, value], ...]`),
   `media` (array of `{photo, alt, title, meta, link}` — real NTSB docket
   photos, not stock art, when they exist), `media_source_label`,
   `location_card` (`map_caption`, `primary`, `region`, `coords_text`,
   `site_title`, `site_sub`, `site_meta`), `docs` (`report_label`,
   `docket_label`), `related_cases` (array of `{title, sub, icon_style}`),
   `about_investigation_type`.

2. **Photos**: aircraft photo should be the *actual accident airframe*
   pre-accident if a real photo of that exact tail number exists (it did
   for both N1098F and N72EX — check Wikimedia Commons by registration
   before falling back to "same model, different tail number"). Incident
   photos come from the NTSB docket (`data.ntsb.gov/Docket/?NTSBNumber=...`
   → find the right factual-report attachment → extract embedded images
   with PyMuPDF, don't screenshot the PDF page). Resize to ~900px wide,
   re-encode as WebP, name as `<description>.<8-char-sha256-of-file>.webp`,
   save to `assets/img/`, credit in `CREDITS.md`.

3. **Generate the page**: `python3 scripts/build_case.py data/cases/<FILE>.json`
   (or `--all` to rebuild every case that has a `page` block). This writes
   `cases/<ntsb-lower>/index.html`. The template lives in
   `scripts/build_case.py` — edit it there, not by hand-patching a
   generated `index.html` (hand edits get clobbered on the next `--all` run).
   If the template itself needs a design change, change it once in the
   script and rebuild everyone with `--all`.

4. **Add it to the home page** (`index.html`) — currently a manual edit to
   the "Latest aviation incidents" list. See "Known gaps" below.

5. **Commit.**

## Known gaps / before going live

- **The home page's incident list is a mix of real and fictional rows.**
  Only the first row (Kobe Bryant) is real; the other five are leftover
  placeholder data from the original design mockup (fake registrations,
  fake NTSB-style summaries). This needs to be cleaned up — either
  generate the whole list from `data/cases/*.json` or hand-replace the
  fictional rows — **before this site is public**. Mixing fabricated
  "incidents" with real NTSB-sourced ones on a safety site is a real
  trust/E-E-A-T problem, not just cosmetic.
- **"Explore by aircraft" / map / accident-type sections on the home page
  are still non-functional mockup content** (`href="#"`, fake stats).
  Fine for now; needs real listing pages or removal before launch.
- **No sitemap.xml / robots.txt yet** — can't be generated correctly
  without a known domain (sitemap URLs must be absolute). Once the
  domain is live:
  `python3 scripts/build_sitemap.py --base-url https://<your-domain>`
  Re-run this after adding new case pages, before each deploy.
- **No Open Graph / canonical / JSON-LD tags yet** in `scripts/build_case.py`'s
  template. Worth adding once there's a real domain to point canonical URLs at.
- 9 of the 12 researched cases have data but no `page` block yet (no
  written contributing-factors/safety-takeaways/photos): `ANC18FA007`
  (Roy Halladay), `CEN23LA348` (Cessna 172), `DCA09MA026` (US Airways 1549),
  `DCA09MA027` (Colgan Air 3407), `DCA25MA108` (DCA midair collision —
  also flagged for a second accuracy pass given how fast and sensitive
  this one is), `ERA24FA036` (Piper PA-28), `WPR22FA338` (Santa Monica
  Flyers spin), `WPR24LA106` (Cirrus SR22), `WPR26MA063` (Greg Biffle,
  preliminary — no page until a final report exists), plus the Chatsworth
  NewsChopper4 case (no confirmed NTSB number yet, `pending`).
- 40 more cases (of the planned 50) haven't been picked yet.

## Conventions carried over from the design mockup

- **Mobile-first, two renderings per page**: desktop uses always-visible
  `.case-desktop-only` sections (facts card, prose sections, photo gallery
  as a 3-up grid in the main column); mobile uses a single
  `.case-mobile-only` accordion (`data-accordion` + `.accordion-section`)
  covering the same content. Both are in the DOM; CSS + `assets/script.js`
  toggle visibility by breakpoint/interaction — never build content only
  for the active tab/panel.
- **Photos & media sits in the main content column, after Safety
  takeaways** — not in the aside sidebar. This matches the one reference
  implementation found for this design and was a deliberate move (see git
  history: "Move Photos & media under the article text").
- Icons are fixed per fact field (same SVG path for "Aircraft", same for
  "Weather", etc. everywhere) — see the `ICONS` dict in
  `scripts/build_case.py`. Don't invent a new icon per case.
