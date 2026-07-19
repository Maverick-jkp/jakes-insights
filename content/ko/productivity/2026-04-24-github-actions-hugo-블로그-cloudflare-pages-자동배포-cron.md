---
title: "GitHub Actions cron 스케줄 무시될 때: Hugo 블로그 Cloudflare Pages 자동배포 해결법"
date: 2026-04-24T20:24:32+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "hugo", "GitHub Actions"]
description: "GitHub Actions cron 스케줄이 무시되는 두 가지 원인: 저장소 비활성화 시 GitHub의 자동 비활성화, Cloudflare Pages의 변경사항 없는 빌드 거부. workflow_dispatch와 빈 커밋으로 해결하는 실전 방법을 정리했습니"
image: "/images/20260424-github-actions-hugo-블로그-cloudf.webp"
technologies: ["GitHub Actions", "Go", "Cloudflare", "Hugo"]
faq:
  - question: "GitHub Actions Hugo 블로그 Cloudflare Pages 자동배포 cron 스케줄 무시될 때 해결법"
    answer: "GitHub Actions cron 스케줄이 무시되는 원인은 두 가지예요. GitHub가 저장소에 60일 이상 활동이 없으면 schedule 워크플로우를 자동 비활성화하는 정책과, Cloudflare Pages가 새 커밋이 없으면 빌드를 트리거하지 않는 구조 때문이에요. 가장 안정적인 해결법은 Cloudflare Pages Deploy Hook URL을 GitHub Actions cron에서 직접 POST 요청으로 호출하는 방식이에요."
  - question: "GitHub Actions schedule cron 60일 지나면 자동 비활성화되는 거 맞아요?"
    answer: "네, GitHub 공식 문서에 명시된 정책이에요. 저장소에 커밋, PR, 이슈 등 실제 사람이 만든 활동이 60일 이상 없으면 schedule 워크플로우가 자동으로 중단돼요. cron 자체 실행은 이 활동 카운트에 포함되지 않기 때문에, cron만 돌리고 있다고 해서 비활성화를 막을 수는 없어요."
  - question: "Hugo 블로그 예약 발행 날짜 지나도 글이 안 올라오는 이유"
    answer: "Hugo는 미래 날짜로 설정된 글을 해당 날짜가 지난 후 빌드에 포함시키는데, Cloudflare Pages는 새 커밋이 푸시될 때만 빌드를 실행하는 구조예요. 그래서 발행 예정일에 아무도 커밋을 하지 않으면 Cloudflare Pages는 새 빌드를 트리거하지 않고, 글은 계속 숨겨진 채로 남아요. 이 문제는 GitHub Actions cron에서 Cloudflare Deploy Hook을 호출하거나 빈 커밋을 푸시해서 강제로 빌드를 트리거하면 해결할 수 있어요."
  - question: "Cloudflare Pages Deploy Hook으로 코드 변경 없이 재배포하는 방법"
    answer: "Cloudflare Pages 설정에서 Deploy Hook URL을 생성한 뒤, GitHub Actions 워크플로우에서 curl -X POST 명령으로 해당 URL을 호출하면 커밋 없이도 빌드가 실행돼요. Deploy Hook URL은 외부에 노출되면 누구나 빌드를 트리거할 수 있어 보안 위험이 있으므로, 반드시 GitHub Secrets에 저장해서 사용해야 해요."
  - question: "GitHub Actions Hugo 블로그 Cloudflare Pages 자동배포 cron 스케줄 무시될 때 해결법 중 빈 커밋 방식 단점"
    answer: "빈 커밋 방식은 git commit --allow-empty로 실제 변경 없이 커밋을 만들어 푸시하는 방법으로, GitHub 60일 비활성화 문제와 Cloudflare 빌드 트리거 문제를 동시에 해결할 수 있어요. 다만 매일 실행하면 한 달에 30개씩 'trigger' 커밋이 쌓여 커밋 히스토리가 지저분해지는 단점이 있어요. 커밋 히스토리 오염이 신경 쓰인다면 Deploy Hook 직접 호출 방식이 더 적합해요."
aliases:
  - "/tech/2026-04-24-github-actions-hugo-블로그-cloudflare-pages-자동배포-cron/"
  - "/ko/tech/2026-04-24-github-actions-hugo-블로그-cloudflare-pages-자동배포-cron/"

---

cron 스케줄을 설정해놨는데 아무 일도 안 일어나는 거예요. 로그엔 아무것도 없고, 배포는 안 되고. 뭐가 잘못된 건지 찾을 수도 없죠.

Hugo 블로그를 GitHub Actions로 빌드하고 Cloudflare Pages에 자동배포하는 구조, 개인 기술 블로그에서 거의 표준이 됐어요. 그런데 이 조합엔 꽤 많은 사람들이 조용히 당하는 함정이 있어요.

> **핵심 요약**
> - GitHub Actions의 `on: schedule` cron 트리거는 저장소에 최근 활동이 없으면 GitHub가 자동으로 비활성화한다.
> - Cloudflare Pages의 Git 통합 방식은 "변경 사항이 있을 때만" 빌드를 트리거하므로, 코드 변경 없이 cron만으로는 재배포가 안 된다.
> - `workflow_dispatch` + cron 조합 또는 빈 커밋(empty commit) 방식으로 이 문제를 우회할 수 있다.
> - Cloudflare Pages의 Deploy Hooks URL을 GitHub Actions cron에서 직접 호출하는 방법이 가장 안정적이다.

---

## 원인이 하나가 아니에요

GitHub Actions cron 스케줄이 무시되는 데는 두 가지 서로 다른 원인이 있어요. GitHub 쪽 문제와 Cloudflare Pages 쪽 문제가 각각 따로 존재하거든요.

**GitHub Actions의 cron 비활성화 정책**

GitHub는 공식 문서에서 저장소에 60일 이상 활동이 없으면 `schedule` 워크플로우를 자동으로 중단한다고 명시하고 있어요. 여기서 "활동"은 커밋, PR, 이슈 등 실제 사람이 만든 이벤트를 말해요. cron 자체 실행은 이 카운트에 포함되지 않아요.

그리고 하나 더 있어요. GitHub의 공용 러너는 과부하 상태일 때 예약된 워크플로우를 지연시키거나 건너뛰는 경우가 있어요. GitHub는 이를 "best-effort scheduling"이라고 표현하는데, 쉽게 말하면 "최선을 다해 실행하겠지만 보장은 못 한다"는 거예요. Codeslog의 사례 분석에 따르면, 3시간마다 실행되도록 설정한 cron이 실제로는 4~6시간 간격으로 실행되는 경우도 있었다고 해요.

**Cloudflare Pages의 빌드 트리거 구조**

Cloudflare Pages는 연결된 Git 저장소의 커밋 이벤트를 감지해서 빌드를 실행해요. 공식 문서 기준으로, Git 통합 방식에서는 브랜치에 새로운 커밋이 푸시될 때만 빌드가 트리거돼요. 코드 변경 없이 시간만 지나서는 Cloudflare Pages가 새로 빌드할 이유를 모르는 거예요.

Hugo 블로그에서 예약 발행을 쓰는 경우가 이 함정에 빠지기 딱 좋아요. 글을 미리 써두고 `date: 2026-05-01`처럼 미래 날짜로 설정해두면, Hugo는 해당 날짜가 지나야 그 글을 빌드에 포함시켜요. 그런데 그날 아무도 커밋을 안 하면, Cloudflare Pages는 새 빌드를 실행하지 않아요. 글은 영원히 숨겨진 채로 남는 거죠.

Chris Wiegman이 Hugo 사이트를 Cloudflare Workers와 Pages에 배포하면서 겪은 경험을 2026년 1월에 공개했는데, 핵심은 같아요. "정적 사이트는 외부 트리거가 없으면 스스로 재빌드되지 않는다." 오류 메시지도 없고, 워크플로우 실패 알림도 없어요. 그냥 조용히 아무 일도 안 일어나는 거예요.

---

## 해결 방법 세 가지

### 방법 1: Cloudflare Deploy Hooks 직접 호출

가장 안정적인 방법이에요. Cloudflare Pages 설정에서 Deploy Hook URL을 생성하면, 외부에서 HTTP POST 요청만 보내도 빌드가 실행돼요. 코드 변경이 필요 없어요.

```yaml
name: Scheduled Deploy
on:
  schedule:
    - cron: '0 */3 * * *'
  workflow_dispatch:

jobs:
  trigger-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Cloudflare Pages Build
        run: |
          curl -X POST "${{ secrets.CF_DEPLOY_HOOK_URL }}"
```

`CF_DEPLOY_HOOK_URL`은 반드시 GitHub Secrets에 저장해야 해요. Deploy Hook URL이 외부에 노출되면 누구든 빌드를 트리거할 수 있으니까요.

### 방법 2: 빈 커밋(Empty Commit) 푸시

저장소에 실제 변경 없이 커밋만 만들어서 푸시하는 방법이에요. GitHub의 60일 비활성화 문제도 함께 해결돼요.

```yaml
- name: Empty commit to trigger build
  run: |
    git config user.email "actions@github.com"
    git config user.name "GitHub Actions"
    git commit --allow-empty -m "chore: trigger scheduled build"
    git push
```

단점은 커밋 히스토리가 지저분해진다는 거예요. 매일 실행하면 한 달에 30개의 "trigger" 커밋이 쌓여요.

### 방법 3: `workflow_dispatch` 추가

cron만 쓰지 않고 `workflow_dispatch`를 함께 설정해두면, 스케줄이 누락됐을 때 GitHub UI에서 수동으로 실행할 수 있어요. 근본적인 해결은 아니지만 보험 역할을 해요.

### 어떤 방법이 맞는 경우

| 기준 | Deploy Hook 호출 | 빈 커밋 | workflow_dispatch |
|------|-----------------|---------|-------------------|
| 안정성 | ✅ 높음 | 중간 | 수동 개입 필요 |
| 설정 복잡도 | 보통 (Secret 설정 필요) | 낮음 | 낮음 |
| 커밋 히스토리 오염 | 없음 | 있음 | 없음 |
| Cloudflare 빌드 월 제한 | 고려 필요 | 고려 필요 | 해당 없음 |
| 60일 비활성화 방지 | ❌ | ✅ | ✅ (수동 시) |
| 예약 발행 자동화 | ✅ | ✅ | ❌ |

예약 발행 자동화가 목적이라면 Deploy Hook 호출이 최선이에요. 코드 변경 없이 Cloudflare Pages를 직접 깨울 수 있거든요. 빈 커밋 방식은 Git 히스토리를 신경 쓰는 프로젝트엔 맞지 않아요.

---

## 적용할 때 챙겨야 할 것들

Hugo 블로그에서 예약 발행을 쓰고 있다면 Deploy Hook + cron 조합으로 설정하고 매 3~6시간마다 실행하도록 잡는 게 좋아요. 참고로 Cloudflare Pages 무료 플랜은 월 500회 빌드 제한이 있어요. 1시간마다 실행하면 한 달에 720회가 되므로, 3시간 간격이 적당한 균형점이에요.

저장소를 오랫동안 업데이트 안 한다면, cron 워크플로우 파일 안에 빈 커밋이나 `workflow_dispatch`를 함께 넣어서 GitHub의 60일 비활성화 정책을 피해야 해요. 안 그러면 어느 순간 스케줄 전체가 조용히 멈춰 있을 거예요.

빌드 성공 여부를 확인하고 싶다면, GitHub Actions에서 Cloudflare API로 배포 상태를 폴링하는 스텝을 추가할 수도 있어요. 단순 블로그라면 Cloudflare Pages 대시보드 알림 설정으로 충분하긴 해요.

---

## 앞으로는 어떻게 될까요

- **GitHub Actions cron의 한계는 구조적 문제**예요. GitHub가 정책을 바꾸지 않는 한, 60일 비활성화 이슈는 계속 있을 거예요.
- **Cloudflare Pages가 예약 빌드 기능을 직접 제공할 가능성이 있어요.** 이미 Workers Cron Triggers가 있는 만큼, Pages에 유사한 기능이 추가되면 외부 트리거 없이도 해결될 수 있어요.
- **지금 당장은 Deploy Hook 기반 접근이 가장 확실해요.**

cron 스케줄이 무시되는 건 버그가 아니에요. 두 시스템의 설계 방식이 맞물리면서 생기는 구조적 간극이에요. 한 번만 제대로 이해하면, 해결도 간단해요.

지금 바로 Cloudflare Pages 설정에서 Deploy Hook을 만들어보세요. 그게 시작이에요.

---

*이 글이 도움이 됐다면, Hugo + GitHub Actions + Cloudflare Pages 조합에서 겪은 다른 설정 문제도 댓글로 남겨주세요. 다음 분석 주제를 선정하는 데 참고할게요.*

## 참고자료

1. [Scheduled Publishing with GitHub Actions Every 3 Hours | Codeslog](https://www.codeslog.com/en/posts/github-actions-scheduled-publish-check/)
2. [Deploying My Hugo Site to Cloudflare Workers - Chris Wiegman](https://chriswiegman.com/2026/01/deploying-my-hugo-site-to-cloudflare-workers/)
3. [Git integration · Cloudflare Pages docs](https://developers.cloudflare.com/pages/configuration/git-integration/)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-white-dice-with-a-black-github-logo-on-it-HLQDfaJUTVI)*
