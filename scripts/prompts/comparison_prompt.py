"""
Comparison Prompt Template

For head-to-head comparison articles (X vs Y, A vs B vs C). Uses a matrix-first
structure: open with the verdict, then the data, then the nuance. Distinct from
the generic analysis template, which buries comparisons inside a single section.

Target: 1,000-1,400 words (EN/KO).
"""


def get_comparison_prompt(topic: str, keywords: list, language: str, audience: str = "tech professionals") -> str:
    keywords_str = ', '.join(keywords[:5])

    word_count = {'en': '1,000-1,400 words', 'ko': '1,000-1,400 단어'}.get(language, '1,000-1,400 words')
    lang_instructions = {'en': 'English', 'ko': '한국어 (Korean)'}.get(language, 'English')

    prompt = f"""Write a head-to-head comparison article on "{topic}".

TARGET: {word_count}
LANGUAGE: {lang_instructions}
AUDIENCE: {audience}
KEYWORDS: {keywords_str}
STYLE: Verdict-first, table-driven, evidence-backed

MANDATORY STRUCTURE:

## 1. Bottom Line Up Front (150-200 words)
- Open with the verdict in the first 2 sentences. Who wins, and on what dimension.
- Then: who SHOULDN'T pick the winner (every comparison has at least one user
  for whom the runner-up is better). Be specific.
- 3-4 bullets listing the dimensions you will compare in section 3.

**Decision Block (MANDATORY)** — insert immediately after the opening, before ## 2.
Pick ONE format and vary across articles:
- Format A: `> **TL;DR** \\n> - Use X if: ... \\n> - Use Y if: ... \\n> - Skip both if: ...`
- Format B: A 2-sentence "If you only read one paragraph" block, no blockquote
- Format C: A numbered "5-second answer" list (1-3 items, very short)

## 2. The Contenders (200-300 words)
- 1 paragraph per option, ~80 words each
- For each: what it is, who makes it, current version/price, headline strength
- Do NOT regurgitate marketing copy — describe what the tool ACTUALLY is, based
  on hands-on usage signals (recent reviews, GitHub activity, real benchmarks)
- If you cannot describe a real, current property of the option, OMIT IT rather
  than invent details

## 3. Head-to-Head Matrix (400-500 words)

**MANDATORY: Open this section with a markdown comparison table.**

| Dimension | Option A | Option B | Winner |
|-----------|----------|----------|--------|
| Pricing (entry tier) | concrete number | concrete number | A/B/Tie |
| Performance | specific metric | specific metric | A/B/Tie |
| Ecosystem / integrations | specific count or examples | specific count or examples | A/B/Tie |
| Learning curve | concrete: "1 hour" / "1 week" | concrete | A/B/Tie |
| Best-case use case | one specific scenario | one specific scenario | — |

**RULES for the table**:
- Use REAL numbers from official docs, pricing pages, or recent (≤6 months) benchmarks
- "Winner" column: pick A, B, or "Tie" — never both win, never "depends"
- If you don't have data for a row, omit the row entirely. Do NOT write "varies" or "depends"

After the table, write 3-4 short paragraphs unpacking the most surprising rows.
Don't repeat the table in prose; explain WHY the winner won that row.

## 4. Where Each One Actually Breaks (200-300 words)

For each option, ONE failure mode:
- **Option A breaks when**: specific scenario where it falls over
- **Option B breaks when**: specific scenario where it falls over

This is the most important section for trust. If you cannot name a real failure
mode (from forums, GitHub issues, post-mortems), the comparison is too shallow —
go research more before writing this section.

## 5. The Verdict & Next Step (150-200 words)
- Repeat the bottom-line verdict from section 1, now with the evidence behind it
- One concrete next step the reader can take in the next 10 minutes (try a free
  tier, run a specific benchmark, read a specific doc page)
- End with one open question worth tracking (NOT a generic "what do you think?")

CRITICAL REQUIREMENTS:
✓ Every numeric claim has an inline source or a clear "based on [official docs / Q1 2026 benchmark]"
✓ Markdown table in section 3 is mandatory — articles without it FAIL
✓ Verdict appears in section 1 AND section 5 (consistent, not contradictory)
✓ "Where each one breaks" section includes named failure modes, not generic hedging
✓ Write entirely in {lang_instructions}

WHAT TO AVOID:
- "It depends on your use case" without explaining WHICH use case → which choice
- Marketing language ("powerful", "robust", "elegant", "seamless")
- Symmetric praise — if both options are great at everything, you haven't dug deep enough
- Inventing benchmark numbers. If you don't have a real benchmark, omit that row
- Photo credit lines in the article body

AI PHRASE BLACKLIST (NEVER USE):
- "game-changer", "revolutionary", "cutting-edge", "state-of-the-art"
- "leverage", "robust", "seamlessly", "synergy", "delve", "tapestry", "realm"
- "pivotal", "multifaceted", "comprehensive", "foster", "facilitate", "utilize"
- "In today's rapidly evolving...", "In the realm of...", "It's important to note"
- "comprehensive guide", "everything you need to know", "dive deep"

CITATION REQUIREMENTS (MANDATORY):
- Every price, benchmark, or version number needs a source
- "According to [Vendor] official pricing as of [month year]..." is the minimum
- Do NOT use: "studies show", "experts say", "users report" without names
- Fabricated benchmarks are UNACCEPTABLE

{_get_language_specific_rules(language)}

Now write the complete comparison article following this structure exactly."""

    return prompt


def _get_language_specific_rules(language: str) -> str:
    rules = {
        'en': """
ENGLISH-SPECIFIC QUALITY RULES:
- Active voice, concrete subjects ("Cursor finishes the refactor in 4 seconds" not "The refactor was completed")
- Lead with the number, then the context. ("$20/month, double Copilot's entry tier." NOT "Cursor, which costs $20/month, is more expensive than Copilot.")
- Sentence length variety — short verdict sentences mixed with longer explanations
- Banned phrases: "Here's the thing", "Sound familiar?", "Let's be honest", "But here's where it gets interesting"
- No vague fake examples ("One Silicon Valley startup..."). Real names or no example.
""",
        'ko': """
한국어 품질 규칙:

톤/스타일:
- 결론 먼저, 근거 나중. 첫 문장에서 누가 이겼는지 말하기
- 표 안에는 진짜 숫자만. "상황에 따라 다름" 같은 행은 통째로 빼기
- 토스처럼 친근하게: "20달러 한 달, Copilot보다 두 배예요" 식으로
- 문장 끝 변화: "~예요", "~죠", "~더라고요", "~인 셈이에요" 섞어 쓰기

금지 표현:
- "이런 경험 있으시죠?" 도입부 외 사용 금지
- "전략적", "효율적", "체계적" — 구체적으로 풀어쓰기
- "결합", "활용", "최적화" — "합치다", "쓰다", "맞추다"로
- "혁신적", "게임체인저", "주목할만한" 절대 금지

비교 글 특별 규칙:
- 결론을 첫 섹션과 마지막 섹션 둘 다에 명시 (서로 모순되면 안 됨)
- 두 옵션이 모든 면에서 다 좋다고 쓰면 깊이 부족 — 진짜 실패 사례 한 개씩 반드시 찾기
- "사용 사례에 따라 다릅니다"로 끝내지 말 것. 어떤 사용 사례에선 어느 쪽인지 명시
""",
    }
    return rules.get(language, '')
