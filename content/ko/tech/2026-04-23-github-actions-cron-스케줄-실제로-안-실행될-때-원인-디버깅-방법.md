---
title: "GitHub Actions cron 스케줄 실제로 안 실행될 때 원인 디버깅 방법"
date: 2026-04-23T20:30:30+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "github", "actions", "cron", "GitHub Actions"]
description: "GitHub Actions cron 스케줄이 실행되지 않는 원인은 서버 부하 지연, 기본 브랜치 불일치, YAML 문법 오류 등 여러 층에 걸쳐 있습니다. 각 원인별 빠른 진단 방법을 정리했습니다."
image: "/images/20260423-github-actions-cron-스케줄-실제로-안-.webp"
technologies: ["GitHub Actions", "Slack"]
faq:
  - question: "GitHub Actions cron 스케줄 실제로 안 실행될 때 원인 디버깅 방법"
    answer: "GitHub Actions cron 스케줄이 실행되지 않는 주요 원인은 크게 세 가지예요. 워크플로우 파일이 기본 브랜치에 없는 경우, 60일 이상 저장소 비활성화로 GitHub가 자동 비활성화한 경우, 그리고 cron 문법 오류가 조용히 무시되는 경우예요. Actions 탭에서 워크플로우 상태 확인 → 기본 브랜치 확인 → crontab.guru로 문법 검증 순서로 빠르게 원인을 좁힐 수 있어요."
  - question: "GitHub Actions schedule 트리거 기본 브랜치 아닌 곳에 있으면 실행 안 되나요"
    answer: "네, GitHub Actions의 schedule 트리거는 저장소의 기본 브랜치에 있는 워크플로우 파일만 실행해요. develop이나 feature 브랜치에 워크플로우를 만들어두면 문법이 완벽해도 절대 실행되지 않아요. 저장소 Settings → General → Default branch에서 기본 브랜치를 확인하고, 해당 브랜치에 워크플로우 파일이 있는지 점검해야 해요."
  - question: "GitHub Actions cron 60일 비활성화 다시 켜는 방법"
    answer: "GitHub는 공개 저장소에서 60일 이상 활동이 없으면 스케줄 워크플로우를 자동으로 비활성화해요. 재활성화하려면 저장소의 Actions 탭에서 해당 워크플로우를 찾아 'Enable workflow' 버튼을 클릭하면 돼요. 이메일 알림이 오긴 하지만 놓치기 쉬우므로, 주기적으로 관리하지 않는 사이드 프로젝트에서 특히 자주 확인해야 해요."
  - question: "GitHub Actions cron 스케줄 실제로 안 실행될 때 원인 디버깅 방법 중 workflow_dispatch 활용하는 이유"
    answer: "workflow_dispatch를 추가해두면 cron이 실행되지 않을 때 워크플로우 자체가 정상인지 수동으로 즉시 확인할 수 있어요. cron 문제인지 워크플로우 내부 로직 문제인지 빠르게 구분할 수 있어서 디버깅 시간을 크게 줄여줘요. schedule과 workflow_dispatch를 함께 on 트리거에 선언하는 것만으로도 충분하고, 코드 한 줄 추가로 얻는 효과가 커서 실무에서 좋은 습관으로 권장돼요."
  - question: "cron 표현식 GitHub Actions에서 검증하는 방법"
    answer: "GitHub Actions는 잘못된 cron 표현식이 있어도 워크플로우 파일 저장 자체는 허용되고 명확한 에러 메시지도 뜨지 않아서 조용히 실패하는 경우가 많아요. crontab.guru에 표현식을 붙여 넣으면 다음 실행 예정 시간을 즉시 확인할 수 있어서 빠른 검증이 가능해요. 특히 필드가 6개인 표현식이나 2월 30일처럼 존재하지 않는 날짜를 지정한 경우가 흔한 실수 유형이니 주의해야 해요."
---

cron 스케줄을 설정했는데 워크플로우가 조용히 침묵하고 있어요. 로그도 없고, 알림도 없고, 그냥 없어요. GitHub Actions를 쓰는 개발자라면 한 번쯤 겪어봤을 상황이죠.

실제로 GitHub Community 포럼에는 "cron 잡이 의도한 대로 실행되지 않는다"는 논의가 2026년 현재도 꾸준히 올라오고 있어요. 원인은 단순해 보이지만, 파고들면 꽤 여러 층에 걸쳐 있어요. GitHub의 서버 부하 정책, 브랜치 기본값 설정, YAML 문법 오류까지 — 디버깅 포인트가 생각보다 많아요.

이 글에서는 cron 스케줄이 안 실행될 때 원인을 체계적으로 진단하고, 각 원인별로 가장 빠른 해결 경로를 짚어드릴게요.

> **핵심 요약**
> - GitHub는 공개 저장소의 cron 워크플로우를 서버 부하에 따라 지연 또는 건너뛸 수 있으며, 최대 수 시간까지 밀리는 경우가 보고되어 있어요.
> - 기본 브랜치가 아닌 곳에 `schedule` 트리거를 정의하면 실행되지 않아요. 이 사실을 모르는 개발자가 꽤 많더라고요.
> - 60일 이상 활동이 없는 저장소의 스케줄 워크플로우는 GitHub가 자동으로 비활성화해요.
> - cron 문법 오류는 GitHub UI에서 명시적 에러 없이 조용히 무시되는 경우가 많아서, 검증 도구를 별도로 써야 해요.

---

## GitHub cron이 원래 "정시"를 보장하지 않아요

먼저 기대치를 조정할 필요가 있어요.

GitHub Actions의 `schedule` 트리거는 **정확한 실행 시간을 보장하지 않아요.** GitHub 공식 문서에 따르면, 스케줄된 워크플로우는 cron 표현식이 지정한 시간에 실행되는 게 아니라 "해당 시간 이후 가능한 빠른 시점"에 큐에 올라가는 구조예요. 공개 저장소에서 많은 워크플로우가 동시에 실행될 때는 수십 분, 심한 경우 수 시간까지 지연될 수 있어요.

GitHub Community 논의(#190423)에서 실제로 보고된 패턴을 보면, UTC 기준 정각에 맞춰 설정한 cron이 가장 많이 몰리고, 따라서 지연도 가장 심하다는 경향이 있어요. `0 * * * *` 같은 표현보다 `17 * * * *`처럼 정각을 피한 설정이 실질적으로 더 예측 가능하게 작동한다는 게 실무에서 나온 팁이에요.

그럼 지연이 아닌 "아예 안 실행"되는 경우는? 이건 다른 문제예요. 원인을 크게 세 가지로 나눌 수 있어요.

---

## 세 가지 주요 원인

### 원인 1: 브랜치 설정 오류 — 가장 흔한 함정

GitHub Actions의 `schedule` 트리거는 **저장소의 기본 브랜치(default branch)에 있는 워크플로우 파일만 실행해요.** `main` 브랜치가 기본인데 `develop`이나 `feature/cicd-setup` 같은 브랜치에 `.github/workflows/cron.yml`을 만들어두면, 문법이 완벽해도 실행이 안 돼요.

확인 방법은 간단해요. 저장소 Settings → General → Default branch를 보세요. 워크플로우 파일이 그 브랜치에 있어야 해요.

이 문제가 특히 많이 생기는 상황은 두 가지예요:
- CI/CD 파이프라인을 별도 브랜치에서 테스트하다가 머지를 빠뜨린 경우
- 저장소 기본 브랜치를 `master`에서 `main`으로 바꾼 후 워크플로우 파일이 구 브랜치에만 남아 있는 경우

### 원인 2: 60일 비활성화 정책

이걸 모르는 분들이 많아요. GitHub는 공개 저장소에서 **60일 이상 커밋이나 다른 활동이 없으면 스케줄 워크플로우를 자동으로 비활성화해요.** 이메일 알림이 오긴 하지만 놓치기 쉽죠.

재활성화는 Actions 탭에서 해당 워크플로우를 찾아 "Enable workflow" 버튼을 누르면 돼요. 사이드 프로젝트나 주기적으로 관리하지 않는 저장소에서 자주 생기는 문제예요.

### 원인 3: cron 문법 오류 — 조용히 실패해요

GitHub Actions YAML에서 cron 표현식이 잘못돼도 워크플로우 저장 자체는 돼요. 에러 메시지가 명확하게 뜨지 않아서 문법이 맞다고 착각하기 쉬워요.

흔한 실수들:

```yaml
# ❌ 잘못된 예
schedule:
  - cron: '* * * * * *'   # 필드가 6개 (표준은 5개)
  - cron: '0 0 30 2 *'    # 2월 30일 — 존재하지 않는 날짜
  - cron: '*/5'           # 필드 수 부족

# ✅ 올바른 예
schedule:
  - cron: '0 9 * * 1-5'   # 평일 오전 9시 (UTC 기준)
```

검증은 [crontab.guru](https://crontab.guru)에서 바로 할 수 있어요. 표현식을 붙여 넣으면 다음 실행 시간을 즉시 보여줘요.

### 디버깅 방법 비교

| 디버깅 방법 | 확인 가능한 문제 | 소요 시간 | 난이도 |
|------------|----------------|-----------|--------|
| Actions 탭 워크플로우 상태 확인 | 비활성화 여부, 최근 실행 이력 | 1분 이내 | 쉬움 |
| crontab.guru로 문법 검증 | cron 표현식 오류 | 1분 이내 | 쉬움 |
| 기본 브랜치 확인 | 브랜치 설정 오류 | 2분 이내 | 쉬움 |
| `workflow_dispatch` 수동 트리거 | 워크플로우 자체 실행 가능 여부 | 5분 이내 | 보통 |
| Act로 로컬 실행 | 전체 파이프라인 오류 | 30분+ | 어려움 |
| GitHub API로 실행 이력 조회 | 큐 지연 vs 미실행 구분 | 10분 이내 | 보통 |

수동 트리거(`workflow_dispatch`)를 추가해두는 건 정말 좋은 습관이에요. cron이 안 돌 때 워크플로우 자체는 멀쩡한지 바로 확인할 수 있거든요.

```yaml
on:
  schedule:
    - cron: '0 9 * * 1-5'
  workflow_dispatch:  # 이 줄 하나가 디버깅 시간을 크게 줄여줘요
```

---

## 실전 디버깅 순서: 5분 안에 원인 찾기

이 순서로 하면 대부분 5분 안에 잡혀요.

**1단계 (1분):** Actions 탭에서 해당 워크플로우가 활성화 상태인지 확인. "This workflow is disabled" 메시지가 있으면 바로 활성화.

**2단계 (1분):** 워크플로우 파일이 기본 브랜치에 있는지 확인.

**3단계 (1분):** crontab.guru에서 cron 표현식 검증. 다음 실행 예정 시간이 말이 되는지 보세요.

**4단계 (2분):** `workflow_dispatch`가 있으면 수동 실행해보기. 이게 안 되면 cron이 아니라 워크플로우 자체 문제예요.

이 네 단계에서 안 잡히면 GitHub 서버 부하로 인한 지연 가능성이 높아요. [githubstatus.com](https://www.githubstatus.com)에서 Actions 서비스 상태를 확인하는 게 다음 수순이에요.

---

## 앞으로 예방하는 법

문제가 해결된 후에도 같은 상황이 반복되지 않으려면 두 가지만 해두면 돼요.

첫째, **모든 cron 워크플로우에 `workflow_dispatch`를 같이 넣어두기.** 디버깅 편의성이 완전히 달라져요.

둘째, **중요한 스케줄 작업은 Slack이나 PagerDuty 같은 외부 알림과 연결하기.** GitHub Actions 자체의 실패 알림만으로는 "조용히 안 실행"되는 상황을 잡기 어려워요. 워크플로우 마지막 단계에 성공 알림을 넣어두면, 그게 안 오는 것 자체가 신호가 되죠.

cron이 조용히 멈춰있을 때, 가장 먼저 의심할 건 거창한 인프라 문제가 아니라 브랜치 하나, 문법 하나, 60일이라는 숫자예요. 단순한 것부터 확인하는 게 결국 가장 빠른 길이에요.

---

*GitHub Actions cron 디버깅 중에 이 글에서 다루지 않은 다른 패턴을 발견하셨나요? 댓글로 공유해 주시면 다음 업데이트에 반영할게요.*

## 참고자료

1. [로컬에서 Act로 GitHub Actions 실행하는 방법](https://apidog.com/kr/blog/how-to-run-your-github-actions-locally-a-comprehensive-guide-kr/)
2. [github action 간단 사용법 | marinesnow34](https://marinesnow34.github.io/2024/09/15/gitaction/)
3. [Cron jobs not getting triggered as intended. · community · Discussion #190423](https://github.com/orgs/community/discussions/190423)


---

*Photo by [Roman Synkevych](https://unsplash.com/@synkevych) on [Unsplash](https://unsplash.com/photos/blue-and-black-penguin-plush-toy-UT8LMo-wlyk)*
