import json
import re
import html
from pathlib import Path
from urllib.parse import quote

BASE_URL = "https://chobibartabd.online"
DATA_FILE = Path("headline-news/index.json")
OUTPUT_DIR = Path("news")


def safe_text(value):
    return html.escape(str(value or "").strip(), quote=True)


def make_slug(record):
    title = record.get("title_en") or record.get("title_bn") or "news"
    title = title.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", title).strip("-")
    if not slug:
        slug = "news-" + re.sub(r"[^0-9]", "", str(record.get("date", "")))
    return slug[:90].strip("-") or "news"


def main():
    if not DATA_FILE.exists():
        raise SystemExit("headline-news/index.json was not found.")

    items = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    if not isinstance(items, list):
        raise SystemExit("Headline JSON must contain a list.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    used_slugs = set()
    generated = 0

    for item in items:
        if not isinstance(item, dict) or item.get("approved") is not True:
            continue

        title_bn = str(item.get("title_bn") or "").strip()
        title_en = str(item.get("title_en") or "").strip()
        title = title_bn or title_en
        if not title:
            continue

        slug = make_slug(item)
        original_slug = slug
        suffix = 2
        while slug in used_slugs:
            slug = f"{original_slug}-{suffix}"
            suffix += 1
        used_slugs.add(slug)

        summary = str(
            item.get("summary_bn")
            or item.get("summary_en")
            or item.get("summary_original")
            or ""
        ).strip()

        image = str(item.get("image") or "").strip()
        if image and not image.startswith(("https://", "http://", "/")):
            image = "/" + image

        source = str(item.get("source") or "").strip()
        source_url = str(item.get("source_url") or item.get("url") or "").strip()
        if source_url and not source_url.startswith(("https://", "http://")):
            source_url = ""

        article_url = f"{BASE_URL}/news/{quote(slug)}.html"
        image_url = (
            image if image.startswith(("https://", "http://"))
            else BASE_URL + image if image else ""
        )

        page_title = safe_text(title)
        page_summary = safe_text(summary)
        page_image = safe_text(image_url)
        page_url = safe_text(article_url)
        page_source = safe_text(source)
        page_source_url = safe_text(source_url)

        image_html = ""
        if image_url:
            image_html = (
                f'<img class="hero" src="{page_image}" '
                f'alt="{page_title}" loading="eager">'
            )

        source_html = ""
        if source_url:
            source_html = (
                f'<p class="source">সূত্র: '
                f'<a href="{page_source_url}" rel="noopener noreferrer" '
                f'target="_blank">{page_source or "মূল সংবাদ"}</a></p>'
            )
        elif source:
            source_html = f'<p class="source">সূত্র: {page_source}</p>'

        page = f"""<!doctype html>
<html lang="bn">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{page_title} | ছবি বার্তা</title>
<meta name="description" content="{page_summary}">
<link rel="canonical" href="{page_url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="ছবি বার্তা">
<meta property="og:title" content="{page_title}">
<meta property="og:description" content="{page_summary}">
<meta property="og:url" content="{page_url}">
<meta property="og:image" content="{page_image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{page_title}">
<meta name="twitter:des…
