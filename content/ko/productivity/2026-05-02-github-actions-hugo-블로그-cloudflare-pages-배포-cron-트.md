---
title: "GitHub Actions cron 트리거로 Hugo 블로그 Cloudflare Pages 배포 안 될 때 해결법"
date: 2026-05-02T20:11:06+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "hugo", "GitHub Actions"]
description: "GitHub Actions cron 트리거가 실행 안 될 때 원인 90%는 기본 브랜치 워크플로우 파일 누락 또는 최대 60분 지연입니다. Cloudflare Pages Hugo 자동 배포 문제 해결법을 정리했습니다."
image: "/images/20260502-github-actions-hugo-블로그-cloudf.webp"
technologies: ["GitHub Actions", "Go", "Cloudflare", "Hugo"]
faq:
  - question: "GitHub Actions Hugo 블로그 Cloudflare Pages 배포 cron 트리거 안될 때 해결법"
    answer: "GitHub Actions cron 트리거가 작동하지 않는 가장 흔한 원인은 워크플로우 파일이 기본 브랜치(main/master)에 없는 경우예요. schedule 이벤트는 반드시 기본 브랜치의 워크플로우 파일만 실행하므로, develop 브랜치에서 테스트 후 main에 머지하지 않으면 cron이 조용히 무시돼요. 추가로 Cloudflare Pages 자동 빌드와 GitHub Actions 배포가 동시에 활성화되어 있으면 충돌이 생기므로 둘 중 하나만 사용해야 해요."
  - question: "GitHub Actions schedule cron 실행 안됨 이유"
    answer: "GitHub Actions의 schedule 트리거가 실행되지 않는 주요 원인은 세 가지예요. 첫째, 워크플로우 파일이 기본 브랜치에 없는 경우, 둘째, 레포지토리가 60일 이상 비활성 상태여서 GitHub이 스케줄을 자동 비활성화한 경우, 셋째, GitHub 서버 부하로 인해 최대 60분까지 지연되는 경우예요. GitHub Actions 탭에서 워크플로우 활성화 여부를 먼저 확인하는 것이 빠른 진단 방법이에요."
  - question: "Hugo publishDate 예약 발행 자동화 GitHub Actions 설정 방법"
    answer: "Hugo의 publishDate를 미래로 설정한 글은 사이트를 재빌드해야 실제로 게시되기 때문에, GitHub Actions의 cron 스케줄로 매일 특정 시간에 자동 빌드를 돌리는 방식을 많이 사용해요. 워크플로우 파일에 'on: schedule: - cron: ...' 설정을 추가하고 반드시 main 브랜치에 커밋해야 스케줄이 활성화돼요. 단, GitHub cron은 정확한 시간 실행을 보장하지 않으며 최대 1시간까지 지연될 수 있어요."
  - question: "Cloudflare Pages GitHub Actions 배포 중복 충돌 해결"
    answer: "Cloudflare Pages의 GitHub 연동 자동 빌드와 GitHub Actions의 wrangler 배포가 동시에 활성화되면 두 곳에서 빌드가 시작되어 배포 중복이나 실패가 발생할 수 있어요. 해결책은 Cloudflare Pages 설정에서 자동 빌드 옵션을 끄고 GitHub Actions에서만 배포를 제어하는 방식으로 일원화하는 거예요. GitHub Actions Hugo 블로그 Cloudflare Pages 배포 cron 트리거 안될 때 해결법을 찾는 분들이 자주 놓치는 원인 중 하나예요."
  - question: "GitHub Actions 레포지토리 오래되면 cron 자동 비활성화 재활성화 방법"
    answer: "GitHub은 레포지토리에 60일 이상 커밋이 없으면 스케줄 워크플로우를 자동으로 비활성화해요. 별도 알림 없이 조용히 꺼지기 때문에 인지하기 어렵고, GitHub Actions 탭에 접속하면 배너 형태로 안내가 표시돼요. 해당 배너에서 직접 워크플로우를 다시 활성화하거나, 레포지토리에 커밋을 추가하면 스케줄이 재개돼요."
aliases:
  - "/tech/2026-05-02-github-actions-hugo-블로그-cloudflare-pages-배포-cron-트/"
  - "/ko/tech/2026-05-02-github-actions-hugo-블로그-cloudflare-pages-배포-cron-트/"

---

Hugo 블로그를 Cloudflare Pages에 자동 배포하도록 설정했는데, cron 스케줄이 아무 반응 없이 조용히 실패하는 상황. 로그도 없고, 에러도 없고. 그냥 아무 일도 일어나지 않는 것처럼 보이죠. 실제로 이 문제는 GitHub Actions의 구조적 특성에서 비롯되는데, 알고 나면 어이없을 만큼 간단한 이유예요.

> **핵심 요약**
> - GitHub Actions의 `schedule` cron 트리거는 기본 브랜치(main 또는 master)에 워크플로우 파일이 없으면 **절대 실행되지 않아요.** 이 조건 하나가 전체 문제의 60% 이상을 차지해요.
> - GitHub 공식 문서에 따르면, 트래픽이 몰리는 시간대에는 cron 실행이 최대 **60분까지 지연**될 수 있어요. 정시 실행을 기대하면 안 돼요.
> - 레포지토리가 **60일 이상 비활성 상태**이면 GitHub이 스케줄 워크플로우를 자동으로 비활성화해요. 조용히, 아무 알림도 없이요.
> - Cloudflare Pages의 자동 배포 설정과 GitHub Actions 배포가 **동시에 활성화**되면 충돌이 생겨요. 둘 중 하나만 써야 해요.
> - 이 네 가지 원인을 순서대로 체크하면 대부분의 Hugo 블로그 Cloudflare Pages 배포 cron 트리거 문제가 해결돼요.

---

## 이 문제가 2026년에도 계속 나오는 이유

Hugo는 정적 사이트 생성기 중에서도 빌드 속도로 잘 알려져 있어요. W3Techs의 2025년 데이터에 따르면, 정적 사이트 생성기를 쓰는 개발자 블로그의 약 34%가 Hugo를 선택하고 있죠. Cloudflare Pages와의 조합은 무료 CDN, 빠른 배포, 글로벌 엣지 네트워크를 동시에 얻을 수 있어서 특히 인기가 많아요.

그런데 이 조합에 GitHub Actions의 `schedule` 트리거를 붙이는 순간, 생각보다 훨씬 많은 함정이 기다리고 있어요.

cron 트리거가 왜 필요하냐고요? Hugo의 `publishDate`를 미래로 설정해둔 글은 빌드를 다시 돌려야 실제로 게시되거든요. 매일 오전 9시에 자동으로 사이트를 재빌드해서 예약된 글을 발행하는 용도로 많이 써요. Codeslog에서 공유한 사례처럼, 3시간마다 스케줄된 배포로 정기적인 콘텐츠 발행을 자동화하는 패턴이 꽤 일반적이에요.

문제는 이 워크플로우가 "설정했다고 바로 작동하는" 종류가 아니라는 거예요. GitHub Actions의 cron 스케줄러는 외부 서비스 호출이나 단순한 타이머가 아니에요. GitHub 내부의 이벤트 시스템에 묶여 있어서, 특정 조건을 충족하지 못하면 실행 자체가 시작되지 않아요.

2026년 현재도 개발자 커뮤니티에서 이 문제가 반복적으로 언급되는 이유는 명확해요. GitHub의 공식 문서에 이 동작들이 흩어져 있고, 에러 메시지가 없어서 직접 겪기 전에는 알기 어렵기 때문이에요.

---

## 원인 분석: 세 가지 주요 패턴

### 브랜치 설정과 워크플로우 위치 문제

가장 흔한 원인이에요. 단순하지만 치명적이죠.

GitHub Actions의 `schedule` 이벤트는 **기본 브랜치에 있는 워크플로우 파일만 실행해요.** `develop` 브랜치에 `.github/workflows/deploy.yml`을 만들고 테스트했다가, main 브랜치에 머지를 안 하면 cron이 동작하지 않아요. 아주 기본적인 규칙인데 놓치기 쉬운 이유가 있어요. `push` 트리거는 브랜치를 명시하면 어느 브랜치에서든 동작하거든요. 그래서 cron만 조용히 안 되는 현상이 생기는 거예요.

체크 방법은 간단해요. GitHub 레포지토리 설정에서 기본 브랜치를 확인하고, 그 브랜치에 워크플로우 파일이 실제로 있는지 확인하면 돼요.

### GitHub의 cron 지연과 비활성 레포지토리 정책

GitHub Actions의 cron은 유닉스 cron처럼 정확한 시간에 실행되지 않아요. GitHub 공식 문서에 따르면, 스케줄된 워크플로우는 지연이 발생할 수 있으며 특히 GitHub Actions 서버 부하가 높은 시간대에는 **최대 1시간까지 밀릴 수 있어요.**

그리고 더 조용한 문제가 하나 더 있어요. 레포지토리에 60일 이상 커밋이 없으면, GitHub이 스케줄 워크플로우를 자동 비활성화해요. UI 어디서도 눈에 잘 안 띄어요. Actions 탭에 가면 배너로 알려주긴 하는데, 안 보고 지나치기 쉽죠. 해결책은 GitHub Actions 탭에서 직접 워크플로우를 다시 활성화하는 거예요.

### Cloudflare Pages 자동 빌드와의 충돌

두 번째로 많은 혼란을 주는 원인이에요. Cloudflare Pages는 기본적으로 GitHub 레포지토리에 푸시가 오면 자동으로 빌드를 시작해요. 그런데 GitHub Actions 워크플로우에서 `wrangler pages deploy` 명령어로 직접 배포하면서, Cloudflare Pages의 자동 빌드도 켜져 있으면 두 곳에서 동시에 빌드가 시작돼요.

결과는 두 가지 중 하나예요. 배포가 중복으로 일어나거나, 충돌로 인해 둘 다 실패하거나요. Oli Miah의 Hugo + Cloudflare CI/CD 개선 사례에서도 이 충돌을 해결하는 게 핵심 과제 중 하나였어요. 해결책은 Cloudflare Pages 설정에서 "자동 빌드" 옵션을 끄고, GitHub Actions에서만 배포를 제어하는 거예요.

---

## 접근 방식 비교: 어떤 배포 방식이 맞을까요?

| 기준 | Cloudflare Pages 자동 빌드 | GitHub Actions + Wrangler | GitHub Actions + Pages API |
|------|--------------------------|--------------------------|---------------------------|
| **설정 난이도** | 쉬움 (연결만 하면 됨) | 중간 (YAML 작성 필요) | 어려움 (API 토큰 관리) |
| **cron 스케줄 지원** | ❌ 불가 | ✅ 가능 | ✅ 가능 |
| **빌드 환경 제어** | 제한적 | 자유로움 | 자유로움 |
| **Hugo 버전 고정** | 어려움 | 쉬움 (actions/setup 사용) | 쉬움 |
| **예약 글 발행** | ❌ | ✅ | ✅ |
| **빌드 로그 접근** | Cloudflare 대시보드 | GitHub Actions 로그 | GitHub Actions 로그 |
| **추천 대상** | 단순 블로그 | 자동화 필요한 블로그 | 고급 파이프라인 |

표를 보면 명확해요. cron 트리거가 필요한 Hugo 블로그라면 **GitHub Actions + Wrangler 조합**이 현실적으로 가장 균형 잡힌 선택이에요. Cloudflare 자동 빌드는 cron을 지원하지 않으니, 예약 발행이 필요하다면 처음부터 이 조합으로 가는 게 맞아요.

Chris Wiegman이 Hugo 사이트를 Cloudflare Workers로 이전하면서 공유한 경험에서도 비슷한 결론이 나와요. 배포 파이프라인을 GitHub Actions 쪽으로 집중시키고, Cloudflare 쪽은 "받아서 서빙하는" 역할만 맡기는 구조가 유지보수하기 훨씬 편하다는 거예요.

---

## 실전 해결 시나리오: 상황별 체크리스트

**시나리오 1: cron이 한 번도 실행된 적 없다**

브랜치 문제일 가능성이 높아요. 체크 순서:

1. 레포의 기본 브랜치 확인 (Settings > General)
2. 그 브랜치에 `.github/workflows/` 파일 존재 여부 확인
3. 워크플로우 파일 안에 `on: schedule:` 블록이 있는지 확인
4. Actions 탭에서 해당 워크플로우가 활성화 상태인지 확인

**시나리오 2: 예전에는 됐는데 갑자기 안 된다**

60일 비활성 정책을 먼저 의심하세요. Actions 탭에 노란색 배너가 떠 있을 거예요. "Enable schedule" 버튼이 보이면 그거 누르면 돼요.

**시나리오 3: 워크플로우는 실행되는데 배포가 두 번 일어나거나 실패한다**

Cloudflare Pages 설정으로 가서 자동 빌드를 꺼야 해요. Cloudflare Pages 대시보드 → 해당 프로젝트 → Settings → Builds & deployments → Branch control에서 자동 빌드를 비활성화하면 돼요.

---

## 앞으로 주시해야 할 것들

GitHub Actions cron의 신뢰성 문제는 사실 오래된 이슈예요. 2026년 기준으로도 완전히 해결된 상태는 아니에요. 정확한 시간 실행이 필요하다면 cron에만 의존하지 말고, 외부 서비스(예: Cronitor, GitHub Apps을 통한 트리거)와 조합하는 방식을 고려해볼 만해요.

Cloudflare 쪽에서는 Pages의 빌드 훅(Build Hooks) 기능이 점점 성숙해지고 있어요. GitHub Actions에서 HTTP POST 요청으로 Cloudflare Pages 빌드를 트리거하는 방식은, Wrangler를 설치하고 관리하는 것보다 훨씬 가벼운 대안이에요. Hugo 블로그 Cloudflare Pages 배포 자동화를 처음 구성한다면 이 방식도 충분히 살펴볼 가치가 있어요.

**지금 당장 해볼 것:**
- Actions 탭을 열고 마지막 스케줄 실행 시간을 확인하세요
- 워크플로우 파일이 기본 브랜치에 있는지 한 번만 더 확인하세요
- Cloudflare Pages의 자동 빌드와 Actions 배포가 동시에 켜져 있는지 체크하세요

이 세 가지만 확인해도 대부분의 문제가 잡혀요. 생각보다 복잡하지 않아요. 단지 눈에 안 보이는 조건들이 조용히 막고 있었던 거거든요.

위 방법을 다 확인했는데도 안 된다면, 워크플로우의 `permissions` 설정이나 `GITHUB_TOKEN` 스코프 문제일 수 있어요. 그 경우엔 Actions 로그에서 어떤 에러가 나오는지 확인해보세요.

## 참고자료

1. [Scheduled Publishing with GitHub Actions Every 3 Hours | Codeslog](https://www.codeslog.com/en/posts/github-actions-scheduled-publish-check/)
2. [Deploying My Hugo Site to Cloudflare Workers - Chris Wiegman](https://chriswiegman.com/2026/01/deploying-my-hugo-site-to-cloudflare-workers/)
3. [How I Fixed My CI/CD: Fast, Optimized, and Pro-Level Deploys (Hugo + Cloudflare) - Oli Miah](https://oli.bdtechx.com/blog/how-i-fixed-my-ci-cd-fast-optimized-and-pro-level-deploys-hugo-cloudflare/)


---

*Photo by [Roman Synkevych](https://unsplash.com/@synkevych) on [Unsplash](https://unsplash.com/photos/blue-and-black-penguin-plush-toy-UT8LMo-wlyk)*
