---
title: "Supabase 무료 플랜 프로젝트 일시정지, GitHub Actions cron으로 자동 방지하는 방법"
date: 2026-04-06T20:13:15+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "supabase", "\ud504\ub85c\uc81d\ud2b8", "\uc77c\uc2dc\uc815\uc9c0", "REST API"]
description: "Supabase 무료 플랜 7일 비활성 자동정지 문제, GitHub Actions cron으로 해결하세요. schedule 트리거로 주기적 API 요청을 자동화해 프로젝트 일시정지를 방지하는 설정 방법을 단계별로 설명합니다."
image: "/images/20260406-supabase-무료-플랜-프로젝트-일시정지-해제-자동.webp"
technologies: ["REST API", "Vercel", "GitHub Actions", "Supabase"]
faq:
  - question: "Supabase 무료 플랜 프로젝트 일시정지 해제 자동화 GitHub Actions cron 설정 방법"
    answer: "Supabase 무료 플랜 프로젝트 일시정지 해제 자동화는 GitHub Actions cron 설정으로 간단히 구현할 수 있어요. .github/workflows/ 폴더에 워크플로우 파일을 만들고, cron 스케줄로 주기적으로 Supabase REST API에 curl 요청을 보내면 7일 비활성 정책을 우회할 수 있어요. 필요한 건 Supabase 프로젝트 URL과 anon key를 GitHub Secrets에 등록하는 것뿐이며, 추가 비용이나 외부 서버 없이 완전 무료로 운영 가능해요."
  - question: "Supabase 무료 플랜 7일 비활성 자동 일시정지 막는 방법"
    answer: "Supabase 무료 플랜은 REST API, 인증, 스토리지 등 모든 API 요청이 7일간 없으면 프로젝트를 자동으로 pause 상태로 전환해요. 이를 막으려면 7일이 되기 전에 주기적으로 API 요청을 보내면 되는데, GitHub Actions의 schedule 트리거를 사용해 매주 1회 더미 요청을 보내는 방식이 가장 간단하고 무료예요. cron 표현식 `0 9 * * 1`처럼 매주 월요일에 한 번만 실행해도 충분히 일시정지를 방지할 수 있어요."
  - question: "Supabase 프로젝트 paused 상태 자동 복구 시간 얼마나 걸려요"
    answer: "Supabase 무료 플랜에서 일시정지된 프로젝트는 대시보드의 Restore 버튼을 누르거나 첫 API 요청이 들어오면 자동 복구되지만, 복구에 최소 몇 초에서 최대 수 분까지 소요될 수 있어요. 이 콜드 스타트 시간 동안 사용자가 접속하면 DB 연결 오류가 발생할 수 있어 실서비스나 MVP 환경에서는 심각한 문제가 될 수 있어요. 때문에 미리 GitHub Actions cron으로 주기적 요청을 보내 일시정지 자체를 방지하는 것이 가장 현실적인 해결책이에요."
  - question: "GitHub Actions cron 문법 매주 특정 요일 실행 설정하는 법"
    answer: "GitHub Actions의 cron 문법은 '분 시 일 월 요일' 순서로 작성해요. 예를 들어 `0 9 * * 1`은 매주 월요일 UTC 오전 9시에 실행되고, `0 9 * * 1,4`는 월요일과 목요일 두 번 실행돼요. GitHub Actions의 schedule 트리거는 UTC 기준으로 동작하므로, 한국 시간(KST)으로 맞추려면 9시간을 빼서 계산해야 해요."
  - question: "Supabase 무료 플랜 일시정지 해제 자동화 GitHub Actions vs Uptime Robot 어떤 게 나아요"
    answer: "Supabase 무료 플랜 프로젝트 일시정지 해제 자동화 방법 중 GitHub Actions cron 설정은 별도 외부 서비스 의존 없이 리포지토리 하나로 완결되어 안정성과 관리 편의성 면에서 가장 우수해요. Uptime Robot 같은 외부 서비스도 무료로 사용 가능하지만, 해당 서비스 자체의 장애나 정책 변경에 영향을 받을 수 있어요. 이미 GitHub을 사용하는 개발자라면 GitHub Actions 방식이 설정 난이도도 낮고 추가 계정 관리도 필요 없어 더 실용적인 선택이에요."
---

사이드 프로젝트 잠깐 손 놨다가 Supabase 대시보드 열었더니 "Project paused" 떠 있던 경험, 개발자라면 한 번쯤 있을 거예요. Supabase 무료 플랜은 7일간 API 요청이 없으면 프로젝트를 자동으로 일시정지해요. 매번 수동으로 해제하는 건 번거롭고, 어느 순간 깜빡하면 서비스가 통째로 멈추죠. GitHub Actions cron 설정 하나면 이 문제를 깔끔하게 해결할 수 있어요.

> **Key Takeaways**
> - Supabase 무료 플랜은 비활성 상태 7일 후 프로젝트를 자동 일시정지하며, 해제에는 최대 수 분이 소요돼 실서비스 운영에 직접적인 영향을 줘요.
> - GitHub Actions의 `schedule` 트리거와 `cron` 문법을 쓰면 주기적으로 Supabase에 더미 요청을 보내 일시정지를 막을 수 있어요.
> - 설정에 필요한 건 Supabase 프로젝트 URL, anon key, 그리고 GitHub Secrets 등록 세 가지뿐이에요.
> - 이 방법은 완전 무료로, 추가 서버나 외부 cron 서비스 없이 GitHub 리포지토리 하나로 해결돼요.

---

## Supabase 무료 플랜 일시정지 정책, 정확히 어떻게 작동하나요?

Supabase는 2022년부터 무료 플랜에 "비활성 프로젝트 일시정지" 정책을 적용하고 있어요. 공식 문서 기준으로, **REST API, 인증, 스토리지 등 어떤 API 요청도 7일간 없으면** 프로젝트가 자동으로 pause 상태로 전환돼요.

일시정지된 프로젝트는 대시보드에서 "Restore" 버튼을 누르거나 첫 API 요청이 들어오면 자동 복구돼요. 문제는 이 복구 시간이 최소 몇 초에서 최대 몇 분까지 걸릴 수 있다는 거예요. 콜드 스타트가 있는 셈이죠.

사이드 프로젝트라면 그냥 넘어갈 수도 있어요. 그런데 MVP나 스테이징 환경처럼 "가끔은 실제로 쓰는" 서비스라면 얘기가 달라요. 사용자가 접속했을 때 DB 연결이 안 돼서 에러가 뜨면, 사용자 신뢰에 직접 영향을 주거든요.

2026년 현재 Supabase 무료 플랜은 여전히 이 정책을 유지하고 있어요. Pro 플랜($25/월)으로 올리면 일시정지 걱정은 없어지지만, 트래픽이 거의 없는 초기 프로젝트에 매달 25달러를 쓰는 건 부담스럽죠. 그래서 많은 개발자들이 GitHub Actions cron 방식을 택해요.

---

## GitHub Actions cron으로 Supabase 일시정지 막기: 단계별 설정

### 핵심 원리: 주기적 더미 요청으로 "활성 상태" 유지

방법은 단순해요. GitHub Actions가 정해진 주기마다 Supabase API에 요청을 보내서 "이 프로젝트 살아있어요"라는 신호를 계속 주는 거예요.

실제로 필요한 건 세 가지예요:
- Supabase 프로젝트 URL (`https://xxxx.supabase.co`)
- Supabase `anon` key
- GitHub Secrets 등록 (URL과 key를 노출하지 않기 위해)

### GitHub Secrets 등록

GitHub 리포지토리 → Settings → Secrets and variables → Actions 순서로 들어가서 두 개를 등록해요:

- `SUPABASE_URL`: Supabase 대시보드의 Project URL
- `SUPABASE_ANON_KEY`: Supabase 대시보드의 anon public key

두 값 모두 Supabase 대시보드 → Settings → API에서 확인할 수 있어요.

### 워크플로우 파일 작성

리포지토리에 `.github/workflows/keep-alive.yml` 파일을 만들고 아래 내용을 붙여 넣어요:

```yaml
name: Supabase Keep Alive

on:
  schedule:
    - cron: '0 9 * * 1'  # 매주 월요일 오전 9시 (UTC)
  workflow_dispatch:      # 수동 실행도 가능하게

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Supabase
        run: |
          curl -X GET "${{ secrets.SUPABASE_URL }}/rest/v1/" \
            -H "apikey: ${{ secrets.SUPABASE_ANON_KEY }}" \
            -H "Authorization: Bearer ${{ secrets.SUPABASE_ANON_KEY }}"
```

cron 문법 `0 9 * * 1`은 "매주 월요일 UTC 오전 9시"를 뜻해요. 7일 정지 정책이니까 주 1회면 충분하죠. 더 여유를 두고 싶다면 `0 9 * * 1,4`로 바꿔서 월·목 두 번 요청해도 돼요.

### 실제로 Supabase에 닿는 요청인지 확인

`/rest/v1/` 엔드포인트는 Supabase의 PostgREST API 루트예요. 특정 테이블이 없어도 응답이 와요. 이 요청 하나로 Supabase는 "활성 API 요청 수신"으로 카운트해요. Supabase 공식 문서는 비활성 판정 기준을 "REST API 포함 모든 API 요청 없음"으로 정의하고 있기 때문에, 이 curl 요청은 완전히 유효한 방식이에요.

---

## 방법 비교: 어떤 방식이 맞는 선택일까요?

Supabase 무료 플랜 일시정지를 막는 방법은 여러 가지예요. 각각의 실질적인 차이를 비교해 볼게요.

| 방식 | 비용 | 설정 난이도 | 안정성 | 별도 인프라 |
|------|------|------------|--------|------------|
| **GitHub Actions cron** | 무료 | 낮음 (5분) | 높음 | 불필요 |
| Uptime Robot / Better Uptime | 무료~유료 | 낮음 | 중간 (외부 서비스 의존) | 불필요 |
| 자체 cron 서버 (EC2 등) | 유료 | 높음 | 높음 | 필요 |
| Vercel / Netlify Scheduled Functions | 무료~유료 | 중간 | 높음 | 불필요 |
| 수동 복구 | 무료 | 없음 | 낮음 (사람이 기억해야 함) | 불필요 |

GitHub Actions cron이 가장 나은 이유는 명확해요. 이미 코드가 GitHub에 있고, 별도 계정이나 서비스 가입 없이 리포지토리 안에서 모든 게 해결되거든요. GitHub Actions는 공개 리포지토리에서 완전 무료, 비공개 리포지토리도 월 2,000분의 무료 사용 시간이 있어요. 이 워크플로우 실행 시간은 1분도 안 되고요.

Uptime Robot 같은 외부 모니터링 서비스도 나쁘진 않아요. 그런데 서비스가 다운되거나 정책이 바뀌면 의존성이 생기는 단점이 있어요. 자체 서버는 비용이 드니까 무료 플랜을 유지하려는 이유 자체와 충돌하고요.

---

## 이 설정, 어떤 상황에 쓸 때 제일 좋을까요?

**시나리오 1: 개인 포트폴리오 / 사이드 프로젝트**
트래픽이 거의 없고 자신만 쓰는 프로젝트라면 딱 맞는 방법이에요. 설정 한 번으로 이후엔 아무것도 안 해도 되거든요. 단, GitHub 리포지토리가 아카이브 상태거나 비활성이면 Actions도 실행 안 되니까 주의해야 해요.

**시나리오 2: 팀 스테이징 환경**
팀원들이 가끔 QA 목적으로 접속하는 스테이징 DB라면 주 2회 ping 정도면 충분해요. `workflow_dispatch`를 설정해두면 "오늘 QA 해야 하는데 혹시 정지됐을까봐" 걱정 없이 수동으로도 돌릴 수 있어요.

**시나리오 3: MVP 초기 배포**
사용자가 간헐적으로 접속하는 초기 서비스라면, 이 방법이 Pro 플랜 업그레이드 전까지의 임시 방어선이 될 수 있어요. 실사용자가 늘기 시작하면 Supabase Pro 플랜으로 넘어가는 걸 고려해야 해요. 무료 플랜에는 일시정지 외에도 데이터베이스 용량(500MB), 동시 연결 수 제한 등 여러 제약이 있거든요.

**참고로 주시해야 할 것들:**
- Supabase가 비활성 기준을 7일 이하로 단축할 경우, cron 주기도 그에 맞게 줄여야 해요
- GitHub Actions 무료 사용 시간 정책이 바뀔 가능성도 있어요 (2026년 현재 기준은 안정적이에요)
- Supabase 공식 문서에서 새로운 "활성화" 방법을 공지할 때 대응 방법이 바뀔 수 있어요

---

## 마무리: 자동화 설정, 지금 5분이면 돼요

Supabase 무료 플랜 일시정지는 사이드 프로젝트 개발자에게 사소하지만 반복적인 마찰이에요. GitHub Actions cron 설정으로 이 문제를 완전히 없앨 수 있어요. 핵심만 정리하면:

- **7일 비활성 → 자동 정지**가 Supabase 무료 플랜의 정책이에요
- **GitHub Actions cron**으로 주 1~2회 ping을 보내면 정지를 막을 수 있어요
- 설정 파일은 `.github/workflows/keep-alive.yml` 하나예요
- 비용은 0원, 추가 서비스 가입도 필요 없어요

앞으로 6~12개월 안에 Supabase가 무료 플랜 정책을 어떻게 바꿀지는 지켜봐야 해요. 사용자 수가 늘면서 무료 인프라 비용 부담이 커지고 있기 때문에, 비활성 기준이 더 짧아질 가능성도 있거든요. 지금 설정해두고, 혹시 정책이 바뀌면 cron 주기만 조정하면 돼요.

"Project paused"가 또 뜰 때까지 기다릴 건가요, 아니면 오늘 5분 쓰고 이 문제를 끝낼 건가요?

## 참고자료

1. [[Supabase 시작하기] - 회원 가입부터 기초 CRUD, RAG를 위한 pgvector 활성화 하기 :: 갓대희의 작은공간](https://goddaehee.tistory.com/377)
2. [배포 시 자동으로 운영 DB에 마이그레이션 적용해보자 (With. Github actions, Supabase)](https://gaebarsaebal.tistory.com/139)
3. [How to Set Up a GitHub Actions Cron Job to Prevent Supabase Inactivity - DEV Community](https://dev.to/nasreenkhalid/how-to-set-up-a-github-actions-cron-job-to-prevent-supabase-inactivity-3m6b)


---

*Photo by [Akshat Sharma](https://unsplash.com/@asphotographypics) on [Unsplash](https://unsplash.com/photos/robotic-arm-with-pincers-in-a-dusty-environment-Au8NdOftMaI)*
