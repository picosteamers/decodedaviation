#!/usr/bin/env python3
"""
Generate a case page (cases/<ntsb-lower>/index.html) from data/cases/<NTSB>.json.

Usage:
    python3 scripts/build_case.py data/cases/DCA20MA059.json
    python3 scripts/build_case.py --all          # rebuild every case that has a "page" block

The JSON schema is documented in CLAUDE.md. Research fields (narrative,
probable_cause, sources_checked, notes, ...) are kept separate from the
"page" block, which holds the editorial/display content actually rendered
on the page. A case with no "page" block is skipped (data collected, page
not written yet).
"""
import json
import sys
import glob
import hashlib
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ICONS = {
    "aircraft": "M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z",
    "registration": "M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2ZM16 2v4M8 2v4M3 10h18",
    "location": "M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0ZM12 7a3 3 0 1 0 0 6a3 3 0 1 0 0-6",
    "route": "M3 3l18 9-18 9 4-9z",
    "phase": "M3 3l18 9-18 9 4-9z",
    "operation": "M12 9a3 3 0 1 0 0 6a3 3 0 1 0 0-6M19.4 15a1.65 1.65 0 0 0 .33 1.82",
    "occupants": "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 3a4 4 0 1 0 0 8a4 4 0 1 0 0-8",
    "fatalities": "M12 2a8 8 0 0 0-8 8c0 3 1.5 5 3 6v3h10v-3c1.5-1 3-3 3-6a8 8 0 0 0-8-8Z",
    "serious": "M10.5 20.5 3.5 13.5a5 5 0 0 1 7-7l7 7a5 5 0 0 1-7 7Z",
    "minor": "M9 3h6v6h6v6h-6v6H9v-6H3V9h6z",
    "damage": "M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0ZM12 9v4M12 17h.01",
    "weather": "M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z",
}

PLANE_PATH = "M2 12l9-2 7-8 2 1-4 7 5 1v2l-5 1 4 7-2 1-7-8-9-2z"
CHECK_PATH = "M5 12.5 10 17 19 7"
CHEVRON_PATH = "m6 9 6 6 6-6"


def icon(name, size=18, stroke_width="1.8"):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="#34435a" stroke-width="{stroke_width}"><path d="{ICONS[name]}"></path></svg>')


def fact_row(icon_name, label, value, sub="", size=18):
    sub_html = f'<span class="fact-sub">{sub}</span>' if sub else ""
    return (f'<div class="fact-row">{icon(icon_name, size)}<span class="fact-k">{label}</span>'
            f'<div class="fact-v"><span>{value}</span>{sub_html}</div></div>')


def build_fact_rows(d, size):
    f = d["page"]["facts"]
    left = [
        fact_row("aircraft", "Aircraft", d["aircraft"]["type"], size=size),
        fact_row("registration", "Registration", d["aircraft"]["registration"], size=size),
        fact_row("location", "Location", f["location_value"], f.get("location_sub", ""), size),
        fact_row("route", f.get("route_label", "Route"), f["route_value"], f.get("route_sub", ""), size),
        fact_row("phase", "Phase of flight", f["phase_value"], f.get("phase_sub", ""), size),
        fact_row("operation", "Operation", f["operation"], size=size),
    ]
    right = [
        fact_row("occupants", "Occupants", d["occupants"], size=size),
        fact_row("fatalities", "Fatalities", d["fatalities"], size=size),
        fact_row("serious", "Serious injuries", d["injuries"]["serious"], size=size),
        fact_row("minor", "Minor injuries", d["injuries"]["minor"], size=size),
        fact_row("damage", "Damage", f["damage"], size=size),
        fact_row("weather", "Weather", f["weather_value"], f.get("weather_sub", ""), size),
    ]
    return left, right


def takeaway_item(text):
    return (f'<div class="takeaway-item"><span class="takeaway-check">'
            f'<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="4" '
            f'stroke-linecap="round" stroke-linejoin="round"><path d="{CHECK_PATH}"></path></svg>'
            f'</span><span>{text}</span></div>')


def related_item(r, thumb_size=22, wrap_size=56):
    href = f'../{r["ntsb"].lower()}/' if r.get("ntsb") else "#"
    return (f'<a class="related-item" href="{href}" style="text-decoration:none;color:inherit">'
            f'<div class="related-thumb" style="width:{wrap_size}px;height:{round(wrap_size*0.93)}px">'
            f'<div class="ac-thumb {r["icon_style"]}" style="height:100%">'
            f'<svg viewBox="0 0 24 24" fill="#2c3e52" width="{thumb_size}" height="{thumb_size}"><path d="{PLANE_PATH}"/></svg>'
            f'</div></div><div><span class="related-title">{r["title"]}</span><br>'
            f'<span class="related-sub">{r["sub"]}</span></div></a>')


def media_item_desktop(m):
    return (f'<a class="media-gallery-item" href="{m["link"]}" target="_blank" rel="noopener">'
            f'<div class="media-gallery-thumb"><img src="../../{m["photo"]}" alt="{m["alt"]}"></div>'
            f'<strong>{m["title"]}</strong><small>{m["meta"]}</small></a>')


def media_item_mobile(m):
    return (f'<a href="{m["link"]}" target="_blank" rel="noopener" class="related-item" style="text-decoration:none;color:inherit">'
            f'<div class="media-thumb" style="width:96px;height:62px;flex-shrink:0">'
            f'<img src="../../{m["photo"]}" alt="{m["alt"]}" style="width:100%;height:100%;object-fit:cover"></div>'
            f'<div><span class="related-title">{m["title"]}</span><br><span class="related-sub">{m["meta"]}</span></div></a>')


def build(d):
    p = d["page"]
    ntsb_lower = d["ntsb_number"].lower()
    left_d, right_d = build_fact_rows(d, 18)
    left_m, right_m = build_fact_rows(d, 16)

    factors_li = "\n            ".join(f"<li>{x}</li>" for x in p["contributing_factors"])
    takeaways_html = "\n          ".join(takeaway_item(x) for x in p["safety_takeaways"])
    media_desktop = "\n          ".join(media_item_desktop(m) for m in p["media"])
    media_mobile = "\n            ".join(media_item_mobile(m) for m in p["media"])
    related_desktop = "\n        ".join(related_item(r) for r in p["related_cases"])
    related_mobile = "\n            ".join(related_item(r, thumb_size=26, wrap_size=56) for r in p["related_cases"])
    specs_html = "\n          ".join(f'<span style="color:var(--muted)">{k}</span><span>{v}</span>' for k, v in p["aircraft_card"]["specs"])

    narrative_source = ("Source: NTSB Final Report (excerpt)" if p.get("narrative_is_excerpt")
                         else "Source: NTSB Final Report")

    title_tag = f'{p["title"]} — {d["location"]["city"]}, {d["location"]["state"]} | Aviation Safety'
    desc = (f'NTSB case {d["ntsb_number"]}: {p["subtitle"]}. What happened, probable cause, '
            f'contributing factors, and safety takeaways.')

    lat = d["location"].get("lat")
    lon = d["location"].get("lon")
    map_zoom = p["location_card"].get("zoom", 14)
    has_coords = lat is not None and lon is not None
    maps_href = f"https://www.google.com/maps?q={lat},{lon}" if has_coords else "#"
    if has_coords:
        map_block_desktop = f'<div class="case-map" id="case-map-{ntsb_lower}-d" data-lat="{lat}" data-lon="{lon}" data-zoom="{map_zoom}"></div>'
        map_block_mobile = f'<div class="case-map" id="case-map-{ntsb_lower}-m" style="height:120px;margin-bottom:8px" data-lat="{lat}" data-lon="{lon}" data-zoom="{map_zoom}"></div>'
    else:
        map_block_desktop = ('<div class="case-map" style="display:flex;align-items:center;justify-content:center;'
                              'background:var(--surface);color:var(--muted);font-size:12px;text-align:center;padding:8px">'
                              'No precise coordinates published for this site</div>')
        map_block_mobile = ('<div class="case-map" style="height:120px;margin-bottom:8px;display:flex;align-items:center;'
                             'justify-content:center;background:var(--surface);color:var(--muted);font-size:12px;text-align:center;padding:8px">'
                             'No precise coordinates published for this site</div>')

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title_tag}</title>
<meta name="description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../../assets/styles.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
</head>
<body>

<header class="site-header site-header--light">
  <div class="container header-row">
    <a class="brand" href="../../index.html">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="#0f1b2d"><path d="M21 16v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5z"/></svg>
      Aviation Safety
    </a>
    <nav class="main-nav">
      <a href="#">Accidents</a>
      <a href="#">Aircraft</a>
      <a href="#">Airports</a>
      <a href="#">Safety</a>
      <a href="#">About</a>
    </nav>
    <div class="header-search">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#56657a" stroke-width="2.2"><circle cx="11" cy="11" r="7"></circle><path d="m20 20-3.5-3.5"></path></svg>
      <input type="text" placeholder="Search aircraft, airport, or case…">
    </div>
    <button class="icon-btn header-search-toggle" aria-label="Search">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="11" cy="11" r="7"></circle><path d="m20 20-3.5-3.5"></path></svg>
    </button>
  </div>
</header>

<main class="container case-main">

  <div class="breadcrumbs">
    <a href="#">Accidents</a><span>›</span><a href="#">United States</a><span>›</span><a href="#">{d["location"]["state"]}</a><span class="case-desktop-only">›</span><span class="case-desktop-only">{p["title"]}</span>
  </div>

  <div class="case-title-block">
    <h1>{p["title"]}</h1>
    <span class="case-subtitle">{p["subtitle"]}</span>
    <span class="case-datetime">{p["datetime_text"]}</span>
  </div>

  <div class="case-badges">
    <div class="badge badge-red">
      <svg class="badge-icon" width="26" height="26" viewBox="0 0 24 24"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z" fill="#d7322d"></path><path d="M12 9v4M12 17h.01" stroke="#fff" stroke-width="2.2" stroke-linecap="round"></path></svg>
      <div><span class="badge-title">{p["badge_outcome"]}</span><br><span class="badge-sub">{p["badge_outcome_sub"]}</span></div>
    </div>
    <div class="badge badge-blue">
      <svg class="badge-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#1d63d8" stroke-width="2" stroke-linecap="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 3a4 4 0 1 0 0 8a4 4 0 1 0 0-8"></path></svg>
      <div><span class="badge-title" style="color:var(--ink)">{p["badge_casualty"]}</span><br><span class="badge-sub">{p["badge_casualty_sub"]}</span></div>
    </div>
  </div>

  <div class="status-banner">
    <span class="status-dot"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="{CHECK_PATH}"></path></svg></span>
    <div><span class="status-label">Investigation status</span><br><span class="status-value">Final report published</span><br><span class="status-meta">{p["status_meta"]}</span></div>
  </div>

  <div class="case-summary-card case-mobile-only">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1d63d8" stroke-width="2" stroke-linejoin="round" style="flex-shrink:0"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8"></path></svg>
    <div><h3>Case summary</h3><p>{p["summary"]}</p></div>
  </div>

  <a class="case-aircraft-card case-mobile-only" href="#" style="text-decoration:none;color:inherit">
    <div class="case-aircraft-thumb"><img src="../../{p["aircraft_card"]["photo"]}" alt="{p["aircraft_card"]["alt"]}" style="width:100%;height:100%;object-fit:cover"></div>
    <div class="case-aircraft-info"><span class="name">{p["aircraft_card"]["name"]}</span><br><span class="sub">{p["aircraft_card"]["sub"]}</span></div>
  </a>

  <div class="case-layout">
    <div class="case-col-main">

      <div class="facts-card case-desktop-only">
        <div class="facts-card-head">Key facts</div>
        <div style="display:grid;grid-template-columns:1fr 1fr">
          <div class="facts-grid" style="border-right:1px solid var(--border)">
            {"".join(left_d)}
          </div>
          <div class="facts-grid">
            {"".join(right_d)}
          </div>
        </div>
      </div>

      <div class="case-section case-desktop-only">
        <div class="case-section-head"><h2 class="case-h2">What happened</h2><span class="source-tag">{narrative_source}</span></div>
        <p class="case-body-text">{p["narrative_excerpt"]}</p>
      </div>

      <div class="case-section case-desktop-only">
        <div class="case-section-head"><h2 class="case-h2">Why it happened</h2><span class="source-tag">Source: NTSB Final Report</span></div>
        <div class="cause-card">
          <div class="cause-card-head"><span>NTSB probable cause</span><span>NTSB</span></div>
          <p>&quot;{d["probable_cause"]}&quot;</p>
        </div>
        <div class="factors-card">
          <span>Contributing factors</span>
          <ul>
            {factors_li}
          </ul>
        </div>
        <div class="takeaways-card">
          <div class="takeaways-head"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1a7f47" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.7V17h8v-2.3A7 7 0 0 0 12 2Z"></path></svg>Safety takeaways</div>
          {takeaways_html}
        </div>
      </div>

      <div class="case-section case-desktop-only">
        <div class="case-section-head"><h2 class="case-h2">Photos &amp; media ({len(p["media"])})</h2><span class="source-tag">{p["media_source_label"]}</span></div>
        <div class="media-gallery">
          {media_desktop}
        </div>
      </div>

      <!-- ===== Mobile: accordion ===== -->
      <div class="accordion case-mobile-only" data-accordion>

        <div class="accordion-section open" data-section>
          <button class="accordion-trigger" type="button"><span class="t">Key facts</span><svg class="chev" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#34435a" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="{CHEVRON_PATH}"></path></svg></button>
          <div class="accordion-panel">
            {"".join(left_m)}
            {"".join(right_m)}
          </div>
        </div>

        <div class="accordion-section" data-section>
          <button class="accordion-trigger" type="button"><span class="t">What happened</span><svg class="chev" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#34435a" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="{CHEVRON_PATH}"></path></svg></button>
          <div class="accordion-panel" hidden>
            <span style="display:block;text-align:right;font-size:11px;color:#56657a;margin-bottom:6px">{narrative_source}</span>
            <p class="case-body-text">{p["narrative_excerpt"]}</p>
          </div>
        </div>

        <div class="accordion-section" data-section>
          <button class="accordion-trigger" type="button"><span class="t">Why it happened</span><svg class="chev" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#34435a" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="{CHEVRON_PATH}"></path></svg></button>
          <div class="accordion-panel" hidden>
            <span style="display:block;text-align:right;font-size:11px;color:#56657a;margin-bottom:6px">Source: NTSB Final Report</span>
            <div class="cause-card">
              <div class="cause-card-head"><span>NTSB probable cause</span><span>NTSB</span></div>
              <p>&quot;{d["probable_cause"]}&quot;</p>
            </div>
          </div>
        </div>

        <div class="accordion-section" data-section>
          <button class="accordion-trigger" type="button"><span class="t">Contributing factors</span><svg class="chev" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#34435a" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="{CHEVRON_PATH}"></path></svg></button>
          <div class="accordion-panel" hidden>
            <ul style="margin:0;padding-left:20px;font-size:14px;line-height:1.6;color:var(--text)">
              {factors_li}
            </ul>
          </div>
        </div>

        <div class="accordion-section open is-takeaways" data-section>
          <button class="accordion-trigger" type="button"><span class="t">Safety takeaways</span><svg class="chev" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#34435a" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="{CHEVRON_PATH}"></path></svg></button>
          <div class="accordion-panel" style="display:flex;flex-direction:column;gap:9px">
            {takeaways_html}
          </div>
        </div>

        <div class="accordion-section" data-section>
          <button class="accordion-trigger" type="button"><span class="t">Photos &amp; media ({len(p["media"])})</span><svg class="chev" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#34435a" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="{CHEVRON_PATH}"></path></svg></button>
          <div class="accordion-panel" hidden style="display:flex;flex-direction:column;gap:10px">
            <span style="font-size:11px;color:var(--muted)">{p["media_source_label"]}</span>
            {media_mobile}
          </div>
        </div>

        <div class="accordion-section" data-section>
          <button class="accordion-trigger" type="button"><span class="t">Location</span><svg class="chev" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#34435a" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="{CHEVRON_PATH}"></path></svg></button>
          <div class="accordion-panel" hidden>
            {map_block_mobile}
            <span style="display:block;font-size:13px;color:var(--text)">{p["location_card"]["coords_text"]} · <a href="{maps_href}" target="_blank" rel="noopener">Open in Maps →</a></span>
            <span style="display:block;font-size:13px;color:var(--muted);margin-top:4px">{p["location_card"]["site_sub"]} · {p["location_card"]["site_meta"]}</span>
          </div>
        </div>

        <div class="accordion-section" data-section>
          <button class="accordion-trigger" type="button"><span class="t">Investigation documents</span><svg class="chev" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#34435a" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="{CHEVRON_PATH}"></path></svg></button>
          <div class="accordion-panel docs-list" hidden style="display:flex;flex-direction:column;gap:10px">
            <a href="{d["links"]["report"] or '#'}" target="_blank" rel="noopener">View final report <span class="doc-count">{p["docs"]["report_label"]}</span> ↗</a>
            <a href="{d["links"]["docket"] or '#'}" target="_blank" rel="noopener">View investigation docket <span class="doc-count">{p["docs"]["docket_label"]}</span> ↗</a>
          </div>
        </div>

        <div class="accordion-section" data-section>
          <button class="accordion-trigger" type="button"><span class="t">Related cases</span><svg class="chev" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#34435a" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="{CHEVRON_PATH}"></path></svg></button>
          <div class="accordion-panel" hidden style="display:flex;flex-direction:column;gap:12px">
            {related_mobile}
          </div>
        </div>

        <div class="accordion-section" data-section>
          <button class="accordion-trigger" type="button"><span class="t">About this case</span><svg class="chev" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#34435a" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="{CHEVRON_PATH}"></path></svg></button>
          <div class="accordion-panel" hidden>
            <div style="display:grid;grid-template-columns:120px 1fr;gap:10px;padding:8px 0;border-top:1px solid var(--border-2);font-size:13px"><span style="color:var(--muted)">NTSB case number</span><span>{d["ntsb_number"]}</span></div>
            <div style="display:grid;grid-template-columns:120px 1fr;gap:10px;padding:8px 0;border-top:1px solid var(--border-2);font-size:13px"><span style="color:var(--muted)">Event type</span><span>Accident</span></div>
            <div style="display:grid;grid-template-columns:120px 1fr;gap:10px;padding:8px 0;border-top:1px solid var(--border-2);font-size:13px"><span style="color:var(--muted)">Investigation type</span><span>{p["about_investigation_type"]}</span></div>
            <div style="display:grid;grid-template-columns:120px 1fr;gap:10px;padding:8px 0;border-top:1px solid var(--border-2);font-size:13px"><span style="color:var(--muted)">Report date</span><span>{p["status_meta"].split("· ")[-1] if "·" in p["status_meta"] else p["status_meta"]}</span></div>
          </div>
        </div>
      </div>

      <div class="case-mobile-only mobile-share">
        <span style="font-size:18px;font-weight:800">Share</span>
        <div style="display:grid;grid-template-columns:repeat(4,1fr)">
          <div style="display:flex;flex-direction:column;align-items:center;gap:6px;font-size:11px;color:var(--text)"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#34435a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>Copy link</div>
          <div style="display:flex;flex-direction:column;align-items:center;gap:6px;font-size:11px;color:var(--text)"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#0f1b2d" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4l16 16M20 4 4 20"></path></svg>X (Twitter)</div>
          <div style="display:flex;flex-direction:column;align-items:center;gap:6px;font-size:11px;color:var(--text)"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1d63d8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 0 20a10 10 0 1 0 0-20M15 8h-1.5A1.5 1.5 0 0 0 12 9.5V22M9.5 13h5"></path></svg>Facebook</div>
          <div style="display:flex;flex-direction:column;align-items:center;gap:6px;font-size:11px;color:var(--text)"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#34435a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h16a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1ZM3 6l9 7 9-7"></path></svg>Email</div>
        </div>
      </div>
      <a class="back-link case-mobile-only" href="../../index.html">← Back to search results</a>

    </div>

    <aside class="case-col-aside case-desktop-only">
      <div class="share-row">
        <div class="ntsb-case-no">NTSB case:<span>{d["ntsb_number"]}</span></div>
        <button class="share-case"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 2a3 3 0 1 0 0 6a3 3 0 1 0 0-6M6 9a3 3 0 1 0 0 6a3 3 0 1 0 0-6M18 16a3 3 0 1 0 0 6a3 3 0 1 0 0-6M8.6 13.5l6.8 4M15.4 6.5l-6.8 4"></path></svg>Share</button>
      </div>

      <div class="side-card">
        <span class="side-card-title">Aircraft</span>
        <div class="case-aircraft-thumb" style="border-radius:6px;overflow:hidden"><img src="../../{p["aircraft_card"]["photo"]}" alt="{p["aircraft_card"]["alt"]}" style="width:100%;height:100%;object-fit:cover"></div>
        <span style="font-size:11px;color:var(--muted)">{p["aircraft_card"]["caption"]}</span>
        <div><span style="font-size:15px;font-weight:600;display:block">{p["aircraft_card"]["name"]}</span><span style="font-size:14px;color:var(--muted)">{p["aircraft_card"]["sub"]}</span></div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px 10px;font-size:12.5px;padding-top:2px">
          {specs_html}
        </div>
        <a href="#" style="font-size:14px;font-weight:600">View aircraft details →</a>
      </div>

      <div class="side-card" style="padding:0;overflow:hidden">
        <div style="padding:12px;display:flex;flex-direction:column;gap:8px">
          <span class="side-card-title">Location</span>
          {map_block_desktop}
          <div class="case-location-info">
            <span class="primary">{p["location_card"]["primary"]}</span>
            <span class="muted">{p["location_card"]["region"]}</span>
            <span style="margin-top:2px">{p["location_card"]["coords_text"]} · <a href="{maps_href}" target="_blank" rel="noopener">Open in Maps →</a></span>
          </div>
        </div>
        <div class="nearest-airport">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#0f1b2d" stroke-width="1.8" stroke-linejoin="round"><path d="{ICONS['aircraft']}"></path></svg>
          <div><span class="nearest-airport-title">{p["location_card"]["site_title"]}</span><br><span class="nearest-airport-sub">{p["location_card"]["site_sub"]}</span><br><span class="nearest-airport-meta">{p["location_card"]["site_meta"]}</span></div>
        </div>
      </div>

      <div class="side-card docs-list">
        <div style="display:flex;align-items:center;gap:10px"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1d63d8" stroke-width="2" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8"></path></svg><span class="side-card-title">Investigation documents</span></div>
        <a href="{d["links"]["report"] or '#'}" target="_blank" rel="noopener" style="padding-left:30px">View final report <span class="doc-count">{p["docs"]["report_label"]}</span></a>
        <a href="{d["links"]["docket"] or '#'}" target="_blank" rel="noopener" style="padding-left:30px">View investigation docket <span class="doc-count">{p["docs"]["docket_label"]}</span></a>
      </div>

      <div class="side-card">
        <div style="display:flex;align-items:baseline;justify-content:space-between"><span class="side-card-title">Related cases</span><a href="#" style="font-size:14px;font-weight:600">View all →</a></div>
        {related_desktop}
        <a href="#" style="font-size:13px;font-weight:600;padding-left:68px;margin-top:-6px">Browse similar cases →</a>
      </div>

    </aside>
  </div>
</main>

<footer class="site-footer">
  <div class="container footer-row">
    <span>Data source: National Transportation Safety Board (NTSB)</span>
    <span>Updated daily</span>
  </div>
</footer>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="../../assets/script.js"></script>
</body>
</html>
"""
    out_dir = os.path.join(ROOT, "cases", ntsb_lower)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "index.html")
    with open(out_path, "w") as f:
        f.write(html)
    return out_path


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--all":
        paths = sorted(glob.glob(os.path.join(ROOT, "data", "cases", "*.json")))
    else:
        paths = sys.argv[1:]
        if not paths:
            print(__doc__)
            sys.exit(1)

    for path in paths:
        with open(path) as f:
            d = json.load(f)
        if not d.get("page"):
            print(f"skip  {os.path.basename(path)} (no 'page' block yet)")
            continue
        out = build(d)
        print(f"built {os.path.relpath(out, ROOT)}")


if __name__ == "__main__":
    main()
