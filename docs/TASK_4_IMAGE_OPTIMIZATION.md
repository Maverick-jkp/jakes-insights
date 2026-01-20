# Task 4: 이미지 최적화 (Image Optimization)

**작업 기간**: 2일
**우선순위**: High
**담당**: Claude Code

---

## 목표

1. WebP 포맷으로 변환하여 60-70% 용량 감소
2. Responsive images로 디바이스별 적절한 크기 제공
3. Lazy loading으로 초기 로딩 속도 향상
4. Unsplash API에서 적절한 크기로 다운로드

**예상 효과:**
- 이미지 용량: 18MB → 7MB (60% 절감)
- 페이지 로딩 속도: 2.5초 → 1.2초 (50% 향상)
- Lighthouse 점수: 75 → 90+ (SEO 향상)

---

## Task 4.1: Hugo Image Processing 설정 (Day 1 오전)

### 작업 내용

#### 1. Hugo Config 수정

**파일**: `hugo.toml`

```toml
# 기존 내용 유지하고 아래 섹션 추가

[imaging]
  # Image processing quality
  quality = 85

  # Resampling filter (Lanczos is best quality)
  resampleFilter = "Lanczos"

  # Anchor point for cropping (Smart = auto-detect focus point)
  anchor = "Smart"

  # Background color for transparent images
  bgColor = "#ffffff"

  # Hint for image processing
  hint = "photo"

[imaging.exif]
  # Keep date info but remove GPS data
  disableDate = false
  disableLatLong = true
  includeFields = ""
  excludeFields = ""
```

#### 2. 이미지를 Page Resource로 변환

**현재 구조 (문제):**
```
static/images/
  ├── ai-coding-tools.jpg
  ├── digital-minimalism.jpg
  └── ...
```
→ Hugo가 Page Resource로 인식 못함 (image processing 불가)

**개선 구조:**
```
content/
  ├── en/
  │   ├── tech/
  │   │   ├── ai-coding-tools/
  │   │   │   ├── index.md
  │   │   │   └── cover.jpg
  │   │   └── digital-minimalism/
  │   │       ├── index.md
  │   │       └── cover.jpg
```
→ Hugo가 Page Bundle로 인식 (image processing 가능)

**마이그레이션 스크립트**: `scripts/convert_to_page_bundles.py` (신규 생성)

```python
#!/usr/bin/env python3
"""
Convert posts to page bundles for Hugo image processing.

Before:
  content/en/tech/ai-coding-tools.md
  static/images/ai-coding-tools.jpg

After:
  content/en/tech/ai-coding-tools/index.md
  content/en/tech/ai-coding-tools/cover.jpg
"""
import os
import shutil
from pathlib import Path

def convert_to_page_bundle(md_file_path: str, static_images_dir: str):
    """Convert a single markdown file to a page bundle."""

    md_path = Path(md_file_path)

    # Create bundle directory
    bundle_dir = md_path.parent / md_path.stem
    bundle_dir.mkdir(exist_ok=True)

    # Move markdown to index.md
    index_path = bundle_dir / "index.md"
    shutil.move(str(md_path), str(index_path))

    # Read frontmatter to find image
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract image path from frontmatter
    import re
    image_match = re.search(r'image:\s*["\']?([^"\'\n]+)["\']?', content)

    if image_match:
        image_path = image_match.group(1)
        # /images/ai-coding-tools.jpg -> ai-coding-tools.jpg
        image_filename = Path(image_path).name

        # Find image in static/images/
        source_image = Path(static_images_dir) / image_filename

        if source_image.exists():
            # Copy image to bundle as cover.jpg
            dest_image = bundle_dir / "cover.jpg"
            shutil.copy2(str(source_image), str(dest_image))

            # Update frontmatter to use relative path
            new_content = content.replace(
                f'image: {image_path}',
                'image: cover.jpg'
            )

            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            print(f"✅ Converted: {md_path.name} → {bundle_dir.name}/")
        else:
            print(f"⚠️  Image not found: {source_image}")
    else:
        print(f"⚠️  No image found in frontmatter: {md_path}")

def main():
    """Convert all posts to page bundles."""

    content_dir = Path("content")
    static_images_dir = "static/images"

    # Process all markdown files
    for lang in ['en', 'ko', 'ja']:
        lang_dir = content_dir / lang

        for category_dir in lang_dir.iterdir():
            if not category_dir.is_dir():
                continue

            for md_file in category_dir.glob("*.md"):
                # Skip if already a bundle (index.md)
                if md_file.name == "index.md":
                    continue

                convert_to_page_bundle(str(md_file), static_images_dir)

    print("\n✅ Conversion complete!")
    print("Next steps:")
    print("1. Test locally: hugo server -D")
    print("2. Verify images display correctly")
    print("3. Commit changes")

if __name__ == '__main__':
    main()
```

**실행:**
```bash
python scripts/convert_to_page_bundles.py
hugo server -D  # 로컬 테스트
```

---

## Task 4.2: Responsive Images 레이아웃 적용 (Day 1 오후)

### 작업 내용

#### 1. Single Post 레이아웃 수정

**파일**: `layouts/_default/single.html`

**현재 (문제):**
```html
<img src="{{ .Params.image }}" alt="{{ .Title }}">
```

**개선 (responsive + WebP):**
```html
{{/* Hero Image - Responsive WebP with fallback */}}
{{ with .Resources.GetMatch "cover.*" }}
  {{ $small := .Resize "400x webp q85" }}
  {{ $medium := .Resize "800x webp q85" }}
  {{ $large := .Resize "1200x webp q85" }}
  {{ $fallback := .Resize "800x jpg q85" }}

  <picture>
    <source
      srcset="{{ $small.RelPermalink }} 400w,
              {{ $medium.RelPermalink }} 800w,
              {{ $large.RelPermalink }} 1200w"
      sizes="(max-width: 600px) 400px,
             (max-width: 1200px) 800px,
             1200px"
      type="image/webp"
    >
    <img
      src="{{ $fallback.RelPermalink }}"
      alt="{{ $.Title }}"
      loading="lazy"
      width="{{ $medium.Width }}"
      height="{{ $medium.Height }}"
      style="width: 100%; height: auto; object-fit: cover;"
    >
  </picture>
{{ end }}
```

**적용 위치**: Hero image 섹션 (파일 상단 ~ 라인 150 부근)

#### 2. List/Homepage 썸네일 수정

**파일**: `layouts/index.html`

**현재 (문제):**
```html
<img src="{{ .Params.image }}" alt="{{ .Title }}">
```

**개선 (thumbnail용 작은 크기):**
```html
{{/* Thumbnail - Optimized for card display */}}
{{ with .Resources.GetMatch "cover.*" }}
  {{ $thumb := .Fill "400x300 webp q85" }}
  {{ $thumb2x := .Fill "800x600 webp q85" }}
  {{ $fallback := .Fill "400x300 jpg q85" }}

  <picture>
    <source
      srcset="{{ $thumb.RelPermalink }} 1x,
              {{ $thumb2x.RelPermalink }} 2x"
      type="image/webp"
    >
    <img
      src="{{ $fallback.RelPermalink }}"
      alt="{{ $.Title }}"
      loading="lazy"
      width="400"
      height="300"
      style="width: 100%; height: 100%; object-fit: cover;"
    >
  </picture>
{{ end }}
```

**적용 위치**:
- Featured post card (라인 300-400)
- Latest posts grid (라인 500-600)
- Small cards (라인 700-800)

#### 3. Category List 페이지 수정

**파일**: `layouts/categories/list.html`

동일한 패턴으로 썸네일 최적화 적용.

---

## Task 4.3: Unsplash API 최적화 (Day 2 오전)

### 작업 내용

#### 1. generate_posts.py 수정

**파일**: `scripts/generate_posts.py`

**현재 (문제):**
```python
# Full resolution download (100-200KB)
download_url = f"https://api.unsplash.com/photos/{photo_id}/download"
response = requests.get(download_url, ...)
```

**개선 (적절한 크기로 다운로드):**
```python
def download_optimized_image(photo_id: str, width: int = 1200, quality: int = 85) -> bytes:
    """
    Download optimized image from Unsplash.

    Args:
        photo_id: Unsplash photo ID
        width: Target width in pixels (default: 1200)
        quality: JPEG quality 1-100 (default: 85)

    Returns:
        Image bytes
    """
    # Trigger download event (required by Unsplash API)
    trigger_url = f"https://api.unsplash.com/photos/{photo_id}/download"
    requests.get(trigger_url, headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"})

    # Download optimized version
    # w=1200: width, q=85: quality, fm=jpg: format
    optimized_url = f"https://images.unsplash.com/photo-{photo_id}?w={width}&q={quality}&fm=jpg"

    response = requests.get(optimized_url, timeout=30)
    response.raise_for_status()

    return response.content

# 사용 예시
image_data = download_optimized_image(photo_id, width=1200, quality=85)
```

**변경 위치**: `download_image()` 함수 (라인 800-850)

#### 2. 기존 이미지 재다운로드 스크립트

**파일**: `scripts/redownload_optimized_images.py` (신규 생성)

```python
#!/usr/bin/env python3
"""
Re-download existing images from Unsplash with optimized size.

This script:
1. Scans all post bundles for cover.jpg
2. Extracts Unsplash photo ID from image credits
3. Re-downloads with optimized parameters (w=1200, q=85)
4. Replaces existing image
"""
import os
import re
import requests
from pathlib import Path
from time import sleep

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

def extract_photo_id_from_post(post_path: Path) -> str:
    """Extract Unsplash photo ID from post frontmatter."""

    with open(post_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Look for Unsplash URL in credits
    # Example: https://unsplash.com/photos/abc123xyz
    match = re.search(r'unsplash\.com/photos/([a-zA-Z0-9_-]+)', content)

    if match:
        return match.group(1)

    return None

def redownload_image(bundle_dir: Path):
    """Re-download optimized image for a post bundle."""

    index_md = bundle_dir / "index.md"
    cover_jpg = bundle_dir / "cover.jpg"

    if not index_md.exists() or not cover_jpg.exists():
        return

    photo_id = extract_photo_id_from_post(index_md)

    if not photo_id:
        print(f"⚠️  No Unsplash ID found: {bundle_dir.name}")
        return

    try:
        # Trigger download event
        trigger_url = f"https://api.unsplash.com/photos/{photo_id}/download"
        requests.get(trigger_url, headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"})

        # Download optimized version
        optimized_url = f"https://images.unsplash.com/photo-{photo_id}?w=1200&q=85&fm=jpg"
        response = requests.get(optimized_url, timeout=30)
        response.raise_for_status()

        # Save
        with open(cover_jpg, 'wb') as f:
            f.write(response.content)

        # Get file size
        size_kb = cover_jpg.stat().st_size / 1024

        print(f"✅ {bundle_dir.name}: {size_kb:.1f} KB")

        # Rate limiting
        sleep(1)

    except Exception as e:
        print(f"❌ {bundle_dir.name}: {e}")

def main():
    """Re-download all images with optimization."""

    if not UNSPLASH_ACCESS_KEY:
        print("❌ UNSPLASH_ACCESS_KEY not set")
        return

    content_dir = Path("content")

    total = 0

    for lang in ['en', 'ko', 'ja']:
        lang_dir = content_dir / lang

        for category_dir in lang_dir.iterdir():
            if not category_dir.is_dir():
                continue

            for bundle_dir in category_dir.iterdir():
                if not bundle_dir.is_dir():
                    continue

                redownload_image(bundle_dir)
                total += 1

    print(f"\n✅ Processed {total} images")

if __name__ == '__main__':
    main()
```

**실행:**
```bash
export UNSPLASH_ACCESS_KEY='your-key'
python scripts/redownload_optimized_images.py
```

---

## Task 4.4: Lazy Loading 및 성능 측정 (Day 2 오후)

### 작업 내용

#### 1. Lazy Loading 확인

위의 레이아웃 수정에서 이미 `loading="lazy"` 속성을 추가했는데, 이것만으로도 충분합니다.

```html
<img loading="lazy" ...>
```

**작동 원리:**
- 브라우저가 자동으로 viewport에 보이는 이미지만 로드
- 스크롤하면 추가 로드
- JavaScript 불필요 (Native browser feature)

#### 2. 성능 측정 스크립트

**파일**: `scripts/measure_image_performance.py` (신규 생성)

```python
#!/usr/bin/env python3
"""
Measure image optimization impact.

Compares:
- Before: static/images/*.jpg (original)
- After: content/**/cover.jpg (optimized)
"""
from pathlib import Path

def get_total_size(directory: Path, pattern: str) -> int:
    """Get total size of all files matching pattern."""
    total = 0
    for file in directory.rglob(pattern):
        total += file.stat().st_size
    return total

def main():
    static_dir = Path("static/images")
    content_dir = Path("content")

    # Before: static/images
    before_size = 0
    if static_dir.exists():
        before_size = get_total_size(static_dir, "*.jpg")

    # After: content bundles
    after_size = get_total_size(content_dir, "cover.jpg")

    # Hugo generated
    resources_dir = Path("resources/_gen/images")
    webp_size = 0
    if resources_dir.exists():
        webp_size = get_total_size(resources_dir, "*.webp")

    print("📊 Image Optimization Results\n")
    print(f"Before (original):    {before_size / 1024 / 1024:.2f} MB")
    print(f"After (optimized):    {after_size / 1024 / 1024:.2f} MB")
    print(f"WebP generated:       {webp_size / 1024 / 1024:.2f} MB")
    print(f"\nSavings:              {(before_size - after_size) / 1024 / 1024:.2f} MB ({(1 - after_size/before_size) * 100:.1f}%)")

if __name__ == '__main__':
    main()
```

**실행:**
```bash
hugo  # Generate WebP versions
python scripts/measure_image_performance.py
```

#### 3. Lighthouse 성능 측정

```bash
# Install Lighthouse CLI
npm install -g lighthouse

# Start local server
hugo server &

# Run Lighthouse
lighthouse http://localhost:1313 --output=json --output-path=./lighthouse-report.json

# View report
lighthouse http://localhost:1313 --view
```

**측정 항목:**
- Performance score
- First Contentful Paint (FCP)
- Largest Contentful Paint (LCP)
- Cumulative Layout Shift (CLS)
- Total image weight

---

## 검증 방법

### Day 1 완료 후 체크리스트

```bash
# 1. Page bundles 생성 확인
ls -la content/en/tech/
# Expected: 디렉토리 형태 (ai-coding-tools/, digital-minimalism/, ...)

# 2. Hugo 빌드 테스트
hugo server -D
# http://localhost:1313 접속

# 3. 이미지 표시 확인
# - 모든 포스트 이미지가 정상 표시되는지
# - 썸네일이 정상 표시되는지

# 4. Resources 생성 확인
ls -la resources/_gen/images/
# Expected: WebP 파일들이 자동 생성됨
```

### Day 2 완료 후 체크리스트

```bash
# 1. 이미지 크기 확인
du -sh content/*/tech/*/cover.jpg
# Expected: 각 이미지 40-80KB

# 2. 전체 용량 측정
python scripts/measure_image_performance.py
# Expected: 60%+ savings

# 3. Lighthouse 점수 확인
lighthouse http://localhost:1313
# Expected: Performance 90+

# 4. 모바일 테스트
# Chrome DevTools → Toggle device toolbar → iPhone 12
# Network tab에서 다운로드 크기 확인
```

---

## 예상 결과

### Before (현재)

```
이미지 구조:
  static/images/ai-coding-tools.jpg (150KB)

HTML:
  <img src="/images/ai-coding-tools.jpg" alt="...">

브라우저 다운로드:
  Desktop: 150KB
  Mobile: 150KB (동일)

페이지 로딩:
  FCP: 1.8s
  LCP: 2.5s
  Total image weight: 18MB
```

### After (개선)

```
이미지 구조:
  content/en/tech/ai-coding-tools/cover.jpg (60KB, optimized source)
  resources/_gen/images/cover_400x.webp (25KB)
  resources/_gen/images/cover_800x.webp (50KB)
  resources/_gen/images/cover_1200x.webp (80KB)

HTML:
  <picture>
    <source srcset="cover_400x.webp 400w, ..." type="image/webp">
    <img src="cover_800x.jpg" loading="lazy">
  </picture>

브라우저 다운로드:
  Desktop: 50KB (WebP)
  Mobile: 25KB (WebP, 400px)

페이지 로딩:
  FCP: 0.9s (50% faster)
  LCP: 1.2s (52% faster)
  Total image weight: 7MB (61% smaller)
```

---

## 회귀 방지

이 작업 후 다음 규칙 준수:

1. **새 포스트는 Page Bundle로 생성**: `content/lang/category/post-name/index.md`
2. **이미지는 bundle 내부에**: `content/lang/category/post-name/cover.jpg`
3. **Unsplash 다운로드 시 최적화 파라미터 사용**: `w=1200&q=85`

**generate_posts.py 수정 필요**: 새 포스트 생성 시 자동으로 bundle 구조 생성

---

## 비용

- **개발 시간**: 2일
- **유지보수 오버헤드**: 낮음 (한번 설정하면 자동)
- **디스크 공간**: Hugo가 여러 크기 생성하므로 약간 증가 (+5MB)
- **빌드 시간**: 약간 증가 (+10초, 첫 빌드만)
- **금전 비용**: $0

---

## 참고 문서

- [Hugo Image Processing](https://gohugo.io/content-management/image-processing/)
- [Responsive Images - MDN](https://developer.mozilla.org/en-US/docs/Learn/HTML/Multimedia_and_embedding/Responsive_images)
- [WebP Format](https://developers.google.com/speed/webp)
- [Lazy Loading](https://web.dev/lazy-loading/)
