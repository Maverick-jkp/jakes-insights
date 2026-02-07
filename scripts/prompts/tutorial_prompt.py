"""
Tutorial Prompt Template

For comprehensive, in-depth tutorials with code examples, comparison tables,
and step-by-step guides. Target: 2,500-3,500 words (EN/KO), 7,500-10,500 chars (JA).
"""

def get_tutorial_prompt(topic: str, keywords: list, language: str, audience: str = "developers and engineers") -> str:
    """
    Generate tutorial prompt for given parameters.

    Args:
        topic: Main topic of the tutorial
        keywords: List of relevant keywords
        language: 'en', 'ko', or 'ja'
        audience: Target audience description

    Returns:
        Complete prompt string
    """

    keywords_str = ', '.join(keywords[:5])  # Use top 5 keywords

    # Language-specific word count targets
    word_count = {
        'en': '2,500-3,500 words',
        'ko': '2,500-3,500 단어',
        'ja': '7,500-10,500 文字'
    }.get(language, '2,500-3,500 words')

    # Language-specific instructions
    lang_instructions = {
        'en': 'English',
        'ko': '한국어 (Korean)',
        'ja': '日本語 (Japanese)'
    }.get(language, 'English')

    prompt = f"""Write a comprehensive tutorial article on "{topic}".

TARGET: {word_count}
LANGUAGE: {lang_instructions}
AUDIENCE: {audience}
KEYWORDS: {keywords_str}
STYLE: Professional, educational, practical

MANDATORY STRUCTURE:

## 1. Introduction ({_get_intro_words(language)})
- Hook: Why is this topic important in 2026?
- Who should read this tutorial?
- What will readers learn by the end?
- Quick preview of key benefits (3-4 bullet points)

## 2. Background & Context ({_get_background_words(language)})
- Brief history or evolution of this technology/concept
- Current landscape and why it matters now
- Key challenges or problems it solves
- Prerequisites or required knowledge (if any)

## 3. Comparison Table ({_get_comparison_words(language)})

Create a detailed markdown comparison table comparing this solution with 2-3 alternatives:

| Feature | {topic} | Alternative 1 | Alternative 2 |
|---------|---------|---------------|---------------|
| Cost | ... | ... | ... |
| Ease of Use | ... | ... | ... |
| Performance | ... | ... | ... |
| Scalability | ... | ... | ... |
| Community/Support | ... | ... | ... |

After the table, explain each comparison point in 2-3 sentences.

## 4. Step-by-Step Implementation Guide ({_get_guide_words(language)})

### Prerequisites
List required tools, software, or knowledge:
- Tool/Software 1
- Tool/Software 2
- Background knowledge needed

### Step 1: [Clear, Action-Oriented Title]
Provide detailed explanation and include a code example or command:

```bash
# Example command with comments
command --option value
```

OR

```python
# Example code with inline comments
def example_function():
    # Explanation of what this does
    return result
```

### Step 2: [Next Step Title]
Continue with more code examples. Include:
```language
# Working code example
# with clear comments
```

### Step 3-5: [Additional Steps]
Provide 3-5 total steps, each with:
- Clear explanation
- Code examples or commands
- Expected output or results
- Common issues to watch for

## 5. Code Examples & Real-World Use Cases ({_get_examples_words(language)})

### Basic Example
```language
# Complete, working basic example
# that readers can copy and run
```

**Explanation:**
Walk through this code line by line, explaining what each part does.

### Advanced Example
```language
# More sophisticated example
# showing real-world usage
```

**Use Case:**
Describe a real-world scenario where this would be useful.

## 6. Best Practices & Tips ({_get_tips_words(language)})

### Common Pitfalls to Avoid
- **Pitfall 1**: Description of the issue
  - Solution: How to avoid or fix it

- **Pitfall 2**: Another common mistake
  - Solution: Best practice to follow

### Optimization Tips
- **Performance Tip 1**: How to improve speed/efficiency
- **Security Tip 1**: Important security consideration
- **Scalability Tip 1**: Planning for growth

### Production Readiness Checklist
- [ ] Checklist item 1
- [ ] Checklist item 2
- [ ] Checklist item 3

## 7. Conclusion & Next Steps ({_get_conclusion_words(language)})
- Summary of key takeaways (3-5 bullet points)
- **Call-to-Action**: Encourage readers to try it today
  - "Start by installing X and following Step 1..."
  - "Try this tutorial with your own project..."
- Links to official documentation
- Recommended next learning resources or advanced topics

CRITICAL REQUIREMENTS:
✓ Use clear H2 (##) and H3 (###) headings throughout
✓ Include at least 2-3 code blocks with proper syntax highlighting
✓ Create exactly 1 comparison table in markdown format
✓ Provide 3-5 numbered, step-by-step instructions
✓ Add practical examples that readers can actually use
✓ End with a clear, actionable call-to-action
✓ Use markdown formatting: **bold**, *italic*, `code`, [links](url)
✓ Write entirely in {lang_instructions}

CODE BLOCK REQUIREMENTS:
- Add descriptive comments in the code
- Use realistic, meaningful variable/function names
- Show complete, runnable examples when possible
- Include error handling where appropriate
- Specify language for syntax highlighting (```python, ```bash, ```javascript, etc.)

TONE & STYLE:
- Professional yet approachable
- Educational and encouraging
- Practical and action-oriented
- Assume reader is intelligent but may be new to this specific topic
- Use "you" to address the reader
- Break complex concepts into digestible pieces

IMPORTANT:
- Do NOT use phrases like "I will", "Let me", "I'll show you" - just teach directly
- Do NOT add meta-commentary about the article itself
- Do NOT use excessive marketing language or hype
- Do NOT make claims you cannot back up with code examples

AI PHRASE BLACKLIST (NEVER USE):
- "game-changer", "revolutionary", "revolutionize"
- "cutting-edge", "state-of-the-art", "groundbreaking"
- "leverage", "robust", "seamlessly", "synergy"
- "In today's rapidly evolving...", "In the ever-changing landscape..."
- "It's important to note that...", "It's worth mentioning..."
- "Whether you're a... or a...", "dive deep", "dive into"
- "comprehensive guide", "everything you need to know"
- Excessive hedging: "Moreover", "Furthermore", "Additionally" (max 1 each)

FACTUAL ACCURACY (MANDATORY):
- All code examples MUST be tested and working
- Version numbers MUST be current and accurate
- Library/framework features MUST exist in current stable versions
- Do NOT invent APIs, methods, or features that don't exist
- If unsure about a specific detail, use general descriptions instead of inventing
- Focus on practical, working solutions

{_get_language_specific_rules(language)}

Now write the complete tutorial article following this structure exactly."""

    return prompt


def _get_intro_words(language: str) -> str:
    """Get intro section word count by language"""
    return {
        'en': '200-250 words',
        'ko': '200-250 단어',
        'ja': '600-750 文字'
    }.get(language, '200-250 words')


def _get_background_words(language: str) -> str:
    """Get background section word count by language"""
    return {
        'en': '350-400 words',
        'ko': '350-400 단어',
        'ja': '1050-1200 文字'
    }.get(language, '350-400 words')


def _get_comparison_words(language: str) -> str:
    """Get comparison section word count by language"""
    return {
        'en': '300-350 words',
        'ko': '300-350 단어',
        'ja': '900-1050 文字'
    }.get(language, '300-350 words')


def _get_guide_words(language: str) -> str:
    """Get guide section word count by language"""
    return {
        'en': '900-1,200 words',
        'ko': '900-1,200 단어',
        'ja': '2700-3600 文字'
    }.get(language, '900-1,200 words')


def _get_examples_words(language: str) -> str:
    """Get examples section word count by language"""
    return {
        'en': '400-500 words',
        'ko': '400-500 단어',
        'ja': '1200-1500 文字'
    }.get(language, '400-500 words')


def _get_tips_words(language: str) -> str:
    """Get tips section word count by language"""
    return {
        'en': '300-400 words',
        'ko': '300-400 단어',
        'ja': '900-1200 文字'
    }.get(language, '300-400 words')


def _get_conclusion_words(language: str) -> str:
    """Get conclusion section word count by language"""
    return {
        'en': '200-250 words',
        'ko': '200-250 단어',
        'ja': '600-750 文字'
    }.get(language, '200-250 words')


def _get_language_specific_rules(language: str) -> str:
    """Return language-specific writing quality rules for tutorials."""
    rules = {
        'en': """
ENGLISH-SPECIFIC QUALITY RULES:
- Use clear, imperative instructions: "Open the file" not "You should open the file"
- Keep explanations concise - readers want to DO, not read paragraphs
- Use consistent terminology throughout (pick one term and stick with it)
- Prefer "you" over "we" for direct instruction
- Code comments should explain WHY, not WHAT
""",
        'ko': """
한국어 품질 규칙:
- 명확한 지시형 문장 사용: "파일을 엽니다" (간결하게)
- 한국어로 자연스러운 기술 용어 사용 (무리한 번역 피하기)
- 코드 주석은 한국어로 작성 (독자 편의)
- 불필요한 높임말 반복 피하기
""",
        'ja': """
日本語品質ルール:
- 過度なヘッジング禁止: 「〜と思います」「〜かもしれません」は最小限に
- 「ただし」は全体で2回まで
- 明確な指示文を使用: 「〜してください」「〜します」
- コードコメントは日本語で記述
- 架空のライブラリやAPIは絶対に使用しない
"""
    }
    return rules.get(language, '')
