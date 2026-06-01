---
title: "GitHub Actions cron 스케줄로 Hugo 블로그 Cloudflare Pages 자동배포 안 될 때 해결법"
date: 2026-04-02T20:10:36+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "hugo", "GitHub Actions"]
description: "GitHub Actions cron이 60일 비활성 시 자동 중단되고 Cloudflare Pages는 Git 푸시만 트리거합니다. workflow_dispatch와 빈 커밋 또는 Deploy Hook으로 3시간 주기 자동배포를 복구하는 방법을 설명합니다."
image: "/images/20260402-github-actions-hugo-블로그-cloudf.webp"
technologies: ["GitHub Actions", "Go", "Cloudflare", "Hugo"]
faq:
  - question: "GitHub Actions Hugo 블로그 Cloudflare Pages 자동배포 cron 스케줄 안 될 때 해결 방법"
    answer: "GitHub Actions cron 스케줄이 안 되는 원인은 크게 두 가지예요. 첫째, 저장소에 60일 이상 활동이 없으면 GitHub이 워크플로우를 자동으로 비활성화하고, 둘째, Cloudflare Pages는 Git 푸시 이벤트 기반으로만 빌드가 트리거되기 때문에 cron 실행만으로는 배포가 일어나지 않아요. Actions 탭에서 워크플로우를 다시 Enable하고, Cloudflare Deploy Hook을 curl로 호출하는 방식을 함께 사용하면 해결할 수 있어요."
  - question: "Cloudflare Pages cron으로 자동 빌드 안 되는 이유"
    answer: "Cloudflare Pages는 기본적으로 Git 저장소에 푸시가 발생할 때만 빌드를 실행해요. GitHub Actions cron 워크플로우가 정상 실행되더라도, 해당 워크플로우가 저장소에 변경사항을 푸시하거나 Cloudflare Deploy Hook을 호출하지 않으면 빌드는 트리거되지 않아요. 따라서 cron 설정 자체는 맞아도 Cloudflare 입장에서는 아무런 신호를 받지 못한 상태가 돼요."
  - question: "Hugo 미래 날짜 포스트 예약 배포 자동화하는 방법"
    answer: "Hugo에서 미래 날짜(future date)로 설정한 포스트가 실제로 공개되려면, 해당 날짜 이후에 빌드 자체가 다시 실행돼야 해요. GitHub Actions cron으로 Cloudflare Deploy Hook URL을 주기적으로 curl 호출하면, 저장소 변경 없이도 Cloudflare 빌드를 강제로 실행시킬 수 있어요. Deploy Hook은 Cloudflare Pages 대시보드 → Settings → Builds & deployments에서 생성하고, GitHub Secrets에 등록해서 사용하면 돼요."
  - question: "GitHub Actions schedule 60일 지나면 비활성화 다시 활성화하는 방법"
    answer: "GitHub은 저장소에 커밋, PR, 이슈 등 활동이 60일 이상 없으면 schedule 트리거가 설정된 워크플로우를 자동으로 비활성화해요. 다시 활성화하려면 해당 저장소의 Actions 탭으로 이동해 비활성화된 워크플로우를 선택한 뒤 'Enable workflow' 버튼을 클릭하면 돼요. Hugo 블로그처럼 글 업로드 빈도가 낮은 저장소는 이 함정에 자주 빠지므로, workflow_dispatch를 함께 설정해두면 수동 실행으로 비활성화를 예방할 수 있어요."
  - question: "GitHub Actions cron 빈 커밋 푸시 vs Deploy Hook 어떤 방법이 더 나은가"
    answer: "빈 커밋 푸시 방식은 설정이 간단하지만 커밋 히스토리가 불필요하게 쌓이는 단점이 있어요. 반면 Cloudflare Deploy Hook을 curl로 호출하는 방식은 저장소를 오염시키지 않고 안정적으로 빌드를 트리거할 수 있어 운영 환경에 더 적합해요. GitHub Actions Hugo 블로그 Cloudflare Pages 자동배포 cron 스케줄 안 될 때 해결 목적으로는 Deploy Hook 방식에 workflow_dispatch를 병행 설정하는 조합이 가장 권장돼요."
---

Hugo 블로그를 Cloudflare Pages에 올려두고, cron 설정까지 했는데 포스트가 안 올라와요. 문법도 맞고, 설정도 맞는데. 그럼 대체 뭐가 문제일까요.

이 글에서는 원인이 정확히 어디에 있는지, 그리고 어떻게 고쳐야 하는지 바로 짚어드릴게요.

> **핵심 요약**
> - GitHub Actions `schedule: cron`은 저장소 활동이 60일 이상 없으면 GitHub이 자동으로 비활성화한다.
> - Cloudflare Pages는 Git 푸시 기반 트리거만 기본 지원하므로, cron만으로는 빌드가 실행되지 않는다.
> - `workflow_dispatch`와 빈 커밋(empty commit) 또는 Deploy Hook을 병행하면 이 문제를 해결할 수 있다.
> - 3시간마다 배포가 필요한 경우, GitHub Actions → Cloudflare Deploy Hook 호출 방식이 가장 안정적이다.
> - 예약된 Hugo 포스트(미래 날짜 `date`)가 실제로 배포되려면 빌드 자체가 트리거돼야 한다는 점을 놓치는 경우가 많다.

---

## cron이 침묵하는 이유, 두 군데예요

문제의 뿌리는 GitHub 쪽과 Cloudflare 쪽, 각각 따로 있어요.

**GitHub Actions의 비활성화 정책**

GitHub 공식 문서에 따르면, `schedule` 트리거가 설정된 워크플로우라도 해당 저장소에 60일간 활동(커밋, PR, 이슈 등)이 없으면 자동으로 비활성화돼요. Hugo 블로그처럼 글을 가끔 올리는 저장소는 이 함정에 딱 맞아요.

비활성화된 워크플로우는 Actions 탭에서 직접 "Enable" 버튼을 눌러야만 다시 작동해요. 근데 이걸 모르고 cron 설정이 잘못됐다고 착각하는 경우가 정말 많거든요.

**Cloudflare Pages의 빌드 트리거 구조**

Cloudflare Pages는 기본적으로 **푸시 이벤트**가 발생할 때 빌드해요. cron 스케줄 자체는 Cloudflare에게 아무런 신호를 주지 않아요. GitHub Actions 워크플로우가 실행되더라도, 그 워크플로우가 Cloudflare에 실제 트리거를 보내거나 저장소에 변경사항을 푸시하지 않으면 빌드는 안 일어나요.

그래서 흔히 나타나는 시나리오가 이거예요.
- cron 설정함 ✅
- 워크플로우 파일 문법 맞음 ✅
- 근데 Cloudflare에서 빌드 안 됨 ❌
- 이유: 워크플로우가 저장소 변경 없이 그냥 종료됨

---

## 세 가지 해결 방법, 직접 비교해볼게요

### 방법 1: Cloudflare Deploy Hook 직접 호출

Cloudflare Pages에서 제공하는 Deploy Hook URL을 GitHub Actions에서 `curl`로 호출하는 방식이에요.

```yaml
name: Scheduled Deploy
on:
  schedule:
    - cron: '0 */3 * * *'
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Cloudflare Deploy
        run: |
          curl -X POST "${{ secrets.CF_DEPLOY_HOOK_URL }}"
```

Deploy Hook URL은 Cloudflare Pages 대시보드 → 해당 프로젝트 → Settings → Builds & deployments에서 생성할 수 있어요. 이걸 GitHub 저장소 Secrets에 `CF_DEPLOY_HOOK_URL`로 저장하면 돼요.

Ben Abt의 2025년 7월 분석에 따르면, 이 방식은 저장소에 실제 변경사항이 없어도 Cloudflare 빌드를 강제로 실행시킬 수 있어서 Hugo의 미래 날짜 포스트 배포에 가장 적합한 방법이에요.

### 방법 2: 빈 커밋(Empty Commit) 푸시

cron 실행 시 저장소에 빈 커밋을 푸시해서 Cloudflare의 Git 트리거를 작동시키는 방식이에요.

```yaml
- name: Empty commit to trigger deploy
  run: |
    git config user.email "actions@github.com"
    git config user.name "GitHub Actions"
    git commit --allow-empty -m "chore: trigger scheduled build"
    git push
```

codeslog.com의 3시간마다 배포 사례에서도 이 방식을 사용했어요. 실제로 작동하지만, 커밋 히스토리가 지저분해진다는 단점이 있어요.

### 방법 3: `workflow_dispatch` 병행 설정 (필수 권고)

이건 단독 해결책이라기보다 위 두 방법에 반드시 함께 붙여야 하는 설정이에요.

```yaml
on:
  schedule:
    - cron: '0 6 * * *'
  workflow_dispatch:
```

`workflow_dispatch`를 추가하면 GitHub Actions UI에서 수동으로 워크플로우를 즉시 실행할 수 있어요. cron이 안 돌아갈 때 테스트하거나 즉시 배포가 필요할 때 유용하죠.

---

### 방법 비교: 어떤 상황에 어떤 방법이 맞을까요?

| 기준 | Deploy Hook 호출 | 빈 커밋 푸시 | 혼합(Hook + dispatch) |
|------|-----------------|-------------|----------------------|
| 저장소 오염 | 없음 | 커밋 히스토리 누적 | 없음 |
| 설정 복잡도 | 중간 (Secret 등록 필요) | 낮음 | 중간 |
| 안정성 | 높음 | 중간 | 높음 |
| 비활성화 위험 | 있음 (60일 규칙) | 있음 (60일 규칙) | 있음 (60일 규칙) |
| 최적 상황 | 미래 포스트 자동배포 | 빠른 테스트용 | 운영 환경 |
| Cloudflare 설정 | Deploy Hook 생성 필요 | 불필요 | Deploy Hook 생성 필요 |

Deploy Hook 방식이 가장 깔끔해요. 저장소 변경 없이 빌드만 실행하기 때문에 Hugo 블로그 Cloudflare Pages 자동배포 목적에 정확히 맞거든요.

---

## 실제로 이렇게 세팅하세요

### GitHub Actions cron 스케줄이 비활성화됐는지 먼저 확인

1. GitHub 저장소 → **Actions** 탭 이동
2. 왼쪽 워크플로우 목록에서 해당 워크플로우 클릭
3. 상단에 "This workflow is disabled" 배너가 보이면 **Enable workflow** 클릭

이 단계를 먼저 해야 해요. 여기서 막혀있으면 아래 설정을 아무리 잘해도 소용없거든요.

### 완성형 워크플로우 파일 예시

```yaml
name: Scheduled Hugo Deploy to Cloudflare
on:
  schedule:
    - cron: '0 0,6,12,18 * * *'  # 하루 4회 (0시, 6시, 12시, 18시 UTC)
  workflow_dispatch:

jobs:
  trigger-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Cloudflare Pages Deploy Hook
        run: |
          curl -s -X POST "${{ secrets.CF_DEPLOY_HOOK_URL }}" \
            -o /dev/null -w "Status: %{http_code}\n"
```

`-w "Status: %{http_code}\n"` 부분은 Cloudflare가 실제로 200 응답을 반환했는지 로그로 확인하는 거예요. 디버깅할 때 유용해요.

---

## 60일 비활성화를 막는 현실적인 방법

이게 진짜 골치예요. Deploy Hook 방식을 써도 GitHub Actions 워크플로우 자체가 비활성화되면 아무것도 안 돌아가거든요.

세 가지 대안을 권고해요.

- **정기적인 `workflow_dispatch` 수동 실행**: 한 달에 한 번이라도 UI에서 직접 실행하면 카운트 초기화돼요.
- **Keep-alive 워크플로우 추가**: 매달 1일 자정에 아무것도 안 하는 워크플로우를 실행시켜서 저장소를 살아있게 만드는 방법이에요.
- **Cloudflare Cron Triggers 사용**: Cloudflare Workers에서 제공하는 기능으로, GitHub 전혀 안 거치고 Cloudflare 자체에서 스케줄 실행이 가능해요. Pages보다 Workers 설정이 필요하지만 가장 독립적인 방법이에요.

---

## 지금 당장 체크해야 할 것들

체크리스트 순서가 중요해요.

1. **Actions 탭에서 워크플로우 활성화 상태 확인** → 비활성화면 Enable
2. **cron 문법 검증** → [crontab.guru](https://crontab.guru)에서 반드시 테스트
3. **Cloudflare Deploy Hook 생성 및 Secret 등록** → 저장소 Settings → Secrets and variables
4. **`workflow_dispatch` 추가** → 수동 테스트용으로 필수
5. **첫 실행 후 Cloudflare Pages 대시보드에서 빌드 로그 확인**

---

## 설정보다 더 중요한 것

설정 자체는 어렵지 않아요. 문제는 GitHub과 Cloudflare라는 두 시스템 사이에 어떤 신호가 오가야 하는지를 모르는 것에서 시작하거든요.

정리하면 이래요.
- **cron만으로는 Cloudflare 빌드가 안 돌아가요** — 반드시 Deploy Hook이나 커밋 트리거가 필요해요
- **60일 비활성화 정책**은 정적 블로그 운영자에게 큰 함정이에요
- **Deploy Hook + `workflow_dispatch` 조합**이 현재 가장 안정적인 방법이에요

Hugo의 `date` 필드에 미래 날짜를 써두고 자동으로 발행되길 기다리고 있다면, 빌드가 그 날짜에 실제로 실행되는지부터 확인해보세요. 거기서 막혀있을 가능성이 높거든요.

---

*참고 자료: Codeslog "Scheduled Publishing with GitHub Actions Every 3 Hours" / Ben Abt "Scheduled Builds for Cloudflare Deployments with GitHub Actions" (Medialesson, 2025.07)*

## 참고자료

1. [Scheduled Publishing with GitHub Actions Every 3 Hours | Codeslog](https://www.codeslog.com/en/posts/github-actions-scheduled-publish-check/)
2. [Scheduled Builds for Cloudflare Deployments with GitHub Actions | BEN ABT](https://benjamin-abt.com/blog/2025/07/14/scheduled-builds-cloudflare-github-actions/)
3. [Scheduled Builds for Cloudflare Deployments with GitHub Actions | by BEN ABT | Medialesson | Medium](https://medium.com/medialesson/scheduled-builds-for-cloudflare-deployments-with-github-actions-93341a112432)


---

*Photo by [Roman Synkevych](https://unsplash.com/@synkevych) on [Unsplash](https://unsplash.com/photos/blue-and-black-penguin-plush-toy-UT8LMo-wlyk)*
