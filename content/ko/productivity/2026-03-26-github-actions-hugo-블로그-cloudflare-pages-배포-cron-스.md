---
title: "GitHub Actions cron 무시되는 Hugo 블로그 Cloudflare Pages 배포 문제 해결법"
date: 2026-03-26T20:17:46+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "hugo", "GitHub Actions"]
description: "GitHub Actions cron 스케줄이 60일 비활성 시 자동 중단되는 정책, UTC 기준 최대 9시간 시차 문제, Cloudflare Pages Deploy Hook 연동까지 Hugo 예약 발행 실패 원인과 해결법을 정리했습니다."
image: "/images/20260326-github-actions-hugo-블로그-cloudf.webp"
technologies: ["GitHub Actions", "Go", "Cloudflare", "Hugo"]
faq:
  - question: "GitHub Actions cron 스케줄 60일 지나면 자동으로 꺼지나요?"
    answer: "네, GitHub 공식 정책에 따르면 저장소에 커밋이나 풀 리퀘스트 활동이 60일 이상 없으면 schedule 기반 워크플로가 자동으로 비활성화됩니다. Hugo 블로그처럼 콘텐츠 업데이트가 뜸한 저장소가 특히 이 문제에 자주 걸립니다. GitHub Actions 화면에서 'Enable workflow' 버튼을 눌러 즉시 재활성화할 수 있습니다."
  - question: "GitHub Actions Hugo 블로그 Cloudflare Pages 배포 cron 스케줄 무시될 때 해결법이 뭔가요?"
    answer: "GitHub Actions Hugo 블로그 Cloudflare Pages 배포 cron 스케줄이 무시될 때 해결법은 크게 세 가지 원인을 순서대로 확인하는 것입니다. 저장소 비활성화로 워크플로가 꺼진 경우, cron 표현식을 UTC가 아닌 KST 기준으로 잘못 작성한 경우, 그리고 Cloudflare Pages Deploy Hook URL을 워크플로에서 호출하지 않은 경우입니다. 세 원인 중 하나만 해결해도 대부분의 케이스가 정상화됩니다."
  - question: "GitHub Actions cron 한국 시간으로 설정하는 방법"
    answer: "GitHub Actions의 cron은 무조건 UTC 기준으로 작성해야 하며, 한국 시간(KST)은 UTC+9이므로 원하는 시각에서 9를 빼면 됩니다. 예를 들어 오전 9시에 배포하려면 'cron: 0 0 * * *'으로 설정해야 하고, '0 9 * * *'으로 쓰면 실제로는 한국 시간 오후 6시에 실행됩니다. 또한 GitHub Actions cron은 서버 부하에 따라 최대 수십 분 지연될 수 있습니다."
  - question: "Cloudflare Pages GitHub Actions에서 빌드했는데 배포가 안 될 때"
    answer: "GitHub Actions에서 Hugo 빌드를 완료했더라도 Cloudflare Pages에 자동으로 배포되지는 않습니다. Cloudflare Pages 대시보드의 Settings → Builds & Deployments → Deploy Hooks에서 URL을 생성한 뒤, 워크플로 마지막 단계에 'curl -X POST '${{ secrets.CLOUDFLARE_DEPLOY_HOOK }}'' 한 줄을 추가해야 실제 배포가 트리거됩니다. 이 훅 호출 없이는 빌드 결과물이 Cloudflare Pages에 전달되지 않습니다."
  - question: "GitHub Actions Hugo 블로그 Cloudflare Pages 배포 cron 스케줄 무시될 때 workflow_dispatch 같이 쓰는 이유"
    answer: "GitHub Actions Hugo 블로그 Cloudflare Pages 배포 cron 스케줄이 무시될 때 해결법 중 하나로 workflow_dispatch를 함께 설정하면 스케줄이 멈춘 상황에서도 버튼 클릭 한 번으로 워크플로를 즉시 실행해 문제를 바로 재현하고 디버깅할 수 있습니다. 또한 cron과 workflow_dispatch를 병행하면 60일 비활성화 정책을 우회하는 빈 커밋 자동화 없이도 수동 실행으로 저장소 활동을 유지하는 데 도움이 됩니다. yaml 파일에 'workflow_dispatch:' 한 줄만 추가하면 적용됩니다."
aliases:
  - "/tech/2026-03-26-github-actions-hugo-블로그-cloudflare-pages-배포-cron-스/"

---

Hugo 블로그 예약 발행 설정해뒀는데, 정해진 시간에 글이 안 올라온 적 있죠? 설정은 완벽해 보이는데 GitHub Actions가 그냥 조용히 멈춰 있는 거예요. 2026년에도 이 문제로 이슈 트래커 뒤지는 개발자들이 꽤 많아요.

왜 이런 일이 생기는지, 실제로 어떻게 해결하는지 데이터 기반으로 살펴볼게요.

---

> **핵심 요약**
> - GitHub Actions의 `schedule` 트리거는 저장소 활동이 60일 이상 없으면 GitHub 정책에 따라 자동으로 비활성화된다.
> - cron 표현식을 UTC 기준으로 작성하지 않으면 예상 시각과 최대 9시간 차이가 생길 수 있다.
> - Cloudflare Pages는 GitHub Actions에서 별도로 Deploy Hook을 호출하지 않으면 Hugo 빌드 결과물을 배포하지 않는다.
> - 3가지 주요 원인(비활성화, 시간대 오류, 배포 훅 누락) 중 하나만 해결해도 절반 이상의 케이스가 해결된다.
> - `workflow_dispatch`를 cron과 병행 설정하면 수동 트리거로 문제를 즉시 재현하고 디버깅할 수 있다.

---

## cron이 갑자기 멈추는 진짜 이유

사실 "갑자기" 멈추는 게 아닌 경우가 대부분이에요.

GitHub Actions의 `schedule` 워크플로는 세 가지 조건이 모두 충족돼야 정상 작동해요. 저장소가 활성 상태여야 하고, cron 표현식이 UTC 기준으로 올바르게 작성돼 있어야 하며, 워크플로의 마지막 단계가 실제로 Cloudflare Pages에 배포 명령을 보내야 해요.

GitHub 공식 문서에 따르면, `schedule` 기반 워크플로가 포함된 저장소에 **60일 이상 커밋이나 풀 리퀘스트 활동이 없으면** 해당 스케줄을 자동으로 비활성화해요. 알림 이메일을 보내긴 하지만 스팸 폴더에 들어가거나 그냥 넘기기 쉽죠. Hugo 블로그처럼 정적 콘텐츠 위주로 가끔 업데이트하는 저장소가 딱 이 패턴에 해당돼요.

두 번째는 시간대 문제예요. GitHub Actions의 cron은 **무조건 UTC 기준**이에요. 한국 시간(KST)은 UTC+9라서, 오전 9시에 배포하고 싶다면 `cron: '0 0 * * *'`으로 써야 해요. `0 9 * * *`으로 쓰면 한국 시간 오후 6시에 실행돼요. 맞아요, 9시간 차이예요.

세 번째는 Cloudflare Pages와의 연결 문제예요. Hugo 빌드를 GitHub Actions에서 돌렸는데 그 결과가 Cloudflare Pages에 전달이 안 되는 경우예요. 설정 구조 자체를 다시 봐야 해요.

---

## 세 가지 원인, 각각 어떻게 고치나요?

### 저장소 비활성화: 가장 쉬운 해결책

GitHub Actions 화면에서 해당 워크플로를 찾아 **"Enable workflow"** 버튼을 누르면 돼요. 말 그대로 끝이에요.

반복되면 곤란하겠죠? 예방 방법은 두 가지예요.

첫째, `git commit --allow-empty -m "keep-alive"` 명령으로 빈 커밋을 자동 생성하는 워크플로를 따로 만들어서 저장소를 계속 활성 상태로 유지하는 방법. 둘째, 배포 워크플로에 `workflow_dispatch` 트리거를 함께 달아두는 거예요.

```yaml
on:
  schedule:
    - cron: '0 0 * * *'
  workflow_dispatch:
```

이 두 줄만 있어도 디버깅이 훨씬 편해져요. 스케줄이 멈춰도 버튼 클릭 한 번으로 즉시 실행하고 문제를 재현할 수 있거든요.

### cron 시간대 오류: UTC 계산 필수

한국 기준 원하는 시각에서 9를 빼면 UTC 시각이에요.

| 원하는 시각 (KST) | cron 표현식 (UTC) | 비고 |
|---|---|---|
| 오전 6시 | `0 21 * * *` | 전날 UTC 21:00 |
| 오전 9시 | `0 0 * * *` | UTC 자정 |
| 오후 12시 | `0 3 * * *` | UTC 03:00 |
| 오후 6시 | `0 9 * * *` | UTC 09:00 |
| 자정 | `0 15 * * *` | UTC 15:00 |

참고로 GitHub Actions cron은 정각에 실행되지 않아요. GitHub 문서에 따르면 **대기열 부하에 따라 최대 수십 분 지연**될 수 있어요. 정확한 타이밍이 중요한 게 아니라면 큰 문제는 아니지만, "왜 9시에 안 올라왔지?" 하고 당황할 수는 있죠.

### Cloudflare Pages 배포 훅 연결: 핵심

이게 가장 많이 놓치는 부분이에요.

GitHub Actions에서 Hugo를 빌드했다고 해서 자동으로 Cloudflare Pages에 올라가는 게 아니에요. Cloudflare Pages에 **Deploy Hook URL**을 만들고, 워크플로 마지막 단계에서 그 URL로 HTTP POST 요청을 보내야 해요.

Cloudflare Pages 대시보드 → 해당 프로젝트 → Settings → Builds & Deployments → Deploy Hooks에서 URL을 생성하고, GitHub 저장소 Secrets에 `CLOUDFLARE_DEPLOY_HOOK`으로 저장한 뒤:

```yaml
- name: Trigger Cloudflare Pages Deployment
  run: curl -X POST "${{ secrets.CLOUDFLARE_DEPLOY_HOOK }}"
```

이 한 줄을 워크플로 마지막에 추가하면 돼요. Benjamin Abt가 2025년 7월에 정리한 방식과 동일한 패턴이에요. Cloudflare Pages가 GitHub 저장소와 직접 연결돼 있으면 Push 이벤트로 배포되지만, GitHub Actions 기반 cron 워크플로에서는 이 훅을 명시적으로 호출해야 해요.

---

## 접근법 비교: 어떤 설정이 내 상황에 맞을까요?

| 항목 | GitHub Actions + Deploy Hook | Cloudflare Pages 직접 연결 | 외부 스케줄러 (Zapier 등) |
|---|---|---|---|
| cron 제어 | 완전 제어 가능 | 제한적 (Push 이벤트만) | 유연하나 유료 |
| 비활성화 위험 | 있음 (60일 규칙) | 없음 | 없음 |
| 설정 복잡도 | 중간 | 낮음 | 낮음 |
| Hugo 빌드 커스텀 | 가능 | 제한적 | 불가 |
| 디버깅 용이성 | 높음 (로그 제공) | 낮음 | 중간 |
| 비용 | 무료 (월 2,000분 한도) | 무료 | 유료 플랜 필요 |

예약 발행이나 빌드 커스텀이 필요하다면 GitHub Actions + Deploy Hook 조합이 가장 나아요. 단순히 Push할 때마다 배포하면 된다면 Cloudflare Pages 직접 연결이 훨씬 간단하고요.

---

## 지금 바로 확인할 체크리스트

**시나리오 1 — 워크플로가 60일 넘게 실행 안 됐어요**
GitHub Actions 탭에서 해당 워크플로 상태를 확인하세요. "This scheduled workflow is disabled" 메시지가 보이면 Enable 버튼 클릭. 이후 `workflow_dispatch`를 추가해 수동 테스트까지 해보세요.

**시나리오 2 — 워크플로는 실행되는데 배포가 안 돼요**
Actions 로그에서 마지막 step을 확인하세요. Cloudflare Deploy Hook POST가 없다면 위에서 설명한 `curl` 명령을 추가하면 돼요. 응답 코드가 `200`이어야 정상이에요.

**시나리오 3 — 시각이 계속 맞지 않아요**
crontab.guru에 현재 cron 표현식을 입력해서 UTC 기준 실행 시각을 확인하세요. KST로 변환하면 실제 배포 예상 시각이 나와요. Codeslog의 사례에서도 UTC 오차 확인이 디버깅 첫 단계였어요.

---

## 앞으로 뭘 지켜볼까요?

GitHub는 2025년부터 저장소 비활성화 정책을 강화하는 방향으로 가고 있어요. Actions 무료 플랜의 월 사용량 한도(현재 2,000분)도 조정될 가능성이 있고요. Cloudflare Pages 쪽에서는 Deploy Hook 외에 API 토큰 기반 직접 배포 트리거 방식도 공식 지원하고 있어서, 보안이 더 중요한 팀이라면 이 방식을 검토할 만해요.

- **지금 당장**: 저장소 Activities 탭에서 마지막 커밋 날짜 확인
- **이번 주 안에**: `workflow_dispatch` 추가하고 수동 실행 테스트
- **다음 달**: keep-alive 워크플로 설정해서 자동 비활성화 예방

결국 핵심은 하나예요. **설정이 맞아도 연결이 끊길 수 있다**는 거예요. cron은 실행됐는데 배포는 안 됐다면, GitHub Actions와 Cloudflare Pages가 서로를 모르는 상태로 돌아가고 있다는 신호예요.

지금 운영 중인 Hugo 블로그의 마지막 자동 배포가 언제였는지 한번 확인해보세요. 생각보다 오래됐을 수 있거든요.

## 참고자료

1. [Scheduled Builds for Cloudflare Deployments with GitHub Actions | BEN ABT](https://benjamin-abt.com/blog/2025/07/14/scheduled-builds-cloudflare-github-actions/)
2. [Scheduled Publishing with GitHub Actions Every 3 Hours | Codeslog](https://www.codeslog.com/en/posts/github-actions-scheduled-publish-check/)
3. [Hugo 블로그 만들기 - Git Submodule로 구성하고 배포하기](https://minyeamer.github.io/blog/hugo-blog-1/)


---

*Photo by [Vimal S](https://unsplash.com/@vimal_saran) on [Unsplash](https://unsplash.com/photos/a-black-and-white-photo-of-water-droplets-1jPUkDs9aCI)*
