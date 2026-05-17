---
title: "GitHub Actions cron 스케줄이 안 될 때 원인과 Hugo 블로그 Cloudflare Pages 자동 배포 연결 방법"
date: 2026-05-17T20:28:53+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "github", "actions", "cron", "GitHub Actions"]
description: "GitHub Actions cron 스케줄이 60일 비활성 시 자동 비활성화되는 문제, UTC 기준 한국 오전 9시는 `0 0 * * *` 설정, shared runner 수십 분 지연까지 Hugo·Cloudflare Pages 자동 배포 실패 원인을 분석합니다"
image: "/images/20260517-github-actions-cron-스케줄-실제로-안-.webp"
technologies: ["GitHub Actions", "Go", "Cloudflare", "Hugo"]
faq:
  - question: "GitHub Actions cron 스케줄 갑자기 안 되는 이유"
    answer: "GitHub Actions cron 스케줄이 실제로 안 될 때 가장 흔한 원인은 저장소 비활성화입니다. GitHub는 60일 동안 커밋이나 이벤트가 없으면 cron 스케줄을 자동으로 꺼버리며, 이는 공식 GitHub 문서에 명시된 정책입니다. GitHub 저장소 Actions 탭에서 해당 Workflow를 열면 'This scheduled workflow is disabled' 메시지로 확인할 수 있습니다."
  - question: "GitHub Actions cron UTC 한국시간 변환 설정 방법"
    answer: "GitHub Actions cron 스케줄은 UTC 기준으로만 동작하기 때문에 한국 시간(KST, UTC+9)을 고려해 설정해야 합니다. 한국 기준 오전 9시에 실행하려면 cron을 '0 0 * * *'로 작성해야 하며, '0 9 * * *'로 쓰면 실제로는 한국 기준 오후 6시에 실행됩니다."
  - question: "Hugo 블로그 자동 배포 Cloudflare Pages cron 실행돼도 배포 안 되는 이유"
    answer: "GitHub Actions cron 스케줄 실제로 안 될 때와 혼동하기 쉽지만, Hugo 블로그 자동 배포 Cloudflare Pages 환경에서는 cron이 정상 실행돼도 배포가 안 되는 별도 문제가 있습니다. Cloudflare Pages의 기본 배포 트리거는 GitHub 저장소에 push가 발생할 때이므로, cron Workflow가 실행되더라도 실제 파일 변경이 없으면 Cloudflare Pages는 아무 동작도 하지 않습니다. 이 문제는 Cloudflare Deploy Hook URL을 Workflow에서 직접 호출하거나 빈 커밋을 push하는 방식으로 해결할 수 있습니다."
  - question: "Cloudflare Pages Hugo 빌드 오류 메시지 없이 빈 페이지 나오는 경우"
    answer: "Cloudflare Pages의 기본 Hugo 버전은 2026년 기준 0.54.0으로, 로컬에서 최신 Hugo 버전으로 구성한 테마나 shortcode와 버전이 맞지 않으면 에러 메시지 없이 빈 페이지가 렌더링됩니다. Cloudflare Pages 대시보드의 Settings → Environment Variables에서 'HUGO_VERSION' 환경 변수를 로컬과 동일한 버전으로 명시하면 해결됩니다."
  - question: "GitHub Actions cron 무료 플랜 실행 시간 지연 얼마나 되나요"
    answer: "GitHub Actions cron 스케줄 실제로 안 될 때처럼 보이지만, 무료 플랜의 shared runner 큐 지연으로 실행이 늦어지는 경우도 많습니다. 트래픽이 몰리는 시간대에는 실제 실행 시각이 20~40분까지 늦어질 수 있으며, GitHub 공식 문서에도 cron은 'best-effort basis(최선 노력 방식)'로 실행된다고 명시되어 있어 정확한 타이밍이 필요한 작업에는 cron만 단독으로 사용하는 것을 권장하지 않습니다."
---

오전 9시가 지났는데 Cloudflare Pages는 조용해요. 로그를 뒤져봐도 실패 메시지조차 없고요. GitHub Actions cron 스케줄이 실제로 안 될 때, 단순한 문법 오류가 아닌 경우가 꽤 많아요.

> **핵심 요약**
> - GitHub Actions cron 스케줄은 저장소가 60일 이상 비활성 상태면 자동으로 비활성화돼요. 공식 GitHub 문서(2026년 기준)에 명시된 사항이에요.
> - UTC 기준으로 동작하기 때문에 한국 기준 오전 9시는 `0 0 * * *`로 설정해야 맞아요.
> - GitHub 무료 플랜 기준 shared runner 큐 지연은 최대 수십 분까지 발생할 수 있고, 이 지연은 트리거 조건을 변경해도 해결되지 않아요.
> - Hugo + Cloudflare Pages 조합은 환경 변수 `HUGO_VERSION`을 명시하지 않으면 빌드가 조용히 실패할 수 있어요.

---

## cron이 갑자기 멈추는 이유

Hugo 블로그를 Cloudflare Pages에 자동 배포하는 파이프라인은 구조 자체는 단순해요. GitHub 저장소에 Workflow 파일을 만들고, `schedule` 트리거로 cron을 걸고, Cloudflare Pages가 변경사항을 감지해 빌드하는 흐름이죠.

그런데 처음 며칠은 잘 되다가 어느 순간부터 아무것도 실행이 안 되는 상황을 마주하게 돼요.

**가장 흔한 원인은 저장소 비활성화예요.** GitHub는 60일 동안 커밋이나 이벤트가 없으면 cron 스케줄을 자동으로 꺼버려요. 개인 블로그 저장소가 특히 이 케이스에 해당할 가능성이 높아요. 포스팅을 한동안 못 하면 저장소에 커밋이 없고, 그러면 스케줄도 멈추는 거죠.

두 번째는 **타임존 문제**예요. GitHub Actions는 UTC 기준으로만 동작해요. 한국 시간(KST)은 UTC+9이기 때문에, 한국 기준 오전 9시에 실행하고 싶다면 cron을 `0 0 * * *`로 써야 해요. `0 9 * * *`로 설정하면 한국 기준 오후 6시에 실행되죠.

세 번째는 **runner 큐 지연**이에요. 무료 플랜에서는 shared runner를 써요. 트래픽이 몰리는 시간대에는 실제 실행 시각이 20~40분 늦어지는 경우가 있어요. GitHub 공식 문서에도 "cron은 최선 노력 방식(best-effort basis)으로 실행된다"고 명시되어 있어요. 정확한 타이밍이 필요하다면 cron만 믿으면 안 된다는 뜻이에요.

---

## Hugo + Cloudflare Pages에서만 나타나는 문제들

cron 자체는 정상 작동하는데 빌드가 실패하는 경우도 있어요. Hugo와 Cloudflare Pages 조합 특유의 이슈예요.

### Hugo 버전 불일치

Cloudflare Pages는 빌드 시 Hugo 버전을 기본값으로 실행해요. 2026년 기준 기본 Hugo 버전은 `0.54.0`이에요. 그런데 로컬에서 최신 Hugo(`0.125.x` 이상)로 테마나 shortcode를 구성했다면, Cloudflare에서 빌드할 때 에러 메시지 없이 빈 페이지가 나와요.

해결책은 환경 변수 설정이에요. Cloudflare Pages 대시보드 → Settings → Environment Variables에서 `HUGO_VERSION`을 로컬과 동일한 버전으로 명시하면 돼요.

### `push` 이벤트가 없으면 Cloudflare가 트리거되지 않아요

Cloudflare Pages의 기본 배포 트리거는 **GitHub 저장소에 push가 발생할 때**예요. GitHub Actions cron은 Cloudflare에 push를 일으키지 않아요. cron으로 Workflow가 실행되더라도, 실제 파일 변경이 없으면 Cloudflare Pages는 아무것도 안 해요.

"분명히 Actions가 돌았는데 왜 배포가 안 되지?" 이 상황이 여기서 나와요.

실제로 배포까지 연결하려면 세 가지 방법이 있어요.

| 방법 | 설명 | 주의사항 |
|------|------|----------|
| Cloudflare API 직접 호출 | Workflow에서 `curl`로 Cloudflare Deploy Hook URL을 호출 | Hook URL이 노출되지 않도록 GitHub Secrets 사용 필수 |
| 빈 커밋 push | `git commit --allow-empty -m "chore: trigger build"` | 커밋 히스토리가 지저분해질 수 있음 |
| Wrangler CLI | `wrangler pages deploy` 명령어로 배포 | Cloudflare API Token 권한 설정 필요 |

셋 다 쓸 수 있는 방법이에요. 그런데 실제로 가장 안정적인 건 **Cloudflare Deploy Hook**을 Workflow에서 직접 호출하는 방식이에요. push 이벤트에 의존하지 않고, Actions가 성공했을 때만 배포를 트리거하니까 제어가 명확해요.

### `on.schedule`과 `on.push`를 함께 쓸 때 생기는 함정

Workflow 파일 상단을 이렇게 쓰는 경우가 많아요.

```yaml
on:
  push:
    branches:
      - main
  schedule:
    - cron: '0 0 * * *'
```

cron으로 실행되면 `github.event_name`이 `schedule`이 되는데, 이후 step에서 `push` 이벤트에서만 세팅되는 환경 변수나 context를 쓰면 Workflow가 조용히 중단돼요. Hugo 테마를 submodule로 관리하는 경우, `actions/checkout`의 `submodules: true` 옵션을 빠뜨리면 테마 파일 없이 빌드가 시도되기도 해요.

---

## 실제로 어떻게 잡아야 할까요

**문제 1: 스케줄이 아예 실행되지 않아요**

저장소 비활성화가 원인일 가능성이 높아요. GitHub 저장소 → Actions 탭 → 해당 Workflow 상단에서 "This scheduled workflow is disabled" 메시지를 확인하세요. 비활성화됐다면 "Enable workflow" 버튼이 있어요. 한 번 활성화하면 다음 실행부터 정상 동작해요.

**문제 2: Actions는 돌았는데 Cloudflare Pages가 업데이트 안 돼요**

Workflow 로그에서 deploy step이 있는지 확인해요. `echo "Hugo build done"` 같은 메시지만 있고 Cloudflare API 호출이 없다면, 빌드만 하고 배포 트리거가 없는 거예요. Cloudflare Deploy Hook을 GitHub Secrets(`CF_DEPLOY_HOOK_URL`)에 저장하고, Workflow 마지막에 `curl -X POST ${{ secrets.CF_DEPLOY_HOOK_URL }}`을 추가하세요.

**문제 3: 배포됐는데 Hugo 빌드 결과물이 이상해요**

`HUGO_VERSION` 환경 변수를 Cloudflare Pages에 명시하지 않았을 가능성이 커요. 로컬에서 `hugo version`으로 확인한 버전을 Cloudflare Pages 환경 변수에 그대로 입력하면 돼요.

---

## 자동 배포가 "자동"이 되려면

- GitHub Actions cron은 저장소가 비활성화되면 자동으로 멈추고, UTC 기준으로 동작해요.
- Cloudflare Pages는 push 이벤트 기반이기 때문에 cron만으로는 배포가 안 돼요. Deploy Hook 연결이 필수예요.
- Hugo 버전 불일치는 빌드 실패의 조용한 원인이에요. `HUGO_VERSION` 명시로 예방할 수 있어요.
- Cloudflare의 2026년 로드맵에는 Pages 배포 트리거 확장이 포함되어 있어요. 앞으로 외부 webhook 트리거 기능이 더 강화될 가능성이 높아요.

가장 먼저 볼 건 Actions 탭의 "disabled" 메시지예요. 자동화 파이프라인이 실제로 자동으로 돌고 있는지, 지금 바로 확인해볼 만해요.

## 참고자료

1. [Hugo · Cloudflare Pages docs](https://developers.cloudflare.com/pages/framework-guides/deploy-a-hugo-site/)
2. [Automatic publishing of my Hugo website using Github and Cloudflare Pages - Virtual to the Core](https://www.virtualtothecore.com/hugo-github-cloudflare-pages/)
3. [Deploy Hugo + Tailwind v4 to Cloudflare: Super Fast GitHub Workflow | Oli Miah](https://oli.bdtechx.com/blog/deploy-hugo-to-cloudflare-github-workflow/)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-white-dice-with-a-black-github-logo-on-it-HLQDfaJUTVI)*
