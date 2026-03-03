#!/usr/bin/env python3
"""One-time: download real images for side-income posts that got placeholders."""
import os, re, requests
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
load_dotenv()

try:
    import certifi
    verify_ssl = certifi.where()
except ImportError:
    verify_ssl = True

unsplash_key = os.environ.get("UNSPLASH_ACCESS_KEY")
if not unsplash_key:
    print("❌ UNSPLASH_ACCESS_KEY not set")
    exit(1)

headers = {"Authorization": f"Client-ID {unsplash_key}"}
KST = timezone(timedelta(hours=9))
NOW = datetime.now(KST)

FALLBACKS = {
    "freelancing":      "freelance work laptop",
    "digital-products": "digital product laptop",
    "ai-income":        "artificial intelligence laptop",
}

broken = [
    ("content/en/side-income/2026-03-03-how-developers-make-50hr-on-upwork-in-2026.md",
     "Upwork freelance developer", "freelancing"),
    ("content/en/side-income/2026-03-03-claude-api-side-project-that-makes-money.md",
     "AI API side project", "ai-income"),
    ("content/en/side-income/2026-03-03-sell-notion-templates-on-gumroad-step-by-step.md",
     "Notion templates digital product", "digital-products"),
    ("content/ko/side-income/2026-03-03-개발자-upwork-시작하는-법-한국에서-가능한가.md",
     "freelance developer laptop", "freelancing"),
    ("content/ko/side-income/2026-03-03-노션-템플릿-판매로-월-수익-내는-실제-방법.md",
     "Notion template digital", "digital-products"),
]

for md_path, query, subtopic in broken:
    photo = None
    for q in [query, FALLBACKS.get(subtopic, "developer laptop money")]:
        resp = requests.get("https://api.unsplash.com/search/photos",
            params={"query": q, "per_page": 3, "orientation": "landscape"},
            headers=headers, timeout=10, verify=verify_ssl)
        results = resp.json().get("results", [])
        if results:
            photo = results[0]
            if q != query:
                print(f"  ℹ️  Fallback: '{q}'")
            break

    if not photo:
        print(f"  ✗ No image found: {Path(md_path).name}")
        continue

    image_url = photo["urls"]["regular"]
    dl_url = photo["links"]["download_location"]
    photographer = photo["user"]["name"]
    photographer_url = photo["user"]["links"]["html"]
    unsplash_url = photo["links"]["html"]
    requests.get(dl_url, headers=headers, timeout=5, verify=verify_ssl)

    slug = re.sub(r'[^a-z0-9\s-]', '', query.lower())[:30].strip().replace(' ', '-')
    filename = f"{NOW.strftime('%Y%m%d')}-{slug}.webp"
    filepath = Path("static/images") / filename
    img_resp = requests.get(f"{image_url}?w=1200&q=85&fm=webp", timeout=15, verify=verify_ssl)
    filepath.write_bytes(img_resp.content)
    print(f"  ✓ {filename} ({len(img_resp.content)/1024:.0f}KB)")

    text = Path(md_path).read_text(encoding="utf-8")
    text = re.sub(r'^image: ".*"', f'image: "/images/{filename}"', text, flags=re.MULTILINE)
    credit = f'\n\n---\n\n*Photo by [{photographer}]({photographer_url}) on [Unsplash]({unsplash_url})*\n'
    if re.search(r'\*Photo by ', text):
        text = re.sub(r'\n\n---\n\n\*Photo by.*?\*\n', credit, text, flags=re.DOTALL)
    else:
        text = text.rstrip() + credit
    Path(md_path).write_text(text, encoding="utf-8")
    print(f"  ✓ Updated: {Path(md_path).name[:50]}")

print("\nDone!")
