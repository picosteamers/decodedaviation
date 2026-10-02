#!/usr/bin/env python3
"""
Generate sitemap.xml and update robots.txt's Sitemap: line, once a domain is known.

Usage:
    python3 scripts/build_sitemap.py --base-url https://your-domain.com

Scans cases/*/index.html for case pages and includes index.html at the root.
Run this once before each deploy that adds new case pages.
"""
import argparse
import glob
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STATIC_PAGES = ["index.html"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True, help="e.g. https://flightcase.example.com (no trailing slash)")
    args = ap.parse_args()
    base = args.base_url.rstrip("/")

    urls = [f"{base}/"]
    for case_dir in sorted(glob.glob(os.path.join(ROOT, "cases", "*"))):
        if os.path.isfile(os.path.join(case_dir, "index.html")):
            slug = os.path.basename(case_dir)
            urls.append(f"{base}/cases/{slug}/")

    entries = "\n".join(
        f"  <url>\n    <loc>{u}</loc>\n  </url>" for u in urls
    )
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n"
        "</urlset>\n"
    )
    with open(os.path.join(ROOT, "sitemap.xml"), "w") as f:
        f.write(sitemap)
    print(f"wrote sitemap.xml with {len(urls)} URLs")

    robots = (
        "User-agent: *\n"
        "Allow: /\n\n"
        f"Sitemap: {base}/sitemap.xml\n"
    )
    with open(os.path.join(ROOT, "robots.txt"), "w") as f:
        f.write(robots)
    print(f"wrote robots.txt pointing at {base}/sitemap.xml")


if __name__ == "__main__":
    main()
