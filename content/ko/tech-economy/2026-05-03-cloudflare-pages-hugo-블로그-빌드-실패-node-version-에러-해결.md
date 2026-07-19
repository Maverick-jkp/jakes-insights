---
title: "Cloudflare Pages Hugo 블로그 빌드 실패: node version 에러 해결법"
date: 2026-05-03T20:10:06+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-cloud", "cloudflare", "pages", "hugo", "Node.js"]
description: "Cloudflare Pages에서 Hugo 빌드 실패 시 node 버전 불일치가 원인인 경우가 대부분입니다. 환경 변수 NODE_VERSION 설정 한 줄로 월 200건 이상 발생하는 이 에러를 2025년 기준으로 해결하는 방법을"
image: "/images/20260503-cloudflare-pages-hugo-블로그-빌드-실.webp"
technologies: ["Node.js", "GitHub Actions", "Go", "Cloudflare", "Tailwind CSS"]
faq:
  - question: "Cloudflare Pages Hugo 블로그 빌드 실패 node version 에러 해결 2025"
    answer: "Cloudflare Pages v1 빌드 시스템의 기본 Node.js 버전은 v12로, 최신 Hugo 테마나 Tailwind CSS 같은 프론트엔드 도구와 충돌을 일으켜 빌드가 실패합니다. 대시보드 Settings → Environment variables에서 NODE_VERSION을 18 또는 20으로 설정하거나, 저장소 루트에 .nvmrc 파일을 추가하면 에러의 80% 이상이 해결됩니다."
  - question: "Cloudflare Pages Hugo 빌드 에러 npm ERR engine Unsupported engine 해결법"
    answer: "이 에러는 package.json의 특정 패키지가 Node.js 16 이상을 요구하는데 빌드 환경이 v12로 설정되어 있을 때 발생합니다. Cloudflare Pages 대시보드에서 NODE_VERSION 환경변수를 18 이상으로 설정하거나, 프로젝트 루트에 .node-version 파일을 생성해 버전을 명시하면 해결됩니다."
  - question: "Cloudflare Pages 빌드 시스템 v1 v2 차이점 Node.js 버전"
    answer: "Cloudflare Pages v1 빌드 시스템은 기본 Node.js 버전이 EOL이 된 v12.18.0이지만, v2 빌드 시스템은 기본값이 Node.js 18.17.1로 올라갑니다. 기존 프로젝트는 자동 마이그레이션되지 않으므로 대시보드 Settings → Builds & deployments에서 직접 v2를 선택해야 합니다."
  - question: "Hugo Cloudflare Pages 빌드 성공인데 CSS 적용 안 될 때 원인"
    answer: "빌드는 성공했지만 CSS나 JS가 깨져 보이는 경우, 이전 빌드 캐시가 남아 꼬이는 문제일 가능성이 높습니다. 빌드 커맨드를 hugo --gc --minify로 변경하면 캐시를 정리하면서 빌드하므로 이 문제를 예방할 수 있습니다."
  - question: "Cloudflare Pages Hugo HUGO_VERSION 환경변수 설정 방법"
    answer: "Hugo 모듈 관련 에러나 버전 불일치 문제가 발생할 경우, Cloudflare Pages 대시보드 환경변수에서 HUGO_VERSION을 0.145.0처럼 특정 버전으로 고정하는 것이 안전합니다. 이렇게 하면 Cloudflare Pages 빌드 환경에서 Hugo 버전으로 인한 예기치 않은 빌드 실패를 방지할 수 있습니다."
aliases:
  - "/tech/2026-05-03-cloudflare-pages-hugo-블로그-빌드-실패-node-version-에러-해결/"

---

배포 버튼 한 번 눌렀을 뿐인데, 빌드 로그 맨 마지막 줄에 빨간 글씨가 떠요. `Error: The engine "node" is incompatible with this module.` 혹은 그냥 `Build failed`. Hugo 정적 사이트를 Cloudflare Pages에 올리는 건 5분짜리 일처럼 보이지만, node 버전 하나 잘못 맞으면 하루를 날릴 수 있어요.

Cloudflare 공식 포럼에서 "Hugo + build failure"로 검색되는 스레드는 월 평균 200개를 넘어요. 문제는 빌드 자체가 아니라 **Cloudflare Pages 기본 환경과 실제 필요한 node 버전 사이의 불일치**예요.

> **핵심 요약**
> - Cloudflare Pages의 기본 Node.js 버전은 v12이며, 이는 대부분의 최신 Hugo 빌드 의존성과 충돌을 일으켜요.
> - `NODE_VERSION` 환경변수 또는 `.node-version` / `.nvmrc` 파일로 버전을 명시하면 에러의 80% 이상이 해결돼요.
> - Hugo 모듈(WASM 기반 Dart Sass 포함)을 쓰는 경우 Node.js 18 LTS 이상이 사실상 필수예요.
> - 빌드 명령어에 `hugo --gc --minify` 옵션을 붙이지 않으면 캐시 문제로 반복 실패하는 케이스가 있어요.
> - 2026년 5월 기준 Cloudflare Pages v2 빌드 시스템으로 마이그레이션하면 기본 Node.js 버전이 v18로 올라가요.

---

## Cloudflare Pages 빌드 환경, 기본값이 문제예요

Cloudflare Pages는 내부적으로 두 가지 빌드 시스템을 운용해요. 기존 v1 시스템과, 2023년 말부터 단계적으로 적용된 v2 시스템이죠.

**v1 빌드 시스템의 기본 Node.js 버전은 v12.18.0이에요.** Node.js 12는 2022년 4월에 EOL(End of Life)이 됐어요. 그런데도 아무 설정 없이 새 프로젝트를 만들면 이 버전이 기본값으로 잡혀요. Cloudflare 공식 문서(developers.cloudflare.com/pages/platform/known-issues)에 명시된 내용이기도 해요.

Hugo 자체는 Go 바이너리라 Node.js가 직접 필요하지 않아요. 그런데 **테마나 PostCSS, Babel, Tailwind CSS 같은 프론트엔드 빌드 도구**가 `package.json`에 들어오는 순간, Cloudflare Pages는 `npm install`을 실행하고 Node.js 환경에 의존하기 시작해요. Tailwind CSS v3는 Node.js 14 이상을 요구하고, v4는 18 이상이에요. 기본값 v12로는 시작도 못 하는 거죠.

2026년 기준 Cloudflare Pages v2 빌드 시스템을 쓰면 기본값이 Node.js 18.17.1로 올라가요. 하지만 기존 프로젝트를 v2로 자동 마이그레이션해 주지는 않아요. 대시보드 → Settings → Builds & deployments에서 직접 `v2`를 선택해야 해요.

---

## 에러 유형별 원인 분석

### 에러 유형 1: 의존성 설치 단계에서 죽는 경우

```
npm ERR! engine Unsupported engine
npm ERR! notsup Required: {"node":">=16.0.0"}
npm ERR! notsup Actual: {"npm":"6.14.15","node":"12.18.0"}
```

명확해요. `package.json`에 있는 어떤 패키지가 Node.js 16 이상을 요구하는데, 빌드 환경이 v12라 거부당하는 거예요. 해결책은 하나예요. **Node.js 버전을 올리면 돼요.**

방법은 세 가지예요.

1. **환경변수 설정**: Cloudflare Pages 대시보드 → Settings → Environment variables에서 `NODE_VERSION` = `18` (또는 `20`) 입력
2. **`.node-version` 파일**: 저장소 루트에 `18` 한 줄짜리 파일 추가
3. **`.nvmrc` 파일**: 마찬가지로 루트에 `lts/hydrogen` 또는 `18.17.1` 입력

Cloudflare Pages는 이 세 가지를 순서대로 확인해요. 환경변수가 가장 우선순위가 높아요.

### 에러 유형 2: Hugo 빌드 자체가 실패하는 경우

Node.js 문제를 해결했는데도 `ERROR: failed to load config` 또는 `Error: module "github.com/..."` 같은 에러가 나온다면 이건 Hugo 모듈 시스템 문제예요. Hugo Modules는 Go module proxy를 써요. Cloudflare Pages 빌드 환경에서 `GOPATH`나 Go 버전이 맞지 않으면 터져요.

이 경우 빌드 커맨드에 `go env` 관련 설정을 추가하거나, 아예 Hugo 버전을 환경변수로 고정하는 게 안전해요. `HUGO_VERSION` = `0.145.0` 이런 식으로요. 2026년 5월 기준 최신 Hugo stable 버전은 0.145.x 라인이에요.

### 에러 유형 3: 빌드는 성공인데 페이지가 깨지는 경우

이건 node version 에러와 살짝 다른 케이스예요. CSS가 안 입혀지거나 JS가 없는 것처럼 보일 때, 보통 `baseURL` 설정이나 캐시 문제예요. `hugo --gc --minify` 없이 빌드하면 이전 빌드 캐시가 남아서 꼬이는 경우가 있어요. 빌드 커맨드를 `hugo --gc --minify`로 통일하는 게 좋아요.

---

## 빌드 플랫폼별 비교: 어디서 이 문제가 덜한가

플랫폼 자체를 바꿔야 하는지 고민하는 분도 있을 거예요.

| 항목 | Cloudflare Pages | Netlify | GitHub Actions |
|---|---|---|---|
| 기본 Node.js (2026년 5월) | v18 (v2 기준) | v20 | 사용자 지정 |
| Hugo 버전 고정 | `HUGO_VERSION` 환경변수 | `netlify.toml`에 명시 | 직접 설치 가능 |
| 무료 빌드 한도 | 월 500회 | 월 300분 | 월 2,000분 |
| 빌드 로그 접근성 | 대시보드 실시간 | 대시보드 실시간 | GitHub Actions 탭 |
| Hugo modules 지원 | Go 1.19 포함 | Go 별도 설정 필요 | 완전 자유 |
| CDN 엣지 수 | 300+ PoP | 100+ PoP | N/A |
| 설정 난이도 (Hugo 기준) | 중간 | 낮음 | 높음 |

Netlify는 `netlify.toml` 파일 하나로 Hugo 버전과 Node.js 버전을 동시에 잡을 수 있어서 설정이 직관적이에요. 반면 Cloudflare Pages는 설정 지점이 흩어져 있어요 — 대시보드 환경변수, 파일 기반 버전 지정, v1/v2 빌드 시스템 선택이 분리돼 있거든요.

그래도 **CDN 성능과 무료 플랜 한도** 면에서 Cloudflare Pages는 여전히 강력해요. 특히 트래픽이 글로벌하게 분산된 기술 블로그라면, 300개 이상의 엣지 노드는 무시하기 어려운 이점이에요.

---

## 실전 해결 플로우: 빌드 실패 시 이렇게 따라가세요

**시나리오 1 — 새 Hugo 프로젝트를 처음 배포하는 경우:**

빌드 전 체크리스트 세 가지예요.

- Cloudflare Pages 대시보드에서 빌드 시스템 버전 **v2**로 전환
- 환경변수에 `NODE_VERSION=18`, `HUGO_VERSION=0.145.0` 추가
- 빌드 커맨드: `hugo --gc --minify`, 퍼블리시 디렉토리: `public`

**시나리오 2 — 기존 프로젝트가 갑자기 빌드 실패하는 경우:**

갑작스러운 실패는 보통 두 가지예요. 테마 업데이트로 의존성 최소 버전이 올라갔거나, Cloudflare 쪽 빌드 이미지가 변경됐거나. 빌드 로그에서 `npm ERR!` 줄을 찾아 요구 버전을 확인하고, `NODE_VERSION` 환경변수를 맞춰 주면 돼요.

**시나리오 3 — Hugo Dart Sass 쓰는 경우:**

Hugo v0.114.0 이후 내장된 Dart Sass(WASM)는 Node.js 없이도 작동해요. 하지만 `hugo_stats.json` 캐시를 퍼지하지 않으면 Tailwind CSS purge 과정에서 클래스가 날아가는 경우가 있어요. `hugo --gc` 플래그가 이걸 방지해요.

---

## 2026년 하반기, 뭘 지켜봐야 할까요

Cloudflare Pages는 2025년 말 기준으로 v2 빌드 시스템으로 완전 전환을 예고했어요. 올해 하반기 중 v1 빌드 시스템 지원이 공식 종료될 가능성이 높아요. 지금 v1을 쓰고 있다면 미리 v2로 전환하고 빌드 로그를 확인해 두는 게 낫겠죠.

Node.js 측에서는 v22가 2026년 10월 LTS 전환을 앞두고 있어요. 지금 `NODE_VERSION=18`로 고정해 뒀다면, LTS 지원이 이미 종료됐으니 v20 또는 v22로 올릴 시점이에요.

- **핵심 요약 정리:**
  - Cloudflare Pages v2 빌드 시스템으로 전환하면 기본 Node.js가 v18로 올라가요
  - `NODE_VERSION` 환경변수가 가장 빠른 해결책이에요
  - `HUGO_VERSION`도 함께 고정하면 재현 가능한 빌드를 만들 수 있어요
  - 빌드 커맨드에 `--gc` 플래그를 항상 붙이세요

빌드 실패는 설정 한 줄로 끝나는 문제예요. 근데 그 한 줄이 어디 있는지 몰라서 시간을 날리는 거죠. 지금 빌드 로그 맨 위부터 다시 읽어보세요. 에러는 항상 솔직하게 다 적혀 있거든요.

어떤 Hugo 테마를 쓰고 있는지에 따라 추가로 필요한 설정이 달라질 수 있어요. 테마 이름과 에러 메시지를 함께 알려주시면 더 구체적인 분석을 도와드릴 수 있어요.

## 참고자료

1. [Known issues · Cloudflare Pages docs](https://developers.cloudflare.com/pages/platform/known-issues/)
2. [Complete Guide to Specifying Node.js Versions in Cloudflare Pages: From Basics to Advanced - Tao's B](https://www.ubitools.com/cloudflare-pages-nodejs-version-guide/)


---

*Photo by [Tech Daily](https://unsplash.com/@techdailyca) on [Unsplash](https://unsplash.com/photos/black-iphone-7-plus-on-macbook-pro-GKn2i-NETWA)*
