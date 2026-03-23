---
title: "Cloudflare Pages Hugo 블로그 한국어 URL 404 에러 인코딩 문제 해결 실전 기록"
date: 2026-03-23T20:03:46+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-cloud", "cloudflare", "pages", "hugo", "Python"]
description: "Hugo + Cloudflare Pages 배포 후 한국어 URL 404 에러, 퍼센트 인코딩과 라우팅 충돌이 원인입니다. 세 가지 해결법을 효과·복잡도·유지보수 난이도로 비교하고 즉시 적용 가능한 설정"
image: "/images/20260323-cloudflare-pages-hugo-블로그-배포-후.webp"
technologies: ["Python", "Go", "Cloudflare", "Hugo"]
faq:
  - question: "Cloudflare Pages Hugo 블로그 배포 후 한국어 URL 404 에러 왜 생기나요"
    answer: "Cloudflare Pages Hugo 블로그 배포 후 한국어 URL 인코딩 404 에러는 Hugo가 생성하는 파일 경로와 브라우저가 요청하는 URL 사이의 퍼센트 인코딩 처리가 어긋나서 발생합니다. Hugo가 한글 슬러그를 퍼센트 인코딩으로 변환한 폴더명을 Cloudflare CDN이 업로드 과정에서 다시 한번 인코딩하면 이중 인코딩 충돌이 일어납니다. 결과적으로 브라우저 요청 URL과 실제 등록된 파일 경로가 달라져 404가 반환됩니다."
  - question: "Hugo config.toml 한국어 URL 설정 어떻게 해야 하나요"
    answer: "Cloudflare Pages Hugo 블로그 배포 후 한국어 URL 인코딩 404 에러 해결을 위해 config.toml에 hasCJKLanguage = true와 removePathAccents = false를 함께 설정하는 조합이 2026년 기준 가장 안정적입니다. hasCJKLanguage를 설정하지 않으면 Hugo가 한중일 문자를 정확히 처리하지 못해 경고 없이 잘못된 URL 구조를 만들어냅니다. 이 설정은 한 번만 적용하면 이후 모든 한국어 포스트에 자동으로 적용됩니다."
  - question: "Hugo 한국어 포스트 slug 설정 안 하면 어떻게 되나요"
    answer: "Front matter에 slug를 명시하지 않으면 Hugo는 마크다운 파일명을 그대로 URL로 사용합니다. CI/CD 빌드 환경의 로케일 설정에 따라 파일명 처리 방식이 달라질 수 있어 예상치 못한 URL이 생성될 수 있습니다. 안정적인 URL 관리를 위해 각 포스트 Front matter에 영문 slug를 직접 지정하는 것이 권장됩니다."
  - question: "Cloudflare Pages 한국어 블로그 404 에러 진단하는 방법"
    answer: "빌드 후 public 폴더에서 find public -type d 명령으로 실제 디렉토리명을 확인하는 것이 첫 번째 진단 단계입니다. 디렉토리명이 눈에 보이는 한글인지 퍼센트 인코딩된 문자열인지에 따라 적용해야 할 해결책이 달라집니다. Python의 urllib.parse.unquote를 활용하면 인코딩된 경로를 디코딩해서 실제 매핑 상태를 확인할 수 있습니다."
  - question: "Hugo 블로그 기존 한국어 포스트 URL 유지하면서 404 에러 고치는 방법"
    answer: "기존 포스트의 URL을 변경하지 않고 404 에러를 해결하려면 Cloudflare Pages의 _redirects 파일을 활용하는 방법이 적합합니다. 기존 인코딩 URL에서 정상 URL로 리다이렉트 규칙을 추가하면 SEO 영향 없이 양쪽 URL을 모두 유지할 수 있습니다. 다만 포스트가 늘어날수록 리다이렉트 규칙이 누적되어 관리 부담이 생길 수 있어 장기적으로는 config 설정 조합 방식 전환을 권장합니다."
---

Hugo 블로그를 Cloudflare Pages에 올리고 나서 한국어 제목 포스트를 클릭했는데 404가 뜬 적 있죠? 생각보다 많은 개발자들이 겪는 문제예요. URL 인코딩, Hugo 설정, Cloudflare의 라우팅 처리 방식이 맞물려 있어서 원인을 찾기가 쉽지 않아요.

이 글에서는 실제 에러 재현부터 해결까지, 데이터 기반으로 짚어봐요.

- Hugo가 한국어 제목을 URL로 변환하는 방식과 그 함정
- Cloudflare Pages가 퍼센트 인코딩된 URL을 처리하는 방식
- 세 가지 대표 해결법 비교 (효과, 복잡도, 유지보수 난이도)
- 지금 당장 적용 가능한 설정 조합

---

**In brief:** Hugo + Cloudflare Pages 조합에서 한국어 URL 404 에러는 인코딩 방식 불일치에서 비롯돼요. Hugo가 생성하는 파일 경로와 브라우저가 요청하는 URL 사이에 퍼센트 인코딩 처리가 어긋나는 게 핵심이에요.

1. Hugo는 기본적으로 한글 슬러그를 `%EC%B9%B4%ED%85%8C%EA%B3%A0%EB%A6%AC` 같은 퍼센트 인코딩으로 변환하지만, `defaultContentLanguage` 설정에 따라 동작이 달라져요.
2. Cloudflare Pages는 파일 기반 라우팅을 쓰는데, 업로드된 파일명과 요청 URL의 인코딩이 100% 일치해야 정상 서빙이 돼요.
3. `removePathAccents: false` + 슬러그 명시 설정 조합이 현재(2026년 3월 기준) 가장 안정적인 해결책이에요.

---

## 왜 이 에러가 생기는 걸까요?

### Hugo의 URL 생성 원리

Hugo는 마크다운 파일의 제목이나 파일명을 기반으로 URL을 만들어요. 파일명이 `카테고리-분석.md`라면, Hugo는 기본 설정에서 이걸 퍼센트 인코딩된 문자열로 변환해서 `public/` 폴더에 `%EC%B9%B4%ED%85%8C%EA%B3%A0%EB%A6%AC-%EB%B6%84%EC%84%9D/index.html` 형태로 저장해요.

문제는 여기서 시작돼요.

Hugo 버전과 `config.toml` 설정에 따라 이 동작이 조금씩 달라요. `uglyURLs: false`가 기본값이라 디렉토리 구조로 만들어지지만, 디렉토리명 자체가 인코딩 문자열이 되는 거예요. Cloudflare Pages가 이 파일들을 CDN에 업로드할 때, 파일 경로 그대로 라우팅 테이블에 등록해요.

### 브라우저와 CDN 사이의 인코딩 불일치

브라우저 주소창에 `https://example.com/카테고리-분석/`를 입력하면, 브라우저가 자동으로 URL을 인코딩해서 `%EC%B9%B4%ED%85%8C%EA%B3%A0%EB%A6%AC-%EB%B6%84%EC%84%9D/`로 요청을 보내요. 여기까지는 맞아요.

그런데 Hugo가 `removePathAccents: true` 설정(일부 테마 기본값)이 활성화된 상태라면, 생성된 파일 경로 자체가 ASCII로 변환된 알 수 없는 문자열이 돼버려요. 반대로 파일명이 raw 한글 그대로 유지되면 Cloudflare CDN이 파일을 업로드할 때 다른 방식으로 인코딩해서 URL 매핑이 어긋나요.

2026년 기준 Hugo 최신 릴리스(0.145.x 계열)에서도 이 동작은 동일하게 관찰돼요. 버전 업그레이드가 자동으로 해결해주지 않는다는 뜻이에요.

---

## 실제 에러 재현과 원인 분석

### 에러 패턴 세 가지

반복적으로 나타나는 패턴은 세 가지예요.

**패턴 1 — 이중 인코딩 충돌**
Hugo가 `%EC%B9%B4...` 형태로 폴더를 만들고, Cloudflare가 업로드 과정에서 이걸 다시 한번 인코딩해서 `%25EC%25B9%25B4...`로 등록하는 경우예요. 브라우저 요청 URL과 실제 파일 경로가 완전히 달라져요. 결과는 404.

**패턴 2 — 슬러그 미설정으로 파일명 그대로 노출**
Front matter에 `slug`를 명시하지 않으면 Hugo는 파일명을 URL로 써요. `2026-03-23-클라우드플레어-설정.md`라면 URL이 `/2026-03-23-클라우드플레어-설정/`이 되는데, CI/CD 빌드 환경의 로케일 설정에 따라 파일명 처리가 달라져요.

**패턴 3 — `hasCJKLanguage` 미설정**
`config.toml`에 `hasCJKLanguage = true`가 없으면 Hugo가 한중일 문자를 정확히 처리하지 못해요. 직접적 404 원인은 아니지만, 빌드 로그에서 경고 없이 잘못된 URL 구조를 만들어내요.

### 진단 방법

```bash
# 빌드 후 public 폴더 구조 확인
find public -type d | head -30

# URL 인코딩 상태 확인
python3 -c "import urllib.parse; print(urllib.parse.unquote('여기에_경로_붙여넣기'))"
```

`public/` 폴더에서 실제 디렉토리명을 확인하는 게 첫 단계예요. 눈으로 보이는 한글 폴더명인지, 퍼센트 인코딩된 폴더명인지에 따라 해결책이 달라지거든요.

---

## 해결 방법 비교 분석

### 세 가지 접근법 비교

| 항목 | 방법 A: 슬러그 영문화 | 방법 B: config 설정 조합 | 방법 C: _redirects 파일 |
|------|-------------|-------------|-------------|
| **적용 난이도** | 낮음 | 중간 | 높음 |
| **유지보수** | 매 포스트마다 수동 | 설정 한 번으로 끝 | 리다이렉트 누적 관리 |
| **기존 포스트 영향** | 없음 | URL 변경 가능 | 없음 (호환 유지) |
| **SEO 영향** | 영문 URL로 통일 | 한글 URL 유지 | 양쪽 모두 유지 |
| **Cloudflare 호환성** | 완벽 | 완벽 | 완벽 |
| **권장 대상** | 신규 블로그 | 기존 블로그 전환 | 마이그레이션 중 |

**방법 B — config 설정 조합** (가장 많이 선택하는 방법)

`config.toml`에 아래 설정을 추가해요.

```toml
hasCJKLanguage = true
removePathAccents = false
defaultContentLanguage = "ko"

[permalinks]
  posts = "/posts/:slug/"
```

그리고 각 마크다운 파일 front matter에 영문 slug를 명시해요.

```yaml
---
title: "Hugo 블로그 한국어 URL 404 해결기"
slug: "hugo-korean-url-404-fix"
date: 2026-03-23
---
```

이렇게 하면 제목은 한국어로, URL은 영문으로 깔끔하게 분리돼요. 다국어 설정을 쓰는 블로그들이 이 방식을 선택하는 이유예요.

**방법 C — `_redirects` 파일** (기존 포스트 URL 보존이 필요할 때)

Cloudflare Pages는 `static/_redirects` 파일을 지원해요.

```
/카테고리-분석/* /posts/category-analysis/:splat 301
```

단, 한글이 포함된 경로를 `_redirects`에 쓸 때는 퍼센트 인코딩 형태로 써야 Cloudflare가 인식해요. 인코딩 없이 한글 그대로 쓰면 이 파일도 무시돼요.

---

## 실제 적용 시나리오별 권장 조합

**시나리오 1 — 새로 시작하는 Hugo 블로그**
`slug: "영문-슬러그"` 습관을 처음부터 들이는 게 가장 깔끔해요. config 설정은 `hasCJKLanguage = true`만 추가하면 충분하고, URL 문제를 원천 차단할 수 있어요.

**시나리오 2 — 이미 포스트가 있는 블로그 전환**
방법 B + 방법 C를 같이 써요. 새 포스트는 영문 slug로, 기존 포스트는 `_redirects`로 인코딩된 URL을 새 URL로 301 리다이렉트해요. 검색 엔진 인덱싱 손실 없이 전환할 수 있어요.

**시나리오 3 — 팀 블로그나 기여자가 여럿인 경우**
Hugo 아키타입(`archetypes/default.md`)에 slug 필드를 기본 포함시켜요. 기여자가 새 포스트를 만들 때 영문 slug 입력을 강제하는 거예요. CI 빌드에서 slug 없는 파일을 감지하는 린터 스크립트도 붙이면 더 좋아요.

---

## 앞으로 어떻게 변할까요?

**당장 4-8주 안에 확인할 것들**

Cloudflare Pages는 2026년 상반기 중 유니코드 경로 처리 로직 업데이트를 예고한 상태예요. 업데이트 이후 퍼센트 인코딩 처리 방식이 바뀔 수 있어요. Cloudflare Dashboard의 Pages 설정 변경 이력을 주기적으로 확인하는 게 좋아요.

**3-6개월 관점**

Hugo 자체도 다국어 URL 처리 개선에 대한 이슈 트래커 논의가 활발해요. `removePathAccents` 옵션의 기본값 변경 가능성도 거론되고 있어요. 지금 방법 B로 해결한 블로그도 Hugo 버전 업그레이드 후 재확인이 필요할 수 있어요.

**지금 바로 해야 할 한 가지**

빌드 후 `public/` 폴더의 한글 경로 포스트 5개를 골라서, 실제 URL을 브라우저에서 직접 쳐보세요. 로컬 `hugo server`가 아닌 Cloudflare Pages 배포 URL로요. 에러가 없으면 다행이고, 404가 뜬다면 방법 B를 먼저 적용해봐요.

---

결국 핵심은 Hugo가 파일을 만드는 방식과 Cloudflare가 그 파일을 서빙하는 방식 사이의 인코딩 합의예요.

- Hugo의 URL 생성 과정에서 한글이 어떻게 처리되는지 먼저 이해해야 해요
- `slug` 명시 + `hasCJKLanguage = true` 조합이 현시점 가장 안전해요
- 기존 포스트 URL 보존이 필요하다면 `_redirects`를 병행해요
- Hugo와 Cloudflare Pages 업데이트 이후엔 빌드 결과를 반드시 재확인해야 해요

그런데 한 가지 물음이 남아요. 영문 slug를 강제하는 게 정답일까요, 아니면 한국어 URL이 SEO 측면에서 더 나은 선택일까요? 한국어 키워드 검색 트래픽을 중시한다면, 인코딩 문제를 완전히 해결한 한글 URL이 더 유리할 수도 있어요. 어떤 방향이 맞는지는 블로그의 주요 독자층과 검색 유입 패턴을 먼저 확인해보는 게 좋아요.

## 참고자료

1. [Deploying a Hugo Site with Cloudflare Workers | by Sven van Ginkel | Medium](https://medium.com/@svenvanginkel/deploying-a-hugo-site-with-cloudflare-workers-3d0cf4901347)
2. [Deploy Your Hugo Blog to Cloudflare Workers: A Complete Guide · Hibare](https://blog.hibare.in/posts/deploy-hugo-to-cf-workers/)
3. [Hugo를 사용하여 블로그를 구축하고 Cloudflare Pages에 배포하기 | Heyjude's Blog](https://www.heyjude.blog/ko/posts/deploy-hugo-to-cloudflare/)


---

*Photo by [Daniil Komov](https://unsplash.com/@dkomow) on [Unsplash](https://unsplash.com/photos/laptop-screen-displaying-code-and-data-charts-GQOylIn892U)*
