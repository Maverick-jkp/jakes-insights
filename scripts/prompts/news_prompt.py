"""
News Prompt Template

For concise, factual news articles with key information and context.
Target: 800-1,200 words (EN/KO).
"""

def get_news_prompt(topic: str, keywords: list, language: str, audience: str = "general tech audience") -> str:
    """
    Generate news prompt for given parameters.

    Args:
        topic: Main topic of the news article
        keywords: List of relevant keywords
        language: 'en' or 'ko'
        audience: Target audience description

    Returns:
        Complete prompt string
    """

    keywords_str = ', '.join(keywords[:5])

    word_count = {
        'en': '800-1,200 words',
        'ko': '800-1,200 단어',
    }.get(language, '800-1,200 words')

    lang_instructions = {
        'en': 'English',
        'ko': '한국어 (Korean)',
    }.get(language, 'English')

    prompt = f"""Write a concise news article on "{topic}".

TARGET: {word_count}
LANGUAGE: {lang_instructions}
AUDIENCE: {audience}
KEYWORDS: {keywords_str}
STYLE: Factual, clear, timely

MANDATORY STRUCTURE:

## 1. Lead Paragraph ({_get_lead_words(language)})
**Answer the 5 W's immediately** (most important information first):
- **WHO**: Key person, company, or organization involved
- **WHAT**: The main event, announcement, or development
- **WHEN**: Specific date, time, or timeframe
- **WHERE**: Location, platform, or context
- **WHY**: Stated reason, motivation, or purpose

Write this as 2-3 sentences that capture the essence of the story.

**KEY TAKEAWAYS BLOCK (MANDATORY)** - Insert immediately after Lead Paragraph, before ## 2:
> **Key Takeaways**
> - 3-5 bullet points summarizing the most important facts
> - Each point: complete, standalone declarative sentence with specific data
> - These should be directly quotable by AI search engines (Perplexity, Google SGE)

## 2. Key Details ({_get_details_words(language)})

### Main Announcement or Event
- Specific features, products, or changes announced
- Important numbers: pricing, user counts, dates, metrics
- Official quotes from company/person (if available)
- Key specifications or technical details

### Supporting Information
Use bullet lists OR markdown tables for clarity:

**Option: Use a table when comparing 2+ items or showing structured data:**

| Item | Detail 1 | Detail 2 | Notes |
|------|----------|----------|-------|
| Feature A | ... | ... | ... |
| Feature B | ... | ... | ... |

**Otherwise use bullet lists:**
- **Technical specifications** (if relevant):
  - Spec 1
  - Spec 2
  - Spec 3
- **Availability and timeline**:
  - When: Launch/release dates
  - Where: Geographic regions or platforms
  - How: Access method or requirements
- **Limitations or caveats** (if any):
  - Important restrictions to note
  - What's NOT included

## 3. Context & Background ({_get_context_words(language)})

### Industry Context
- How this fits into broader industry trends
- Recent related developments from competitors
- Current market landscape or state of technology

### Company or Technology Background
- Brief history (2-3 sentences maximum)
- Previous related products, services, or announcements
- Current market position or significance
- Why this company/development matters

## 4. Impact & Analysis ({_get_impact_words(language)})

### Who is Affected?
- **Developers/Engineers**: Specific impact on their work
- **Businesses/Organizations**: Business implications
- **End Users/Consumers**: How their experience changes

### What Changes?
- **Immediate effects** (this week/month):
  - Change 1
  - Change 2
- **Medium-term implications** (next 3-6 months):
  - Implication 1
  - Implication 2

### What to Watch Next
- Upcoming milestones or dates to track
- Potential issues or concerns to monitor
- Follow-up developments likely to happen
- Related announcements expected from competitors

CRITICAL REQUIREMENTS:
✓ Start with the most important information (inverted pyramid)
✓ Keep paragraphs short (2-4 sentences each)
✓ Use bullet points for lists and specifications
✓ Include specific dates, numbers, and facts
✓ Cite sources when referencing specific claims
✓ Use markdown formatting: **bold**, *italic*, bullet lists
✓ Write entirely in {lang_instructions}

FACTUAL REPORTING:
- Stick to verifiable facts
- Attribute claims to sources ("According to...", "The company stated...")
- Use precise language ("increased by 20%" not "increased significantly")
- Include official quotes when relevant
- Specify dates precisely ("February 4, 2026" not "recently")

TONE & STYLE:
- Factual and objective
- Clear and concise
- Timely and relevant
- Professional and neutral
- Get to the point quickly
- Avoid editorializing

THINGS TO INCLUDE:
- Specific dates and numbers
- Official company/person names
- Product/service names and versions
- Links to official announcements (if mentioning them)
- Key technical specifications (if relevant)
- Market context

THINGS TO AVOID:
- Speculation beyond stated facts
- Personal opinions or biased language
- Excessive background information
- Marketing hype or promotional language
- Unnecessary jargon (explain technical terms)
- Vague timeframes ("soon", "recently" - be specific)
- Filler content just to reach word count

AI PHRASE BLACKLIST (NEVER USE - 2025 Research Based):
- "game-changer", "revolutionary", "revolutionize"
- "cutting-edge", "state-of-the-art", "groundbreaking"
- "leverage", "robust", "seamlessly", "synergy"
- "delve", "tapestry", "realm", "testament"
- "pivotal", "multifaceted", "comprehensive"
- "foster", "endeavour", "facilitate", "optimize", "utilize"
- "In today's rapidly evolving...", "In the ever-changing landscape..."
- "In the realm of...", "In essence", "In summary", "In conclusion"
- "It's important to note that...", "It's worth mentioning..."
- "Certainly!", "Absolutely!", "Great question!"
- "Whether you're a... or a...", "dive deep", "dive into"
- "comprehensive guide", "everything you need to know"
- "Let me break down", "You might be thinking"
- Excessive hedging: "Moreover", "Furthermore", "Additionally" (max 1 each total)

CITATION REQUIREMENTS (MANDATORY):
- Every statistic MUST have an inline source: "According to [Source Name]..."
- Every percentage claim needs verification: Link to study or official report
- Do NOT use: "studies show", "research indicates", "experts say" without naming the specific study/expert
- If you cannot verify a statistic, DO NOT include it
- Fabricated statistics are UNACCEPTABLE - better to omit than to invent

KEEP IT CONCISE:
- News should be factual and to-the-point
- Don't pad with unnecessary details
- If it's 800 words of good content, that's better than 1,200 words of fluff
- Focus on what readers need to know NOW

{_get_language_specific_rules(language)}

Now write the complete news article following this structure exactly."""

    return prompt


def _get_lead_words(language: str) -> str:
    return {
        'en': '120-150 words',
        'ko': '120-150 단어',
    }.get(language, '120-150 words')


def _get_details_words(language: str) -> str:
    return {
        'en': '350-450 words',
        'ko': '350-450 단어',
    }.get(language, '350-450 words')


def _get_context_words(language: str) -> str:
    return {
        'en': '250-300 words',
        'ko': '250-300 단어',
    }.get(language, '250-300 words')


def _get_impact_words(language: str) -> str:
    return {
        'en': '200-250 words',
        'ko': '200-250 단어',
    }.get(language, '200-250 words')


def _get_language_specific_rules(language: str) -> str:
    """Return language-specific writing quality rules."""
    rules = {
        'en': """
ENGLISH-SPECIFIC QUALITY RULES:
- Write in active voice ("The company announced" not "It was announced by")
- Lead with the most important fact - no filler introductions
- Use concrete numbers and dates, not vague terms like "significant" or "recently"
- Attribute all claims to specific sources
- Prefer simple direct language: "said" not "stated", "use" not "utilize"

TONE REQUIREMENTS:
- News should still be engaging - not boring corporate speak
- Keep sentences punchy and direct
- Explain WHY something matters to the reader, not just WHAT happened

BANNED PHRASES:
- "Here's the thing" (overused)
- "Sound familiar?" (overused)
- "One industry expert..." (vague - use real names)
""",
        'ko': """
한국어 품질 규칙:
- 자연스러운 구어체 유지 (뉴스도 딱딱하지 않게)
- 핵심 정보를 먼저 전달 (역피라미드 구조)
- 한국 독자에게 친숙한 맥락 제공
- 불필요한 영어 단어 피하기

톤/스타일:
- 토스 뉴스처럼: 딱딱하지 않으면서도 신뢰감 있게
- "~거든요" 문단당 최대 1회
- "결합", "활용", "최적화" 같은 번역투 금지

금지 표현 (2025 AI 탐지 기반):
- "이런 경험 있으시죠?" (뉴스에 부적절)
- "한 업계 관계자에 따르면" (실명 사용 권장)
- "물론", "~할 수 있습니다", "중요합니다", "주목할만한"
- "~하는 것이 중요하다", "혁신적", "게임체인저"
""",
    }
    return rules.get(language, '')
