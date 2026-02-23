#!/usr/bin/env python3
"""
Keyword Curator - Semi-automated keyword research for blog content

Generates keyword candidates using Claude API based on KEYWORD_STRATEGY.md
Provides interactive selection interface for human filtering (5 minutes weekly)

Usage:
    python scripts/keyword_curator.py
    python scripts/keyword_curator.py --count 15
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import requests

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

try:
    import certifi
except ImportError:
    safe_print("Warning: certifi not installed - SSL verification may fail")
    certifi = None

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))
from utils.security import safe_print, mask_secrets

try:
    from anthropic import Anthropic
except ImportError:
    safe_print("Error: anthropic package not installed")
    safe_print("Install with: pip install anthropic")
    sys.exit(1)


CURATION_PROMPT_WITH_TRENDS = """역할:
너는 광고 수익 최적화를 위한 기술 전문 키워드 큐레이터다.
아래 커뮤니티 토픽(HackerNews, Dev.to, Lobsters, ProductHunt)을 바탕으로 **고CPC, 감정 반응형** 키워드를 제안하라.

📊 **소스**: Community 100% (HackerNews, Dev.to, Lobsters, ProductHunt)
📊 **언어 비중**: EN 50% ({en_count}개), KO 50% ({ko_count}개)

🌐 **Community Topics (HackerNews, Dev.to, Lobsters, ProductHunt)**:
{community_topics}

---

**🌏 EN → KO 번역 전략 (KO 키워드 생성 핵심 규칙):**
커뮤니티 토픽은 대부분 영어지만, KO 키워드는 그 영어 핫 토픽을 **한국어 독자 관점**으로 재해석해서 만들어라.
- EN 커뮤니티 토픽 → 한국 독자에게 의미 있는 KO 키워드로 변환
- 단순 번역이 아닌, 한국 개발자/테크 사용자가 실제 검색할 만한 표현으로 적절히 변환
- 예시:
  - "OpenAI releases GPT-5" → KO: "GPT-5 출시 한국 개발자 영향"
  - "Apple Silicon M4 benchmark" → KO: "애플 M4 성능 실제 체감"
  - "GitHub Copilot now free" → KO: "깃허브 코파일럿 무료 전환 어떻게"
  - "Linux kernel 7.0 released" → KO: "리눅스 커널 7.0 업데이트 변경사항"

**🚨 언어 문자 검증 규칙 (반드시 준수):**
- **영어(en) 키워드**: 한글(가-힣) 포함 금지
  - 올바른 예: "OpenAI GPT-5 developer impact", "GitHub Copilot free tier"
  - 잘못된 예: "붉은사막" (한글 포함)
- **한국어(ko) 키워드**: 반드시 한글(가-힣) 포함 필요
  - 올바른 예: "GPT-5 출시 영향", "애플 M4 성능" (영문 약어 혼용 허용)
  - 잘못된 예: "GPT-5 release" (한글 없음)

**목표:**
한국어 / 영어 각각에서
**불안, 분노, 궁금증**을 유발하는 테크 키워드만 제안하라.

**금지:**
- 추상적인 요약 ("AI 트렌드", "새로운 기술")
- 긍정적이고 평화로운 키워드 (자극 없는 단순 정보)
- **같은 키워드를 다른 언어로 중복 제안하는 것** (EN/KO 각각 독립적 키워드)
- **테크와 무관한 키워드**:
  - ❌ 제외: 스포츠, 연예인, 드라마, 영화, 아이돌, 음악
  - ❌ 제외: 날씨/자연재해 (태풍, 한파, 폭설)
  - ❌ 제외: 사람 이름 단독 (연예인 실명, 정치인 이름)
  - ❌ 제외: 결혼/이혼/출산/사건사고
  - ❌ 제외: "스포츠 테크", "날씨 앱" 같은 억지 기술 연결 — 핵심이 기술이 아니면 제외
  - ✅ 포함: AI, 클라우드, 프로그래밍, 소프트웨어, 앱, 게임, 사이버보안, 반도체, 스타트업 기술, EdTech, DevOps, 오픈소스

출력 형식:
반드시 JSON 형식으로만 응답하라.

[
  {{
    "keyword": "커뮤니티 토픽 기반 키워드 (EN: 영어 원문 스타일, KO: 한국 독자 관점 표현)",
    "raw_search_title": "사용자가 구글에 검색할 때 정확히 입력하는 검색어",
    "editorial_title": "기사 제목 형식의 독자 친화적 제목",
    "core_fear_question": "사용자의 핵심 두려움을 담은 질문 한 문장",
    "language": "ko",
    "category": "tech",
    "source_topic": "참고한 커뮤니티 토픽 원문 제목 (HackerNews/Dev.to/Lobsters/ProductHunt)",
    "search_intent": "사용자가 지금 당장 검색하는 이유",
    "angle": "이 키워드를 다룰 때의 관점",
    "competition_level": "low",
    "why_it_works": "이 키워드가 효과적인 이유 (트래픽/공감 근거)",
    "purpose": "high competition인 경우에만: Traffic acquisition / Brand positioning / Viral content 중 하나",
    "keyword_type": "trend",
    "priority": 7,
    "risk_level": "safe",
    "name_policy": "no_real_names",
    "intent_signal": "STATE_CHANGE"
  }}
]

중요:
- keyword_type은 "trend"만 사용 (이 프롬프트는 트렌드 전용)
- category는 **"tech" 하나만** 사용 (테크 전문 퍼블리케이션 전략)
- language는 "en", "ko" 중 하나
- competition_level은 "low", "medium", "high" 중 하나
- priority는 1-10 사이의 숫자
- risk_level은 "safe", "caution", "high_risk" 중 하나 (기본값: "safe")
- name_policy는 "no_real_names" (기본값)
- intent_signal은 "STATE_CHANGE", "PROMISE_BROKEN", "SILENCE", "DEADLINE_LOST", "COMPARISON" 중 하나
- source_topic 필드: 참고한 커뮤니티 토픽 원문을 반드시 기재 (추적용)

**언어별 톤 차이:**
- 🇺🇸 English: developer impact, performance, workflow disruption 중심
- 🇰🇷 Korean: 한국 개발자/사용자 관점, 실제 체감, 국내 영향 중심

**🔴 안전 가이드라인:**
- 명예훼손/비난/비방 표현 금지
- 실명은 공적 인물(CEO, 창업자) + 기술 맥락에서만 허용

**중복 방지 규칙:**
- Intent signals: STATE_CHANGE, PROMISE_BROKEN, SILENCE, DEADLINE_LOST, COMPARISON
- 같은 signal을 가진 키워드는 언어당 최대 2개까지만

**🚨 언어별 키워드 생성 규칙 (절대 준수):**
반드시 정확히 {count}개의 키워드를 생성하라:
- 영어(en): 정확히 {en_count}개 — 커뮤니티 토픽을 영어 키워드로 직접 활용
- 한국어(ko): 정확히 {ko_count}개 — 커뮤니티 토픽을 한국 독자 관점으로 재해석
- 총합: 정확히 {count}개

모든 키워드의 category는 반드시 "tech"로 설정할 것."""


CURATION_PROMPT_EVERGREEN = """역할:
너는 **장기 트래픽** 확보를 위한 Evergreen 키워드 큐레이터다.
아래 Evergreen 키워드 풀에서 **검색량이 지속되는, 교육/가이드성** 키워드를 제안하라.

Evergreen 키워드 풀 (언어별로 구분됨):

🇺🇸 English Keywords:
{evergreen_en}

🇰🇷 Korean Keywords:
{evergreen_ko}

**🚫 이미 큐에 존재하는 키워드 (절대 중복 제안 금지):**
{existing_keywords}

**목표:**
- **지속적 검색 수요**: 1년 후에도 검색되는 주제
- **교육/가이드성**: "how to", "guide", "방법", "가이드" 등
- **낮은 경쟁**: low~medium competition 위주
- **실용적 가치**: 독자에게 실질적 도움이 되는 내용

**금지:**
- 시사성 토픽 (속보, 사건 사고)
- 실명 인물 관련 (연예인, 정치인)
- 논란/감정 자극형 키워드
- 추상적 주제 ("AI의 미래", "기술 트렌드")
- **위 "이미 큐에 존재하는 키워드" 목록과 동일하거나 유사한 키워드**

출력 형식:
반드시 JSON 형식으로만 응답하라.

[
  {{
    "keyword": "위 Evergreen 키워드 풀에서 선택한 키워드 (또는 유사 변형)",
    "raw_search_title": "사용자가 구글에 검색할 때 정확히 입력하는 검색어",
    "editorial_title": "기사 제목 형식의 독자 친화적 제목",
    "core_question": "사용자가 해결하고 싶은 핵심 질문 (교육적)",
    "language": "ko",
    "category": "tech",
    "search_intent": "사용자가 이 키워드를 검색하는 실질적 이유 (학습, 문제 해결, 의사 결정 등)",
    "angle": "이 키워드를 다룰 때의 관점 (교육, 비교, 가이드 등)",
    "competition_level": "low",
    "why_evergreen": "이 키워드가 장기간 검색될 이유 (지속적 수요 근거)",
    "keyword_type": "evergreen",
    "priority": 6,
    "risk_level": "safe",
    "name_policy": "no_real_names",
    "content_depth": "comprehensive"
  }}
]

중요:
- keyword_type은 "evergreen"만 사용 (이 프롬프트는 에버그린 전용)
- category는 **"tech" 하나만** 사용 (테크 전문 퍼블리케이션 전략)
- language는 "en", "ko" 중 하나 (비율: EN 50%, KO 50%)
- competition_level은 "low", "medium"만 사용 (high 금지)
- priority는 6-9 사이 (Evergreen은 장기 가치가 높으므로 우선순위 상향)
- risk_level은 무조건 "safe"
- content_depth는 "comprehensive"

**🚨 언어별 키워드 생성 규칙:**
반드시 정확히 {count}개의 키워드를 생성하라:
- 영어(en): 정확히 {en_count}개
- 한국어(ko): 정확히 {ko_count}개
- 총합: 정확히 {count}개

모든 키워드의 category는 반드시 "tech"로 설정할 것.
"""


class KeywordCurator:
    def __init__(self, api_key: str = None, google_api_key: str = None, google_cx: str = None):
        """Initialize keyword curator with Claude API and Google Custom Search"""
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            safe_print("❌ ERROR: ANTHROPIC_API_KEY not found")
            safe_print("   Please set it as environment variable")
            safe_print("   Example: export ANTHROPIC_API_KEY='your-key-here'")
            raise ValueError("ANTHROPIC_API_KEY not found")

        # Brave Search API (replacing Google Custom Search)
        self.brave_api_key = os.environ.get("BRAVE_API_KEY")

        # Keep Google API keys for backward compatibility (deprecated)
        self.google_api_key = google_api_key or os.environ.get("GOOGLE_API_KEY")
        self.google_cx = google_cx or os.environ.get("GOOGLE_CX")

        if not self.brave_api_key:
            safe_print("⚠️  Brave Search API key not found")
            safe_print("   Set BRAVE_API_KEY environment variable")
            safe_print("   Falling back to Claude-only mode")
            if self.google_api_key and self.google_cx:
                safe_print("   Note: Google Custom Search API is deprecated for new users")

        try:
            self.client = Anthropic(api_key=self.api_key)
            self.model = "claude-sonnet-4-6"
            safe_print("  ✓ Anthropic API client initialized successfully")
        except Exception as e:
            safe_print(f"❌ ERROR: Failed to initialize Anthropic client")
            safe_print(f"   Error: {mask_secrets(str(e))}")
            raise

        # Load existing queue
        self.queue_path = Path("data/topics_queue.json")
        try:
            self.queue_data = self._load_queue()
            safe_print(f"  ✓ Loaded topic queue: {len(self.queue_data.get('topics', []))} topics")
        except Exception as e:
            safe_print(f"⚠️  WARNING: Failed to load existing queue, starting fresh")
            safe_print(f"   Error: {str(e)}")
            self.queue_data = {"topics": []}

    def _load_queue(self) -> Dict:
        """Load existing topic queue"""
        if not self.queue_path.exists():
            return {"topics": []}

        with open(self.queue_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_queue(self):
        """Save updated topic queue"""
        try:
            # Ensure parent directory exists
            self.queue_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.queue_path, 'w', encoding='utf-8') as f:
                json.dump(self.queue_data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            safe_print(f"❌ ERROR: Failed to save queue to filesystem")
            safe_print(f"   Path: {self.queue_path}")
            safe_print(f"   Error: {str(e)}")
            raise
        except Exception as e:
            safe_print(f"❌ ERROR: Unexpected error saving queue")
            safe_print(f"   Error: {str(e)}")
            raise

    def detect_intent_signals(self, query: str) -> list:
        """Detect intent signals from query for deduplication"""
        signals = []

        # State transition patterns
        if any(word in query.lower() for word in ["after", "갑자기", "suddenly", "overnight"]):
            signals.append("STATE_CHANGE")

        # Promise broken patterns
        if any(word in query.lower() for word in ["promised", "supposed to", "약속", "denied", "거부"]):
            signals.append("PROMISE_BROKEN")

        # Silence patterns
        if any(word in query.lower() for word in ["no response", "ignored", "무응답", "침묵"]):
            signals.append("SILENCE")

        # Deadline/time loss patterns
        if any(word in query.lower() for word in ["deadline", "too late", "마감", "놓침"]):
            signals.append("DEADLINE_LOST")

        # Comparison/injustice patterns
        if any(word in query.lower() for word in ["others got", "only me", "나만"]):
            signals.append("COMPARISON")

        return signals if signals else ["GENERAL"]

    def fetch_community_topics(self) -> Dict[str, List[Dict]]:
        """Fetch trending topics from HackerNews, Reddit, and ProductHunt"""
        safe_print(f"\n{'='*60}")
        safe_print(f"  🌐 Fetching topics from community sources...")
        safe_print(f"{'='*60}\n")

        community_topics = []
        verify_ssl = certifi.where() if certifi else True

        # 1. HackerNews - Top Stories + Top Comments (free, no auth)
        try:
            safe_print("  → Fetching from HackerNews (with top comments)...")
            hn_top_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            response = requests.get(hn_top_url, timeout=10, verify=verify_ssl)
            response.raise_for_status()
            story_ids = response.json()[:10]  # Top 10 stories

            for story_id in story_ids[:5]:  # Fetch details for top 5
                try:
                    item_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                    item_resp = requests.get(item_url, timeout=5, verify=verify_ssl)
                    item_resp.raise_for_status()
                    item = item_resp.json()

                    if item and item.get('title'):
                        # Fetch top 3 comments for additional context
                        top_comments = []
                        comment_ids = item.get('kids', [])[:3]  # Top 3 comment IDs
                        for comment_id in comment_ids:
                            try:
                                comment_url = f"https://hacker-news.firebaseio.com/v0/item/{comment_id}.json"
                                comment_resp = requests.get(comment_url, timeout=3, verify=verify_ssl)
                                comment_resp.raise_for_status()
                                comment = comment_resp.json()
                                if comment and comment.get('text'):
                                    # Strip HTML tags and limit length
                                    import re
                                    clean_text = re.sub('<[^<]+?>', '', comment.get('text', ''))
                                    if len(clean_text) > 500:
                                        clean_text = clean_text[:500] + '...'
                                    top_comments.append(clean_text)
                            except Exception:
                                continue

                        community_topics.append({
                            'title': item['title'],
                            'source': 'HackerNews',
                            'url': item.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                            'score': item.get('score', 0),
                            'comments': item.get('descendants', 0),
                            'top_comments': top_comments  # NEW: Developer insights
                        })
                except Exception:
                    continue

            hn_count = len([t for t in community_topics if t['source'] == 'HackerNews'])
            safe_print(f"    ✓ Found {hn_count} topics from HackerNews (with comments)")

        except Exception as e:
            safe_print(f"    ⚠️ HackerNews fetch failed: {mask_secrets(str(e))}")

        # 2. Dev.to - Developer community (free, no auth needed)
        try:
            safe_print("  → Fetching from Dev.to (top articles)...")
            devto_url = "https://dev.to/api/articles?top=1&per_page=5"
            headers = {'User-Agent': 'JakesTechInsights/1.0'}
            response = requests.get(devto_url, headers=headers, timeout=10, verify=verify_ssl)
            response.raise_for_status()
            data = response.json()

            for article in data[:5]:
                if article.get('title'):
                    community_topics.append({
                        'title': article['title'],
                        'source': 'Dev.to',
                        'url': article.get('url', ''),
                        'score': article.get('positive_reactions_count', 0),
                        'comments': article.get('comments_count', 0)
                    })

            devto_count = len([t for t in community_topics if t['source'] == 'Dev.to'])
            safe_print(f"    ✓ Found {devto_count} topics from Dev.to")

        except Exception as e:
            safe_print(f"    ⚠️ Dev.to fetch failed: {mask_secrets(str(e))}")

        # 3a. Lobsters - Tech community (free, no auth needed)
        try:
            safe_print("  → Fetching from Lobsters (hottest)...")
            lobsters_url = "https://lobste.rs/hottest.json"
            response = requests.get(lobsters_url, headers={'User-Agent': 'JakesTechInsights/1.0'}, timeout=10, verify=verify_ssl)
            response.raise_for_status()
            data = response.json()

            for article in data[:5]:
                if article.get('title'):
                    community_topics.append({
                        'title': article['title'],
                        'source': 'Lobsters',
                        'url': article.get('url') or article.get('short_id_url', ''),
                        'score': article.get('score', 0),
                        'comments': article.get('comment_count', 0)
                    })

            lobsters_count = len([t for t in community_topics if t['source'] == 'Lobsters'])
            safe_print(f"    ✓ Found {lobsters_count} topics from Lobsters")

        except Exception as e:
            safe_print(f"    ⚠️ Lobsters fetch failed: {mask_secrets(str(e))}")

        # 3. ProductHunt - Using Atom feed with descriptions (no auth needed)
        try:
            safe_print("  → Fetching from ProductHunt (with descriptions)...")
            import xml.etree.ElementTree as ET
            ph_feed_url = "https://www.producthunt.com/feed"
            response = requests.get(ph_feed_url, timeout=10, verify=verify_ssl)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            # ProductHunt uses Atom format, not RSS - need to use namespace
            atom_ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entries = root.findall('atom:entry', atom_ns)

            for entry in entries[:5]:
                title_elem = entry.find('atom:title', atom_ns)
                link_elem = entry.find('atom:link', atom_ns)
                content_elem = entry.find('atom:content', atom_ns)  # Atom uses 'content' not 'description'

                if title_elem is not None and title_elem.text:
                    # Extract URL from link element's href attribute
                    url = ''
                    if link_elem is not None:
                        url = link_elem.get('href', '')

                    # Extract and clean description from content
                    description = ''
                    if content_elem is not None and content_elem.text:
                        import re
                        description = re.sub('<[^<]+?>', '', content_elem.text)  # Strip HTML
                        description = ' '.join(description.split())  # Normalize whitespace
                        if len(description) > 500:
                            description = description[:500] + '...'

                    community_topics.append({
                        'title': title_elem.text.strip(),
                        'source': 'ProductHunt',
                        'url': url,
                        'score': 0,
                        'comments': 0,
                        'description': description  # Product details
                    })

            ph_count = len([t for t in community_topics if t['source'] == 'ProductHunt'])
            safe_print(f"    ✓ Found {ph_count} topics from ProductHunt (with descriptions)")

        except Exception as e:
            safe_print(f"    ⚠️ ProductHunt fetch failed: {mask_secrets(str(e))}")

        safe_print(f"\n  🎉 Total {len(community_topics)} community topics fetched!\n")

        return {'en': community_topics}  # All community sources are English

    def fetch_trending_from_rss(self) -> Dict[str, List[str]]:
        """Fetch trending topics from Google Trends RSS feeds grouped by language"""
        import xml.etree.ElementTree as ET

        rss_urls = {
            "KR": "https://trends.google.co.kr/trending/rss?geo=KR",
            "US": "https://trends.google.co.kr/trending/rss?geo=US"
        }

        # Map region to language
        region_to_lang = {
            "KR": "ko",
            "US": "en"
        }

        # Group trends by language
        trends_by_lang = {"ko": [], "en": []}

        for geo, url in rss_urls.items():
            try:
                verify_ssl = certifi.where() if certifi else True
                response = requests.get(url, timeout=10, verify=verify_ssl)
                response.raise_for_status()

                # Parse XML
                root = ET.fromstring(response.content)

                # Find all items (trending topics)
                items = root.findall('.//item')

                lang = region_to_lang[geo]
                for item in items[:5]:  # Top 5 per region (15 total)
                    title_elem = item.find('title')
                    if title_elem is not None and title_elem.text:
                        trends_by_lang[lang].append(title_elem.text.strip())

                safe_print(f"  ✓ Found {min(len(items), 5)} trends from {geo} → {lang}")

            except requests.exceptions.Timeout:
                safe_print(f"  ⚠️  RSS fetch timeout for {geo}: Request took too long")
                continue
            except requests.exceptions.HTTPError as e:
                safe_print(f"  ⚠️  RSS HTTP error for {geo}: {e.response.status_code if e.response else 'unknown'}")
                continue
            except ET.ParseError as e:
                safe_print(f"  ⚠️  RSS parse error for {geo}: Invalid XML format")
                safe_print(f"     Error: {str(e)}")
                continue
            except Exception as e:
                safe_print(f"  ⚠️  RSS fetch error for {geo}: {mask_secrets(str(e))}")
                continue

        return trends_by_lang

    def fetch_trending_topics(self) -> Dict[str, str]:
        """Fetch trending topics using Google Trends RSS feeds, grouped by language"""
        safe_print(f"\n{'='*60}")
        safe_print(f"  🔥 Fetching REAL-TIME trending topics from Google Trends RSS...")
        safe_print(f"{'='*60}\n")

        # Try RSS feeds first (most reliable method)
        trends_by_lang = self.fetch_trending_from_rss()

        # Check if we got any trends
        total_trends = sum(len(trends) for trends in trends_by_lang.values())

        if total_trends > 0:
            safe_print(f"\n  🎉 Total {total_trends} real-time trending topics from RSS!")
            safe_print(f"     EN: {len(trends_by_lang['en'])}, KO: {len(trends_by_lang['ko'])}\n")
        else:
            safe_print("  ⚠️  RSS feeds failed. Falling back to pattern-based queries...\n")
            # Fallback to pattern queries (grouped by language)
            trends_by_lang = {
                "en": [
                    "account banned after update no response",
                    "service outage promised compensation denied",
                    "class action deadline passed too late",
                    "refund promised but denied suddenly",
                    "government support supposed to but denied",
                    "new policy suddenly stricter than announced",
                    "celebrity apology issued but backlash continues"
                ],
                "ko": [
                    "앱 업데이트 후 갑자기 먹통",
                    "집단소송 신청 마감 놓침",
                    "정부지원 조건 발표와 다름",
                    "사과문 냈지만 논란 계속",
                    "리콜 발표했는데 환불 거부"
                ]
            }

        # Flatten for search queries (but keep language tracking)
        all_queries = []
        for lang, queries in trends_by_lang.items():
            for query in queries:
                all_queries.append((query, lang))

        # If no Brave Search API, skip search results
        if not self.brave_api_key:
            safe_print("  🚨 CRITICAL WARNING: Brave Search API not configured")
            safe_print("  📌 References will NOT be generated for keywords!")
            safe_print("  📌 Set BRAVE_API_KEY environment variable")
            safe_print("  📌 OR: Add it as GitHub Secret for automated workflows\n")
            self.search_results = []

            # Format trends by language for prompt
            trends_formatted = {}
            for lang, queries in trends_by_lang.items():
                trends_formatted[lang] = "\n".join([f"Query: {q}" for q in queries[:10]])

            return trends_formatted

        all_results = []
        for query, query_lang in all_queries:
            try:
                # Brave Search API endpoint
                url = "https://api.search.brave.com/res/v1/web/search"
                headers = {
                    "Accept": "application/json",
                    "X-Subscription-Token": self.brave_api_key
                }
                params = {
                    "q": query,
                    "count": 3,  # Get top 3 results per query for better quality
                    "freshness": "pw"  # Past week (최신 뉴스)
                }

                # Add delay to avoid rate limiting
                time.sleep(0.5)

                verify_ssl = certifi.where() if certifi else True
                response = requests.get(url, headers=headers, params=params, verify=verify_ssl)
                response.raise_for_status()

                data = response.json()

                # Brave API returns results in "web" -> "results" structure
                web_results = data.get("web", {}).get("results", [])

                if web_results:
                    # Detect intent signals for this query
                    signals = self.detect_intent_signals(query)

                    for item in web_results:
                        all_results.append({
                            "query": query,
                            "query_lang": query_lang,  # Track which language this query belongs to
                            "signals": signals,  # Add intent signals
                            "title": item.get("title", ""),
                            "snippet": item.get("description", ""),  # Brave uses "description" not "snippet"
                            "link": item.get("url", ""),  # Brave uses "url" not "link"
                            "source": item.get("url", "").split("/")[2] if item.get("url") else ""  # Extract domain
                        })

                safe_print(f"  ✓ Fetched {len(web_results)} results for: {query}")

            except requests.exceptions.Timeout:
                safe_print(f"  ⚠️  Timeout fetching results for '{query[:50]}...'")
                continue
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else 'unknown'
                safe_print(f"  ⚠️  HTTP error ({status_code}) for '{query[:50]}...'")
                if status_code == 403:
                    safe_print(f"     ⚠️  Brave API Access Forbidden - check API key")
                elif status_code == 429:
                    safe_print(f"     Rate limit exceeded (2000/month limit)")
                continue
            except json.JSONDecodeError:
                safe_print(f"  ⚠️  Invalid JSON response for '{query[:50]}...'")
                continue
            except requests.exceptions.RequestException as e:
                safe_print(f"  ⚠️  Network error for '{query[:50]}...': {mask_secrets(str(e))}")
                continue
            except Exception as e:
                safe_print(f"  ⚠️  Unexpected error for '{query[:50]}...': {mask_secrets(str(e))}")
                continue

        safe_print(f"\n✅ Total {len(all_results)} trending topics fetched\n")

        # Store results for reference extraction
        self.search_results = all_results

        # Format results for Claude, grouped by language
        trends_by_lang_formatted = {"en": [], "ko": []}
        for r in all_results:
            lang = r.get('query_lang', 'en')
            if lang in trends_by_lang_formatted:
                trends_by_lang_formatted[lang].append(
                    f"Query: {r['query']}\nTitle: {r['title']}\nSnippet: {r['snippet']}\n"
                )

        # Convert to string format per language
        trends_formatted = {}
        for lang in ["en", "ko"]:
            trends_formatted[lang] = "\n\n".join(trends_by_lang_formatted[lang][:10])  # Top 10 per language

        return trends_formatted

    def filter_by_risk(self, candidates: List[Dict]) -> List[Dict]:
        """Filter out high-risk keywords automatically"""
        safe_candidates = []
        filtered_count = 0

        for kw in candidates:
            # Auto-reject high-risk
            if kw.get("risk_level") == "high_risk":
                filtered_count += 1
                safe_print(f"  🔴 Filtered high-risk: {kw.get('keyword', 'unknown')}")
                continue

            # Flag caution items for manual review
            if kw.get("risk_level") == "caution":
                kw["needs_review"] = True
                safe_print(f"  🟡 Caution flagged: {kw.get('keyword', 'unknown')}")

            safe_candidates.append(kw)

        if filtered_count > 0:
            safe_print(f"\n⚠️  {filtered_count} high-risk keywords filtered out\n")

        return safe_candidates

    def fetch_evergreen_references(self, keyword: str, lang: str, freshness: str = "py") -> List[Dict]:
        """Fetch references for a keyword via Brave Search.
        freshness: 'pw' = past week (trend), 'py' = past year (evergreen)
        """
        if not self.brave_api_key:
            safe_print(f"  ⚠️  No Brave API key - skipping references for: {keyword}")
            return []

        try:
            url = "https://api.search.brave.com/res/v1/web/search"
            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": self.brave_api_key
            }
            params = {
                "q": keyword,
                "count": 3,
                "freshness": freshness
            }

            time.sleep(0.5)  # Rate limiting

            verify_ssl = certifi.where() if certifi else True
            response = requests.get(url, headers=headers, params=params, verify=verify_ssl)
            response.raise_for_status()

            data = response.json()
            web_results = data.get("web", {}).get("results", [])

            references = []
            seen_domains = set()

            for item in web_results:
                link = item.get("url", "")
                title = item.get("title", "")
                source = link.split("/")[2] if link else ""

                if link and source and source not in seen_domains:
                    references.append({
                        "title": title[:100],
                        "url": link,
                        "source": source
                    })
                    seen_domains.add(source)

                if len(references) >= 3:
                    break

            return references

        except Exception as e:
            safe_print(f"  ⚠️  Failed to fetch references for '{keyword}': {mask_secrets(str(e))}")
            return []

    def extract_references(self, all_results: List[Dict], keyword: str, lang: str) -> List[Dict]:
        """Extract top 3 references for a keyword based on search results"""
        # Find relevant results for this keyword
        # Match by language and keyword similarity
        relevant = []

        for result in all_results:
            query = result.get("query", "").lower()
            # Simple matching: if keyword words appear in query
            keyword_words = set(keyword.lower().split())
            query_words = set(query.split())

            # Check language match (simple heuristic)
            is_relevant = len(keyword_words & query_words) > 0

            if is_relevant:
                relevant.append(result)

        # Take top 3 unique sources
        references = []
        seen_domains = set()

        for result in relevant[:10]:  # Check first 10 relevant results
            link = result.get("link", "")
            source = result.get("source", "")
            title = result.get("title", "")

            if link and source and source not in seen_domains:
                references.append({
                    "title": title[:100],  # Truncate long titles
                    "url": link,
                    "source": source
                })
                seen_domains.add(source)

            if len(references) >= 3:  # Get 3 references per keyword for AdSense quality
                break

        return references

    def load_evergreen_keywords(self) -> Dict[str, Dict[str, List[str]]]:
        """Load evergreen keywords from JSON file"""
        evergreen_path = Path("data/evergreen_keywords.json")
        if not evergreen_path.exists():
            safe_print("⚠️  Evergreen keywords file not found, using empty pool")
            return {"tech": {"en": [], "ko": []}, "business": {"en": [], "ko": []}}

        with open(evergreen_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def generate_candidates(self, count: int = 15, keyword_type: str = "trend") -> List[Dict]:
        """Generate keyword candidates using Claude API

        Args:
            count: Number of keywords to generate
            keyword_type: "trend" or "evergreen"
        """
        safe_print(f"\n{'='*60}")
        safe_print(f"  🔍 Generating {count} {keyword_type} keyword candidates...")
        safe_print(f"{'='*60}\n")

        # Calculate per-language count (EN 50%, KO 50%)
        en_count = count // 2
        ko_count = count - en_count  # Remainder to KO

        if keyword_type == "evergreen":
            # Load evergreen keywords pool
            evergreen_pool = self.load_evergreen_keywords()

            # Format evergreen keywords for prompt
            evergreen_en = "\n".join([f"- {kw}" for cat in evergreen_pool.values() for kw in cat.get("en", [])])
            evergreen_ko = "\n".join([f"- {kw}" for cat in evergreen_pool.values() for kw in cat.get("ko", [])])

            # Collect existing keywords from queue to prevent duplicates
            existing_keywords = [t['keyword'] for t in self.queue_data.get('topics', [])]
            existing_keywords_text = "\n".join([f"- {kw}" for kw in existing_keywords[-100:]]) if existing_keywords else "없음"

            # Generate prompt with evergreen data
            prompt = CURATION_PROMPT_EVERGREEN.format(
                evergreen_en=evergreen_en,
                evergreen_ko=evergreen_ko,
                count=count,
                en_count=en_count,
                ko_count=ko_count,
                existing_keywords=existing_keywords_text
            )

            # For evergreen, we don't need real-time search results
            self.search_results = []

        else:  # trend
            # Fetch community topics only (HackerNews, Dev.to, Lobsters, ProductHunt)
            # Google Trends RSS removed: it produced non-tech (entertainment, weather, sports) keywords
            self.search_results = []
            community_data = self.fetch_community_topics()
            community_topics_list = community_data.get('en', [])

            # Format community topics for prompt (with additional context)
            def format_community_topic(t):
                base = f"- [{t['source']}] {t['title']} (score: {t['score']}, comments: {t['comments']})\n  URL: {t['url']}"

                # Add HackerNews top comments if available
                if t.get('top_comments'):
                    comments_text = "\n  💬 Top developer comments:\n"
                    for i, comment in enumerate(t['top_comments'][:2], 1):  # Max 2 comments
                        comments_text += f"    {i}. {comment[:200]}...\n" if len(comment) > 200 else f"    {i}. {comment}\n"
                    base += comments_text

                # Add ProductHunt description if available
                if t.get('description'):
                    desc = t['description'][:300] + '...' if len(t['description']) > 300 else t['description']
                    base += f"\n  📝 Description: {desc}"

                return base

            community_topics_formatted = "\n".join([
                format_community_topic(t)
                for t in community_topics_list[:15]  # Top 15 community topics
            ]) or "No community topics available"

            # Generate prompt with community data only
            prompt = CURATION_PROMPT_WITH_TRENDS.format(
                community_topics=community_topics_formatted,
                count=count,
                en_count=en_count,
                ko_count=ko_count
            )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=16000,  # Increased for 30+ keywords
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
        except Exception as e:
            safe_print(f"❌ ERROR: Claude API call failed")
            safe_print(f"   Error: {mask_secrets(str(e))}")
            safe_print(f"   This is a critical error - cannot continue without keyword candidates")
            sys.exit(1)

        if not response or not response.content:
            safe_print(f"❌ ERROR: Empty response from Claude API")
            safe_print(f"   This is a critical error - cannot continue without keyword candidates")
            sys.exit(1)

        # Parse JSON response
        content = response.content[0].text.strip()

        # Extract JSON from markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        try:
            candidates = json.loads(content)
        except json.JSONDecodeError as e:
            safe_print(f"❌ ERROR: Failed to parse JSON response from Claude")
            safe_print(f"   Parse error: {str(e)}")
            safe_print(f"   Raw response (first 500 chars):\n{content[:500]}")
            safe_print(f"   This is a critical error - cannot continue with invalid JSON")
            sys.exit(1)

        safe_print(f"✅ Generated {len(candidates)} candidates\n")

        # STEP 1: Remove duplicates (keep first occurrence, regardless of category)
        seen_keywords = {}
        dedup_candidates = []
        duplicates_removed = 0

        for candidate in candidates:
            keyword_lower = candidate.get('keyword', '').lower()
            if keyword_lower in seen_keywords:
                duplicates_removed += 1
                first_category = seen_keywords[keyword_lower]
                duplicate_category = candidate.get('category')
                safe_print(f"  🔴 DUPLICATE REMOVED: '{candidate.get('keyword')}' (duplicate category: {duplicate_category}, already exists as: {first_category})")
            else:
                # Store the category of the first occurrence
                seen_keywords[keyword_lower] = candidate.get('category')
                dedup_candidates.append(candidate)

        if duplicates_removed > 0:
            safe_print(f"\n⚠️  Removed {duplicates_removed} duplicate keywords from Claude's response")
            safe_print(f"    Policy: One keyword = one category (first occurrence wins)\n")

        # STEP 2: Enforce tech-only category (reject non-tech keywords)
        # Strategy: block obvious non-tech terms. Claude is already instructed to pick
        # tech-only, but sometimes reframes sports/entertainment keywords as "tech angle".
        non_tech_keywords = [
            # Sports (EN)
            'vs', 'match', 'league', 'cup', 'tournament', 'championship', 'season',
            'basketball', 'football', 'soccer', 'baseball', 'hockey', 'tennis', 'golf',
            'nba', 'nfl', 'mlb', 'nhl', 'premier league', 'uefa', 'champions league',
            'world cup', 'olympics', 'ufc', 'boxing', 'wrestling', 'mma', 'cricket', 'icc',
            # Sports clubs / teams (EN)
            'united', 'city fc', 'real madrid', 'barcelona',
            # Entertainment / Animation (EN)
            'gta', 'release date',
            'invincible', 'superhero', 'animated series', 'animation', 'cartoon', 'anime', 'manga',
            'tv series', 'tv show', 'streaming show', 'episode', 'season finale',
            'celebrity', 'actor', 'singer', 'idol', 'kpop', 'drama', 'movie',
            'wedding', 'marriage', 'divorce',
            # Weather / natural disasters (EN)
            'weather', 'snow storm', 'freeze watch', 'frost warning', 'blizzard',
            'tornado', 'hurricane', 'storm watch', 'weather alert',
            # Legal non-tech (EN)
            'attorney', 'lawyer', 'accident', 'injury', 'lawsuit',
            # Sports (KO)
            '축구', '야구', '농구', '배구', '테니스', '골프', '선수권', '리그', '경기', '결승',
            '현대 모터스', '전북', '전남', '울산 hd', '수원',  # K-League clubs
            # Entertainment (KO)
            '연예인', '드라마', '아이돌', '가수', '배우', '예능', '영화',
            '애니메이션', '만화', '웹툰', '라노벨',
            '결혼', '이혼', '웨딩', '출산', '열애', '교제', '연애',
            # Weather / natural disasters (KO)
            '날씨', '폭우', '한파', '폭설', '주의보', '경보', '태풍', '폭풍', '기상청',
        ]

        rejected_non_tech = []
        filtered_dedup = []
        for candidate in dedup_candidates:
            keyword_lower = candidate.get('keyword', '').lower()
            category = candidate.get('category', 'tech')

            # Force all categories to tech
            if category != 'tech':
                candidate['category'] = 'tech'

            # Reject clearly non-tech keywords
            is_non_tech = any(term in keyword_lower for term in non_tech_keywords)

            # Reject Korean person names: pure Hangul 2-4 chars (e.g. "서주경")
            # or person name + life event (e.g. "전경민 결혼")
            import re
            keyword_orig = candidate.get('keyword', '')
            is_person_name = bool(re.match(r'^[가-힣]{2,4}$', keyword_orig)) or \
                             bool(re.match(r'^[가-힣]{2,4}\s+(결혼|이혼|출산|사망|사고|논란|파문|열애|연애|교제)$', keyword_orig))

            if is_non_tech or is_person_name:
                rejected_non_tech.append(keyword_orig)
                reason = "person name" if is_person_name else "non-tech"
                safe_print(f"  🔴 REJECTED ({reason}): {keyword_orig}")
            else:
                filtered_dedup.append(candidate)

        dedup_candidates = filtered_dedup

        if rejected_non_tech:
            safe_print(f"\n⚠️  Rejected {len(rejected_non_tech)} non-tech keywords (tech-only strategy)\n")

        # Apply risk filtering
        filtered_candidates = self.filter_by_risk(dedup_candidates)

        # Extract references for each candidate
        safe_print(f"📚 Extracting references for {len(filtered_candidates)} candidates...\n")
        keywords_with_refs = 0
        keywords_without_refs = 0

        for candidate in filtered_candidates:
            keyword = candidate.get("keyword", "")
            lang = candidate.get("language", "en")
            kw_type = candidate.get("keyword_type", "trend")

            # Fetch references directly by keyword via Brave Search.
            # trend: freshness='pw' (past week), evergreen: freshness='py' (past year)
            freshness = "pw" if kw_type == "trend" else "py"
            references = self.fetch_evergreen_references(keyword, lang, freshness)

            candidate["references"] = references
            if references:
                safe_print(f"  ✓ {len(references)} refs for: {keyword[:50]}...")
                keywords_with_refs += 1
            else:
                keywords_without_refs += 1

        safe_print("")

        # Validation warning
        if keywords_without_refs > 0:
            safe_print(f"⚠️  WARNING: {keywords_without_refs}/{len(filtered_candidates)} keywords have NO references")
            safe_print(f"   This means generated posts will lack credible sources!")
            if not self.brave_api_key:
                safe_print(f"   ROOT CAUSE: BRAVE_API_KEY not configured\n")
        else:
            safe_print(f"✅ All {keywords_with_refs} keywords have references!\n")

        return filtered_candidates

    def display_candidates(self, candidates: List[Dict]):
        """Display candidates with numbered list"""
        safe_print(f"{'='*60}")
        safe_print(f"  📋 Keyword Candidates")
        safe_print(f"{'='*60}\n")

        # Group by language
        by_lang = {"en": [], "ko": []}
        for c in candidates:
            lang = c.get("language", "en")
            if lang in by_lang:
                by_lang[lang].append(c)

        idx = 1
        lang_names = {"en": "English", "ko": "Korean"}

        for lang in ["en", "ko"]:
            if by_lang[lang]:
                safe_print(f"\n[{lang_names[lang]}]")
                safe_print("-" * 60)

                for candidate in by_lang[lang]:
                    type_emoji = "🔥" if candidate.get("keyword_type") == "trend" else "🌲"
                    comp_emoji = {
                        "low": "🟢",
                        "medium": "🟡",
                        "high": "🔴"
                    }.get(candidate.get("competition_level", "medium"), "⚪")

                    safe_print(f"\n{idx}. {type_emoji} {candidate['keyword']}")
                    safe_print(f"   Category: {candidate['category']} | Competition: {comp_emoji} {candidate.get('competition_level', 'N/A')}")
                    safe_print(f"   Intent: {candidate['search_intent']}")
                    safe_print(f"   Angle: {candidate['angle']}")
                    safe_print(f"   Why: {candidate.get('why_it_works', 'N/A')[:80]}...")

                    idx += 1

        safe_print(f"\n{'='*60}\n")

    def interactive_selection(self, candidates: List[Dict]) -> List[Dict]:
        """Interactive selection of keywords"""
        safe_print("어떤 키워드를 큐에 추가할까요?")
        safe_print("숫자를 쉼표로 구분해서 입력하세요 (예: 1,3,5,7,10)")
        safe_print("또는 'all'을 입력하면 전부 추가됩니다.")
        safe_print("'q'를 입력하면 취소합니다.\n")

        while True:
            user_input = input("선택: ").strip()

            if user_input.lower() == 'q':
                safe_print("❌ 취소되었습니다.")
                return []

            if user_input.lower() == 'all':
                return candidates

            try:
                # Parse selected indices
                selected_indices = [int(x.strip()) for x in user_input.split(',')]

                # Validate indices
                if any(idx < 1 or idx > len(candidates) for idx in selected_indices):
                    safe_print(f"⚠️  잘못된 번호입니다. 1-{len(candidates)} 범위로 입력하세요.\n")
                    continue

                # Convert to 0-based index and return selected candidates
                selected = [candidates[idx - 1] for idx in selected_indices]
                return selected

            except ValueError:
                safe_print("⚠️  잘못된 형식입니다. 예: 1,3,5\n")

    def _validate_keyword_language(self, keyword: str, language: str) -> bool:
        """Validate that keyword matches the specified language"""

        def has_hangul(text):
            """Check if text contains Korean characters"""
            return any('\uac00' <= char <= '\ud7a3' for char in text)

        def has_hiragana_katakana(text):
            """Check if text contains Japanese characters"""
            return any(
                ('\u3040' <= char <= '\u309f') or  # Hiragana
                ('\u30a0' <= char <= '\u30ff')     # Katakana
                for char in text
            )

        # Validation rules
        if language == 'ko':
            # Korean must have Hangul
            if not has_hangul(keyword):
                return False
            # Korean cannot have Japanese characters
            if has_hiragana_katakana(keyword):
                return False
        elif language == 'en':
            # English cannot have Korean/Japanese
            if has_hangul(keyword) or has_hiragana_katakana(keyword):
                return False

        return True

    def add_to_queue(self, selected: List[Dict]):
        """Add selected keywords to topic queue with language and duplicate validation"""
        if not selected:
            safe_print("선택된 키워드가 없습니다.")
            return

        safe_print(f"\n{'='*60}")
        safe_print(f"  💾 큐에 {len(selected)}개 키워드 추가 중...")
        safe_print(f"{'='*60}\n")

        # Get existing keywords for duplicate check (case-insensitive)
        existing_keywords = {t['keyword'].lower() for t in self.queue_data['topics']}

        # Get next ID
        existing_ids = [int(t['id'].split('-')[0]) for t in self.queue_data['topics'] if t['id'].split('-')[0].isdigit()]
        next_id = max(existing_ids) + 1 if existing_ids else 1

        added_count = 0
        rejected_count = 0
        for candidate in selected:
            # Validate keyword-language match
            keyword = candidate.get('keyword', '')
            language = candidate.get('language', 'en')

            # Check for duplicate keyword
            if keyword.lower() in existing_keywords:
                safe_print(f"  🔴 REJECTED: Duplicate keyword")
                safe_print(f"     Keyword: {keyword}")
                safe_print(f"     Reason: Keyword already exists in queue")
                rejected_count += 1
                continue

            if not self._validate_keyword_language(keyword, language):
                safe_print(f"  🔴 REJECTED: Keyword-language mismatch")
                safe_print(f"     Keyword: {keyword}")
                safe_print(f"     Language: {language}")
                safe_print(f"     Reason: Keyword contains characters from different language")
                rejected_count += 1
                continue
            # Generate topic ID
            topic_id = f"{next_id:03d}-{candidate['language']}-{candidate['category']}-{candidate['keyword'][:20].replace(' ', '-')}"

            # Create topic entry
            topic = {
                "id": topic_id,
                "keyword": candidate['keyword'],
                "category": candidate['category'],
                "lang": candidate['language'],
                "priority": candidate.get('priority', 7),
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "retry_count": 0,
                "keyword_type": candidate.get('keyword_type', 'evergreen'),
                "search_intent": candidate.get('search_intent', ''),
                "angle": candidate.get('angle', ''),
                "competition_level": candidate.get('competition_level', 'medium'),
                "references": candidate.get('references', [])
            }

            # Add expiry_days for trend keywords
            if topic['keyword_type'] == 'trend':
                topic['expiry_days'] = 3  # 3 days expiry for trending keywords
                # Add content_type hint for trends: prefer BREAKING
                topic['content_type_hint'] = 'BREAKING'
            elif topic['keyword_type'] == 'evergreen':
                # Add content_type hint for evergreen: prefer GUIDE
                topic['content_type_hint'] = 'GUIDE'
            else:
                # Mixed or undefined: let generate_posts.py decide
                topic['content_type_hint'] = 'MIXED'

            self.queue_data['topics'].append(topic)

            type_label = "🔥 Trend" if topic['keyword_type'] == 'trend' else "🌲 Evergreen"
            safe_print(f"  ✓ Added: {type_label} | {candidate['keyword']}")

            added_count += 1
            next_id += 1

        # Save queue
        self._save_queue()

        safe_print(f"\n✅ {added_count}개 키워드가 큐에 추가되었습니다!")
        if rejected_count > 0:
            safe_print(f"🔴 {rejected_count}개 키워드가 언어 불일치로 거부되었습니다!")
        safe_print(f"📊 Total topics in queue: {len(self.queue_data['topics'])}")

        # Show statistics
        self._show_queue_stats()

    def _show_queue_stats(self):
        """Show queue statistics"""
        topics = self.queue_data['topics']

        # Count by status (safe for any status value)
        by_status = {"pending": 0, "in_progress": 0, "completed": 0, "failed": 0}
        for t in topics:
            status = t.get('status', 'pending')
            by_status[status] = by_status.get(status, 0) + 1

        # Count by type
        by_type = {"trend": 0, "evergreen": 0, "unknown": 0}
        for t in topics:
            ktype = t.get('keyword_type', 'unknown')
            by_type[ktype] = by_type.get(ktype, 0) + 1

        # Count by language
        by_lang = {"en": 0, "ko": 0}
        for t in topics:
            lang = t.get('lang', 'en')
            if lang in by_lang:
                by_lang[lang] = by_lang.get(lang, 0) + 1

        safe_print(f"\n{'='*60}")
        safe_print(f"  📊 Queue Statistics")
        safe_print(f"{'='*60}")
        safe_print(f"  Status: Pending={by_status['pending']}, In Progress={by_status['in_progress']}, Completed={by_status['completed']}")
        safe_print(f"  Type: 🔥 Trend={by_type['trend']}, 🌲 Evergreen={by_type['evergreen']}, Unknown={by_type['unknown']}")
        safe_print(f"  Language: EN={by_lang['en']}, KO={by_lang['ko']}")
        safe_print(f"{'='*60}\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Keyword Curator for blog content")
    parser.add_argument('--count', type=int, default=15, help="Number of candidates to generate (default: 15)")
    parser.add_argument('--auto', action='store_true', help="Automatically add all candidates without interactive selection")
    parser.add_argument('--type', choices=['trend', 'evergreen', 'mixed'], default='trend',
                       help="Keyword type: trend (default), evergreen, or mixed")
    parser.add_argument('--evergreen-ratio', type=float, default=0.2,
                       help="Ratio of evergreen keywords in mixed mode (default: 0.2)")
    args = parser.parse_args()

    # Check API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        safe_print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    # Initialize curator
    curator = KeywordCurator()

    # Generate candidates based on type
    if args.type == 'mixed':
        # Mixed mode: Community 80% + Evergreen 20%
        # trend candidates come from HackerNews, Dev.to, Lobsters, ProductHunt only
        evergreen_count = int(args.count * args.evergreen_ratio)
        trend_count = args.count - evergreen_count

        safe_print(f"\n📊 Mixed Mode: {trend_count} trend (Community sources) + {evergreen_count} evergreen keywords")
        safe_print(f"   Sources: HackerNews + Dev.to + Lobsters + ProductHunt + Evergreen {evergreen_count}\n")

        # Generate trend keywords
        if trend_count > 0:
            trend_candidates = curator.generate_candidates(count=trend_count, keyword_type="trend")
        else:
            trend_candidates = []

        # Generate evergreen keywords
        if evergreen_count > 0:
            evergreen_candidates = curator.generate_candidates(count=evergreen_count, keyword_type="evergreen")
        else:
            evergreen_candidates = []

        # Combine candidates
        candidates = trend_candidates + evergreen_candidates

    else:
        # Single type mode
        candidates = curator.generate_candidates(count=args.count, keyword_type=args.type)

    # Display candidates
    curator.display_candidates(candidates)

    # Selection
    if args.auto:
        # Auto mode: add all candidates
        safe_print("\n🤖 Auto mode: Adding all candidates to queue...\n")
        selected = candidates
    else:
        # Interactive mode: ask user
        selected = curator.interactive_selection(candidates)

    # Add to queue
    if selected:
        curator.add_to_queue(selected)

    safe_print("\n✨ Done!\n")


if __name__ == "__main__":
    main()
