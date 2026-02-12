# 프롬프트 개선 전략

**작성일**: 2026-02-12
**목적**: AI 패턴 제거 + 흡인력 있는 콘텐츠 생성
**기반**: 파이프라인 분석 + Medium/Dev.to 벤치마크

---

## 현재 문제점 요약

### 1. AI 패턴 감지 위험 (심각)

**증상**:
- "Here's the thing" (글당 5-9회)
- "Sound familiar?" (거의 모든 글)
- "Let me break down" (반복)
- 문장 길이가 균일함 (Burstiness 낮음)

**원인**:
- 시스템 프롬프트에 "Medium/Substack 스타일"만 명시
- AI 블랙리스트가 불완전 (delve, tapestry, realm, foster 누락)
- 문장 변주 지시가 없음

**영향**:
- GPTZero/Originality.ai에서 즉시 탐지 가능
- Google의 "Scaled Content Abuse" 정책 위반 가능
- Dev.to 커뮤니티 반감

### 2. 코드 블록 생성 실패 (심각)

**증상**:
- Tutorial 프롬프트에 "코드 블록 2-3개 필수"라고 되어 있지만 실제 생성 안 됨
- Quality Gate가 tutorial에서 코드 블록 2개 미만이면 FAIL인데도 통과됨 (버그?)

**원인**:
- Claude가 프롬프트의 코드 블록 요청을 무시
- 강제성이 없음 ("필수"라고만 되어있음)

**영향**:
- Dev.to에서 코드 없는 tech 글은 "빈 칼로리 콘텐츠"로 취급
- 개발자 타겟 글인데 코드가 없으면 신뢰도 하락

### 3. 워드카운트 혼란 (중간)

**현재 상태**:
- 시스템 프롬프트: 800-1,100 (AdSense 최적화)
- 프롬프트 파일: 800~3,500 (유형별)
- 실제 생성: 2,700~3,900 (너무 김)

**문제**:
- Dev.to 최적: 5분 (약 1,200-1,500 단어)
- 현재: 10-15분 (2,700~3,900 단어) → 너무 길어서 이탈

**원인**:
- Editor Agent가 "확장" 로직만 있고 "축약" 로직이 약함
- 프롬프트 파일의 타겟이 너무 높음

### 4. 도입부 흡인력 부족 (중간)

**증상**:
- 대부분 "You've been there, right?" 같은 공감 유도로 시작
- 구체적 숫자, 반전, 고백 같은 강력한 Hook 없음

**원인**:
- 시스템 프롬프트에 도입부 템플릿이 없음
- "흥미로운 도입부"라는 추상적 지시만 있음

---

## 개선 전략

### A. AI 패턴 제거

#### A1. 금지 단어 목록 확장

**현재 블랙리스트** (scripts/prompts/*.py):
```
영어: "game-changer", "revolutionary", "cutting-edge", "leverage", "robust",
      "seamlessly", "synergy", "Moreover", "Furthermore", "Additionally"
한국어: "결합", "활용", "최적화", "전략적", "효율적", "체계적"
```

**추가할 단어** (2025 연구 기반):
```
영어:
- delve, tapestry, realm, testament, pivotal, multifaceted, comprehensive
- foster, endeavour, facilitate, optimize, utilize
- "In today's ever-evolving world", "In the realm of", "In essence"
- "Certainly!", "Absolutely!", "Great question!"
- "It's important to note", "It's worth mentioning"

한국어:
- "물론", "~할 수 있습니다", "중요합니다", "주목할만한"
- "~하는 것이 중요하다", "혁신적", "게임체인저"
```

#### A2. 문장 변주 명시적 요청

시스템 프롬프트에 추가:
```
CRITICAL - Sentence Variation (Burstiness):
- Mix short punchy sentences (5-7 words) with longer explanatory ones (25-35 words)
- Example pattern: Short. Long explanation with details and context. Short. Medium.
- Avoid uniform sentence lengths (AI detection flag)
- Aim for high perplexity: use unexpected word choices occasionally
```

#### A3. 구어체 강제

```
Conversational Markers (MUST include):
- Contractions: you're, it's, doesn't, I've, we're
- Direct questions to reader
- Occasional incomplete sentences for emphasis
- "So", "And", "But" as sentence starters (not "Moreover/Furthermore")
```

### B. 코드 블록 생성 강제

#### B1. Tutorial 프롬프트 수정

**현재** (scripts/prompts/tutorial_prompt.py):
```python
"Include 2-3 code examples with syntax highlighting"
```

**개선**:
```python
"MANDATORY: Include exactly 3 code blocks:
1. Basic example (10-15 lines) - demonstrating core concept
2. Intermediate example (20-30 lines) - real-world use case
3. Production-ready example (30-50 lines) - with error handling

Use actual library/framework names (NO foo/bar placeholders).
Each code block MUST have:
- Syntax highlighting (```language)
- Inline comments explaining key lines
- Before/After context explaining what it does"
```

#### B2. Quality Gate 강화

quality_gate.py에서:
```python
# Tutorial에서 코드 블록 < 2개면 FAIL
if content_type == 'tutorial':
    code_blocks = len(re.findall(r'```\w+', content))
    if code_blocks < 2:
        return FAIL  # 현재는 WARNING만 나오는 것 같음
```

### C. 워드카운트 조정

#### C1. 유형별 타겟 재조정

| 유형 | 현재 | 개선 | 이유 |
|------|------|------|------|
| News | 800-1,200 | 600-900 | 뉴스는 빠르게 읽혀야 함 |
| Analysis | 1,500-2,000 | 1,200-1,800 | Dev.to 최적 (5-7분) |
| Tutorial | 2,500-3,500 | 1,800-2,500 | 너무 길면 이탈 |

#### C2. Editor Agent 수정

```python
# 최대값 130% 초과 시 → 중복 제거가 아니라 적극적 축약
if word_count > target_max * 1.3:
    instruction = "Cut to {target_max} words. Remove:\n" \
                  "- Redundant explanations\n" \
                  "- Generic introductions\n" \
                  "- Filler transitions"
```

### D. 도입부 Hook 강화

#### D1. Hook 템플릿 추가

시스템 프롬프트에:
```
Opening Hook (pick ONE):
1. Number Hook: "[Specific number] of [things] revealed [surprising insight]"
   Example: "500 PR reviews taught me that most bugs hide in plain sight"

2. Confession Hook: "I [did X] for [time] before realizing [Y]"
   Example: "I advocated TDD for 3 years but never used it in my side projects"

3. Reversal Hook: "Everyone does X, but we chose Y"
   Example: "While everyone was moving to microservices, we went back to monolith"

4. Anecdote Hook: "Friday 6 PM, [specific action], [dramatic result]"
   Example: "Friday 6 PM, hit deploy, and Slack exploded with 47 alerts"

5. Data Hook: "We reduced [metric] from X to Y"
   Example: "We cut build time from 14 minutes to 47 seconds"

DO NOT start with:
- "You've probably been there..."
- "In today's world of..."
- Generic problem statements
```

#### D2. 첫 문단 길이 제한

```
First paragraph: Maximum 50 words (2-3 sentences)
Get to the point immediately. Save context for paragraph 2.
```

### E. 페르소나 강화

#### E1. 구체적 페르소나 설정

**현재** (generate_posts.py 시스템 프롬프트):
```
"You are a professional tech blogger writing in Medium/Substack style"
```

**개선**:
```
"You are a senior software engineer with 7+ years of production experience.
You've worked at both startups (20-person teams) and mid-sized companies (200+ people).
You write like you're explaining to a smart colleague over coffee - direct, opinionated,
occasionally self-deprecating. You back claims with specific examples from real projects.
You prefer showing code over abstract explanations."
```

#### E2. 언어별 페르소나 차별화

**영어**:
```
Persona: Senior engineer at a SaaS startup. Direct, practical, code-first.
Tone: "Here's what worked, here's what didn't, here's why."
References: Real companies (Stripe, Vercel, GitHub), not generic "a company"
```

**한국어**:
```
Persona: 토스 스타일 - 친근하면서 신뢰감 있는 전문가
Tone: "~예요/~죠" 체. 전문용어 즉시 풀어서 설명.
References: 국내 서비스 (토스, 카카오, 배민) 사례 활용
```

---

## 구현 우선순위

### Phase 1: 긴급 (즉시)
1. **AI 블랙리스트 확장** - delve, tapestry, realm, foster 등 추가
2. **문장 변주 지시** - Burstiness 명시적 요청
3. **구어체 강제** - 축약형, 직접 호칭 필수화

### Phase 2: 중요 (1-2일 내)
4. **코드 블록 강제** - Tutorial 프롬프트 수정 + Quality Gate 강화
5. **도입부 Hook 템플릿** - 5가지 패턴 중 선택
6. **페르소나 구체화** - 7년차 엔지니어, 실전 경험 강조

### Phase 3: 최적화 (3-5일 내)
7. **워드카운트 조정** - 유형별 타겟 재설정
8. **Editor Agent 개선** - 적극적 축약 로직
9. **언어별 페르소나** - EN/KO 차별화

---

## 성공 지표

### 정량적
- [ ] AI detection score < 20% (GPTZero 기준)
- [ ] Tutorial 글 100% 코드 블록 2개 이상 포함
- [ ] 평균 워드카운트 1,500-2,000 범위 (현재 2,700~3,900)
- [ ] 문장 길이 표준편차 > 8 (Burstiness 지표)

### 정성적
- [ ] "Here's the thing" 같은 AI 패턴 0회
- [ ] 도입부 첫 10단어에 숫자/반전/고백 포함
- [ ] Dev.to 커뮤니티에 1개 글 테스트 포스팅 시 긍정적 반응
- [ ] 실제 사람이 "AI가 쓴 것 같다"고 느끼지 않음

---

## 다음 단계

1. **scripts/prompts/*.py 수정** - 위 전략 적용
2. **generate_posts.py 시스템 프롬프트 수정** - 페르소나, 문장 변주
3. **quality_gate.py 강화** - 코드 블록 체크 FAIL 처리
4. **테스트 생성** - 각 유형별 1개씩 생성하여 검증
5. **Dev.to 테스트 포스팅** - 가장 좋은 글 1개 수동 크로스포스팅

---

**Last Updated**: 2026-02-12
**Next Review**: Phase 1 구현 완료 후
