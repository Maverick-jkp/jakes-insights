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
너는 광고 수익 최적화를 위한 키워드 큐레이터다.
아래 실시간 트렌드 검색 결과와 커뮤니티 토픽을 바탕으로 **고CPC, 감정 반응형** 키워드를 제안하라.

📊 **소스 비중**: Google Trends 40% + Community 40% + Evergreen 20%
📊 **언어 비중**: EN 40% ({en_count}개), KO 40% ({ko_count}개), JA 20% ({ja_count}개)

실시간 트렌드 데이터 (언어별로 구분됨):

🇺🇸 English (US) Trends:
{trends_en}

🇰🇷 Korean (KR) Trends:
{trends_ko}

🇯🇵 Japanese (JP) Trends:
{trends_ja}

🌐 **Community Topics (HackerNews, Dev.to, Lobsters, ProductHunt)**:
{community_topics}

**중요**: Community Topics는 영어 원문이지만, 한국/일본 독자에게도 유용한 내용이면 KO/JA 버전으로도 제안하라.
예: "OpenAI releases new model" → EN 원문 + KO "OpenAI 새 모델 출시" + JA "OpenAI新モデル発表"

**🔴 중요 규칙: 언어-키워드 매칭 (CRITICAL - 위반 시 즉시 거부)**
1. English (US) 트렌드의 Query → language: "en"으로만 사용
2. Korean (KR) 트렌드의 Query → language: "ko"로만 사용
3. Japanese (JP) 트렌드의 Query → language: "ja"로만 사용
4. **절대로 일본어 키워드를 한국어 게시물에 사용하거나, 한국어 키워드를 일본어 게시물에 사용하지 말 것**
5. 위 트렌드 데이터의 Query를 그대로 keyword로 사용하라. 절대 재해석하거나 재작성하지 말 것.

**🚨 언어 문자 검증 규칙 (반드시 준수):**
- **영어(en) 키워드**: 한글(가-힣), 히라가나(ぁ-ん), 가타카나(ァ-ヶ), 한자(一-龯) 포함 금지
  - 올바른 예: "NBA", "Kobe Bryant", "quad cortex"
  - 잘못된 예: "붉은사막" (한글 포함), "フォートナイト" (가타카나 포함)
- **한국어(ko) 키워드**: 반드시 한글(가-힣) 포함 필요
  - 올바른 예: "붉은사막", "김연아", "u23" (영문 약어는 허용)
  - 잘못된 예: "red desert" (한글 없음), "フォートナイト" (일본어)
- **일본어(ja) 키워드**: 반드시 히라가나/가타카나/한자 포함 필요
  - 올바른 예: "フォートナイト", "三笘薫", "地震速報"
  - 잘못된 예: "fortnite" (일본어 문자 없음), "붉은사막" (한글)

목표:
한국어 / 영어 / 일본어 각각에서
**불안, 분노, 궁금증**을 유발하는 키워드만 제안하라.

금지:
- 추상적인 트렌드 요약 ("AI 트렌드", "새로운 기술")
- 교육/정보성 키워드 ("~하는 방법", "~란 무엇인가")
- 긍정적이고 평화로운 키워드
- **Query를 재해석하거나 다시 쓰는 것**
- **같은 키워드를 다른 카테고리로 중복 제안하는 것** (예: "相葉雅紀"를 tech와 society 모두에 제안하지 말 것. 하나의 키워드는 하나의 카테고리만 가져야 함)

출력 형식:
반드시 JSON 형식으로만 응답하라.

[
  {{
    "keyword": "위 트렌드 데이터의 Query를 그대로 복사 (재해석 금지)",
    "raw_search_title": "사용자가 구글에 검색할 때 정확히 입력하는 검색어 (keyword와 동일하게)",
    "editorial_title": "기사 제목 형식의 독자 친화적 제목",
    "core_fear_question": "사용자의 핵심 두려움을 담은 질문 한 문장",
    "language": "ko",
    "category": "tech",  # ONLY: tech, business, society, entertainment, sports (5 categories + 1 reserved)
    "search_intent": "사용자가 지금 당장 검색하는 이유 (행동하지 않으면 무엇을 잃는지)",
    "angle": "이 키워드를 다룰 때의 관점",
    "competition_level": "low",
    "why_it_works": "사용자가 지금 행동하지 않으면 영구적으로 무엇을 잃는지 (마감/기회 손실 중심)",
    "purpose": "high competition인 경우에만: Traffic acquisition / Brand positioning / Viral content 중 하나",
    "keyword_type": "trend",
    "priority": 7,
    "risk_level": "safe",
    "name_policy": "no_real_names",
    "intent_signal": "STATE_CHANGE"
  }}
]

중요:
- keyword_type은 무조건 "trend"만 사용 (evergreen 금지)
- category는 **5개 카테고리만** 사용: "tech", "business", "society", "entertainment", "sports"
- **카테고리 분배 비율 (중요)**:
  * tech: 40% (가장 높은 CPM, 우선순위 최고)
  * business: 20%
  * society: 15%
  * sports: 15%
  * entertainment: 10%
- Tech 관련 키워드는 최대한 많이 선택할 것 (AI, ML, cloud, programming, frameworks, devops 등)
  - ⚠️ "finance", "lifestyle", "education"은 더 이상 사용 금지 (각각 business, society, tech로 통합됨)
- language는 "en", "ko", "ja" 중 하나 (비율: EN 40%, KO 40%, JA 20%)
- competition_level은 "low", "medium", "high" 중 하나
- priority는 1-10 사이의 숫자 (높을수록 우선순위 높음)
- risk_level은 "safe", "caution", "high_risk" 중 하나 (기본값: "safe")
- name_policy는 "no_real_names", "generic_only" 중 하나 (기본값: "no_real_names")
- intent_signal은 "STATE_CHANGE", "PROMISE_BROKEN", "SILENCE", "DEADLINE_LOST", "COMPARISON" 중 하나
- 지금 시점(2026년 1월)에서 현실적인 키워드만 제안
- 예시는 절대 사용하지 말고, 실제 검색 가능성이 높은 키워드만 제안
- **중요**: 위 실시간 트렌드 데이터의 Query를 keyword 필드에 그대로 복사할 것
- **keyword 필드는 절대 재작성하지 말고 Query를 정확히 그대로 사용**
- **중요**: 5개 카테고리(tech, business, society, entertainment, sports)를 반드시 고르게 분배할 것

**🔴 카테고리 분류 가이드 (5개 카테고리 - CRITICAL):**
- **tech**: 기술, IT, AI, 게임, 앱, 소프트웨어, **교육 기술(EdTech), 온라인 학습**
  - 예시: "AI", "ChatGPT", "iPhone", "게임", "온라인 강의", "코딩 교육"
  - ⚠️ 이전 "education" 카테고리 내용 포함

- **business**: 경제, 기업, 주식, 부동산, 창업, **금융, 투자, 세금, 보험, 연금, 시장**
  - 예시: "테슬라 주가", "부동산 시장", "스타트업", "비트코인", "금리", "환율"
  - ⚠️ 이전 "finance" 카테고리 내용 포함

- **society**: 사회 이슈, 정치, 정책, 범죄, 재난, **건강, 여행, 음식, 패션, 라이프스타일**
  - 예시: "지진속보", "정부 정책", "다이어트", "여행지 추천", "건강 관리", "트렌드"
  - ⚠️ 이전 "lifestyle" 카테고리 내용 포함
  - **주의**: 스포츠 관련은 무조건 sports로 (사회 이슈라도)

- **entertainment**: 영화, 드라마, 음악, 예능, 연예인 (단, 스포츠 선수는 제외)
  - 예시: "넷플릭스", "BTS", "오징어게임", "영화 리뷰"

- **sports**: 모든 운동 경기, 선수, 팀 (축구, 야구, 농구, UFC, e스포츠, U23 등 전부)
  - 예시: "UFC", "u23", "손흥민", "KBO", "NBA", "wimbledon"
  - **중요**: 격투기, 청소년 스포츠도 무조건 sports
- **education**: 교육, 대학, 입시, 자격증, 학습

언어별 톤 차이:
- 🇺🇸 English: rights, compensation, legal leverage, lawsuits 중심
- 🇰🇷 Korean: 불공정, 좌절, 소비자 보호, 책임 추궁 중심
- 🇯🇵 Japanese: 불투명성, 공식 절차, 적절한 대응 방법 중심

**🔴 안전 가이드라인:**

주의사항:
- 명예훼손/비난/비방 표현 금지
- 사실 기반의 trending 키워드는 실명 사용 가능

각 키워드에 리스크 레벨 표시:
- "risk_level": "safe" (기본값)
- "risk_level": "caution" (논란 가능성 있음)

각 키워드에 실명 정책 표시:
- "name_policy": "no_real_names" (실명 불필요)
- "name_policy": "real_names_ok" (trending 뉴스 등 실명 포함 가능)

**중복 방지 규칙:**
- Intent signals: STATE_CHANGE, PROMISE_BROKEN, SILENCE, DEADLINE_LOST, COMPARISON
- 같은 signal을 가진 키워드는 언어당 최대 2개까지만
- 5개 signal을 언어별로 균등하게 분배

**🚨 언어별 키워드 생성 규칙 (절대 준수):**
반드시 정확히 {count}개의 키워드를 생성하라:
- 영어(en): 정확히 {per_lang}개 (1개라도 부족하거나 초과하면 안 됨)
- 한국어(ko): 정확히 {per_lang}개 (1개라도 부족하거나 초과하면 안 됨)
- 일본어(ja): 정확히 {per_lang}개 (1개라도 부족하거나 초과하면 안 됨)
- 총합: 정확히 {count}개

**언어별 트렌드 데이터 사용 규칙:**
- 🇺🇸 English (US) Trends에서 {per_lang}개 키워드 추출 → language: "en"
- 🇰🇷 Korean (KR) Trends에서 {per_lang}개 키워드 추출 → language: "ko"
- 🇯🇵 Japanese (JP) Trends에서 {per_lang}개 키워드 추출 → language: "ja"
- 만약 한 언어의 트렌드가 부족하면, 다른 언어 트렌드를 절대 사용하지 말고 해당 언어로 새로운 키워드를 생성하라

각 언어 내에서 5개 카테고리(tech, business, society, entertainment, sports)를 최대한 균등하게 분배하되,
반드시 각 언어별로 정확히 {per_lang}개씩 생성하는 것이 최우선이다.

⚠️ **카테고리 변경 사항 (2026-01-25):**
- 기존 8개 → 새로운 5개 카테고리로 통합
- "education" → "tech"로 통합
- "finance" → "business"로 통합
- "lifestyle" → "society"로 통합"""


CURATION_PROMPT_EVERGREEN = """역할:
너는 **장기 트래픽** 확보를 위한 Evergreen 키워드 큐레이터다.
아래 Evergreen 키워드 풀에서 **검색량이 지속되는, 교육/가이드성** 키워드를 제안하라.

Evergreen 키워드 풀 (언어별로 구분됨):

🇺🇸 English Keywords:
{evergreen_en}

🇰🇷 Korean Keywords:
{evergreen_ko}

🇯🇵 Japanese Keywords:
{evergreen_ja}

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
- keyword_type은 무조건 "evergreen"만 사용 (trend 금지)
- category는 **5개 카테고리만** 사용: "tech", "business", "society", "entertainment", "sports"
- language는 "en", "ko", "ja" 중 하나 (비율: EN 40%, KO 40%, JA 20%)
- competition_level은 "low", "medium"만 사용 (high 금지 - 경쟁 피할 것)
- priority는 5-8 사이 (Evergreen은 트렌드보다 낮은 우선순위)
- risk_level은 무조건 "safe" (Evergreen은 안전해야 함)
- content_depth는 "comprehensive" (상세한 가이드 형식)

**🔴 카테고리별 Evergreen 키워드 예시:**
- **tech**: "프로그래밍 독학 방법", "web development roadmap", "AI tools for beginners"
- **business**: "passive income ideas", "부업 아이디어", "startup funding guide"
- **society**: "mental health management", "건강한 생활 습관", "climate change solutions"
- **entertainment**: "Netflix recommendations", "음악 제작 입문", "photography tips"
- **sports**: "home workout routine", "마라톤 훈련 계획", "yoga for beginners"

**🚨 언어별 키워드 생성 규칙:**
반드시 정확히 {count}개의 키워드를 생성하라:
- 영어(en): 정확히 {per_lang}개
- 한국어(ko): 정확히 {per_lang}개
- 일본어(ja): 정확히 {per_lang}개
- 총합: 정확히 {count}개

각 언어 내에서 5개 카테고리를 균등하게 분배할 것.
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
            self.model = "claude-sonnet-4-5-20250929"
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
        if any(word in query.lower() for word in ["after", "갑자기", "suddenly", "突然", "overnight"]):
            signals.append("STATE_CHANGE")

        # Promise broken patterns
        if any(word in query.lower() for word in ["promised", "supposed to", "약속", "発表", "denied", "거부", "拒否"]):
            signals.append("PROMISE_BROKEN")

        # Silence patterns
        if any(word in query.lower() for word in ["no response", "ignored", "説明なし", "무응답", "침묵"]):
            signals.append("SILENCE")

        # Deadline/time loss patterns
        if any(word in query.lower() for word in ["deadline", "too late", "마감", "期限", "놓침", "逃し"]):
            signals.append("DEADLINE_LOST")

        # Comparison/injustice patterns
        if any(word in query.lower() for word in ["others got", "only me", "나만", "自分だけ"]):
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
            "US": "https://trends.google.co.kr/trending/rss?geo=US",
            "JP": "https://trends.google.co.kr/trending/rss?geo=JP"
        }

        # Map region to language
        region_to_lang = {
            "KR": "ko",
            "US": "en",
            "JP": "ja"
        }

        # Group trends by language
        trends_by_lang = {"ko": [], "en": [], "ja": []}

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
            safe_print(f"     EN: {len(trends_by_lang['en'])}, KO: {len(trends_by_lang['ko'])}, JA: {len(trends_by_lang['ja'])}\n")
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
                ],
                "ja": [
                    "アカウント停止 理由説明なし",
                    "返金約束したが 拒否された",
                    "政府支援 突然 条件厳しく",
                    "謝罪文出したが 炎上続く",
                    "リコール発表 返金対応なし"
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
        trends_by_lang_formatted = {"en": [], "ko": [], "ja": []}
        for r in all_results:
            lang = r.get('query_lang', 'en')
            trends_by_lang_formatted[lang].append(
                f"Query: {r['query']}\nTitle: {r['title']}\nSnippet: {r['snippet']}\n"
            )

        # Convert to string format per language
        trends_formatted = {}
        for lang in ["en", "ko", "ja"]:
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

    def fetch_evergreen_references(self, keyword: str, lang: str) -> List[Dict]:
        """Fetch references for evergreen keywords on-demand using Brave Search"""
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
                "freshness": "py"  # Past year (for evergreen content)
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
            return {"tech": {"en": [], "ko": [], "ja": []}, "business": {"en": [], "ko": [], "ja": []}}

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

        # Calculate per-language count
        per_lang = count // 3  # Distribute evenly across 3 languages

        if keyword_type == "evergreen":
            # Load evergreen keywords pool
            evergreen_pool = self.load_evergreen_keywords()

            # Format evergreen keywords for prompt
            evergreen_en = "\n".join([f"- {kw}" for cat in evergreen_pool.values() for kw in cat.get("en", [])])
            evergreen_ko = "\n".join([f"- {kw}" for cat in evergreen_pool.values() for kw in cat.get("ko", [])])
            evergreen_ja = "\n".join([f"- {kw}" for cat in evergreen_pool.values() for kw in cat.get("ja", [])])

            # Generate prompt with evergreen data
            prompt = CURATION_PROMPT_EVERGREEN.format(
                evergreen_en=evergreen_en,
                evergreen_ko=evergreen_ko,
                evergreen_ja=evergreen_ja,
                count=count,
                per_lang=per_lang
            )

            # For evergreen, we don't need real-time search results
            self.search_results = []

        else:  # trend
            # Fetch trending topics from Google (store for reference extraction)
            self.search_results = []  # Store search results
            trends_by_lang = self.fetch_trending_topics()

            # Fetch community topics (HackerNews, Dev.to, Lobsters, ProductHunt)
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

            # Calculate language-specific counts (EN 40%, KO 40%, JA 20%)
            en_count = int(count * 0.4)
            ko_count = int(count * 0.4)
            ja_count = count - en_count - ko_count  # Remainder goes to JA

            # Generate prompt with trending data (grouped by language)
            prompt = CURATION_PROMPT_WITH_TRENDS.format(
                trends_en=trends_by_lang.get('en', 'No English trends available'),
                trends_ko=trends_by_lang.get('ko', 'No Korean trends available'),
                trends_ja=trends_by_lang.get('ja', 'No Japanese trends available'),
                community_topics=community_topics_formatted,
                count=count,
                per_lang=per_lang,
                en_count=en_count,
                ko_count=ko_count,
                ja_count=ja_count
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

        # STEP 2: Auto-correct sports keywords category
        sports_keywords = ['vs', 'vs.', 'game', 'match', 'league', 'cup', 'tournament', 'championship',
                          'basketball', 'football', 'soccer', 'baseball', 'hockey', 'tennis', 'golf',
                          'nba', 'nfl', 'mlb', 'nhl', 'premier league', 'uefa', 'champions league',
                          'world cup', 'olympics', 'ufc', 'boxing', 'wrestling', 'mma',
                          'u23', 'u-23', 'u21', 'u-21', 'player', 'team', 'squad']

        corrected_count = 0
        for candidate in dedup_candidates:
            keyword_lower = candidate.get('keyword', '').lower()
            category = candidate.get('category', '')

            # Auto-detect sports keywords
            if category != 'sports':
                is_sports = any(sport_term in keyword_lower for sport_term in sports_keywords)
                if is_sports:
                    old_category = category
                    candidate['category'] = 'sports'
                    corrected_count += 1
                    safe_print(f"  ✅ AUTO-CORRECTED: {candidate.get('keyword')} ({old_category} → sports)")

        if corrected_count > 0:
            safe_print(f"\n✅ Auto-corrected {corrected_count} sports keywords\n")

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

            # For evergreen keywords, fetch references on-demand
            if kw_type == "evergreen" and not self.search_results:
                references = self.fetch_evergreen_references(keyword, lang)
            else:
                references = self.extract_references(self.search_results, keyword, lang)

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
            if not self.google_api_key or not self.google_cx:
                safe_print(f"   ROOT CAUSE: Google Custom Search API credentials not configured")
                safe_print(f"   FIX: Set GOOGLE_API_KEY and GOOGLE_CX environment variables\n")
        else:
            safe_print(f"✅ All {keywords_with_refs} keywords have references!\n")

        return filtered_candidates

    def display_candidates(self, candidates: List[Dict]):
        """Display candidates with numbered list"""
        safe_print(f"{'='*60}")
        safe_print(f"  📋 Keyword Candidates")
        safe_print(f"{'='*60}\n")

        # Group by language
        by_lang = {"en": [], "ko": [], "ja": []}
        for c in candidates:
            lang = c.get("language", "en")
            by_lang[lang].append(c)

        idx = 1
        lang_names = {"en": "English", "ko": "Korean", "ja": "Japanese"}

        for lang in ["en", "ko", "ja"]:
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
        import unicodedata

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

        def has_kanji_only(text):
            """Check if text contains only Kanji/Chinese characters (could be Japanese)"""
            return any('\u4e00' <= char <= '\u9fff' for char in text)

        def has_vietnamese_chars(text):
            """Check if text contains Vietnamese diacritics"""
            vietnamese_chars = ['đ', 'ă', 'â', 'ê', 'ô', 'ơ', 'ư', 'á', 'à', 'ả', 'ã', 'ạ',
                               'ắ', 'ằ', 'ẳ', 'ẵ', 'ặ', 'ấ', 'ầ', 'ẩ', 'ẫ', 'ậ',
                               'é', 'è', 'ẻ', 'ẽ', 'ẹ', 'ế', 'ề', 'ể', 'ễ', 'ệ',
                               'í', 'ì', 'ỉ', 'ĩ', 'ị', 'ó', 'ò', 'ỏ', 'õ', 'ọ',
                               'ố', 'ồ', 'ổ', 'ỗ', 'ộ', 'ớ', 'ờ', 'ở', 'ỡ', 'ợ',
                               'ú', 'ù', 'ủ', 'ũ', 'ụ', 'ứ', 'ừ', 'ử', 'ữ', 'ự',
                               'ý', 'ỳ', 'ỷ', 'ỹ', 'ỵ']
            return any(char in text.lower() for char in vietnamese_chars)

        def has_spanish_only_chars(text):
            """Check if text contains Spanish-only characters (ñ, á, é, í, ó, ú, ü, ¿, ¡)"""
            # Check for Spanish question/exclamation marks
            if '¿' in text or '¡' in text:
                return True
            # Check for ñ
            if 'ñ' in text.lower():
                return True
            return False

        # Validation rules
        if language == 'ko':
            # Korean must have Hangul
            if not has_hangul(keyword):
                return False
            # Korean cannot have Japanese characters
            if has_hiragana_katakana(keyword) or (has_kanji_only(keyword) and not has_hangul(keyword)):
                return False
            # Korean cannot have Vietnamese/Spanish
            if has_vietnamese_chars(keyword) or has_spanish_only_chars(keyword):
                return False
        elif language == 'ja':
            # Japanese must have Hiragana/Katakana or Kanji
            if not (has_hiragana_katakana(keyword) or has_kanji_only(keyword)):
                return False
            # Japanese cannot have Korean
            if has_hangul(keyword):
                return False
            # Japanese cannot have Vietnamese/Spanish
            if has_vietnamese_chars(keyword) or has_spanish_only_chars(keyword):
                return False
        elif language == 'en':
            # English cannot have Korean/Japanese
            if has_hangul(keyword) or has_hiragana_katakana(keyword):
                return False
            # English cannot have Vietnamese (common in trends)
            if has_vietnamese_chars(keyword):
                return False
            # English cannot have Spanish-only markers
            if has_spanish_only_chars(keyword):
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
        by_lang = {"en": 0, "ko": 0, "ja": 0}
        for t in topics:
            lang = t.get('lang', 'en')
            by_lang[lang] = by_lang.get(lang, 0) + 1

        safe_print(f"\n{'='*60}")
        safe_print(f"  📊 Queue Statistics")
        safe_print(f"{'='*60}")
        safe_print(f"  Status: Pending={by_status['pending']}, In Progress={by_status['in_progress']}, Completed={by_status['completed']}")
        safe_print(f"  Type: 🔥 Trend={by_type['trend']}, 🌲 Evergreen={by_type['evergreen']}, Unknown={by_type['unknown']}")
        safe_print(f"  Language: EN={by_lang['en']}, KO={by_lang['ko']}, JA={by_lang['ja']}")
        safe_print(f"{'='*60}\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Keyword Curator for blog content")
    parser.add_argument('--count', type=int, default=15, help="Number of candidates to generate (default: 15)")
    parser.add_argument('--auto', action='store_true', help="Automatically add all candidates without interactive selection")
    parser.add_argument('--type', choices=['trend', 'evergreen', 'mixed'], default='trend',
                       help="Keyword type: trend (default), evergreen, or mixed")
    parser.add_argument('--evergreen-ratio', type=float, default=0.6,
                       help="Ratio of evergreen keywords in mixed mode (default: 0.6)")
    args = parser.parse_args()

    # Check API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        safe_print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    # Initialize curator
    curator = KeywordCurator()

    # Generate candidates based on type
    if args.type == 'mixed':
        # Mixed mode: generate both trend and evergreen
        evergreen_count = int(args.count * args.evergreen_ratio)
        trend_count = args.count - evergreen_count

        safe_print(f"\n📊 Mixed Mode: {trend_count} trend + {evergreen_count} evergreen keywords\n")

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
