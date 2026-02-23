# 전면 개편 계획서 (Revamp Plan)

**작성일**: 2026-02-12
**목적**: Tech 전문 블로그로 재탄생 - 글로벌 인사이트, 다국어 접근
**타임라인**: 4-5시간 (1일 완료 가능)

---

## 1. 전략 재정의

### 포지셔닝

**Before**: "AI-powered multilingual blog covering diverse topics"
**After**: **"Global tech insights in English and Korean - where Silicon Valley meets Seoul"**

**핵심 가치 제안**:
- 🌍 **글로벌 tech 정보를 다국어로** - Vercel, Stripe, a16z → 한국어로
- 🇰🇷 **한국 tech 씬을 글로벌에** - 토스, 카카오 → 영어로
- 🎯 **업계 구루 인사이트 큐레이션** - Lenny, Ben Thompson, tech leaders
- 📊 **데이터 기반 분석** - RAG + 커뮤니티 마이닝
- 💎 **고품질 소수정예** - 매일 5개 토픽 (10개 글), 전부 전문가 수준

### 타겟 독자

**영어 독자**:
- Primary: 개발자, 엔지니어, tech enthusiasts
- Secondary: PM, 스타트업 founder
- Geo: US, Europe, Global

**한국어 독자**:
- Primary: 한국 개발자 (영어 자료 부담 느끼는)
- Secondary: Tech 업계 종사자, 스타트업
- Geo: 한국, 한국어권

### 차별화 포인트

| 경쟁사 | 우리 차별화 |
|--------|------------|
| **Dev.to** | 영어만, 커뮤니티 중심 | EN+KO, 큐레이션 + 분석 |
| **GeekNews** | 한국어만, 링크 모음 | 심층 분석, 글로벌 소스 |
| **Velog** | 개인 블로그, 튜토리얼 | 업계 구루 인사이트 종합 |
| **회사 Tech 블로그** | 자사 기술만 | 크로스 플랫폼 비교/분석 |

**우리만의 강점**: "글로벌 tech 인사이트를 한국어로, 한국 tech 씬을 영어로"

---

## 2. 디자인 개편

### 디자인 철학

**키워드**: Minimal, Professional, Content-First, Developer-Friendly

**피할 것**:
- ❌ AI 생성 블로그 템플릿 (너무 generic)
- ❌ 과도한 색상/그라데이션
- ❌ 복잡한 레이아웃
- ❌ 광고 같은 느낌

**지향점**:
- ✅ Stripe처럼 미니멀하고 세련됨
- ✅ Toss처럼 친근하면서 전문적
- ✅ Josh Comeau처럼 typography 중심
- ✅ 읽기에 최적화 (600-700px content width)

### 레이아웃 구조

#### 홈페이지
```
[Logo/Title]                    [EN | KO]

Global Tech Insights
Where Silicon Valley meets Seoul

[Featured Post - Large]
  - 최신/인기 글 1개
  - 큰 이미지 + 제목 + 발췌

[Latest Posts - Grid]
  - 최신 5개 (카드 형태)
  - 이미지 + 제목 + 날짜 + 읽기 시간

[Popular This Week]
  - 주간 인기 5개

[Categories]
  ❌ 제거! (Tech만이니까 불필요)
```

#### 포스트 페이지
```
[Breadcrumb]
Home > [Post Title]

[Post Header]
  - 제목 (large, bold)
  - 메타: 날짜, 읽기 시간, 언어
  - Tags: 기술 스택만 (AWS, React, Go 등)

[Table of Contents - Sticky Sidebar]
  - 섹션 자동 생성
  - 스크롤 시 현재 위치 하이라이트

[Content - Typography First]
  - Max-width: 680px (읽기 최적)
  - Line-height: 1.75
  - Font: System fonts (San Francisco, Segoe UI, etc.)
  - Code blocks: Syntax highlighting
  - Tables: 깔끔한 border
  - 이미지: Full-width available

[Footer]
  - Share buttons (minimal)
  - Related posts (2-3개)
  - Newsletter signup (나중에)
```

### 색상 팔레트 (제안)

**Option A: Monochrome Professional**
```
Background: #FFFFFF
Text: #1a1a1a
Accent: #0066FF (links)
Code background: #f6f8fa
Border: #e1e4e8
```

**Option B: Dark Mode First**
```
Background: #0d1117
Text: #c9d1d9
Accent: #58a6ff
Code background: #161b22
Border: #30363d
```

**Option C: Toss-Inspired** (추천!)
```
Background: #FAFAFA
Text: #191919
Primary: #3182F6 (Toss Blue)
Secondary: #F04452 (Accent)
Code: #F7F8F9
Border: #E5E8EB
```

### Typography

**제목**:
```css
H1: 48px, Bold, -0.02em letter-spacing
H2: 32px, Bold, -0.01em
H3: 24px, Semibold
```

**본문**:
```css
Body: 18px/1.75, Regular
Code: JetBrains Mono, 16px
```

### 차별화 디자인 요소

**1. Reading Progress Bar**
```
페이지 상단에 얇은 progress bar
스크롤하면 진행도 표시 (Stripe처럼)
```

**2. Estimated Reading Time**
```
"8 min read" 표시 (Medium처럼)
실제 읽기 시간 기반
```

**3. Code Block Enhancement**
```
- Copy 버튼 (우측 상단)
- 언어 표시 (좌측 상단)
- Line numbers (optional)
```

**4. TOC Sidebar (Desktop)**
```
우측에 sticky TOC
현재 섹션 하이라이트
Smooth scroll
```

**5. Language Switcher**
```
우측 상단에 깔끔하게
EN ↔ KO 토글
같은 글의 다른 언어 버전으로 이동
```

**6. Minimal Footer**
```
No clutter. Just:
- About (간단히)
- GitHub
- RSS
```

---

## 3. 콘텐츠 아키텍처

### 카테고리 구조

**제거**:
- sports, entertainment, society, business

**유지**:
- **Tech** (단일 카테고리)

**대신 분류**:
- **태그**: 기술 스택 기반 (React, Go, AWS, Kubernetes, etc.)
- **페이지**: Latest, Popular, Archive
- **검색**: 전체 텍스트 검색 (Algolia 또는 Pagefind)

### URL 구조

```
/en/slug/                 # 영어 글
/ko/slug/                 # 한국어 글 (같은 slug)

예시:
/en/react-server-components/
/ko/react-server-components/

hreflang 태그로 연결:
<link rel="alternate" hreflang="ko" href="/ko/react-server-components/" />
<link rel="alternate" hreflang="en" href="/en/react-server-components/" />
```

### Hugo 설정 변경

```toml
# hugo.toml
[languages]
  [languages.en]
    languageName = "English"
    weight = 1
    contentDir = "content/en"

  [languages.ko]
    languageName = "한국어"
    weight = 2
    contentDir = "content/ko"

# Remove category taxonomy, use tags only
[taxonomies]
  tag = "tags"
```

---

## 4. 콘텐츠 소스 종합 전략

### 미국/글로벌 소스

#### 업계 구루 & Newsletter
| 소스 | 전문 분야 | 접근 방법 |
|------|-----------|-----------|
| **Lenny Rachitsky** | Product, PM, Growth | Newsletter (무료 글), Podcast show notes |
| **Ben Thompson** | Strategy, Business | Stratechery (무료 글만) |
| **Gergely Orosz** | Engineering, Career | Pragmatic Engineer (무료 글) |
| **a16z** | VC, Startups, AI | Blog, Podcast transcripts |
| **Acquired** | Company analysis | Show notes (매우 상세) |

#### Tech 회사 블로그
| 회사 | 강점 | RSS |
|------|------|-----|
| **Vercel** | Next.js, Edge, 웹 성능 | ✅ |
| **Stripe** | Payments, API 설계, 인프라 | ✅ |
| **Netlify** | JAMstack, DevOps, CI/CD | ✅ |
| **GitHub** | Git, Actions, Copilot | ✅ |
| **Cloudflare** | CDN, Workers, Security | ✅ |
| **AWS** | 클라우드 아키텍처 | ✅ |

#### 커뮤니티
| 커뮤니티 | API/RSS | 활용 방법 |
|----------|---------|-----------|
| **HackerNews** | Algolia API | Top stories + 댓글 |
| **Dev.to** | Public API | Top articles + 댓글 |
| **Product Hunt** | REST API | 신제품 트렌드 |
| **Lobsters** | JSON feed | Tech 토론 |

### 한국 소스

#### Tech 회사 블로그
| 회사 | 강점 | RSS |
|------|------|-----|
| **토스** | 핀테크, 프론트엔드, UX | ✅ |
| **카카오** | 대규모 시스템, 검색, AI | ✅ |
| **우아한형제들** | 배달 서비스, MSA | ✅ |
| **네이버 D2** | 검색, AI, 오픈소스 | ✅ |
| **라인** | 메시징, 글로벌 서비스 | ✅ |
| **당근** | 로컬 서비스, 커뮤니티 | ✅ |
| **컬리** | 이커머스, 물류 | ✅ |

#### 커뮤니티
| 커뮤니티 | API/RSS | 활용 방법 |
|----------|---------|-----------|
| **GeekNews** | RSS | 인기글, 토론 |
| **Velog** | RSS (trending) | 개발 튜토리얼, 경험담 |
| **Okky** | 크롤링 (API 없음) | Q&A, 실무 경험 |
| **Disquiet** | RSS 가능성 | 프로덕트, 스타트업 |

#### 개인 블로그 (한국)
- **Outsider** (https://blog.outsider.ne.kr)
- **44bits** (https://www.44bits.io)
- **Seongwon Jeong** (https://si.mpli.st)

### 추가 추천 소스

#### YouTube → Transcript
| 채널 | 내용 | Transcript |
|------|------|------------|
| **Fireship** | Tech news, tutorials | ✅ Auto-generated |
| **ThePrimeagen** | Programming, tools | ✅ |
| **개발바닥** (KR) | 개발 토론 | ✅ |
| **나는 프로그래머다** (KR) | 커리어, 인터뷰 | ✅ |

#### Podcast → Show Notes
| Podcast | 형태 | 활용 |
|---------|------|------|
| **Lenny's Podcast** | Show notes 상세 | 핵심 인사이트 추출 |
| **Acquired** | 2-3시간 에피소드 → 상세 notes | 회사 분석 |
| **All-In Podcast** | Tech/VC 토론 | Show notes |

#### Research Papers (선택적)
- **arXiv.org** - AI/ML 최신 연구
- **Papers with Code** - 구현 포함 논문

---

## 5. 파이프라인 재설계

### 키워드 큐레이션 변경

**keyword_curator.py 수정**:

```python
# 현재: EN 50% + KO 50% 별도 키워드
# 변경: 글로벌 Tech 키워드 100% (영어 기준)

# 각 키워드를 EN + KO 둘 다 생성
# 예: "React Server Components" → EN 글 + KO 글

소스:
- HackerNews (US tech)
- GeekNews (KR tech + 글로벌)
- Dev.to (영어 커뮤니티)
- Velog trending (한국 트렌드)
- 회사 블로그 RSS (Vercel, Stripe, 토스, 카카오)
```

**출력**:
```json
{
  "keyword": "React Server Components",
  "langs": ["en", "ko"],  // 둘 다 생성
  "category": "tech",
  "sources": {
    "guru": "Lenny mentioned RSC adoption in Feb 2026 newsletter",
    "company": "Vercel blog: RSC performance improvements",
    "community": "HN discussion with 234 comments"
  }
}
```

### 콘텐츠 생성 변경

**generate_posts.py 수정**:

```python
for topic in topics:
    # Step 1: RAG (1번만, 언어 무관)
    rag_context = rag_pipeline.get_context(topic['keyword'])

    # Step 2: 커뮤니티 (1번만)
    # - HN (영어)
    # - GeekNews (한국어도 포함)
    # - Dev.to (영어)
    community_insights = community_miner.get_insights(topic['keyword'])

    # Step 3: 구루 인사이트 (새로 추가!)
    guru_insights = guru_miner.get_insights(topic['keyword'])
    # - Lenny's Newsletter 검색
    # - a16z blog 검색
    # - Acquired show notes 검색

    # Step 4: Few-Shot Examples (언어별)
    en_examples = get_examples('en')  # Vercel, Stripe 스타일
    ko_examples = get_examples('ko')  # 토스, 카카오 스타일

    # Step 5: EN 글 생성
    en_post = generate_draft(
        topic,
        lang='en',
        context=rag_context + community_insights + guru_insights,
        examples=en_examples
    )

    # Step 6: KO 글 생성 (병렬!)
    ko_post = generate_draft(
        topic,
        lang='ko',
        context=rag_context + community_insights + guru_insights,  # 같은 context!
        examples=ko_examples
    )
```

**핵심**:
- RAG/커뮤니티/구루 인사이트는 **1번만** 수집
- EN + KO에 **재사용** → 비용 절감 + 일관성

### API 비용 재계산

**현재** (Phase 1-3):
```
5 EN 키워드 → RAG 5번 + 커뮤니티 5번 + Draft/Edit 5번 = $1.40
5 KO 키워드 → RAG 5번 + 커뮤니티 5번 + Draft/Edit 5번 = $1.40
합계: $2.80/일
```

**개편 후**:
```
5 글로벌 키워드 →
  - RAG 5번 (영어)
  - 커뮤니티 5번 (EN + KO 통합)
  - 구루 5번 (새로 추가)
  - Draft/Edit EN 5번
  - Draft/Edit KO 5번 (context 재사용!)

비용:
- RAG: 5 × $0.10 = $0.50
- 커뮤니티: 5 × $0.03 = $0.15
- 구루: 5 × $0.05 = $0.25 (새로 추가)
- Draft/Edit: 10 × $0.15 = $1.50
합계: $2.40/일 (현재보다 저렴!)

월간: $2.40 × 30 = $72/월
```

---

## 6. 새로운 컴포넌트

### guru_miner.py (새로 추가)

```python
"""
Guru Insights Miner

Mines insights from industry thought leaders:
- Lenny's Newsletter
- Stratechery
- Pragmatic Engineer
- a16z Blog
- Acquired Show Notes
"""

def search_lenny(keyword):
    # Lenny's Newsletter RSS 검색
    # 키워드 관련 글 찾기
    # 핵심 인사이트 추출

def search_a16z(keyword):
    # a16z blog RSS
    # VC 관점의 분석

def get_guru_insights(keyword):
    # 여러 소스 통합
    # Claude로 핵심 인사이트 추출
    # "According to Lenny Rachitsky..." 형태로 반환
```

### few_shot_examples.py (새로 추가)

```python
"""
Few-Shot Writing Examples

High-quality tech writing examples for style learning.
"""

EN_ANALYSIS_EXAMPLES = [
    {
        "source": "Vercel Blog",
        "title": "How we optimized package installs in Turbopack",
        "opening": "Three months ago, our build times hit 14 minutes...",
        "style_notes": "Direct opening, specific numbers, problem→solution"
    },
    {
        "source": "Stripe Blog",
        "title": "Designing robust and predictable APIs with idempotency",
        "opening": "A payment fails. The user retries. Now they're charged twice...",
        "style_notes": "Scenario-based opening, real problem"
    }
]

KO_ANALYSIS_EXAMPLES = [
    {
        "source": "토스 Tech Blog",
        "title": "토스증권 렌더링 최적화로 초기 렌더 속도 1.5배 개선하기",
        "opening": "2분이면 끝나야 할 화면 로딩이 10초씩 걸렸어요...",
        "style_notes": "문제 상황 직접 제시, 구체적 숫자"
    }
]
```

### korean_community_miner.py (확장)

```python
"""
Korean Community Mining

GeekNews, Velog, Okky에서 인사이트 추출
"""

def search_geeknews(keyword):
    # RSS에서 인기글 검색
    # 토론 댓글 추출

def search_velog(keyword):
    # Trending posts 크롤링
    # 개발자 경험담 추출
```

---

## 7. 실행 계획

### Phase A: 전략 문서화 (완료!)
- [x] revamp-plan.md 작성
- [ ] CLAUDE.md 업데이트
- [ ] README.md 업데이트

### Phase B: 기존 콘텐츠 정리 (10분)

```bash
# 1. 백업 (git에 있으니 괜찮지만 확실하게)
git tag archive/before-revamp

# 2. 전체 삭제
rm -rf content/en/* content/ko/*

# 3. .gitkeep 추가
touch content/en/.gitkeep content/ko/.gitkeep

# 4. topics_queue.json 초기화
# 기존 큐 백업 후 새로 시작
```

### Phase C: 디자인 구현 (2-3시간)

**Step 1: Hugo 테마 선택**
- Option A: 기존 테마 대폭 커스터마이징
- Option B: 처음부터 커스텀 테마 (추천!)

**Step 2: 레이아웃 작성**
```
layouts/
  _default/
    baseof.html          # 기본 템플릿
    list.html            # 홈페이지, 아카이브
    single.html          # 포스트 페이지
  partials/
    header.html          # 헤더 (logo, 언어 스위처)
    footer.html          # 미니멀 푸터
    toc.html             # 목차 사이드바
    reading-progress.html # 읽기 진행 바
  shortcodes/
    code-block.html      # 개선된 코드 블록
```

**Step 3: CSS 작성**
```
assets/css/
  main.css            # 메인 스타일
  typography.css      # 폰트, 읽기 최적화
  code.css            # 코드 블록 스타일
  dark-mode.css       # 다크모드 (optional)
```

**Step 4: 필수 기능**
- Reading progress bar
- TOC sidebar (sticky)
- Code copy button
- 언어 스위처
- Responsive (mobile-first)

### Phase D: 파이프라인 업데이트 (2시간)

**Step 1: guru_miner.py 작성** (30분)
- Lenny, a16z, Acquired 인사이트 추출

**Step 2: korean_community_miner.py** (30분)
- GeekNews RSS
- Velog trending 크롤링

**Step 3: few_shot_examples.py** (30분)
- Vercel, Stripe, 토스 예시 수집
- Claude로 스타일 분석

**Step 4: generate_posts.py 병렬 생성 로직** (30분)
- EN + KO 동시 생성
- Context 재사용

**Step 5: keyword_curator.py 수정** (30분)
- Tech only
- 글로벌 소스 중심
- GeekNews 추가

### Phase E: 첫 배치 생성 (30분)

```bash
# 1. 새 키워드 5개 큐레이션
python scripts/keyword_curator.py --count 10 --auto

# 2. 첫 배치 생성 (5 topics × 2 langs = 10 posts)
python scripts/generate_posts.py --count 5

# 3. 수동 품질 검증
# - AI 패턴 체크
# - RAG/커뮤니티 반영 확인
# - Few-shot 효과 확인

# 4. 배포
git add .
git commit -m "🎉 Revamp: First batch of high-quality tech posts"
git push
```

---

## 8. 타임라인

| Phase | 작업 | 시간 | 누적 |
|-------|------|------|------|
| **A** | 전략 문서화 | 30분 | 0.5h |
| **B** | 기존 콘텐츠 삭제 | 10분 | 0.7h |
| **C** | 디자인 구현 | 2-3시간 | 3h |
| **D** | 파이프라인 업데이트 | 2시간 | 5h |
| **E** | 첫 배치 생성 | 30분 | 5.5h |

**총 소요**: **5-6시간** (1일 완료 가능)

---

## 9. 성공 지표

### 즉시 측정 가능

- [ ] 기존 198개 포스트 삭제 완료
- [ ] 새 디자인 배포 (모바일/데스크탑 확인)
- [ ] 첫 10개 글 생성 (5 topics × 2 langs)
- [ ] AI 패턴 평균 < 2개/글
- [ ] RAG 출처 인용 100%
- [ ] Few-shot 효과 확인

### 1주일 후

- [ ] 35개 글 발행 (5 topics/day × 7 days)
- [ ] 품질 일관성 유지 (7-8점/10점)
- [ ] AdSense 재신청
- [ ] Google Search Console 인덱싱 확인

### 1개월 후

- [ ] 150개 글 (고품질)
- [ ] AdSense 승인
- [ ] Dev.to 크로스포스팅 1-2개 테스트
- [ ] DA > 10
- [ ] 월간 트래픽 > 5k PV

---

## 10. 리스크 & 완화

### 리스크 1: 기존 트래픽 손실

**현실**: 현재 트래픽 거의 없음 (DA 0)
**완화**: 손실 최소, 새 출발 기회

### 리스크 2: 디자인 구현 시간

**현실**: CSS/Hugo 작업 오래 걸릴 수 있음
**완화**:
- 최소 기능으로 시작 (MVP)
- 점진적 개선
- 또는 깔끔한 Hugo 테마 선택 후 약간 커스터마이징

### 리스크 3: 파이프라인 버그

**현실**: 병렬 생성 로직 복잡
**완화**:
- 단계별 테스트
- 에러 핸들링 강화
- Dry-run 모드

---

## 11. 즉시 결정 필요

### Q1: 디자인 접근법

**Option A**: 기존 Hugo 테마 커스터마이징 (빠름, 2시간)
**Option B**: 완전 커스텀 테마 (느림, 4-5시간, 독창성 ↑)

→ **추천**: Option A (속도 우선, 나중에 개선)

### Q2: 기존 콘텐츠

**Option A**: 전부 삭제 (깔끔)
**Option B**: 상위 20개 수동 선별 후 보존

→ **추천**: Option A (전부 삭제, 새 출발)

### Q3: 첫 배치 생성 시점

**Option A**: 디자인 완성 후 (전체 완성)
**Option B**: 디자인과 병렬 (빠른 검증)

→ **추천**: Option B (파이프라인 먼저 테스트)

---

## 다음 단계

**지금 바로**:
1. 전략 확정 (위 계획 승인)
2. Phase B 실행 (기존 콘텐츠 삭제)
3. Phase D 시작 (파이프라인 먼저 - 디자인 병렬 가능)

**어떻게 진행할까요?**