---
title: "GitHub Actions cron 스케줄 안 돌아갈 때 원인 분석 및 대안"
date: 2026-04-28T21:07:33+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "github", "actions", "cron", "GitHub Actions"]
description: "GitHub Actions cron이 설정 시각보다 2시간 늦게 실행되거나 아예 skip되는 이유, best-effort 정책과 레포 비활성화 자동 중단 원인, 그리고 현실적인 대안 3가지를 진단 방법과 함께 정리했습니다."
image: "/images/20260428-github-actions-cron-스케줄-실제로-안-.webp"
technologies: ["GitHub Actions", "Cloudflare", "Supabase"]
faq:
  - question: "GitHub Actions cron 스케줄 설정했는데 왜 안 돌아가나요"
    answer: "GitHub Actions cron 스케줄이 실제로 안 돌아갈 때 원인은 크게 세 가지입니다. 첫째, GitHub Actions cron은 UTC 기준이라 KST 9시 실행을 원하면 '0 0 * * *'으로 설정해야 합니다. 둘째, 레포에 60일간 커밋이 없으면 GitHub이 예약 워크플로우를 자동으로 비활성화하며, Actions 탭에서 노란 배너로 확인할 수 있습니다. 셋째, cron 워크플로우 파일이 기본 브랜치가 아닌 다른 브랜치에만 있으면 스케줄러가 등록 자체를 하지 않습니다."
  - question: "GitHub Actions cron 30분 이상 지연되는 이유"
    answer: "GitHub Actions cron은 공식적으로 SLA(서비스 수준 보장)가 없는 'best-effort' 방식이라 고부하 시 수십 분에서 최대 1-2시간까지 지연될 수 있습니다. 매 시간 정각(0 * * * *)처럼 정시 패턴을 쓰는 레포가 수십만 개라 해당 시간대에 큐가 몰리는 구조적 문제가 원인입니다. '0 1 * * *' 대신 '7 1 * * *'처럼 홀수 분으로 설정하면 큐 경합이 줄어 지연을 어느 정도 완화할 수 있습니다."
  - question: "GitHub Actions 60일 비활성화 워크플로우 다시 활성화 방법"
    answer: "레포 Actions 탭에서 해당 워크플로우를 클릭하면 상단에 'This scheduled workflow is disabled because...' 노란 배너가 표시되고, 'Enable workflow' 버튼을 누르면 즉시 재활성화됩니다. 이 비활성화 정책은 60일간 커밋 활동이 없을 때 자동으로 적용되며, Supabase 프리 티어처럼 주기적 ping이 필요한 서비스에서 특히 문제가 됩니다. Cron-job.org로 7일마다 repository_dispatch 이벤트를 보내면 비용 없이 이 정책을 우회할 수 있습니다."
  - question: "GitHub Actions cron 대신 쓸 수 있는 정확한 스케줄러"
    answer: "GitHub Actions cron 스케줄이 실제로 안 돌아갈 때 가장 현실적인 대안은 Cron-job.org에서 GitHub API로 HTTP POST를 보내 repository_dispatch 이벤트로 워크플로우를 트리거하는 방식입니다. 초 단위 정확도가 필요하다면 Cloudflare Workers cron을 사용하면 되며, 무료 티어가 하루 10만 요청이라 일반적인 cron 용도로 충분합니다. 두 방식 모두 GitHub 큐 지연에서 완전히 자유롭지만, GitHub PAT 관리와 외부 서비스 의존성이 추가된다는 트레이드오프가 있습니다."
  - question: "Supabase 프리 티어 자동 paused 방지하는 방법"
    answer: "Supabase 프리 티어는 일정 기간 활동이 없으면 프로젝트가 paused 상태가 되는데, GitHub Actions cron으로 주기적 ping을 설정해도 60일 비활성화 정책 때문에 워크플로우 자체가 멈출 수 있습니다. Cron-job.org 무료 플랜에서 7일마다 repository_dispatch 이벤트를 트리거하도록 설정하면 GitHub의 비활성화 정책과 Supabase paused 문제를 동시에 해결할 수 있습니다. 이 방식은 외부 서비스 의존성이 생기지만 비용이 들지 않아 개인 프로젝트에 적합합니다."
---

`schedule: cron: '0 9 * * *'` 설정해놨는데 9시가 아니라 11시에 돌거나, 아예 안 돌아가는 경우 있죠? 로그엔 에러도 없고, 워크플로우는 멀쩡해 보이는데 타이밍만 엉망인 그 상황이요.

GitHub Actions cron은 구조적으로 "best-effort" 방식이에요. SLA(서비스 수준 보장)가 없어요. 공식 문서도 "고부하 시 지연될 수 있다"고 명시하고 있고요. 그런데 이게 생각보다 훨씬 크게 체감돼요.

**핵심 포인트 미리 보기**:
- GitHub 공식 문서가 인정한 cron 지연 문제
- 레포 비활성화 정책으로 인한 워크플로우 자동 비활성화
- 현실적인 대안 세 가지와 각각의 트레이드오프
- 지금 당장 쓸 수 있는 진단 방법

---

> **핵심 요약**
> - GitHub Actions cron은 "고부하 시 최대 수십 분 지연될 수 있다"고 공식 명시되어 있고, SLA가 없어요.
> - 60일간 커밋 활동이 없으면 GitHub이 예약 워크플로우를 자동 비활성화해요.
> - 기본 브랜치에 워크플로우 파일이 없으면 cron 스케줄 자체가 등록되지 않아요.
> - 외부 크론 트리거(Cron-job.org, Cloudflare Workers)로 이 제약을 우회할 수 있어요.
> - Supabase 프리 티어처럼 주기적 ping이 필요한 서비스는 GitHub Actions cron 지연에 특히 취약해요.

---

## cron 스케줄의 구조적 한계

GitHub Community 포럼의 2024-2025년 스레드들을 보면, 정시(`:00`) cron의 평균 지연은 15-30분, 최악의 경우 1-2시간이 넘는다는 보고가 반복돼요. 매 시간 정각(`0 * * * *`)이나 매 15분(`*/15 * * * *`) 같은 패턴을 쓰는 레포가 수십만 개라서, 그 시간대에 큐가 폭발적으로 늘어나는 거예요.

실제로 `7 * * * *`처럼 홀수 분으로 설정한 사람들은 지연이 훨씬 적다고 해요. GitHub 공식 문서도 "cron 표현을 무작위화하라"고 권장하지만, 그렇게 하는 팀은 많지 않아요.

구조적인 문제는 두 가지예요.

**첫째**, 60일간 커밋이 없으면 예약 워크플로우가 자동 비활성화돼요. Supabase 프리 티어처럼 주기적으로 ping을 보내야 활성 상태를 유지하는 서비스에서 치명적이죠. LevelUp GitConnected의 분석에 따르면 이 정책 때문에 Supabase 프로젝트가 예기치 않게 paused 상태가 된 케이스가 실제로 다수 보고됐어요.

**둘째**, cron 워크플로우는 반드시 기본 브랜치에 정의돼 있어야 등록돼요. feature 브랜치에 아무리 완벽한 `schedule` 블록을 써놔도 GitHub 스케줄러는 그걸 무시해요.

---

## 안 돌아가는 이유 세 가지

### 1. 시간대 문제 + 큐 지연

GitHub Actions cron은 **UTC 기준**이에요. KST 오전 9시에 실행하려면 `0 0 * * *`으로 설정해야 해요. `0 9 * * *`로 쓰면 KST 오후 6시에 돌아요. 이걸 모르고 쓰는 경우가 생각보다 많아요.

### 2. 레포 비활성화 자동 정책

60일 무활동 = 예약 워크플로우 자동 정지예요. GitHub이 이메일로 알려주긴 하는데, 자동화 목적으로 만든 계정이라 확인을 못 하는 경우가 생겨요.

확인은 간단해요. 레포 → Actions 탭 → 해당 워크플로우 클릭 → 상단 노란 배너에 "This scheduled workflow is disabled because..."가 뜨면 "Enable workflow" 버튼 한 번 누르면 돼요.

### 3. 브랜치 문제

기본 브랜치 이름이 `main`인데 파일이 `master` 브랜치에만 있다면? 등록 안 돼요. 레포 설정 → Default branch에서 꼭 확인해야 해요.

---

## 대안 비교

| 방식 | 신뢰도 | 설정 난이도 | 비용 | 적합한 상황 |
|------|--------|------------|------|------------|
| GitHub Actions 기본 cron | 낮음 | 아주 쉬움 | 무료 | 정확한 타이밍 불필요할 때 |
| Cron-job.org → `repository_dispatch` | 높음 | 보통 | 무료 플랜 있음 | 외부 의존 괜찮을 때 |
| Cloudflare Workers cron | 매우 높음 | 조금 복잡 | 무료 티어 충분 | 초 단위 정확도 필요할 때 |
| 자체 호스팅 러너 + systemd/cron | 매우 높음 | 복잡 | 서버 비용 발생 | 엔터프라이즈, 온프레미스 |

**Cron-job.org + `repository_dispatch`** 조합이 가장 현실적이에요. Cron-job.org에서 원하는 시간에 GitHub API로 HTTP POST를 보내면, `repository_dispatch` 이벤트로 워크플로우가 실행돼요. GitHub 큐 지연에서 완전히 자유로워지고요.

**Cloudflare Workers**는 코드 몇 줄로 cron 트리거를 설정하면 Cloudflare 글로벌 인프라가 정확하게 실행해줘요. 무료 티어가 하루 10만 요청이라 일반적인 cron에는 충분하고도 남아요.

단, 외부 트리거 방식은 GitHub PAT 관리가 추가로 필요하고 외부 서비스 의존성이 생겨요. 항상 정답은 아니에요.

---

## 지금 당장 쓸 수 있는 방법

**Supabase처럼 살아있음을 증명해야 하는 서비스**: Cron-job.org 무료 플랜으로 7일마다 `repository_dispatch` ping을 보내세요. 비용 0원에 60일 비활성화 정책도 우회돼요.

**CI 배포처럼 타이밍이 어느 정도 중요한 경우**: cron 표현을 홀수 분으로 바꾸세요. `0 1 * * *` 대신 `7 1 * * *`처럼요. 큐 경합이 확 줄어요. 워크플로우 시작에 `date` 명령어로 실제 실행 시간을 로그에 찍어두면 모니터링하기도 좋고요.

**금융, 알림, 데이터 파이프라인처럼 정확한 타이밍이 필수인 경우**: Cloudflare Workers나 자체 호스팅 러너로 가야 해요. GitHub cron을 메인 트리거로 쓰는 건 이 상황엔 맞지 않아요.

---

## 마무리

- GitHub Actions cron은 **SLA 없는 best-effort 스케줄러**예요. 정확한 타이밍이 필요하면 다른 방법을 써야 해요.
- **60일 비활성화 정책**은 실제로 많은 자동화를 조용히 죽이고 있어요. 지금 운영 중인 cron 워크플로우 목록을 한 번 점검해볼 가치가 있어요.
- **외부 트리거 방식**은 무료로 신뢰도를 크게 올릴 수 있는 현실적인 선택지예요.

GitHub이 스케줄러 인프라를 개선할 가능성은 있지만, 공식 로드맵에는 없어요. 지금 운영 중인 cron 워크플로우가 몇 개인지, 마지막으로 확인한 게 언제인지 기억하시나요?

## 참고자료

1. [Supabase Free Tier Will Pause Your App. Here’s the GitHub Actions Fix.](https://levelup.gitconnected.com/supabase-free-tier-will-pause-your-app-heres-the-github-actions-fix-8c1fd35b49ca?gi=635926fc9413)
2. [로컬에서 Act로 GitHub Actions 실행하는 방법](https://apidog.com/kr/blog/how-to-run-your-github-actions-locally-a-comprehensive-guide-kr/)
3. [[Feature]: Action Recorder → Cron Scheduler (hermes record) · Issue #4439 · NousResearch/hermes-agen](https://github.com/NousResearch/hermes-agent/issues/4439)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-white-dice-with-a-black-github-logo-on-it-HLQDfaJUTVI)*
