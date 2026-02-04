# Phase 3.5: 콘텐츠 품질 & 카테고리 전략 개선

**목표:** 레퍼런스 블로그 수준의 품질 달성 + Tech 중심 수익화 전략
**기간:** 1-2주
**핵심:** 모든 글이 아닌, **글 타입별 차별화 전략**

---

## 🎯 핵심 인사이트: 글 타입별 접근

### 레퍼런스 블로그 분석 결과

#### Memory Hub 패턴
- **긴 튜토리얼** (3,000 단어): 10-15%만 해당
  - OpenClaw Heartbeat 같은 신기술 심층 분석
  - 코드 예제 + 단계별 가이드 + 비교표

- **중간 분석글** (1,500-2,000 단어): 60-70%
  - Tech News, 트렌드 분석
  - 개념 설명 + 의견

- **짧은 뉴스** (800-1,200 단어): 15-20%
  - 속보성 뉴스
  - 간단한 요약

#### Digital Bourgeois 패턴
- **전문 분석글** (1,200-1,500 단어): 대부분
  - RAG vs Fine-tuning 비교
  - 아키텍처 설명

- **짧은 소식** (500-800 단어): 일부
  - 신제품 발표
  - 간단한 업데이트

**결론: 모든 글이 3,000 단어는 아님. 토픽에 따라 차등 적용!**

---

## 📋 글 타입 분류 시스템

### Type A: 심층 튜토리얼 (15%) ⭐⭐⭐⭐⭐
**대상 토픽:**
- 새로운 기술/프레임워크 (OpenClaw, 새 AI 모델)
- 복잡한 개념 (RAG, Fine-tuning, Kubernetes)
- 실전 가이드 (배포, 설정, 통합)

**요구사항:**
- 단어 수: 2,500-3,500
- 포함 요소:
  - ✅ 코드 예제 (2-3개)
  - ✅ 비교표 (vs 대안)
  - ✅ 단계별 가이드
  - ✅ 실전 팁
  - ✅ CTA (시도해보기)

**예시 토픽:**
```
- "Kubernetes 클러스터 구축 완전 가이드"
- "ChatGPT vs Claude vs Gemini 완벽 비교"
- "AWS Lambda로 서버리스 API 만들기"
```

**프롬프트 템플릿:**
```python
TUTORIAL_PROMPT = """
Write a comprehensive 2,500-3,500 word tutorial on {topic}.

MUST INCLUDE:
1. Introduction (200 words)
   - What is {topic}?
   - Why is it important?
   - Who should use it?

2. Background & Context (400 words)
   - History/Evolution
   - Current landscape
   - Key challenges

3. Comparison Table (300 words)
   Create a markdown table comparing {topic} with 2-3 alternatives:
   | Feature | {topic} | Alternative 1 | Alternative 2 |
   |---------|---------|---------------|---------------|
   | Cost | ... | ... | ... |
   | Ease of Use | ... | ... | ... |
   | Performance | ... | ... | ... |

4. Step-by-Step Implementation (1,000 words)
   - Prerequisites
   - Installation steps with code examples
   - Configuration examples
   - Testing & verification

5. Code Examples (500 words)
   Include 2-3 practical code snippets:
   ```language
   # Example code here
   ```
   Explain each example clearly.

6. Best Practices & Tips (400 words)
   - Common pitfalls to avoid
   - Performance optimization tips
   - Security considerations

7. Conclusion & Next Steps (200 words)
   - Summary of key points
   - Call-to-action: "Try it today"
   - Links to official docs/resources

Structure with clear H2/H3 headings.
"""
```

---

### Type B: 표준 분석글 (60%) ⭐⭐⭐⭐
**대상 토픽:**
- Tech News (새 제품 발표, 업데이트)
- 트렌드 분석 (AI 시장 동향)
- 개념 설명 (벡터 DB, RAG)

**요구사항:**
- 단어 수: 1,500-2,000
- 포함 요소:
  - ✅ 명확한 구조 (3-4 섹션)
  - ✅ 비교 포인트 (간단한 리스트나 표)
  - ⚠️ 코드 예제 (선택적, 필요시만)
  - ✅ 실용적 인사이트

**예시 토픽:**
```
- "2026년 AI 트렌드 전망"
- "Google의 새로운 Gemini 2.0 발표"
- "벡터 데이터베이스란 무엇인가?"
```

**프롬프트 템플릿:**
```python
ANALYSIS_PROMPT = """
Write a 1,500-2,000 word analysis article on {topic}.

STRUCTURE:
1. Introduction (250 words)
   - Hook: What's happening?
   - Why it matters
   - Key takeaway preview

2. Background (300 words)
   - Context needed to understand
   - Previous developments

3. Main Analysis (700 words)
   - Key features/points (3-5 items)
   - Comparison with alternatives (bullet list or simple table)
   - Impact on industry/users

4. Practical Implications (400 words)
   - Who should care?
   - How to prepare/adapt
   - Opportunities and challenges

5. Conclusion (250 words)
   - Summary
   - Future outlook
   - Reader takeaway

Include comparison elements:
- Either a markdown table OR
- Bullet-point comparison list

Use H2/H3 headings for clear structure.
"""
```

---

### Type C: 짧은 뉴스 (25%) ⭐⭐⭐
**대상 토픽:**
- 속보성 뉴스 (제품 출시, 인수합병)
- 이벤트 소식 (컨퍼런스, 세미나)
- 간단한 업데이트

**요구사항:**
- 단어 수: 800-1,200
- 포함 요소:
  - ✅ 핵심 사실 전달
  - ✅ 간단한 배경
  - ⚠️ 상세 분석 불필요

**예시 토픽:**
```
- "Anthropic, Claude 4 출시"
- "Microsoft, OpenAI에 100억 달러 추가 투자"
- "AWS re:Invent 2026 주요 발표"
```

**프롬프트 템플릿:**
```python
NEWS_PROMPT = """
Write a concise 800-1,200 word news article on {topic}.

STRUCTURE:
1. Lead (150 words)
   - Who, What, When, Where, Why
   - Most important information first

2. Details (400 words)
   - Key features/announcements
   - Important numbers/facts
   - Quotes (if available)

3. Context (300 words)
   - Background information
   - Why this matters
   - Connection to broader trends

4. Impact (200 words)
   - Who is affected?
   - What changes?
   - Next steps to watch

Keep it factual and concise. Use bullet points for lists.
"""
```

---

## 🤖 자동 분류 시스템

### 토픽별 자동 타입 결정

```python
# scripts/utils/content_classifier.py

def classify_content_type(topic, keywords, category):
    """
    토픽을 분석해서 Type A/B/C 자동 분류
    """
    topic_lower = topic.lower()
    keywords_str = ' '.join(keywords).lower()

    # Type A: 심층 튜토리얼 (15%)
    tutorial_indicators = [
        'how to', 'guide', 'tutorial', 'step by step',
        'implementation', 'setup', 'install', 'configure',
        'complete guide', '완전 가이드', '완벽 가이드'
    ]

    complex_tech = [
        'kubernetes', 'docker', 'terraform', 'aws',
        'architecture', 'deployment', 'microservices',
        'rag', 'fine-tuning', 'ml ops'
    ]

    if (any(ind in topic_lower for ind in tutorial_indicators) or
        any(tech in keywords_str for tech in complex_tech)):
        return 'tutorial'  # Type A

    # Type C: 짧은 뉴스 (25%)
    news_indicators = [
        'announces', 'launches', 'releases', '발표', '출시',
        'acquires', 'funding', 'investment', '인수', '투자',
        'breaking', 'update', 'news'
    ]

    if any(ind in topic_lower for ind in news_indicators):
        return 'news'  # Type C

    # Type B: 표준 분석 (기본값, 60%)
    return 'analysis'  # Type B


# 타입별 설정
CONTENT_TYPE_CONFIG = {
    'tutorial': {
        'word_count': (2500, 3500),
        'prompt_template': 'TUTORIAL_PROMPT',
        'priority': 1.5,  # 중요도 높음
        'requires': ['code_examples', 'comparison_table', 'step_guide', 'tips']
    },
    'analysis': {
        'word_count': (1500, 2000),
        'prompt_template': 'ANALYSIS_PROMPT',
        'priority': 1.0,
        'requires': ['comparison_list', 'insights']
    },
    'news': {
        'word_count': (800, 1200),
        'prompt_template': 'NEWS_PROMPT',
        'priority': 0.8,
        'requires': ['facts', 'context']
    }
}
```

---

## 🎯 카테고리 전략 통합

### Phase 1: Hybrid 전략 + 글 타입 분류

```python
# scripts/keyword_curator.py 개선

CATEGORY_WEIGHTS = {
    'tech': 0.40,
    'business': 0.20,
    'society': 0.15,
    'sports': 0.15,
    'entertainment': 0.10
}

# Tech 내부 타입 분포
TECH_TYPE_DISTRIBUTION = {
    'tutorial': 0.15,   # 심층 가이드
    'analysis': 0.60,   # 표준 분석
    'news': 0.25        # 짧은 뉴스
}

# 다른 카테고리는 대부분 Analysis/News
OTHER_TYPE_DISTRIBUTION = {
    'analysis': 0.70,
    'news': 0.30
}
```

---

## 📊 예상 콘텐츠 분포

### 일 6개 게시물 기준

**카테고리 분포:**
```
Tech: 2-3개 (40%)
  - Tutorial: 0-1개 (Type A)
  - Analysis: 1-2개 (Type B)
  - News: 0-1개 (Type C)

Business: 1-2개 (20%)
  - Analysis: 1개
  - News: 0-1개

Society: 1개 (15%)
Sports: 1개 (15%)
Entertainment: 0-1개 (10%)
```

**주간 예상 (42개 게시물):**
```
Type A (Tutorial): 4-6개 (15%)
  - 평균 3,000 단어
  - 코드 + 테이블 + 가이드

Type B (Analysis): 25-28개 (60%)
  - 평균 1,700 단어
  - 구조화된 분석 + 비교

Type C (News): 10-12개 (25%)
  - 평균 1,000 단어
  - 간결한 사실 전달
```

**평균 글 길이:**
```
(6 × 3,000) + (25 × 1,700) + (10 × 1,000) / 42
= 18,000 + 42,500 + 10,000 / 42
= 70,500 / 42
= 1,678 단어/글

현재: 1,200 단어/글
개선 후: 1,678 단어/글 (+40%)
```

---

## 🚀 구현 로드맵

### Week 1: 기반 시스템 구축

#### Day 1-2: 콘텐츠 분류 시스템
```bash
# 새 파일 생성
scripts/utils/content_classifier.py
  - classify_content_type()
  - CONTENT_TYPE_CONFIG

# 기존 파일 수정
scripts/keyword_curator.py
  - CATEGORY_WEIGHTS 조정 (Tech 40%)
  - 타입별 분류 통합
```

#### Day 3-4: 타입별 프롬프트 템플릿
```bash
scripts/prompts/
  - tutorial_prompt.py
  - analysis_prompt.py
  - news_prompt.py

scripts/generate_posts.py
  - 타입별 프롬프트 선택 로직
  - 단어 수 동적 조정
```

#### Day 5-7: 테스트 & 검증
```bash
# 각 타입별 3-5개 게시물 생성 테스트
python scripts/generate_posts.py --test-types

# 품질 확인
- Type A: 코드/테이블/가이드 포함?
- Type B: 구조화된 분석?
- Type C: 간결한 뉴스?
```

---

### Week 2: 최적화 & 배포

#### Day 8-10: Tech 서브카테고리 구조
```bash
# Hugo 구조 생성
content/
  ├── en/tech/
  │   ├── ai-ml/
  │   ├── cloud/
  │   ├── development/
  │   └── data/
  ├── ko/tech/
  └── ja/tech/

# 자동 분류 로직
scripts/utils/tech_categorizer.py
```

#### Day 11-12: 품질 게이트 강화
```bash
scripts/quality_gate.py 개선
  - Type A 검증: 코드 블록 2개 이상?
  - Type A 검증: 테이블 1개 이상?
  - 타입별 단어 수 검증
```

#### Day 13-14: 배포 & 모니터링
```bash
# 워크플로우 업데이트
.github/workflows/daily-content.yml
  - 타입별 생성 지원

# 첫 주 자동 생성
- 월요일부터 매일 4 PM 자동 실행
- 타입 분포 모니터링
```

---

## 📈 예상 효과

### 콘텐츠 품질 지표

| 지표 | 현재 | Phase 3.5 후 | 변화 |
|------|------|-------------|------|
| 평균 글 길이 | 1,200 단어 | 1,678 단어 | +40% |
| Tech 비중 | 15% | 40% | +167% |
| 심층 튜토리얼 | 0% | 15% | New |
| 코드 예제 보유 | 0% | 15% | New |
| 비교표 포함 | 0% | 30% | New |

### 트래픽 & 수익 예측

| 지표 | 1개월 후 | 3개월 후 | 6개월 후 |
|------|---------|---------|---------|
| 월 게시물 | 180개 | 540개 | 1,080개 |
| Tech 게시물 | 72개 | 216개 | 432개 |
| 월 PV | 50K | 150K | 400K |
| 광고 CPM | $4 | $6 | $8 |
| 월 예상 수익 | $200 | $900 | $3,200 |

### SEO 효과

```
긴 글 (2,000+ 단어):
- Google 순위: 평균 10-15위 상승
- 체류 시간: 2분 → 4분 (+100%)
- 이탈률: 60% → 45% (-25%)

코드 예제 포함:
- Featured Snippet 노출: +40%
- 개발자 트래픽: +80%

비교표 포함:
- "vs" 키워드 순위: 상위 20위
- 정보성 검색 유입: +60%
```

---

## ⚠️ 주의사항

### 모든 글에 모든 요소 불필요

❌ **잘못된 접근:**
```
모든 게시물에 코드 + 테이블 + 가이드 강제
→ 부자연스러움, 품질 저하
```

✅ **올바른 접근:**
```
토픽에 맞게 자동 분류 → 타입별 템플릿 적용
- Tutorial 토픽 → 코드 + 테이블 + 가이드
- News 토픽 → 간결한 사실 전달
- Analysis 토픽 → 구조화된 분석 + 비교
```

### Claude API 비용 관리

**현재 (평균 1,200 단어):**
- 일 6개 × $0.15 = $0.90/일
- 월: $27

**Phase 3.5 후 (평균 1,678 단어):**
- Type A (3,000 단어): 0.8개 × $0.30 = $0.24
- Type B (1,700 단어): 3.6개 × $0.17 = $0.61
- Type C (1,000 단어): 1.6개 × $0.10 = $0.16
- 일 6개 = $1.01/일
- 월: $30.30 (+12%)

**ROI:**
- 비용 증가: +$3.30/월
- 예상 수익 증가: +$200/월 (1개월 후)
- ROI: 6,000%

---

## 🎯 최종 요약

### 핵심 전략
**"모든 글을 3,000 단어로 만들지 않는다. 토픽에 맞는 타입을 자동 분류해서 차등 적용한다."**

### 3가지 글 타입
1. **Type A (15%)**: 심층 튜토리얼 - 코드 + 테이블 + 가이드
2. **Type B (60%)**: 표준 분석 - 구조화된 분석 + 비교
3. **Type C (25%)**: 짧은 뉴스 - 간결한 사실 전달

### 카테고리 전략
- **Tech 40%** (수익화 핵심)
- **Business 20%** (지원)
- **Others 40%** (트래픽 다양성)

### 예상 결과
- 평균 글 길이: +40%
- Tech 비중: +167%
- 월 예상 수익 (3개월): $900
- API 비용 증가: +12% (완전히 감당 가능)

### 차별화 포인트
- 레퍼런스: 수동 편집으로 품질 확보
- **우리: AI 자동 분류 + 타입별 템플릿으로 품질 확보**

---

**바로 Week 1 시작할까요?**
- Day 1-2: 콘텐츠 분류 시스템 구축
- Day 3-4: 타입별 프롬프트 템플릿
- Day 5-7: 테스트 & 검증
