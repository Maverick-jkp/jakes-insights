---
title: "GitHub Actions 무료 플랜 월 2000분 소진 원인과 Hugo 블로그 빌드 최적화 실전"
date: 2026-05-30T20:44:14+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "github", "actions", "2000/ubd84", "GitHub Actions"]
description: "GitHub Actions 무료 플랜 월 2,000분이 예상보다 빨리 소진되는 이유는 빌드가 아닌 트리거와 캐시 전략에 있습니다. Hugo 빌드를 캐시 적용 시 3~5분에서 40~90초로 단축하는 워크플"
image: "/images/20260530-github-actions-무료-플랜-월-2000분-소.webp"
technologies: ["GitHub Actions", "Go", "Tailwind CSS", "Hugo"]
faq:
  - question: "GitHub Actions 무료 플랜 월 2000분 금방 소진되는 이유"
    answer: "GitHub Actions 무료 플랜 월 2000분 소진 패턴 분석 Hugo 블로그 빌드 최적화 실전 사례를 보면, 과도한 트리거 설정과 캐시 미설정이 주원인이에요. 모든 브랜치에 push 이벤트를 걸어두면 초안·테스트 브랜치 작업까지 전부 빌드되고, npm install을 매번 새로 돌리면 빌드 한 번에 3~5분씩 소모돼요. 여기에 concurrency 설정이 없으면 연속 커밋 시 중복 빌드까지 발생해 분 소진이 가속화됩니다."
  - question: "Hugo 블로그 GitHub Actions 빌드 시간 줄이는 방법"
    answer: "GitHub Actions 무료 플랜 월 2000분 소진 패턴 분석 Hugo 블로그 빌드 최적화 실전에 따르면, npm 캐시와 Hugo 바이너리 캐시를 적용하는 것이 가장 효과적이에요. actions/cache를 사용해 package-lock.json 해시를 키로 설정하면 의존성이 바뀌지 않는 한 캐시가 유지되며, 빌드 시간이 캐시 없이 3~5분에서 캐시 적용 후 40~90초로 줄어들어요. 월 2000분 기준으로 약 두 배 더 많은 빌드를 돌릴 수 있습니다."
  - question: "GitHub Actions concurrency 설정 안 하면 어떻게 되나요"
    answer: "concurrency 설정이 없으면 같은 브랜치에 커밋을 연속으로 push할 때 이전 빌드가 끝나기 전에 새 빌드가 시작되어 동시에 여러 워크플로우가 실행돼요. 예를 들어 5번 연속 push 시 5개 빌드가 동시에 돌면서 분을 5배로 소모할 수 있습니다. cancel-in-progress: true 옵션을 추가하면 이전 실행이 자동 취소되고 최신 커밋만 빌드해 불필요한 소모를 막을 수 있어요."
  - question: "GitHub Actions paths 필터 Hugo 빌드에 적용하는 법"
    answer: "on.push.paths 옵션을 사용해 content/, themes/, config.toml 등 Hugo 빌드에 실제로 영향을 주는 경로만 트리거 대상으로 지정할 수 있어요. README.md 수정이나 .github/ 설정 변경처럼 Hugo와 무관한 파일 변경은 빌드를 건너뛰게 되어 불필요한 실행을 30~50%까지 줄일 수 있습니다. branches 옵션과 함께 main 브랜치만 타겟하면 트리거 범위를 더욱 효과적으로 좁힐 수 있어요."
  - question: "GitHub Actions self-hosted 러너 Hugo 블로그에 쓸 만한가요"
    answer: "월 빌드 횟수가 200회를 넘어서면 self-hosted 러너를 고려하는 것이 합리적이에요. self-hosted 러너는 GitHub Actions 분 차감이 없고 캐시가 7일 만료 없이 영구 유지되어 빌드 속도도 더 일관되게 유지할 수 있습니다. 다만 서버 비용과 러너 직접 관리가 필요하므로, 빌드 횟수가 적은 소규모 블로그라면 트리거·캐시 최적화만으로도 충분한 경우가 많아요."
---

Hugo 블로그를 GitHub Actions로 배포하다 보면 어느 날 갑자기 "Usage limit reached" 메시지를 마주치게 돼요. 월 2,000분이면 충분할 것 같았는데, 실제로는 생각보다 훨씬 빨리 바닥이 나거든요.

문제는 빌드 자체가 아니에요. 불필요한 트리거, 비효율적인 캐시 전략, 잘못된 워크플로우 구조가 진짜 범인이에요.

---

> **핵심 요약**
> - GitHub Actions 무료 플랜은 private 레포 기준 월 2,000분이며, Ubuntu 러너 기준 1분 단위로 차감돼요.
> - Hugo 블로그의 평균 빌드 시간은 캐시 없이 약 3~5분, 캐시 적용 시 40~90초로 줄어요.
> - 월 2,000분 기준으로 캐시 없는 빌드는 약 400~660회, 캐시 적용 시 약 1,300~3,000회까지 가능해요.
> - PR 브랜치 트리거와 불필요한 `push` 이벤트 설정이 분 소진의 주원인이에요.
> - 핵심은 캐시 전략과 트리거 범위 제한, 딱 두 가지예요.

---

## 분은 어디서 새는 걸까요

GitHub 공식 문서에 따르면 public 레포는 Actions가 무제한 무료예요. 문제는 private 레포인데, Ubuntu 러너 1분당 1분이 차감되고, Windows는 두 배, macOS는 열 배 요금이 붙어요. Hugo 빌드는 보통 Ubuntu 러너를 쓰니까 1:1 비율로 차감되는 셈이에요.

분 소진 패턴을 보면 세 가지가 눈에 띄어요.

**첫 번째, 과도한 트리거 설정이에요.** `on: push`만 설정해두면 모든 브랜치의 push마다 빌드가 돌아요. 초안 작성 브랜치, 이미지 리사이즈 브랜치, 테스트 브랜치까지 전부요. 주 5회 포스팅을 해도, 브랜치 작업·수정·리베이스까지 합치면 실제 push 횟수는 열 배 이상이 되기도 해요.

**두 번째, 캐시 미설정이에요.** Hugo 빌드에서 가장 오래 걸리는 단계는 Go 모듈 다운로드와 npm 의존성 설치예요. Tailwind CSS 기반 테마처럼 npm을 쓰는 경우, 캐시 없이 매번 `npm install`을 돌리면 빌드 시간이 3~5분까지 늘어나요.

**세 번째, 동시 실행 중복이에요.** PR에 커밋을 연속으로 push하면, 기존 실행이 끝나기 전에 새 실행이 시작돼요. `concurrency` 설정이 없으면 두 빌드가 동시에 돌면서 분을 두 배로 써요.

---

## 스텝별로 얼마나 걸리나

Hugo 블로그의 일반적인 빌드 파이프라인을 분해하면 이렇게 돼요.

| 스텝 | 캐시 없음 | 캐시 적용 |
|---|---|---|
| `actions/checkout` | 15~25초 | 15~25초 |
| Hugo 설치 | 20~40초 | 5~10초 |
| npm install (테마 의존성) | 60~120초 | 5~15초 |
| Hugo 빌드 | 15~45초 | 15~45초 |
| GitHub Pages 배포 | 10~20초 | 10~20초 |
| **총합** | **약 2~4분** | **약 50~115초** |

checkout과 Hugo 빌드 자체는 크게 줄이기 어려워요. 그런데 Hugo 설치와 npm install은 캐시로 80~90%까지 줄일 수 있어요. 월 2,000분 기준으로 계산하면, 캐시 없이 평균 3분짜리 빌드는 약 666회, 캐시 적용으로 90초로 줄이면 1,333회까지 돌릴 수 있어요. 딱 두 배 차이예요.

---

## 실전 최적화: 세 가지 레버

**트리거 범위를 좁혀요**

`on: push`를 그냥 쓰면 안 돼요. `main` 브랜치만 타겟하고, `paths` 필터로 Hugo와 무관한 변경은 빌드를 건너뛰게 해야 해요.

```yaml
on:
  push:
    branches:
      - main
    paths:
      - 'content/**'
      - 'themes/**'
      - 'config.toml'
  pull_request:
    branches:
      - main
```

README.md 수정이나 `.github/` 설정 변경은 Hugo 빌드가 필요 없잖아요. 이 설정 하나로 불필요한 실행의 30~50%를 줄일 수 있어요.

**캐시를 제대로 설정해요**

npm 캐시를 빠뜨리는 경우가 많아요. 이렇게 써요.

```yaml
- name: Cache npm dependencies
  uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-npm-${{ hashFiles('themes/*/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-npm-
```

`hashFiles`로 `package-lock.json`의 해시를 키로 쓰면, 의존성이 바뀌지 않는 한 캐시가 계속 유지돼요. Hugo 바이너리도 버전이 자주 안 바뀌면 캐시 대상이에요.

**`concurrency`로 중복 실행을 막아요**

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

`cancel-in-progress: true`를 넣으면 이전 실행이 자동으로 취소되고 최신 커밋만 빌드해요. 이게 없으면 5번 연속 push 시 5개 빌드가 동시에 돌 수 있어요.

---

## self-hosted 러너, 언제 고민하나요

규모가 커지면 GitHub-hosted 러너만으로는 한계가 와요.

| 기준 | GitHub-hosted | Self-hosted |
|---|---|---|
| 비용 | 월 2,000분 무료 | 서버 비용만 (분 차감 없음) |
| 설정 복잡도 | 없음 | 보통~높음 |
| 캐시 지속성 | 7일 만료 | 영구 (직접 관리) |
| 권장 상황 | 월 빌드 200회 미만 | 월 빌드 200회 이상 |

self-hosted 러너는 분 차감이 없어요. ARM64 기반 self-hosted 러너는 GitHub-hosted 대비 빌드 비용을 최대 70%까지 줄일 수 있다는 분석도 있어요. 단, 외부 PR에 노출될 경우 보안 위험이 있기 때문에 private 레포나 신뢰된 기여자만 있는 환경에서 써야 해요.

Hugo 블로그처럼 혼자 운영하는 사이트라면, 먼저 트리거·캐시 최적화로 2,000분 안에서 해결하는 게 현실적이에요.

---

## 숫자부터 확인하세요

정리하면 이렇게 돼요.

- 트리거 범위를 `main` + `paths` 필터로 좁히면 불필요한 실행의 절반 가까이 사라져요.
- npm 캐시와 Hugo 바이너리 캐시를 같이 쓰면 빌드 시간이 3~5분에서 1분 내외로 줄어요.
- `concurrency` 설정으로 중복 실행을 막으면 분을 훨씬 아낄 수 있어요.
- 월 빌드 횟수가 200회를 넘기 시작하면 self-hosted 러너 전환을 고민할 때예요.

가장 먼저 할 일은 현재 어디서 분이 사라지는지 보는 거예요. GitHub Actions의 "Usage" 탭에서 레포별 사용량을 월 단위로 확인할 수 있어요. 숫자를 먼저 보고 나면, 어디를 손봐야 할지 바로 보여요.

지금 Hugo 빌드 워크플로우 파일 열어보셨나요? `paths` 필터 하나 추가하는 데 30초면 돼요.

## 참고자료

1. [GitHub Actions Self-Hosted Runner 대규모 운영과 보안 하드닝 가이드 | Chaos and Order](https://www.youngju.dev/blog/devops/2026-03-05-devops-github-actions-self-hosted-runner-ops)
2. [GitHub Copilot 사용법 정리: VS Code에서 설치부터 무료 체험까지 : 네이버 블로그](https://m.blog.naver.com/techref/224009853779)
3. [GitHub Actions Private Repo에서 ARM64 빌드와 비용 최적화](https://rainbound.tistory.com/1342)


---

*Photo by [Ferenc Almasi](https://unsplash.com/@flowforfrank) on [Unsplash](https://unsplash.com/photos/a-computer-screen-with-a-bunch-of-buttons-on-it--FHIdRVGets)*
