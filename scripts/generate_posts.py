#!/usr/bin/env python3
"""
Content Generation Script

Generates blog posts using Claude API with two-stage process:
1. Draft Agent: Creates initial content
2. Editor Agent: Refines and improves the draft

Usage:
    python generate_posts.py --count 3
    python generate_posts.py --topic-id 001-en-tech-ai-coding
"""

import os
import sys
import json
import argparse
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from topic_queue import reserve_topics, mark_completed, mark_failed
from utils.security import safe_print, mask_secrets
from utils.content_classifier import ContentClassifier
from affiliate_config import (
    detect_product_mentions,
    generate_affiliate_link,
    create_affiliate_box,
    get_affiliate_disclosure,
    should_add_affiliate_links
)
from internal_linker import InternalLinker
from ab_test_manager import ABTestManager
from prompts import get_tutorial_prompt, get_analysis_prompt, get_news_prompt

try:
    from anthropic import Anthropic
except ImportError:
    safe_print("Error: anthropic package not installed")
    safe_print("Install with: pip install anthropic")
    sys.exit(1)

try:
    import requests
except ImportError:
    safe_print("Error: requests package not installed")
    safe_print("Install with: pip install requests")
    sys.exit(1)

try:
    import certifi
except ImportError:
    safe_print("Warning: certifi not installed - SSL verification may fail on Windows")
    safe_print("Install with: pip install certifi")
    certifi = None


# System prompts for different languages
SYSTEM_PROMPTS = {
    "en": f"""You are a professional writer for Jake's Tech Insights blog.

📅 IMPORTANT: Today's date is {datetime.now().year}-{datetime.now().month:02d}-{datetime.now().day:02d}
When referencing current information, ALWAYS use {datetime.now().year}, NOT previous years.

🎯 Goal: 800-1,100 words of concise, high-impact content (AdSense optimized)

[EDITORIAL POLICY - READ FIRST]
This is an in-depth tech analysis publication covering:
- Technology trends, SaaS analysis, data-driven industry reports, developer tools
- Reader value and analytical depth are PRIMARY goals
- Data-backed claims and evidence-based analysis ARE required

Your role:
- Provide evidence-based analysis with specific data points
- Structure content as analytical reports, not news recaps
- Include comparison data, market context, and actionable conclusions
- Every claim should reference a specific source, study, or dataset
- Assume all provided topics are already approved for publication
- Your job is to deliver clear, data-driven analysis

Output requirements:
- Include data-backed conclusions and practical recommendations
- Provide context: why this matters NOW and what comes next
- Support every claim with evidence or reasoning
- Be specific: use numbers, dates, and named sources

Every topic must clearly answer:
- What does the data show?
- Why does this matter for the reader?
- What should they do or watch for next?

[Length Guide - Brevity is Key!]
- Total: 800-1,100 words (optimized completion rate)
- Each ## section: 120-180 words (core insights only)
- Intro: 80-100 words (strong hook)
- Conclusion: 60-80 words (clear CTA)
- **Finish completely**: No mid-sentence cutoffs

[Key Takeaways Block - MANDATORY]
After the introduction and before the first ## heading, ALWAYS include:
> **Key Takeaways**
> - 3-5 bullet points summarizing key insights
> - Each must be a complete, declarative sentence with specific data
> - Written as standalone statements (quotable by AI search engines)

[Content Principles]
1. First paragraph: Hook with the core finding or data point (1-2 sentences)
2. Structure: Context → Data Analysis → Comparison → Practical Implications → Conclusion
3. Tone: Medium/Substack style - conversational, personal, direct
4. SEO: Keyword "{{keyword}}" naturally 4-6 times
5. Sections: 3-4 ## headings (scannable)
6. End: Clear CTA - question or next step

[Writing Style (Required!)]
- Use "you" and "I" sparingly for conversational tone
- Short direct sentences without filler phrases
- Natural transitions without overused connectors
- Avoid AI tell-tale phrases: "Here's the thing", "Sound familiar?", "Look", "Let me explain"
- Strong sentence starters: State facts directly, use specific data points
- Include recent dates, statistics, and concrete examples (2025-2026 data preferred)

[Style - Completion Optimized]
- Active voice, short sentences (1-2 lines)
- Core value only (cut fluff)
- Specific numbers/examples (1-2 selective)
- Bullet points for scannability
- End with punch: "Here's the bottom line."

[Absolutely Avoid]
- Redundancy: repeating same points ❌
- AI tells: "certainly", "it's important to note", "moreover", "furthermore"
- Academic tone: formal, distant language
- Abstract buzzwords: "revolutionary", "game-changer", "cutting-edge"
- Excessive emojis, unnecessary case studies
- Aggro triggers: "shock", "expose", "truth revealed", "jaw-dropping", "unbelievable"

[Headline Patterns - Analytical (Use ONLY these patterns)]
A. Comparison: "[X] vs [Y]: What the Data Shows in [year]"
B. Deep Dive: "Why [topic] Matters: [specific data point]"
C. Market Analysis: "The State of [topic] in [year]: Key Findings"
D. Practical Guide: "How [topic] Changes [outcome]: Data-Driven Analysis"

⚠️ Core: Complete 800-1,100 word article. Plenty of headroom in 12,000 tokens!""",

    "ko": f"""당신은 Jake's Tech Insights 블로그의 전문 작가입니다.

📅 중요: 오늘 날짜는 {datetime.now().year}년 {datetime.now().month}월 {datetime.now().day}일입니다
현재 정보를 언급할 때 반드시 {datetime.now().year}년을 사용하세요. 과거 연도 사용 금지.

🎯 핵심 목표: 800-1,100 단어의 간결하고 임팩트 있는 글 작성 (애드센스 최적화)

[편집 방침 - 반드시 숙지]
이 사이트는 심층 기술 분석 미디어입니다:
- 기술 트렌드, SaaS 분석, 데이터 기반 리포트, 개발자 도구
- 독자 가치와 분석의 깊이가 핵심 목표
- 데이터 기반 주장과 근거 있는 분석이 필수

당신의 역할:
- 구체적 데이터와 근거를 포함한 분석 제공
- 뉴스 요약이 아닌 분석 리포트 형태로 구성
- 비교 데이터, 시장 맥락, 실용적 결론 포함
- 모든 주장에 출처, 연구, 데이터셋 참조 필수
- 모든 토픽은 이미 편집팀이 승인한 것으로 간주하세요

출력 요구사항:
- 데이터 기반 결론과 실용적 권장 사항 포함
- 맥락 제공: 왜 지금 중요한지, 다음에 무엇이 올지
- 모든 주장에 근거나 논리 뒷받침
- 구체적으로: 숫자, 날짜, 실명 출처 사용

모든 토픽은 명확히 답해야 합니다:
- 데이터가 무엇을 보여주는가?
- 독자에게 왜 중요한가?
- 다음에 무엇을 주시해야 하는가?

[길이 가이드 - 간결함이 핵심!]
- 전체 글: 800-1,100 단어 (완독률 최적화)
- 각 ## 섹션: 120-180 단어 (핵심만 전달)
- 도입부: 80-100 단어 (강력한 후킹)
- 결론: 60-80 단어 (명확한 CTA)
- **마지막 문장까지 반드시 완성**: 끊김 없이 완결하세요

[핵심 요약 블록 - 필수]
도입부 이후, 첫 ## 헤딩 전에 반드시 포함:
> **핵심 요약**
> - 3-5개 핵심 인사이트를 불릿으로 요약
> - 각 포인트는 구체적 데이터를 포함한 완결된 문장
> - 선언적 문장으로 작성 (AI 검색 엔진이 인용 가능한 형태)

[콘텐츠 원칙]
1. 첫 문단: 핵심 발견이나 데이터 포인트로 후킹 (1-2문장)
2. 구조: 맥락 → 데이터 분석 → 비교 → 실용적 시사점 → 결론
3. 톤: 토스(Toss) 스타일 - 전문적이지만 편안한 친구 같은 느낌
4. SEO: 키워드 "{{keyword}}"를 자연스럽게 4-6회 포함
5. 섹션: 3-4개 ## 헤딩 (각 섹션은 읽기 쉽게)
6. 끝: 명확한 CTA - 질문이나 다음 단계 제안

[토스 스타일 말투 (필수!)]
- "~해요" 반말 존댓말 사용 (습니다/합니다 ❌)
- "어떤가요?", "한번 볼까요?", "궁금하지 않으세요?" 같은 친근한 질문
- "사실", "실제로", "그런데", "참고로" 같은 자연스러운 접속사
- 숫자를 친근하게: "10개 → 열 개", "50% → 절반", "3배 → 세 배"
- 짧고 강렬한 문장: "놀랍죠?", "맞아요.", "이게 핵심이에요."

[스타일 - 완독률 최적화]
- 능동태 위주, 짧은 문장 (1-2줄)
- 핵심만 전달 (불필요한 설명 제거)
- 구체적 숫자/예시 (1-2개만 선택적으로)
- 불릿 포인트 적극 활용 (스캔 가능하게)
- 문단 끝 강조: "왜 그럴까요?", "이게 핵심이에요."

[절대 금지]
- 중언부언: 같은 내용 반복 ❌
- AI 티: "물론", "~할 수 있습니다", "~하는 것이 중요합니다"
- 딱딱한 문체: "~습니다/~합니다" (해요체만!)
- 추상적 표현: "혁신적", "게임체인저", "주목할 만한"
- 과도한 이모지, 불필요한 사례 나열
- 어그로 단어: "충격", "폭로", "실체", "진실", "소름", "충격적", "완벽 정리", "한 번에 이해"

[헤드라인 패턴 - 분석형 (이 패턴만 사용)]
A. 비교: "[X] vs [Y]: 데이터가 보여주는 [year]년 현황"
B. 심층 분석: "[주제]가 중요한 이유: [구체적 데이터 포인트]"
C. 시장 분석: "[year]년 [주제] 현황: 핵심 발견"
D. 실전 가이드: "[주제]가 [결과]를 바꾸는 방법: 데이터 기반 분석"

⚠️ 핵심: 800-1,100 단어로 완결된 글을 작성하세요. 12,000 토큰 내에서 여유있게!"""
}


class ContentGenerator:
    def __init__(self, api_key: Optional[str] = None, unsplash_key: Optional[str] = None):
        """Initialize content generator with Claude API and Unsplash API"""
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            safe_print("❌ ERROR: ANTHROPIC_API_KEY not found")
            safe_print("   Please set it as environment variable or pass to constructor")
            safe_print("   Example: export ANTHROPIC_API_KEY='your-key-here'")
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Set it as environment variable or pass to constructor."
            )

        # Initialize with Prompt Caching beta header
        try:
            self.client = Anthropic(
                api_key=self.api_key,
                default_headers={
                    "anthropic-beta": "prompt-caching-2024-07-31"
                }
            )
            self.model = "claude-sonnet-4-5-20250929"
            safe_print("  ✓ Anthropic API client initialized successfully")
        except Exception as e:
            safe_print(f"❌ ERROR: Failed to initialize Anthropic client: {mask_secrets(str(e))}")
            raise

        # Unsplash API (optional)
        self.unsplash_key = unsplash_key or os.environ.get("UNSPLASH_ACCESS_KEY")
        if self.unsplash_key:
            safe_print("  🖼️  Unsplash API enabled")
        else:
            safe_print("  ⚠️  Unsplash API key not found (images will be skipped)")
            safe_print("     Set UNSPLASH_ACCESS_KEY environment variable to enable")

        # Initialize A/B Test Manager
        self.ab_test_manager = ABTestManager()
        safe_print("  🧪 A/B Test Manager initialized")

    def generate_draft(self, topic: Dict) -> tuple[str, str]:
        """Generate initial draft using Draft Agent with Prompt Caching

        Returns:
            tuple: (draft_content, content_type)
        """
        keyword = topic['keyword']
        lang = topic['lang']
        category = topic['category']
        references = topic.get('references', [])  # Get references from topic

        # Classify content type
        classifier = ContentClassifier()
        keywords = [keyword]  # Use topic keyword
        content_type = classifier.classify(keyword, keywords, category)

        safe_print(f"  🎯 Content type: {content_type}")
        safe_print(f"  📝 Generating draft for: {keyword}")

        # Get type-specific prompt
        if content_type == 'tutorial':
            user_prompt = get_tutorial_prompt(keyword, keywords, lang)
        elif content_type == 'analysis':
            user_prompt = get_analysis_prompt(keyword, keywords, lang)
        else:  # news
            user_prompt = get_news_prompt(keyword, keywords, lang)

        # Append references if available
        if references and len(references) > 0:
            user_prompt += "\n\n## References (Use for factual accuracy)\n\n"
            for i, ref in enumerate(references[:3], 1):  # Use top 3
                user_prompt += f"{i}. {ref['title']}\n   URL: {ref['url']}\n"
                if ref.get('snippet'):
                    user_prompt += f"   Summary: {ref['snippet']}\n"
                user_prompt += "\n"
            user_prompt += "Use these references for factual information, but DO NOT plagiarize. Write in your own words.\n"

        system_prompt = SYSTEM_PROMPTS[lang].format(keyword=keyword)

        # Use Prompt Caching: cache the system prompt
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=12000,
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                messages=[{
                    "role": "user",
                    "content": user_prompt
                }]
            )
        except Exception as e:
            error_msg = mask_secrets(str(e))
            safe_print(f"  ❌ ERROR: API call failed during draft generation")
            safe_print(f"     Topic: {topic.get('id', 'unknown')}")
            safe_print(f"     Keyword: {keyword}")
            safe_print(f"     Error: {error_msg}")
            raise

        if not response or not response.content:
            safe_print(f"  ❌ ERROR: Empty response from API")
            safe_print(f"     Topic: {topic.get('id', 'unknown')}")
            raise ValueError("Empty response from Claude API")

        draft = response.content[0].text

        # Log cache performance
        usage = response.usage
        cache_read = getattr(usage, 'cache_read_input_tokens', 0)
        cache_create = getattr(usage, 'cache_creation_input_tokens', 0)

        # Always show cache status
        if cache_read > 0:
            safe_print(f"  💾 Cache HIT: {cache_read} tokens saved!")
        elif cache_create > 0:
            safe_print(f"  💾 Cache created: {cache_create} tokens")
        else:
            safe_print(f"  ℹ️  No caching (usage: input={usage.input_tokens}, output={usage.output_tokens})")

        safe_print(f"  ✓ Draft generated ({len(draft)} chars)")
        return draft, content_type

    def edit_draft(self, draft: str, topic: Dict, content_type: str = 'analysis') -> str:
        """Refine draft using Editor Agent with Prompt Caching

        Args:
            draft: Draft content to edit
            topic: Topic dictionary
            content_type: Type of content (tutorial/analysis/news)

        Returns:
            str: Edited content
        """
        lang = topic['lang']

        safe_print(f"  ✏️  Editing draft...")

        if not draft or len(draft.strip()) == 0:
            safe_print(f"  ⚠️  WARNING: Empty draft provided for editing")
            safe_print(f"     Topic: {topic.get('id', 'unknown')}")
            raise ValueError("Cannot edit empty draft")

        editor_prompt = self._get_editor_prompt(lang, content_type)

        # Use Prompt Caching: cache the editor instructions
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=12000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": editor_prompt,
                                "cache_control": {"type": "ephemeral"}
                            },
                            {
                                "type": "text",
                                "text": f"\n\n---\n\n{draft}"
                            }
                        ]
                    }
                ]
            )
        except Exception as e:
            error_msg = mask_secrets(str(e))
            safe_print(f"  ❌ ERROR: API call failed during draft editing")
            safe_print(f"     Topic: {topic.get('id', 'unknown')}")
            safe_print(f"     Draft length: {len(draft)} chars")
            safe_print(f"     Error: {error_msg}")
            raise

        if not response or not response.content:
            safe_print(f"  ❌ ERROR: Empty response from editing API")
            safe_print(f"     Topic: {topic.get('id', 'unknown')}")
            raise ValueError("Empty response from Claude API during editing")

        edited = response.content[0].text

        # Log cache performance
        usage = response.usage
        cache_read = getattr(usage, 'cache_read_input_tokens', 0)
        cache_create = getattr(usage, 'cache_creation_input_tokens', 0)

        # Always show cache status
        if cache_read > 0:
            safe_print(f"  💾 Cache HIT: {cache_read} tokens saved!")
        elif cache_create > 0:
            safe_print(f"  💾 Cache created: {cache_create} tokens")
        else:
            safe_print(f"  ℹ️  No caching (usage: input={usage.input_tokens}, output={usage.output_tokens})")

        safe_print(f"  ✓ Draft edited ({len(edited)} chars)")
        return edited

    def _get_draft_prompt(self, keyword: str, category: str, lang: str, references: List[Dict] = None) -> str:
        """Get draft generation prompt based on language"""
        # Get current date in KST
        from datetime import datetime, timezone, timedelta
        kst = timezone(timedelta(hours=9))
        today = datetime.now(kst)
        current_date = today.strftime("%Y년 %m월 %d일")  # Korean format
        current_date_en = today.strftime("%B %d, %Y")  # English format
        current_year = today.year

        # Format references for prompt
        refs_section = ""
        if references and len(references) > 0:
            refs_list = "\n".join([
                f"- [{ref.get('title', 'Source')}]({ref.get('url', '')}) - {ref.get('source', '')}"
                for ref in references[:3]
            ])
            refs_section = f"\n\n📚 USE THESE REFERENCES:\n{refs_list}\n"

        prompts = {
            "en": f"""📅 TODAY'S DATE: {current_date_en}
⚠️ IMPORTANT: You are writing this article as of TODAY ({current_date_en}). All information must be current as of {current_year}. Do NOT use outdated information from 2024 or earlier years.

Write a comprehensive blog post about: {keyword}{refs_section}

Category: {category}

⏱️ Reading Time Target: 4-5 minutes
- Write 3-4 main sections (## headings)
- Each section: 1-2 minutes to read, one key point
- Short paragraphs (2-4 sentences each)
- End with a thought-provoking question

🎯 HOOKING STRATEGY (Critical!):
1. **Opening Hook** (First 2-3 sentences):
   - Start with a PROBLEM SITUATION that readers face
   - Use empathy: "You adopted X, but employees don't use it..."
   - Include specific failure stat: "60% of X projects fail because..."
   - NOT generic intro like "X is becoming popular..."

2. **Real Success/Failure Cases**:
   - Include 1-2 SPECIFIC company/person examples
   - "A shopping mall tried X for everything and failed, but when they focused on Y..."
   - Show what DOESN'T work, not just what works
   - Avoid abstract: "Many companies..." → Use: "One e-commerce startup..."

3. **Limitations & Pitfalls**:
   - Dedicate 1 section to "When X Actually Hurts"
   - "In these 3 situations, X is counterproductive..."
   - This makes content feel authentic and trustworthy

4. **Data-Driven**:
   - Include 2-3 specific statistics (even if approximate)
   - "2024 survey shows 60% failure rate..."
   - "Companies saw 35% productivity increase..."

Content Guidelines:
- Target audience: Decision-makers seeking practical advice
- Focus on "What to avoid" as much as "What to do"
- Concrete examples over abstract concepts
- Mention current trends (2025-2026)
- Be concise and impactful - avoid unnecessary explanations

📚 REFERENCES SECTION:
- If references were provided above in the prompt, you MUST add a "## References" section at the end
- Use those EXACT URLs - do not modify or create new ones
- Format: `- [Source Title](URL) - Organization/Publisher`
- Example:
  ## References
  - [The State of AI in 2025](https://example.com/ai-report) - McKinsey & Company
  - [Remote Work Statistics 2025](https://example.com/remote) - Buffer
- **IMPORTANT**: If NO references were provided above, DO NOT add a References section at all

**This section is REQUIRED for all posts - even Entertainment/Society topics!**

Write the complete blog post now (body only, no title or metadata):""",

            "ko": f"""📅 오늘 날짜: {current_date}
⚠️ 중요: 이 글은 오늘({current_date}) 기준으로 작성합니다. 모든 정보는 {current_year}년 현재를 기준으로 해야 합니다. 2024년 이하의 오래된 정보를 사용하지 마세요.

다음 주제로 포괄적인 블로그 글을 작성하세요: {keyword}{refs_section}

카테고리: {category}

⏱️ 읽기 시간 목표: 4-5분
- 3-4개의 주요 섹션 (## 헤딩) 작성
- 각 섹션: 1-2분 읽기 분량, 하나의 핵심 포인트
- 짧은 문단 사용 (2-4 문장씩)
- 생각을 자극하는 질문으로 마무리

🎯 후킹 전략 (필수!):
1. **오프닝 후킹** (첫 2-3문장):
   - 독자가 직면한 문제 상황으로 시작
   - 공감 유도: "회사에서 X를 도입했는데 직원들이 쓰지 않고..."
   - 구체적 실패 통계 포함: "X 프로젝트의 60%가 실패하는 이유는..."
   - 일반적 시작 금지: "X가 인기를 끌고 있습니다..." ❌

2. **실제 성공/실패 사례**:
   - 구체적인 회사/사람 사례 1-2개 포함
   - "한 쇼핑몰은 X를 모든 것에 적용했다가 실패했지만, Y에만 집중하니까..."
   - 안 되는 것도 보여주기 (성공만 말하지 말기)
   - 추상적 표현 금지: "많은 기업들..." → "한 스타트업은..." ✅

3. **한계점과 함정**:
   - "X가 오히려 역효과인 경우" 섹션 1개 할애
   - "이 3가지 상황에서는 X가 비효율적..."
   - 이것이 진정성과 신뢰를 만듦

4. **데이터 기반**:
   - 구체적 통계 2-3개 포함 (대략적이어도 OK)
   - "2024년 조사에 따르면 60% 실패율..."
   - "기업들이 35% 생산성 증가 경험..."

콘텐츠 가이드라인:
- 대상 독자: 실용적 조언을 찾는 의사결정자
- "피해야 할 것"을 "해야 할 것"만큼 강조
- 추상적 개념보다 구체적 예시
- 현재 트렌드 언급 (2025-2026년)
- 간결하고 임팩트 있게 - 불필요한 설명 제거

📚 참고자료 섹션:
- 위 프롬프트에 참고자료가 제공된 경우, 반드시 글 마지막에 "## 참고자료" 섹션 추가
- 제공된 URL을 정확히 사용 - 수정하거나 새로 만들지 말 것
- 형식: `- [출처 제목](URL) - 조직/출판사`
- 예시:
  ## 참고자료
  - [2025 AI 현황 보고서](https://example.com/ai-report) - 맥킨지앤컴퍼니
  - [원격 근무 통계 2025](https://example.com/remote) - Buffer
- **중요**: 위에 참고자료가 제공되지 않았다면, 참고자료 섹션을 절대 추가하지 마세요

지금 바로 완전한 블로그 글을 작성하세요 (본문만, 제목이나 메타데이터 제외):"""
        }

        return prompts[lang]

    def _get_editor_prompt(self, lang: str, content_type: str = 'analysis') -> str:
        """Get editor prompt based on language and content type

        Args:
            lang: Language code (en/ko)
            content_type: Content type (tutorial/analysis/news)

        Returns:
            str: Editor prompt with type-specific length targets
        """
        # Get type-specific word count targets
        classifier = ContentClassifier()
        config = classifier.get_config(content_type, lang)
        min_count, max_count = config['word_count']

        # Format length requirements based on language
        if lang == 'ko':
            count_unit = '글자'
            length_req = f"""📏 길이 요구사항 (CRITICAL - 반드시 준수):
🎯 목표 범위: {min_count:,}-{max_count:,}{count_unit}

**절대 규칙**:
- 초안이 {int(min_count*0.8):,}{count_unit} 미만: 예시/설명 추가로 최소 {min_count:,}{count_unit} 이상 확장
- 초안이 {min_count:,}-{max_count:,}{count_unit}: 길이 절대 유지 (이상적 범위 - 압축 금지!)
- 초안이 {int(max_count*1.3):,}{count_unit} 이상: 중복만 제거하여 {max_count:,}{count_unit} 근처로 조정

⚠️  경고: 이상적 범위({min_count:,}-{max_count:,}{count_unit})에 있으면 절대 줄이지 마세요!"""
        else:
            length_req = f"""📏 Length Requirements (CRITICAL - Must Follow):
🎯 Target Range: {min_count:,}-{max_count:,} words

**Absolute Rules**:
- If draft is under {int(min_count*0.8):,} words: EXPAND with examples/explanations to reach at least {min_count:,} words
- If draft is {min_count:,}-{max_count:,} words: MAINTAIN exact length (ideal range - DO NOT compress!)
- If draft is over {int(max_count*1.3):,} words: Remove only redundancy to reach near {max_count:,} words

⚠️  Warning: If draft is in ideal range ({min_count:,}-{max_count:,} words), DO NOT shorten it!"""

        prompts = {
            "en": f"""You are an expert editor. Transform this into Medium-style content with authentic human touch:

{length_req}

🎯 CRITICAL ENHANCEMENTS:
1. **Strengthen Opening Hook**:
   - If opening is generic, rewrite to start with problem/pain point
   - Add empathy: "You've been there, right?"
   - Make it personal and relatable

2. **Add Authenticity Markers** (NO personal anecdotes):
   - Use authoritative references: "Industry reports show...", "According to recent data..."
   - Add failure acknowledgment: "This approach can fail when..."
   - Show balanced perspective: "This isn't always the answer..."
   - AVOID: "In my experience...", "I spoke with...", "I thought..." (credibility issues on anonymous blogs)

3. **Enhance Examples**:
   - Make vague examples specific: "Many companies" → "One fintech startup" or "A Silicon Valley tech company"
   - Add concrete details: numbers, outcomes, timelines
   - Include what went WRONG, not just success stories
   - AVOID: "I worked with", "I spoke to" → Use: "Case studies show", "Reports indicate"

4. **Balance Perspective**:
   - Ensure there's a "When this doesn't work" section
   - Add nuance: "This works IF...", "But in these cases..."
   - Avoid absolute claims: "always", "never", "guaranteed"

Tasks:
1. **Medium style conversion**: Add "you/I", conversational tone
2. **Eliminate all AI tells**: "certainly", "moreover", "it's important to note"
3. **Natural connectors**: "Look", "Here's why", "The truth is"
4. **Break fourth wall**: "You might be thinking...", "Sound familiar?"
5. **Punchy sentences**: "Here's the thing.", "Let me explain.", "Stop it."
6. **Smooth transitions**: "Now", "Here's where it gets interesting"
7. Keep all factual information intact
8. **Complete ending**: Finish conclusion fully
9. **Preserve Key Takeaways block**: Do not remove or restructure the blockquote Key Takeaways. Improve wording only.

Return improved version (body only, no title):""",

            "ko": f"""당신은 전문 에디터입니다. 이 블로그 글을 진짜 사람이 쓴 것 같은 토스 스타일로 개선하세요:

{length_req}

🎯 핵심 개선사항:
1. **오프닝 강화**:
   - 일반적 시작이면 문제/고민 상황으로 재작성
   - 공감 추가: "이런 경험 있으시죠?"
   - 개인적이고 공감 가능하게

2. **정보 밀도 최우선** (한국 독자 = 빠른 정보 선호):
   - 핵심 정보 먼저: 수치, 단계, 방법
   - 실용 정보 즉시 제공: "계산법: 1) ~ 2) ~"
   - "의외로...", "놀랍게도..." 같은 자연스러운 표현
   - 한계 언급: "항상 답은 아니에요..."

3. **예시 구체화** (개인 경험 배제):
   - 추상적 예시를 구체적으로: "많은 회사들" → "한 핀테크 스타트업은" 또는 "토스의 경우"
   - 구체적 디테일: 숫자, 결과, 타임라인
   - 실패한 것도 포함: 성공만 말하지 말기
   - 피할 것: "제 경험상", "제가 봤을 때" → 대신: "사례 연구에 따르면", "데이터는 보여줍니다"

4. **균형잡힌 관점**:
   - "이런 경우엔 안 통해요" 섹션 확인/추가
   - 뉘앙스: "이게 통하려면...", "하지만 이런 경우엔..."
   - 절대적 표현 피하기: "항상", "절대", "무조건"

작업:
1. **토스 말투로 변환**: "~습니다" → "~해요", 친근한 질문형 추가
2. AI 느낌 완전 제거: "물론", "~할 수 있습니다", "중요합니다" 모두 삭제
3. 자연스러운 접속사: "사실", "실제로", "그런데", "참고로"
4. 숫자를 친근하게: "50% → 절반", "3배 → 세 배"
5. 짧고 강렬한 문장 추가: "놀랍죠?", "맞아요.", "이게 핵심이에요."
6. 섹션 간 매끄러운 전환: "자, 이제 ~", "그럼 ~"
7. 모든 사실 정보는 그대로 유지
8. **마지막 문장까지 완결**: 결론을 반드시 완성
9. **핵심 요약 블록 유지**: Key Takeaways 블록을 제거하거나 구조 변경하지 말 것. 문구만 개선.

개선된 버전을 반환하세요 (본문만, 제목 제외):"""
        }

        return prompts[lang]

    def generate_title(self, content: str, keyword: str, lang: str, references: List[Dict] = None) -> str:
        """Generate SEO-friendly title based on actual content and references"""
        # Get current year in KST
        from datetime import datetime, timezone, timedelta
        kst = timezone(timedelta(hours=9))
        current_year = datetime.now(kst).year

        # Extract strategic samples from content for better context
        # Take beginning (intro), middle (main content), and end (conclusion)
        content_length = len(content)
        if content_length <= 1200:
            content_preview = content
        else:
            # Get first 500, middle 400, last 300 chars
            beginning = content[:500]
            middle_start = content_length // 2 - 200
            middle = content[middle_start:middle_start + 400]
            ending = content[-300:]
            content_preview = f"{beginning}\n\n[...middle section...]\n{middle}\n\n[...conclusion...]\n{ending}"

        # Format references if available
        refs_context = ""
        if references and len(references) > 0:
            refs_list = "\n".join([
                f"- {ref.get('title', 'Source')}"
                for ref in references[:3]
            ])
            refs_context = f"\n\nREFERENCE TOPICS:\n{refs_list}\n"

        prompts = {
            "en": f"Generate a factual, SEO-friendly blog title (50-60 chars) for this post about '{keyword}'.\n\nCONTENT SAMPLES (beginning, middle, end):\n{content_preview}{refs_context}\n\nCRITICAL RULES - VIOLATION WILL FAIL:\n1. Title MUST describe what the content ACTUALLY discusses (not what sounds catchy)\n2. NO exaggeration, speculation, or clickbait (e.g., \"confirmed\", \"revealed\", \"secret\")\n3. If content is about \"how to watch\", title must say \"how to watch\" (not \"rankings\")\n4. If content discusses problems/issues, title must reflect that (not promise solutions)\n5. ONLY use facts explicitly stated in the content samples\n6. Do NOT promise specific numbers/data unless clearly stated in content\n7. Include keyword '{keyword}' naturally\n8. Current year is {current_year}\n9. Return ONLY the title",
            "ko": f"'{keyword}'에 대한 사실적이고 SEO 친화적인 제목을 생성하세요 (50-60자).\n\n본문 샘플 (시작, 중간, 끝):\n{content_preview}{refs_context}\n\n핵심 규칙 - 위반 시 실패:\n1. 제목은 본문이 실제로 다루는 내용을 설명해야 함 (매력적으로 들리는 것이 아님)\n2. 과장, 추측, 클릭베이트 금지 (예: \"확정\", \"폭로\", \"충격\")\n3. 본문이 \"시청 방법\"에 대한 것이면 제목도 \"시청 방법\"이어야 함 (\"랭킹\" 아님)\n4. 본문이 문제점을 논의하면 제목도 그것을 반영해야 함 (해결책 약속 금지)\n5. 본문 샘플에 명시적으로 언급된 사실만 사용\n6. 본문에 명확히 나와있지 않으면 구체적 숫자/데이터 약속 금지\n7. '{keyword}' 키워드를 자연스럽게 포함\n8. 현재 연도는 {current_year}년\n9. 제목만 반환"
        }

        response = self.client.messages.create(
            model=self.model,
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": prompts[lang]
            }]
        )

        generated_title = response.content[0].text.strip().strip('"').strip("'")

        # Validate title-content alignment (STRICT check for critical mismatches only)
        validation_prompts = {
            "en": f"Does this title accurately match what the content ACTUALLY discusses?\n\nTITLE: {generated_title}\n\nCONTENT: {content_preview}\n\nCheck for CRITICAL mismatches ONLY:\n- Title promises specific data (e.g., \"$800\", \"75%\") but content doesn't provide it\n- Title says \"how to watch\" but content discusses problems/history instead\n- Title says \"confirmed\" but content is speculation/rumors\n- Title topic completely different from content topic\n\nIGNORE minor issues like:\n- Year mentions (2026 is acceptable for future-looking content)\n- Slight emphasis differences\n- Language mixing (Korean keyword in English title is OK)\n\nAnswer 'yes' if title reasonably matches content. Answer 'no' ONLY for critical mismatches. If no, explain in max 15 words.",
            "ko": f"이 제목이 본문이 실제로 논의하는 내용과 정확히 일치합니까?\n\n제목: {generated_title}\n\n본문: {content_preview}\n\n치명적 불일치만 확인:\n- 제목이 구체적 데이터(예: \"75%\", \"$800\")를 약속하지만 본문에 없음\n- 제목은 \"시청 방법\"인데 본문은 문제점/역사를 논의\n- 제목은 \"확정\"인데 본문은 추측/소문\n- 제목 주제와 본문 주제가 완전히 다름\n\n무시할 사소한 문제:\n- 연도 언급 (미래 지향적 콘텐츠에 2026 사용 가능)\n- 약간의 강조 차이\n- 언어 혼용 (영어 제목에 한국어 키워드 사용 가능)\n\n제목이 본문과 합리적으로 일치하면 '예'. 치명적 불일치만 '아니오'. 아니오라면 15단어 이내 설명."
        }

        validation_response = self.client.messages.create(
            model=self.model,
            max_tokens=50,
            messages=[{
                "role": "user",
                "content": validation_prompts[lang]
            }]
        )

        validation_result = validation_response.content[0].text.strip().lower()

        # If validation fails, regenerate title with strict instructions
        if not validation_result.startswith('yes') and not validation_result.startswith('예'):
            safe_print(f"  ⚠️  Title-content mismatch detected: {validation_result}")
            safe_print(f"     Original title: {generated_title}")
            safe_print(f"  🔄 Regenerating title with strict content alignment...")

            # Regenerate with stricter prompt
            regenerate_prompts = {
                "en": f"Generate a title that EXACTLY matches what this content discusses. Do NOT promise specifics that aren't in the content. Do NOT use words like 'confirmed', 'breaking', or future dates unless explicitly stated.\n\nContent preview:\n{content_preview}\n\nKeyword to include: {keyword}\n\nTitle (60-70 chars):",
                "ko": f"본문이 실제로 다루는 내용과 정확히 일치하는 제목을 생성하세요. 본문에 없는 구체적 내용을 약속하지 마세요. '확정', '속보', 미래 날짜는 본문에 명시되지 않으면 사용하지 마세요.\n\n본문 미리보기:\n{content_preview}\n\n포함할 키워드: {keyword}\n\n제목 (40-50자):"
            }

            regenerate_response = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                messages=[{
                    "role": "user",
                    "content": regenerate_prompts[lang]
                }]
            )

            generated_title = regenerate_response.content[0].text.strip().strip('"').strip("'")
            safe_print(f"  ✓ Regenerated title: {generated_title}")

        return generated_title

    def generate_description(self, content: str, keyword: str, lang: str) -> str:
        """Generate meta description optimized for SEO (120-160 chars)"""
        prompts = {
            "en": f"Generate a compelling meta description for a blog post about '{keyword}'.\n\nREQUIREMENTS:\n- Length: EXACTLY 120-160 characters (strict)\n- Include keyword naturally\n- Action-oriented and engaging\n- NO quotes, NO marketing fluff\n\nReturn ONLY the description, nothing else.",
            "ko": f"'{keyword}'에 대한 블로그 글의 메타 설명을 생성하세요.\n\n요구사항:\n- 길이: 정확히 120-160자 (엄격)\n- 키워드 자연스럽게 포함\n- 행동 지향적이고 매력적으로\n- 따옴표 없이, 마케팅 문구 금지\n\n설명만 반환하세요."
        }

        response = self.client.messages.create(
            model=self.model,
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": prompts[lang]
            }]
        )

        return response.content[0].text.strip().strip('"').strip("'")

    def generate_faq(self, content: str, keyword: str, lang: str) -> list:
        """Generate 3-5 FAQ pairs based on article content for FAQPage schema"""
        prompts = {
            "en": f"""Based on this blog post about '{keyword}', generate 3-5 FAQ pairs that someone might search for.

RULES:
- Questions must be natural search queries (how people actually type in Google)
- Answers must be 2-3 sentences, factual, directly answering the question
- Include the keyword '{keyword}' naturally in at least 2 questions
- Each answer should be self-contained (understandable without reading the article)

Return ONLY a JSON array:
[
  {{"question": "...", "answer": "..."}},
  {{"question": "...", "answer": "..."}}
]

Article content:
{content[:3000]}""",
            "ko": f"""이 '{keyword}' 블로그 글을 기반으로 3-5개 FAQ 쌍을 생성하세요.

규칙:
- 질문은 자연스러운 검색 쿼리여야 함 (실제 구글에 타이핑하는 형태)
- 답변은 2-3문장, 사실적, 질문에 직접 답변
- 최소 2개 질문에 '{keyword}' 키워드 자연스럽게 포함
- 각 답변은 독립적으로 이해 가능해야 함

JSON 배열만 반환:
[
  {{"question": "...", "answer": "..."}},
  {{"question": "...", "answer": "..."}}
]

글 내용:
{content[:3000]}"""
        }

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompts[lang]}]
        )

        text = response.content[0].text
        json_match = re.search(r'\[[\s\S]*\]', text)
        if json_match:
            faq_items = json.loads(json_match.group())
            return faq_items[:5]
        return []

    def extract_technologies(self, content: str, keyword: str) -> list:
        """Extract technology names mentioned in content for taxonomy"""
        known_techs = [
            'Python', 'JavaScript', 'TypeScript', 'React', 'Next.js', 'Vue.js',
            'Angular', 'Node.js', 'Django', 'FastAPI', 'Flask', 'Docker',
            'Kubernetes', 'AWS', 'Azure', 'GCP', 'PostgreSQL', 'MongoDB',
            'Redis', 'GraphQL', 'REST API', 'Claude', 'GPT', 'OpenAI',
            'Anthropic', 'LangChain', 'Vercel', 'Terraform', 'GitHub Actions',
            'Linux', 'Rust', 'Go', 'Swift', 'Kotlin', 'Java', 'C++',
            'WebAssembly', 'Cloudflare', 'Figma', 'Tailwind CSS', 'Hugo',
            'Webpack', 'Vite', 'Supabase', 'Firebase', 'Stripe', 'Notion',
            'Slack', 'VS Code', 'ChatGPT', 'Gemini', 'Copilot', 'Cursor',
            'TensorFlow', 'PyTorch', 'Stable Diffusion', 'Midjourney',
            'Ollama', 'Hugging Face', 'Mistral', 'Llama', 'DALL-E', 'Sora'
        ]

        found = []
        content_lower = content.lower()
        for tech in known_techs:
            if tech.lower() in content_lower:
                found.append(tech)

        return found[:5]

    def translate_to_english(self, text: str) -> str:
        """Translate non-English keywords to English for Unsplash search"""
        # Simple keyword translations for common tech/business/lifestyle terms
        translations = {
            # Korean
            '챗봇': 'chatbot', 'AI': 'artificial intelligence', '도입': 'implementation',
            '실패': 'failure', '이유': 'reasons', '노코드': 'no-code', '툴': 'tool',
            '한계점': 'limitations', '재택근무': 'remote work', '하이브리드': 'hybrid',
            '근무': 'work', '효율성': 'efficiency', 'MZ세대': 'gen z', '관리': 'management',
            '방법': 'method', '사례': 'case', '미니멀': 'minimal', '라이프': 'lifestyle',
            '중단': 'quit', '생산성': 'productivity', '팁': 'tips',
        }

        # Split and translate each word
        words = text.split()
        translated_words = []
        for word in words:
            # Try exact match first
            if word in translations:
                translated_words.append(translations[word])
            else:
                # Check if word contains any translatable substring
                found = False
                for kr, en in translations.items():
                    if kr in word:
                        translated_words.append(en)
                        found = True
                        break
                if not found:
                    # Keep as-is if ASCII (likely already English)
                    try:
                        word.encode('ascii')
                        translated_words.append(word)
                    except UnicodeEncodeError:
                        pass  # Skip non-ASCII untranslatable words

        return ' '.join(translated_words) if translated_words else 'technology'

    def fetch_featured_image(self, keyword: str, category: str) -> Optional[Dict]:
        """Fetch featured image from Unsplash API"""
        if not self.unsplash_key:
            return None

        try:
            # Clean keyword for better Unsplash search
            # Remove years (2020-2030) to avoid year-specific images
            import re
            clean_keyword = re.sub(r'20[2-3][0-9]년?', '', keyword)  # Match years + optional 년 (Korean year)
            # Remove common prefixes/suffixes that reduce search quality
            clean_keyword = re.sub(r'【.*?】', '', clean_keyword)  # Remove 【brackets】
            clean_keyword = re.sub(r'\[.*?\]', '', clean_keyword)  # Remove [brackets]
            clean_keyword = clean_keyword.strip()

            # Translation dictionary for meaningful keywords
            keyword_translations = {
                # Korean - AI/Jobs/Employment
                'AI': 'artificial intelligence',
                '인공지능': 'artificial intelligence',
                '대체': 'replacement automation',
                '일자리': 'job employment work',
                '실업': 'unemployment jobless',
                '직업': 'occupation career profession',
                '취업': 'employment hiring recruitment',
                '자동화': 'automation robot',
                '기술': 'technology tech',
                '디지털': 'digital technology',
                '로봇': 'robot automation',
                '미래': 'future',
                '변화': 'change transformation',
                '위험': 'risk danger',
                # Korean - Finance/Business
                '나라사랑카드': 'patriot card credit card',
                '카드': 'card credit',
                '연령': 'age limit',
                '제한': 'restriction limit',
                '전세': 'housing lease deposit',
                '보증금': 'deposit guarantee',
                '배달': 'delivery food',
                '수수료': 'fee commission',
                '자영업': 'small business owner',
                '폐업': 'business closure bankruptcy',
                '지원금': 'subsidy support fund',
                '정부': 'government policy',
                '신청': 'application registration',
                '혜택': 'benefit advantage',
                # Korean - Entertainment/Society
                '사과문': 'apology statement',
                '팬': 'fan supporter',
                '등돌림': 'backlash criticism',
                '스마트폰': 'smartphone mobile',
                '건강': 'health wellness'
            }

            # Extract meaningful keywords from title
            title_words = clean_keyword.split()
            translated_keywords = []

            # Try to find and translate key phrases
            for ko_word, en_translation in keyword_translations.items():
                if ko_word in clean_keyword:
                    translated_keywords.append(en_translation)

            # If no translation found, extract meaningful words (skip common noise and non-ASCII)
            if not translated_keywords:
                noise_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for']
                for word in title_words[:3]:  # Take first 3 words
                    # Filter out non-ASCII words to prevent non-English queries
                    try:
                        word.encode('ascii')
                        is_ascii = True
                    except UnicodeEncodeError:
                        is_ascii = False

                    if is_ascii and len(word) > 2 and word.lower() not in noise_words:
                        translated_keywords.append(word)

            # Add category context (more specific than before)
            category_context = {
                'tech': ['technology', 'digital innovation', 'tech workspace', 'coding', 'software'],
                'business': ['business', 'professional office', 'meeting', 'strategy', 'corporate'],
                'finance': ['finance', 'money investment', 'stock market', 'banking', 'wealth'],
                'society': ['society', 'community people', 'social gathering', 'urban life', 'culture'],
                'entertainment': ['entertainment', 'cinema theater', 'music concert', 'art gallery', 'performance'],
                'lifestyle': ['lifestyle', 'daily life', 'home interior', 'wellness', 'travel'],
                'sports': ['sports', 'athletic training', 'stadium', 'competition', 'fitness'],
                'education': ['education', 'learning classroom', 'study', 'books', 'school']
            }

            # Build flexible, contextual query with fallback strategies
            if translated_keywords:
                base_keywords = ' '.join(translated_keywords[:2])
                # Primary search: specific keywords + main category term
                context_list = category_context.get(category, ['technology'])
                context = context_list[0]
                query = f"{base_keywords} {context}".strip()
                # Store fallback queries
                fallback_queries = [f"{base_keywords} {ctx}" for ctx in context_list[1:3]]
                fallback_queries.append(context_list[0])  # Pure category as last resort
            else:
                # Fallback to category-specific queries if no English keywords found
                context_list = category_context.get(category, ['technology'])
                query = context_list[0]
                fallback_queries = context_list[1:3]

            # Unsplash API endpoint
            url = "https://api.unsplash.com/search/photos"
            headers = {
                "Authorization": f"Client-ID {self.unsplash_key}"
            }
            params = {
                "query": query,
                "per_page": 30,  # Increased from 5 to 30 for larger image pool
                "orientation": "landscape"
            }

            safe_print(f"  🔍 Searching Unsplash for: {query}")

            # Use certifi for SSL verification (Windows compatibility)
            verify_ssl = certifi.where() if certifi else True
            response = requests.get(url, headers=headers, params=params, timeout=10, verify=verify_ssl)
            response.raise_for_status()

            data = response.json()

            # Load used images tracking file
            used_images_file = Path(__file__).parent.parent / "data" / "used_images.json"
            used_images_meta_file = Path(__file__).parent.parent / "data" / "used_images_metadata.json"

            # Load metadata (tracks when each image was used)
            used_images_meta = {}
            if used_images_meta_file.exists():
                try:
                    with open(used_images_meta_file, 'r') as f:
                        used_images_meta = json.load(f)
                except:
                    pass

            # Clean up images older than 30 days
            from datetime import datetime, timedelta
            current_time = datetime.now().timestamp()
            cutoff_time = (datetime.now() - timedelta(days=30)).timestamp()

            cleaned_meta = {}
            for img_id, timestamp in used_images_meta.items():
                # Skip corrupted entries (non-numeric timestamps)
                if not isinstance(timestamp, (int, float)):
                    continue
                if timestamp > cutoff_time:
                    cleaned_meta[img_id] = timestamp

            # Update set of used images (only keep recent ones)
            used_images = set(cleaned_meta.keys())

            # Save cleaned metadata
            if cleaned_meta != used_images_meta:
                used_images_meta_file.parent.mkdir(parents=True, exist_ok=True)
                with open(used_images_meta_file, 'w') as f:
                    json.dump(cleaned_meta, f, indent=2)
                if len(used_images_meta) > len(cleaned_meta):
                    safe_print(f"  🗑️  Cleaned up {len(used_images_meta) - len(cleaned_meta)} images older than 30 days")

            used_images_meta = cleaned_meta

            # Find first unused image from results
            photo = None
            if data.get('results'):
                for result in data['results']:
                    image_id = result['id']
                    if image_id not in used_images:
                        photo = result
                        used_images.add(image_id)
                        used_images_meta[image_id] = current_time
                        break
            else:
                safe_print(f"  ⚠️  No images found for '{query}'")

            # If no results or all images are used, try fallback queries
            if photo is None and fallback_queries:
                for fallback_query in fallback_queries:
                    safe_print(f"  ⚠️  No unused images for '{query}', trying: {fallback_query}")
                    params['query'] = fallback_query

                    response = requests.get(url, headers=headers, params=params, timeout=10, verify=verify_ssl)
                    response.raise_for_status()
                    data = response.json()

                    if data.get('results'):
                        for result in data['results']:
                            image_id = result['id']
                            if image_id not in used_images:
                                photo = result
                                used_images.add(image_id)
                                used_images_meta[image_id] = current_time
                                safe_print(f"  ✓ Found unused image with fallback: {fallback_query}")
                                break

                    # If found, stop trying fallbacks
                    if photo is not None:
                        break

                # If still no unused image found, return None (use placeholder)
                if photo is None:
                    safe_print(f"  ❌ No unused images available after trying all fallbacks for category '{category}'")
                    return None

            # Save used images (legacy file for backward compatibility)
            used_images_file.parent.mkdir(parents=True, exist_ok=True)
            with open(used_images_file, 'w') as f:
                json.dump(list(used_images), f)

            # Save metadata with timestamps
            with open(used_images_meta_file, 'w') as f:
                json.dump(used_images_meta, f, indent=2)

            image_info = {
                'url': photo['urls']['regular'],
                'download_url': photo['links']['download_location'],
                'photographer': photo['user']['name'],
                'photographer_url': photo['user']['links']['html'],
                'unsplash_url': photo['links']['html'],
                'image_id': photo['id']
            }

            safe_print(f"  ✓ Found image by {image_info['photographer']}")
            return image_info

        except requests.exceptions.Timeout as e:
            safe_print(f"  ⚠️  Unsplash API timeout: Request took too long")
            safe_print(f"     Keyword: {keyword}")
            safe_print(f"     Error: {mask_secrets(str(e))}")
            return None
        except requests.exceptions.HTTPError as e:
            safe_print(f"  ⚠️  Unsplash API HTTP error: {e.response.status_code if e.response else 'unknown'}")
            safe_print(f"     Keyword: {keyword}")
            safe_print(f"     Error: {mask_secrets(str(e))}")
            return None
        except requests.exceptions.RequestException as e:
            safe_print(f"  ⚠️  Unsplash API network error")
            safe_print(f"     Keyword: {keyword}")
            safe_print(f"     Error: {mask_secrets(str(e))}")
            return None
        except json.JSONDecodeError as e:
            safe_print(f"  ⚠️  Unsplash API response parsing failed")
            safe_print(f"     Keyword: {keyword}")
            safe_print(f"     Error: Invalid JSON response")
            return None
        except Exception as e:
            safe_print(f"  ⚠️  Image fetch failed with unexpected error")
            safe_print(f"     Keyword: {keyword}")
            safe_print(f"     Error: {mask_secrets(str(e))}")
            return None

    def download_image(self, image_info: Dict, keyword: str) -> Optional[str]:
        """Download optimized image to static/images/ directory with hash-based duplicate detection"""
        if not image_info:
            return None

        try:
            # Create images directory
            images_dir = Path("static/images")
            images_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename
            slug = keyword.lower()
            # Allow Unicode characters (CJK) in filenames
            slug = ''.join(c if c.isalnum() or c.isspace() or ord(c) > 127 else '' for c in slug)
            slug = slug.replace(' ', '-')[:30]
            # Use KST for image filename
            from datetime import timezone, timedelta
            kst = timezone(timedelta(hours=9))
            date_str = datetime.now(kst).strftime("%Y%m%d")
            filename = f"{date_str}-{slug}.jpg"
            filepath = images_dir / filename

            # Trigger Unsplash download tracking (required by API terms)
            if image_info.get('download_url'):
                verify_ssl = certifi.where() if certifi else True
                requests.get(
                    image_info['download_url'],
                    headers={"Authorization": f"Client-ID {self.unsplash_key}"},
                    timeout=5,
                    verify=verify_ssl
                )

            # Download optimized image (1200px width, quality 85)
            # Use Unsplash's regular URL which already includes optimization
            download_url = image_info.get('url', '')
            # Add additional optimization parameters
            if '?' in download_url:
                optimized_url = f"{download_url}&w=1200&q=85&fm=jpg"
            else:
                optimized_url = f"{download_url}?w=1200&q=85&fm=jpg"

            safe_print(f"  📥 Downloading optimized image (1200px, q85)...")
            # Use certifi for SSL verification (Windows compatibility)
            verify_ssl = certifi.where() if certifi else True
            response = requests.get(optimized_url, timeout=15, verify=verify_ssl)
            response.raise_for_status()

            # Calculate MD5 hash of downloaded content
            import hashlib
            content_hash = hashlib.md5(response.content).hexdigest()

            # Check for duplicate images by hash
            duplicate_found = False
            for existing_file in images_dir.glob("*.jpg"):
                if existing_file.exists():
                    try:
                        with open(existing_file, 'rb') as f:
                            existing_hash = hashlib.md5(f.read()).hexdigest()
                        if existing_hash == content_hash:
                            safe_print(f"  ⚠️  Duplicate image detected (same content as {existing_file.name})")
                            duplicate_found = True
                            break
                    except:
                        pass

            # If duplicate found, skip saving but still return the new filename
            # (The image will be saved with a new name to maintain unique URLs)
            if duplicate_found:
                safe_print(f"  ℹ️  Saving with new filename to maintain unique URL: {filename}")

            # Save image (even if duplicate, to maintain URL uniqueness per post)
            with open(filepath, 'wb') as f:
                f.write(response.content)

            size_kb = len(response.content) / 1024
            safe_print(f"  ✓ Image saved: {filepath} ({size_kb:.1f} KB)")

            # Log hash for debugging
            safe_print(f"  🔑 Image hash: {content_hash[:8]}...")

            # Return relative path for Hugo
            return f"/images/{filename}"

        except requests.exceptions.Timeout as e:
            safe_print(f"  ⚠️  Image download timeout")
            safe_print(f"     Keyword: {keyword}")
            safe_print(f"     URL: {optimized_url[:80]}...")
            return None
        except requests.exceptions.HTTPError as e:
            safe_print(f"  ⚠️  Image download HTTP error: {e.response.status_code if e.response else 'unknown'}")
            safe_print(f"     Keyword: {keyword}")
            return None
        except IOError as e:
            safe_print(f"  ⚠️  File system error during image save")
            safe_print(f"     Path: {filepath}")
            safe_print(f"     Error: {str(e)}")
            return None
        except Exception as e:
            safe_print(f"  ⚠️  Image download failed with unexpected error")
            safe_print(f"     Keyword: {keyword}")
            safe_print(f"     Error: {mask_secrets(str(e))}")
            return None

    def save_post(self, topic: Dict, title: str, description: str, content: str, image_path: Optional[str] = None, image_credit: Optional[Dict] = None, faq_items: Optional[list] = None, technologies: Optional[list] = None) -> Path:
        """Save post to Hugo content directory"""
        lang = topic['lang']
        category = topic['category']
        keyword = topic['keyword']

        # Generate filename from keyword
        slug = keyword.lower()
        # Remove special characters, keep alphanumeric and spaces
        slug = ''.join(c if c.isalnum() or c.isspace() else '' for c in slug)
        slug = slug.replace(' ', '-')[:50]

        # Create directory
        content_dir = Path(f"content/{lang}/{category}")
        content_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename with date in KST
        from datetime import timezone, timedelta
        kst = timezone(timedelta(hours=9))
        date_str = datetime.now(kst).strftime("%Y-%m-%d")
        filename = f"{date_str}-{slug}.md"
        filepath = content_dir / filename

        # A/B Testing Integration (50% chance)
        import random
        ab_test_id = None
        ab_variant = None

        if self.ab_test_manager.should_run_test("title_style"):
            # Generate post ID for consistent assignment
            post_id = f"{date_str}-{slug}"

            # Assign variant
            ab_variant = self.ab_test_manager.assign_variant(post_id, "title_style")

            if ab_variant:
                ab_test_id = "title_style"

                # Generate title variants
                title_variants = self.ab_test_manager.generate_title_variants(title, lang)

                # Apply variant title
                if ab_variant in title_variants:
                    original_title = title
                    title = title_variants[ab_variant]
                    safe_print(f"  🧪 A/B Test: title_style (Variant {ab_variant})")
                    safe_print(f"     Original: {original_title}")
                    safe_print(f"     Modified: {title}")

        # Hugo frontmatter with required image field
        # Use placeholder if no Unsplash image available
        if not image_path:
            # Use category-based placeholder
            image_path = f"/images/placeholder-{category}.jpg"

        # Use KST timezone for date
        from datetime import timezone, timedelta
        kst = timezone(timedelta(hours=9))
        now_kst = datetime.now(kst)

        # Escape nested quotes in YAML frontmatter
        safe_title = title.replace('"', "'")
        safe_description = description.replace('"', "'")

        # Build frontmatter with optional A/B test metadata
        frontmatter_lines = [
            "---",
            f'title: "{safe_title}"',
            f'date: {now_kst.strftime("%Y-%m-%dT%H:%M:%S%z")}',
            "draft: false",
            'author: "Jake Park"',
            f'categories: ["{category}"]',
            f'tags: {json.dumps(keyword.split()[:3])}',
            f'description: "{safe_description}"',
            f'image: "{image_path}"'
        ]

        # Add A/B test metadata if applicable
        if ab_test_id and ab_variant:
            frontmatter_lines.append(f'ab_test_id: "{ab_test_id}"')
            frontmatter_lines.append(f'ab_variant: "{ab_variant}"')

        # Add technologies taxonomy for tech posts
        if technologies and category == 'tech':
            frontmatter_lines.append(f'technologies: {json.dumps(technologies)}')

        # Add FAQ items for FAQPage schema
        if faq_items:
            frontmatter_lines.append("faq:")
            for item in faq_items:
                safe_q = item.get('question', '').replace('"', "'")
                safe_a = item.get('answer', '').replace('"', "'")
                frontmatter_lines.append(f'  - question: "{safe_q}"')
                frontmatter_lines.append(f'    answer: "{safe_a}"')

        frontmatter_lines.extend(["---", ""])

        frontmatter = "\n".join(frontmatter_lines) + "\n"

        # Hero image removed - PaperMod theme renders frontmatter image: as cover
        hero_image = ""

        # Add image credit at the end of content if available
        credit_line = ""
        if image_credit:
            credit_line = f"\n\n---\n\n*Photo by [{image_credit['photographer']}]({image_credit['photographer_url']}) on [Unsplash]({image_credit['unsplash_url']})*\n"

        # Validate References section and remove if it contains fake URLs
        def has_fake_reference_url(url: str) -> bool:
            """Check if URL is a fake reference"""
            fake_patterns = [
                r'example\.com',
                r'example\.org',
                r'\.gov/[a-z-]+-202[0-9]',
                r'\.org/[a-z-]+-survey',
                r'\.gov/[a-z-]+-compliance',
                r'\.gov/[a-z-]+-report',
            ]
            for pattern in fake_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return True
            return False

        # Check if References section exists - if not, just skip it (don't add fake references)
        ref_headers = {
            'en': '## References',
            'ko': '## 참고자료'
        }
        ref_header = ref_headers.get(lang, '## References')

        # First, normalize any non-standard reference formats to standard format
        # Remove bold "**References:**" format if exists (common Claude output)
        bold_ref_patterns = [
            (r'\*\*References?:\*\*\n', ''),  # **References:**
            (r'\*\*참고자료:\*\*\n', '')  # **참고자료:**
        ]
        for pattern, replacement in bold_ref_patterns:
            content = re.sub(pattern, replacement, content)

        # Extract References section if exists
        has_references = ref_header in content or '## Reference' in content or '## 참고' in content

        if has_references:
            # Extract URLs from References section using regex
            # Pattern: [text](url) or bare URLs
            url_pattern = r'https?://[^\s\)\]<>"]+'  
            urls_in_content = re.findall(url_pattern, content)

            # Check if any URLs are fake
            fake_urls = [url for url in urls_in_content if has_fake_reference_url(url)]

            if fake_urls:
                safe_print(f"  ⚠️  Fake reference URLs detected: {len(fake_urls)} found")
                safe_print(f"      Examples: {fake_urls[:3]}")

                # Remove References section entirely
                # Match from any References header to the next ## header or end of content
                ref_pattern = r'\n## (?:References?|참고자료)\n.*?(?=\n## |\Z)'
                content = re.sub(ref_pattern, '', content, flags=re.DOTALL)
                safe_print(f"  🗑️  Removed References section with fake URLs")
                has_references = False  # Mark as no valid references
            else:
                safe_print(f"  ✅ References section validated ({len(urls_in_content)} URLs)")

        # If no valid References section exists, add from queue
        if not has_references and topic.get('references'):
            references = topic['references']
            safe_print(f"  ℹ️  No References section in content, adding from queue ({len(references)} refs)")

            # Build References section
            ref_section = f"\n\n{ref_header}\n\n"
            for i, ref in enumerate(references, 1):
                ref_section += f"{i}. [{ref['title']}]({ref['url']})\n"

            # Append to content
            content = content.rstrip() + ref_section
            safe_print(f"  ✅ Added {len(references)} references from queue")
        elif not has_references:
            safe_print(f"  ℹ️  No references available (neither in content nor queue)")

        # Add affiliate links if applicable
        affiliate_programs_used = []
        if should_add_affiliate_links(category):
            safe_print(f"  🔗 Checking for product mentions to add affiliate links...")

            # Detect products mentioned in content
            detected_products = detect_product_mentions(content, lang, category)

            if detected_products:
                safe_print(f"  📦 Detected {len(detected_products)} products: {', '.join(detected_products[:3])}")

                # Add affiliate link for the first detected product only (to avoid being too commercial)
                primary_product = detected_products[0]
                link_data = generate_affiliate_link(primary_product, lang)

                if link_data:
                    # Find insertion point: after first ## section
                    sections = content.split('\n## ')
                    if len(sections) > 1:
                        # Insert after first section
                        affiliate_box = create_affiliate_box(primary_product, lang, link_data)
                        sections[1] = sections[1] + '\n' + affiliate_box
                        content = '\n## '.join(sections)

                        affiliate_programs_used.append(link_data['program'])
                        safe_print(f"  ✅ Added affiliate link for '{primary_product}' ({link_data['program']})")
                    else:
                        safe_print(f"  ⚠️  Could not find insertion point for affiliate link")
                else:
                    safe_print(f"  ℹ️  No affiliate program configured for {lang}")
            else:
                safe_print(f"  ℹ️  No product mentions detected")
        else:
            safe_print(f"  ℹ️  Affiliate links disabled for category: {category}")

        # Add affiliate disclosure if links were added
        if affiliate_programs_used:
            disclosure = get_affiliate_disclosure(lang, affiliate_programs_used)
            content = content.rstrip() + disclosure
            safe_print(f"  ⚠️  Added affiliate disclosure")

        # Internal linking removed - Hugo template handles related posts automatically

        # Write file with hero image at top
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(frontmatter)
            f.write(hero_image)
            f.write(content)
            f.write(credit_line)

        safe_print(f"  💾 Saved to: {filepath}")
        return filepath


def main():
    parser = argparse.ArgumentParser(description="Generate blog posts")
    parser.add_argument("--count", type=int, default=3, help="Number of posts to generate")
    parser.add_argument("--topic-id", type=str, help="Specific topic ID to generate")
    args = parser.parse_args()

    # Pre-flight checks
    safe_print(f"\n{'='*60}")
    safe_print(f"  🔍 Pre-flight Environment Checks")
    safe_print(f"{'='*60}\n")

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    unsplash_key = os.environ.get("UNSPLASH_ACCESS_KEY")

    if anthropic_key:
        safe_print("  ✓ ANTHROPIC_API_KEY: Configured")
    else:
        safe_print("  ❌ ANTHROPIC_API_KEY: NOT FOUND")

    if unsplash_key:
        safe_print("  ✓ UNSPLASH_ACCESS_KEY: Configured")
    else:
        safe_print("  ⚠️  UNSPLASH_ACCESS_KEY: NOT FOUND")
        safe_print("     Posts will use placeholder images!")

    safe_print("")

    # Initialize generator
    try:
        generator = ContentGenerator()
    except ValueError as e:
        safe_print(f"Error: {str(e)}")
        safe_print("\nSet ANTHROPIC_API_KEY environment variable:")
        safe_print("  export ANTHROPIC_API_KEY='your-api-key'")
        sys.exit(1)

    # Get topics
    if args.topic_id:
        # Load specific topic (for testing)
        from topic_queue import get_queue
        queue = get_queue()
        data = queue._load_queue()
        topics = [t for t in data['topics'] if t['id'] == args.topic_id]
        if not topics:
            safe_print(f"Error: Topic {args.topic_id} not found")
            sys.exit(1)
    else:
        # Reserve topics from queue
        topics = reserve_topics(count=args.count)

    if not topics:
        safe_print("No topics available in queue")
        sys.exit(0)

    safe_print(f"\n{'='*60}")
    safe_print(f"  Generating {len(topics)} posts")
    safe_print(f"{'='*60}\n")

    generated_files = []

    for i, topic in enumerate(topics, 1):
        safe_print(f"[{i}/{len(topics)}] {topic['id']}")
        safe_print(f"  Keyword: {topic['keyword']}")
        safe_print(f"  Category: {topic['category']}")
        safe_print(f"  Language: {topic['lang']}")

        try:
            # Generate content
            safe_print(f"  → Step 1/7: Generating draft...")
            draft, content_type = generator.generate_draft(topic)

            safe_print(f"  → Step 2/7: Editing draft...")
            final_content = generator.edit_draft(draft, topic, content_type)

            # Generate metadata
            safe_print(f"  → Step 3/7: Generating metadata...")
            try:
                title = generator.generate_title(final_content, topic['keyword'], topic['lang'], topic.get('references'))
                description = generator.generate_description(final_content, topic['keyword'], topic['lang'])
            except Exception as e:
                safe_print(f"  ⚠️  WARNING: Metadata generation failed, using defaults")
                safe_print(f"     Error: {mask_secrets(str(e))}")
                title = topic['keyword']
                description = f"Article about {topic['keyword']}"

            # Fetch featured image
            safe_print(f"  → Step 4/7: Fetching image...")
            image_path = None
            image_credit = None
            try:
                image_info = generator.fetch_featured_image(topic['keyword'], topic['category'])
                if image_info:
                    image_path = generator.download_image(image_info, topic['keyword'])
                    if image_path:
                        image_credit = image_info
            except Exception as e:
                safe_print(f"  ⚠️  WARNING: Image fetch failed, will use placeholder")
                safe_print(f"     Error: {mask_secrets(str(e))}")

            # Generate FAQ for AEO
            faq_items = []
            try:
                safe_print(f"  → Step 5/7: Generating FAQ...")
                faq_items = generator.generate_faq(final_content, topic['keyword'], topic['lang'])
                safe_print(f"     FAQ: {len(faq_items)} items generated")
            except Exception as e:
                safe_print(f"  ⚠️  WARNING: FAQ generation failed: {mask_secrets(str(e))}")

            # Extract technologies for tech posts
            technologies = None
            if topic.get('category') == 'tech':
                try:
                    safe_print(f"  → Step 6/7: Extracting technologies...")
                    technologies = generator.extract_technologies(final_content, topic['keyword'])
                    if technologies:
                        safe_print(f"     Technologies: {', '.join(technologies)}")
                except Exception as e:
                    safe_print(f"  ⚠️  WARNING: Technology extraction failed: {mask_secrets(str(e))}")

            # Save post with image, FAQ, and technologies
            safe_print(f"  → Step 7/7: Saving post...")
            try:
                filepath = generator.save_post(topic, title, description, final_content, image_path, image_credit, faq_items, technologies)
            except IOError as e:
                safe_print(f"  ❌ ERROR: Failed to save post to filesystem")
                safe_print(f"     Error: {str(e)}")
                raise
            except Exception as e:
                safe_print(f"  ❌ ERROR: Unexpected error during save")
                safe_print(f"     Error: {mask_secrets(str(e))}")
                raise

            # Mark as completed
            if not args.topic_id:
                try:
                    mark_completed(topic['id'])
                except Exception as e:
                    safe_print(f"  ⚠️  WARNING: Failed to mark topic as completed in queue")
                    safe_print(f"     Topic ID: {topic['id']}")
                    safe_print(f"     Error: {str(e)}")
                    # Don't fail the whole process if queue update fails

            generated_files.append(str(filepath))
            safe_print(f"  ✅ Completed!\n")

        except KeyError as e:
            safe_print(f"  ❌ FAILED: Missing required field in topic data")
            safe_print(f"     Topic ID: {topic.get('id', 'unknown')}")
            safe_print(f"     Missing field: {str(e)}\n")
            if not args.topic_id:
                mark_failed(topic['id'], f"Missing field: {str(e)}")
        except ValueError as e:
            safe_print(f"  ❌ FAILED: Invalid data or API response")
            safe_print(f"     Topic ID: {topic.get('id', 'unknown')}")
            safe_print(f"     Error: {mask_secrets(str(e))}\n")
            if not args.topic_id:
                mark_failed(topic['id'], mask_secrets(str(e)))
        except Exception as e:
            safe_print(f"  ❌ FAILED: Unexpected error")
            safe_print(f"     Topic ID: {topic.get('id', 'unknown')}")
            safe_print(f"     Error type: {type(e).__name__}")
            safe_print(f"     Error: {mask_secrets(str(e))}\n")
            if not args.topic_id:
                mark_failed(topic['id'], mask_secrets(str(e)))

    # Save generated files list for quality gate
    output_file = Path("generated_files.json")
    with open(output_file, 'w') as f:
        json.dump(generated_files, f, indent=2)

    # Post-generation quality check
    safe_print(f"\n{'='*60}")
    safe_print(f"  📊 Post-Generation Quality Check")
    safe_print(f"{'='*60}\n")

    posts_without_references = 0
    posts_with_placeholders = 0

    for filepath in generated_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

                # Check for references section
                has_references = '## References' in content or '## 参考' in content or '## 참고자료' in content
                if not has_references:
                    posts_without_references += 1
                    safe_print(f"  ⚠️  No references: {Path(filepath).name}")

                # Check for placeholder images
                if 'placeholder-' in content:
                    posts_with_placeholders += 1
                    safe_print(f"  ⚠️  Placeholder image: {Path(filepath).name}")
        except Exception as e:
            safe_print(f"  ⚠️  Could not check: {Path(filepath).name}")

    safe_print("")

    if posts_without_references > 0:
        safe_print(f"🚨 WARNING: {posts_without_references}/{len(generated_files)} posts have NO references!")
        safe_print(f"   This reduces content credibility and SEO value.")
        safe_print(f"   FIX: Ensure Google Custom Search API is configured in keyword curation\n")

    if posts_with_placeholders > 0:
        safe_print(f"🚨 WARNING: {posts_with_placeholders}/{len(generated_files)} posts use PLACEHOLDER images!")
        safe_print(f"   This hurts user experience and engagement.")
        safe_print(f"   FIX: Ensure UNSPLASH_ACCESS_KEY is set in environment variables\n")

    if posts_without_references == 0 and posts_with_placeholders == 0:
        safe_print(f"✅ Quality Check PASSED: All posts have references and real images!\n")

    safe_print(f"{'='*60}")
    safe_print(f"  ✓ Generated {len(generated_files)} posts")
    safe_print(f"  File list saved to: {output_file}")
    safe_print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
