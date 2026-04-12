---
title: "GitHub Actions Hugo 블로그 Cloudflare Pages 배포 cron 트리거 실행 안 될 때 원인 해결"
date: 2026-04-12T19:57:52+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "github", "actions", "hugo", "GitHub Actions"]
description: "GitHub Actions cron 트리거가 조용히 실패하는 세 가지 원인을 분석했습니다. 60일 비활성 레포 자동 비활성화, Cloudflare API 시크릿 누락, cron 표현식 오류를 실제 Hugo 블로그 배포 환경 기준으로 정"
image: "/images/20260412-github-actions-hugo-블로그-cloudf.webp"
technologies: ["GitHub Actions", "Go", "Cloudflare", "Hugo"]
faq:
  - question: "GitHub Actions cron 트리거 60일 지나면 자동으로 꺼지나요"
    answer: "네, GitHub 공식 정책에 따라 기본 브랜치에 60일 이상 커밋이 없으면 schedule 트리거가 자동으로 비활성화돼요. Hugo 블로그처럼 업데이트 빈도가 낮은 레포지토리는 특히 이 조건에 걸리기 쉬워요. Actions 탭에서 워크플로를 수동으로 다시 활성화하거나 아무 파일이나 수정해서 커밋하면 즉시 복구돼요."
  - question: "GitHub Actions Hugo 블로그 Cloudflare Pages 배포 cron 트리거 실행 안 될 때 원인 해결 방법"
    answer: "GitHub Actions Hugo 블로그 Cloudflare Pages 배포 cron 트리거가 실행 안 될 때 원인은 크게 세 가지예요. 레포지토리 60일 비활성화로 인한 자동 비활성화, CLOUDFLARE_API_TOKEN 또는 CLOUDFLARE_ACCOUNT_ID 시크릿 누락, cron 표현식을 KST 기준으로 잘못 작성해 9시간 오차가 발생하는 경우예요. 각 원인을 순서대로 점검하면 대부분 해결돼요."
  - question: "GitHub Actions cron 표현식 한국 시간 KST로 설정하는 법"
    answer: "GitHub Actions의 cron은 항상 UTC 기준으로 동작하기 때문에 KST로 직접 설정할 수 없어요. 한국 시간 오전 9시에 실행하려면 9시간을 빼서 UTC 자정인 '0 0 * * *'으로 작성해야 해요. KST 기준으로 그대로 입력하면 실제 실행 시간이 항상 9시간 늦어지는 문제가 생겨요."
  - question: "GitHub Actions 워크플로 성공인데 Cloudflare Pages 배포가 안 되는 이유"
    answer: "워크플로 로그에 성공으로 표시돼도 CLOUDFLARE_API_TOKEN의 권한 범위가 잘못 설정되거나 CLOUDFLARE_ACCOUNT_ID가 누락되면 실제 배포는 조용히 실패해요. 에러 메시지가 명확하게 출력되지 않는 경우도 있어서 '성공했는데 배포가 안 되는' 상황이 발생해요. 두 시크릿이 모두 올바르게 설정되어 있는지, API 토큰에 Cloudflare Pages 배포 권한이 포함되어 있는지 먼저 확인하세요."
  - question: "Hugo 예약 포스트 빌드했는데 글이 안 보일 때 해결법"
    answer: "Hugo는 프론트매터의 date 필드가 빌드 시점보다 미래면 해당 포스트를 자동으로 미발행 처리해요. 예를 들어 KST 기준 날짜를 그대로 쓰면 UTC 변환 후 빌드 시점보다 미래가 되어 포스트가 숨겨질 수 있어요. 빌드 커맨드에 --buildFuture 플래그를 추가하거나, date 필드를 빌드 시점보다 충분히 이른 시간으로 설정하면 해결돼요."
---

Hugo 블로그 예약 발행 설정해뒀는데 포스트가 안 올라와요. 워크플로 파일은 멀쩡해 보이고, 로그도 없고, 에러도 없어요. 그냥 조용히 실패한 거예요.

생각보다 많은 개발자들이 이 함정에 빠져요. 원인은 대부분 세 곳 중 하나예요.

> **핵심 요약**
> - GitHub Actions의 `schedule` 트리거는 레포지토리가 60일 이상 비활성 상태면 자동으로 비활성화돼요. Hugo 블로그처럼 글 업데이트 빈도가 낮으면 특히 주의해야 해요.
> - Cloudflare Pages는 GitHub Actions에서 직접 배포할 때 `CLOUDFLARE_API_TOKEN`과 `CLOUDFLARE_ACCOUNT_ID` 시크릿이 누락되면 워크플로가 실행돼도 배포는 조용히 실패해요.
> - cron 표현식의 시간대는 항상 UTC 기준이에요. 한국 시간(KST) 기준으로 쓰면 실제 실행 시간이 9시간 밀려요.
> - GitHub 무료 플랜에서 cron은 예정 시간보다 최대 수십 분 지연될 수 있어요. SLA가 없는 "best-effort" 방식이에요.
> - Hugo의 `draft: false` + `date` 필드 설정이 맞아도, 빌드 시점이 예약 시간보다 앞서면 포스트는 발행되지 않아요.

---

## cron 트리거가 실행 안 되는 이유: 생각보다 단순해요

**원인 1: 레포지토리 비활성화**

GitHub 공식 문서에 따르면, 기본 브랜치에 60일 동안 커밋이 없으면 예약 워크플로가 자동으로 꺼져요. Hugo 블로그는 한 달에 포스트 몇 개만 올리는 경우가 많아서 이 60일 기준에 걸리기 쉬워요. GitHub는 "이 레포는 활성 상태가 아니구나"라고 판단하고 조용히 cron을 멈춰요.

해결은 간단해요. Actions 탭에서 해당 워크플로를 수동으로 다시 활성화하거나, 아무 파일이나 약간 수정해서 커밋하면 다시 살아나요.

**원인 2: UTC vs KST 혼동**

```yaml
on:
  schedule:
    - cron: '0 9 * * *'
```

이 설정은 UTC 기준 오전 9시예요. 한국 시간으로는 오후 6시가 되는 거죠. KST 기준인 줄 알고 쓰면 항상 9시간이 틀려요. 한국 시간 오전 9시에 맞추려면 `'0 0 * * *'`으로 설정해야 해요.

**원인 3: GitHub의 cron 지연**

GitHub 워크플로 스케줄러는 정확도 보장이 없어요. GitHub Status 페이지와 개발자 커뮤니티 보고에 따르면, 피크 타임에는 예정 시간보다 30분 이상 지연되는 경우도 있어요. 3시간마다 포스트를 발행하는 워크플로라면 이 지연이 쌓여서 하루에 꽤 차이가 날 수 있어요.

---

## Cloudflare Pages 배포 파이프라인: 어디서 끊기는가

Hugo 블로그를 Cloudflare Pages에 배포할 때 GitHub Actions를 직접 쓰는 방식과, Cloudflare의 자체 CI를 쓰는 방식 두 가지가 있어요. 선택에 따라 문제가 생기는 지점도 달라요.

**GitHub Actions 직접 배포 방식의 함정**

`wrangler` CLI나 `cloudflare/pages-action`을 쓸 때는 시크릿 설정이 핵심이에요. Ben Abt의 2025년 가이드에서도 강조하는 부분인데, `CLOUDFLARE_API_TOKEN`의 권한 범위가 잘못 설정되면 워크플로 자체는 성공으로 표시돼도 실제 배포는 안 돼요.

필요한 시크릿:
- `CLOUDFLARE_API_TOKEN` — Cloudflare Pages 배포 권한 포함
- `CLOUDFLARE_ACCOUNT_ID` — 계정 ID (프로젝트 ID와 다름)

이 둘 중 하나만 빠져도 배포가 실패해요. 그런데 에러 메시지가 워크플로 로그에 명확하게 안 나올 때도 있어서 "성공했는데 왜 안 배포되지?" 상황이 생겨요.

**Cloudflare Pages 자체 CI 방식의 한계**

Cloudflare Pages의 내장 CI는 Git 이벤트(push)에만 반응해요. cron 기반 자동 빌드를 네이티브로 지원하지 않아요. Codeslog의 사례에서도 "3시간마다 Hugo 포스트 자동 발행"을 구현하려면 결국 GitHub Actions의 cron에 의존해서 빈 커밋을 만들거나 Cloudflare API를 직접 호출하는 방식을 써야 했어요.

**배포 방식 비교**

| 기준 | GitHub Actions 직접 배포 | Cloudflare Pages 자체 CI | GitHub → CF Pages (webhook) |
|------|--------------------------|--------------------------|------------------------------|
| cron 지원 | ✅ 직접 지원 | ❌ 미지원 | ⚠️ 우회 필요 |
| 설정 복잡도 | 높음 (시크릿 관리) | 낮음 | 중간 |
| 비활성화 위험 | ✅ 60일 룰 적용 | ❌ 해당 없음 | ✅ 60일 룰 적용 |
| Hugo 버전 제어 | ✅ 자유롭게 지정 | ⚠️ 환경변수로 제한적 지정 | ⚠️ 동일 |
| 디버깅 가시성 | 높음 | 낮음 | 중간 |
| 추천 용도 | cron 배포, 세밀한 제어 필요 시 | 단순 push 배포 | 레거시 설정 유지 시 |

cron 활용 면에서는 GitHub Actions 직접 배포가 사실상 유일한 선택지예요. 그만큼 관리 포인트도 많고요.

---

## Hugo의 날짜 필드와 빌드 타이밍

워크플로가 정상적으로 실행돼도 포스트가 안 보이는 또 다른 원인은 Hugo의 날짜 처리 방식에 있어요.

Hugo는 `date` 필드가 빌드 시점보다 미래면 해당 포스트를 발행하지 않아요. 예를 들어 워크플로가 UTC 03:00에 실행되고, 포스트의 `date`가 `2026-04-13T00:00:00+09:00`이면, UTC로 변환하면 `2026-04-12T15:00:00Z`예요. 빌드 시점인 `2026-04-12T03:00:00Z`보다 12시간이 남은 거죠. Hugo는 이 포스트를 미발행으로 처리해요.

해결 방법은 두 가지예요.

1. Hugo 빌드 커맨드에 `--buildFuture` 플래그를 추가하기
2. 날짜를 빌드 시점보다 충분히 앞서게 설정하기 (더 안전한 방식)

Caktus Group의 2025년 가이드에서도 YAML 프론트매터에서 시간대를 생략하면 로컬 시간으로 처리될 수 있어 빌드 환경(Ubuntu, UTC)과 충돌이 생긴다고 설명해요. 시간대 명시는 습관적으로 해두는 게 낫죠.

---

## 실제 디버깅 순서: 5단계 체크리스트

**1단계: 워크플로가 실행됐는지 확인**
GitHub Actions 탭에서 실행 기록을 직접 확인해요. 기록 자체가 없다면 레포지토리 비활성화 문제예요. 수동 실행(`workflow_dispatch`)으로 먼저 테스트해봐요.

**2단계: cron 표현식 UTC 검증**
[crontab.guru](https://crontab.guru)로 UTC 기준 실행 시간을 확인해요. 의도한 KST 시간과 맞는지 체크예요.

**3단계: 시크릿 설정 재확인**
레포지토리 Settings → Secrets에서 `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` 두 개가 모두 있는지, API 토큰의 권한 범위가 Cloudflare Pages 배포를 포함하는지 확인해요.

**4단계: Hugo 빌드 로그 확인**
워크플로 실행은 됐는데 포스트가 안 나온다면 Hugo 빌드 단계 출력을 봐요. "Page skipped" 메시지가 있으면 날짜 문제예요.

**5단계: Cloudflare Pages 대시보드 확인**
GitHub Actions 로그와 별개로 Cloudflare Pages 대시보드에서도 배포 히스토리를 확인해요. 두 쪽 모두 성공이어야 진짜 배포된 거예요.

---

## 정리: 어디서 막혔는지 알면 바로 풀려요

원인은 크게 세 곳이에요. 레포지토리 비활성화, UTC/KST 혼동, 시크릿 누락. 여기에 Hugo의 날짜 필드 처리가 더해지면 "워크플로는 성공인데 포스트가 없는" 상황이 만들어져요.

Cloudflare Pages는 자체 cron을 지원하지 않으니, 예약 발행이 필요한 Hugo 블로그라면 GitHub Actions 직접 배포 방식은 피할 수 없어요. 5단계 체크리스트를 기준으로 하나씩 짚어나가면 대부분 30분 안에 원인을 찾을 수 있어요.

워크플로 고쳐서 다시 돌렸을 때, 예약 시간에 정확히 포스트가 올라오는 그 순간이 꽤 쾌적해요. 한번 세팅해두면 한동안 신경 안 써도 되니까요. 다만, 60일 비활성화 룰만큼은 꼭 기억해두세요.

---

*참고 자료: Codeslog "Scheduled Publishing with GitHub Actions Every 3 Hours" (2025), Caktus Group "How to Deploy a Hugo Site to Cloudflare Pages With Github Actions" (2025.08), Ben Abt "Scheduled Builds for Cloudflare Deployments with GitHub Actions" (2025.07)*

## 참고자료

1. [Scheduled Publishing with GitHub Actions Every 3 Hours | Codeslog](https://www.codeslog.com/en/posts/github-actions-scheduled-publish-check/)
2. [How to Deploy a Hugo Site to Cloudflare Pages With Github Actions | Caktus Group](https://www.caktusgroup.com/blog/2025/08/20/how-to-deploy-a-hugo-site-to-cloudflare-pages-with-github-actions/)
3. [Scheduled Builds for Cloudflare Deployments with GitHub Actions | BEN ABT](https://benjamin-abt.com/blog/2025/07/14/scheduled-builds-cloudflare-github-actions/)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-white-dice-with-a-black-github-logo-on-it-HLQDfaJUTVI)*
