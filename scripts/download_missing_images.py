#!/usr/bin/env python3
"""
Download missing images for posts based on their titles and categories.
"""
import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY")
if not UNSPLASH_ACCESS_KEY:
    print("❌ UNSPLASH_ACCESS_KEY not set")
    sys.exit(1)

# Map each missing image filename → best search query
IMAGE_QUERIES = {
    "20260211-f1.jpg": "formula 1 racing car speed",
    "20260211-lg전자-주가.jpg": "stock market finance chart",
    "20260211-seamus-culleton-ice-detention.jpg": "immigration detention law justice",
    "20260211-코딩-부트캠프-추천.jpg": "coding bootcamp programming laptop",
    "20260212-car-accident-attorney.jpg": "car accident law attorney",
    "20260212-ryan-beiermeister.jpg": "artificial intelligence OpenAI technology",
    "20260212-국시원.jpg": "medical exam certification study",
    "20260212-클라우드-컴퓨팅-기초.jpg": "cloud computing server technology",
    "20260213-ai-in-healthcare.jpg": "AI healthcare hospital medical technology",
    "20260213-ai-입문-가이드.jpg": "artificial intelligence beginner guide technology",
    "20260213-nh.jpg": "winter storm infrastructure snow",
    "20260213-고양시장.jpg": "city hall government election politics",
    "20260213-명절.jpg": "korean traditional holiday family celebration",
    "20260214-ai-에이전트.jpg": "AI agent automation robot technology",
    "20260214-ai-코딩-도구-2026.jpg": "AI coding tools developer software",
    "20260214-cursor-ai-editor.jpg": "code editor programming software development",
    "20260214-donotnotify.jpg": "smartphone notification app mobile",
    "20260214-james-franco.jpg": "hollywood actor film entertainment",
    "20260214-localgpt.jpg": "local AI model privacy computing",
    "20260214-printer-driver.jpg": "printer technology hardware office",
}

def fetch_and_download(filename, query, output_dir):
    output_path = output_dir / filename
    if output_path.exists():
        print(f"  ✓ Already exists: {filename}")
        return True

    print(f"  🔍 {filename} ← \"{query}\"")

    url = "https://api.unsplash.com/search/photos"
    headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
    params = {"query": query, "per_page": 3, "orientation": "landscape"}

    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        results = r.json().get("results", [])
        if not results:
            print(f"  ⚠️  No results for: {query}")
            return False

        photo = results[0]
        img_url = photo["urls"]["regular"]
        photographer = photo["user"]["name"]

        img_r = requests.get(img_url, timeout=30)
        img_r.raise_for_status()
        output_path.write_bytes(img_r.content)
        print(f"  ✅ Downloaded ({photographer}): {filename}")

        # Unsplash download tracking (required by API terms)
        try:
            requests.get(photo["links"]["download_location"],
                         headers=headers, timeout=5)
        except Exception:
            pass

        return True

    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False


def main():
    output_dir = Path("/Users/jake/jakes-insights/static/images")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"🖼️  Downloading {len(IMAGE_QUERIES)} images to {output_dir}\n")
    ok, fail = 0, 0
    for filename, query in IMAGE_QUERIES.items():
        if fetch_and_download(filename, query, output_dir):
            ok += 1
        else:
            fail += 1

    print(f"\n✅ Done — {ok} downloaded, {fail} failed")


if __name__ == "__main__":
    main()
