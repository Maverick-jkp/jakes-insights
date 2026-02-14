#!/usr/bin/env python3
"""
Few-Shot Writing Examples

High-quality tech writing examples for style learning.
Extracted patterns from: Vercel, Stripe, Toss, Dev.to top articles
"""

from typing import Dict

# English Analysis/Tutorial Examples
EN_EXAMPLES = {
    "analysis": """
# Style Example: Tech Analysis (Vercel/Stripe style)

**Opening Pattern**:
Direct problem statement with specific numbers.
Example: "Three months ago, our build times hit 14 minutes. Today they're 47 seconds."

**Transition Style**:
- Use questions: "Why does this matter?"
- Short declarative: "The problem wasn't obvious."
- Direct address: "You've probably seen this pattern."

**Data Presentation**:
- Tables for comparisons
- Inline numbers with context
- "According to [Source]" citations

**Tone**:
- Direct, no hedging
- Use contractions (it's, we're, doesn't)
- Mix short and long sentences dramatically
- Occasional sentence fragments. Like this.

**Avoid**:
- ❌ "Here's the thing" / "Sound familiar?"
- ❌ "Let me explain" / "You might be thinking"
- ❌ Corporate speak / formal tone
""",

    "tutorial": """
# Style Example: Tutorial (Dev.to/Josh Comeau style)

**Opening Pattern**:
Start with the "aha moment" or the problem solved.
Example: "I spent 6 hours debugging CORS errors before realizing..."

**Code Style**:
- Show, don't tell
- Real examples, no foo/bar
- Inline comments explaining "why", not "what"
- Before/After comparisons

**Structure**:
- TL;DR at top
- Prerequisites section
- Step-by-step with code
- "What could go wrong" section
- Next steps

**Tone**:
- Encouraging, like a helpful colleague
- Acknowledge common mistakes without being condescending
- "This tripped me up too"

**Avoid**:
- ❌ "Simply do X" when X is complex
- ❌ "Obviously" / "Just" / "Easily"
- ❌ Skipping error handling
"""
}

# Korean Examples (Toss/Kakao style)
KO_EXAMPLES = {
    "analysis": """
# 스타일 예시: 기술 분석 (토스/카카오 블로그 스타일)

**도입부 패턴**:
문제 상황을 구체적 숫자로 제시.
예: "2분이면 끝나야 할 화면 로딩이 10초씩 걸렸어요."

**전환 스타일**:
- 질문 활용: "왜 그럴까요?"
- 짧은 문장: "문제는 이거였어요."
- 독자 호명: "비슷한 경험 있으실 거예요."

**데이터 제시**:
- 비교 표 사용
- 구체적 숫자 + 맥락
- "~에 따르면" 출처 명시

**톤**:
- 친근한 대화체 (해요체)
- "~거든요", "~죠", "~예요" 섞어 쓰기
- 문장 길이 극단적으로 변주
- 한 줄 문장도 ok. 이렇게요.

**피할 것**:
- ❌ "이런 경험 있으시죠?" (과다 사용)
- ❌ "솔직히 말하면" (반복)
- ❌ "~할 수 있습니다" (딱딱함)
- ❌ "활용", "결합", "최적화" (번역투)
""",

    "tutorial": """
# 스타일 예시: 튜토리얼 (Velog 인기글 스타일)

**도입부 패턴**:
문제 해결 순간이나 깨달음으로 시작.
예: "6시간 동안 CORS 에러로 고생하다가 알게 된 건데요..."

**코드 스타일**:
- 보여주기 > 설명하기
- 실제 예시 사용 (foo/bar 금지)
- 주석은 "왜"를 설명
- Before/After 비교

**구조**:
- 요약 먼저
- 사전 준비물
- 단계별 가이드 + 코드
- "흔한 실수" 섹션
- 다음 단계

**톤**:
- 선배가 후배 알려주듯
- 실수를 인정: "저도 처음엔 헷갈렸어요"
- 격려: "잘하고 있어요!"

**피할 것**:
- ❌ "간단하게 X하면 됩니다" (복잡한데)
- ❌ "당연히" / "쉽게" (오만함)
- ❌ 에러 핸들링 생략
"""
}


def get_examples(lang: str, content_type: str = "analysis") -> str:
    """
    Get few-shot examples for a language and content type.

    Args:
        lang: 'en' or 'ko'
        content_type: 'analysis', 'tutorial', or 'news'

    Returns:
        Example text
    """
    if lang == "en":
        return EN_EXAMPLES.get(content_type, EN_EXAMPLES["analysis"])
    elif lang == "ko":
        return KO_EXAMPLES.get(content_type, KO_EXAMPLES["analysis"])
    else:
        return ""


def get_all_examples() -> Dict[str, Dict[str, str]]:
    """Get all examples organized by language and type"""
    return {
        "en": EN_EXAMPLES,
        "ko": KO_EXAMPLES
    }


if __name__ == '__main__':
    # Print examples for verification
    print("=== English Examples ===\n")
    for content_type, example in EN_EXAMPLES.items():
        print(f"\n## {content_type.upper()}\n")
        print(example)

    print("\n\n=== Korean Examples ===\n")
    for content_type, example in KO_EXAMPLES.items():
        print(f"\n## {content_type.upper()}\n")
        print(example)
