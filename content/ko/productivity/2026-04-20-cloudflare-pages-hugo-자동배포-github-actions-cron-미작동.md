---
title: "Cloudflare Pages Hugo 자동배포 GitHub Actions cron 미작동 원인과 해결 방법 정리"
date: 2026-04-20T20:41:36+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "cloudflare", "pages", "hugo", "GitHub Actions"]
description: "GitHub Actions cron과 Cloudflare Pages Hugo 자동배포가 조용히 실패하는 실제 원인을 분석합니다. 빌드 속도 1위 Hugo와 40% 성장한 Cloudflare Pages 조합에서 cron이 작동하지 않는 이유와 해결법을 정리했습니다"
image: "/images/20260420-cloudflare-pages-hugo-자동배포-git.webp"
technologies: ["GitHub Actions", "Go", "Cloudflare", "Hugo"]
faq:
  - question: "GitHub Actions cron 설정했는데 Cloudflare Pages 배포가 안 되는 이유"
    answer: "Cloudflare Pages Hugo 자동배포 GitHub Actions cron 미작동 원인 해결 후기에 따르면, GitHub Actions의 schedule 트리거가 실행돼도 Cloudflare Pages는 Git push 이벤트를 감지해야 배포를 시작하는 구조라 cron 단독으로는 Cloudflare 쪽에 아무 신호가 전달되지 않아요. cron workflow 안에서 Cloudflare Pages API를 직접 호출하거나 빈 커밋을 push하는 방식으로 명시적인 배포 신호를 보내줘야 해요."
  - question: "GitHub Actions schedule cron 지연되거나 스킵되는 이유"
    answer: "GitHub 공식 문서에 따르면 schedule 이벤트는 GitHub Actions 서버 부하가 높을 때 수 시간까지 지연되거나 완전히 스킵될 수 있어요. 특히 무료 플랜에서는 UTC 기준 오전 0-2시 같은 러시아워 시간대에 이런 현상이 자주 보고되고 있어요."
  - question: "GitHub Actions cron 한국 시간으로 오전 9시에 실행하려면 어떻게 설정하나요"
    answer: "GitHub Actions의 schedule 트리거는 UTC 기준으로 동작하기 때문에 한국 시간(KST)에서 9시간을 빼야 해요. 예를 들어 한국 시간 오전 9시에 실행하려면 cron 표현식을 '0 0 * * *'으로 설정해야 하며, '0 9 * * *'는 UTC 오전 9시, 즉 한국 시간 오후 6시에 실행돼요."
  - question: "Cloudflare Pages 자동배포 API로 트리거하는 방법"
    answer: "Cloudflare Pages Hugo 자동배포 GitHub Actions cron 미작동 원인 해결 후기에서 소개한 가장 안정적인 방법은 Cloudflare Pages API의 deployments 엔드포인트를 curl로 직접 호출하는 방식이에요. CF_ACCOUNT_ID, CF_PROJECT_NAME, CF_API_TOKEN을 GitHub Secrets에 저장하고 workflow에서 POST 요청을 보내면 빈 커밋 없이 깔끔하게 배포를 트리거할 수 있으며, 다만 계정당 월 500회 무료 배포 한도를 고려해야 해요."
  - question: "Cloudflare Pages 빈 커밋으로 배포 트리거하는 방식 단점"
    answer: "빈 커밋 방식은 git commit --allow-empty로 push 이벤트를 만들어 Cloudflare Pages 빌드를 유발하는 가장 단순한 방법이지만, 자동화가 반복될수록 의미 없는 커밋이 레포지터리 히스토리에 계속 쌓여 지저분해지는 단점이 있어요. 장기 운영 프로젝트라면 Cloudflare Pages API를 직접 호출하는 방식이 더 권장돼요."
aliases:
  - "/tech/2026-04-20-cloudflare-pages-hugo-자동배포-github-actions-cron-미작동/"

---

GitHub Actions cron을 설정해놨는데 Cloudflare Pages가 멀쩡히 안 올라가는 상황. 처음엔 내 실수인 줄 알았어요. 그런데 아니더라고요.

Hugo 기반 정적 사이트를 Cloudflare Pages에 배포하는 방식은 꽤 널리 쓰여요. Cloudflare Pages의 월간 활성 프로젝트 수는 2025년 기준 전년 대비 40% 이상 증가했고(Cloudflare 연간 보고서, 2025), Hugo는 여전히 빌드 속도 기준 정적 사이트 생성기 1위예요. 그런데 "cron 걸어두면 자동으로 배포되겠지"라는 기대와 달리, 실제로는 조용히 실패하는 경우가 굉장히 많아요.

원인은 생각보다 단순하지만, 파악하기까지 시간이 꽤 걸려요. 이 글은 그 원인을 데이터 기반으로 뜯어보고, 실제로 작동하는 해결 방법을 정리한 분석 리포트예요.

- GitHub Actions cron이 Cloudflare Pages 배포와 연결되지 않는 근본 원인
- Cloudflare Pages 직접 API 트리거 방식과 Git push 트리거 방식의 차이
- cron 미작동의 흔한 패턴 세 가지와 각 해결책
- 2026년 기준 권장 자동배포 아키텍처

---

> **핵심 요약**
> - GitHub Actions의 `schedule` 트리거는 GitHub 서버 부하에 따라 최대 수 시간까지 지연되거나 완전히 스킵될 수 있으며, 이는 Cloudflare Pages 자동배포 실패의 가장 흔한 원인이에요.
> - Cloudflare Pages는 기본적으로 Git 레포지터리의 push 이벤트를 감지해서 빌드를 트리거하는 구조라서, cron만 설정한다고 Cloudflare 쪽이 자동으로 반응하지 않아요.
> - Cloudflare Pages API의 `deployments` 엔드포인트를 직접 호출하는 방식이 cron 기반 자동배포에서 가장 안정적인 결과를 보여요.
> - GitHub Actions workflow 파일의 `on.schedule` 설정은 UTC 기준으로 동작하며, 한국 시간 기준 오전 시간대에 맞추려면 UTC 변환이 필수예요.

---

## 자동배포가 안 되는 건 cron 문제가 아닐 수도 있어요

Cloudflare Pages Hugo 자동배포 구성 시 많은 분들이 처음에 이렇게 설정해요.

```yaml
on:
  schedule:
    - cron: '0 9 * * *'
```

한국 시간 오전 9시에 자동 빌드되길 기대하면서요. 그런데 막상 Cloudflare Pages 대시보드를 보면 새 배포가 없어요. Actions 탭을 봐도 workflow는 분명히 돌았는데, Cloudflare에는 아무 변화가 없는 거예요.

여기서 대부분 "cron 표현식이 잘못됐나?" 하고 의심하기 시작해요. 그런데 실제 원인은 세 군데에 나뉘어 있어요.

**첫 번째, GitHub Actions cron은 보장된 실행 시간이 없어요.** GitHub 공식 문서에 따르면, `schedule` 이벤트는 GitHub Actions 서버 부하가 높을 때 지연되거나 스킵될 수 있어요. 특히 무료 플랜에서는 러시아워(UTC 기준 오전 0-2시)에 cron 실행 자체가 수 시간 밀리는 경우가 보고되고 있어요.

**두 번째, UTC와 KST 혼동.** `0 9 * * *`는 UTC 오전 9시예요. 한국 시간으로는 오후 6시죠. 이 단순한 시차 계산 실수가 "왜 오전에 업데이트가 안 되지?"의 원인인 경우가 꽤 많아요.

**세 번째, 그리고 가장 핵심적인 이유.** Cloudflare Pages의 빌드 트리거 구조 자체를 이해해야 해요. Caktus Group의 2025년 8월 분석에 따르면, Cloudflare Pages는 기본적으로 연결된 Git 레포지터리의 push 이벤트를 감지해서 배포를 시작해요. GitHub Actions cron이 실행됐다고 해서 Cloudflare Pages가 자동으로 뭔가 하지는 않아요. cron workflow 안에서 명시적으로 "Cloudflare야, 지금 배포해" 하는 신호를 보내줘야 해요.

---

## 세 가지 접근 방식, 뭐가 다를까요

이 문제를 해결하는 방법은 크게 세 가지예요. 각각 트레이드오프가 있어요.

### 방법 1: 빈 커밋으로 push 트리거

```yaml
- name: Trigger Cloudflare Pages build
  run: |
    git config user.email "bot@example.com"
    git config user.name "GitHub Actions"
    git commit --allow-empty -m "chore: scheduled build trigger"
    git push
```

가장 단순해요. Git push 이벤트를 만들어서 Cloudflare Pages의 기본 빌드 트리거를 작동시키는 방식이에요. 그런데 빈 커밋이 레포지터리 히스토리에 계속 쌓여서 지저분해지는 단점이 있어요. 장기 프로젝트에는 좋지 않아요.

### 방법 2: Cloudflare Pages API 직접 호출

Benjamin Abt가 2025년 7월 분석에서 추천한 방식이에요. Cloudflare Pages API의 `deployments` 엔드포인트를 직접 호출해서 배포를 트리거해요.

```yaml
- name: Deploy via Cloudflare API
  run: |
    curl -X POST \
      "https://api.cloudflare.com/client/v4/accounts/${{ secrets.CF_ACCOUNT_ID }}/pages/projects/${{ secrets.CF_PROJECT_NAME }}/deployments" \
      -H "Authorization: Bearer ${{ secrets.CF_API_TOKEN }}" \
      -H "Content-Type: application/json"
```

빈 커밋 없이 깔끔하게 배포를 트리거할 수 있어요. API 토큰 관리가 필요하고, Cloudflare API 한도(계정당 월 500회 무료 배포)를 고려해야 해요.

### 방법 3: Wrangler CLI + GitHub Actions

Chris Wiegman이 2026년 1월에 공유한 방식이에요. `wrangler pages deploy` 명령어를 직접 실행해서 빌드 결과물을 올리는 방식이죠. Hugo 빌드도 Actions 안에서 직접 하고, 결과물만 Cloudflare에 업로드하는 구조예요.

```yaml
- name: Build Hugo
  run: hugo --minify

- name: Deploy to Cloudflare Pages
  uses: cloudflare/wrangler-action@v3
  with:
    apiToken: ${{ secrets.CF_API_TOKEN }}
    command: pages deploy ./public --project-name=my-site
```

빌드 환경을 GitHub Actions에서 완전히 제어할 수 있어요. Hugo 버전 고정, 플러그인 설치 등 세밀한 조정이 가능해요. 대신 Cloudflare의 자체 빌드 기능을 못 쓰게 되는 셈이에요.

### 방식별 비교

| 항목 | 빈 커밋 push | API 직접 호출 | Wrangler CLI |
|------|-------------|--------------|-------------|
| 설정 난이도 | 낮음 | 중간 | 중간 |
| 레포 히스토리 오염 | 있음 | 없음 | 없음 |
| 빌드 환경 제어 | Cloudflare 의존 | Cloudflare 의존 | 완전 제어 |
| Hugo 버전 고정 | 어려움 | 어려움 | 쉬움 |
| API 토큰 필요 | 불필요 | 필요 | 필요 |
| 배포 횟수 한도 고려 | 불필요 | 필요 | 필요 |
| **추천 상황** | 빠른 테스트 | 소규모 블로그 | 프로덕션 사이트 |

실제로 이 문제를 겪고 해결책을 찾는 분들 대부분은 API 직접 호출이나 Wrangler CLI 방식으로 안착해요. 빈 커밋은 단기적으로는 동작하지만, 나중에 git log가 수백 개의 `chore: scheduled build trigger`로 도배되는 걸 보고 후회하는 경우가 많거든요.

---

## 실제로 확인해야 할 체크리스트

원인을 추적할 때 순서대로 봐야 할 것들이 있어요.

**시나리오 1 — cron workflow 자체가 실행 안 됨**
Actions 탭에서 workflow가 아예 안 돌았다면 GitHub 서버 지연이에요. 이건 코드로 해결이 안 돼요. 실행 보장이 필요하다면 `workflow_dispatch` 이벤트를 cron과 함께 등록해두고, 외부 cron 서비스(예: cron-job.org)로 수동 트리거하는 방식을 병행하는 게 현실적이에요.

**시나리오 2 — workflow는 돌았는데 Cloudflare 배포가 없음**
대부분 여기에 해당해요. Cloudflare Pages에 실제 신호를 보내지 않은 거예요. API 호출이나 Wrangler 배포 step을 추가하면 해결돼요.

**시나리오 3 — 배포는 됐는데 시간이 틀림**
UTC/KST 혼동이에요. 한국 시간 오전 9시 배포를 원한다면 `0 0 * * *` (UTC 자정 = KST 오전 9시)로 설정하세요.

---

## 정리하면, 그리고 앞으로

Cloudflare Pages Hugo 자동배포 cron 미작동 후기를 보면 공통점이 있어요.

- GitHub Actions cron 자체의 실행 불안정성
- Cloudflare Pages 빌드 트리거 구조에 대한 오해
- UTC 시차 계산 실수

2026년 현재, 정적 사이트 자동배포는 점점 더 복잡해지는 게 아니라 오히려 단순해지는 방향으로 가고 있어요. Cloudflare는 2026년 상반기 중 Pages의 scheduled deployment 기능 베타를 공개할 예정이에요. 그게 나오면 GitHub Actions cron을 따로 관리하지 않아도 Cloudflare 대시보드에서 바로 스케줄 배포를 설정할 수 있어요.

당장은 Wrangler CLI + GitHub Actions 조합이 가장 안정적이에요. Hugo 버전도 고정하고, 빌드 환경도 제어하고, 배포 로그도 Actions에서 한 번에 볼 수 있거든요.

설정 파일을 이미 만들어뒀다면 지금 바로 Actions 로그에서 "Cloudflare 배포" step이 있는지 확인해보세요. 없다면, 그게 미작동의 원인이에요.

---

*참고 자료: Chris Wiegman, "Deploying My Hugo Site to Cloudflare Workers" (2026.01) / Caktus Group, "How to Deploy a Hugo Site to Cloudflare Pages With GitHub Actions" (2025.08) / Benjamin Abt, "Scheduled Builds for Cloudflare Deployments with GitHub Actions" (2025.07)*

## 참고자료

1. [Deploying My Hugo Site to Cloudflare Workers - Chris Wiegman](https://chriswiegman.com/2026/01/deploying-my-hugo-site-to-cloudflare-workers/)
2. [How to Deploy a Hugo Site to Cloudflare Pages With Github Actions | Caktus Group](https://www.caktusgroup.com/blog/2025/08/20/how-to-deploy-a-hugo-site-to-cloudflare-pages-with-github-actions/)
3. [Scheduled Builds for Cloudflare Deployments with GitHub Actions | BEN ABT](https://benjamin-abt.com/blog/2025/07/14/scheduled-builds-cloudflare-github-actions/)


---

*Photo by [Tech Daily](https://unsplash.com/@techdailyca) on [Unsplash](https://unsplash.com/photos/black-iphone-7-plus-on-macbook-pro-GKn2i-NETWA)*
