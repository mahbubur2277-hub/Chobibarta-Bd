import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
import xml.etree.ElementTree as ET
from openai import OpenAI


# Only add feeds after checking access and reuse terms.
FEEDS = {
    "BBC News বাংলা": "https://feeds.bbci.co.uk/bengali/rss.xml",
    "Dhaka Tribune": "https://www.dhakatribune.com/articles/rss/home",
    "bdnews24.com": "https://bdnews24.com/?getXmlFeed=true&widgetId=1150&widgetName=rssfeed",
}

output_dir = Path("review")
output_dir.mkdir(exist_ok=True)
items = []
seen = set()


def has_bengali(text):
    return any("\u0980" <= char <= "\u09FF" for char in (text or ""))


OPENAI_FAILED= False


def translate_to_english(text):
    global OPENAI_FAILED

    text = (text or "").strip()
    if not text:
        return ""

    if not has_bengali(text):
        return text

    # 1. Google Translate is the primary service.
    google_key = os.getenv("GOOGLE_TRANSLATE_API_KEY")

    if google_key:
        try:
            payload = json.dumps({
                "q": text,
                "target": "en",
                "format": "text",
            }).encode("utf-8")

            request = Request(
                "https://translation.googleapis.com/language/translate/v2",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-goog-api-key": google_key,
                },
                method="POST",
            )

            with urlopen(request, timeout=20) as response:
                result = json.loads(
                    response.read().decode("utf-8")
                )

            translations = result.get("data", {}).get(
                "translations", []
            )

            if translations:
                translated = (
                    translations[0].get("translatedText") or ""
                ).strip()

                if translated:
                    print("Translation succeeded with Google Translate.")
                    return translated

        except Exception as exc:
            print(f"Google Translate failed; trying backup: {exc}")
    else:
        print("Google Translate key is missing; trying backup.")

    # 2. OpenAI is an optional backup.
    if not OPENAI_FAILED:
        try:
            client = OpenAI()
            response = client.responses.create(
                model="gpt-4.1-mini",
                input=(
                    "Translate this Bengali news text into accurate, "
                    "natural English. Preserve names and facts. "
                    "Return only the translation:\n\n" + text
                ),
            )

            translated = response.output_text
            if translated and translated.strip():
                print("Translation succeeded with OpenAI.")
                return translated.strip()

        except Exception as exc:
            print(f"OpenAI translation failed; trying free backup: {exc}")
            OPENAI_FAILED = True

    # 3. Optional free community translation services.
    endpoints = [
        "https://translate.fedilab.app/translate",
        "https://translate.cutie.dating/translate",
    ]

    for endpoint in endpoints:
        try:
            data = urlencode({
                "q": text,
                "source": "auto",
                "target": "en",
                "format": "text",
            }).encode("utf-8")

            request = Request(
                endpoint,
                data=data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                method="POST",
            )

            with urlopen(request, timeout=20) as response:
                result = json.loads(
                    response.read().decode("utf-8")
                )

            translated = (
                result.get("translatedText") or ""
            ).strip()

            if translated:
                print("Translation succeeded with a free backup.")
                return translated

        except Exception as exc:
            print(f"Free translation backup failed: {exc}")

    print("All translation services failed; manual review needed.")
    return ""
        
    
for source, url in FEEDS.items():
    try:
        request = Request(url, headers={"User-Agent": "ChobiBartaBD-NewsReader/1.0"})
        with urlopen(request, timeout=20) as response:
            root = ET.fromstring(response.read())

        for entry in root.findall(".//item"):
            title = (entry.findtext("title") or "").strip()
            link = (entry.findtext("link") or "").strip()
            description = (entry.findtext("description") or "").strip()

            if not title or not link or link in seen:
                continue

            seen.add(link)
            items.append({
                "source": source,
                "title_original": title,
                "summary_original": description,
                "source_url": link,
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "status": "needs_review",
                
            "title_en": translate_to_english(title) or title,
                "title_bn": title,
                "summary_en": translate_to_english(description) or description,
                "summary_bn": description,


                
                
                
        
                "approved": False
            })

    except Exception as exc:
        print(f"Could not collect {source}: {exc}")

for index, item in enumerate(items, start=1):
    filename = f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-{index:03d}.json"
    (output_dir / filename).write_text(
        json.dumps(item, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

print(f"Saved {len(items)} headlines for review.")

    
    


print(f"Saved {len(items)} headlines for review.")
