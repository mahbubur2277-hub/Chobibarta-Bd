import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

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
                "title_en": title if not any("\u0980" <= char <= "\u09FF" for char in title) else "",
                "title_bn": title if any("\u0980" <= char <= "\u09FF" for char in title) else "",
                "summary_bn": description if any("\u0980" <= char <= "\u09FF" for char in description) else "",
                
        
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
