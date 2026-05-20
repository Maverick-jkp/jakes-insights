---
title: "GitHub Actions cron 실행 안 될 때: Hugo 블로그 Cloudflare Pages 자동 배포 해결법"
date: 2026-05-20T21:36:23+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "github", "actions", "hugo", "GitHub Actions"]
description: "GitHub Actions cron이 60일 비활성 후 자동 비활성화되는 정책, Hugo 블로그 Cloudflare Pages 자동 배포가 갑자기 멈추는 원인과 워크플로우 재활성화 방법을 정리했습니다."
image: "/images/20260520-github-actions-hugo-블로그-cloudf.webp"
technologies: ["GitHub Actions", "Go", "Cloudflare", "Hugo"]
faq:
  - question: "GitHub Actions cron 스케줄 설정했는데 워크플로우가 자동으로 안 실행돼요"
    answer: "리포지토리에 커밋이나 PR 같은 활동이 60일 이상 없으면 GitHub이 schedule 기반 워크플로우를 자동으로 비활성화합니다. Actions 탭에서 해당 워크플로우를 찾아 'Enable workflow' 버튼을 클릭하면 즉시 복구되며, workflow_dispatch 트리거를 함께 설정해두면 수동으로도 빠르게 재실행할 수 있습니다."
  - question: "GitHub Actions Hugo 블로그 Cloudflare Pages 자동 배포 cron 실행 안 될 때 해결법이 뭔가요"
    answer: "GitHub Actions Hugo 블로그 Cloudflare Pages 자동 배포 cron 실행 안 될 때 해결법은 크게 세 가지를 확인하는 것입니다. 리포지토리 60일 비활성화로 워크플로우가 꺼졌는지, cron 표현식이 UTC 기준으로 올바르게 작성됐는지, Hugo의 publishDate가 빌드 시점보다 미래로 설정되어 포스트가 렌더링에서 제외된 건 아닌지 순서대로 점검하세요. workflow_dispatch 트리거와 Cloudflare Pages Deploy Hook을 함께 구성하면 더 안정적인 파이프라인을 만들 수 있습니다."
  - question: "Hugo publishDate 설정했는데 예약 포스팅이 배포 후에도 안 보여요"
    answer: "Hugo는 빌드 실행 시각보다 publishDate가 미래인 포스트를 기본적으로 렌더링하지 않습니다. 빌드 명령에 --buildFuture 플래그를 추가하거나, publishDate를 UTC 기준으로 작성하고 워크플로우에 TZ='Asia/Seoul' hugo --minify처럼 타임존을 명시해서 빌드 시점과 게시 시점이 일치하도록 맞춰야 합니다."
  - question: "GitHub Actions cron UTC 시간 한국 시간으로 변환하는 방법"
    answer: "GitHub Actions의 cron 트리거는 UTC 기준으로 동작하므로 한국 시간(KST)에서 9시간을 빼서 입력해야 합니다. 예를 들어 KST 오전 9시에 실행하려면 cron 표현식을 '0 0 * * *'으로 설정하면 되고, 워크플로우 내 빌드 명령에도 TZ='Asia/Seoul'을 명시해 Hugo가 올바른 시간대로 포스트를 판단하도록 해주는 것이 좋습니다."
  - question: "GitHub Actions Hugo 블로그 Cloudflare Pages 자동 배포 cron 실행 안 될 때 Cloudflare Deploy Hook 연동 방법"
    answer: "Cloudflare Pages 대시보드에서 Settings → Builds & Deployments → Deploy Hooks 메뉴로 이동해 Hook URL을 생성한 뒤, 해당 URL을 GitHub Secrets에 CF_DEPLOY_HOOK으로 저장합니다. GitHub Actions 워크플로우에서 curl -X POST '${{ secrets.CF_DEPLOY_HOOK }}' 명령을 실행하면 새 커밋 없이도 Cloudflare Pages 빌드를 직접 트리거할 수 있어 cron 기반 자동 배포를 더 안정적으로 운영할 수 있습니다."
---

어젯밤 예약해둔 포스팅이 오늘 아침에도 올라와 있지 않아요. GitHub Actions 워크플로우 탭을 열면 마지막 실행 기록이 며칠 전 그대로. cron 스케줄은 맞게 써놨는데, 아무 일도 안 일어났죠. Hugo 블로그를 GitHub Actions로 자동 배포하고 Cloudflare Pages와 연결해둔 분들이라면 한 번쯤 겪는 상황이에요.

> **핵심 요약**
> - GitHub Actions의 `schedule` 트리거는 리포지토리 비활성 기간이 60일을 넘으면 자동으로 꺼진다. 2026년 현재도 동일하게 적용되는 공식 정책이다.
> - cron 표현식이 정확해도 GitHub 서버 부하에 따라 최대 수십 분 지연될 수 있어, 정시 실행을 가정한 포스팅 스케줄은 실제로 어긋날 수 있다.
> - `workflow_dispatch`를 병행 설정하면 수동 트리거로 빠르게 복구할 수 있고, Cloudflare Pages 빌드 훅과 조합하면 더 안정적인 파이프라인을 만들 수 있다.
> - Hugo의 `publishDate` 필드 단독 설정만으로는 자동 배포가 되지 않는다. 배포 시점을 코드가 실행되는 시점과 따로 관리해야 한다.

---

## GitHub Actions cron, 왜 갑자기 멈추는 걸까요?

가장 많이 보이는 원인부터 짚을게요.

**GitHub의 비활성 리포지토리 정책**이에요. GitHub 공식 문서에 따르면, 리포지토리에 커밋이나 Pull Request 같은 활동이 60일 이상 없으면 `schedule` 기반 워크플로우가 자동으로 비활성화돼요. 조용히 꺼지는 거예요. 알림도 없고요. 개인 기술 블로그처럼 작성 주기가 긴 경우에 딱 걸리는 패턴이죠.

두 번째는 **cron 표현식 오류**예요. GitHub Actions는 UTC 기준으로 실행되는데, 한국 시간(KST = UTC+9)을 그냥 쓰면 9시간 어긋나요. 오전 9시에 올리고 싶어서 `0 9 * * *`라고 썼다면, 실제로는 오후 6시(KST)에 실행되는 셈이에요.

세 번째는 **GitHub Actions 서버 자체의 지연**이에요. GitHub은 공식적으로 `schedule` 트리거가 "정확한 시간을 보장하지 않는다"고 명시해 놨어요. 서버 부하가 높은 시간대에는 수십 분씩 늦어지는 경우도 드물지 않아요.

Hugo 블로그를 GitHub Actions로 빌드하고 Cloudflare Pages에 자동 배포하는 구조는 각 단계가 잘 연결되면 꽤 깔끔한 파이프라인이에요. 문제는 이 구조에서 cron이 실행 안 될 때 침묵한다는 점이에요. 에러 로그도, 알림도 없이 그냥 아무 일도 안 일어나요.

---

## 원인별 진단과 해결법

### 비활성화된 워크플로우 복구하기

GitHub 리포지토리에서 **Actions → 해당 워크플로우 → "Enable workflow"** 버튼을 찾아 클릭하면 바로 살아나요. 그런데 60일이 지나면 다시 꺼져요.

근본적인 해결책은 두 가지예요.

첫째, **워크플로우 안에 더미 커밋을 자동 생성하는 로직**을 심는 방법이에요. 빌드 스텝 중에 `git commit --allow-empty`로 빈 커밋을 하나 만들면, 리포지토리 활동이 유지되어 비활성화를 막을 수 있어요.

둘째, **`workflow_dispatch` 트리거를 함께 달아두는 것**이에요. Actions 탭에서 수동으로 실행할 수 있고, 비활성화 이후에도 버튼 한 번으로 즉시 복구 및 재실행이 가능해요.

```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # UTC 기준 매일 자정 (KST 오전 9시)
  workflow_dispatch:       # 수동 트리거 병행
```

### cron 표현식과 Hugo publishDate 불일치 문제

Hugo의 `publishDate`는 빌드 시점 기준으로 작동해요. 빌드가 실행되는 시각보다 `publishDate`가 미래면 해당 포스트는 렌더링되지 않아요. `--buildFuture` 플래그를 명시적으로 넣지 않는 한요.

이 구조에서 cron이 정상 실행돼도 빌드 결과물에 포스팅이 없으니 배포가 "됐지만 안 된 것처럼" 보이거든요. 실제로 가장 찾기 어려운 함정이에요.

해결 방법은 간단해요. 워크플로우 YAML에서 Hugo 빌드 명령에 타임존을 명시하고, 게시 예정 글은 `publishDate`를 UTC 기준으로 작성하는 거예요.

```yaml
- name: Build Hugo
  run: TZ="Asia/Seoul" hugo --minify
```

### Cloudflare Pages 빌드 훅 연동

Cloudflare Pages는 GitHub 리포지토리와 연결하면 푸시 이벤트에 반응해서 자동 빌드를 해줘요. 그런데 GitHub Actions cron으로 새 커밋 없이 배포만 트리거하고 싶을 때는 **Cloudflare Pages의 Deploy Hook URL**을 써야 해요.

Cloudflare Pages 대시보드 → Settings → Builds & Deployments → Deploy Hooks에서 URL을 생성한 다음, GitHub Actions 워크플로우에서 `curl`로 POST 요청을 날리면 끝이에요.

```yaml
- name: Trigger Cloudflare Pages Deploy
  run: curl -X POST "${{ secrets.CF_DEPLOY_HOOK }}"
```

Deploy Hook URL은 GitHub Secrets에 `CF_DEPLOY_HOOK`으로 저장해두면 노출 걱정 없이 쓸 수 있어요.

### 접근 방식 비교

| 항목 | cron 단독 | cron + workflow_dispatch | Cloudflare Deploy Hook |
|------|-----------|--------------------------|------------------------|
| 자동화 수준 | 높음 | 높음 | 높음 |
| 복구 편의성 | 낮음 | 높음 | 중간 |
| UTC 시간 관리 필요 | 필수 | 필수 | 불필요 |
| 비활성 리포지토리 위험 | 있음 | 있음 (수동 보완) | 없음 |
| Hugo publishDate 연동 | 주의 필요 | 주의 필요 | 빌드 시점 독립 |
| 설정 복잡도 | 낮음 | 낮음 | 중간 |

대부분의 개인 Hugo 블로그에는 **cron + workflow_dispatch 조합**이 현실적이에요. Deploy Hook은 Cloudflare Pages 설정까지 손봐야 하니 처음 구축하는 분들한테는 살짝 부담스러울 수 있거든요.

---

## 실전 체크리스트: 문제 발생 시 순서대로

**시나리오 1 — 워크플로우가 며칠째 실행 안 됐을 때**
Actions 탭에서 워크플로우 상태를 확인하고 "disabled" 상태면 Enable 버튼 클릭 → 이후 `workflow_dispatch`를 추가해서 같은 상황 재발을 막아요.

**시나리오 2 — 워크플로우는 실행됐는데 포스팅이 안 보일 때**
빌드 로그에서 Hugo가 몇 개 페이지를 생성했는지 확인해요. "0 pages" 혹은 예상보다 적으면 `publishDate` 문제일 가능성이 높아요. `TZ` 환경변수와 YAML 프런트매터의 날짜를 UTC 기준으로 맞춰보세요.

**시나리오 3 — cron 타이밍이 계속 어긋날 때**
GitHub Actions 자체 지연은 피할 수 없어요. 대신 Cloudflare Pages Deploy Hook과 외부 cron 서비스(예: cron-job.org)를 조합하면 GitHub 서버 부하에서 독립적으로 실행 시간을 조정할 수 있어요.

---

## 지금 당장 할 수 있는 것들

그냥 아무것도 안 되는 상태가 제일 답답하죠. 에러가 나면 오히려 고치기 쉬운데, 침묵하는 실패는 원인 파악부터가 막막해요.

핵심만 다시 짚으면:
- **60일 비활성 정책**을 모르면 당할 수밖에 없어요. `workflow_dispatch` 추가가 최선의 보험이에요.
- **UTC vs KST** 혼동은 cron 실행 자체보다 더 자주 문제를 만들어요.
- **Hugo publishDate와 빌드 시점**은 별개예요. 빌드 커맨드에 `TZ` 설정을 붙이는 것부터 시작하세요.
- **Cloudflare Pages Deploy Hook**은 한 번 설정해두면 GitHub Actions 의존도를 크게 낮출 수 있어요.

지금 쓰고 있는 워크플로우 YAML에 `workflow_dispatch` 트리거가 없다면, 지금 바로 추가해두는 게 좋아요. 두 줄이면 끝나고, 다음번에 cron이 멈췄을 때 10분 만에 복구할 수 있게 해주거든요.

자동 배포 파이프라인이 "알아서 잘 돌아가고 있다"고 믿는 순간, 가장 중요한 포스팅이 날아가더라고요. 지금 한 번 확인해보는 건 어떨까요?

## 참고자료

1. [サボりのAlice、そして意図せず増殖した記事、制御不能の自動投稿！GitHub Actionsのcronが動かなかった話｜えいりす](https://note.com/alice_ai_blog/n/nd200e3274b1a)
2. [Hugo를 사용하여 블로그를 구축하고 Cloudflare Pages에 배포하기 | Heyjude's Blog](https://www.heyjude.blog/ko/posts/deploy-hugo-to-cloudflare/)
3. [Cloudflare Pages와 GitHub을 활용한 무료 웹 서비스 배포 가이드](https://easy-scraping.com/entry/Cloudflare-Pages%EC%99%80-GitHub%EC%9D%84-%ED%99%9C%EC%9A%A9%ED%95%9C-%EB%AC%B4%EB%A3%8C-%EC%9B%B9-%EC%84%9C%EB%B9%84%EC%8A%A4-%EB%B0%B0%ED%8F%AC-%EA%B0%80%EC%9D%B4%EB%93%9C)


---

*Photo by [Ferenc Almasi](https://unsplash.com/@flowforfrank) on [Unsplash](https://unsplash.com/photos/a-computer-screen-with-a-bunch-of-buttons-on-it--FHIdRVGets)*
