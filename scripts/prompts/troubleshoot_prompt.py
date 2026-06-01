"""
Troubleshoot Prompt Template

For "X not working / Y error / Z fails" articles. Different from tutorials —
tutorials assume nothing works yet and walk through setup; troubleshoot articles
assume the user has something half-working and needs to find the broken piece.

Target: 900-1,300 words (EN/KO).
"""


def get_troubleshoot_prompt(topic: str, keywords: list, language: str, audience: str = "tech professionals") -> str:
    keywords_str = ', '.join(keywords[:5])

    word_count = {'en': '900-1,300 words', 'ko': '900-1,300 단어'}.get(language, '900-1,300 words')
    lang_instructions = {'en': 'English', 'ko': '한국어 (Korean)'}.get(language, 'English')

    prompt = f"""Write a troubleshooting article on "{topic}".

TARGET: {word_count}
LANGUAGE: {lang_instructions}
AUDIENCE: {audience} (already familiar with the tool — they hit a wall, not a beginner)
KEYWORDS: {keywords_str}
STYLE: Diagnostic, terminal-friendly, fix-first then explanation

MANDATORY STRUCTURE:

## 1. The Symptom (100-150 words)
- Describe the exact symptom in one paragraph. Include the literal error
  message if there is one. Readers should be able to Cmd+F their error here.
- One sentence on why this is more annoying than it sounds (the implicit cost).

**Quick-Fix Block (MANDATORY)** — insert right after the symptom paragraph.
Choose ONE format:
- Format A: A fenced code block showing the 1-3 line fix that works for the most
  common cause. NO explanation yet.
- Format B: A `> **First check:**` blockquote with the single most likely cause
  and how to verify it in under 30 seconds.

The point: a reader landing from a search engine should get a candidate fix in
the first 30 seconds, before deciding whether to read the rest.

## 2. The Three Most Likely Causes (400-500 words)

For EACH cause (write 3 of them):

### Cause N: [One-line description]

**How to verify** (2-4 lines):
- A specific command, log query, or config check that confirms this is the cause
- What "yes this is it" looks like vs "no, move on"

**The fix** (code block + 2 sentences):
```bash
# concrete commands or config snippet
```

**Why this happens** (1-2 sentences):
- Brief technical explanation. Just enough that the reader understands and
  doesn't hit it again. Don't write a textbook chapter.

RULES:
- Order causes by likelihood, not by complexity. Most common goes first.
- If a cause is rare (<5%) and easy to rule out, mention it; if rare AND hard,
  push it to "## 3. Less Likely Causes" and keep this section to 3 entries.
- Every "verify" step must be runnable in under 1 minute.
- Every "fix" must be a specific command, config diff, or click path —
  NOT "make sure your configuration is correct."

## 3. Less Likely Causes (Worth Ruling Out) (150-200 words)
- Brief bulleted list of 2-4 less common causes
- Each: one line on the cause, one line on a fast check
- Use this section as a checklist; don't write paragraphs

## 4. If None of That Worked (100-150 words)
- The single best place to ask (specific GitHub issue tracker, Discord channel,
  Stack Overflow tag, vendor support tier — be specific, name it)
- The minimum information to include when asking, so the maintainer can help
  (version numbers, OS, the actual logs, what you've already tried)
- One link to the most-useful official doc page for this error

## 5. How to Prevent This Next Time (100-150 words)
- One concrete habit, config setting, or pre-flight check that catches this
  before it bites again
- If there's no good prevention (some bugs are just bugs), say so honestly
  and skip this section

CRITICAL REQUIREMENTS:
✓ The fix appears in section 1 (quick-fix block) AND section 2 (most likely
  cause). They should not contradict each other.
✓ Every command in a code block has been mentally executed — no fictional flags,
  no commands that look right but don't exist
✓ Every "verify" step is concrete and fast (<1 min)
✓ Section 4 names a SPECIFIC support channel, not "ask the community"
✓ Write entirely in {lang_instructions}

WHAT TO AVOID:
- "Make sure your configuration is correct" — useless, name the exact config key
- Hedging in fixes ("you might want to try...") — say "Run this:" and put the command
- Inventing CLI flags. If you're not sure a flag exists, omit it or check official docs
- Writing the entire article in past tense ("I encountered this when...") —
  use present tense, second person ("If you see X, run Y")
- Photo credit lines in body

AI PHRASE BLACKLIST (NEVER USE):
- "game-changer", "revolutionary", "cutting-edge"
- "leverage", "robust", "seamlessly", "synergy"
- "delve", "tapestry", "realm", "pivotal", "multifaceted"
- "foster", "facilitate", "utilize"
- "In today's rapidly evolving...", "It's important to note that..."
- "comprehensive guide", "everything you need to know"

CITATION / EVIDENCE REQUIREMENTS:
- If you cite a GitHub issue, version, or behavior, link to or name it
- If you describe an error message, quote it verbatim
- Do NOT invent error messages. If you don't know the exact text, describe the
  symptom in your own words instead.

{_get_language_specific_rules(language)}

Now write the complete troubleshooting article following this structure exactly."""

    return prompt


def _get_language_specific_rules(language: str) -> str:
    rules = {
        'en': """
ENGLISH-SPECIFIC QUALITY RULES:
- Imperative, second person: "Run this." "Check that." NOT "One could consider running..."
- Code blocks for every command, even one-liners
- Lead with the verb: "Restart the daemon." NOT "What you'll want to do is restart the daemon."
- Banned phrases: "Here's the thing", "Sound familiar?", "Let's be honest"
- No vague filler: "Generally speaking..." → just delete the phrase and say the thing.
""",
        'ko': """
한국어 품질 규칙:

톤/스타일:
- 명령형으로: "이거 실행해보세요." 식으로 직접적으로
- 코드 블록 적극 활용 — 한 줄 명령도 ```bash``` 안에 넣기
- 토스처럼 친근하게, 단 디버깅 글은 약간 더 빠릿빠릿하게
- 문장 끝 변화: "~예요", "~죠", "~보세요", "~해두면 돼요"

금지 표현:
- "확인해보시기 바랍니다" → "확인해보세요"로 줄이기
- "일반적으로", "보통은" → 빼고 본론 바로 가기
- "전략적", "효율적", "체계적" 금지
- 에러 메시지는 따옴표로 그대로 인용. 의역 금지.

트러블슈팅 글 특별 규칙:
- 1번 섹션의 빠른 해결책과 2번 섹션의 가장 유력한 원인이 일치해야 함
- "설정을 확인하세요" 같은 막연한 문장 금지 — 정확한 설정 키 이름 명시
- 3가지 원인은 가능성 높은 순서. 복잡한 순서 아님.
- 5번 섹션이 정직하게 "예방 불가능" 일 때는 그렇게 쓰고 섹션 자체 생략 OK
""",
    }
    return rules.get(language, '')
