---
title: "Cloudflare Pages Hugo 자동 배포가 끊기는 원인과 GitHub Actions cron 무시 문제 해결"
date: 2026-03-10T20:01:04+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "cloudflare", "pages", "hugo", "GitHub Actions"]
description: "GitHub Actions cron이 60일 비활동 시 자동 비활성화되고, Cloudflare Pages는 Git 커밋 없이 배포를 감지 못하는 두 가지 원인을 진단하고 Hugo 자동 배포를 복구하는 방법을 설명합니다."
image: "/images/20260310-cloudflare-pages-hugo-자동-배포-gi.webp"
technologies: ["GitHub Actions", "Go", "Cloudflare", "Hugo"]
faq:
  - question: "Cloudflare Pages Hugo 자동 배포 GitHub Actions cron 무시되는 원인 해결 방법"
    answer: "Cloudflare Pages Hugo 자동 배포에서 GitHub Actions cron이 무시되는 원인은 두 가지입니다. 저장소 활동이 60일 이상 없으면 GitHub가 스케줄 워크플로우를 자동 비활성화하고, Cloudflare Pages는 Git 커밋 기반으로만 배포를 감지하기 때문에 Actions가 실행돼도 커밋이 없으면 배포가 트리거되지 않습니다. Cloudflare Pages Deploy Hook URL을 생성해 Actions cron에서 POST 요청을 보내는 방식으로 두 문제를 동시에 해결할 수 있습니다."
  - question: "GitHub Actions schedule cron 60일 지나면 자동으로 꺼지나요"
    answer: "네, GitHub 공식 문서에 따르면 저장소에 60일 이상 활동이 없으면 GitHub가 스케줄 워크플로우를 자동으로 비활성화합니다. 비활성화 전에 이메일 알림이 발송되며, 알림을 받은 후 Actions 탭에서 워크플로우를 다시 활성화하면 됩니다. 워크플로우에 `workflow_dispatch`를 함께 설정해두면 비활성화 이후 수동 실행으로 빠르게 복구할 수 있습니다."
  - question: "Cloudflare Pages 커밋 없이 배포 트리거하는 방법"
    answer: "Cloudflare Pages는 Deploy Hook URL을 통해 Git 커밋 없이도 배포를 시작할 수 있습니다. Cloudflare Pages 대시보드에서 Deploy Hook을 생성한 뒤, 해당 URL로 HTTP POST 요청을 보내면 빌드와 배포가 자동으로 시작됩니다. GitHub Actions에서 `curl -X POST` 명령으로 이 URL을 호출하면 cron 기반 자동 배포가 완성됩니다."
  - question: "GitHub Actions cron UTC 시간 KST로 변환하는 법"
    answer: "GitHub Actions의 cron 표현식은 UTC 기준으로 동작하며, 한국 표준시(KST)는 UTC+9입니다. 예를 들어 KST 오전 9시에 배포하려면 cron 표현식을 `0 0 * * *`으로 설정해야 합니다. 또한 GitHub Actions 스케줄은 트래픽에 따라 최대 15~30분의 지연이 발생할 수 있으므로 정각 배포가 필수인 경우 여유 시간을 고려해야 합니다."
  - question: "Hugo 블로그 자동 배포 더미 커밋 방식 문제점"
    answer: "더미 커밋 방식은 의미 없는 파일 변경을 반복해서 저장소 히스토리를 오염시키고, 장기적으로 유지보수 부담이 높아집니다. Cloudflare Pages Hugo 자동 배포 환경에서는 GitHub Actions cron과 Deploy Hook을 조합하는 방식이 저장소를 오염시키지 않으면서 설정 복잡도도 낮아 대부분의 케이스에 권장됩니다. 빌드 환경을 직접 제어해야 하는 경우에만 Actions에서 직접 빌드하고 배포하는 방식을 선택하면 됩니다."
---

cron 표현식도 맞고, 워크플로우 파일도 문법 오류 없어 보이는데 Cloudflare Pages 배포가 뚝 끊겼어요. GitHub Actions 스케줄 설정을 분명히 했는데 왜 안 되는 건지 감이 안 잡히는 상황, 겪어봤죠?

원인은 두 가지가 동시에 작동해서예요.

---

> **핵심 요약**
> - GitHub Actions의 `schedule` 트리거는 저장소 활동이 60일 이상 없으면 GitHub가 자동으로 비활성화한다.
> - Cloudflare Pages는 Git 커밋 기반으로 배포를 감지하므로, Actions가 직접 API를 호출하지 않으면 트리거 자체가 누락된다.
> - Hugo 정적 사이트는 콘텐츠 변경이 적은 구간이 생기면 위 두 문제가 동시에 발생한다.
> - Cloudflare Pages Deploy Hook + GitHub Actions cron 조합으로 두 문제를 동시에 해결할 수 있다.

---

## 두 서비스가 배포를 다르게 인식해요

Hugo 같은 정적 사이트는 배포 주기가 불규칙해요. 한 달에 포스트 하나 올릴 수도 있고, 외부 API 데이터로 페이지를 주기적으로 재생성해야 할 수도 있어요. 그래서 자연스럽게 GitHub Actions `schedule` + Cloudflare Pages 조합이 등장하는데, 문제는 이 두 서비스가 서로 **다른 방식으로 배포를 인식**한다는 거예요.

- GitHub Actions는 "워크플로우를 실행"해요.
- Cloudflare Pages는 "Git 저장소의 변경(push)"을 감지해 배포해요.

Actions가 실행돼도 저장소에 실제 커밋이 없으면 Cloudflare Pages는 아무 반응을 안 해요. 그리고 저장소 활동 자체가 뜸해지면 GitHub가 스케줄 워크플로우를 꺼버려요. 이 두 가지가 맞물리면 자동 배포가 조용히 멈춰버리는 거예요.

## GitHub Actions cron이 멈추는 정확한 조건

GitHub 공식 문서에는 이렇게 명시돼 있어요:

> "If a repository has had no activity for 60 days, GitHub will disable scheduled workflows for that repository."

60일. 생각보다 짧죠. 콘텐츠 업데이트가 뜸한 블로그라면 두 달만 지나도 스케줄이 멈출 수 있어요.

그리고 `cron` 표현식 자체의 지연 문제도 있어요. GitHub Actions 스케줄은 UTC 기준으로 동작하고, **최대 15~30분의 지연**이 발생할 수 있어요. 트래픽이 몰리는 시간대에는 더 길어지기도 해요. 정각 배포가 필요한 경우라면 이 부분도 고려해야 해요.

## 해결책: Deploy Hook이 핵심이에요

Cloudflare Pages는 두 가지 방식으로 배포를 시작해요.

1. Git 저장소에 새 커밋이 push될 때
2. **Deploy Hook URL이 POST 요청을 받을 때**

두 번째가 핵심이에요. Deploy Hook은 Cloudflare Pages 대시보드에서 생성하는 고유 URL인데, 이 URL로 HTTP POST를 보내면 커밋 없이도 빌드와 배포가 시작돼요. GitHub Actions cron에서 이 URL을 호출하면 "커밋 없는 자동 배포"가 완성되는 거예요.

워크플로우 핵심 부분은 이렇게 생겼어요:

```yaml
on:
  schedule:
    - cron: '0 6 * * *'  # 매일 UTC 06:00
  workflow_dispatch:

jobs:
  trigger-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Cloudflare Pages Deploy Hook
        run: |
          curl -X POST "${{ secrets.CF_DEPLOY_HOOK_URL }}"
```

단 7줄이에요. 커밋도 필요 없고, Hugo 빌드를 Actions에서 돌릴 필요도 없어요. Cloudflare Pages가 알아서 Hugo 빌드를 해줘요.

## 세 가지 접근법 비교

| 기준 | Deploy Hook + cron | Actions 직접 빌드/배포 | 더미 커밋 |
|------|-------------------|----------------------|----------|
| 설정 복잡도 | 낮음 | 높음 | 중간 |
| 저장소 오염 | 없음 | 없음 | 있음 |
| 빌드 환경 제어 | Cloudflare 기본값 | 완전 제어 | Cloudflare 기본값 |
| 유지보수 부담 | 낮음 | 중간 | 높음 |
| 추천 여부 | ✅ 대부분 케이스 | ✅ 커스텀 빌드 필요 시 | ❌ |

더미 커밋 방식은 저장소 히스토리가 지저분해지고, 결국 "의미 없는 파일 변경"을 계속 만들어야 해요. 장기적으로 권장하지 않아요.

## 60일 비활성화 문제는 별도로 잡아야 해요

Deploy Hook 방식을 써도 저장소에 커밋이 안 생기면 GitHub가 스케줄 워크플로우를 비활성화할 수 있어요. 위 워크플로우 코드에 `workflow_dispatch`를 함께 넣은 이유가 이거예요. 스케줄이 멈췄을 때 수동으로 실행할 수 있고, 저장소 활동으로도 인식돼요.

GitHub는 비활성화 전에 이메일도 보내줘요. 알림 받으면 Actions 탭에서 워크플로우를 다시 활성화하면 돼요.

## 마무리: 체크리스트 세 가지

- **Cloudflare Pages Deploy Hook URL을 만들어 GitHub 시크릿에 저장했는가** — 커밋 없는 배포의 핵심이에요.
- **워크플로우에 `workflow_dispatch`가 있는가** — 60일 비활성화 후 빠르게 복구할 수 있어요.
- **cron 표현식이 UTC 기준으로 작성됐는가** — KST는 UTC+9이에요. 오전 9시 배포를 원하면 `0 0 * * *`이에요.

세 가지 다 맞는데도 배포가 안 된다면, GitHub Actions 탭에서 워크플로우가 "disabled" 상태인지 먼저 확인해보세요. 생각보다 많은 경우가 거기서 끝나거든요.

## 참고자료

1. [r/CloudFlare on Reddit: Github pages vs Cloudflare](https://www.reddit.com/r/CloudFlare/comments/1pwgio6/github_pages_vs_cloudflare/)
2. [Scheduled Builds for Cloudflare Deployments with GitHub Actions | by BEN ABT | Medialesson | Medium](https://medium.com/medialesson/scheduled-builds-for-cloudflare-deployments-with-github-actions-93341a112432)
3. [Deploying My Hugo Site to Cloudflare Workers - Chris Wiegman](https://chriswiegman.com/2026/01/deploying-my-hugo-site-to-cloudflare-workers/)


---

*Photo by [Daniil Komov](https://unsplash.com/@dkomow) on [Unsplash](https://unsplash.com/photos/laptop-screen-displaying-code-and-data-charts-GQOylIn892U)*
