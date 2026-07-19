---
title: "JavaScript 번들 비대화 원인과 npm 패키지 문제 해결 방법"
date: 2026-03-22T19:31:19+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "javascript", "\ube44\ub300\ud654", "npm", "React"]
description: "npm 패키지 의존성 중앙값 47개 시대, JavaScript 번들이 1.4MB를 넘는 이유와 moment.js·lodash 같은 무거운 패키지를 진단하고 교체하는 실전 최적화 방법을 다룹니다."
image: "/images/20260322-javascript-번들-비대화-원인-npm-패키지-문.webp"
technologies: ["JavaScript", "React", "Vercel", "Go", "Java"]
faq:
  - question: "JavaScript 번들 크기 줄이는 방법 어디서부터 시작해야 하나요"
    answer: "JavaScript 번들 비대화 원인 npm 패키지 문제 해결의 출발점은 도구 교체가 아니라 의존성 감사예요. `npm ls --depth=0`이나 `npx depcheck` 명령어로 중복 패키지와 불필요한 의존성을 먼저 확인하고, 중복 버전 제거만으로도 번들 크기를 15~20% 줄일 수 있어요."
  - question: "lodash import 방식에 따라 번들 크기 차이 얼마나 나나요"
    answer: "`import _ from 'lodash'` 방식은 lodash 전체(약 72KB gzip)가 번들에 포함되지만, `import debounce from 'lodash/debounce'`처럼 개별 함수만 가져오면 해당 함수 코드만 번들에 들어가요. 이처럼 통째로 import하는 패턴이 JavaScript 번들 비대화 원인 중 가장 흔한 npm 패키지 문제여서, import 방식 교체만으로도 번들 크기를 크게 줄일 수 있어요."
  - question: "moment.js 대신 뭐 써야 번들 가벼워지나요"
    answer: "`moment.js`는 gzip 기준 약 67KB에 사용하지 않는 40개 언어 로케일 데이터까지 번들에 포함되는 문제가 있어요. `date-fns`는 동일 기능 대비 약 75% 더 가볍고 tree-shaking도 잘 지원되기 때문에 대체 라이브러리로 가장 많이 권장돼요."
  - question: "webpack rollup esbuild 번들 크기 차이 어느 정도인가요"
    answer: "동일 코드 기준 세 빌더의 번들 크기 차이는 최대 30% 이상 벌어질 수 있어요. Rollup은 초기 설계 자체가 ESM 기반이라 tree-shaking 정확도가 가장 높고 번들 크기가 가장 작으며, esbuild는 빌드 속도는 압도적이지만 복잡한 tree-shaking 시나리오에서는 다소 보수적으로 동작해요."
  - question: "프로덕션 빌드에 개발 코드 섞이는 거 어떻게 확인하나요"
    answer: "`process.env.NODE_ENV` 설정이 제대로 되어 있지 않으면 개발 모드 경고 코드와 디버깅 유틸이 프로덕션 번들에 그대로 포함돼요. React 기준으로 개발 빌드는 약 140KB gzip인 반면 프로덕션 빌드는 약 45KB로 약 두 배 차이가 나기 때문에, 빌드 설정에서 NODE_ENV가 `production`으로 명확히 지정되어 있는지 반드시 확인해야 해요."
aliases:
  - "/tech/2026-03-22-javascript-번들-비대화-원인-npm-패키지-문제-해결/"

---

페이지가 느리다는 건 알겠는데, 정확히 **뭐가** 느린 건지 모르는 상황. 빌드 결과물이 수십 MB에 달하고, Lighthouse 점수는 빨간불인데 어디서부터 손을 대야 할지 막막하죠. 그리고 이 문제, 2026년 현재 더 심각해지고 있어요.

> **핵심 요약**
> - npm 생태계 패키지 수는 2026년 기준 약 280만 개를 넘었고, 패키지 하나가 의존하는 다른 패키지 수는 중앙값 기준 47개예요 (npm Registry 공식 통계).
> - HTTP Archive의 2025년 Web Almanac 데이터에 따르면, 모바일 기준 중앙값 JavaScript 페이로드는 **472KB**(gzip 전 기준 약 1.4MB)로 2022년 대비 23% 증가했어요.
> - `moment.js`, `lodash`, `date-fns` 등 흔히 쓰는 유틸리티 라이브러리가 번들 비대화의 핵심 원인으로 지목돼요 — 실제로 tree-shaking이 제대로 안 되는 경우가 절반 이상이에요.
> - webpack, Rollup, esbuild 세 빌더의 번들 크기 차이는 동일 코드 기준 최대 30% 이상 벌어져요.
> - 번들 비대화 문제 해결의 핵심은 도구 교체가 아니라 **의존성 감사**에서 시작해요.

---

## JavaScript 번들이 커지는 구조적 배경

npm이 처음 등장한 건 2010년이에요. 당시엔 패키지 재사용이라는 개념 자체가 신선했죠. 그런데 지금은요?

`npm install` 한 번에 수백 개의 패키지가 `node_modules` 폴더에 쌓여요. 간단한 React 앱 하나를 CRA로 만들면 약 1,300개 이상의 패키지가 설치되고, 디스크 사용량은 300MB를 넘기는 경우가 흔해요. 이게 전부 번들로 들어가는 건 아니지만, **의도하지 않은 코드가 번들에 섞이는 건** 훨씬 더 쉬운 일이에요.

문제가 구조적으로 커진 건 크게 세 가지 흐름 때문이에요.

첫째, **패키지 의존성의 깊이**가 깊어졌어요. A 패키지가 B를 쓰고, B는 C를 쓰고, C는 또 D를 써요. 이 체인이 깊어질수록 내가 실제로 필요한 기능과 관계없는 코드가 번들에 섞여 들어가요.

둘째, **CJS(CommonJS)와 ESM(ES Modules)의 혼재**가 문제예요. tree-shaking은 ESM 기반에서만 제대로 작동하는데, npm에 올라온 패키지 중 상당수가 아직 CJS 형식이에요. Bundlephobia 분석(2025년 4분기 기준)에 따르면, 상위 1,000개 패키지 중 약 38%가 여전히 CJS 전용 배포를 해요.

셋째, **편의 우선 개발 문화**예요. `npm install` 한 줄로 기능을 추가할 수 있으니, 10줄짜리 유틸 함수를 직접 짜는 대신 100KB짜리 라이브러리를 통째로 설치하는 경우가 많죠.

---

## 번들 비대화의 세 가지 실제 원인

### 원인 1: 통째로 import하는 라이브러리

번들 크기 문제를 파고들다 보면 가장 먼저 만나는 패턴이에요.

```js
// ❌ 이렇게 쓰면 lodash 전체가 번들에 들어가요 (약 72KB gzip)
import _ from 'lodash';
_.debounce(fn, 300);

// ✅ 이렇게 쓰면 debounce 하나만 들어가요
import debounce from 'lodash/debounce';
```

`moment.js`는 더 심각해요. gzip 기준 약 67KB인데, 로케일 데이터가 전부 함께 묶여요. 한국어 하나만 필요한데 40개 언어 데이터가 번들로 들어가는 거예요. Bundlephobia 기준 `date-fns`는 동일 기능 대비 약 75% 더 가볍고, tree-shaking도 잘 돼요.

### 원인 2: 중복 패키지 버전 충돌

프로젝트 규모가 커지면 같은 패키지의 여러 버전이 동시에 설치되는 경우가 생겨요. `react-query v4`와 `v5`가 함께 들어가거나, `lodash 4.17.15`와 `4.17.21`이 동시에 존재하는 상황이요.

`npm ls --depth=0`이나 `npx depcheck` 명령어로 이 상태를 바로 확인할 수 있어요. 실제 프로젝트 감사 사례를 보면, 중복 버전 제거만으로 번들 크기를 **15~20%** 줄이는 경우가 드물지 않아요.

### 원인 3: 개발 전용 코드가 프로덕션 빌드에 섞이는 경우

`process.env.NODE_ENV` 체크가 제대로 안 되면 개발 모드 경고 코드, 디버깅 유틸, 테스트 픽스처가 프로덕션 번들에 통째로 들어가요. React 자체도 개발 빌드와 프로덕션 빌드의 크기 차이가 약 두 배예요 — 개발 빌드 기준 약 140KB gzip, 프로덕션은 약 45KB.

---

## 번들러별 비교: 어떤 도구가 더 잘 걸러낼까

빌더 선택은 생각보다 큰 변수예요.

| 기준 | webpack 5 | Rollup | esbuild |
|------|-----------|--------|---------|
| **기본 번들 크기** | 중간 | 가장 작음 | 중간 |
| **tree-shaking 정확도** | 좋음 | 최상 | 보통 |
| **빌드 속도** | 느림 | 중간 | 매우 빠름 |
| **CJS 패키지 처리** | 자동 변환 | 플러그인 필요 | 자동 변환 |
| **코드 스플리팅** | 최상 | 좋음 | 제한적 |
| **적합한 상황** | 복잡한 앱 | 라이브러리 배포 | 빠른 빌드 우선 |

Rollup이 tree-shaking에서 우위를 보이는 이유는 초기 설계 자체가 ESM 기반이기 때문이에요. webpack은 플러그인 생태계가 넓고 코드 스플리팅 제어가 세밀한 대신, 번들 크기 최적화에는 별도 설정이 많이 필요해요.

esbuild는 빌드 속도가 압도적이에요 — Go 언어로 짜여 있어서 webpack 대비 수십 배 빠르지만, 복잡한 tree-shaking 시나리오에서는 다소 보수적으로 동작해요. Vite는 내부적으로 esbuild(개발 서버)와 Rollup(프로덕션 빌드)을 조합하는 방식으로 두 장점을 절충하는 구조예요.

---

## 지금 당장 실행할 수 있는 감사 순서

한 번에 다 고치려다 더 복잡해지는 경우가 많아요. 단계별로 접근하는 게 훨씬 효과적이에요.

**1단계 — 번들 가시화 (1시간 이내)**

`webpack-bundle-analyzer` 또는 `rollup-plugin-visualizer`를 붙이면 어떤 패키지가 얼마나 차지하는지 한눈에 보여요. 보통 이 단계에서 "이 패키지가 이렇게 큰 줄 몰랐다"는 발견이 나와요.

**2단계 — 대체재 조사 (Bundlephobia 활용)**

[bundlephobia.com](https://bundlephobia.com)에서 현재 쓰는 패키지 이름을 검색하면 gzip 크기, tree-shaking 지원 여부, 가벼운 대체재까지 바로 알려줘요. `moment` → `day.js`(약 2KB gzip), `lodash` → `radash`나 직접 구현 등 교체 경로가 명확해요.

**3단계 — Dynamic import 도입**

초기 로딩에 필요없는 코드는 나중에 불러오는 패턴이에요.

```js
// 버튼 클릭 시점에 차트 라이브러리를 불러와요
const { Chart } = await import('chart.js');
```

이 패턴 하나로 초기 번들을 20~30% 줄인 사례가 많아요. 대시보드나 관리자 페이지처럼 특정 기능이 조건부로 사용되는 경우에 특히 효과가 커요.

**4단계 — CI에 번들 크기 검사 추가**

`bundlesize` 또는 `size-limit` 패키지를 CI 파이프라인에 붙이면, PR마다 번들 크기 변화를 자동으로 리포팅해요. 인지하지 못한 사이에 번들이 커지는 걸 사전에 차단하는 구조예요. Vercel, Netlify 모두 이 훅을 공식 지원해요.

---

## 앞으로 6-12개월, 뭘 주시해야 할까

번들 비대화 문제는 도구 문제가 아니라 **습관과 감시 체계** 문제예요.

- **ES2025 top-level await**와 모듈 페더레이션 확산으로 런타임 번들 분리 패턴이 더 일반화될 거예요.
- npm 7+의 workspaces 기능이 성숙해지면서 모노레포에서의 중복 패키지 문제가 줄어들 가능성이 있어요.
- Bun의 번들러 기능이 안정화 단계에 접어들고 있어서, 2026년 하반기엔 esbuild의 강력한 경쟁자가 될 수 있어요.

지금 당장 `webpack-bundle-analyzer` 하나만 붙여도 번들의 절반은 이미 설명이 돼요. 어떤 패키지가 가장 먼저 눈에 들어오던가요? 그 패키지가 정말 필요한 건지, 아니면 편의상 설치된 건지 — 거기서 시작하면 돼요.

## 참고자료

1. [Use npm Packages in the Browser with Browserify](https://www.sourcetrail.com/javascript/how-to-use-npm-packages-in-the-browser-with-browserify/)
2. [Windows 환경에서 ait build 시 TypeScript loader ParseError 발생 - 개발 - 앱인토스 개발자 커뮤니티](https://techchat-apps-in-toss.toss.im/t/windows-ait-build-typescript-loader-parseerror/3018)
3. [How to Install Claude Code in 2026: Complete Guide for Mac, Windows & Linux | LaoZhang AI Blog](https://blog.laozhang.ai/en/posts/how-to-install-claude-code)


---

*Photo by [HackerNoon](https://unsplash.com/@hackernoon) on [Unsplash](https://unsplash.com/photos/a-man-sitting-in-front-of-a-laptop-computer-tvYJNqq0I6A)*
