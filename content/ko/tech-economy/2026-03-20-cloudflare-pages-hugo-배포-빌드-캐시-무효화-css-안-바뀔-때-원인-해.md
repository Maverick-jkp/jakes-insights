---
title: "Cloudflare Pages Hugo 배포 후 CSS 안 바뀔 때: 빌드 캐시 무효화 원인과 해결"
date: 2026-03-20T19:58:07+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-cloud", "cloudflare", "pages", "hugo", "Go"]
description: "Cloudflare Pages에서 Hugo CSS가 배포 후에도 안 바뀌는 원인은 CDN·빌드·브라우저 3개 캐시 레이어에 있어요. resources/_gen/ 캐시 처리와 hugo --gc 옵션으로 해결하는 방법을 정리했어요."
image: "/images/20260320-cloudflare-pages-hugo-배포-빌드-캐시.webp"
technologies: ["Go", "Cloudflare", "Hugo"]
faq:
  - question: "Cloudflare Pages Hugo 배포 후 CSS 안 바뀔 때 원인 뭔가요"
    answer: "Cloudflare Pages Hugo 배포 시 CSS가 안 바뀌는 원인은 크게 세 가지 캐시 레이어(Hugo 빌드 캐시, Cloudflare CDN 캐시, 브라우저 캐시)에서 각각 발생할 수 있어요. 가장 흔한 주범은 Hugo의 `resources/_gen/` 빌드 캐시로, 이 폴더가 Git에 포함되지 않으면 Cloudflare Pages 빌드 환경에서 버전 불일치가 생겨 이전 스타일이 그대로 나올 수 있어요. 세 레이어를 순서대로 확인하는 게 가장 빠른 해결 방법이에요."
  - question: "Hugo 빌드 캐시 무효화하는 방법"
    answer: "Hugo 빌드 명령어에 `--gc` 플래그를 추가하면(`hugo --gc --minify`) 빌드 후 오래된 캐시 파일을 자동으로 정리해줘요. 빌드 시간이 소폭 늘어나지만 `resources/_gen/` 캐시 불일치로 인한 CSS 문제를 확실히 줄일 수 있어요. 또는 `resources/_gen/` 폴더를 `.gitignore`에서 제외해 Git에 포함하는 방법도 있어요."
  - question: "Cloudflare Pages 배포했는데 변경사항이 반영 안 될 때 캐시 퍼지하는 법"
    answer: "Cloudflare 대시보드에서 '캐시 제거(Purge Everything)'를 수동으로 실행하거나, Cloudflare API로 특정 URL만 선택해 퍼지할 수 있어요. Cloudflare Pages 빌드 캐시 무효화가 자동으로 이뤄지는 경우도 있지만, 커스텀 도메인과 Cloudflare Proxy를 함께 쓰는 환경에서는 자동 퍼지가 완전히 적용되지 않을 수 있어 수동 확인이 필요해요."
  - question: "Hugo CSS fingerprint 적용하는 방법"
    answer: "Hugo 템플릿에서 `{{ $style := resources.Get 'css/main.css' | fingerprint }}`와 같이 `fingerprint` 함수를 사용하면 파일 내용이 바뀔 때마다 URL 해시값도 자동으로 변경돼요. 브라우저는 URL이 달라지면 항상 새 파일을 요청하기 때문에, 브라우저 캐시로 인해 CSS 변경사항이 반영 안 되는 문제를 근본적으로 해결할 수 있어요."
  - question: "Hugo 배포 CSS 문제 가장 빠르게 해결하는 조합"
    answer: "빌드 명령어를 `hugo --gc --minify`로 설정하고, Cloudflare Pages의 자동 캐시 퍼지가 정상 작동하는지 확인하는 것이 가장 현실적인 조합이에요. 이 두 가지만 적용해도 대부분의 CSS 안 바뀌는 현상은 해결되며, 브라우저 캐시 문제까지 잡으려면 Hugo의 fingerprint 기능을 추가로 적용하면 돼요."
---

Hugo로 스타일 수정했는데 배포하고 나서도 화면이 그대로인 거, 맞죠? 원인은 대부분 하나예요 — 캐시가 이전 파일을 붙잡고 있는 거예요.

> **핵심 요약**
> - CSS가 안 바뀌는 현상은 크게 세 가지 레이어(Cloudflare CDN 캐시, Hugo 빌드 캐시, 브라우저 캐시)에서 각각 발생할 수 있어요.
> - Hugo는 기본적으로 `resources/_gen/` 폴더에 CSS 처리 결과를 캐시하는데, 이 폴더가 Git에 없으면 Cloudflare Pages 빌드 환경에서 매번 재생성되거나 이상하게 동작할 수 있어요.
> - Cloudflare 무료 플랜 기준으로 Pages 빌드는 월 500회까지 지원하고, CDN 캐시 퍼지는 별도 API로 제어 가능해요.
> - `hugo --gc --minify` 옵션을 빌드 명령어에 추가하면 오래된 캐시 파일이 자동 정리돼서 CSS 불일치 문제를 상당수 예방할 수 있어요.

---

## 이 문제가 계속 터지는 이유

Hugo는 빠르고 가벼워요. Cloudflare Pages와의 궁합도 좋죠. 그런데 아이러니하게도 이 "빠름"이 문제의 씨앗이기도 해요.

Hugo는 속도를 위해 여러 곳에서 캐시를 적극적으로 써요. Sass나 PostCSS로 처리한 CSS 파일, 이미지 변환 결과물, 파이프라인 처리 파일들을 전부 `resources/_gen/` 안에 저장해둬요. 로컬에선 아무 문제 없어요. 근데 Cloudflare Pages 빌드 서버는 매 배포마다 새 환경에서 시작하기 때문에, 이 캐시 폴더가 없으면 처음부터 다시 만들어야 해요.

이때 버전 불일치나 환경 차이가 생기면? CSS가 엉뚱하게 렌더링되거나, 아예 이전 버전 스타일이 그대로 나와요.

핵심은 이거예요 — 캐시 문제는 한 곳에서만 오지 않아요. CDN, 빌드 시스템, 브라우저. 세 레이어를 순서대로 의심해야 해요.

---

## 세 가지 캐시 레이어: 어디서 막히는 걸까

### Hugo 빌드 캐시: 가장 흔한 주범

로컬에서 `hugo` 명령어를 실행하면 `resources/_gen/` 폴더가 생겨요. Sass로 작성한 스타일시트를 처리한 결과물이 여기 들어가죠. 문제는 이 폴더를 `.gitignore`에 넣어버린 경우예요.

Cloudflare Pages 빌드 환경은 `git clone` 후 빌드를 실행하는 구조예요. `.gitignore`에 `resources/`가 들어가 있으면, 빌드 서버는 이 폴더 없이 CSS를 새로 만들어야 해요. 이때 Hugo 버전이나 Sass 처리 도구의 버전이 로컬과 조금이라도 다르면 결과물도 달라질 수 있어요.

해결책은 두 가지예요:

- `resources/_gen/` 폴더를 Git에 포함하거나
- 빌드 명령어에 `--gc` 플래그를 추가해서 Hugo가 매번 깨끗하게 재생성하도록 강제하기

```bash
hugo --gc --minify
```

`--gc`는 빌드 후 오래된 캐시 파일을 지워주는 옵션이에요. 빌드가 아주 약간 느려지지만, 불일치 문제를 확실히 줄여줘요.

### Cloudflare CDN 캐시: 눈에 안 보이는 레이어

배포가 성공적으로 끝났는데도 변경이 안 보인다면, Cloudflare CDN이 이전 CSS를 엣지 서버에 캐시하고 있을 수 있어요. `Cache-Control` 헤더를 별도로 설정하지 않은 경우, Cloudflare는 정적 파일을 기본적으로 강하게 캐시해요.

Cloudflare Pages는 배포할 때 자동으로 캐시를 퍼지해줘요. 그런데 커스텀 도메인 + Cloudflare Proxy를 함께 쓰는 구성에서는 이 자동 퍼지가 완전히 적용 안 되는 경우가 있어요. 이럴 땐 대시보드에서 수동으로 "캐시 제거(Purge Everything)"를 실행하거나, API로 특정 URL만 퍼지할 수 있어요.

```bash
curl -X POST "https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache" \
  -H "Authorization: Bearer {api_token}" \
  -H "Content-Type: application/json" \
  --data '{"purge_everything":true}'
```

### 브라우저 캐시: 제일 단순한 용의자

강력 새로 고침(Ctrl+Shift+R 또는 Cmd+Shift+R) 먼저 눌러봤나요? 브라우저 캐시는 사용자 로컬에 CSS 파일을 저장하기 때문에, 서버에서 파일이 바뀌어도 캐시 만료 전까지 오래된 버전을 보여줘요. 시크릿 창에서 열어보는 것도 빠른 확인 방법이에요.

---

## 접근법 비교: 어떤 방식으로 해결할까

| 방법 | 난이도 | 효과 범위 | 부작용 |
|------|--------|-----------|--------|
| `--gc --minify` 빌드 옵션 추가 | 낮음 | Hugo 빌드 캐시 | 빌드 시간 소폭 증가 |
| `resources/_gen/` Git 포함 | 낮음 | Hugo 빌드 캐시 | 레포 용량 증가 |
| Cloudflare 캐시 수동 퍼지 | 낮음 | CDN 캐시 | 매번 수동 작업 필요 |
| CSS 파일에 해시 쿼리스트링 추가 | 중간 | 브라우저 캐시 | Hugo 템플릿 수정 필요 |
| Cloudflare Pages 배포 훅 + 캐시 퍼지 자동화 | 높음 | CDN + 배포 연동 | API 설정 필요 |

가장 현실적인 조합은 `--gc --minify` 빌드 옵션 + Cloudflare 자동 캐시 퍼지 확인이에요. 이 두 가지만 잡아도 대부분의 CSS 안 바뀌는 현상은 해결돼요.

Hugo 템플릿에서 CSS를 불러올 때 아래처럼 파일 지문(fingerprint)을 붙이면 브라우저 캐시 문제까지 잡을 수 있어요:

```html
{{ $style := resources.Get "css/main.css" | fingerprint }}
<link rel="stylesheet" href="{{ $style.RelPermalink }}">
```

파일 내용이 바뀌면 URL의 해시값도 바뀌기 때문에, 브라우저는 항상 새 파일을 받아와요. 제일 깔끔한 장기 해결책이에요.

---

## 지금 당장 확인할 체크리스트

**배포 직후 CSS가 안 바뀔 때 순서대로 확인하세요:**

1. **시크릿 창에서 열기** — 브라우저 캐시 배제
2. **Cloudflare Pages 빌드 로그 확인** — 빌드가 실제로 성공했는지
3. **Cloudflare 대시보드에서 캐시 퍼지** — 커스텀 도메인 쓴다면 필수
4. **빌드 명령어 확인** — `hugo --gc --minify`로 설정되어 있는지
5. **Hugo 버전 확인** — 로컬과 Cloudflare Pages 빌드 환경의 버전이 같은지 (`HUGO_VERSION` 환경변수로 고정 가능)

특히 5번이 간과되기 쉬워요. Cloudflare Pages는 `HUGO_VERSION`을 지정하지 않으면 기본값을 써요. 로컬에서 최신 Hugo를 쓰다가 배포 환경이 구버전이면, Sass 처리 결과가 다르게 나올 수 있어요. 실제로 이 버전 차이 하나 때문에 몇 시간을 날리는 경우가 꽤 있어요.

---

## 마무리: 캐시는 레이어로 생각하세요

CSS 안 바뀌는 문제는 단일 원인이 아니에요. Hugo 빌드 캐시, Cloudflare CDN 캐시, 브라우저 캐시 — 이 세 레이어를 각각 의심하고 순서대로 확인하는 게 핵심이에요.

Hugo + Cloudflare Pages 조합을 계속 쓴다면, 처음 셋업할 때부터 `fingerprint`와 `--gc` 옵션을 넣어두는 걸 추천해요. 나중에 트러블슈팅하는 시간이 훨씬 줄어들거든요. Hugo 빌드 환경 변수 설정이나 Cloudflare Pages에서 인증 추가하는 방법도 꽤 자주 나오는 주제인데, 다음에 다뤄볼게요.

## 참고자료

1. [Hugo를 사용하여 블로그를 구축하고 Cloudflare Pages에 배포하기 | Heyjude's Blog](https://www.heyjude.blog/ko/posts/deploy-hugo-to-cloudflare/)
2. [클라우드플레어 무료 플랜, 어디까지 가능할까? (요청, 빌드, 스토리지 제한 총정리) - Sentio](https://sentio5.com/entry/cloudflare-free-plan-limits/)
3. [[배포] Cloudflare Pages 배포에 인증 추가하기](https://meal-coding.tistory.com/54)


---

*Photo by [Oberon Copeland @veryinformed.com](https://unsplash.com/@veryinformed) on [Unsplash](https://unsplash.com/photos/a-computer-screen-with-a-list-EtCxIuaG-zU)*
