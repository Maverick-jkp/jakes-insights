"""
Analysis Prompt Template

For standard analysis articles with structured sections and comparison elements.
Target: 1,500-2,000 words (EN/KO), 4,500-6,000 chars (JA).
"""

def get_analysis_prompt(topic: str, keywords: list, language: str, audience: str = "tech professionals") -> str:
    """
    Generate analysis prompt for given parameters.

    Args:
        topic: Main topic of the analysis
        keywords: List of relevant keywords
        language: 'en', 'ko', or 'ja'
        audience: Target audience description

    Returns:
        Complete prompt string
    """

    keywords_str = ', '.join(keywords[:5])

    word_count = {
        'en': '1,500-2,000 words',
        'ko': '1,500-2,000 단어',
        'ja': '4,500-6,000 文字'
    }.get(language, '1,500-2,000 words')

    lang_instructions = {
        'en': 'English',
        'ko': '한국어 (Korean)',
        'ja': '日本語 (Japanese)'
    }.get(language, 'English')

    prompt = f"""Write an analytical article on "{topic}".

TARGET: {word_count}
LANGUAGE: {lang_instructions}
AUDIENCE: {audience}
KEYWORDS: {keywords_str}
STYLE: Analytical, insightful, balanced

MANDATORY STRUCTURE:

## 1. Introduction ({_get_intro_words(language)})
- **Hook**: What's happening with this topic right now?
- **Why it matters**: Explain significance in 2026 context
- **Thesis statement**: Your main argument or insight
- **Preview**: Quick bullet list of key points (3-4 items)

## 2. Background & Context ({_get_background_words(language)})
- What led to the current situation?
- Key players or companies involved
- Brief timeline of important recent events
- Current state of the technology/market/situation
- Why this is becoming important now

## 3. Main Analysis ({_get_analysis_words(language)})

Divide into 3-4 clear subsections:

### Key Point #1: [Descriptive Title]
- Main description and explanation
- Impact on the industry/users
- Specific examples or evidence
- Data or statistics if available

### Key Point #2: [Descriptive Title]
- Continue analysis
- Use concrete examples
- Compare to previous or alternative approaches

### Key Point #3: [Descriptive Title]
- Build on previous points
- Show connections or implications

### Comparison Analysis

Choose ONE format based on what makes sense:

**FORMAT A - Markdown Table** (if comparing 3+ options):

| Feature | Option A | Option B | Option C |
|---------|----------|----------|----------|
| Criteria 1 | ... | ... | ... |
| Criteria 2 | ... | ... | ... |
| Criteria 3 | ... | ... | ... |
| Best For | ... | ... | ... |

**FORMAT B - Structured Comparison** (if comparing 2 options):

**Option A:**
- **Pros**:
  - Advantage 1
  - Advantage 2
- **Cons**:
  - Limitation 1
  - Limitation 2
- **Best for**: Specific use cases

**Option B:**
- **Pros**:
  - Advantage 1
  - Advantage 2
- **Cons**:
  - Limitation 1
  - Limitation 2
- **Best for**: Different use cases

After the comparison, provide 2-3 paragraphs analyzing the trade-offs.

## 4. Practical Implications ({_get_implications_words(language)})

### Who Should Care?
- **Developers/Engineers**: Why they should pay attention
- **Companies/Organizations**: Business implications
- **End Users**: How it affects them

### How to Prepare or Respond
- **Short-term actions** (next 1-3 months):
  - Action 1
  - Action 2
- **Long-term strategy** (next 6-12 months):
  - Strategy 1
  - Strategy 2

### Opportunities & Challenges
- **Opportunity #1**: Describe the potential upside
  - How to capitalize on it
- **Challenge #1**: Describe the potential downside
  - How to mitigate it
- **Opportunity #2 / Challenge #2**: Continue as needed

## 5. Conclusion & Future Outlook ({_get_conclusion_words(language)})
- **Summary**: Recap the 3-4 key insights in bullet points
- **Future predictions**: What to expect in the next 6-12 months
  - Near-term developments
  - Potential game-changers
- **Reader takeaway**: One clear action or mindset shift
- **Final thought**: Forward-looking statement

CRITICAL REQUIREMENTS:
✓ Use H2 (##) and H3 (###) headings to structure content
✓ Include ONE comparison element (table OR structured list)
✓ Provide 3-5 concrete, specific examples throughout
✓ Add relevant data, statistics, or quotes when possible
✓ Link concepts together - show how points connect
✓ Use markdown formatting: **bold**, *italic*, `code`, bullet lists
✓ Write entirely in {lang_instructions}

COMPARISON REQUIREMENTS:
- Compare at least 2 options/approaches/solutions
- Use specific criteria (cost, performance, ease of use, etc.)
- Be balanced - show pros AND cons
- Provide context for when each option makes sense

TONE & STYLE:
- Analytical and thoughtful
- Balanced perspective (avoid bias)
- Forward-looking and insightful
- Professional but accessible
- Use "you" sparingly - focus on the topic
- Support claims with evidence or reasoning

THINGS TO INCLUDE:
- Real-world examples or use cases
- Connections to broader trends
- Practical implications
- Balanced pros and cons
- Forward-looking perspective

THINGS TO AVOID:
- Pure speculation without basis
- One-sided arguments
- Marketing language or hype
- Excessive technical jargon without explanation
- Making unsubstantiated predictions
- Personal opinions stated as facts

AI PHRASE BLACKLIST (NEVER USE):
- "game-changer", "revolutionary", "revolutionize"
- "cutting-edge", "state-of-the-art", "groundbreaking"
- "leverage", "robust", "seamlessly", "synergy"
- "In today's rapidly evolving...", "In the ever-changing landscape..."
- "It's important to note that...", "It's worth mentioning..."
- "Whether you're a... or a...", "dive deep", "dive into"
- "comprehensive guide", "everything you need to know"
- Excessive hedging: "Moreover", "Furthermore", "Additionally" (max 1 each)

CITATION REQUIREMENTS (MANDATORY):
- Every statistic MUST have an inline source: "According to [Source Name]..."
- Every percentage claim needs verification: Link to study or official report
- Do NOT use: "studies show", "research indicates", "experts say" without naming the specific study/expert
- If comparing products/services, use REAL specifications from official sources
- Do NOT invent products, features, or companies that don't exist
- Fabricated data is UNACCEPTABLE - better to be general than to lie

Now write the complete analysis article following this structure exactly."""

    return prompt


def _get_intro_words(language: str) -> str:
    return {
        'en': '250-300 words',
        'ko': '250-300 단어',
        'ja': '750-900 文字'
    }.get(language, '250-300 words')


def _get_background_words(language: str) -> str:
    return {
        'en': '300-350 words',
        'ko': '300-350 단어',
        'ja': '900-1050 文字'
    }.get(language, '300-350 words')


def _get_analysis_words(language: str) -> str:
    return {
        'en': '700-900 words',
        'ko': '700-900 단어',
        'ja': '2100-2700 文字'
    }.get(language, '700-900 words')


def _get_implications_words(language: str) -> str:
    return {
        'en': '350-400 words',
        'ko': '350-400 단어',
        'ja': '1050-1200 文字'
    }.get(language, '350-400 words')


def _get_conclusion_words(language: str) -> str:
    return {
        'en': '200-250 words',
        'ko': '200-250 단어',
        'ja': '600-750 文字'
    }.get(language, '200-250 words')
