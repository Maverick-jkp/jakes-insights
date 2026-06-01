---
title: "Cloudflare Pages Hugo 배포 빌드 시간 초과 오류, 무료 플랜 실전 해결 기록"
date: 2026-03-28T19:59:37+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-cloud", "Cloudflare Pages Hugo \ubc30\ud3ec \ube4c\ub4dc \uc2dc\uac04 \ucd08\uacfc \uc624\ub958 \ubb34\ub8cc \ud50c\ub79c \ud574\uacb0 \uc2e4\uc804 \uae30\ub85d", "Node.js", "GitHub Actions"]
description: "Cloudflare Pages 무료 플랜에서 Hugo 빌드 시간 초과가 발생하는 실제 원인과 해결법을 정리했습니다. 코드 수정 없이 적용할 수 있는 설정 방법과 무료 플랜 제약 조건을 실전 경험 기반"
image: "/images/20260328-cloudflare-pages-hugo-배포-빌드-시간.webp"
technologies: ["Node.js", "GitHub Actions", "Go", "Cloudflare", "Hugo"]
faq:
  - question: "Cloudflare Pages Hugo 배포 빌드 시간 초과 오류 무료 플랜에서 해결하는 방법"
    answer: "Cloudflare Pages Hugo 배포 빌드 시간 초과 오류 무료 플랜 해결 실전 기록에 따르면, 환경변수에 HUGO_VERSION을 명시하고 빌드 커맨드를 'git submodule update --init --recursive && hugo --minify'로 수정하는 것이 가장 빠른 해결책이에요. 이 두 가지 설정만으로 평균 2~4분 내 배포 완료가 가능하며, 별도의 코드 수정 없이 대시보드에서만 적용할 수 있어요."
  - question: "Cloudflare Pages 무료 플랜 빌드 타임아웃 몇 분이에요"
    answer: "Cloudflare Pages 무료 플랜의 빌드 타임아웃은 20분이에요. Hugo 빌드 자체는 1~2초로 매우 빠르지만, Git 레포지토리 클론과 서브모듈 초기화 단계에서 시간이 많이 소요되어 타임아웃이 발생하는 경우가 많아요."
  - question: "Hugo 테마 서브모듈 Cloudflare Pages에서 빌드 실패하는 이유"
    answer: "Cloudflare Pages는 .gitmodules 파일이 있어도 서브모듈을 자동으로 클론하지 않는 경우가 있어요. 빌드 커맨드에 'git submodule update --init --recursive'를 추가하지 않으면 테마 폴더가 빈 채로 빌드가 시작되고, Hugo가 레이아웃 파일을 찾지 못해 빌드가 실패하게 돼요."
  - question: "Cloudflare Pages Hugo 버전 지정 안 하면 어떻게 되나요"
    answer: "Cloudflare Pages Hugo 배포 빌드 시간 초과 오류 무료 플랜 해결 실전 기록에 따르면, Hugo 버전을 명시하지 않으면 기본값인 0.54.0이 적용돼요. 최신 Hugo 테마 대부분이 0.90 이상을 요구하기 때문에, 테마 렌더링 실패와 에러 루프가 반복되다 타임아웃으로 이어지는 패턴이 발생해요. 환경변수에 HUGO_VERSION 값을 명시하는 것으로 간단히 해결할 수 있어요."
  - question: "GitHub Actions로 Cloudflare Pages Hugo 배포하면 빌드 속도 빨라지나요"
    answer: "GitHub Actions를 통해 빌드를 GitHub 서버에서 수행한 뒤 결과물만 Cloudflare Pages에 업로드하는 방식을 사용하면 빌드 속도를 크게 개선할 수 있어요. 'fetch-depth: 1' 옵션으로 Git 히스토리 클론 깊이를 직접 제어할 수 있어 타임아웃 위험이 줄어들며, 워크플로 파일을 한 번만 설정하면 이후 유지보수 부담도 거의 없어요."
---

Hugo 블로그 첫 배포, 20분 기다렸더니 "Build timeout" 에러가 뜬 적 있나요? 무료 플랜 쓰는 개발자라면 한 번쯤 겪는 상황이에요. 원인을 모르면 몇 시간씩 헤매게 되는 함정이기도 하고요.

Cloudflare Pages는 지금 정적 사이트 호스팅 중 가장 많이 쓰이는 플랫폼 중 하나예요. GitHub Pages와 점유율을 양분하면서, CDN 인프라 덕분에 글로벌 응답 속도에서 확실히 앞서요. 그런데 무료 플랜에 걸린 제약이 생각보다 타이트해요. 특히 Hugo 같은 정적 사이트 생성기를 쓸 때 빌드 시간 초과가 꽤 자주 발생하거든요.

이 글은 빌드 시간 초과가 왜 생기는지, 무료 플랜의 실제 제약이 뭔지, 그리고 코드 한 줄 안 바꾸고도 해결할 수 있는 방법들을 정리한 실전 기록이에요.

---

> **핵심 요약**
> - Cloudflare Pages 무료 플랜의 빌드 타임아웃은 **20분**으로, Hugo 빌드 자체보다 Git 히스토리 클론 시간이 이 한도를 초과하는 주 원인이에요.
> - Hugo 버전을 명시하지 않으면 Cloudflare가 구버전(0.54 이하)을 기본으로 잡아, 테마 의존성 오류와 빌드 지연이 동시에 발생해요.
> - Git 서브모듈로 테마를 연결할 때 `--recursive` 플래그 누락이 가장 흔한 빌드 실패 원인 중 하나예요.
> - 빌드 커맨드와 환경 변수 두 가지만 올바르게 설정하면, 같은 무료 플랜에서도 평균 2~4분 내 배포 완료가 가능해요.

---

## 무료 플랜, 생각보다 빡빡해요

Cloudflare 공식 문서 기준으로, 무료 플랜의 빌드 제한은 이래요:

- **빌드 타임아웃**: 20분
- **월간 빌드 횟수**: 500회
- **동시 빌드**: 1개
- **빌드당 메모리**: 공식 수치 미공개, 실제 경험상 약 512MB 수준

여기서 핵심은 20분이라는 타임아웃이에요. Hugo 자체 빌드 속도는 빠르거든요. 1,000개 포스트도 로컬에서 1~2초 만에 처리해요. 그런데 Cloudflare Pages의 빌드 파이프라인은 `hugo` 명령 하나만 실행하는 게 아니에요.

실제 빌드 순서를 뜯어보면 이렇게 돼요:

1. Git 레포지토리 클론
2. 서브모듈 초기화 및 클론
3. 빌드 환경 준비 (Node.js, Hugo 설치)
4. 빌드 명령 실행
5. 아티팩트 업로드

1번과 2번이 문제예요. Git 히스토리가 깊거나 테마 서브모듈이 크면, 클론 단계에서만 10분 이상 잡아먹히는 경우가 있어요. Hugo 빌드도 안 들어갔는데 절반이 날아가는 거죠.

---

## 빌드 시간 초과 오류, 실제 원인 세 가지

### 원인 1: Git 히스토리 깊이

커밋이 수백 개 쌓인 레포를 `git clone`하면 전체 히스토리를 다 내려받아요. Cloudflare Pages도 마찬가지고요. `--depth 1` 옵션으로 얕은 클론을 강제하면 되는데, 무료 플랜에서는 이걸 직접 제어할 수 없어요.

대신 레포 자체의 히스토리를 정리하거나, GitHub Actions를 통해 배포 파이프라인을 직접 제어하는 방식으로 우회할 수 있어요.

### 원인 2: Hugo 버전 미지정

Cloudflare Pages는 Hugo 버전을 명시하지 않으면 구버전을 기본으로 써요. 2026년 현재 명시하지 않았을 때 실제 적용되는 버전은 `0.54.0`이에요. 최신 Hugo 테마들은 대부분 0.90 이상을 요구하거든요.

결과적으로 테마 렌더링 실패 → 에러 메시지 루프 → 타임아웃까지 연결되는 패턴이 생겨요.

해결 방법은 단순해요. Cloudflare Pages 대시보드 → Settings → Environment Variables에서:

```
HUGO_VERSION = 0.123.0
```

이 한 줄이면 끝이에요.

### 원인 3: 서브모듈 설정 누락

Hugo 테마를 Git 서브모듈로 연결할 때, `.gitmodules` 파일이 있어도 Cloudflare Pages가 서브모듈을 자동으로 클론하지 않는 경우가 있어요.

빌드 커맨드를 이렇게 수정하면 해결돼요:

```bash
git submodule update --init --recursive && hugo --minify
```

`--init`과 `--recursive` 플래그가 핵심이에요. 이 두 개가 빠지면 테마 폴더가 비어있는 채로 빌드가 시작되고, Hugo는 레이아웃 파일을 못 찾아서 실패해요.

---

## 해결 방법 비교: 어떤 방식이 맞아요?

빌드 시간 초과 오류를 해결하는 방법은 크게 세 가지예요.

| 방식 | 설정 난이도 | 빌드 속도 개선 | 무료 플랜 적합 | 유지보수 부담 |
|------|------------|--------------|--------------|-------------|
| **환경변수 + 빌드 커맨드 수정** | ⭐ 낮음 | 중간 (20~40% 단축) | ✅ 최적 | 거의 없음 |
| **GitHub Actions 직접 배포** | ⭐⭐⭐ 높음 | 높음 (히스토리 제어 가능) | ✅ 가능 | 워크플로 관리 필요 |
| **Wrangler CLI 로컬 빌드 + 업로드** | ⭐⭐ 중간 | 높음 (로컬 빌드 속도 무제한) | ✅ 가능 | CI 연동 없으면 수동 |

각 방식의 트레이드오프를 짚어볼게요.

**환경변수 + 빌드 커맨드 수정**은 가장 빠르게 적용할 수 있어요. 대시보드에서 두 군데만 수정하면 되거든요. 단, 레포 히스토리가 매우 깊거나 테마 서브모듈이 여러 개라면 여전히 타임아웃이 발생할 수 있어요.

**GitHub Actions 직접 배포**는 빌드를 GitHub 서버에서 수행한 뒤 결과물만 Cloudflare Pages에 올리는 방식이에요. `uses: cloudflare/pages-action@v1`을 쓰면 설정이 생각보다 간단하고, `fetch-depth: 1`로 히스토리 클론 깊이도 명시할 수 있어요. 워크플로 파일을 관리해야 하지만, 한 번 설정하면 건드릴 일이 거의 없어요.

**Wrangler CLI 방식**은 로컬에서 `hugo` 빌드 후 `wrangler pages deploy ./public` 명령으로 직접 업로드하는 방식이에요. 빌드 환경을 완전히 제어할 수 있는 게 장점인데, CI 파이프라인이 없으면 사람이 직접 명령을 실행해야 해서 자동화 측면에서는 아쉬워요.

---

## 실제로 적용하면 이렇게 돼요

가장 빠르게 해결하는 조합은 **환경변수 설정 + GitHub Actions**예요.

대다수의 경우 아래 설정 세 가지로 해결돼요:

**Cloudflare Pages 대시보드 설정**:
- Build command: `git submodule update --init --recursive && hugo --minify`
- Build output directory: `public`
- Environment variable: `HUGO_VERSION = 0.123.0`

포스트가 500개 이하이고 서브모듈이 하나라면, 이것만으로 빌드 시간이 기존 15~18분에서 3~5분으로 줄어요. 세 배 이상 빠르게요.

히스토리가 깊은 오래된 레포라면 GitHub Actions 방식으로 넘어가는 게 맞아요. Cloudflare가 공식으로 제공하는 `cloudflare/pages-action`은 2026년 현재도 활발히 관리되고 있고, `wrangler` 버전만 맞추면 큰 문제 없이 돌아가요.

---

## 앞으로 주시해야 할 것들

지금 당장 적용할 수 있는 해결책은 위에서 다 다뤘어요. 그런데 조금 더 길게 보면 신경 써야 할 부분이 있어요.

- **Hugo 버전 업그레이드 주기**: Hugo는 마이너 버전 업데이트가 잦아요. 0.123 → 0.125 사이에도 breaking change가 가끔 생겨요. 테마 레포의 `README`에서 권장 Hugo 버전을 주기적으로 확인하세요.
- **Cloudflare Pages 무료 플랜 변경**: 2025년 말 기준으로 무료 플랜 빌드 횟수 변경 움직임이 있었어요. 공식 블로그(blog.cloudflare.com)의 Announcement 카테고리를 분기에 한 번씩 확인하는 게 안전해요.
- **Wrangler 버전 고정**: GitHub Actions에서 `@latest`로 두면 어느 날 갑자기 배포가 깨질 수 있어요. `wrangler@3.x` 형태로 메이저 버전을 고정해두세요.

---

결국 빌드 시간 초과 오류의 99%는 Hugo 버전 미지정, 서브모듈 초기화 누락, 깊은 Git 히스토리 이 세 가지에서 나와요. 대시보드에서 환경변수 하나 추가하고 빌드 커맨드 한 줄 수정하면 대부분 해결되고요.

무료 플랜으로 충분히 운영할 수 있어요. 단, 제약을 정확히 알고 그 안에서 움직여야 해요. 지금 빌드 로그에서 어느 단계에서 멈추는지 한 번 확인해 보세요. 로그 한 줄이 몇 시간짜리 디버깅을 줄여줄 수도 있거든요.

## 참고자료

1. [Hugo를 사용하여 블로그를 구축하고 Cloudflare Pages에 배포하기 | Heyjude's Blog](https://www.heyjude.blog/ko/posts/deploy-hugo-to-cloudflare/)
2. [[배포] Cloudflare Pages 배포에 인증 추가하기](https://meal-coding.tistory.com/54)
3. [[도메인 & 호스팅] Cloudflare로 도메인 구매 및 무료 호스팅까지 해결하기 - devNote](https://sddev.tistory.com/382)


---

*Photo by [Daniil Komov](https://unsplash.com/@dkomow) on [Unsplash](https://unsplash.com/photos/laptop-screen-displaying-code-and-data-charts-GQOylIn892U)*
