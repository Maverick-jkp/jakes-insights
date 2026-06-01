---
title: "GitHub Actions cron 스케줄 안 돌아갈 때 원인 분석과 해결 방법"
date: 2026-05-21T22:08:20+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "cron", "AWS"]
description: "GitHub Actions cron 스케줄이 조용히 건너뛰어지는 이유, 알고 계셨나요? 부하 집중 시간대엔 최대 60분 이상 지연됩니다. schedule 트리거 내부 동작과 실제 원인 세 가지를 분석합니다."
image: "/images/20260521-github-actions-cron-스케줄-실제로-안-.webp"
technologies: ["AWS", "GitHub Actions", "Go"]
faq:
  - question: "GitHub Actions cron 스케줄 설정했는데 왜 실행이 안 되나요"
    answer: "GitHub Actions cron 스케줄 실제로 안 돌아갈 때 원인 분석 및 해결 방법 정리에 따르면, 가장 흔한 원인은 세 가지입니다. 레포지토리에 60일간 커밋이 없어 자동 비활성화된 경우, 워크플로 파일이 기본 브랜치(main)가 아닌 다른 브랜치에 있는 경우, 또는 cron 표현식을 6개 필드로 잘못 작성한 경우입니다. GitHub Actions 탭에서 워크플로 상태를 먼저 확인하고, 'Enable workflow' 버튼이 보인다면 클릭해서 재활성화하면 대부분 해결됩니다."
  - question: "GitHub Actions schedule 트리거 60분 이상 지연되는 이유"
    answer: "GitHub Actions의 schedule 트리거는 정확한 실시간 스케줄러가 아니라, 지정된 시각 이후에 내부 큐에 워크플로를 넣고 러너 가용성에 따라 실행하는 구조입니다. 특히 UTC 기준 오전 9시~11시에는 전 세계 팀들의 push, PR 이벤트가 동시에 몰려 최대 60분 이상 지연이 발생할 수 있습니다. 정확한 실행 시각이 중요한 작업이라면 외부 스케줄러와 workflow_dispatch를 조합하는 방식을 고려해야 합니다."
  - question: "GitHub Actions cron 60일 비활성화 다시 활성화하는 방법"
    answer: "GitHub는 레포지토리에 60일간 커밋 활동이 없으면 schedule 워크플로를 에러 알림 없이 자동으로 비활성화합니다. 재활성화하려면 GitHub 웹에서 Actions 탭으로 이동해 해당 워크플로를 찾아 'Enable workflow' 버튼을 클릭하거나, 레포지토리에 아무 커밋이나 추가하면 됩니다."
  - question: "GitHub Actions cron 표현식 몇 개 필드 써야 하나요"
    answer: "GitHub Actions는 '분 시간 일 월 요일' 순서의 5개 필드 cron 표현식만 지원합니다. 일부 시스템에서 사용하는 초(seconds)를 포함한 6개 필드 형식은 인식하지 않아 워크플로가 조용히 실행되지 않을 수 있습니다. 또한 schedule 트리거는 무조건 UTC 기준으로 동작하므로, 한국 시간 오전 9시에 실행하려면 UTC 기준인 '0 0 * * *'으로 설정해야 합니다."
  - question: "GitHub Actions cron 스케줄 실제로 안 돌아갈 때 디버깅하는 방법"
    answer: "GitHub Actions cron 스케줄 실제로 안 돌아갈 때 원인 분석 및 해결 방법 정리에서 권장하는 방법은 workflow_dispatch 트리거를 함께 등록하는 것입니다. workflow_dispatch를 추가하면 수동으로 즉시 실행해 워크플로 자체의 동작을 검증할 수 있어, cron 표현식 문제인지 워크플로 로직 문제인지 빠르게 구분할 수 있습니다. 추가로 crontab.guru에서 표현식을 사전 검증하고, YAML 린터로 파일 구조 오류 여부를 확인하는 것도 필수입니다."
---

cron을 설정했는데 워크플로가 안 돌아간다. 로그도 없고, 에러도 없고. 그냥 조용히 넘어가 버린다. 생각보다 많은 팀에서 반복되는 문제예요.

GitHub Actions의 `schedule` 트리거는 겉으로 보기엔 단순해요. `0 9 * * 1`처럼 cron 표현식 하나 넣으면 끝이니까요. 그런데 실제로 배포 환경에서 쓰다 보면 스케줄이 수십 분씩 밀리거나, 아예 건너뛰는 일이 생겨요. devactivity.com의 커뮤니티 분석에 따르면, 부하가 집중되는 시간대엔 GitHub Actions cron 워크플로가 예정 시각보다 **최대 60분 이상** 지연되는 케이스가 꾸준히 보고되고 있어요. 놀랍죠?

이 글에서는 원인을 세 가지 축으로 정리해 드릴게요.

- `schedule` 트리거의 내부 동작 방식과 지연 원인
- 비활성화 메커니즘과 레포지토리 상태 문제
- 실무에서 바로 쓸 수 있는 대안 접근법과 모니터링 전략

---

> **핵심 요약**
> - GitHub Actions의 `schedule` 트리거는 정확한 실시간 스케줄러가 아니며, GitHub 내부 큐 상태에 따라 예정 시각 대비 최대 60분 이상 지연될 수 있다 (devactivity.com, 2025 커뮤니티 데이터 기준).
> - 레포지토리에 **60일간 커밋이 없으면** GitHub이 cron 워크플로를 자동으로 비활성화한다. 이 사실을 모르는 팀이 많다.
> - 기본 브랜치(보통 `main`)가 아닌 브랜치에 워크플로 파일을 두면 `schedule` 트리거가 동작하지 않는다.
> - `workflow_dispatch`를 함께 등록하면 수동 실행 + 디버깅이 동시에 가능해서 실무 운영 비용이 크게 줄어든다.

---

## GitHub의 cron은 "예약"이 아니라 "큐"예요

cron 표현식을 보면 `* * * * *` 형식으로 분 단위까지 지정하잖아요. 자연스럽게 "이 시각에 정확히 돌겠구나"라고 생각하게 돼요. 그런데 GitHub Actions의 `schedule`은 실제로 그렇게 동작하지 않아요.

GitHub 공식 문서를 보면 명확하게 나와 있어요. `schedule` 이벤트는 "지정된 cron 시각 *이후*에 가능한 한 빠르게 실행"되는 구조예요. 즉, 해당 시각에 GitHub 내부 스케줄러가 워크플로를 큐에 넣고, 러너 가용성과 플랫폼 부하에 따라 실행이 시작돼요. 정확한 타이밍 보장은 없어요.

devactivity.com이 커뮤니티 데이터를 분석한 결과, 지연이 주로 발생하는 시간대는 UTC 기준 오전 9시~11시예요. 전 세계 팀들이 업무를 시작하면서 push 이벤트, PR 트리거가 동시에 몰리는 구간이거든요. 이 시간대에 `schedule`을 걸어둔 팀은 거의 필연적으로 지연을 겪어요.

실무에서 cron으로 돌리는 워크플로는 보통 "정시 데이터 수집", "매일 아침 배포", "주간 리포트 생성" 같은 시간에 민감한 작업이 많아요. 30분 늦게 돌아간 리포트는 그날 미팅에서 쓸모가 없고요.

### 비활성화 메커니즘, 모르면 진짜 황당해요

GitHub에는 잘 알려지지 않은 정책이 있어요. 레포지토리에 **60일간 커밋 활동이 없으면** `schedule` 워크플로를 자동으로 비활성화해요. 에러 메시지도 없고, 이메일 알림도 기본값은 꺼져 있어요. 그냥 조용히 멈춰요.

Yeshin Lee가 Medium에 기록한 케이스가 딱 이 경우예요. 수개월간 알림 봇 워크플로가 돌지 않았는데, 원인이 이 자동 비활성화였던 거죠. 코드는 멀쩡하고, 설정도 문제없고, GitHub이 "이 레포 안 쓰나보다"라고 판단해서 꺼버린 거예요.

재활성화 방법은 Actions 탭에서 해당 워크플로를 찾아 "Enable workflow" 버튼을 누르면 돼요. 아니면 레포에 아무 커밋이나 하면 다시 살아나요. 원인을 알면 해결은 30초예요. 문제는 이걸 모른다는 거죠.

---

## 원인별로 뜯어보면 이렇게 나뉘어요

크게 네 가지 카테고리가 나와요.

### 1. 브랜치 위치 문제

`schedule` 트리거는 **기본 브랜치에 있는 워크플로 파일만** 인식해요. `develop` 브랜치에서 테스트하다가 파일을 거기 놔두면? 안 돌아요.

`main` 브랜치에 `.github/workflows/your-workflow.yml`이 있어야 해요. 확인 방법은 간단해요. GitHub 웹에서 레포 루트로 들어가서 `.github/workflows/` 폴더가 보이는지 확인하세요. 안 보인다면 브랜치 문제예요.

### 2. cron 표현식 오류

GitHub Actions는 **5개 필드** cron 표현식만 받아요. `분 시간 일 월 요일` 형식이에요. 일부 시스템에서 쓰는 6개 필드(초 포함) 형식은 지원하지 않아요.

```yaml
# 잘못된 예
- cron: '0 0 9 * * 1'  # 6개 필드 - 동작 안 해요

# 올바른 예
- cron: '0 9 * * 1'    # 5개 필드 - 매주 월요일 9시 UTC
```

타임존도 주의해야 해요. `schedule`은 무조건 UTC 기준이에요. 서울 시간 오전 9시에 돌리려면 UTC 기준 0시(`0 0 * * *`)로 설정해야 해요.

### 3. YAML 문법 오류

인덴트 하나만 틀려도 워크플로 자체가 파싱 실패해요. 에러가 표시될 때도 있지만, 조용히 무시되는 케이스도 있어요. [crontab.guru](https://crontab.guru)로 표현식을 먼저 검증하고, YAML 린터로 파일 구조를 확인하는 습관이 필요해요.

---

## 원인별 해결 방법 비교

| 원인 | 발생 빈도 | 진단 방법 | 해결 방법 | 소요 시간 |
|------|----------|----------|----------|---------|
| 60일 비활성화 | 높음 | Actions 탭 → 워크플로 상태 확인 | "Enable workflow" 클릭 또는 더미 커밋 | 5분 |
| 브랜치 위치 오류 | 중간 | 기본 브랜치에서 파일 위치 확인 | `main`에 파일 이동 후 push | 10분 |
| cron 표현식 오류 | 중간 | crontab.guru에 표현식 붙여넣기 | UTC 기준으로 재작성 | 10분 |
| GitHub 플랫폼 지연 | 높음 | Actions 탭 실행 기록 타임스탬프 비교 | 타이밍에 덜 민감한 시간대로 변경 | 15분 |
| YAML 문법 오류 | 낮음 | PR에서 파일 변경 시 문법 경고 확인 | YAML 린터 적용 | 20분 |

지연 문제는 해결이 아니라 **설계로 우회**하는 게 현실적이에요. devactivity.com 분석에서도 UTC 00:00~06:00 구간이 상대적으로 부하가 적고 지연 발생률이 낮다고 나와요.

---

## 실무에서 바로 쓸 수 있는 접근법

**`workflow_dispatch` 같이 등록하세요.** `schedule`만 쓰면 수동으로 테스트할 방법이 없어요. 아래처럼 두 트리거를 같이 쓰면 버튼 하나로 즉시 실행 + 스케줄 실행을 모두 잡을 수 있어요.

```yaml
on:
  schedule:
    - cron: '0 0 * * *'
  workflow_dispatch:
```

처음 설정할 때 수동으로 한 번 돌려보고 정상 동작을 확인한 뒤 스케줄에 맡기면 돼요. 디버깅 시간이 확 줄어요.

60일 비활성화 대응으로는 더미 커밋을 주기적으로 만드는 방법보다, 팀 캘린더에 "분기마다 비활성 레포 Actions 상태 점검"을 등록하는 게 더 깔끔해요.

**타이밍이 진짜 중요한 작업**이라면 GitHub Actions `schedule` 하나만 믿지 마세요. AWS EventBridge Scheduler나 Google Cloud Scheduler 같은 외부 스케줄러에서 `workflow_dispatch`를 HTTP로 호출하는 구조가 훨씬 안정적이에요. 실행 보장과 타이밍 정밀도가 완전히 달라요.

---

## 정리하면

**`schedule`은 "정확한 시각"이 아니라 "대략 그 시각 이후"라는 개념**으로 쓰는 게 맞아요.

- 60일 비활성화 정책 → Actions 탭에서 주기적으로 확인
- 기본 브랜치 + 올바른 UTC cron → 설정의 기본
- `workflow_dispatch` 병행 등록 → 디버깅과 운영 모두 잡는 방법
- 타이밍 민감 작업 → 외부 스케줄러로 `workflow_dispatch` 호출

GitHub은 Actions의 스케줄 신뢰도를 개선하는 방향으로 인프라를 투자하고 있어요. 공식 로드맵에 스케줄 워크플로 지연 완화가 언급되어 있지만, 정확한 릴리즈 일정은 공개되지 않았어요. 지금 당장은 플랫폼 개선을 기다리기보다 설계 단계에서 지연을 가정하고 만드는 게 더 현실적인 방향이에요.

cron 하나 고치는 데 반나절을 쓴 경험이 있다면, 이번에 설정을 다시 점검해 보세요.

## 참고자료

1. [Troubleshooting GitHub Actions Cron Jobs: Resolving Scheduled Workflow Delays](https://devactivity.com/insights/github-actions-cron-delays-a-community-insight-into-engineering-workflow-scheduling/)
2. [n개월 째 날라오던 Github Actions 버그 고치기. 대부분의 개발은 귀차니즘에서 시작되었다(?) | by Yeshin Lee | Medium](https://yeslee-v.medium.com/n%EA%B0%9C%EC%9B%94-%EC%A7%B8-%EB%82%A0%EB%9D%BC%EC%98%A4%EB%8D%98-github-action-%EB%B2%84%EA%B7%B8-%EA%B3%A0%EC%B9%98%EA%B8%B0-bbee7c1e3bb5)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-white-dice-with-a-black-github-logo-on-it-HLQDfaJUTVI)*
