---
title: "GitHub Actions cron 스케줄 실제로 안 돌아갈 때 원인 분석 및 우회 방법"
date: 2026-04-03T20:07:57+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "cron", "AWS"]
description: "GitHub Actions cron이 제때 안 도는 이유는 UTC 고정, 최대 수십 분 지연, 60일 무커밋 시 자동 비활성화 때문입니다. 구조적 원인과 실무 우회 방법을 분석합니다."
image: "/images/20260403-github-actions-cron-스케줄-실제로-안-.webp"
technologies: ["AWS", "REST API", "GitHub Actions", "Go"]
faq:
  - question: "GitHub Actions cron 스케줄 왜 안 돌아가요"
    answer: "GitHub Actions cron 스케줄이 실제로 안 돌아갈 때 원인 분석 및 우회 방법을 보면 크게 세 가지 원인이 있어요. 리포지토리에 60일 이상 커밋이 없으면 scheduled workflow가 자동으로 비활성화되고, GitHub 인프라 부하로 인해 최대 수십 분 지연이 발생할 수 있으며, cron 표현식을 UTC가 아닌 로컬 시간 기준으로 잘못 설정하는 경우도 많아요. Actions 탭에서 워크플로를 클릭했을 때 비활성화 메시지가 보이면 'Enable workflow' 버튼으로 바로 재활성화할 수 있어요."
  - question: "GitHub Actions cron UTC 한국 시간 변환 방법"
    answer: "GitHub Actions cron은 타임존 설정 옵션이 없고 무조건 UTC 기준으로만 동작해요. 한국 시간(KST)은 UTC+9이므로, 예를 들어 한국 기준 오전 9시에 실행하려면 cron 표현식을 '0 0 * * *'으로 설정해야 해요. 'crontab.guru' 사이트에서 표현식을 미리 검증하면 시간 변환 실수를 쉽게 예방할 수 있어요."
  - question: "GitHub Actions scheduled workflow 60일 비활성화 해제하는 법"
    answer: "기본 브랜치에 60일 이상 커밋이 없으면 GitHub가 scheduled workflow를 자동으로 꺼요. 리포지토리의 Actions 탭에서 해당 워크플로를 클릭했을 때 상단에 'This scheduled workflow is disabled because...' 메시지가 표시되면 이 경우에 해당해요. 'Enable workflow' 버튼 하나로 즉시 재활성화할 수 있어요."
  - question: "GitHub Actions cron 정확한 시간에 실행하는 방법"
    answer: "GitHub Actions cron 스케줄이 실제로 안 돌아갈 때 원인 분석 및 우회 방법 중 가장 신뢰도 높은 방법은 외부 스케줄러로 workflow_dispatch를 트리거하는 방식이에요. AWS EventBridge, Google Cloud Scheduler, 또는 무료로 사용 가능한 cron-job.org 같은 서비스가 지정 시각에 GitHub REST API를 호출하면 초 단위 정확도로 워크플로를 실행할 수 있어요. 워크플로에 'on: workflow_dispatch'를 추가하고 기존 schedule도 백업용으로 함께 유지하는 구성이 실무에서 가장 널리 쓰여요."
  - question: "GitHub Actions cron 지연 줄이는 방법"
    answer: "매 시간 정각(0분)과 30분에는 전 세계 수십만 개 리포지토리의 트리거가 동시에 몰려 GitHub 인프라 부하가 높아져요. '0 9 * * *' 대신 '7 9 * * *'처럼 정각을 살짝 비켜가는 것만으로도 지연을 줄일 수 있으며, GitHub 엔지니어링 팀도 비공식적으로 권장하는 방법이에요. 단, GitHub는 scheduled workflow에 SLA를 제공하지 않으므로 정확한 실행 시각이 중요한 작업이라면 외부 스케줄러를 사용하는 것이 근본적인 해결책이에요."
---

오전 9시에 돌아야 할 배치 작업이 9시 40분에 시작됐어요. 로그를 뒤져봤는데 워크플로 자체는 멀쩡해요. 내 설정 문제인지, GitHub 문제인지조차 모르겠는 상황. GitHub Actions cron을 쓰는 팀이라면 한 번쯤 겪는 일이에요.

이 글은 cron 스케줄이 실제로 왜 제때 안 돌아가는지, 구조적 원인부터 실무 우회 방법까지 정리한 분석이에요.

> **핵심 요약**
> - GitHub Actions cron은 UTC 기준으로만 동작해요. 타임존 설정이 없어서 한국 시간과 최대 9시간 차이가 날 수 있어요.
> - GitHub 공식 문서는 "cron 스케줄은 부하 상태에 따라 최대 수 분에서 수십 분 지연될 수 있다"고 명시해요.
> - 리포지토리 기본 브랜치에 60일 이상 커밋이 없으면 scheduled workflow가 자동으로 꺼져요.
> - 실무에서 가장 신뢰할 수 있는 우회책은 외부 스케줄러로 `workflow_dispatch`를 트리거하는 방식이에요.

---

## GitHub cron의 구조적 한계

GitHub Actions가 cron 스케줄을 도입했을 때는 간단한 보조 자동화 도구 수준이었어요. 매일 새벽 캐시를 지우거나, 주 1회 리포트를 돌리는 정도. 그런데 지금은 많은 팀이 이걸 프로덕션 배치 작업의 핵심 트리거로 써요. 데이터 파이프라인, 알림 발송, 외부 API 동기화까지요.

문제는 GitHub가 이 기능을 "best-effort" 방식으로 설계했다는 거예요. 공식 문서에 이렇게 적혀 있어요. "scheduled workflows는 높은 부하 상태에서 지연되거나 누락될 수 있으며, GitHub은 SLA를 제공하지 않는다"고요.

Hacker News에서 GitHub 가동률을 추적한 스레드(2025년 기준)를 보면, GitHub Actions 실행 인프라는 전체 플랫폼 중 간헐적 지연이 가장 많이 보고되는 컴포넌트 중 하나예요. 특히 매 시간 정각(`0 * * * *` 같은 패턴)에 전 세계 수십만 개 리포지토리가 동시에 트리거되는 게 주원인으로 꼽혀요.

타임존 문제도 있어요. GitHub Actions cron은 무조건 UTC 기준이에요. 별도 timezone 설정 옵션이 없고요. 한국 기준 오전 9시에 돌리려면 `0 0 * * *`으로 설정해야 하는데, 모르고 `0 9 * * *`으로 썼다가 오후 6시에 돌아가는 걸 발견하는 팀이 여전히 많아요.

---

## 실제 원인 3가지

### 원인 1: 비활성 리포지토리의 자동 비활성화

60일간 기본 브랜치에 커밋이 없으면 GitHub가 scheduled workflow를 자동으로 꺼요. 공식 문서에 명시된 정책이에요. 내부 도구나 개인 프로젝트에서 자주 생기는 문제예요. YAML도 맞고 설정도 정상인데 어느 날부터 안 돌아간다면 이걸 먼저 의심하세요.

확인 방법은 간단해요. 리포지토리 → Actions 탭 → 해당 워크플로 클릭. 상단에 "This scheduled workflow is disabled because..." 메시지가 있으면 바로 이 케이스예요. "Enable workflow" 버튼 하나로 재활성화돼요.

### 원인 2: cron 표현식 해석 오류

GitHub Actions cron 문법은 표준 Unix cron과 거의 같지만 미묘한 차이가 있어요.

| 필드 | 범위 | 주의점 |
|------|------|--------|
| 분 | 0–59 | 없음 |
| 시 | 0–23 | UTC 기준 |
| 일 | 1–31 | 월과 함께 설정 시 OR 조건 |
| 월 | 1–12 | `JAN-DEC` 문자 지원 안 함 |
| 요일 | 0–6 (일=0) | 일부 cron 도구와 0/7 차이 있음 |

실수가 잦은 패턴은 `0 9 * * 1-5`예요. "UTC 기준 매 평일 오전 9시"인데, 한국 시간으로는 오후 6시죠. `crontab.guru`에서 표현식을 미리 검증하는 습관이 가장 빠른 예방법이에요.

### 원인 3: GitHub 인프라 부하

이건 사용자가 컨트롤할 수 없는 영역이에요. 매 시간 정각과 30분에 트리거가 몰리기 때문에, 이 시각만 피해도 지연이 줄어요. `0 9 * * *` 대신 `7 9 * * *`처럼 정각을 살짝 비켜가는 방식이에요. GitHub 엔지니어링 팀도 비공식적으로 권장한 방법이에요.

---

## 우회 방법 비교

| 방법 | 정확도 | 설정 복잡도 | 비용 | 적합한 상황 |
|------|--------|------------|------|------------|
| GitHub cron 직접 사용 | 낮음 (±30분) | 쉬움 | 무료 | 타이밍 덜 중요한 작업 |
| 외부 스케줄러 → `workflow_dispatch` | 높음 (±초 단위) | 중간 | 유료/무료 혼재 | 정확한 시각 필요한 배치 |
| 자체 서버 cron → GitHub API 호출 | 매우 높음 | 어려움 | 서버 비용 | 미션 크리티컬 작업 |

실무에서 가장 널리 쓰이는 건 **외부 스케줄러 + `workflow_dispatch` 조합**이에요.

작동 방식은 이래요. AWS EventBridge, Google Cloud Scheduler, 혹은 무료 플랜이 있는 `cron-job.org` 같은 서비스가 지정 시각에 GitHub REST API를 호출해요. 엔드포인트는 `POST /repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches`고요. 워크플로에는 `on: workflow_dispatch`를 추가해두면 돼요.

```yaml
on:
  schedule:
    - cron: '7 0 * * *'   # 백업용으로 유지
  workflow_dispatch:        # 외부 트리거 수신
    inputs:
      triggered_by:
        description: 'Trigger source'
        required: false
        default: 'manual'
```

이렇게 `schedule`과 `workflow_dispatch`를 같이 두면, 외부 스케줄러가 정각에 정확히 트리거하고 GitHub cron이 백업으로 남아있는 구조예요.

---

## 상황별 권장 방안

**타이밍이 비즈니스 로직에 직결될 때** (오전 8시 정확히 리포트 발송, 장 시작 전 데이터 준비 등):
외부 스케줄러가 맞아요. AWS EventBridge는 월 100만 건까지 무료고, `cron-job.org`는 소규모 팀에게 충분한 무료 플랜이 있어요. GitHub API 토큰으로 `workflow_dispatch`를 트리거하면 거의 초 단위로 정확해요.

**타이밍이 느슨해도 되는 작업** (야간 캐시 갱신, 주간 의존성 업데이트 등):
GitHub cron을 그냥 써도 돼요. 다만 정각은 피하고, 60일 비활성 정책은 기억해두세요. "마지막 실행 시각" 모니터링만 붙여놔도 누락을 빠르게 잡을 수 있어요.

**지금 당장 확인할 것들:**
- cron으로 돌리는 워크플로 중 마지막 실행이 3일 이상 된 게 있는지
- 해당 리포지토리 기본 브랜치 커밋이 60일을 넘겼는지
- UTC ↔ KST 변환이 맞게 설정됐는지 `crontab.guru`로 재검증

---

## GitHub cron을 믿되, 맹신하지 마세요

한 줄로 정리하면 이거예요. **GitHub cron은 편리하지만 SLA가 없는 best-effort 시스템이에요.**

핵심만 다시 짚으면:
- 60일 비활성 시 자동 비활성화 → 주기적 모니터링 필수
- UTC 기반 타임존 → 반드시 사전 검증
- 정각 트리거 혼잡 → 7분, 13분처럼 엇박자 설정
- 정확한 타이밍 필요 → 외부 스케줄러 + `workflow_dispatch` 조합

앞으로 GitHub이 cron에 타임존 설정이나 실행 보장 옵션을 추가할 가능성도 있어요. 이미 GitHub Issues에 관련 피처 리퀘스트가 수백 개 올라와 있거든요. 유료 플랜 기능으로 "정시 실행 보장"이 생긴다면 꽤 많은 팀이 쓸 것 같아요.

지금 팀의 scheduled workflow 목록을 열어보세요. 마지막 실행이 언제였나요?

## 참고자료

1. [로컬에서 Act로 GitHub Actions 실행하는 방법](https://apidog.com/kr/blog/how-to-run-your-github-actions-locally-a-comprehensive-guide-kr/)
2. [2. Github Action (With Syntax) - Somaz의 IT 공부 일지 - 티스토리](https://somaz.tistory.com/233)
3. [GitHub's Historic Uptime | Hacker News](https://news.ycombinator.com/item?id=47591928)


---

*Photo by [Ferenc Almasi](https://unsplash.com/@flowforfrank) on [Unsplash](https://unsplash.com/photos/a-computer-screen-with-a-bunch-of-buttons-on-it--FHIdRVGets)*
