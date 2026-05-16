---
title: "GitHub Actions cron 실행 안 될 때: Hugo 블로그 Cloudflare Pages 자동배포 트러블슈팅"
date: 2026-05-16T20:21:14+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "github", "actions", "hugo", "GitHub Actions"]
description: "GitHub Actions cron이 침묵하는 3가지 원인과 Hugo-Cloudflare Pages 배포 실패 진단법을 다룹니다. YAML 문법 함정, GitHub 정책, 빌드 환경 제약까지 실제 동작하는 워크플로우 패턴으로 해결하세요."
image: "/images/20260516-github-actions-hugo-블로그-cloudf.webp"
technologies: ["GitHub Actions", "Go", "Cloudflare", "Hugo"]
faq:
  - question: "GitHub Actions cron 스케줄 설정했는데 자동으로 실행이 안 되는 이유"
    answer: "GitHub Actions Hugo 블로그 Cloudflare Pages 자동배포 cron 실행 안 될 때 트러블슈팅에서 가장 먼저 확인해야 할 원인은 GitHub의 비활성 저장소 정책이에요. 저장소에 60일 이상 활동이 없으면 GitHub이 예약 워크플로우를 자동으로 일시정지하며, 알림 이메일을 놓치기 쉬워서 모르고 지나치는 경우가 많아요. 그 외에도 cron 표현식의 UTC/KST 시간대 혼동, GitHub 서버 트래픽 집중 시간대의 실행 지연도 주요 원인이에요."
  - question: "GitHub Actions cron UTC 시간 한국 시간으로 변환하는 방법"
    answer: "GitHub Actions의 cron 표현식은 UTC 기준으로만 동작하기 때문에, 한국 시간(KST)에서 9시간을 빼서 입력해야 해요. 예를 들어 KST 오후 6시에 실행하려면 `0 9 * * *`으로 작성해야 하며, `0 18 * * *`으로 쓰면 실제로는 KST 새벽 3시에 실행돼요. 매시 정각처럼 많이 사용되는 시간대는 GitHub 서버 부하로 수십 분 지연될 수 있으므로 피하는 것이 좋아요."
  - question: "Hugo 빌드는 성공했는데 Cloudflare Pages 배포가 안 될 때 원인"
    answer: "Cloudflare Pages 배포가 실패할 때는 API 토큰 권한과 GitHub Secrets 설정을 먼저 확인해야 해요. Cloudflare Pages API 토큰에 `Cloudflare Pages: Edit` 권한이 있어야 하고, `CLOUDFLARE_API_TOKEN`과 `CLOUDFLARE_ACCOUNT_ID` 두 가지 모두 GitHub Secrets에 등록되어 있어야 해요. 또한 Wrangler CLI 직접 배포 방식과 Cloudflare Pages Git 연동 방식을 동시에 사용하면 배포가 충돌하는 케이스도 보고되고 있어요."
  - question: "GitHub Actions Hugo 블로그 Cloudflare Pages 자동배포 cron 실행 안 될 때 워크플로우 안정적으로 구성하는 방법"
    answer: "GitHub Actions Hugo 블로그 Cloudflare Pages 자동배포 cron 실행 안 될 때 트러블슈팅 관점에서 가장 권장되는 방법은 `schedule`과 `push` 트리거를 함께 쓰는 이중 구성이에요. push 이벤트가 저장소 활동으로 인정되어 60일 비활성화 정책을 자연스럽게 방지하고, cron이 지연되거나 실패해도 글을 올리는 순간 즉시 배포가 트리거돼요. 단일 cron만 사용하면 실패 시 대안이 없지만, 이중 트리거 구성은 안정성이 훨씬 높아요."
  - question: "Cloudflare Pages 무료 플랜 빌드 횟수 제한 초과 방지하는 방법"
    answer: "Cloudflare Pages 무료 플랜은 빌드당 최대 20분, 월 500회 빌드 제한이 있어서 cron 주기를 설계할 때 이 수치를 먼저 확인해야 해요. 예를 들어 매시간 실행하면 월 약 720회로 제한을 초과할 수 있으므로, 매일 1회 또는 매주 단위로 cron 주기를 설정하는 것이 안전해요. push 트리거를 함께 쓰는 이중 구성은 빌드 횟수를 더 소비할 수 있으므로, 실제 글 발행 빈도와 월 빌드 제한을 함께 고려해서 주기를 결정해야 해요."
---

cron 스케줄을 설정했는데 아무것도 실행되지 않아요. 워크플로우 파일은 완벽한데, GitHub Actions는 침묵합니다.

Hugo 블로그를 Cloudflare Pages에 자동배포하는 파이프라인을 구성했다면 한 번쯤 마주치는 상황이에요. 문제는 생각보다 훨씬 다양한 곳에 숨어 있거든요. GitHub의 정책 변경, YAML 문법 함정, Cloudflare Pages의 빌드 제한까지.

이 글에서 다룰 내용을 미리 정리하면:

- GitHub Actions cron이 실행 안 되는 3가지 주요 원인
- Hugo 빌드 실패 vs. 배포 실패, 어디서 끊기는지 진단하는 방법
- Cloudflare Pages의 빌드 환경 제약 이해
- 실제 동작하는 워크플로우 구성 패턴 비교

---

> **핵심 요약**
> - GitHub Actions의 비활성 저장소 cron 일시정지 정책(60일 비활동 시 자동 비활성화)이 Hugo 자동배포 실패의 가장 흔한 원인이에요.
> - Hugo 빌드 실패와 Cloudflare Pages 배포 실패는 에러가 나타나는 위치가 다르기 때문에, 로그를 보는 순서가 중요해요.
> - Cloudflare Pages는 빌드당 최대 20분, 월 500회 빌드 제한(무료 플랜)이 있어서 cron 주기 설계 때 이 수치를 먼저 확인해야 해요.
> - `schedule` 트리거와 `push` 트리거를 함께 쓰는 이중 구성이 안정성 면에서 단일 cron 구성보다 훨씬 나아요.

---

## GitHub Actions cron, 갑자기 안 되는 이유

GitHub Actions의 cron 동작 방식은 생각만큼 단순하지 않아요.

가장 흔한 원인부터 보면, **GitHub의 비활성 저장소 정책**이에요. GitHub 공식 문서에 따르면, 저장소에 60일 이상 아무런 활동이 없으면 예약된 워크플로우를 자동으로 일시정지해요. 알림 이메일이 오긴 하는데 놓치기 쉽죠. 블로그 글을 오래 안 올렸다면 이것부터 확인하세요.

두 번째는 **cron 문법 자체의 함정**이에요. GitHub Actions의 cron 표현식은 UTC 기준으로 동작해요. 한국 시간(KST) 오후 6시에 실행하고 싶다면 `0 9 * * *`으로 적어야 해요. `0 18 * * *`이 아니에요.

```yaml
# 자주 발생하는 실수
on:
  schedule:
    - cron: '0 9 * * *'  # 이게 KST 오후 6시예요, 오전 9시 아니에요
```

세 번째는 **GitHub Actions의 cron 지연 문제**예요. GitHub 공식 문서는 트래픽이 많을 때 예약 실행이 수 분에서 수십 분까지 지연될 수 있다고 명시하고 있어요. 특히 매시 정각(`0 * * * *`)처럼 많은 사람이 쓰는 시간대는 더 심해요.

---

## Hugo 빌드와 Cloudflare Pages 배포, 어디서 끊기는가

실패 지점은 크게 세 곳으로 나뉘어요.

**1단계: Hugo 빌드 단계**
워크플로우 로그에서 `hugo --minify` 명령 실행 직후 에러가 나면 빌드 문제예요. 가장 흔한 원인은 Hugo 버전 불일치예요. 로컬에서는 Hugo 0.145가 깔려 있는데, 워크플로우에서 `latest` 버전을 불러오면 브레이킹 체인지가 생길 수 있어요.

```yaml
- name: Setup Hugo
  uses: peaceiris/actions-hugo@v3
  with:
    hugo-version: 'latest'  # ❌ 버전 고정하세요
    hugo-version: '0.145.0' # ✅ 이렇게
```

**2단계: Cloudflare Pages 배포 단계**
빌드는 성공했는데 배포가 안 된다면 API 토큰이나 Account ID 문제일 가능성이 높아요. Cloudflare Pages API 토큰은 `Cloudflare Pages: Edit` 권한이 있어야 하고, GitHub Secrets에 `CLOUDFLARE_API_TOKEN`과 `CLOUDFLARE_ACCOUNT_ID` 두 가지 모두 등록해야 해요.

그리고 Cloudflare의 공식 Pages 문서에 따르면, 직접 Wrangler CLI를 쓰는 방식과 Cloudflare Pages의 Git 연동 방식을 동시에 쓸 때 배포가 충돌하는 케이스도 보고되고 있어요.

---

## 워크플로우 구성: 단일 cron vs. 이중 트리거 비교

| 구분 | 단일 cron | 이중 트리거 (cron + push) |
|------|-----------|--------------------------|
| 설정 복잡도 | 낮음 | 약간 높음 |
| 안정성 | 낮음 (cron 지연/실패 시 대안 없음) | 높음 |
| 즉시 배포 가능 | ❌ | ✅ |
| 비활성 저장소 방지 | 어려움 | push로 자동 방지 |
| 월 빌드 횟수 소비 | cron 주기에 따라 다름 | 더 많이 소비 가능 |
| 권장 용도 | 단순 콘텐츠 갱신 | 실제 블로그 운영 |

이중 트리거가 나은 이유는 단순해요. `push` 이벤트가 있으면 저장소 활동이 생겨서 60일 비활성화 정책을 자연스럽게 피할 수 있어요. cron이 지연되거나 실패해도 글을 올리는 순간 배포가 트리거되거든요.

실제 동작하는 워크플로우 예시를 보면:

```yaml
name: Deploy Hugo to Cloudflare Pages

on:
  schedule:
    - cron: '0 0 * * 1'  # 매주 월요일 UTC 자정 (KST 월요일 오전 9시)
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: true
          fetch-depth: 0

      - name: Setup Hugo
        uses: peaceiris/actions-hugo@v3
        with:
          hugo-version: '0.145.0'
          extended: true

      - name: Build
        run: hugo --minify

      - name: Deploy to Cloudflare Pages
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: 'your-project-name'
          directory: 'public'
```

---

## 실제로 이걸 맞닥뜨렸을 때 대응 순서

**상황 1: cron이 전혀 실행되지 않을 때**
GitHub 저장소 → Actions 탭 → 왼쪽 워크플로우 목록을 보세요. 워크플로우 이름 옆에 `...` 메뉴가 있고 "Enable workflow" 버튼이 보이면 비활성화된 거예요. 활성화 후 수동 실행(`workflow_dispatch` 추가)으로 즉시 테스트하는 게 빨라요.

**상황 2: 빌드는 성공하는데 Cloudflare Pages에 반영이 안 될 때**
Cloudflare Pages 대시보드에서 해당 프로젝트의 "Deployments" 탭을 봐요. GitHub Actions에서 배포 요청이 왔는지 확인하고, 안 왔다면 Secrets 값이 맞는지 재확인하세요. API 토큰은 한 번 저장하면 다시 볼 수 없어서 실수를 눈치채기 어렵거든요.

**상황 3: 무료 플랜 빌드 한도 초과**
Cloudflare Pages 무료 플랜은 월 500회 빌드예요. cron을 매시간 설정하면 한 달에 720회가 되어서 한도를 초과해요. cron을 하루 1회 이하로 줄이거나, 변경이 있을 때만 빌드되도록 조건 분기를 추가하는 방법을 써야 해요.

참고로 놓치기 쉬운 함정이 하나 더 있어요. `actions/checkout`에 `submodules: true`를 빠뜨리면 Hugo 테마가 빈 폴더로 체크아웃되고, 빌드가 에러 없이 성공하면서 테마가 적용 안 된 빈 페이지가 배포돼요. 에러 메시지가 없어서 원인 찾기가 더 어렵죠.

---

## 앞으로 주시할 것들

- **핵심 정리**:
  - 60일 비활성화 정책이 가장 흔한 cron 실패 원인이에요
  - Hugo 버전은 반드시 고정하세요. `latest`는 언제 터질지 모르는 시한폭탄이에요
  - Cloudflare Pages 무료 500회 빌드 한도를 cron 주기 설계 전에 계산하세요
  - 이중 트리거(`schedule` + `push`)가 단일 cron보다 안정적이에요

GitHub Actions는 비활성 정책을 더 세밀하게 조정하는 방향으로 움직이고 있어요. Cloudflare도 Workers와 Pages를 통합하는 작업을 진행 중이라서, 배포 방식 자체가 조금씩 달라질 수 있어요. Chris Wiegman이 2026년 1월 Cloudflare Workers로 전환한 사례처럼, Pages에서 Workers로 이동하는 선택지도 앞으로 더 자주 보게 될 거예요.

당장 파이프라인이 멈춰 있다면, GitHub Actions 탭을 열어서 워크플로우가 활성화 상태인지 먼저 확인해보세요. 대부분의 문제는 거기서 시작되니까요.

---

*참고 자료: [Cloudflare Pages Hugo 공식 가이드](https://developers.cloudflare.com/pages/framework-guides/deploy-a-hugo-site/), [GitHub Actions 스케줄 트리거 공식 문서](https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows#schedule)*

## 참고자료

1. [Hugo를 사용하여 블로그를 구축하고 Cloudflare Pages에 배포하기 | Heyjude's Blog](https://www.heyjude.blog/ko/posts/deploy-hugo-to-cloudflare/)
2. [Hugo · Cloudflare Pages docs](https://developers.cloudflare.com/pages/framework-guides/deploy-a-hugo-site/)
3. [Deploying My Hugo Site to Cloudflare Workers - Chris Wiegman](https://chriswiegman.com/2026/01/deploying-my-hugo-site-to-cloudflare-workers/)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-white-dice-with-a-black-github-logo-on-it-HLQDfaJUTVI)*
