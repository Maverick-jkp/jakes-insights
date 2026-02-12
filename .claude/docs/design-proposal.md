# 디자인 제안서 - Tech Blog Revamp

**작성일**: 2026-02-12
**목표**: 전문적이면서 독창적인 tech 블로그 디자인
**참고**: Stripe, Vercel, Toss, Linear

---

## 디자인 철학

**3대 원칙**:
1. **Content-First**: 글이 주인공, 디자인은 조연
2. **Typography-Driven**: 폰트와 여백으로 고급스러움
3. **Functionally Minimal**: 필요한 것만, 하지만 완벽하게

**피할 것**:
- ❌ 블로그 템플릿 느낌 (Wix, WordPress 같은)
- ❌ 과도한 색상/그라데이션
- ❌ 복잡한 네비게이션
- ❌ 광고판 같은 레이아웃

---

## 색상 시스템 (Toss + Stripe 믹스)

### Light Mode (기본)

```css
/* Primary Palette */
--bg-primary: #FAFAFA;        /* 배경 (약간 회색빛) */
--bg-secondary: #FFFFFF;      /* 카드 배경 */
--text-primary: #121212;      /* 본문 (pure black 아님) */
--text-secondary: #666666;    /* 메타데이터 */

/* Accent Colors */
--accent-blue: #3182F6;       /* Toss Blue - 링크, 버튼 */
--accent-purple: #7C3AED;     /* Code, 강조 */
--accent-gray: #E5E8EB;       /* Border, divider */

/* Semantic */
--code-bg: #F7F8F9;
--code-border: #E1E4E8;
--hover-bg: #F3F4F6;
```

### Dark Mode (Optional, 나중에)

```css
--bg-primary: #0D1117;
--bg-secondary: #161B22;
--text-primary: #C9D1D9;
--accent-blue: #58A6FF;
```

---

## Typography System

### 폰트 선택

**제목 (Headings)**:
```css
font-family:
  -apple-system, BlinkMacSystemFont,
  "Segoe UI", "Noto Sans KR",
  "Helvetica Neue", Arial, sans-serif;
font-weight: 700;
letter-spacing: -0.02em;  /* Tight for impact */
```

**본문 (Body)**:
```css
font-family:
  -apple-system, BlinkMacSystemFont,
  "Segoe UI", "Noto Sans KR",
  sans-serif;
font-size: 18px;
line-height: 1.75;       /* 읽기 편안함 */
font-weight: 400;
letter-spacing: -0.003em;
```

**코드 (Code)**:
```css
font-family:
  "JetBrains Mono", "Fira Code",
  "SF Mono", Monaco, monospace;
font-size: 16px;
line-height: 1.6;
```

### 크기 스케일

```css
--text-xs: 14px;    /* Meta, captions */
--text-sm: 16px;    /* Secondary text */
--text-base: 18px;  /* Body */
--text-lg: 20px;    /* Intro paragraph */
--text-xl: 24px;    /* H3 */
--text-2xl: 32px;   /* H2 */
--text-3xl: 48px;   /* H1, Post title */
--text-4xl: 64px;   /* Hero title (홈페이지) */
```

---

## 레이아웃 구조

### 홈페이지 (index.html)

```
┌─────────────────────────────────────────────┐
│ [Logo] Global Tech Insights    [EN | KO]   │ ← Header (sticky)
│                                             │
│ Where Silicon Valley meets Seoul            │ ← Tagline
├─────────────────────────────────────────────┤
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │ [Featured Post - Large Card]          │ │ ← 최신 글 1개
│  │                                       │ │   (큰 이미지 + 제목)
│  │  [Image - Full Width]                 │ │
│  │                                       │ │
│  │  Title (48px, bold)                   │ │
│  │  Excerpt (2 lines)                    │ │
│  │  8 min read · Feb 12                  │ │
│  └───────────────────────────────────────┘ │
│                                             │
│  Latest Posts                               │ ← Section title
│  ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│  │ [Card]  │ │ [Card]  │ │ [Card]  │      │ ← Grid (3 cols)
│  │ Image   │ │ Image   │ │ Image   │      │
│  │ Title   │ │ Title   │ │ Title   │      │
│  │ 5 min   │ │ 7 min   │ │ 12 min  │      │
│  └─────────┘ └─────────┘ └─────────┘      │
│                                             │
│  ┌─────────┐ ┌─────────┐                  │
│  │ [Card]  │ │ [Card]  │                  │
│  └─────────┘ └─────────┘                  │
│                                             │
│  [Load More] or Pagination                  │
│                                             │
├─────────────────────────────────────────────┤
│ Footer (minimal)                            │
│ About · GitHub · RSS                        │
└─────────────────────────────────────────────┘
```

### 포스트 페이지 (single.html)

```
Desktop:
┌────────────────┬─────────────────────────┬──────────┐
│ [Header]       │                         │          │
├────────────────┴─────────────────────────┴──────────┤
│                │                         │          │
│                │ [Post Header]           │ [TOC]    │ ← Sticky
│                │ Title (48px)            │ - Intro  │
│                │ Feb 12 · 8 min · EN     │ - How..  │
│                │                         │ - What.. │
│                │ ───────────────────     │ - Why... │
│                │                         │          │
│  [Sidebar]     │ [Content]               │          │
│  (empty or     │ Max-width: 680px        │          │
│   related)     │                         │          │
│                │ Typography-focused      │          │
│                │ - Large text            │          │
│                │ - Ample spacing         │          │
│                │ - Code blocks           │          │
│                │ - Tables                │          │
│                │                         │          │
│                │ [Share buttons]         │          │
│                │ [Related posts]         │          │
│                │                         │          │
│  120px         │       680px             │  200px   │
└────────────────┴─────────────────────────┴──────────┘

Mobile:
┌──────────────────────────┐
│ [Header - Collapsed]     │
├──────────────────────────┤
│ Title                    │
│ Meta                     │
│ ─────────────────        │
│                          │
│ [Content]                │
│ Full width - 90vw        │
│                          │
│ [TOC - Collapsible]      │
└──────────────────────────┘
```

---

## 차별화 디자인 요소

### 1. Reading Progress Indicator

**위치**: 페이지 최상단 (fixed)
**스타일**: 얇은 바 (2px), gradient

```css
.reading-progress {
  position: fixed;
  top: 0;
  left: 0;
  width: 0%;  /* JS로 계산 */
  height: 2px;
  background: linear-gradient(90deg, #3182F6 0%, #7C3AED 100%);
  z-index: 9999;
  transition: width 0.1s ease;
}
```

```javascript
// JS
window.addEventListener('scroll', () => {
  const scrolled = (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100;
  document.querySelector('.reading-progress').style.width = scrolled + '%';
});
```

### 2. Enhanced Code Blocks

**특징**:
- 복사 버튼 (우측 상단)
- 언어 표시 (좌측 상단)
- Line numbers (optional)
- Syntax highlighting (Prism.js)

```html
<div class="code-block">
  <div class="code-header">
    <span class="language">python</span>
    <button class="copy-btn">Copy</button>
  </div>
  <pre><code class="language-python">
def hello():
    print("Hello, World!")
  </code></pre>
</div>
```

```css
.code-block {
  position: relative;
  background: var(--code-bg);
  border: 1px solid var(--code-border);
  border-radius: 8px;
  margin: 2rem 0;
  overflow: hidden;
}

.code-header {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 1rem;
  background: #FAFBFC;
  border-bottom: 1px solid var(--code-border);
  font-size: 14px;
}

.copy-btn {
  background: transparent;
  border: 1px solid #D1D5DB;
  padding: 4px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.copy-btn:hover {
  background: #F3F4F6;
  border-color: var(--accent-blue);
}
```

### 3. Sticky Table of Contents (Desktop)

**위치**: 우측 사이드바
**기능**: 현재 섹션 하이라이트, smooth scroll

```html
<aside class="toc-sidebar">
  <nav class="toc">
    <h4>Table of Contents</h4>
    <ul>
      <li><a href="#intro" class="active">Introduction</a></li>
      <li><a href="#background">Background</a></li>
      <li><a href="#analysis">Analysis</a></li>
      <li><a href="#conclusion">Conclusion</a></li>
    </ul>
  </nav>
</aside>
```

```css
.toc-sidebar {
  position: sticky;
  top: 100px;
  width: 200px;
  max-height: calc(100vh - 120px);
  overflow-y: auto;
}

.toc ul {
  list-style: none;
  padding-left: 0;
}

.toc li {
  margin: 0.5rem 0;
}

.toc a {
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s;
  padding-left: 1rem;
  border-left: 2px solid transparent;
}

.toc a.active {
  color: var(--accent-blue);
  border-left-color: var(--accent-blue);
  font-weight: 500;
}

.toc a:hover {
  color: var(--text-primary);
}
```

### 4. 언어 스위처 (Unique)

**컨셉**: 플래그 대신 깔끔한 토글

```html
<div class="lang-switcher">
  <a href="/en/react-server-components/" class="lang-link active">EN</a>
  <span class="separator">/</span>
  <a href="/ko/react-server-components/" class="lang-link">KO</a>
</div>
```

```css
.lang-switcher {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 14px;
  font-weight: 500;
}

.lang-link {
  color: var(--text-secondary);
  text-decoration: none;
  padding: 6px 12px;
  border-radius: 6px;
  transition: all 0.2s;
}

.lang-link:hover {
  background: var(--hover-bg);
  color: var(--text-primary);
}

.lang-link.active {
  color: var(--accent-blue);
  background: rgba(49, 130, 246, 0.1);
}

.separator {
  color: var(--text-secondary);
}
```

### 5. Card Design (홈페이지)

**컨셉**: Subtle shadow, hover lift

```css
.post-card {
  background: var(--bg-secondary);
  border: 1px solid var(--accent-gray);
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
}

.post-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08);
  border-color: var(--accent-blue);
}

.post-card-image {
  width: 100%;
  aspect-ratio: 16/9;
  object-fit: cover;
}

.post-card-content {
  padding: 1.5rem;
}

.post-card-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: var(--text-primary);
  line-height: 1.4;
}

.post-card-meta {
  display: flex;
  gap: 1rem;
  font-size: 14px;
  color: var(--text-secondary);
}
```

---

## 레이아웃 상세

### Header (전체 페이지 공통)

**특징**: Minimal, sticky on scroll

```html
<header class="site-header">
  <div class="container">
    <div class="header-content">
      <div class="logo">
        <h1>Global Tech Insights</h1>
        <span class="tagline">Where Silicon Valley meets Seoul</span>
      </div>

      <nav class="main-nav">
        <a href="/">Latest</a>
        <a href="/popular/">Popular</a>
        <a href="/archive/">Archive</a>
      </nav>

      <div class="header-actions">
        <div class="lang-switcher">
          <a href="/en/" class="active">EN</a>
          <span>/</span>
          <a href="/ko/">KO</a>
        </div>
        <button class="search-btn">🔍</button>
      </div>
    </div>
  </div>
</header>
```

```css
.site-header {
  position: sticky;
  top: 0;
  background: rgba(250, 250, 250, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--accent-gray);
  z-index: 100;
  padding: 1rem 0;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
}

.logo h1 {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
  color: var(--text-primary);
}

.tagline {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 400;
}

.main-nav {
  display: flex;
  gap: 2rem;
}

.main-nav a {
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 15px;
  font-weight: 500;
  transition: color 0.2s;
}

.main-nav a:hover {
  color: var(--accent-blue);
}
```

### 포스트 컨테이너

**특징**: Narrow for readability (Stripe 스타일)

```css
.post-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 4rem 2rem;
  display: grid;
  grid-template-columns: 120px 680px 200px;
  gap: 4rem;
}

/* Content column (중앙) */
.post-content {
  grid-column: 2;
}

/* TOC (우측) */
.toc-sidebar {
  grid-column: 3;
}

/* Mobile */
@media (max-width: 1024px) {
  .post-container {
    grid-template-columns: 1fr;
    gap: 2rem;
    padding: 2rem 1rem;
  }

  .post-content {
    grid-column: 1;
  }

  .toc-sidebar {
    display: none;  /* Mobile에선 숨김 */
  }
}
```

---

## 차별화 요소 (Unique Features)

### 1. Animated Section Divider

**컨셉**: 섹션 사이에 subtle gradient line

```css
.section-divider {
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    var(--accent-blue) 50%,
    transparent 100%
  );
  margin: 4rem 0;
  opacity: 0.3;
}
```

### 2. Pull Quotes (인용 강조)

**컨셉**: Stripe 스타일 큰 따옴표

```css
.pull-quote {
  font-size: 24px;
  line-height: 1.5;
  font-weight: 500;
  color: var(--text-primary);
  margin: 3rem 0;
  padding-left: 2rem;
  border-left: 4px solid var(--accent-blue);
  font-style: italic;
}
```

### 3. Tag Pills (기술 스택)

**컨셉**: 작고 깔끔한 pill 형태

```css
.tag-pill {
  display: inline-block;
  background: var(--hover-bg);
  color: var(--text-secondary);
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.2s;
}

.tag-pill:hover {
  background: var(--accent-blue);
  color: white;
}
```

### 4. Reading Time with Icon

**컨셉**: Visual indicator

```html
<div class="reading-time">
  <svg>...</svg>
  <span>8 min read</span>
</div>
```

```css
.reading-time {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-secondary);
  font-size: 14px;
}

.reading-time svg {
  width: 16px;
  height: 16px;
  opacity: 0.6;
}
```

### 5. Minimal Footer (차별화)

**컨셉**: No clutter, 한 줄

```html
<footer class="site-footer">
  <div class="container">
    <div class="footer-content">
      <p>© 2026 Global Tech Insights</p>
      <nav class="footer-nav">
        <a href="/about/">About</a>
        <a href="https://github.com/..." target="_blank">GitHub</a>
        <a href="/feed.xml">RSS</a>
      </nav>
    </div>
  </div>
</footer>
```

```css
.site-footer {
  border-top: 1px solid var(--accent-gray);
  padding: 2rem 0;
  margin-top: 8rem;
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: var(--text-secondary);
}

.footer-nav {
  display: flex;
  gap: 2rem;
}

.footer-nav a {
  color: var(--text-secondary);
  text-decoration: none;
  transition: color 0.2s;
}

.footer-nav a:hover {
  color: var(--accent-blue);
}
```

---

## 특별 컴포넌트

### Key Takeaways Block

**현재**: 단순 blockquote
**개선**: 박스 스타일, icon

```css
.key-takeaways {
  background: linear-gradient(
    135deg,
    rgba(49, 130, 246, 0.05) 0%,
    rgba(124, 58, 237, 0.05) 100%
  );
  border-left: 4px solid var(--accent-blue);
  border-radius: 8px;
  padding: 1.5rem 2rem;
  margin: 2rem 0;
}

.key-takeaways h4 {
  font-size: 16px;
  font-weight: 600;
  color: var(--accent-blue);
  margin-bottom: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.key-takeaways ul {
  list-style: none;
  padding-left: 0;
}

.key-takeaways li {
  position: relative;
  padding-left: 1.5rem;
  margin-bottom: 0.75rem;
}

.key-takeaways li::before {
  content: "→";
  position: absolute;
  left: 0;
  color: var(--accent-blue);
  font-weight: 700;
}
```

### Comparison Tables

**특징**: 헤더 sticky, hover highlight

```css
table {
  width: 100%;
  border-collapse: collapse;
  margin: 2rem 0;
  font-size: 16px;
}

thead {
  position: sticky;
  top: 60px;  /* Header height */
  background: var(--bg-secondary);
  z-index: 10;
}

th {
  background: var(--hover-bg);
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  border-bottom: 2px solid var(--accent-blue);
}

td {
  padding: 1rem;
  border-bottom: 1px solid var(--accent-gray);
}

tr:hover {
  background: var(--hover-bg);
}
```

---

## 구현 파일 구조

```
layouts/
  _default/
    baseof.html           # 기본 템플릿
    list.html             # 홈페이지
    single.html           # 포스트
  partials/
    head.html             # <head> 태그
    header.html           # 사이트 헤더
    footer.html           # 사이트 푸터
    toc.html              # 목차
    reading-progress.html # 진행 바
    code-block.html       # 코드 블록
    post-card.html        # 포스트 카드 (홈페이지용)
  shortcodes/
    keytakeaways.html     # Key Takeaways 블록

assets/
  css/
    main.css              # 메인 스타일
    variables.css         # CSS 변수
    typography.css        # 폰트 스타일
    components.css        # 컴포넌트 (cards, buttons 등)
    layout.css            # 레이아웃 (grid, flexbox)
    code.css              # 코드 블록 전용
  js/
    reading-progress.js   # 읽기 진행 바
    toc.js                # TOC 하이라이트
    code-copy.js          # 코드 복사
```

---

## 반응형 Breakpoints

```css
/* Mobile */
@media (max-width: 640px) {
  --text-3xl: 36px;  /* Title 작게 */
  .post-container { grid-template-columns: 1fr; }
}

/* Tablet */
@media (min-width: 641px) and (max-width: 1024px) {
  .post-container { grid-template-columns: 1fr 680px 1fr; }
  .toc-sidebar { display: none; }
}

/* Desktop */
@media (min-width: 1025px) {
  .post-container { grid-template-columns: 120px 680px 200px; }
}
```

---

## 다음 단계

**지금 구현할 순서**:
1. ✅ CSS 변수 정의 (variables.css)
2. ✅ 기본 레이아웃 (baseof.html, header, footer)
3. ✅ 홈페이지 (list.html + post-card)
4. ✅ 포스트 페이지 (single.html + TOC)
5. ✅ 특수 컴포넌트 (code blocks, key takeaways)
6. ✅ JS 인터랙션 (progress bar, TOC highlight, copy button)

**예상 시간**: 2-3시간

---

**이 디자인 괜찮아요?** 수정하고 싶은 부분 있으면 말해주세요. 아니면 바로 구현 시작할게요.
