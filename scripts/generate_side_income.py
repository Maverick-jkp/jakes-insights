#!/usr/bin/env python3
"""
Side-Income Content Generation Script

Generates blog posts specifically for the side-income track.
- Uses fixed keyword pool from data/side_income_keywords.json
- EN: Written for English-speaking developer audience
- KO: Introduces overseas monetization methods to Korean readers
- Fetches HN/Reddit-style context for freshness
- Daily: 2 EN + 2 KO posts (configurable via --count)

Usage:
    python scripts/generate_side_income.py --count 2
    python scripts/generate_side_income.py --lang en --count 1
    python scripts/generate_side_income.py --dry-run
"""

import os
import sys
import json
import argparse
import re
import hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from utils.security import safe_print, mask_secrets
from utils.community_miner import CommunityMiner

try:
    from anthropic import Anthropic
except ImportError:
    print("Error: anthropic package not installed. Run: pip install anthropic")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("Error: requests package not installed. Run: pip install requests")
    sys.exit(1)

try:
    import certifi
except ImportError:
    certifi = None

# ── Constants ────────────────────────────────────────────────────────────────

KST = timezone(timedelta(hours=9))
KEYWORDS_FILE = Path(__file__).parent.parent / "data" / "side_income_keywords.json"
USED_FILE = Path(__file__).parent.parent / "data" / "side_income_used.json"
CATEGORY = "side-income"
MODEL = "claude-sonnet-4-6"

NOW = datetime.now(KST)
TODAY = NOW.strftime("%Y-%m-%d")
YEAR = NOW.year

# ── System Prompts ────────────────────────────────────────────────────────────

SYSTEM_PROMPTS = {
    "en": f"""You are a professional writer for Jake's Tech Insights blog.

📅 Today is {TODAY}. Always reference {YEAR}, never older years.

🎯 You write for the **side-income** section: developers who want to earn money beyond their day job.

[AUDIENCE]
- Software developers, 2-10 years experience
- Looking for realistic, actionable income paths
- Skeptical of hype — trust numbers, hate vague promises

[EDITORIAL POLICY]
- Every income claim MUST include a realistic range (e.g., "$500-$2,000/mo")
- Include real platform names, real rate data, real timelines
- No vague promises. "You can make money" → "Upwork senior devs average $75-$120/hr"
- Compare options honestly — acknowledge downsides

[STRUCTURE - 900-1,200 words]
1. Hook (60-80 words): Specific number or surprising data point
2. Key Takeaways block (MANDATORY):
   > **Key Takeaways**
   > - 3-4 concrete, data-backed statements
3. Main content (3-4 ## sections)
4. Conclusion with clear next step (60-80 words)

[WRITING STYLE]
- Write as a senior dev who's actually done this, talking to a peer
- Short punchy sentences mixed with detail. "Short. Explanation here. Short again."
- Contractions required: you're, it's, doesn't, I've, can't
- Tone: direct, honest, slightly skeptical of hype yourself

[AI PHRASE BLACKLIST - NEVER USE]:
- "delve", "tapestry", "pivotal", "multifaceted", "seamless", "synergy"
- "In today's rapidly evolving..." / "In the realm of..."
- "Moreover", "Furthermore" (max 1 across whole article)
- "Here's the thing" / "Let me explain" / "You might be thinking"
- "comprehensive", "robust", "optimize", "utilize", "foster"

[INCOME REALISM RULES]
- Always give a realistic time-to-first-dollar estimate
- Mention the "boring middle" — after the initial setup, what's the actual grind?
- Compare: active income (time-for-money) vs passive (upfront work, delayed return)
- If a method requires capital or rare skills, say so upfront

[HEADLINE PATTERNS - use one]:
- "How Developers Make $X/[period] with [method]: Real Numbers"
- "[Platform A] vs [Platform B] for Developers: What the Data Shows"
- "The $X/mo [method] Side Income for Developers: A Realistic Guide"
- "[method] Income for Developers: Honest Numbers from {YEAR}"

⚠️ Write a complete 900-1,200 word article. Include real numbers.""",

    "ko": f"""당신은 Jake's Tech Insights 블로그의 전문 작가입니다.

📅 오늘은 {TODAY}입니다. 항상 {YEAR}년 기준으로 작성하세요.

🎯 당신은 **side-income(부업)** 섹션 작가입니다: 개발자가 본업 외에 수익을 내는 방법을 소개합니다.

[핵심 역할 — 해외 수익화 방법을 한국 독자에게 소개]
- 미국/해외 개발자들이 실제로 사용하는 부업 방법을 한국 독자에게 소개
- "이런 방법이 있다더라"가 아니라 "실제로 이렇게 작동합니다"
- 한국에서 적용 가능한지, 장벽은 무엇인지 솔직하게 분석
- 현실적인 수치 필수: "월 $500-$2,000 범위", "시작까지 2-3주"

[독자 프로필]
- 경력 2-8년 한국 개발자
- 부업 관심 있지만 해외 플랫폼 낯섦
- 야근 없이 추가 수입 원함
- 숫자와 실사례를 신뢰, 막연한 희망은 불신

[편집 원칙]
- 수입 주장에는 반드시 범위 포함 (예: "월 50만원-200만원")
- 실제 플랫폼명, 실제 단가 데이터, 현실적인 타임라인
- 한국에서의 적용 현실: 가능한 부분 / 어려운 부분 구분
- 해외 성공 사례를 한국 맥락으로 재해석

[구조 — 900-1,200 단어]
1. 훅 (60-80 단어): 구체적인 수치나 의외의 데이터
2. 핵심 요약 블록 (필수):
   > **핵심 요약**
   > - 3-4개의 구체적이고 데이터 기반 문장
3. 본문 (3-4개 ## 섹션)
4. 결론 + 명확한 다음 단계 (60-80 단어)

[토스 스타일 말투 (필수)]
- "~해요", "~인데요", "~거든요" (습니다/합니다 ❌)
- 짧은 문장과 긴 문장 극단적으로 섞기
- "솔직히", "사실", "실제로", "그런데" 같은 자연스러운 접속사
- 구체적 숫자: "월 100만원" "시급 8만원" "3개월 안에"

[AI 표현 금지 목록]:
- "종합적으로", "다양한 측면에서", "혁신적인", "패러다임"
- "중요한 것은", "주목할 만한", "시사하는 바가 크다"
- "이와 같이", "이러한 맥락에서", "요약하자면"
- 습니다/합니다체 혼용

[수익 현실성 규칙]
- 첫 수익 시점 예상 필수 (예: "첫 달은 설정 위주, 2-3개월부터 수익")
- "지루한 중간 과정" 언급 — 처음 설정 후 실제로 어떻게 유지하나
- 능동 수입(시간-돈 교환) vs 패시브(초기 투자, 지연 수익) 비교
- 한국 특수 상황: 세금 처리, 플랫폼 접근성, 언어 장벽

[제목 패턴 — 하나 선택]:
- "해외 개발자들이 [방법]으로 월 $X 버는 법: 한국 적용기"
- "[플랫폼A] vs [플랫폼B] 개발자 단가 비교: {YEAR}년 실제 데이터"
- "개발자 부업 [방법] 현실적인 월수익 분석"
- "[방법]으로 월 XX만원: 해외 성공 사례와 한국 현실"

⚠️ 완성된 900-1,200 단어 글을 작성하세요. 실제 수치를 포함하세요."""
}

# ── Keyword Pool Management ──────────────────────────────────────────────────

def load_keywords() -> Dict:
    """Load keyword pool from data file."""
    with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_used() -> Dict:
    """Load used keyword tracking file."""
    if USED_FILE.exists():
        with open(USED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"en": [], "ko": []}


def save_used(used: Dict):
    """Save used keyword tracking file."""
    with open(USED_FILE, "w", encoding="utf-8") as f:
        json.dump(used, f, ensure_ascii=False, indent=2)


def pick_keywords(lang: str, count: int) -> List[Dict]:
    """Pick next unused keywords for a language. Resets cycle when exhausted."""
    keywords = load_keywords()
    used = load_used()

    pool = keywords.get(lang, [])
    used_ids = set(used.get(lang, []))

    available = [k for k in pool if k["id"] not in used_ids]

    # Reset cycle if exhausted
    if len(available) < count:
        safe_print(f"  ♻️  [{lang}] Keyword pool exhausted, resetting cycle")
        used[lang] = []
        save_used(used)
        available = pool[:]

    selected = available[:count]

    # Mark as used
    used[lang] = used.get(lang, []) + [k["id"] for k in selected]
    save_used(used)

    return selected


# ── Community Context (HN) ────────────────────────────────────────────────────

def get_community_context(keyword: str, api_key: str) -> str:
    """Fetch HackerNews context for freshness signal."""
    try:
        miner = CommunityMiner(anthropic_api_key=api_key)
        if not miner.enabled:
            return ""

        # Search HN for related discussions
        stories = miner.search_hackernews(keyword, max_results=3)
        if not stories:
            return ""

        context_parts = []
        for story in stories[:3]:
            title = story.get("title", "")
            points = story.get("points", 0)
            comments = story.get("num_comments", 0)
            if title:
                context_parts.append(f"- HN: \"{title}\" ({points} pts, {comments} comments)")

        if context_parts:
            return "Recent community discussions:\n" + "\n".join(context_parts)
        return ""

    except Exception as e:
        safe_print(f"  ⚠️  Community context failed: {e}")
        return ""


# ── Image Fetching ────────────────────────────────────────────────────────────

def _unsplash_search(query: str, unsplash_key: str, verify_ssl) -> Optional[Dict]:
    """Search Unsplash and return first photo or None."""
    search_url = "https://api.unsplash.com/search/photos"
    headers = {"Authorization": f"Client-ID {unsplash_key}"}
    params = {"query": query[:50], "per_page": 5, "orientation": "landscape"}
    resp = requests.get(search_url, params=params, headers=headers,
                        timeout=10, verify=verify_ssl)
    resp.raise_for_status()
    results = resp.json().get("results", [])
    return results[0] if results else None


# Fallback queries per subtopic when original keyword returns no results
SUBTOPIC_FALLBACKS = {
    "freelancing":      "freelance work laptop",
    "digital-products": "digital product laptop",
    "ai-income":        "artificial intelligence laptop",
    "saas":             "software startup laptop",
    "content":          "content creator laptop",
    "passive":          "passive income money",
    "security":         "cybersecurity code",
    "jobs":             "remote work laptop",
    "general":          "developer side hustle",
}


def fetch_image(keyword: str, unsplash_key: str, subtopic: str = "") -> tuple[Optional[str], Optional[Dict]]:
    """Fetch image from Unsplash with fallback queries. Never returns None if key is set."""
    if not unsplash_key:
        return None, None

    try:
        verify_ssl = certifi.where() if certifi else True
        headers = {"Authorization": f"Client-ID {unsplash_key}"}

        # Try original keyword, then subtopic fallback, then generic fallback
        fallback = SUBTOPIC_FALLBACKS.get(subtopic, "developer laptop money")
        queries = [keyword, fallback, "developer laptop"]
        photo = None
        for q in queries:
            photo = _unsplash_search(q, unsplash_key, verify_ssl)
            if photo:
                if q != keyword:
                    safe_print(f"  ℹ️  Image fallback used: '{q}'")
                break

        if not photo:
            return None, None

        image_url = photo["urls"]["regular"]
        download_url = photo["links"]["download_location"]
        photographer = photo["user"]["name"]
        photographer_url = photo["user"]["links"]["html"]
        unsplash_url = photo["links"]["html"]

        # Trigger download tracking (Unsplash API ToS)
        requests.get(download_url, headers=headers, timeout=5, verify=verify_ssl)

        # Download image
        slug = re.sub(r'[^a-z0-9\s-]', '', keyword.lower())[:30].strip().replace(' ', '-')
        date_str = NOW.strftime("%Y%m%d")
        filename = f"{date_str}-{slug}.webp"
        filepath = Path("static/images") / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        optimized_url = f"{image_url}?w=1200&q=85&fm=webp"
        img_resp = requests.get(optimized_url, timeout=15, verify=verify_ssl)
        img_resp.raise_for_status()

        # Duplicate detection
        content_hash = hashlib.md5(img_resp.content).hexdigest()
        for existing in filepath.parent.glob("*.webp"):
            try:
                if hashlib.md5(existing.read_bytes()).hexdigest() == content_hash:
                    safe_print(f"  ⚠️  Duplicate image, using new filename anyway")
                    break
            except Exception:
                pass

        filepath.write_bytes(img_resp.content)
        safe_print(f"  ✓ Image: {filepath} ({len(img_resp.content) / 1024:.1f} KB)")

        return f"/images/{filename}", {
            "photographer": photographer,
            "photographer_url": photographer_url,
            "unsplash_url": unsplash_url
        }

    except Exception as e:
        safe_print(f"  ⚠️  Image fetch failed: {e}")
        return None, None


# ── Content Generation ────────────────────────────────────────────────────────

def generate_tags(keyword: str, subtopic: str) -> List[str]:
    """Generate SEO tags for a side-income post."""
    tags = [f"subtopic-{subtopic}"]

    stop = {"a","an","the","in","on","at","to","for","of","and","or","is","are",
            "how","what","why","when","with","vs","as","from","by"}
    words = [w for w in keyword.split() if w.lower() not in stop and len(w) > 2]

    # Add meaningful words as tags
    for w in words[:3]:
        t = w.lower().strip(".,!?")
        if t and t not in [x.lower() for x in tags]:
            tags.append(t)

    return tags[:5]


def generate_post(kw: Dict, lang: str, client: Anthropic,
                  community_context: str) -> tuple[str, str, str]:
    """Generate title, description, and body for a side-income post."""
    keyword = kw["keyword"]
    subtopic = kw["subtopic"]

    context_block = f"\n\n[Recent community context for freshness]\n{community_context}" if community_context else ""

    prompt = f"""Write a complete side-income article for the keyword: "{keyword}"
Subtopic: {subtopic}{context_block}

Requirements:
- 900-1,200 words
- Start with a specific income number or surprising stat
- Include realistic income ranges throughout
- Mention actual platform names, rates, timelines
- End with a concrete next step

Write the full article body in Markdown (##, ###, bullet points).
Do NOT include a title line (no # heading at top) — just the body."""

    safe_print(f"  📝 Generating [{lang}] article: {keyword[:50]}...")

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPTS[lang],
        messages=[{"role": "user", "content": prompt}]
    )

    body = response.content[0].text.strip()

    # Generate title
    title_prompt = f"""Write a title for this {lang} article about: "{keyword}"

Follow this style guide exactly:
{"Use one of these patterns: 'How Developers Make $X/period with [method]: Real Numbers', '[method] Income for Developers: Honest Numbers from " + str(YEAR) + "'" if lang == "en" else "패턴: '해외 개발자들이 [방법]으로 월 $X 버는 법', '개발자 부업 [방법] 현실 분석 " + str(YEAR) + "'"}

Return ONLY the title, no quotes, no explanation."""

    title_response = client.messages.create(
        model=MODEL,
        max_tokens=100,
        system=SYSTEM_PROMPTS[lang],
        messages=[{"role": "user", "content": title_prompt}]
    )
    title = title_response.content[0].text.strip().strip('"').strip("'")

    # Generate description
    body_preview = body[:600]
    desc_prompt = f"""Write a meta description (120-155 characters) for this article.

Title: {title}
Article preview: {body_preview}

Rules:
- Include a specific income number if present
- No generic phrases like "Learn how to" or "In this article"
- Must be a complete sentence
- {"English" if lang == "en" else "Korean (한국어)"}

Return ONLY the description text."""

    desc_response = client.messages.create(
        model=MODEL,
        max_tokens=200,
        system=SYSTEM_PROMPTS[lang],
        messages=[{"role": "user", "content": desc_prompt}]
    )
    description = desc_response.content[0].text.strip().strip('"').strip("'")

    return title, description, body


# ── Save Post ─────────────────────────────────────────────────────────────────

def save_post(kw: Dict, lang: str, title: str, description: str, body: str,
              image_path: Optional[str], image_credit: Optional[Dict]) -> Path:
    """Save generated post to Hugo content directory."""
    keyword = kw["keyword"]
    subtopic = kw["subtopic"]

    # Generate slug
    slug = keyword.lower()
    slug = ''.join(c if c.isalnum() or c.isspace() or ord(c) > 127 else '' for c in slug)
    slug = slug.replace(' ', '-')[:50].strip('-')

    # Directory
    content_dir = Path(f"content/{lang}/{CATEGORY}")
    content_dir.mkdir(parents=True, exist_ok=True)

    date_str = NOW.strftime("%Y-%m-%d")
    filename = f"{date_str}-{slug}.md"
    filepath = content_dir / filename

    # Image fallback
    if not image_path:
        image_path = f"/images/placeholder-{CATEGORY}.jpg"

    # Escape YAML values
    safe_title = title.replace('"', "'")
    safe_desc = description.replace('"', "'")

    tags = generate_tags(keyword, subtopic)

    frontmatter_lines = [
        "---",
        f'title: "{safe_title}"',
        f'date: {NOW.strftime("%Y-%m-%dT%H:%M:%S%z")}',
        "draft: false",
        'author: "Jake Park"',
        f'categories: ["{CATEGORY}"]',
        f'tags: {json.dumps(tags, ensure_ascii=False)}',
        f'description: "{safe_desc}"',
        f'image: "{image_path}"',
        "---",
        ""
    ]

    frontmatter = "\n".join(frontmatter_lines) + "\n"

    credit_line = ""
    if image_credit:
        credit_line = (
            f"\n\n---\n\n"
            f"*Photo by [{image_credit['photographer']}]({image_credit['photographer_url']}) "
            f"on [Unsplash]({image_credit['unsplash_url']})*\n"
        )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(frontmatter)
        f.write(body)
        f.write(credit_line)

    safe_print(f"  ✓ Saved: {filepath}")
    return filepath


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate side-income blog posts")
    parser.add_argument("--count", type=int, default=2,
                        help="Posts per language (default: 2)")
    parser.add_argument("--lang", choices=["en", "ko", "both"], default="both",
                        help="Language to generate (default: both)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show selected keywords without generating content")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    unsplash_key = os.environ.get("UNSPLASH_ACCESS_KEY")

    if not api_key:
        safe_print("❌ ANTHROPIC_API_KEY not set")
        sys.exit(1)

    client = Anthropic(api_key=api_key)

    langs = ["en", "ko"] if args.lang == "both" else [args.lang]

    safe_print(f"\n🚀 Side-Income Content Generator")
    safe_print(f"   Date: {TODAY} (KST)")
    safe_print(f"   Langs: {', '.join(langs)} | Count: {args.count} each")
    safe_print(f"   Unsplash: {'✓' if unsplash_key else '✗ (no images)'}")
    safe_print("")

    total_generated = 0

    for lang in langs:
        safe_print(f"── [{lang.upper()}] Picking {args.count} keywords ──")
        keywords = pick_keywords(lang, args.count)

        for kw in keywords:
            safe_print(f"\n  Keyword #{kw['id']}: {kw['keyword']}")
            safe_print(f"  Subtopic: {kw['subtopic']}")

            if args.dry_run:
                safe_print("  [dry-run] skipping generation")
                continue

            # Fetch community context
            safe_print("  🔍 Fetching HN context...")
            context = get_community_context(kw["keyword"], api_key)

            # Fetch image
            safe_print("  🖼️  Fetching image...")
            image_path, image_credit = fetch_image(kw["keyword"], unsplash_key, kw["subtopic"])

            # Generate content
            try:
                title, description, body = generate_post(kw, lang, client, context)
            except Exception as e:
                safe_print(f"  ❌ Generation failed: {e}")
                continue

            # Save
            filepath = save_post(kw, lang, title, description, body,
                                 image_path, image_credit)

            safe_print(f"  ✅ Done: {filepath.name}")
            total_generated += 1

        safe_print("")

    safe_print(f"✅ Generated {total_generated} posts total")
    if args.dry_run:
        safe_print("  (dry-run mode — no files written)")


if __name__ == "__main__":
    main()
