---
title: "Hugo 블로그 Cloudflare Pages 배포 시 GitHub Actions cron 트리거 안될 때 원인과 해결"
date: 2026-05-04T21:06:18+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "hugo", "\ube14\ub85c\uadf8", "cloudflare", "GitHub Actions"]
description: "Hugo 블로그 GitHub Actions cron이 실행 안 될 때, 60일 이상 커밋 없으면 schedule 워크플로우가 자동 비활성화됩니다. Cloudflare Pages 직접 업로드 방식의 트리거 구조 차이와 재활성화 방법을 설명합니다."
image: "/images/20260504-hugo-블로그-cloudflare-pages-배포-g.webp"
technologies: ["GitHub Actions", "Go", "Cloudflare", "Hugo"]
faq:
  - question: "GitHub Actions cron 트리거 설정했는데 워크플로우가 자동으로 안 실행되는 이유"
    answer: "GitHub는 기본 브랜치에 60일 이상 커밋이 없으면 schedule 워크플로우를 자동으로 비활성화해요. Actions 탭에서 해당 워크플로우를 선택했을 때 'Enable workflow' 버튼이 보이면 비활성 상태인 것이므로, 버튼을 눌러 재활성화한 뒤 workflow_dispatch 트리거로 수동 테스트를 먼저 진행해 보세요."
  - question: "Hugo 블로그 Cloudflare Pages 배포 GitHub Actions cron 트리거 안될 때 원인 해결 방법"
    answer: "Hugo 블로그 Cloudflare Pages 배포 GitHub Actions cron 트리거 안될 때 원인은 크게 세 가지예요. 저장소 비활성화로 인한 워크플로우 중단, Cloudflare API 토큰 권한 누락(CLOUDFLARE_API_TOKEN과 CLOUDFLARE_ACCOUNT_ID 모두 필요), Hugo publishDate 미래 날짜 설정과 --buildFuture 플래그 충돌이에요. 각 항목을 순서대로 점검하면 대부분 해결돼요."
  - question: "Cloudflare Pages에서 Hugo 예약 발행 자동 빌드 구현하는 방법"
    answer: "Cloudflare Pages 자체에는 cron 빌드 기능이 없기 때문에, Git 연동 방식이 아닌 GitHub Actions + wrangler pages deploy 조합을 사용해야 해요. Actions의 schedule 트리거로 원하는 시간에 빌드를 실행하고, npx wrangler pages deploy ./public 명령어로 Cloudflare에 직접 업로드하는 구조로 구성하면 예약 발행이 가능해요."
  - question: "wrangler pages deploy 명령어 에러 없이 실행됐는데 실제 배포가 안 되는 경우"
    answer: "Cloudflare API 토큰에 Cloudflare Pages:Edit 권한이 빠져 있거나, CLOUDFLARE_ACCOUNT_ID 환경 변수가 누락된 경우 wrangler가 에러 없이 종료되면서도 실제 배포가 이루어지지 않아요. GitHub Actions 워크플로우의 env 블록에 CF_API_TOKEN과 CF_ACCOUNT_ID 두 값을 모두 설정했는지 반드시 확인해 보세요."
  - question: "Hugo publishDate 미래 날짜 포스트가 빌드 후에도 블로그에 안 나타남"
    answer: "Hugo는 기본적으로 publishDate가 미래인 포스트를 빌드에서 제외해요. 해당 포스트를 강제로 포함하려면 hugo --buildFuture 플래그를 붙여야 하지만, cron으로 예약 발행 날짜에 맞춰 자동 빌드하는 구조라면 오히려 플래그 없이 hugo만 실행해야 해당 시점 이전 콘텐츠만 정상 노출돼요."
---

GitHub Actions `schedule` 트리거를 설정했는데 빌드가 멈췄어요. 로그엔 아무것도 없고, 워크플로우는 그냥 조용히 실행이 안 돼요. Hugo 블로그를 Cloudflare Pages에 배포하는 파이프라인에서 이 문제를 겪는 개발자가 꽤 늘었어요. 단순한 설정 실수처럼 보이지만, 실제로는 GitHub, Cloudflare, Hugo가 맞물리는 구조적인 문제예요.

> **핵심 요약**
> - GitHub Actions `schedule` 워크플로우는 기본 브랜치에 최근 60일간 커밋이 없으면 자동으로 비활성화돼요 (GitHub 공식 문서 기준).
> - Cloudflare Pages의 직접 업로드 방식은 Git 연동과 다르게 동작하기 때문에, Actions 트리거 조건을 별도로 맞춰야 해요.
> - Hugo의 `publishDate` 미래 날짜 설정이 cron 빌드에서 콘텐츠를 누락시키는 숨겨진 원인이 될 수 있어요.
> - `wrangler pages deploy` 명령어와 Cloudflare API 토큰 권한 범위를 정확히 맞추지 않으면 배포 단계에서 조용히 실패해요.

---

## cron 트리거, 갑자기 왜 안 될까요?

### GitHub Actions의 조용한 비활성화 정책

GitHub는 2022년부터 `schedule` 이벤트에 **비활성 저장소 자동 비활성화 정책**을 적용하고 있어요. 기본 브랜치(`main` 또는 `master`)에 60일 동안 커밋이 없으면, 예약 워크플로우가 실행을 멈춰요. GitHub 공식 문서에 명시된 내용이에요.

블로그 포스팅을 오랫동안 쉬거나, 초안만 쌓아두고 `draft: true`로 관리하다 보면 이 조건에 딱 걸려요. 워크플로우 파일을 삭제한 것도 아니고, 에러도 없는데 실행이 안 되는 거예요. 당연히 디버깅도 막막하죠.

확인 방법은 간단해요. GitHub 저장소 → **Actions** 탭 → 해당 워크플로우 선택 → 우측 상단 "Enable workflow" 버튼이 보이면 비활성 상태인 거예요.

### cron 스케줄 지연과 큐잉 문제

또 다른 원인은 GitHub의 **Actions 큐 지연**이에요. GitHub 공식 블로그에 따르면, `schedule` 이벤트는 지정한 시각에 정확히 실행되는 걸 보장하지 않아요. `*/5 * * * *` 같은 짧은 주기나 정각(`0 * * * *`) 시각대에는 수십 분씩 밀릴 수 있어요. Hugo 블로그에서 예약 발행용 cron을 돌린다면, 실행 자체는 됐는데 타이밍이 어긋나 콘텐츠가 안 보이는 상황이 생겨요.

---

## Cloudflare Pages 배포 파이프라인의 구조적 함정

### Git 연동 vs. 직접 업로드: 두 방식의 차이

Cloudflare Pages에 Hugo 블로그를 연결하는 방법은 크게 두 가지예요.

| 항목 | Git 연동 방식 | GitHub Actions + `wrangler` |
|------|------------|---------------------------|
| 트리거 | push 이벤트 자동 감지 | Actions 워크플로우 직접 호출 |
| cron 지원 | ❌ (Cloudflare 자체 미지원) | ✅ (Actions schedule 사용) |
| 빌드 환경 | Cloudflare 관리 | 직접 제어 |
| Hugo 버전 고정 | 환경 변수로 설정 | `actions/setup-go` 등 직접 |
| API 토큰 필요 | ❌ | ✅ (`Cloudflare Pages:Edit`) |
| 예약 발행 가능 | ❌ | ✅ |

Git 연동 방식은 push할 때만 빌드가 돼요. 예약 발행을 하고 싶다면 반드시 GitHub Actions + `wrangler pages deploy` 조합을 써야 해요. Cloudflare Pages 자체에는 cron 빌드 기능이 없거든요. Cloudflare Workers의 cron 기능과 헷갈리기 쉬운 부분이에요.

### API 토큰 권한과 `wrangler` 배포 실패

GitHub Actions에서 `wrangler pages deploy ./public` 명령어를 쓸 때, Cloudflare API 토큰에 정확히 `Cloudflare Pages:Edit` 권한이 있어야 해요. `Zone:Read`만 있거나 계정 수준 권한이 빠지면, 명령어가 에러 없이 실행됐다고 표시되면서도 실제 배포가 안 돼요.

Cloudflare 개발자 문서에 따르면, `wrangler`는 `CLOUDFLARE_API_TOKEN`과 `CLOUDFLARE_ACCOUNT_ID` 두 개의 환경 변수를 모두 요구해요. 계정 ID를 빠뜨리는 경우가 생각보다 많아요.

```yaml
- name: Deploy to Cloudflare Pages
  run: npx wrangler pages deploy ./public --project-name=my-hugo-blog
  env:
    CLOUDFLARE_API_TOKEN: ${{ secrets.CF_API_TOKEN }}
    CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CF_ACCOUNT_ID }}
```

### Hugo `publishDate`와 `--buildFuture` 플래그

예약 발행을 위해 Hugo 포스트에 미래 날짜를 `publishDate`로 설정했다면, 빌드 명령어에 `--buildFuture` 플래그를 붙여야 해요. 안 붙이면 그 포스트는 빌드에서 그냥 빠져요. 에러도 없이요.

그런데 반대로 cron으로 예약 발행 날짜에 맞춰 자동 빌드하는 구조라면, 빌드 명령어는 `--buildFuture` 없이 그냥 `hugo`로 써야 해당 날짜 이전 콘텐츠만 나와요. 목적에 따라 정반대의 설정이 필요한 셈이에요.

---

## 실제로 점검할 체크리스트

**시나리오 1: 워크플로우가 아예 실행 안 됨**

저장소에 60일 이상 커밋이 없었다면 비활성화됐을 가능성이 높아요. Actions 탭에서 워크플로우를 수동으로 재활성화하고, `workflow_dispatch` 트리거를 추가해서 수동 실행 테스트를 먼저 해보세요. 이후 더미 커밋이나 문서 업데이트로 활성 상태를 유지하는 게 깔끔해요.

**시나리오 2: 워크플로우는 실행됐는데 배포가 안 됨**

Actions 로그에서 `wrangler` 단계를 확인해요. `Authentication error`나 빈 출력이 보이면 토큰 문제예요. Cloudflare 대시보드 → **My Profile** → **API Tokens**에서 토큰 권한을 재점검하세요. `Cloudflare Pages:Edit` + 해당 계정 범위가 둘 다 있어야 해요.

**시나리오 3: 배포됐는데 새 포스트가 안 보임**

Hugo 빌드 로그에서 "Pages built"를 확인해요. 포스트 수가 예상보다 적다면 `publishDate`나 `draft: true` 상태를 점검하세요. `hugo --buildDrafts` 또는 `--buildFuture` 중 어느 게 필요한지 목적에 맞게 선택하면 돼요.

---

## 다음에 뭘 봐야 할까요?

Hugo + Cloudflare Pages + GitHub Actions 조합은 개인 블로그와 소규모 팀 문서 사이트에서 가장 많이 쓰이는 스택 중 하나예요. Cloudflare는 2025년 말 Pages와 Workers의 통합을 점진적으로 진행하고 있어서, 앞으로 `wrangler` 명령어 구조가 바뀔 수 있어요. Chris Wiegman이 2026년 1월에 Workers로 마이그레이션한 사례처럼, Pages에서 Workers로 이동하는 흐름도 생기고 있고요.

지금 당장 챙길 것:
- `workflow_dispatch` 트리거를 항상 같이 넣어 수동 테스트 루트를 열어두기
- `wrangler` 버전을 `package.json`에 고정 (`"wrangler": "3.x"`)
- Hugo 버전도 환경 변수 `HUGO_VERSION`으로 고정해서 Cloudflare 빌드와 Actions 빌드 환경 맞추기

cron 트리거 문제는 대부분 세 가지 중 하나예요. GitHub 비활성화 정책, Cloudflare API 권한 누락, 아니면 Hugo 빌드 플래그 미스매치. 하나씩 확인하면 생각보다 금방 찾을 수 있어요.

워크플로우 YAML을 공유할 수 있다면 댓글로 올려주세요. 같이 들여다볼게요.

## 참고자료

1. [Hugo · Cloudflare Pages docs](https://developers.cloudflare.com/pages/framework-guides/deploy-a-hugo-site/)
2. [Deploying My Hugo Site to Cloudflare Workers - Chris Wiegman](https://chriswiegman.com/2026/01/deploying-my-hugo-site-to-cloudflare-workers/)
3. [How I Fixed My CI/CD: Fast, Optimized, and Pro-Level Deploys (Hugo + Cloudflare) - Oli Miah](https://oli.bdtechx.com/blog/how-i-fixed-my-ci-cd-fast-optimized-and-pro-level-deploys-hugo-cloudflare/)


---

*Photo by [Conny Schneider](https://unsplash.com/@choys_) on [Unsplash](https://unsplash.com/photos/a-blue-background-with-lines-and-dots-xuTJZ7uD7PI)*
