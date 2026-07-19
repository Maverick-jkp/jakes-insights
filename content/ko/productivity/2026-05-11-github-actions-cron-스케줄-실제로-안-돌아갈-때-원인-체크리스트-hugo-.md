---
title: "GitHub Actions cron 스케줄 안 돌아갈 때 원인 체크리스트 Hugo 블로그 대응법"
date: 2026-05-11T21:59:07+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "cron", "GitHub Actions"]
description: "Hugo 블로그 GitHub Actions cron 스케줄이 조용히 멈췄다면, GitHub 인프라 지연·워크플로우 문법 오류·비활성 저장소 정책 등 실제 원인별 체크리스트를 확인하세요."
image: "/images/20260511-github-actions-cron-스케줄-실제로-안-.webp"
technologies: ["GitHub Actions", "Go", "Hugo"]
faq:
  - question: "GitHub Actions cron 스케줄이 실행이 안 될 때 가장 먼저 확인할 것"
    answer: "GitHub Actions cron 스케줄 실제로 안 돌아갈 때 원인 체크리스트에서 가장 먼저 확인해야 할 것은 워크플로우 파일이 저장소의 기본 브랜치(main 또는 master)에 있는지 여부입니다. GitHub Actions의 cron 트리거는 기본 브랜치에 위치한 워크플로우 파일만 인식하기 때문에, develop이나 gh-pages 같은 다른 브랜치에 파일이 있으면 cron이 아예 실행되지 않습니다."
  - question: "Hugo 블로그 GitHub Actions cron 60일 지나면 자동으로 꺼지는 이유"
    answer: "GitHub 공식 문서에 따르면 60일 이상 커밋 활동이 없는 저장소의 cron 워크플로우는 자동으로 비활성화됩니다. Hugo 블로그처럼 콘텐츠 업데이트가 뜸한 저장소에서 자주 발생하는 문제로, Actions 탭에서 'Enable workflow' 버튼을 클릭해 수동으로 다시 활성화할 수 있습니다."
  - question: "GitHub Actions cron UTC KST 시간대 차이 계산 방법"
    answer: "GitHub Actions의 cron 스케줄은 UTC 기준으로 실행되며, 한국 시간(KST)과는 9시간 차이가 납니다. 예를 들어 cron 표현식에 '0 9 * * *'라고 쓰면 UTC 오전 9시, 즉 KST 오후 6시에 실행되므로 한국 시간 기준으로 원하는 시각에서 9시간을 빼서 입력해야 합니다."
  - question: "GitHub Actions cron 정각 0 0 * * * 설정하면 왜 늦게 실행되나요"
    answer: "GitHub Actions cron 스케줄 실제로 안 돌아갈 때 원인 체크리스트 중 하나가 바로 고부하 시간대 설정입니다. '0 0 * * *'처럼 정각에 맞추면 전 세계 수많은 워크플로우가 동시에 실행 요청을 보내 대기 시간이 수십 분에서 수 시간까지 길어질 수 있습니다. '17 3 * * *'처럼 엇박자 시간으로 설정하면 지연을 줄이는 데 도움이 됩니다."
  - question: "GitHub Actions cron 디버깅할 때 workflow_dispatch 같이 쓰는 이유"
    answer: "workflow_dispatch 트리거를 cron과 함께 설정하면 예약 실행 외에도 GitHub UI에서 언제든 수동으로 워크플로우를 직접 실행할 수 있습니다. cron이 돌지 않는 상황에서 설정 문제인지 인프라 문제인지 빠르게 구분할 수 있어 디버깅이 훨씬 수월해집니다."
aliases:
  - "/tech/2026-05-11-github-actions-cron-스케줄-실제로-안-돌아갈-때-원인-체크리스트-hugo-/"

---

## 1. 어떤 상황인지부터 짚어볼게요

Hugo 블로그를 GitHub Actions로 자동 배포하도록 설정해 뒀는데, 어느 날 확인해보니 cron 스케줄이 안 돌아간 거예요. 로그도 없고, 에러도 없고. 그냥 조용히 실패한 상태.

단순한 설정 실수처럼 보이지만, 실제로는 GitHub Actions 자체의 인프라 이슈이거나 워크플로우 파일의 미묘한 문법 문제일 가능성이 높아요. GitHub Actions는 전 세계 수백만 개의 CI/CD 파이프라인을 돌리고 있고, cron 스케줄 지연 및 누락 문제는 GitHub Status 페이지에 반복적으로 등장하는 알려진 이슈예요.

Hacker News의 "Incident with Actions – Resolved" 스레드를 보면, cron 기반 워크플로우가 수 시간씩 지연되거나 아예 실행되지 않는 사례가 꾸준히 보고돼 왔어요. Hugo 블로그처럼 정기 빌드가 핵심인 프로젝트에서는 이게 치명적일 수 있죠.

이 글에서 다룰 내용은 이래요:

- cron 스케줄이 실제로 안 돌아가는 핵심 원인들
- Hugo 배포 워크플로우에서 자주 발생하는 설정 함정
- 원인별 체크리스트와 빠른 진단 방법
- 대안 트리거 전략과 상황별 선택 기준

---

> **핵심 요약**
> - GitHub Actions cron은 UTC 기준으로 실행되며, 한국 시간(KST)과 9시간 차이가 나서 의도한 시각과 어긋나는 경우가 잦다.
> - 기본 브랜치(`main` 또는 `master`)가 아닌 곳에 워크플로우를 배치하면 cron이 아예 실행되지 않는다.
> - GitHub 공식 문서에 따르면, 비활성 상태(60일 이상 푸시 없음)인 저장소의 cron 워크플로우는 자동으로 비활성화된다.
> - GitHub Actions 인프라 지연으로 인해 cron 실행이 수십 분에서 수 시간 늦어지는 사례가 실제로 보고되어 있다.
> - `workflow_dispatch` 트리거를 병행하면 수동 재실행과 디버깅이 훨씬 쉬워진다.

---

## 2. 이 문제가 반복되는 이유

GitHub Actions의 cron 스케줄러는 Quartz Scheduler 같은 전용 cron 엔진이 아니에요. GitHub의 공유 인프라 위에서 실행되는 작업 큐인 셈이라, 플랫폼 부하 상태에 따라 지연이 발생해요.

GitHub Status 페이지에는 Actions 관련 인시던트가 간헐적으로 기록돼 있어요. Hacker News 스레드에서도 개발자들이 "cron이 수 시간 늦게 돌았다", "특정 날 아예 실행 안 됐다"는 경험을 공유한 적 있죠.

Hugo 블로그의 경우, 보통 이런 워크플로우를 써요:

```yaml
on:
  schedule:
    - cron: '0 9 * * 1'  # 매주 월요일 오전 9시
  push:
    branches:
      - main
```

문제는 `0 9 * * 1`이 UTC 기준이라는 거예요. KST로는 오후 6시예요. 한국 시간 기준으로 짜면 안 되는 이유가 바로 이거예요.

Yeshin Lee의 Medium 글에서도 비슷한 경험이 담겨 있어요. 수개월간 Actions가 의도한 대로 안 돌아간 원인을 추적해 보니, 인프라 이슈라고 생각했는데 알고 보니 본인 설정 문제였던 거죠. 많은 개발자들이 겪는 전형적인 함정이에요.

---

## 3. 원인별 체크리스트

### 원인 1: 브랜치 문제 — cron은 기본 브랜치에서만 돌아요

GitHub Actions의 cron 트리거는 **저장소의 기본 브랜치**에 있는 워크플로우 파일만 인식해요. 워크플로우를 `develop`이나 `gh-pages` 브랜치에 커밋해 뒀다면, cron이 아예 실행 안 되는 게 정상이에요.

체크 방법:
- GitHub 저장소 → Settings → General → Default branch 확인
- `.github/workflows/` 폴더가 **기본 브랜치**에 있는지 확인

Hugo 프로젝트에서는 소스 코드가 `main`, 빌드 결과물이 `gh-pages`에 올라가는 구조가 흔해요. 이때 워크플로우 파일은 반드시 `main` 브랜치에 있어야 해요.

---

### 원인 2: 비활성 저장소 자동 비활성화

GitHub 공식 문서에 따르면, **60일 이상 커밋 활동이 없는 저장소**의 cron 워크플로우는 자동으로 꺼져요. Hugo 블로그처럼 콘텐츠 업데이트가 뜸한 저장소에서 자주 발생하는 케이스예요.

비활성화된 워크플로우는 GitHub Actions 탭에서 확인할 수 있어요. "This scheduled workflow is disabled because there has been no activity in this repository" 메시지가 보이면 수동으로 다시 활성화해야 해요.

다시 켜는 방법: Actions 탭 → 해당 워크플로우 선택 → "Enable workflow" 클릭.

---

### 원인 3: cron 문법은 맞지만 시간대가 틀렸어요

| 실수 유형 | 예시 | 의도한 실행 | 실제 실행 |
|-----------|------|------------|-----------|
| KST를 UTC로 착각 | `0 9 * * *` | KST 오전 9시 | KST 오후 6시 |
| 분/시 순서 반전 | `9 0 * * *` | 오전 9시 | 오전 0시 9분 |
| 윤일/월말 미고려 | `0 9 31 * *` | 매월 31일 | 31일 없는 달 스킵 |
| 고부하 시간대 | `0 0 * * *` | 자정 정각 | 수십 분 지연 가능 |

특히 `0 0 * * *`처럼 정각에 맞추면, 전 세계 수많은 워크플로우가 동시에 실행되기 때문에 대기 시간이 길어요. `17 3 * * *`처럼 살짝 엇박자로 설정하면 지연이 줄어드는 경우가 많아요.

---

### 원인 4: GitHub Actions 인프라 자체 지연

이건 내 코드 문제가 아니에요. GitHub 쪽 문제예요.

Hacker News의 Actions 인시던트 스레드를 보면, cron 스케줄이 수 시간 지연되거나 완전히 스킵된 사례가 문서화돼 있어요. 진단 방법은 단순해요: [githubstatus.com](https://www.githubstatus.com)에서 Actions 항목을 확인하면 돼요.

이런 상황에 대비해 `workflow_dispatch` 트리거를 함께 걸어두면, 인프라 이슈가 있어도 수동으로 즉시 실행할 수 있어요.

```yaml
on:
  schedule:
    - cron: '17 3 * * 1'
  workflow_dispatch:  # 수동 실행 가능하게
  push:
    branches:
      - main
```

Andrew Connell의 Hugo CI/CD 가이드에서도 이 세 트리거를 함께 쓰는 방식을 추천해요. 실무에서 검증된 패턴이에요.

---

### 트리거 전략 비교

| 기준 | cron 단독 | cron + push | cron + push + dispatch |
|------|-----------|-------------|------------------------|
| 정기 빌드 | ✅ | ✅ | ✅ |
| 즉시 재실행 | ❌ | 부분적 | ✅ |
| 디버깅 편의성 | 낮음 | 보통 | 높음 |
| 인프라 지연 대응 | ❌ | ❌ | ✅ |
| 설정 복잡도 | 낮음 | 낮음 | 보통 |

세 트리거를 함께 쓰는 게 Hugo 블로그 배포에는 가장 현실적인 선택이에요.

---

## 4. 실전 진단: 이 순서대로 확인해보세요

**시나리오 1: 처음 설정했는데 cron이 한 번도 안 돌았어요.**

워크플로우 파일이 기본 브랜치에 있는지 먼저 확인하세요. `main`이 기본 브랜치인데 `master`에 파일이 있다면 cron은 영원히 침묵해요. GitHub Actions 탭에 해당 워크플로우가 보이지 않는다면, 파일 위치를 의심하세요.

**시나리오 2: 한동안 잘 됐는데 갑자기 안 돌아요.**

60일 비활성화 정책에 해당할 가능성이 높아요. Actions 탭에서 워크플로우 상태 메시지를 확인하고, "Enable workflow"로 다시 켜면 돼요. 이후에는 빈 커밋(`git commit --allow-empty`)으로 저장소 활동을 주기적으로 유지하는 게 좋아요.

**시나리오 3: 돌긴 도는데 시간이 맞지 않아요.**

cron 문법을 UTC 기준으로 다시 계산해보세요. `crontab.guru`에 붙여넣으면 바로 확인할 수 있어요. KST 기준 원하는 시각에서 9시간을 빼면 UTC 값이 나와요.

---

## 5. 정리하면 이래요

GitHub Actions cron 스케줄이 안 돌아갈 때, 원인의 절반 이상은 설정 문제예요. 나머지는 GitHub 인프라 이슈고요.

핵심 체크리스트를 정리하면:

- **워크플로우 파일이 기본 브랜치에 있는가?**
- **저장소가 60일 이상 비활성 상태인가?**
- **cron 시간이 UTC 기준으로 맞게 설정돼 있는가?**
- **GitHub Actions 인프라 상태가 정상인가?** (githubstatus.com)
- **`workflow_dispatch`가 함께 설정돼 있어서 수동 실행이 가능한가?**

앞으로 GitHub Actions의 스케줄 안정성이 개선될 여지는 있어요. GitHub이 Actions 인프라 확장 투자를 지속하고 있거든요. 그런데 공유 인프라의 근본적인 한계는 쉽게 사라지지 않아요.

Hugo 블로그를 자동화로 운영한다면, cron 하나에만 의존하지 말고 `push` + `workflow_dispatch`를 함께 걸어두는 게 훨씬 안전해요. 자동화는 언제나 수동 복구 경로를 남겨두는 게 기본이니까요.

지금 당장 GitHub Actions 탭을 열어서 워크플로우 상태 메시지를 확인해보세요.

## 참고자료

1. [Automated Hugo Releases (CI/CD) with Github Actions](https://www.andrewconnell.com/blog/automated-hugo-releases-with-github-actions/)
2. [n개월 째 날라오던 Github Actions 버그 고치기. 대부분의 개발은 귀차니즘에서 시작되었다(?) | by Yeshin Lee | Medium](https://yeslee-v.medium.com/n%EA%B0%9C%EC%9B%94-%EC%A7%B8-%EB%82%A0%EB%9D%BC%EC%98%A4%EB%8D%98-github-action-%EB%B2%84%EA%B7%B8-%EA%B3%A0%EC%B9%98%EA%B8%B0-bbee7c1e3bb5)
3. [Incident with Actions – Resolved | Hacker News](https://news.ycombinator.com/item?id=48022900)


---

*Photo by [Roman Synkevych](https://unsplash.com/@synkevych) on [Unsplash](https://unsplash.com/photos/blue-and-black-penguin-plush-toy-UT8LMo-wlyk)*
