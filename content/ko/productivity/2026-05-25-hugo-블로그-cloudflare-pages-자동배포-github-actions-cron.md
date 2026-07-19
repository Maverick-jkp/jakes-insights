---
title: "Hugo 블로그 Cloudflare Pages 자동배포 GitHub Actions cron 스케줄 안될 때 원인과 해결"
date: 2026-05-25T22:51:15+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "hugo", "/ube14/ub85c/uadf8", "cloudflare", "JavaScript"]
description: "Hugo 블로그 Cloudflare Pages 자동배포 중 GitHub Actions cron 스케줄이 작동하지 않는다면 60일 비활성 리포지토리 자동 비활성화 정책을 먼저 확인하세요. 에러 없이 조용히 멈추는 원인과 해결법을"
image: "/images/20260525-hugo-블로그-cloudflare-pages-자동배포.webp"
technologies: ["JavaScript", "Vercel", "GitHub Actions", "Go", "Java"]
faq:
  - question: "GitHub Actions cron 스케줄 설정했는데 아무것도 안 실행되는 이유"
    answer: "GitHub Actions는 60일간 리포지토리에 아무 활동이 없으면 schedule 트리거를 자동으로 비활성화하는 정책이 있어요. Actions 탭에서 해당 워크플로우를 선택했을 때 'Enable workflow' 버튼이 보인다면 비활성화된 것이므로, 버튼을 눌러 다시 활성화하면 다음 cron 주기부터 정상 동작해요."
  - question: "Hugo 블로그 Cloudflare Pages 자동배포 GitHub Actions cron 스케줄 안될 때 원인 해결 방법"
    answer: "Hugo 블로그 Cloudflare Pages 자동배포에서 GitHub Actions cron 스케줄이 안 될 때 원인은 크게 세 가지예요: 60일 비활성 정책으로 인한 워크플로우 자동 비활성화, 워크플로우 파일 브랜치와 Cloudflare Pages 프로덕션 브랜치 불일치, 그리고 UTC와 KST 타임존 차이로 예약 글이 빌드에서 누락되는 경우예요. 빌드 명령어에 'TZ='Asia/Seoul' hugo --minify'처럼 타임존을 명시하면 타임존 관련 문제를 해결할 수 있어요."
  - question: "Hugo publishDate 예약 발행 글이 자동배포에서 빠지는 이유"
    answer: "GitHub Actions는 UTC 기준으로 동작하기 때문에, 한국 시간(KST) 기준으로 오늘 날짜인 글도 UTC로는 아직 전날로 인식되어 빌드에서 제외될 수 있어요. 빌드 명령어를 'TZ='Asia/Seoul' hugo --minify'로 변경해 타임존을 명시적으로 지정하거나, '--buildFuture' 옵션을 신중하게 활용하면 이 문제를 해결할 수 있어요."
  - question: "Cloudflare Pages Build Hook cron으로 자동 빌드 트리거하는 방법"
    answer: "Cloudflare Pages의 Build Hook URL을 생성한 뒤, GitHub Actions 워크플로우에서 'curl -X POST' 명령으로 해당 URL에 요청을 보내면 빌드가 트리거돼요. 이 방식은 GitHub Actions cron 단독 사용보다 안정적이고, API 응답으로 성공·실패 여부를 명시적으로 확인할 수 있어 디버깅도 쉬워요."
  - question: "Hugo 블로그 Cloudflare Pages 자동배포 GitHub Actions cron 스케줄 안될 때 브랜치 설정 확인하는 법"
    answer: "워크플로우 yaml 파일이 위치한 브랜치와 Cloudflare Pages 대시보드에서 프로덕션으로 설정된 브랜치가 일치하는지 확인해야 해요. 예를 들어 워크플로우는 'master' 브랜치에 있는데 Cloudflare Pages가 'main' 브랜치를 바라보고 있으면, cron이 정상 실행되어도 Cloudflare Pages 입장에서는 변화가 없어 배포가 트리거되지 않아요."
aliases:
  - "/tech/2026-05-25-hugo-블로그-cloudflare-pages-자동배포-github-actions-cron/"

---

cron 스케줄을 걸어놨는데 아무것도 안 올라와 있어요. 로그도 깨끗하고, 에러도 없어요. 그냥 아무 일도 안 일어난 거예요.

Hugo 블로그를 Cloudflare Pages에 자동배포하면서 GitHub Actions cron 스케줄을 쓰다 보면 꼭 이런 상황이 한 번은 찾아와요. 설정은 다 맞는데 왜 안 되는 걸까요? 실제로 찾아보면 이 문제를 겪은 사람이 정말 많고, 원인도 여러 갈래로 나뉘어요. 2026년 현재도 GitHub Actions의 이 특성은 바뀌지 않았거든요.

> **핵심 요약**
> - GitHub Actions의 cron 스케줄은 비활성 리포지토리에서 **자동으로 비활성화**되는 정책이 있어요. 60일 기준이 적용돼요.
> - Hugo 블로그 Cloudflare Pages 자동배포 파이프라인에서 cron이 안 되는 원인은 크게 세 가지예요: 워크플로우 비활성화, cron 문법 오류, 브랜치 불일치.
> - GitHub 공식 문서에 따르면 cron 스케줄은 UTC 기준으로 동작하고, 피크 시간대에는 최대 수십 분 지연이 발생할 수 있어요.
> - Cloudflare Pages의 빌드 훅(Build Hook)을 함께 쓰면 cron 의존도를 줄이고 더 안정적인 자동배포 파이프라인을 만들 수 있어요.

---

## 왜 이 문제가 계속 나오냐면요

Hugo는 정적 사이트 생성기 시장에서 꾸준히 쓰이는 도구예요. Jekyll보다 빌드 속도가 빠르고, Gatsby처럼 JavaScript 생태계에 의존하지 않아서 기술 블로거나 개발자들이 선호하죠.

배포 플랫폼으로는 Cloudflare Pages가 점점 많이 쓰여요. Vercel, Netlify와 비교했을 때 무료 플랜의 대역폭 제한이 없다는 게 큰 장점이에요. GitHub에서 직접 연결하면 푸시할 때마다 자동으로 빌드가 트리거돼요.

문제는 예약 발행이에요. Hugo는 `publishDate`를 미래 날짜로 설정하면 그 날짜 전에는 빌드해도 해당 글이 생성되지 않아요. 그래서 매일 자정에 GitHub Actions cron으로 빌드를 트리거하고, Cloudflare Pages가 그걸 잡아서 배포하는 구조를 많이 써요.

그런데 이 구조가 조용히 망가지는 경우가 꽤 있어요. 특히 블로그를 한동안 안 올리다가 돌아왔을 때요.

공식 GitHub 문서에서도 "cron 스케줄은 항상 정확한 시간에 실행되지 않을 수 있다"고 명시하고 있어요. 그리고 이건 2026년 현재도 바뀌지 않았어요.

---

## 원인 세 가지, 하나씩 봐요

### 원인 1: 리포지토리 비활성화로 워크플로우가 꺼진 경우

GitHub는 **60일간 리포지토리에 아무 활동이 없으면 `schedule` 트리거를 자동으로 비활성화**해요. 공식 문서에 이 정책이 명시돼 있어요.

블로그를 두 달 넘게 안 업데이트했다면? 자동배포 cron이 조용히 꺼진 거예요.

확인 방법은 간단해요. GitHub 리포지토리의 **Actions 탭 → 워크플로우 선택 → Enable workflow** 버튼이 보인다면 비활성화된 거예요. 활성화하고 나면 다음 cron 주기부터 정상 동작해요.

그런데 이게 끝이 아니에요.

### 원인 2: cron 문법은 맞는데 브랜치가 틀린 경우

Hugo 블로그 Cloudflare Pages 자동배포 설정할 때 가장 자주 보는 실수예요.

```yaml
on:
  schedule:
    - cron: '0 15 * * *'  # UTC 15시 = KST 자정
```

이렇게 설정해놓고 Cloudflare Pages는 `main` 브랜치를 바라보는데, 워크플로우는 `master` 브랜치에 있는 경우가 있어요. 결과는? cron은 실행됐지만 Cloudflare Pages 입장에서는 아무 변화가 없는 거예요.

워크플로우 파일이 어느 브랜치에 있는지, Cloudflare Pages가 어느 브랜치를 프로덕션으로 보는지 — 이 두 개가 맞아야 해요.

### 원인 3: cron은 맞는데 Hugo가 예약 글을 빌드 안 한 경우

빌드 명령어를 이렇게 쓴 경우를 봐요:

```bash
hugo --minify
```

이 명령어는 현재 날짜 기준으로 빌드해요. `publishDate`가 오늘 날짜인 글도 빠질 수 있어요. 타임존 때문이에요.

GitHub Actions는 UTC 기준으로 돌아가거든요. 한국 시간으로 5월 25일 자정에 cron이 돌아도, UTC로는 아직 5월 24일이에요. 그러면 오늘 예약 발행한 글이 포함 안 돼요.

해결 방법은 두 가지예요.

```bash
# 방법 1: 환경변수로 타임존 지정
TZ="Asia/Seoul" hugo --minify

# 방법 2: 미래 날짜 글도 포함 (주의해서 써야 해요)
hugo --minify --buildFuture
```

---

## 접근 방법 비교: 어떤 방식이 더 나을까요?

| 항목 | GitHub Actions cron 단독 | Cloudflare Pages Build Hook 병행 |
|------|--------------------------|----------------------------------|
| 설정 복잡도 | 낮음 | 중간 |
| 안정성 | 불안정 (지연/비활성화 위험) | 높음 |
| 비활성화 리스크 | 60일 규칙 적용 | 없음 |
| 타임존 처리 | 수동 설정 필요 | 워크플로우에서 제어 가능 |
| 비용 | 무료 (Public repo) | 무료 |
| 디버깅 난이도 | 높음 (묵묵히 실패) | 낮음 (명시적 API 응답) |

Cloudflare Pages의 Build Hook는 특정 URL에 POST 요청을 보내면 빌드가 트리거되는 기능이에요. GitHub Actions에서 cron으로 해당 URL에 `curl` 요청을 보내는 방식으로 쓸 수 있어요.

```yaml
- name: Trigger Cloudflare Build
  run: |
    curl -X POST "https://api.cloudflare.com/client/v4/pages/webhooks/deploy_hooks/YOUR_HOOK_ID"
```

이 방식을 쓰면 GitHub Actions는 그냥 "신호를 보내는 역할"만 해요. 빌드 자체는 Cloudflare Pages가 담당하고, 실제 배포 로그도 Cloudflare 대시보드에서 바로 볼 수 있어요.

---

## 실제로 문제를 찾고 고치는 순서

**상황 1: 워크플로우가 아예 안 돌았을 때**

Actions 탭에서 워크플로우 실행 기록이 비어 있다면 비활성화된 거예요. Enable workflow로 재활성화하고, 더미 커밋을 하나 넣어서 강제로 활성화 신호를 줘요. 앞으로는 60일 안에 한 번씩 의미 있는 커밋을 남기는 게 좋아요.

**상황 2: 워크플로우는 돌았는데 Cloudflare에 반영이 안 됐을 때**

워크플로우 로그를 보면 Hugo 빌드 결과물이 나와 있을 거예요. 빌드는 성공했는데 배포가 안 됐다면 `git push` 단계에서 뭔가 빠진 거예요. 워크플로우에서 변경사항이 없으면 push가 스킵되고, Cloudflare는 아무 신호도 못 받아요.

빈 커밋을 만들어서 push를 강제하거나, Build Hook를 쓰는 게 더 깔끔해요.

**상황 3: 배포됐는데 예약 글이 없을 때**

타임존 문제예요. 위에서 설명한 `TZ="Asia/Seoul"` 방법을 써요. 그래도 안 된다면 `--buildFuture` 플래그를 쓰되, 진짜 미래 글이 같이 올라가지 않도록 `publishDate` 관리를 꼼꼼하게 해야 해요.

---

## 정리하면 이렇게 돼요

Hugo 블로그 Cloudflare Pages 자동배포에서 GitHub Actions cron 스케줄이 안 될 때, 원인은 거의 세 가지 중 하나예요.

- **60일 비활성화 정책** → Actions 탭에서 직접 확인하고 재활성화
- **브랜치 불일치** → Cloudflare Pages 프로덕션 브랜치와 워크플로우 위치 맞추기
- **타임존 + 빌드 플래그** → `TZ="Asia/Seoul"` 또는 `--buildFuture` 써서 해결

다음 6-12개월 안에 GitHub Actions의 cron 신뢰성이 개선될 거라는 공식 신호는 아직 없어요. 그래서 Build Hook를 병행하는 구조가 당분간은 가장 안정적인 답이에요.

지금 당장 Hugo 블로그 Cloudflare Pages 자동배포가 안 되고 있다면, Actions 탭부터 열어보세요. Enable 버튼이 있으면 그게 범인이에요.

배포 구조를 더 단단하게 만들고 싶다면 — Build Hook로 cron의 역할을 분리하는 방식을 한번 적용해보세요. 생각보다 간단하거든요.

## 참고자료

1. [サボりのAlice、そして意図せず増殖した記事、制御不能の自動投稿！GitHub Actionsのcronが動かなかった話｜えいりす](https://note.com/alice_ai_blog/n/nd200e3274b1a)
2. [Automatic publishing of my Hugo website using Github and Cloudflare Pages - Virtual to the Core](https://www.virtualtothecore.com/hugo-github-cloudflare-pages/)
3. [Host on Cloudflare](https://gohugo.io/host-and-deploy/host-on-cloudflare/)


---

*Photo by [NASA](https://unsplash.com/@nasa) on [Unsplash](https://unsplash.com/photos/photo-of-outer-space-Q1p7bh3SHj8)*
