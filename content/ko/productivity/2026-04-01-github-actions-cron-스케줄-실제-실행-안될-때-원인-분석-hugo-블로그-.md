---
title: "GitHub Actions cron 스케줄 실행 안 될 때 원인 분석: Hugo 블로그 자동 배포 점검법"
date: 2026-04-01T20:17:50+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "cron", "GitHub Actions"]
description: "GitHub Actions cron 스케줄이 실행 안 될 때 확인할 핵심 원인 4가지: 60일 비활성 시 자동 비활성화, UTC 기준으로 KST와 9시간 차이, 서버 부하로 인한 지연 또는 스킵, Hugo 배포 시"
image: "/images/20260401-github-actions-cron-스케줄-실제-실행-.webp"
technologies: ["GitHub Actions", "Go", "Hugo"]
faq:
  - question: "GitHub Actions cron 스케줄 설정했는데 실행이 안 되는 이유"
    answer: "GitHub Actions cron 스케줄 실제 실행 안될 때 원인은 크게 세 가지예요. 기본 브랜치에 60일 이상 커밋이 없으면 GitHub이 자동으로 스케줄을 비활성화하고, cron 표현식을 UTC가 아닌 한국 시간 기준으로 잘못 작성했거나, 5분 미만 간격으로 설정한 경우 실행 자체가 무시돼요. Actions 탭에서 워크플로 상태를 먼저 확인하고 'Disabled due to inactivity' 메시지가 있으면 수동으로 재활성화하면 해결돼요."
  - question: "GitHub Actions schedule 60일 비활성화 다시 켜는 방법"
    answer: "GitHub Actions의 schedule 트리거는 기본 브랜치에 60일 이상 커밋이 없으면 자동으로 꺼지는데, 별도 알림이 없어서 모르고 지나치기 쉬워요. Actions 탭에서 해당 워크플로를 선택하고 'Enable' 버튼을 눌러 수동으로 재활성화하면 다음 cron 주기부터 정상 실행돼요."
  - question: "GitHub Actions cron UTC KST 시간 변환 한국 시간으로 설정하는 법"
    answer: "GitHub Actions의 cron 표현식은 무조건 UTC 기준으로 동작하기 때문에 한국 시간(KST, UTC+9)으로 변환해서 작성해야 해요. 예를 들어 KST 오전 9시에 실행하려면 'cron: 0 0 * * *'처럼 9시간을 빼서 UTC 00:00으로 설정하면 돼요. crontab.guru 사이트에서 표현식을 검증해보면 실수를 줄일 수 있어요."
  - question: "Hugo 블로그 자동 배포 GitHub Actions 빌드 성공인데 사이트 반영 안 될 때"
    answer: "Hugo 블로그 자동 배포 시 빌드는 성공했지만 사이트가 바뀌지 않는다면 빌드 결과물이 올바른 브랜치에 push됐는지, GitHub Pages 설정에서 해당 브랜치를 소스로 지정했는지 확인해야 해요. GITHUB_TOKEN 권한이 부족하거나 브랜치 보호 규칙으로 인해 push 단계에서 403 오류가 발생하는 경우도 많으니 워크플로 로그의 git push 단계를 중점적으로 살펴보세요."
  - question: "Hugo GitHub Actions git submodule 테마 빌드 실패 해결"
    answer: "Hugo 블로그 자동 배포에서 테마를 Git Submodule로 관리할 때 checkout 단계에 'submodules: true' 옵션을 빠뜨리면 테마 디렉토리가 비어서 빌드가 실패해요. actions/checkout@v4 사용 시 with 옵션에 'submodules: true'와 'fetch-depth: 0'을 함께 추가하면 정상적으로 테마를 포함해 빌드할 수 있어요."
aliases:
  - "/tech/2026-04-01-github-actions-cron-스케줄-실제-실행-안될-때-원인-분석-hugo-블로그-/"
  - "/ko/tech/2026-04-01-github-actions-cron-스케줄-실제-실행-안될-때-원인-분석-hugo-블로그-/"

---

Hugo 블로그 정성껏 만들었는데, cron 스케줄 설정해놓고 아무것도 안 일어나본 적 있죠? 설정은 분명 맞는 것 같은데 배포가 안 된다면, 원인은 생각보다 여러 곳에 숨어 있어요.

> **핵심 요약**
> - GitHub Actions `schedule` 트리거는 **레포지토리가 60일 이상 비활성 상태면 자동으로 꺼져요.** 알림도 없이요.
> - cron 표현식은 **UTC 기준**이라, 한국 시간(KST, UTC+9)으로 안 바꾸면 예상과 9시간 다른 시각에 실행돼요.
> - GitHub 서버 부하가 높을 땐 `schedule` 이벤트가 **수십 분 지연**되거나 드물게 아예 스킵돼요.
> - Hugo 블로그 자동 배포엔 **브랜치 보호 규칙, 퍼미션, Git Submodule 설정**이 동시에 맞아야 정상 동작해요.

---

## GitHub Actions cron, 어떻게 작동하나

`schedule` 트리거는 POSIX cron 문법을 써요. 매일 KST 오전 9시에 빌드하려면 이렇게요.

```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # UTC 00:00 = KST 09:00
```

그런데 이게 **엄밀한 약속이 아니에요.** GitHub 공식 문서엔 이렇게 나와 있어요.

> "Note: GitHub Actions is not intended to replace dedicated task schedulers. Under high load, scheduled workflow runs may be delayed."

cron 스케줄은 정확한 실행 시각을 보장하지 않아요. 이 전제를 모르면 실행이 왜 안 되는지 한참 헤매게 돼요.

---

## 실제로 실행이 안 되는 주요 원인 세 가지

### 원인 #1: 60일 비활성화로 스케줄이 조용히 꺼짐

가장 많은 사람이 놓치는 부분이에요. GitHub은 **기본 브랜치에 60일 이상 커밋이 없으면** `schedule` 트리거를 자동으로 비활성화해요. 2022년부터 적용된 공식 정책이에요.

Hugo 블로그 특성상 콘텐츠를 한동안 안 올리면 커밋 공백이 생겨요. 두 달이 지나면? cron은 조용히 꺼져요. 알림도 없이요.

**진단**: Actions 탭 → 해당 워크플로 → "This scheduled workflow is disabled because there has been no recent activity" 메시지 확인.

**해결**: 워크플로를 수동으로 `Enable`하면 돼요. 재활성화 이후 첫 번째 cron 주기부터 다시 실행돼요.

---

### 원인 #2: UTC 착각 + 최소 간격 제한

cron 표현식은 무조건 **UTC 기준**이에요. `cron: '0 9 * * *'`을 쓰면 KST로 오후 6시에 실행돼요. 오전 9시에 배포하려면 `cron: '0 0 * * *'`이어야 해요.

그리고 **5분 미만 간격은 지원 안 해요.** `*/3 * * * *`처럼 3분마다 실행하려 하면 그냥 무시돼요.

| 설정 | 의도 | 실제 동작 |
|---|---|---|
| `0 9 * * *` | KST 오전 9시 | KST 오후 6시 실행 |
| `*/3 * * * *` | 3분마다 | 실행 안 됨 |
| `0 0 * * *` | UTC 자정 | KST 오전 9시 정상 실행 |

---

### 원인 #3: Hugo 배포 파이프라인 구성 오류

cron 자체는 멀쩡한데 **파이프라인 구성 오류**로 실패하는 케이스도 많아요.

**Git Submodule 누락.** Hugo 테마를 Submodule로 관리하면 `submodules: true` 옵션을 빠뜨렸을 때 테마 디렉토리가 비어서 빌드가 실패해요.

```yaml
- uses: actions/checkout@v4
  with:
    submodules: true
    fetch-depth: 0
```

**퍼미션 문제.** `GITHUB_TOKEN` 권한이 부족하면 push 단계에서 403 오류가 나요.

```yaml
permissions:
  contents: write
  pages: write
  id-token: write
```

**브랜치 보호 규칙 충돌.** `main` 브랜치에 직접 push를 막아두면, 자동 배포 워크플로가 결과물을 올리려다 막혀버려요.

---

## 어떤 순서로 확인해야 하나

**"워크플로가 아예 실행 안 돼요"** → Actions 탭에서 비활성화 여부 먼저 확인. 그다음 [crontab.guru](https://crontab.guru)로 cron 표현식 검증. 직전 60일 내 기본 브랜치 커밋 여부 확인.

**"실행은 됐는데 배포가 안 됐어요"** → Actions 로그에서 각 스텝 확인. 대부분 `git push` 단계에서 실패해요. 퍼미션 설정과 브랜치 보호 규칙을 먼저 봐요.

**"빌드는 성공인데 사이트가 안 바뀌어요"** → 빌드 결과물이 올바른 브랜치에 올라갔는지, GitHub Pages 설정에서 해당 브랜치를 소스로 지정했는지 확인해요.

참고로 실시간성이 필요한 배포엔 cron 단독보다 `push` 트리거와 함께 쓰는 게 나아요.

---

## 마치며

GitHub Actions cron 실행 안 될 때 원인은 세 층위로 요약돼요.

- **GitHub 정책층**: 60일 비활성화 자동 중단, 5분 최소 간격
- **시간 설정층**: UTC 기준 오해, 잘못된 cron 표현식
- **파이프라인층**: Submodule·퍼미션·브랜치 규칙 충돌

세 가지 중 하나만 어긋나도 배포가 멈춰요. 반대로 이 세 층위를 순서대로 체크하면 대부분 해결돼요.

지금 당장 Actions 탭 열어서 워크플로 상태 확인해보세요. "Disabled due to inactivity" 메시지가 있다면, 오늘 재활성화하면 내일부터 다시 자동 배포가 돌아가요. 생각보다 허무하게 간단한 경우가 꽤 많더라고요.

막힌 단계가 있다면 댓글로 남겨줘요. 같이 봐요.

## 참고자료

1. [Hugo 블로그 만들기 - Git Submodule로 구성하고 배포하기](https://minyeamer.github.io/blog/hugo-blog-1/)
2. [10. Github Actions 배포 자동화 :: takeU](https://takeu.tistory.com/414)
3. [2. Github Action (With Syntax) - Somaz의 IT 공부 일지 - 티스토리](https://somaz.tistory.com/233)


---

*Photo by [NASA](https://unsplash.com/@nasa) on [Unsplash](https://unsplash.com/photos/photo-of-outer-space-Q1p7bh3SHj8)*
