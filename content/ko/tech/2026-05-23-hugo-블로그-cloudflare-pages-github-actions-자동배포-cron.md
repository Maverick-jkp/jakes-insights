---
title: "Hugo 블로그 Cloudflare Pages 자동배포, GitHub Actions cron 트리거 안 될 때 해결법"
date: 2026-05-23T20:34:47+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "hugo", "/ube14/ub85c/uadf8", "cloudflare", "GitHub Actions"]
description: "Hugo 블로그 GitHub Actions cron이 60일 비활성 시 자동 중단되는 문제와 Cloudflare Pages 배포 실패 원인을 분석합니다. publishDate만으로는 자동 발행이 안 되며, 워크플로우 유지 방법과 지연 대응법을 정리했습"
image: "/images/20260523-hugo-블로그-cloudflare-pages-gith.webp"
technologies: ["GitHub Actions", "Go", "Cloudflare", "Hugo"]
faq:
  - question: "Hugo 블로그 Cloudflare Pages GitHub Actions 자동배포 cron 트리거 안 될 때 해결법"
    answer: "GitHub Actions의 schedule 트리거는 레포지토리에 60일 이상 활동이 없으면 GitHub이 자동으로 비활성화합니다. Actions 탭에서 비활성화된 워크플로우를 확인하고 'Enable workflow'를 클릭한 뒤, 재발 방지를 위해 workflow_dispatch를 cron과 함께 설정해두면 수동 테스트로 문제를 빠르게 격리할 수 있습니다."
  - question: "GitHub Actions cron 실행됐는데 Cloudflare Pages 빌드가 안 되는 이유"
    answer: "Cloudflare Pages는 연결된 Git 레포에 push 이벤트가 발생해야 빌드를 시작하는 구조입니다. GitHub Actions가 정상 실행됐더라도 레포에 실제 push가 없으면 Cloudflare Pages는 빌드를 트리거하지 않으므로, 빈 커밋(empty commit)을 push하는 단계를 워크플로우에 추가해야 합니다. 이때 [skip ci] 태그를 커밋 메시지에 붙이지 않으면 push로 인해 GitHub Actions가 재실행되는 무한 루프가 발생할 수 있으니 반드시 포함해야 합니다."
  - question: "GitHub Actions schedule cron UTC 시간 한국 시간으로 맞추는 법"
    answer: "GitHub Actions의 cron은 UTC 기준으로 동작하며, 한국 시간(KST)은 UTC+9이므로 한국 시간 오전 9시에 실행하려면 cron 표현식을 '0 0 * * *'으로 작성해야 합니다. crontab.guru 사이트에서 미리 시뮬레이션해보면 5분 이내로 정확한 표현식을 확인할 수 있습니다."
  - question: "Hugo publishDate 예약 발행 자동화 GitHub Actions 60일 비활성화 막는 방법"
    answer: "Hugo 블로그 Cloudflare Pages GitHub Actions 자동배포 cron 트리거 안 될 때 해결법으로 가장 효과적인 방법은 workflow_dispatch를 schedule과 함께 설정하는 것입니다. 이렇게 하면 Actions 탭에서 'Run workflow' 버튼으로 수동 실행이 가능해져 레포 활성 상태를 유지하기 쉽고, cron이 정상 작동하는지 즉시 검증할 수 있습니다."
  - question: "GitHub Actions cron 대신 Cloudflare Pages Deploy Hook 외부 cron 쓰는 게 나은가요"
    answer: "발행 신뢰성이 중요하다면 cron-job.org 같은 외부 cron 서비스로 Cloudflare Pages Deploy Hook을 직접 호출하는 방식이 GitHub Actions cron보다 안정적입니다. GitHub Actions cron은 60일 비활성화 위험과 수십 분의 best-effort 지연이 있는 반면, Deploy Hook 방식은 GitHub 의존도를 낮추고 무료로 높은 신뢰성을 확보할 수 있습니다."
---

GitHub Actions cron을 믿고 잠자리에 들었는데, 다음 날 아침 예약 포스트가 하나도 발행되지 않았어요. 그 허탈함, 겪어본 사람만 알죠.

> **핵심 요약**
> - GitHub Actions의 `schedule` 트리거는 레포지토리가 60일 이상 비활성 상태이면 GitHub이 자동으로 비활성화한다(GitHub Docs, 2025).
> - Cloudflare Pages는 자체 빌드 트리거를 갖지만, Hugo `publishDate` 필드만으로는 자동 발행이 되지 않는다 — GitHub Actions 워크플로우가 별도로 push를 해야 한다.
> - cron 트리거가 정시에 실행되더라도 최대 수십 분 지연이 발생할 수 있으며, 이는 GitHub 공식 문서에도 명시된 "best-effort" 방침이다.
> - `workflow_dispatch`를 cron과 병행 설정하면, 수동 트리거로 즉시 테스트해 문제를 격리할 수 있다.

---

## cron이 멈추는 이유부터 짚어볼게요

Hugo는 정적 사이트 생성기예요. 빌드 시점에 `publishDate`가 미래 날짜인 글은 기본적으로 렌더링하지 않아요. 그래서 "예약 발행"을 구현하려면 주기적으로 빌드를 다시 돌려야 하죠. 이 역할을 GitHub Actions의 `schedule` 트리거에 맡기는 방식이 2023년 이후 Hugo 커뮤니티의 사실상 표준처럼 자리잡았어요.

문제는 GitHub 쪽에 있어요. **레포지토리에 60일 동안 커밋·PR·이슈 등 활동이 없으면 scheduled workflow를 자동 비활성화**해요(GitHub Docs, Actions > Usage limits, 2025). 블로그 특성상 글 발행 간격이 길면 정확히 이 구간에 걸려요. 비활성화 알림 이메일이 오긴 하는데, 스팸함에 조용히 묻히는 경우가 비일비재하죠.

일본 개발자 えいりす의 사례(note.com, 2024)가 이걸 잘 보여줘요. AI 자동 글쓰기 워크플로우를 구성했는데, 어느 시점부터 cron이 아예 실행되지 않아 기사가 쌓이지 않다가 레포를 다시 활성화하자 밀린 작업들이 한꺼번에 터진 거예요.

Cloudflare Pages는 연결된 Git 레포에 push 이벤트가 오면 빌드를 시작해요. cron 스케줄에 따라 GitHub Actions가 빈 커밋 또는 실제 콘텐츠 변경을 push해야 Cloudflare Pages가 빌드를 트리거하는 구조예요. GitHub Actions가 멈추면 Cloudflare Pages도 당연히 멈춰요. 두 서비스가 서로 의존하는 파이프라인 구조인 셈이에요.

---

## 세 가지 주요 원인과 해결법

### 원인 1: GitHub Actions 레포 비활성화

앞서 말한 60일 규칙이에요. 해결은 단순해요.

1. GitHub 레포 → **Actions 탭** → 비활성화된 워크플로우 확인
2. "Enable workflow" 버튼 클릭
3. 재발 방지를 위해 `workflow_dispatch` 추가

```yaml
on:
  schedule:
    - cron: '0 */3 * * *'  # 3시간마다
  workflow_dispatch:         # 수동 실행 허용
```

이것만 추가하면 Actions 탭에서 "Run workflow" 버튼이 생겨요. cron이 살아있는지 즉시 확인할 수 있고, 디버깅 시간이 확 줄어요.

### 원인 2: cron 문법 오류 또는 타임존 혼동

GitHub Actions cron은 **UTC 기준**이에요. 한국 시간(KST)은 UTC+9라서, 한국 시간 오전 9시에 맞추려면 `0 0 * * *`으로 써야 해요. `0 9 * * *`으로 써두고 왜 오후에 발행되냐고 당황하는 경우가 꽤 많아요.

[crontab.guru](https://crontab.guru)에서 미리 시뮬레이션해보는 게 제일 빨라요. 5분도 안 걸려요.

그리고 `schedule` 트리거는 GitHub 공식 문서 기준 **지연이 발생할 수 있는 "best-effort" 실행**이에요. 트래픽이 몰리는 시간대엔 수십 분 밀릴 수 있어요. 정확히 9:00에 발행돼야 하는 뉴스레터 같은 용도라면 GitHub Actions cron은 맞지 않아요.

### 원인 3: push가 없어서 Cloudflare Pages 빌드가 안 됨

Hugo 자동배포 파이프라인에서 가장 많이 놓치는 부분이에요. GitHub Actions가 실행됐더라도, Cloudflare Pages가 빌드를 하려면 **레포에 push가 일어나야** 해요.

빈 커밋(empty commit)을 push하는 방식이 가장 흔해요.

```yaml
- name: Trigger Cloudflare Pages build
  run: |
    git config user.email "actions@github.com"
    git config user.name "GitHub Actions"
    git commit --allow-empty -m "chore: scheduled build trigger [skip ci]"
    git push
```

`[skip ci]` 태그를 빠뜨리면 이 push로 GitHub Actions가 또 실행되는 무한 루프가 생겨요. 반드시 붙여주세요.

---

## 접근 방식 비교

| 방법 | 난이도 | 안정성 | 비용 | 적합한 경우 |
|------|--------|--------|------|-------------|
| GitHub Actions cron + empty commit | 낮음 | 중간 (60일 비활성화 위험) | 무료 | 개인 블로그, 주 1-2회 발행 |
| Cloudflare Pages Deploy Hook (외부 cron) | 중간 | 높음 | 무료~유료 | 정기 발행, 신뢰성 필요 시 |
| cron-job.org + Deploy Hook | 낮음 | 높음 | 무료 | GitHub 의존도 낮추고 싶을 때 |
| GitHub Actions + `workflow_dispatch` 병행 | 낮음 | 중간+ | 무료 | 수동 테스트 병행하고 싶을 때 |

Cloudflare Pages의 **Deploy Hook**은 특정 URL에 POST 요청이 오면 빌드를 시작하는 기능이에요. GitHub Actions 대신 [cron-job.org](https://cron-job.org) 같은 외부 무료 cron 서비스로 이 URL을 호출하면, GitHub 비활성화 이슈를 완전히 우회할 수 있어요.

Virtualtothecore.com의 가이드(2024)도 이 접근을 권장해요. "GitHub Actions는 빌드 플랫폼으로 직접 쓰기보다, Cloudflare Pages 빌드 훅과 외부 스케줄러를 조합하는 쪽이 더 예측 가능하다"는 요지예요.

---

## 실전 점검 체크리스트

문제가 생겼을 때 이 순서대로 확인하세요.

- `[ ]` GitHub Actions 탭에서 워크플로우 활성화 상태 확인
- `[ ]` cron 문법 UTC 기준으로 재확인 (crontab.guru 사용)
- `[ ]` `workflow_dispatch` 추가해서 수동 실행 테스트
- `[ ]` 워크플로우 실행 후 실제 push/deploy hook 호출 여부 확인
- `[ ]` Cloudflare Pages 빌드 로그에서 트리거 이벤트 타입 확인
- `[ ]` 레포에 최근 60일 내 커밋이 있는지 확인

**중장기 방지책**: Codeslog의 분석(2024)에 따르면, 3시간 간격 cron으로 Hugo 사이트를 운영할 때 장기적으로 안정적인 방식은 **GitHub Actions를 레포 활성화 유지용으로만 쓰고**, 실제 Cloudflare 빌드 트리거는 Deploy Hook + 외부 스케줄러로 분리하는 거예요. 파이프라인 책임이 명확해지고, 어디서 깨졌는지 바로 보여요.

---

## 마무리: 파이프라인은 단순할수록 강해요

핵심만 짚을게요.

- GitHub Actions cron은 60일 비활성화 규칙 때문에 장기 운영엔 불안정해요
- `workflow_dispatch` 추가는 5분짜리 작업인데 디버깅 시간을 크게 줄여줘요
- Cloudflare Pages Deploy Hook + 외부 cron 조합이 제일 단순하고 안정적이에요
- 타임존은 항상 UTC로 계산하고, crontab.guru로 검증하는 습관을 들이세요

앞으로 GitHub이 비활성화 기준을 바꾸거나, Cloudflare Pages가 자체 스케줄 빌드 기능을 추가할 수도 있어요. 실제로 Cloudflare의 2025 로드맵에 "scheduled builds" 기능이 언급된 바 있거든요. 나오면 파이프라인이 훨씬 단순해지겠죠.

지금 당장 해결하고 싶다면, 먼저 Actions 탭 열어서 워크플로우가 살아있는지부터 확인해 보세요. 생각보다 허탈하게 해결될 수 있어요.

---

*이 글이 도움됐다면, 자신의 Hugo 파이프라인 구성을 댓글로 공유해줘요. 어떤 방식이 실제로 잘 동작하는지 더 많은 사례를 모아볼게요.*

## 참고자료

1. [サボりのAlice、そして意図せず増殖した記事、制御不能の自動投稿！GitHub Actionsのcronが動かなかった話｜えいりす](https://note.com/alice_ai_blog/n/nd200e3274b1a)
2. [Automatic publishing of my Hugo website using Github and Cloudflare Pages - Virtual to the Core](https://www.virtualtothecore.com/hugo-github-cloudflare-pages/)
3. [Scheduled Publishing with GitHub Actions Every 3 Hours | Codeslog](https://www.codeslog.com/en/posts/github-actions-scheduled-publish-check/)


---

*Photo by [Conny Schneider](https://unsplash.com/@choys_) on [Unsplash](https://unsplash.com/photos/a-blue-background-with-lines-and-dots-xuTJZ7uD7PI)*
