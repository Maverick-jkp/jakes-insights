#!/usr/bin/env python3
"""
AI Reviewer - Self-Review Agent

Uses Claude API to review generated blog posts before human approval.
Provides scores and recommendations for content quality.

Usage:
    python ai_reviewer.py
    python ai_reviewer.py --file content/en/tech/2026-01-16-my-post.md
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.security import safe_print, mask_secrets

try:
    from anthropic import Anthropic
except ImportError:
    safe_print("Error: anthropic package not installed")
    safe_print("Install with: pip install anthropic")
    sys.exit(1)


# Review prompts for different languages
REVIEW_PROMPTS = {
    "en": """You are an expert content reviewer for a tech blog. Review this blog post and provide a detailed assessment.

Evaluation Criteria:
1. **Authenticity** (1-10): Does it sound natural and human? No AI-sounding phrases?
2. **Value** (1-10): Does it provide practical, actionable insights?
3. **Engagement** (1-10): Is it interesting and well-structured?
4. **Technical Accuracy** (1-10): Are facts and technical details correct?
5. **SEO Quality** (1-10): Good keyword usage, meta description, structure?
6. **AEO Readiness** (1-10): Has Key Takeaways block? Declarative, quotable statements? Would AI search engines cite this?

For each criterion, provide:
- Score (1-10)
- Brief explanation (1-2 sentences)
- Specific suggestions for improvement (if score < 8)

Overall Recommendation:
- APPROVE: Ready to publish (average score >= 8.0)
- REVISE: Needs minor improvements (average score 6.0-7.9)
- REJECT: Needs major rewrite (average score < 6.0)

Return your review as JSON with this structure:
{
  "scores": {
    "authenticity": {"score": 8, "explanation": "...", "suggestions": "..."},
    "value": {"score": 9, "explanation": "..."},
    ...
  },
  "average_score": 8.2,
  "recommendation": "APPROVE",
  "summary": "Overall assessment in 2-3 sentences",
  "top_strengths": ["strength 1", "strength 2"],
  "top_improvements": ["improvement 1", "improvement 2"]
}

Blog Post to Review:
---
{content}
---

Provide your review now:""",

    "ko": """당신은 기술 블로그의 전문 콘텐츠 리뷰어입니다. 이 블로그 글을 검토하고 상세한 평가를 제공하세요.

평가 기준:
1. **진정성** (1-10): 자연스럽고 인간적인가? AI 느낌나는 표현 없는가?
2. **가치** (1-10): 실용적이고 실행 가능한 인사이트를 제공하는가?
3. **참여도** (1-10): 흥미롭고 구조가 잘 짜여있는가?
4. **기술 정확성** (1-10): 사실과 기술적 세부사항이 정확한가?
5. **SEO 품질** (1-10): 키워드 사용, 메타 설명, 구조가 좋은가?
6. **AEO 대비** (1-10): 핵심 요약 블록이 있는가? 선언적이고 인용 가능한 문장이 있는가? AI 검색 엔진이 인용할 만한가?

각 기준에 대해 제공:
- 점수 (1-10)
- 간단한 설명 (1-2문장)
- 구체적인 개선 제안 (점수 < 8인 경우)

전체 추천:
- APPROVE: 게시 준비 완료 (평균 점수 >= 8.0)
- REVISE: 약간의 개선 필요 (평균 점수 6.0-7.9)
- REJECT: 대대적인 재작성 필요 (평균 점수 < 6.0)

다음 구조의 JSON으로 리뷰를 반환하세요:
{
  "scores": {
    "authenticity": {"score": 8, "explanation": "...", "suggestions": "..."},
    "value": {"score": 9, "explanation": "..."},
    ...
  },
  "average_score": 8.2,
  "recommendation": "APPROVE",
  "summary": "2-3문장으로 전체 평가",
  "top_strengths": ["강점 1", "강점 2"],
  "top_improvements": ["개선점 1", "개선점 2"]
}

검토할 블로그 글:
---
{content}
---

지금 리뷰를 제공하세요:"""
}


class AIReviewer:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize AI Reviewer with Claude API"""
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Set it as environment variable or pass to constructor."
            )

        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-6"

    def review_post(self, filepath: Path) -> Dict:
        """Review a single blog post"""
        # Read file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Detect language from filepath
        lang = self._detect_language(filepath)

        safe_print(f"  🔍 Reviewing with AI: {filepath.name}")
        safe_print(f"  Language: {lang}")

        # Get review prompt (use replace instead of .format() to avoid
        # KeyError when blog content contains curly braces like {scores})
        prompt = REVIEW_PROMPTS[lang].replace("{content}", content)

        # Call Claude API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Parse response
        review_text = response.content[0].text

        # Try to extract JSON from response
        try:
            # Find JSON in response (might be wrapped in markdown code blocks)
            import re
            json_match = re.search(r'\{[\s\S]*\}', review_text)
            if json_match:
                review = json.loads(json_match.group())
            else:
                # Fallback if no JSON found
                review = {
                    "error": "Could not parse JSON response",
                    "raw_response": review_text
                }
        except json.JSONDecodeError as e:
            review = {
                "error": f"JSON parse error: {mask_secrets(str(e))}",
                "raw_response": review_text
            }

        # Add metadata
        review['file'] = str(filepath)
        review['language'] = lang
        review['model'] = self.model

        return review

    def _detect_language(self, filepath: Path) -> str:
        """Detect language from filepath"""
        path_str = str(filepath)
        if '/ko/' in path_str:
            return 'ko'
        return 'en'

    def print_review(self, review: Dict):
        """Print review in human-readable format"""
        safe_print(f"\n{'='*60}")
        safe_print(f"  AI Review Results")
        safe_print(f"{'='*60}\n")

        if 'error' in review:
            safe_print(f"❌ Error: {review['error']}")
            safe_print(f"\nRaw response:\n{review.get('raw_response', 'N/A')}")
            return

        # Recommendation
        rec = review.get('recommendation', 'N/A')
        rec_emoji = {
            'APPROVE': '✅',
            'REVISE': '⚠️',
            'REJECT': '❌'
        }.get(rec, '❓')

        safe_print(f"{rec_emoji} Recommendation: {rec}")
        safe_print(f"📊 Average Score: {review.get('average_score', 'N/A')}/10\n")

        # Summary
        if 'summary' in review:
            safe_print(f"Summary:\n{review['summary']}\n")

        # Scores
        if 'scores' in review:
            safe_print("Detailed Scores:")
            for criterion, details in review['scores'].items():
                score = details.get('score', 'N/A')
                explanation = details.get('explanation', 'N/A')
                safe_print(f"\n  {criterion.capitalize()}: {score}/10")
                safe_print(f"  {explanation}")

                if 'suggestions' in details and details['suggestions']:
                    safe_print(f"  💡 Suggestions: {details['suggestions']}")

        # Strengths
        if 'top_strengths' in review and review['top_strengths']:
            safe_print(f"\n💪 Top Strengths:")
            for strength in review['top_strengths']:
                safe_print(f"  • {strength}")

        # Improvements
        if 'top_improvements' in review and review['top_improvements']:
            safe_print(f"\n🔧 Top Improvements:")
            for improvement in review['top_improvements']:
                safe_print(f"  • {improvement}")


def main():
    parser = argparse.ArgumentParser(description="AI Reviewer for generated content")
    parser.add_argument('--file', type=str, help="Specific file to review")
    args = parser.parse_args()

    # Initialize reviewer
    try:
        reviewer = AIReviewer()
    except ValueError as e:
        safe_print(f"Error: {mask_secrets(str(e))}")
        safe_print("\nSet ANTHROPIC_API_KEY environment variable:")
        safe_print("  export ANTHROPIC_API_KEY='your-api-key'")
        sys.exit(1)

    # Get files to review
    if args.file:
        # Review specific file
        filepath = Path(args.file)
        if not filepath.exists():
            safe_print(f"Error: File not found: {filepath}")
            sys.exit(1)
        files_to_review = [filepath]
    else:
        # Review from generated_files.json
        generated_files_path = Path("generated_files.json")
        if not generated_files_path.exists():
            safe_print("Error: generated_files.json not found")
            safe_print("Run generate_posts.py first or use --file to specify a file")
            sys.exit(1)

        with open(generated_files_path, 'r') as f:
            generated_files = json.load(f)

        files_to_review = [Path(f) for f in generated_files if Path(f).exists()]

    if not files_to_review:
        safe_print("No files to review")
        sys.exit(0)

    safe_print(f"\n{'='*60}")
    safe_print(f"  AI Reviewer - Reviewing {len(files_to_review)} files")
    safe_print(f"{'='*60}\n")

    all_reviews = []

    for filepath in files_to_review:
        safe_print(f"File: {filepath.name}")

        try:
            review = reviewer.review_post(filepath)
            reviewer.print_review(review)
            all_reviews.append(review)
            safe_print("")

        except Exception as e:
            safe_print(f"  ❌ Review failed: {mask_secrets(str(e))}\n")
            all_reviews.append({
                "file": str(filepath),
                "error": mask_secrets(str(e))
            })

    # Save review report
    report_path = Path("ai_review_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "total_files": len(all_reviews),
            "reviews": all_reviews
        }, f, indent=2, ensure_ascii=False)

    safe_print(f"{'='*60}")
    safe_print(f"  Review report saved to: {report_path}")
    safe_print(f"{'='*60}\n")

    # Summary
    approved = sum(1 for r in all_reviews if r.get('recommendation') == 'APPROVE')
    revise = sum(1 for r in all_reviews if r.get('recommendation') == 'REVISE')
    reject = sum(1 for r in all_reviews if r.get('recommendation') == 'REJECT')
    errors = sum(1 for r in all_reviews if 'error' in r)

    safe_print("Summary:")
    safe_print(f"  ✅ Approved: {approved}")
    safe_print(f"  ⚠️  Revise: {revise}")
    safe_print(f"  ❌ Reject: {reject}")
    if errors:
        safe_print(f"  🚫 Errors: {errors}")


if __name__ == "__main__":
    main()
