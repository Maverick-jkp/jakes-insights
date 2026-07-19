---
title: "GitHub Actions cron 스케줄 안 돌아갈 때 원인 분석과 Cloudflare Pages 배포 연동 문제"
date: 2026-04-22T20:51:05+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "cron", "Next.js"]
description: "GitHub Actions cron 스케줄이 silent fail되는 3가지 원인과 60일 비활성 자동 비활성화 메커니즘을 분석합니다. Cloudflare Pages 자체 CI와 충돌 시 Wrangler 인증 오류 해결법까지 정리했습니다."
image: "/images/20260422-github-actions-cron-스케줄-실제로-안-.webp"
technologies: ["Next.js", "Node.js", "GitHub Actions", "Cloudflare"]
faq:
  - question: "GitHub Actions cron 스케줄 설정했는데 왜 실행이 안 되나요"
    answer: "GitHub Actions cron 스케줄 실제로 안 돌아갈 때 원인 분석을 해보면 크게 세 가지가 문제예요. 저장소에 60일 이상 커밋 활동이 없으면 스케줄이 자동 비활성화되고, 피크 시간대에는 수 시간씩 지연될 수 있으며, yml 파일이 기본 브랜치(main)에 없으면 아예 무시돼요. 이 세 가지를 먼저 확인한 뒤 다른 원인을 찾는 게 순서예요."
  - question: "GitHub Actions schedule 60일 자동 비활성화 막는 방법"
    answer: "repository_dispatch 트리거를 워크플로우에 함께 추가하면 수동 실행이 가능해지고 GitHub가 이를 활동으로 인식해 자동 비활성화를 방지할 수 있어요. 매월 한 번 더미 커밋을 만드는 보조 스케줄을 추가하는 방식도 실무에서 자주 쓰여요."
  - question: "Cloudflare Pages 배포 연동 GitHub Actions cron 같이 쓸 때 이중 빌드 문제 해결법"
    answer: "GitHub Actions cron 스케줄 실제로 안 돌아갈 때 원인 분석과 Cloudflare Pages 배포 연동을 함께 다룰 때, 이중 빌드 충돌이 자주 발생해요. Cloudflare Pages 대시보드에서 'Build Automatically' 옵션을 끄고, GitHub Actions의 wrangler-action으로 배포를 단일화하면 두 빌드가 충돌하는 문제를 해결할 수 있어요."
  - question: "wrangler-action Cloudflare Pages 배포 권한 오류 조용히 실패하는 이유"
    answer: "Workers용 API 토큰과 Pages용 API 토큰은 필요한 권한 스코프가 달라서, Workers용 토큰으로 Pages 배포를 시도하면 명확한 오류 없이 조용히 실패해요. Cloudflare 대시보드에서 API 토큰에 'Cloudflare Pages: Edit' 권한이 포함되어 있는지 반드시 확인해야 해요."
  - question: "GitHub Actions cron 표현식 한국 시간으로 설정하면 안 되는 이유"
    answer: "GitHub Actions의 cron 표현식은 UTC 기준으로 동작하기 때문에 한국 시간(KST)을 그대로 입력하면 의도한 시간보다 9시간 늦게 실행돼요. 예를 들어 한국 시간 오전 9시에 실행하려면 UTC 기준인 '0 0 * * *'으로 설정해야 해요."
aliases:
  - "/tech/2026-04-22-github-actions-cron-스케줄-실제로-안-돌아갈-때-원인-분석-cloudfla/"

---

GitHub Actions cron 설정했는데 안 돌아가죠? yml 문법은 멀쩡한데 워크플로우가 그냥 조용히 죽어있는 상황, 생각보다 훨씬 흔해요. Cloudflare Pages 배포까지 연동해놨다면 원인이 두 레이어에 걸쳐 있어서 진단이 더 복잡해지고요.

> **핵심 요약**
> - GitHub Actions `schedule` 트리거는 공식 문서 기준으로 최대 수 시간까지 지연될 수 있고, 저장소 비활성 상태에서는 스케줄 자체가 자동 비활성화돼요.
> - Cloudflare Pages는 자체 CI 빌드와 GitHub Actions 연동이 충돌하면, 두 빌드가 동시에 돌거나 Wrangler 인증 오류로 배포가 실패하는 패턴이 자주 나와요.
> - `push` 없이 `schedule`만 쓰는 저장소는 60일 이상 비활성 상태로 분류되어 스케줄이 자동 정지돼요.
> - Workers용 API 토큰으로 Pages 배포를 시도하면 조용히 실패해요. 인증 스코프가 달라요.

---

## cron이 안 돌아가는 진짜 이유 세 가지

**첫째, 지연 문제.** GitHub 공식 문서는 `schedule` 트리거의 실행 시간을 보장하지 않는다고 명시해요. UTC 기준 월~금 오전 피크 시간대에는 수 시간씩 밀리는 경우도 있어요. `0 9 * * *`으로 오전 9시 잡아놨는데 실제로는 오전 11시에 실행되는 식이죠.

**둘째, 자동 비활성화.** 이게 핵심이에요. GitHub는 저장소에 60일 이상 커밋 활동이 없으면 스케줄 워크플로우를 자동 일시 정지해요. `schedule`만 단독으로 쓰는 저장소라면 코드 변경 없이 60일이 지나는 순간, 아무 알림 없이 cron이 멈춰요. GitHub [Workflow disabling policy](https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows#schedule)에 명시된 내용이에요.

**셋째, 브랜치 불일치.** `schedule` 트리거는 항상 기본 브랜치(`main`)를 기준으로 실행돼요. yml 파일이 다른 브랜치에만 있거나 수정이 기본 브랜치에 반영 안 된 상태면, 변경 사항이 아예 무시돼요.

이 세 가지 중 하나라도 해당된다면, Cloudflare 연동 보기 전에 여기부터 확인해야 해요.

---

## Cloudflare Pages 연동의 함정

### 이중 빌드 충돌

Cloudflare Pages는 GitHub 저장소와 연결되면 push 이벤트를 자체적으로 감지해서 빌드를 돌려요. 여기에 GitHub Actions로 별도 배포 워크플로우까지 만들면, 같은 커밋에 두 개의 빌드가 동시에 실행되는 상황이 생겨요.

리소스 낭비만의 문제가 아니에요. 두 빌드가 서로 다른 환경 변수나 빌드 명령을 쓰면 결과물이 달라질 수 있거든요. Medialesson 팀이 공유한 사례에서도 이 이중 빌드 문제를 해결하기 위해 Cloudflare Pages 자동 빌드를 비활성화하고 GitHub Actions로 단일화하는 방식을 택했어요.

해결 방법은 간단해요. Cloudflare Pages 대시보드에서 **"Build Automatically"** 옵션을 끄고, GitHub Actions에서 Wrangler를 통해 배포만 담당하게 하면 돼요.

### API 토큰 스코프 불일치

`cloudflare/wrangler-action` 쓸 때 가장 자주 보이는 오류가 인증 실패예요. Workers 배포와 Pages 배포에 필요한 API 토큰 권한이 달라요.

| 배포 대상 | 필요한 API 토큰 권한 |
|-----------|---------------------|
| Cloudflare Workers | `Workers Scripts: Edit` |
| Cloudflare Pages | `Cloudflare Pages: Edit` |
| 둘 다 사용 | 두 권한 모두 포함 |

Workers용 토큰으로 Pages 배포를 시도하면 조용히 실패하거나, 권한 오류가 워크플로우 로그에 애매하게 남아요. Cloudflare 공식 문서에서도 토큰 권한 범위를 명확히 나눠서 설정하라고 권고하고 있어요.

### 올바른 스케줄 + Pages 배포 구조

```
schedule 트리거 발동
→ GitHub Actions 워크플로우 실행
→ 빌드 (Node.js/Next.js 등)
→ wrangler-action으로 Cloudflare Pages에 직접 배포
→ Cloudflare Pages 자동 빌드는 비활성화 상태 유지
```

이 구조에서 `schedule`이 안 돌아가면, Cloudflare 쪽 문제가 아니라 GitHub Actions cron 자체 문제인 경우가 대부분이에요.

---

## 원인별 진단 체크리스트

**GitHub Actions 레벨:**
- 저장소 Settings → Actions → General에서 워크플로우 활성화 상태 확인
- `push` 활동이 60일 이내에 있었는지 확인 (없으면 스케줄 자동 정지)
- yml 파일이 기본 브랜치에 있는지 확인
- cron 표현식이 UTC 기준인지 확인 (한국 시간으로 적으면 안 돼요)

**Cloudflare 연동 레벨:**
- API 토큰에 `Cloudflare Pages: Edit` 권한 포함 여부 확인
- `CLOUDFLARE_ACCOUNT_ID` 시크릿 정확히 설정되어 있는지 확인
- Cloudflare Pages 대시보드에서 자동 빌드 비활성화 상태 확인
- wrangler-action 버전 확인 (2026년 4월 기준 v3 계열 권장)

---

## 시나리오별 해결법

**60일 비활성화 문제라면?**
`repository_dispatch` 트리거를 같이 달아두면 수동 실행이 가능해지고, GitHub Actions가 이를 활동으로 인식해서 자동 비활성화를 막을 수 있어요. 매월 한 번 더미 커밋을 만드는 보조 스케줄을 추가하는 방식도 쓰여요.

**인증 오류로 Pages 배포가 실패한다면?**
Cloudflare 대시보드에서 API 토큰 새로 만들 때 "Cloudflare Pages: Edit" 항목 체크하고, GitHub Secrets에 `CLOUDFLARE_API_TOKEN`으로 등록하세요. 기존에 Workers용 토큰 그대로 쓰고 있었다면 반드시 교체해야 해요.

**빌드는 성공인데 배포가 반영 안 된다면?**
Cloudflare Pages 자동 빌드와 GitHub Actions가 동시에 돌고 있는 경우예요. Pages 대시보드 Git 연동 섹션에서 자동 배포를 끄고, wrangler-action이 단독으로 배포를 담당하게 하면 해결돼요.

---

## 정리하면

문제는 보통 GitHub 레벨에서 먼저 발생하고, Cloudflare 레벨에서 증폭돼요.

- 스케줄 자동 비활성화(60일 룰)가 가장 흔한 1차 원인이에요
- API 토큰 스코프 불일치가 침묵하는 배포 실패를 만들어요
- 이중 빌드 구조는 결과물 불일치와 디버깅 난이도를 높여요
- yml 파일 위치와 cron 표현식 시간대는 기본 중의 기본이에요

지금 바로 Actions 탭에서 마지막 스케줄 실행이 언제였는지 확인해 보세요. 아무 기록도 없다면 60일 비활성화가 이미 일어났을 가능성이 높아요. Cloudflare Pages 연동을 새로 설정하거나 정비 중이라면, API 토큰 권한 범위 재확인이 가장 먼저예요.

디버깅의 절반은 "어디서 멈췄는지 아는 것"이에요. 로그 찾았나요?

## 참고자료

1. [GitHub - cloudflare/wrangler-action: 🧙‍♀️ easily deploy cloudflare workers applications using wrangl](https://github.com/cloudflare/wrangler-action)
2. [GitHub Actions · Cloudflare Workers docs](https://developers.cloudflare.com/workers/ci-cd/external-cicd/github-actions/)
3. [Scheduled Builds for Cloudflare Deployments with GitHub Actions | by BEN ABT | Medialesson | Medium](https://medium.com/medialesson/scheduled-builds-for-cloudflare-deployments-with-github-actions-93341a112432)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-white-dice-with-a-black-github-logo-on-it-HLQDfaJUTVI)*
