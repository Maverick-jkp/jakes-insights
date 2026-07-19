---
title: "Hugo 블로그 Cloudflare Pages 자동배포 GitHub Actions cron 트리거 안 될 때 원인과 해결"
date: 2026-05-05T20:33:56+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "hugo", "\ube14\ub85c\uadf8", "cloudflare", "GitHub Actions"]
description: "Hugo 블로그 Cloudflare Pages 자동배포에서 GitHub Actions cron 트리거가 안 될 때, schedule 이벤트는 기본 브랜치에만 동작하며 60일 비활성 저장소는 자동 비활성화됩니다. 원인별 해결법을 정리했습니다."
image: "/images/20260505-hugo-블로그-cloudflare-pages-자동배포.webp"
technologies: ["GitHub Actions", "Go", "Cloudflare", "Hugo"]
faq:
  - question: "Hugo 블로그 Cloudflare Pages 자동배포 GitHub Actions cron 트리거 안 될 때 원인"
    answer: "GitHub Actions의 schedule 이벤트는 반드시 기본 브랜치(main 또는 master)에 워크플로우 파일이 있어야 동작해요. 또한 60일 이상 커밋이 없는 비활성 레포는 GitHub이 자동으로 예약 실행을 비활성화하기 때문에, Actions 탭에서 워크플로우를 수동으로 Enable 해줘야 해요."
  - question: "GitHub Actions cron 설정했는데 스케줄 배포가 안 되는 이유"
    answer: "가장 흔한 원인은 워크플로우 파일이 기본 브랜치가 아닌 다른 브랜치에 있거나, cron 표현식을 한국 시간(KST) 기준으로 잘못 작성한 경우예요. GitHub Actions의 cron은 UTC 기준으로 동작하므로, 한국 시간 오전 9시에 실행하려면 '0 0 * * *'으로 설정해야 해요."
  - question: "Cloudflare Pages 예약 자동 빌드 설정하는 방법"
    answer: "Cloudflare Pages에는 Netlify처럼 자체 스케줄 빌드 기능이 없어서, 외부 CI/CD를 통해 트리거를 직접 쏴줘야 해요. 가장 안정적인 방법은 Cloudflare API 토큰을 발급받아 GitHub Actions에서 curl로 Deploy Hook을 호출하는 방식이며, 이 방법은 Git 히스토리를 오염시키지 않아요."
  - question: "GitHub Actions schedule 60일 비활성화 재활성화 방법"
    answer: "GitHub는 60일 이상 커밋이 없는 레포의 schedule 이벤트를 자동으로 비활성화해요. 재활성화하려면 레포의 Actions 탭에서 해당 워크플로우를 찾아 Enable 버튼을 클릭하면 바로 적용돼요."
  - question: "Hugo 블로그 Cloudflare Pages 자동배포 GitHub Actions cron 트리거 안 될 때 해결 가장 안정적인 방법"
    answer: "Cloudflare Pages API Deploy Hook을 GitHub Actions에서 직접 호출하는 방법이 가장 안정적으로 권장돼요. 빈 커밋 푸시 방식보다 Git 히스토리가 깔끔하게 유지되고, Cloudflare 대시보드에서 빌드 로그를 일관되게 확인할 수 있어요."
aliases:
  - "/tech/2026-05-05-hugo-블로그-cloudflare-pages-자동배포-github-actions-cron/"

---

설정은 다 맞는 것 같은데 스케줄 배포가 아무것도 안 돼요. `schedule` 이벤트까지 넣었는데 Cloudflare Pages는 조용합니다. 이 문제로 시간을 버리는 개발자가 생각보다 많아요.

이 글에선 Hugo 블로그 Cloudflare Pages 자동배포 환경에서 GitHub Actions cron 트리거가 안 될 때 원인이 뭔지, 어떻게 고치는지 짚어볼게요.

> **핵심 요약**
> - GitHub Actions의 `schedule` 이벤트는 기본 브랜치(`main` 또는 `master`)에만 동작해요. 다른 브랜치에 워크플로우 파일이 있으면 cron이 실행되지 않아요.
> - GitHub는 공식 문서에서 "inactive repository"의 경우 60일 이후 예약 실행을 자동 비활성화한다고 명시하고 있어요.
> - Cloudflare Pages는 자체 스케줄 트리거 기능이 없어요. 예약 배포는 전적으로 외부 CI/CD에 의존해야 해요.
> - cron 표현식의 시간대는 UTC 기준이에요. 한국 시간(KST)과 9시간 차이가 있어서 의도한 시간에 안 돌 수 있어요.
> - Cloudflare Pages API를 직접 호출하는 방식이 가장 안정적인 우회책이에요.

---

## cron 트리거가 안 되는 이유, 구조부터 봐야 해요

Hugo 같은 정적 사이트 제너레이터(SSG)를 Cloudflare Pages에 올리는 선택이 2025-2026년 사이 확 늘었어요. 무료 티어가 넉넉하고 CDN 성능이 좋으니까요.

그런데 정적 사이트의 고질적인 문제가 있어요. **콘텐츠가 빌드 타임에 고정**된다는 거예요. 예약 발행, 매일 자동 빌드, 외부 API 데이터 갱신 같은 걸 하려면 누군가 주기적으로 "빌드해!" 명령을 내려야 해요.

자연스럽게 GitHub Actions의 `schedule` 이벤트가 등장하죠. 매일 오전 9시에 자동으로 Hugo 빌드 후 Cloudflare에 배포하는 그림. 근데 실제로 해보면... 안 돌아요.

GitHub Actions 공식 커뮤니티 포럼과 Stack Overflow에서 `schedule not triggering` 관련 이슈가 지속적으로 상위권에 올라와 있어요. 설정이 문제가 아니라, 구조를 모르고 쓰기 때문이에요.

### 원인 1: 워크플로우 파일이 기본 브랜치에 없어요

GitHub Actions의 `schedule` 이벤트는 **기본 브랜치에 있는 워크플로우 파일만 인식**해요. `develop` 브랜치나 `feature` 브랜치에 `.github/workflows/deploy.yml`을 넣어도 cron은 실행되지 않아요.

GitHub 공식 문서는 이를 명확히 해요:

> "Scheduled workflows run on the latest commit on the default or base branch."

기본 브랜치 이름이 `master`인 레포에 `main` 브랜치로 파일을 올리면? 역시 안 돼요. 레포 설정에서 기본 브랜치가 뭔지 먼저 확인하세요.

### 원인 2: 60일 비활성화 정책

GitHub는 활동이 없는 레포의 예약 실행을 자동으로 끊어요. **60일 이상 커밋이 없는 레포**의 경우 `schedule` 이벤트를 비활성화해요.

블로그 글을 오래 안 썼거나, Cloudflare Pages 쪽에서 직접 배포하고 GitHub에 커밋을 안 했다면 이 조건에 해당할 수 있어요. 이메일 알림이 오긴 하지만 놓치는 경우가 많아요.

재활성화는 간단해요. Actions 탭에서 워크플로우를 직접 "Enable"하면 돼요.

### 원인 3: cron 표현식의 시간대 착각

GitHub Actions의 cron 스케줄은 **UTC 기준**이에요. 한국 시간(KST)은 UTC+9이니까 9시간 차이가 있어요.

매일 아침 9시(KST)에 빌드하고 싶다면:

```yaml
# ❌ 잘못된 설정 (KST 기준으로 착각)
- cron: '0 9 * * *'

# ✅ 올바른 설정 (UTC 기준, 실제 KST 09:00)
- cron: '0 0 * * *'
```

이 실수 하나 때문에 새벽 6시에 빌드가 돌거나, 아예 안 도는 것처럼 보이는 경우가 꽤 있어요.

### 원인 4: Cloudflare Pages 자체엔 스케줄 배포 기능이 없어요

Cloudflare Pages는 **Git 푸시 이벤트 기반**으로만 자동 배포가 돼요. Netlify처럼 "Scheduled builds" 메뉴가 없어요.

결국 Hugo 블로그 Cloudflare Pages 자동배포를 예약으로 돌리려면 **외부에서 트리거를 쏴줘야** 해요. 이게 GitHub Actions가 필요한 이유이고, cron 설정을 정확히 해야 하는 이유예요.

---

## 해결 방법 세 가지, 뭘 골라야 할까요

### 비교: 배포 트리거 방식

| 항목 | Git 빈 커밋 푸시 | Cloudflare Pages API 직접 호출 | Wrangler CLI 사용 |
|------|-----------------|-------------------------------|------------------|
| 구현 난이도 | 낮음 | 중간 | 중간 |
| 안정성 | 보통 | 높음 | 높음 |
| Git 히스토리 오염 | 있음 | 없음 | 없음 |
| Cloudflare 토큰 필요 | 아니오 | 예 | 예 |
| 빌드 로그 확인 | GitHub + CF 둘 다 | CF 대시보드 | CF 대시보드 |
| 권장 여부 | 단순 테스트용 | ✅ 추천 | 고급 사용자용 |

**방법 A: 빈 커밋 푸시**는 가장 단순해요. GitHub Actions에서 `git commit --allow-empty`를 실행해 Git 이벤트를 만들고, Cloudflare Pages가 그 이벤트를 감지해서 빌드해요. 그런데 Git 로그가 지저분해지고, 팀 프로젝트엔 적합하지 않아요.

**방법 B: Cloudflare Pages API 직접 호출**은 가장 깔끔해요. Cloudflare에서 API 토큰을 발급받고, GitHub Actions에서 `curl`로 배포 훅(Deploy Hook)을 쏘는 방식이에요.

```yaml
# .github/workflows/scheduled-deploy.yml
name: Scheduled Deploy
on:
  schedule:
    - cron: '0 0 * * *'  # 매일 KST 09:00
  workflow_dispatch:       # 수동 실행도 가능하게

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Cloudflare Pages Deploy
        run: |
          curl -X POST "${{ secrets.CF_DEPLOY_HOOK_URL }}"
```

Cloudflare Pages 대시보드 → Settings → Builds & deployments → Deploy hooks에서 훅 URL을 만들 수 있어요. 이 URL을 GitHub Secrets에 `CF_DEPLOY_HOOK_URL`로 저장하면 끝이에요.

`workflow_dispatch`를 같이 넣으면 Actions 탭에서 수동으로도 실행할 수 있어서 테스트하기 편해요.

---

## 실제로 적용할 때 주의할 포인트

**시나리오 1: 처음 설정했는데 아무것도 안 돌아요**
워크플로우 파일이 기본 브랜치에 있는지 먼저 확인하세요. Actions 탭 → 해당 워크플로우 → "This workflow has a schedule trigger" 배지가 보여야 정상이에요. 안 보이면 브랜치 문제예요.

**시나리오 2: 한동안 잘 됐는데 갑자기 안 돼요**
60일 비활성화 정책 때문일 가능성이 높아요. Actions 탭에서 워크플로우 상태를 확인하고 비활성화됐으면 Enable 눌러주세요. 최근 커밋이 없었다면 빈 커밋 하나 날려서 레포를 깨워주세요.

**시나리오 3: cron은 실행됐는데 Cloudflare에 배포가 안 돼요**
Deploy Hook URL이 정확한지, 혹은 만료되지 않았는지 확인하세요. Cloudflare Pages 대시보드에서 훅을 재발급하고 GitHub Secrets도 업데이트해야 해요. 훅은 만료되지 않지만, 실수로 삭제하거나 프로젝트를 다시 만든 경우엔 URL이 바뀌어요.

---

## 정리하면 이렇게 돼요

cron 트리거가 안 될 때 원인은 거의 네 가지 중 하나예요. 브랜치 위치, 60일 비활성화, 시간대 착각, 또는 Cloudflare Pages 자체의 스케줄 기능 부재.

- `schedule` 이벤트는 기본 브랜치 워크플로우 파일에서만 동작
- 60일 무활동 시 자동 비활성화되니 주기적으로 확인
- cron 표현식은 항상 UTC 기준으로 작성
- Deploy Hook + `workflow_dispatch` 조합이 가장 안정적인 Hugo 블로그 Cloudflare Pages 자동배포 방법

참고로, Cloudflare Workers의 Cron Triggers 기능이 이미 있고 Pages와의 통합을 요청하는 피드백이 커뮤니티 포럼에 꾸준히 올라오고 있어요. 네이티브 스케줄 빌드 기능이 추가될 가능성은 있지만, 지금 당장은 Deploy Hook 방식이 가장 확실해요. 설정 한 번만 제대로 해두면 이후엔 신경 안 써도 되는 구조예요.

혹시 Deploy Hook 외에 더 깔끔한 방법을 찾으셨다면 댓글로 공유해 주세요.

## 참고자료

1. [Hugo · Cloudflare Pages docs](https://developers.cloudflare.com/pages/framework-guides/deploy-a-hugo-site/)
2. [How I Fixed My CI/CD: Fast, Optimized, and Pro-Level Deploys (Hugo + Cloudflare) - Oli Miah](https://oli.bdtechx.com/blog/how-i-fixed-my-ci-cd-fast-optimized-and-pro-level-deploys-hugo-cloudflare/)
3. [Scheduled Builds for Cloudflare Deployments with GitHub Actions | by BEN ABT | Medialesson | Medium](https://medium.com/medialesson/scheduled-builds-for-cloudflare-deployments-with-github-actions-93341a112432)


---

*Photo by [Conny Schneider](https://unsplash.com/@choys_) on [Unsplash](https://unsplash.com/photos/a-blue-background-with-lines-and-dots-xuTJZ7uD7PI)*
