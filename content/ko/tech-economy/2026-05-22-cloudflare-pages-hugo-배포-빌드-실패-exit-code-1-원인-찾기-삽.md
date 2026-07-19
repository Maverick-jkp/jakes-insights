---
title: "Cloudflare Pages Hugo 배포 빌드 실패 exit code 1 원인 찾기"
date: 2026-05-22T21:41:47+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-cloud", "cloudflare", "pages", "hugo", "GitHub Actions"]
description: "Cloudflare Pages Hugo 빌드 exit code 1 실패의 주요 원인 4가지—Hugo 버전 불일치(기본값 0.54.0), Git 서브모듈 누락, 환경변수 미설정, 빌드 커맨드 오탈자—를 직접 삽질하며 찾아"
image: "/images/20260522-cloudflare-pages-hugo-배포-빌드-실패.webp"
technologies: ["GitHub Actions", "Go", "Cloudflare", "Hugo"]
faq:
  - question: "cloudflare pages hugo 배포 빌드 실패 exit code 1 원인이 뭔가요"
    answer: "Cloudflare Pages Hugo 배포 빌드 실패 exit code 1의 원인을 찾는 삽질 후기에서 정리된 주요 원인은 Hugo 버전 불일치, Git 서브모듈 누락, 환경변수 미설정, 빌드 커맨드 오탈자 4가지예요. 그 중 Cloudflare Pages 기본 Hugo 버전이 0.54.0으로 고정되어 있어서 로컬 환경과의 버전 gap이 가장 흔한 원인이에요. HUGO_VERSION 환경변수 하나만 제대로 설정해도 빌드 실패의 절반 이상을 해결할 수 있어요."
  - question: "cloudflare pages hugo HUGO_VERSION 환경변수 설정 방법"
    answer: "Cloudflare Pages 프로젝트 설정에서 Environment Variables 메뉴로 이동해 HUGO_VERSION 키에 원하는 버전 값(예: 0.126.1)을 추가하면 돼요. 이 설정 없이는 Cloudflare Pages가 기본값인 Hugo 0.54.0으로 빌드를 시도하기 때문에 최신 테마와 충돌이 발생해요. Sass/SCSS를 사용하는 테마라면 Hugo Extended 버전도 별도로 명시해야 해요."
  - question: "cloudflare pages hugo 테마 서브모듈 빌드 실패 해결 방법"
    answer: "Cloudflare Pages는 기본적으로 Git 서브모듈을 자동으로 체크아웃하지 않아서 테마 디렉토리가 비어있는 채로 빌드가 실행돼 exit code 1이 발생해요. 가장 권장되는 해결 방법은 서브모듈 대신 Hugo Modules로 전환하는 것으로, go.mod 기반 의존성 관리를 사용하면 이 문제가 깔끔하게 사라져요. Cloudflare Pages 빌드 환경에는 go 런타임이 기본 포함되어 있어서 별도 설정 없이 Hugo Modules를 바로 사용할 수 있어요."
  - question: "hugo function not defined 에러 cloudflare pages에서만 나는 이유"
    answer: "이 에러는 Cloudflare Pages의 기본 Hugo 버전(0.54.0)이 너무 낮아서 최신 Hugo 함수를 인식하지 못할 때 발생해요. 로컬 환경에서는 최신 Hugo 버전으로 빌드되기 때문에 문제없이 동작하지만, Cloudflare Pages 환경에서는 버전 gap으로 인해 동일한 코드가 실패하는 거예요. Environment Variables에서 HUGO_VERSION을 로컬과 동일한 버전으로 지정하면 해결돼요."
  - question: "cloudflare pages 빌드 로그 exit code 1만 나오고 에러 메시지 없을 때"
    answer: "에러 메시지 없이 exit code 1만 출력되는 경우는 Git 서브모듈 누락이나 빌드 커맨드 오탈자가 원인인 경우가 많아요. cloudflare pages hugo 배포 빌드 실패 exit code 1 원인 찾기 삽질 후기에 따르면 서브모듈 문제는 특히 아무 설명 없이 빌드가 종료되는 패턴을 보여요. Cloudflare Pages Known Issues 공식 문서에서 서브모듈 관련 제한사항을 확인하고, 빌드 커맨드 오탈자도 함께 점검해보는 것이 좋아요."
aliases:
  - "/tech/2026-05-22-cloudflare-pages-hugo-배포-빌드-실패-exit-code-1-원인-찾기-삽/"
  - "/ko/tech/2026-05-22-cloudflare-pages-hugo-배포-빌드-실패-exit-code-1-원인-찾기-삽/"

---

배포 버튼을 눌렀는데 빌드 로그 마지막 줄에 `exit code: 1`이 찍히는 순간, 머릿속이 하얘지죠. 에러 메시지는 짧고, 원인은 다섯 개쯤 되고, 검색 결과는 2019년 스택오버플로우. Cloudflare Pages와 Hugo 조합은 2026년 기준 정적 사이트 배포의 사실상 표준 스택이 됐지만, 빌드 실패 이슈는 여전히 개발자들을 괴롭히고 있어요.

> **핵심 요약**
> - Cloudflare Pages의 Hugo 빌드 실패 `exit code 1`은 단일 원인이 아니라 Hugo 버전 불일치, Git 서브모듈 누락, 환경변수 미설정, 빌드 커맨드 오탈자 등 4가지 주요 원인군으로 분류돼요.
> - Cloudflare Pages의 기본 Hugo 버전은 `0.54.0`인데, 로컬 개발 환경은 `0.125.x` 이상을 쓰는 경우가 많아서 버전 gap이 가장 흔한 원인이에요.
> - `HUGO_VERSION` 환경변수 하나만 제대로 설정해도 빌드 실패의 절반 이상을 해결할 수 있어요.
> - Cloudflare Pages의 [Known Issues 공식 문서](https://developers.cloudflare.com/pages/platform/known-issues/)에는 Git 서브모듈 관련 제한사항이 명시돼 있지만, 많은 개발자가 이걸 모르고 지나쳐요.

---

## Hugo + Cloudflare Pages는 왜 이렇게 자주 터질까요?

사실 Hugo 자체는 빌드가 매우 빠르고 안정적인 도구예요. 문제는 **Hugo가 버전 간 호환성을 엄격하게 관리하는 도구**라는 점이에요. 마이너 버전 하나 차이로 테마가 렌더링 안 되거나, 함수가 deprecated돼서 빌드가 터지는 일이 꽤 자주 생겨요.

여기에 Cloudflare Pages의 특성이 겹쳐요. Cloudflare Pages는 자체 빌드 환경을 제공하는데, 이 환경의 기본 Hugo 버전이 `0.54.0`으로 고정돼 있어요. Cloudflare 공식 문서에 따르면, 이 기본값은 명시적으로 `HUGO_VERSION`을 지정하지 않으면 그대로 적용돼요. 그런데 2026년 현재 Hugo 최신 안정 버전은 `0.126.x` 계열이고, 대부분의 현대적인 Hugo 테마는 `0.100.0` 이상을 요구해요.

결과적으로 로컬에서는 멀쩡히 빌드되던 사이트가 Cloudflare Pages에 올라가는 순간 `exit code: 1`과 함께 죽어버리는 거예요.

두 번째 맥락은 **Git 서브모듈**이에요. Hugo 테마를 서브모듈로 관리하는 패턴은 흔하지만, Cloudflare Pages는 기본적으로 서브모듈을 자동으로 체크아웃하지 않아요. Cloudflare 공식 Known Issues 문서에도 이 제한이 명시돼 있는데, 서브모듈 초기화 없이 테마 디렉토리가 비어있으면 Hugo는 당연히 빌드에 실패하고 `exit code: 1`을 뱉어요.

이 두 가지 원인만 알아도 대부분의 삽질은 피할 수 있어요. 그런데 막상 처음 마주하면 로그가 너무 짧아서 어디가 문제인지 잡기가 어렵죠.

---

## 원인별 진단: 로그를 읽는 법

### Hugo 버전 불일치: 가장 흔한 범인

빌드 로그에서 이런 메시지를 본 적 있나요?

```
Error: "/opt/buildhome/repo/themes/xxx/layouts/_default/baseof.html:1:1": 
template: _default/baseof.html:1: function "xxx" not defined
```

버전 불일치일 때 자주 나오는 패턴이에요. `function not defined` 에러는 낮은 Hugo 버전에서 최신 Hugo 함수를 인식 못 할 때 발생해요.

해결법은 간단해요. Cloudflare Pages 프로젝트 설정 → **Environment Variables**에서 아래처럼 추가하면 돼요:

```
HUGO_VERSION = 0.126.1
```

한 줄이에요. 그런데 이걸 몰라서 한나절 삽질하는 경우가 많아요.

주의할 점: `Hugo Extended`가 필요한 테마도 있어요. Sass/SCSS를 쓰는 테마라면 일반 Hugo 바이너리로는 빌드가 안 돼요. 이 경우에는 `HUGO_VERSION`과 함께 빌드 커맨드나 빌드 환경 설정에서 extended 버전을 명시해야 해요.

### Git 서브모듈: 조용히 죽는 케이스

서브모듈 문제는 에러 메시지가 더 애매해요:

```
Error: module "xxx" not found; either add it as a Hugo Module or store it 
locally.
```

또는 그냥:

```
exit code: 1
```

아무 설명 없이요. 이게 더 당혹스럽죠.

Cloudflare Pages의 Known Issues 문서에는 서브모듈 관련 제한사항이 명시돼 있어요. 서브모듈이 있는 경우, Cloudflare Pages가 자동으로 `git submodule update --init --recursive`를 실행해주지 않는 경우가 있어요. 해결 방법은 두 가지예요:

| 방법 | 설명 | 권장 여부 |
|------|------|-----------|
| Hugo Modules로 전환 | `go.mod`/`go.sum` 기반 의존성 관리, 서브모듈 불필요 | ✅ 2026년 권장 |
| `git submodule` 유지 | 빌드 커맨드에 수동 초기화 스크립트 추가 | ⚠️ 가능하지만 번거로움 |
| 테마 파일 직접 복사 | 서브모듈 제거, themes/ 디렉토리에 직접 커밋 | ❌ 업데이트 불편 |

Hugo Modules는 `go` 런타임이 필요하지만, Cloudflare Pages 빌드 환경에는 기본으로 포함돼 있어요. 서브모듈 대신 Hugo Modules로 전환하면 이 문제가 깔끔하게 사라져요.

### 빌드 커맨드 오류: 의외로 자주 나와요

Cloudflare Pages 프로젝트 설정에서 **Build command**를 직접 입력하는데, 여기서 오타가 나도 `exit code: 1`이에요. 예를 들어:

```bash
# 잘못된 예
hugo --minify --baseURL $CF_PAGES_URL

# 맞는 예 (환경변수 따옴표 처리)
hugo --minify --baseURL "$CF_PAGES_URL"
```

`$CF_PAGES_URL`은 Cloudflare Pages가 자동으로 제공하는 환경변수예요. 따옴표 없이 쓰면 URL에 슬래시나 특수문자가 포함될 때 파싱 오류가 날 수 있어요.

빌드 디렉토리 설정도 체크해야 해요. Hugo의 기본 출력 디렉토리는 `public/`이에요. Cloudflare Pages의 **Build output directory**가 `public`으로 설정돼 있지 않으면 배포 자체는 성공해도 빈 사이트가 올라가요.

---

## 비교: 정적 사이트 호스팅 플랫폼의 Hugo 지원 현황

Cloudflare Pages만의 문제인지, 다른 플랫폼도 비슷한지 짚고 넘어갈게요.

| 항목 | Cloudflare Pages | Netlify | GitHub Pages |
|------|-----------------|---------|--------------|
| 기본 Hugo 버전 | `0.54.0` (명시 필요) | 자동 감지 (`netlify.toml`) | Actions에서 직접 지정 |
| Hugo Extended 지원 | 환경변수로 지정 가능 | `netlify.toml`에서 지정 | Actions에서 직접 설치 |
| Git 서브모듈 | 제한적 (Known Issue) | 기본 지원 | Actions에서 처리 가능 |
| 빌드 속도 | 빠름 | 보통 | Actions 설정에 따라 다름 |
| 무료 티어 빌드 시간 | 500회/월 | 300분/월 | 무제한 (공개 저장소) |
| 커스텀 도메인 + SSL | 무료 | 무료 | 무료 |

Netlify는 `netlify.toml` 파일에 Hugo 버전을 명시하는 방식이라 버전 관리가 더 직관적이에요. GitHub Actions는 설정이 복잡하지만 가장 자유도가 높고요.

Cloudflare Pages가 불편한 건 아니에요. 환경변수 하나만 제대로 잡으면 빌드가 안정적이고, CDN 성능은 세 플랫폼 중 가장 좋아요. 다만 **초기 설정에서 문서를 꼼꼼히 읽어야 한다**는 전제가 붙어요.

---

## 실전 체크리스트: 배포 전 반드시 확인할 것들

`exit code: 1`을 마주쳤을 때, 순서대로 확인하면 빠르게 원인을 잡을 수 있어요.

**시나리오 1 — 첫 배포인데 바로 실패할 때:**
1. Cloudflare Pages 환경변수에 `HUGO_VERSION` 설정 여부 확인
2. 로컬 Hugo 버전 확인: `hugo version`
3. 두 버전이 일치하도록 환경변수 수정

**시나리오 2 — 예전엔 됐는데 갑자기 안 될 때:**
테마를 업데이트했다면 새 테마의 Hugo 최소 요구 버전을 확인하세요. 테마 `README.md` 또는 `theme.toml`에 보통 명시돼 있어요. 요구 버전이 올라갔다면 환경변수도 함께 올려야 해요.

**시나리오 3 — 로그에 아무것도 안 나올 때:**
서브모듈 문제일 가능성이 높아요. 로컬에서 `git submodule status`를 실행해서 서브모듈이 제대로 초기화돼 있는지 확인하고, Hugo Modules 전환을 고려해보세요.

참고로, Cloudflare Pages의 빌드 로그는 **Settings → Builds & deployments → 해당 배포 클릭**에서 전체 로그를 볼 수 있어요. 기본 화면보다 훨씬 많은 정보가 나오니까, 에러 확인은 반드시 전체 로그 기준으로 하세요.

---

## 정리하며: exit code 1, 이제 안 무서워요

**핵심 요약:**
- 원인의 80%는 Hugo 버전 불일치 또는 서브모듈 누락이에요
- `HUGO_VERSION` 환경변수 설정은 Cloudflare Pages + Hugo 조합의 필수 작업
- Hugo Modules 전환은 서브모듈 문제를 근본적으로 해결해요
- 빌드 커맨드와 출력 디렉토리 설정도 꼭 더블체크해야 해요

앞으로 6개월 안에 Hugo `0.130.x` 계열이 나올 가능성이 높고, Cloudflare Pages도 빌드 환경 업데이트를 계속 진행하고 있어요. 주기적으로 환경변수의 Hugo 버전을 업데이트해주는 게 장기적으로 빌드 안정성을 유지하는 방법이에요.

`exit code: 1`은 사실 Hugo가 "나 뭔가 잘못됐어"라고 보내는 SOS 신호예요. 신호를 해독하는 법만 알면, 더 이상 하얘질 필요 없어요.

Cloudflare Pages Hugo 배포를 처음 설정하면서 겪은 빌드 실패가 있다면, 어떤 원인이었는지 댓글로 공유해주세요. 패턴이 쌓이면 더 나은 진단 가이드를 만들 수 있을 것 같아요.

## 참고자료

1. [[배포] Cloudflare Pages 배포에 인증 추가하기 - 밥 먹고 코딩](https://meal-coding.tistory.com/54)
2. [Known issues · Cloudflare Pages docs](https://developers.cloudflare.com/pages/platform/known-issues/)


---

*Photo by [Growtika](https://unsplash.com/@growtika) on [Unsplash](https://unsplash.com/photos/a-computer-tower-with-a-purple-light-wlQUkvDhvQw)*
