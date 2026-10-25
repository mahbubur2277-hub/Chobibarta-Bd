import html
import json
import re
from pathlib import Path
from urllib.parse import quote

BASE_URL = "https://chobibartabd.online"
DATA_FILE = Path("headline-news/index.json")
OUTPUT_DIR = Path("news")


def safe_text(value):
    """Escape text safely for use in HTML."""
    return html.escape(str(value or "").strip(), quote=True)


def make_slug(record, index):
    """Create a safe, unique-friendly filename for an article."""
    title = str(
        record.get("title_en")
        or record.get("title_bn")
        or "news"
    ).strip()

    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")

    if not slug:
        date = re.sub(
            r"[^0-9]",
            "",
            str(record.get("date") or "")
        )
        slug = f"news-{date}" if date else f"news-{index}"

    return slug[:90].strip("-") or f"news-{index}"


def main():
    if not DATA_FILE.exists():
        raise SystemExit(
            "ERROR: headline-news/index.json was not found."
        )

    try:
        items = json.loads(
            DATA_FILE.read_text(encoding="utf-8")
        )
    except (json.JSONDecodeError, OSError) as exc:
        raise SystemExit(f"ERROR: Cannot read headline JSON: {exc}")

    if not isinstance(items, list):
        raise SystemExit(
            "ERROR: Headline JSON must contain a list."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    used_slugs = set()
    generated = 0

    for index, item in enumerate(items, start=1):
        # Never generate a public article from unapproved news.
        if not isinstance(item, dict):
            continue

        if item.get("approved") is not True:
            continue

        title_bn = str(item.get("title_bn") or "").strip()
        title_en = str(item.get("title_en") or "").strip()
        title = title_bn or title_en

        if not title:
            print(f"Skipping approved item {index}: no title.")
            continue

        # Ensure each generated filename is unique.
        original_slug = make_slug(item, index)
        slug = original_slug
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

        # Allow absolute image URLs or site-relative image paths.
        if image and not image.startswith(
            ("https://", "http://", "/")
        ):
            image = "/" + image

        source = str(item.get("source") or "").strip()
        source_url = str(
            item.get("source_url") or item.get("url") or ""
        ).strip()

        # Only create clickable source links for HTTP(S) URLs.
        if not source_url.startswith(("https://", "http://")):
            source_url = ""

        article_url = f"{BASE_URL}/news/{quote(slug)}.html"

        if image.startswith(("https://", "http://")):
            image_url = image
        elif image:
            image_url = BASE_URL + image
        else:
            image_url = ""

        page_title = safe_text(title)
        page_summary = safe_text(summary)
        page_image = safe_text(image_url)
        page_url = safe_text(article_url)
        page_source = safe_text(source)

        image_html = ""
        if image_url:
            image_html = (
                f'<img class="hero" src="{page_image}" '
                f'alt="{page_title}" loading="eager">'
            )

        source_html = ""
        if source_url:
            page_source_url = safe_text(source_url)
            source_label = page_source or "মূল সংবাদ"
            source_html = (
                '<p class="source">সূত্র: '
                f'<a href="{page_source_url}" '
                'target="_blank" rel="noopener noreferrer">'
                f'{source_label}</a></p>'
            )
        elif source:
            source_html = (
                f'<p class="source">সূত্র: {page_source}</p>'
            )

        # The doubled braces below are required by Python f-strings.
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
<meta name="twitter:description" content="{page_summary}">
<meta name="twitter:image" content="{page_image}">
<style>
* {{
    box-sizing: border-box;
}}
body {{
    margin: 0;
    background: #f4f6f8;
    color: #222;
    font-family: Arial, "Noto Sans Bengali", sans-serif;
    line-height: 1.85;
}}
.site-header {{
    background: #a71920;
    color: white;
    padding: 16px 20px;
    border-bottom: 4px solid #e4b23c;
}}
.header-inner {{
    max-width: 1000px;
    margin: auto;
}}
.site-name {{
    margin: 0;
    font-size: 28px;
    font-weight: bold;
}}
.site-name a {{
    color: white;
    text-decoration: none;
}}
.site-subtitle {{
    margin: 2px 0 0;
    font-size: 14px;
}}
.container {{
    max-width: 900px;
    margin: 28px auto;
    padding: 0 16px;
}}
.article {{
    background: white;
    padding: 28px;
    border: 1px solid #e3e6e8;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}}
h1 {{
    margin: 0 0 20px;
    color: #20252a;
    font-size: clamp(25px, 4vw, 36px);
    line-height: 1.55;
}}
.hero {{
    display: block;
    width: 100%;
    height: auto;
    max-height: 520px;
    object-fit: contain;
    margin: 0 auto 24px;
    border-radius: 6px;
}}
.summary {{
    font-size: 19px;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
}}
.source {{
    margin-top: 28px;
    padding-top: 14px;
    border-top: 1px solid #ddd;
    color: #555;
    font-size: 15px;
}}
.source a {{
    color: #a71920;
    text-decoration: none;
}}
.source a:hover {{
    text-decoration: underline;
}}
.site-footer {{
    max-width: 900px;
    margin: 0 auto;
    padding: 0 16px 30px;
    text-align: center;
    color: #666;
    font-size: 14px;
}}
.site-footer a {{
    color: #a71920;
}}
@media (max-width: 600px) {{
    .container {{
        margin: 16px auto;
    }}
    .article {{
        padding: 18px;
    }}
    .site-name {{
        font-size: 24px;
    }}
    .summary {{
        font-size: 17px;
    }}
}}
</style>
</head>
<body>
<header class="site-header">
  <div class="header-inner">
    <p class="site-name">
      <a href="{BASE_URL}/">ছবি বার্তা</a>
    </p>
    <p class="site-subtitle">সত্য ও নির্ভরযোগ্য সংবাদ</p>
  </div>
</header>
<main class="container">
  <article class="article">
    <h1>{page_title}</h1>
    {image_html}
    <div class="summary">{page_summary}</div>
    {source_html}
  </article>
</main>
<footer class="site-footer">
  <p><a href="{BASE_URL}/">ছবি বার্তা</a> — মূল ওয়েবসাইটে ফিরে যান</p>
</footer>
</body>
</html>
"""

        output_file = OUTPUT_DIR / f"{slug}.html"
        output_file.write_text(page, encoding="utf-8")
        generated += 1

        print(f"Generated: {output_file}")

    print(f"Finished: generated {generated} approved article pages.")


if _name_ == "_main_":
    main()
