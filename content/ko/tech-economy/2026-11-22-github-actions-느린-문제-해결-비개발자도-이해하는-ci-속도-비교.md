---
title: "GitHub Actions 느린 문제 해결: YAML 설정으로 CI 속도 높이는 방법"
date: 2026-11-22T02:38:24+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-devtools", "github", "actions", "/ube44/uac1c/ubc1c/uc790/ub3c4"]
description: "GitHub Actions CI 속도를 절반으로 줄이는 실전 방법. YAML 세 줄로 30–50% 단축, Docker 레이어 캐시가 npm보다 7배 효과적, macOS runner 비용 함정까지 — 불필요한 작업 제거부터 시작하세요."
image: "/images/20261122-github-actions-느린-문제-해결-비개발자도.webp"
faq:
  - question: "PR 올릴 때마다 CI가 두 번씩 도는 이유가 뭔가요?"
    answer: "push와 pull_request 트리거가 동시에 설정되어 있으면 같은 커밋에 CI가 두 번 실행돼요. Actions 탭에서 같은 커밋 SHA에 실행이 두 개 보이면 이 경우인데, push 이벤트에 브랜치 필터를 걸어서 main만 실행되도록 제한하면 해결돼요."
  - question: "코드 한 줄 고쳤는데 이전 빌드가 계속 돌고 있어요, 멈추게 할 수 있나요?"
    answer: "concurrency 설정에 cancel-in-progress: true를 추가하면 돼요. GitHub 기본값은 실행을 취소하지 않고 큐에 쌓기 때문에, 이미 덮어씌워진 커밋의 CI가 끝까지 돌면서 runner 시간을 낭비해요. YAML 세 줄로 해결되고 체감 속도가 가장 빠르게 개선돼요."
  - question: "npm 캐시 설정했는데 왜 아직도 느리죠?"
    answer: "npm 의존성 캐시보다 Docker 레이어 캐시가 7배 더 효과적이에요. Docker를 쓰고 있다면 npm cache 설정만으로는 한계가 있고, 레이어 캐시를 추가로 적용하면 빌드 시간이 cold 기준 19초에서 6초 수준으로 떨어질 수 있어요."
  - question: "macOS runner 쓰면 비용이 갑자기 튀는 게 정상인가요?"
    answer: "정상이 아니라 흔한 실수예요. macOS runner는 Linux 대비 10배 비싸서 matrix에 하나만 섞여 있어도 청구 금액이 크게 올라요. 워크플로우 파일에서 macos 키워드를 검색해서 꼭 필요한 테스트가 아니면 제거하는 게 맞아요."
  - question: "문서 파일 수정했을 뿐인데 전체 테스트가 도는 걸 막을 수 있나요?"
    answer: "on.push.paths에 실제 코드 경로만 지정하면 돼요. src/** 나 package.json처럼 코드와 관련된 경로만 넣어두면 문서나 README 변경 시에는 CI가 아예 실행되지 않아요."
---

PR 올릴 때마다 CI가 10분씩 도는 거, 코드 한 줄 고쳤는데도요. 이 글은 그 시간을 절반 이하로 줄이는 방법을 다뤄요.

> **핵심 요약**
> - YAML 설정 세 줄로 30–50% 단축 가능해요 (GitSpider 분석 기준)
> - Docker 레이어 캐시가 npm 의존성 캐시보다 7배 더 효과적이에요 — 대부분 npm만 캐시하고 멈추죠
> - `cancel-in-progress: true` 없이 쓰면, 이미 덮어씌워진 커밋의 CI가 끝까지 돌면서 runner 분을 낭비해요
> - macOS runner는 Linux 대비 10배 비싸요. matrix에 stray macOS 항목 하나라도 있으면 비용이 튀어요
> - 더 빠른 머신이 아니라 불필요한 작업 자체를 없애는 게 먼저예요

---

## 1. 증상 확인

PR을 푸시할 때마다 GitHub Actions 탭에서 워크플로우가 큐에 걸리거나, 끝날 필요 없는 오래된 실행이 계속 돌아가는 걸 볼 수 있어요. 로그 상단에 `Waiting for a runner to pick up this job`이 수 분씩 떠 있거나, 같은 브랜치에서 실행이 두 개 동시에 보이면 전형적인 패턴이에요.

실제로 빌드 자체가 느린 게 아니라, 대기와 중복 실행이 체감 시간을 부풀리는 경우가 많아요. [GitSpider 분석](https://gitspider.com/guides/github-actions-ci-slow-how-to-speed-up)에 따르면 캐시와 동시 실행 취소만 적용해도 wall-clock 시간이 30–50% 줄어요.

**가장 빠른 첫 번째 수정:**

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

---

## 2. 가장 유력한 원인 세 가지

### Cause 1: push와 pull_request 트리거가 동시에 걸려 있어요

**확인:** Actions 탭에서 같은 커밋 SHA에 실행이 두 개 보이면 바로 이 경우예요.

```yaml
# 이렇게 되어 있으면 문제예요
on:
  push:
  pull_request:
```

**수정:**

```yaml
on:
  push:
    branches:
      - main
  pull_request:
```

같은 저장소 브랜치에서 PR을 열면 `push`와 `pull_request` 이벤트가 동시에 발생해요. 별도 설정 없이 둘 다 쓰면 CI가 두 번 도는 거예요.

---

### Cause 2: 오래된 실행이 취소되지 않고 끝까지 돌아요

**확인:** 연속으로 커밋을 푸시했을 때 이전 실행이 `In progress`로 계속 남아 있는지 보세요.

```bash
gh run list --branch <브랜치명> --status in_progress
```

두 개 이상 보이면 이 원인이에요.

**수정:**

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

GitHub의 기본값은 실행을 취소하지 않고 큐에 쌓아요. 명시하지 않으면 덮어씌워진 커밋의 CI가 끝까지 돌면서 runner 분을 소모해요.

---

### Cause 3: 의존성이 매번 새로 설치돼요

**확인:** 워크플로우 로그에서 `npm install` 단계가 매번 30초 이상 걸리면 캐시가 없는 거예요.

**수정:**

```yaml
- uses: actions/setup-node@v4
  with:
    node-version: '20'
    cache: 'npm'   # 이 한 줄이 전부예요
```

GitHub Actions runner는 매번 클린 환경에서 시작해요. `cache` 옵션 없이는 `node_modules`를 항상 새로 받아요. [GitSpider](https://gitspider.com/guides/github-actions-ci-slow-how-to-speed-up) 분석 기준으로 Node/Python 프로젝트에서 30–90초 낭비예요.

> **Docker 쓰고 있다면.** [DEV Community 벤치마크](https://dev.to/kalemi/why-is-github-actions-slow-four-causes-each-measured-2k0d) (2026년 9월, Node 20.20.2 기준)에서 Docker 레이어 캐시가 npm 캐시보다 7배 효과적이었어요. cold build 19.5초 → warm cache 5.8초. npm `cache:` 설정 다음 단계로 볼만해요.

---

## 3. 가능성은 낮지만 확인해볼 것들

- **macOS runner가 matrix에 섞여 있음**: `runs-on: macos-latest`가 하나라도 있으면 Linux 대비 10배 비용이에요. `.github/workflows/*.yml`에서 `macos` 검색해서 불필요한 항목 제거하세요.
- **path 필터 없음**: 문서만 바꿔도 전체 CI가 돌아요. `on.push.paths`에 `src/**`, `package.json`처럼 실제 코드 경로를 넣어두면 돼요.
- **job timeout 없음**: GitHub 기본값은 6시간이에요. 하나가 hung되면 그 시간까지 runner를 잡아요. `timeout-minutes: 15` 정도는 각 job에 넣어두세요.
- **거대한 test matrix**: PR마다 모든 OS × 버전 조합을 돌리고 있다면, PR은 단일 OS/버전으로, full matrix는 `main` 브랜치나 nightly로 옮기는 게 맞아요.

---

## 4. 그래도 안 된다면

[GitHub Community Discussions — Actions 카테고리](https://github.com/orgs/community/discussions/categories/actions)가 가장 빠르게 답 받는 곳이에요. Stack Overflow라면 `github-actions` 태그로 질문하세요.

질문할 때 반드시 포함할 것들:

- `.github/workflows/ci.yml` 전체 (secrets 제외)
- 느린 실행의 Run ID
- `created_at` vs `started_at` 타임스탬프
- 이미 시도한 수정 내용

---

## 5. 다음번엔 이렇게 막아요

PR 템플릿이나 workflow 보일러플레이트에 아래 세 가지를 기본으로 넣어두면 처음부터 피할 수 있어요.

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  build:
    timeout-minutes: 20
    steps:
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
```

[StarSling 사례](https://starsling.dev/github-actions-too-slow)에서도 "측정 먼저, 수정 나중"을 권해요. `created_at` → `started_at` 갭이 크면 runner 공급 문제, 그 외에는 대부분 YAML 설정이에요. 더 빠른 머신보다 불필요한 실행을 없애는 게 먼저예요. 위 설정 적용하고 나서 타임스탬프로 꼭 비교해보세요.

---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-white-dice-with-a-black-github-logo-on-it-HLQDfaJUTVI)*
