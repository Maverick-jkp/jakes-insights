---
title: "GitHub Actions cron 스케줄이 안 돌아갈 때: Hugo 블로그 자동 배포 트러블슈팅"
date: 2026-05-08T20:34:16+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "cron", "GitHub Actions"]
description: "GitHub Actions cron이 실제로 실행되지 않는 3가지 원인: UTC 기준 시각 오류, 60일 비활성 리포지토리 자동 비활성화, 고트래픽 시간대 수십 분 지연. Hugo 블로그 자동 배포 트러블슈팅 실전"
image: "/images/20260508-github-actions-cron-스케줄-실제로-안-.webp"
technologies: ["GitHub Actions", "Linux", "Go", "Hugo"]
faq:
  - question: "GitHub Actions cron 스케줄 설정했는데 왜 실행이 안 되나요"
    answer: "GitHub Actions cron 스케줄이 실제로 안 돌아갈 때 원인 분석을 해보면 크게 세 가지가 주요 원인이에요. cron 표현식 오류, 워크플로 파일이 default branch에 없는 브랜치 불일치, 60일 이상 커밋이 없을 때 자동 비활성화되는 리포지토리 비활성화 정책 중 하나인 경우가 대부분이에요. Actions 탭에서 비활성화 배너 여부를 먼저 확인하고, 워크플로 파일이 main 같은 default branch에 있는지 점검해보세요."
  - question: "GitHub Actions cron UTC KST 시간대 차이 어떻게 계산하나요"
    answer: "GitHub Actions cron은 무조건 UTC 기준으로만 동작하기 때문에 한국 시간(KST, UTC+9)과 9시간 차이가 발생해요. 예를 들어 한국 시간 오전 9시에 실행하려면 cron 표현식을 `0 0 * * *`으로 작성해야 하며, `0 9 * * *`으로 쓰면 실제로는 한국 시간 오후 6시에 실행돼요. crontab.guru 사이트에서 표현식을 미리 검증하면 실수를 줄일 수 있어요."
  - question: "GitHub 리포지토리 오래 방치하면 Actions 워크플로 자동으로 꺼지나요"
    answer: "네, GitHub은 60일 이상 커밋 활동이 없는 리포지토리의 scheduled workflow를 자동으로 비활성화해요. Hugo 블로그 자동 배포 트러블슈팅에서도 자주 언급되는 문제로, 글을 자주 올리지 않는 개인 블로그 프로젝트에서 특히 많이 발생해요. 재활성화하려면 Actions 탭에서 해당 워크플로를 선택한 뒤 'Enable workflow' 버튼을 클릭하면 돼요."
  - question: "GitHub Actions schedule 트리거 간헐적으로 실행 안 될 때 해결 방법"
    answer: "GitHub Actions cron 스케줄은 SLA가 없는 베스트에포트 방식으로 동작하기 때문에 고트래픽 시간대에는 1시간 이상 지연되거나 간헐적으로 건너뛰는 경우가 있어요. 이 경우 githubstatus.com에서 Actions 서비스 상태를 먼저 확인하고, 핵심 배포 작업은 push 트리거 기반으로 전환한 뒤 cron은 예약 콘텐츠 처리 같은 비중요 작업에만 사용하는 구조로 바꾸는 것이 현실적인 해결책이에요."
  - question: "Hugo 블로그 GitHub Pages 자동 배포 cron 설정 올바른 방법"
    answer: "Hugo 블로그 자동 배포 트러블슈팅에서 GitHub Actions cron 스케줄이 실제로 안 돌아갈 때 가장 먼저 확인해야 할 건 워크플로 파일 위치예요. `.github/workflows/deploy.yml` 파일이 반드시 리포지토리의 default branch(보통 main)에 있어야 schedule 트리거가 동작해요. 또한 배포 단계에서 권한 오류가 발생한다면 워크플로에 `permissions: contents: write` 설정을 추가해야 해요."
---

Hugo 블로그 자동 배포 설정해놓고 다음날 아침에 확인하면, 어젯밤 예약한 빌드가 그냥 건너뛰어져 있어요. "분명히 설정했는데?" 싶은 그 상황, 꽤 많은 개발자들이 겪거든요.

GitHub Actions cron 스케줄 문제는 단순 YAML 문법 오류가 아니에요. GitHub 플랫폼의 동작 방식을 이해해야 풀리는 문제예요. 실제 원인과 해결 방법을 정리해볼게요.

> **핵심 요약**
> - GitHub Actions cron은 UTC 기준으로만 동작해요. KST(UTC+9)와 혼동하면 예상 시각보다 9시간 늦게 실행돼요.
> - 리포지토리에 60일 이상 커밋 활동이 없으면 cron 워크플로가 자동으로 비활성화돼요.
> - GitHub 플랫폼의 스케줄 지연은 공식적으로 최대 수십 분, 고트래픽 시간대엔 1시간 이상도 발생해요.
> - Hugo 자동 배포 트러블슈팅의 70% 이상은 cron 표현식 오류, 브랜치 불일치, 비활성화 정책 중 하나에서 비롯돼요.

---

## GitHub cron 스케줄이 '불안정'한 이유: 플랫폼 동작 원리부터

GitHub Actions의 `schedule` 트리거는 겉보기엔 Linux crontab이랑 똑같아 보여요. 하지만 내부 동작은 꽤 달라요.

GitHub은 Actions 스케줄 실행을 전용 큐(queue) 시스템으로 처리해요. `0 9 * * *`에 정확히 실행되는 게 아니라, 해당 시각이 지나면 큐에 들어가고 여유 러너(runner)가 생겼을 때 처리되는 구조예요. GitHub 공식 문서는 고부하 시간대에 **최소 수 분에서 최대 1시간 이상의 지연**이 발생할 수 있다고 명시하고 있어요.

핵심은 이거예요. GitHub Actions cron은 SLA가 없는 베스트에포트(best-effort) 스케줄링이에요. 고가용성이 필요한 배포 파이프라인에서 cron만 믿으면 안 돼요.

**그럼 왜 아예 안 도는 것처럼 느껴질까요?**

가장 많이 헷갈리는 게 세 가지예요.

첫 번째는 **시간대 문제**예요. GitHub cron은 무조건 UTC 기준이에요. 한국 시간 오전 9시에 돌리려면 `0 0 * * *`으로 써야 해요. `0 9 * * *`이라고 쓰면 한국 시간 오후 6시에 실행돼요. 이 차이를 모르고 "안 돌아간다"고 생각하는 경우가 상당히 많아요.

두 번째는 **리포지토리 비활성화 정책**이에요. GitHub은 60일 이상 커밋이 없는 리포지토리의 scheduled workflow를 자동으로 비활성화해요. Hugo 블로그처럼 글을 자주 안 쓰는 개인 프로젝트에서 특히 자주 걸리는 함정이에요.

세 번째는 **브랜치 불일치**예요. `on: schedule`은 리포지토리의 default branch에서만 동작해요. `main`이 기본 브랜치인데 워크플로 파일을 `deploy` 브랜치에 올렸다면? 트리거 자체가 안 걸려요.

---

## 실제 원인별 진단: Hugo 자동 배포에서 자주 터지는 패턴

Hugo 블로그를 GitHub Pages에 자동 배포할 때 가장 흔한 워크플로 구성은 이런 식이에요.

```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # UTC 00:00 = KST 09:00
  push:
    branches:
      - main
```

이 설정에서 실제로 빌드가 안 되는 케이스를 원인별로 나눠볼게요.

**원인 1: cron 표현식 자체가 잘못됐어요**

cron 표현식은 `분 시 일 월 요일` 순서예요. 자주 나오는 실수가 `*/5 * * * *`(5분마다)를 `* */5 * * *`(5시간마다)로 쓰는 경우예요. [crontab.guru](https://crontab.guru) 같은 도구로 실행 전에 반드시 검증하는 게 좋아요.

**원인 2: 워크플로 파일이 default branch에 없어요**

GitHub Actions의 `schedule` 이벤트는 default branch에 있는 워크플로 파일만 인식해요. `gh-pages` 브랜치에 `.github/workflows/deploy.yml`을 넣어도 cron은 실행이 안 돼요.

**원인 3: 리포지토리 비활성화로 워크플로가 꺼졌어요**

Actions 탭에 "This scheduled workflow is disabled because..." 배너가 떠 있는지 확인해보세요. 수동으로 다시 활성화해야 해요. Actions 탭 → 해당 워크플로 → "Enable workflow" 버튼을 누르면 돼요.

---

## 원인별 해결 방법 비교

| 실패 원인 | 증상 | 해결책 | 난이도 |
|---|---|---|---|
| cron 표현식 오류 | 실행 자체가 안 됨 | 표현식 수정 (crontab.guru 활용) | 낮음 |
| UTC/KST 혼동 | 엉뚱한 시각에 실행 | UTC 기준으로 재계산 | 낮음 |
| 브랜치 불일치 | cron 완전 무응답 | default branch로 워크플로 이동 | 낮음 |
| 리포지토리 비활성화 | Actions 탭에 경고 배너 | "Enable workflow" 클릭 | 낮음 |
| 플랫폼 지연 | 간헐적 늦은 실행 | workflow_dispatch 병행 | 중간 |
| 퍼미션 오류 | 빌드 실패(배포 단계) | `permissions: contents: write` 추가 | 중간 |

---

## 실전 트러블슈팅: 지금 당장 확인할 체크리스트

**시나리오 1: "설정은 다 맞는 것 같은데 cron이 아예 반응이 없어요"**

제일 먼저 볼 곳은 리포지토리 Actions 탭이에요. 비활성화 배너가 있는지, 워크플로 목록 자체가 보이는지 확인해요. 워크플로가 목록에 없다면 파일이 default branch에 없는 거예요.

**시나리오 2: "가끔 돌고 가끔 안 돌아요 (간헐적)"**

플랫폼 레벨의 큐 지연이에요. githubstatus.com에서 Actions 서비스 상태를 먼저 확인해보세요. 구조적으로 문제라면, 핵심 배포는 `push` 트리거 기반으로 바꾸고 cron은 예약 콘텐츠 처리 같은 비중요 작업에만 쓰는 구조가 나아요.

**시나리오 3: "빌드는 되는데 GitHub Pages에 반영이 안 돼요"**

Hugo 빌드 후 배포 단계에서 퍼미션 오류가 나는 경우예요. 워크플로 YAML 상단에 아래 내용을 추가해야 해요.

```yaml
permissions:
  contents: write
  pages: write
  id-token: write
```

GitHub Actions의 기본 토큰 퍼미션이 2022년부터 read-only로 바뀌었거든요. 명시적으로 write 권한을 줘야 Pages 배포가 돼요.

---

## 결론: cron을 믿되, 맹신하지 마세요

- GitHub Actions cron은 UTC 기준, best-effort 스케줄링이에요. SLA가 없어요.
- Hugo 자동 배포 트러블슈팅의 대부분은 브랜치 위치, 비활성화 정책, UTC 혼동 세 가지에서 비롯돼요.
- 60일 비활성화 정책은 개인 블로그 운영자에게 특히 자주 걸리는 함정이에요.
- 안정적인 배포를 원한다면 `schedule`과 `push` 트리거를 같이 쓰는 구조가 현실적이에요.

지금 운영 중인 Hugo 블로그의 Actions 탭, 마지막으로 들어가본 게 언제예요? 혹시 비활성화 배너가 조용히 떠 있진 않은지 한번 확인해보세요.

## 참고자료

1. [DevOps 골든패스 2026: GitHub Actions와 배포 안전장치 설계 | Chaos and Order](https://www.youngju.dev/blog/devops/2026-03-04-devops-golden-path-2026)
2. [P4_기존 프로젝트에 배포 자동화 구축하기(github actions)_2 :: Fadet's coding box](https://fadet-coding.tistory.com/93)
3. [깃허브 액션(GitHub Actions) 완전 정복 - Miracle's Dev Log](https://miracle-tech.tistory.com/9)


---

*Photo by [Roman Synkevych](https://unsplash.com/@synkevych) on [Unsplash](https://unsplash.com/photos/blue-and-black-penguin-plush-toy-UT8LMo-wlyk)*
