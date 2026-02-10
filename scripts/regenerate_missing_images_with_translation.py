#!/usr/bin/env python3
"""
Regenerate missing images with English keyword translation

For CJK keywords that don't have images on Unsplash,
translate them to generic English keywords based on context.
"""

import os
import re
import json
import requests
import certifi
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

# Load config
UNSPLASH_KEY = os.environ.get('UNSPLASH_ACCESS_KEY')
if not UNSPLASH_KEY:
    print("❌ Error: UNSPLASH_ACCESS_KEY not found in environment")
    exit(1)

# Keyword translation mapping (CJK → English)
KEYWORD_TRANSLATION = {
    # Korean
    '붉은사막': 'desert video game',
    '뉴진스': 'kpop girl group',
    '유시민': 'korean politician',
    '이관희 홍진경': 'korean celebrity couple',
    '실리콘투': 'silicon valley technology',
    '신지': 'korean celebrity',
    '캐시워크 정답': 'mobile app quiz',
    '강원기': 'korean business executive',
    '경상대': 'korean university campus',
    '양승태': 'korean judge court',
    '창원대': 'korean university campus',
    '지석진': 'korean variety show host',
    '부산대학교': 'korean university campus',
    '부산대': 'korean university campus',
    '중앙대': 'korean university campus',
    '원더맨': 'marvel superhero',
    '연세대': 'korean university campus',
    '전남대': 'korean university campus',
    '오태석': 'korean theater director'
}

def find_posts_with_missing_images() -> List[Dict]:
    """Find all posts with missing image files"""
    posts = []

    for post_path in Path('content').rglob('*.md'):
        with open(post_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract frontmatter
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not match:
            continue

        frontmatter = match.group(1)

        # Extract image path
        image_match = re.search(r'^image:\s*["\']?(.+?)["\']?$', frontmatter, re.MULTILINE)
        if not image_match:
            continue

        image_path = image_match.group(1).strip()
        full_path = Path('static') / image_path.lstrip('/')

        if not full_path.exists():
            # Extract keyword from tags
            tags_match = re.search(r'^tags:\s*(\[.*?\])$', frontmatter, re.MULTILINE)
            keyword = None

            if tags_match:
                try:
                    tags = json.loads(tags_match.group(1))
                    keyword = ' '.join(tags) if tags else None
                except json.JSONDecodeError:
                    pass

            # Extract category
            category_match = re.search(r'^categories:\s*\["(.+?)"\]', frontmatter, re.MULTILINE)
            category = category_match.group(1) if category_match else 'general'

            posts.append({
                'post_path': str(post_path),
                'post_name': post_path.name,
                'image_path': image_path,
                'keyword': keyword,
                'category': category
            })

    return posts

def translate_keyword(keyword: str, category: str) -> str:
    """Translate CJK keyword to English or return generic keyword"""
    # Check if keyword is in translation map
    if keyword in KEYWORD_TRANSLATION:
        return KEYWORD_TRANSLATION[keyword]

    # Generic fallback based on category
    category_fallback = {
        'entertainment': 'entertainment celebrity lifestyle',
        'society': 'society news people',
        'tech': 'technology innovation digital',
        'business': 'business corporate professional',
        'sports': 'sports competition athlete',
        'finance': 'finance money investment',
        'lifestyle': 'lifestyle people modern',
        'education': 'education learning school'
    }

    return category_fallback.get(category, 'news people')

def fetch_unsplash_image(keyword: str, category: str) -> Optional[Dict]:
    """Fetch image from Unsplash API"""
    if not keyword:
        return None

    # Translate keyword if needed
    search_keyword = translate_keyword(keyword, category)

    try:
        verify_ssl = certifi.where() if certifi else True

        # Search for relevant image
        response = requests.get(
            'https://api.unsplash.com/search/photos',
            params={
                'query': search_keyword,
                'per_page': 1,
                'orientation': 'landscape'
            },
            headers={'Authorization': f'Client-ID {UNSPLASH_KEY}'},
            timeout=10,
            verify=verify_ssl
        )
        response.raise_for_status()

        data = response.json()
        if data.get('results'):
            photo = data['results'][0]
            return {
                'url': photo['urls']['regular'],
                'download_url': photo['links']['download_location'],
                'photographer': photo['user']['name'],
                'photographer_url': photo['user']['links']['html'],
                'photo_url': photo['links']['html']
            }
    except Exception as e:
        print(f"  ⚠️  Unsplash API error: {e}")

    return None

def download_image(image_info: Dict, target_path: str) -> bool:
    """Download image to target path"""
    try:
        # Trigger Unsplash download tracking
        if image_info.get('download_url'):
            verify_ssl = certifi.where() if certifi else True
            requests.get(
                image_info['download_url'],
                headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"},
                timeout=5,
                verify=verify_ssl
            )

        # Download optimized image
        download_url = image_info.get('url', '')
        if '?' in download_url:
            optimized_url = f"{download_url}&w=1200&q=85&fm=jpg"
        else:
            optimized_url = f"{download_url}?w=1200&q=85&fm=jpg"

        verify_ssl = certifi.where() if certifi else True
        response = requests.get(optimized_url, timeout=15, verify=verify_ssl)
        response.raise_for_status()

        # Save image
        target_file = Path('static') / target_path.lstrip('/')
        target_file.parent.mkdir(parents=True, exist_ok=True)

        with open(target_file, 'wb') as f:
            f.write(response.content)

        print(f"  ✅ Downloaded: {target_file.name}")
        return True

    except Exception as e:
        print(f"  ❌ Download failed: {e}")
        return False

def update_used_images_tracking(image_path: str, image_info: Dict):
    """Update used_images.json with new image"""
    try:
        # Load existing data
        used_images_file = Path('data/used_images.json')
        if used_images_file.exists():
            with open(used_images_file, 'r', encoding='utf-8') as f:
                used_images = json.load(f)
        else:
            used_images = []

        # Add new image
        image_filename = Path(image_path).name
        if image_filename not in used_images:
            used_images.append(image_filename)

        # Save
        with open(used_images_file, 'w', encoding='utf-8') as f:
            json.dump(used_images, f, indent=2, ensure_ascii=False)

        # Update metadata
        metadata_file = Path('data/used_images_metadata.json')
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata = {}

        metadata[image_filename] = {
            'photographer': image_info.get('photographer', 'Unknown'),
            'photographer_url': image_info.get('photographer_url', ''),
            'photo_url': image_info.get('photo_url', ''),
            'downloaded_at': datetime.now().isoformat()
        }

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    except Exception as e:
        print(f"  ⚠️  Could not update tracking: {e}")

def main():
    print("🔍 Finding posts with missing images...\n")

    missing_posts = find_posts_with_missing_images()

    if not missing_posts:
        print("✅ No missing images found!")
        return

    print(f"Found {len(missing_posts)} posts with missing images\n")

    success_count = 0
    failed_count = 0

    for i, post in enumerate(missing_posts, 1):
        print(f"[{i}/{len(missing_posts)}] {post['post_name']}")

        if not post['keyword']:
            print(f"  ⚠️  No keyword found, using category: {post['category']}")
            post['keyword'] = post['category']

        print(f"  Original: {post['keyword']}")
        translated = translate_keyword(post['keyword'], post['category'])
        print(f"  Search: {translated}")

        # Fetch image from Unsplash
        image_info = fetch_unsplash_image(post['keyword'], post['category'])

        if not image_info:
            print(f"  ❌ Could not fetch image from Unsplash")
            failed_count += 1
            continue

        # Download image
        if download_image(image_info, post['image_path']):
            update_used_images_tracking(post['image_path'], image_info)
            success_count += 1
        else:
            failed_count += 1

        print()

    print("\n" + "="*60)
    print(f"✅ Success: {success_count}/{len(missing_posts)}")
    print(f"❌ Failed: {failed_count}/{len(missing_posts)}")
    print("="*60)

if __name__ == '__main__':
    main()
