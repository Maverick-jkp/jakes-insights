---
title: "Supabase 무료 플랜 1주 휴면 자동 중지, cron으로 방지하는 실전 설정"
date: 2026-05-15T21:10:10+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-web", "Supabase /ubb34/ub8cc /ud50c/ub79c /ud504/ub85c/uc81d/ud2b8 1/uc8fc /ud734/uba74 /uc790/ub3d9 /uc911/uc9c0 /ubc29/uc9c0 cron /uc6b0/ud68c /uc2e4/uc804 /uc124/uc815", "PostgreSQL", "REST API"]
description: "Supabase 무료 플랜 7일 비활성 자동 중지를 막는 실전 방법. GitHub Actions cron과 pg_cron 확장으로 주기적 ping을 설정해 콜드 스타트 지연 없이 프로젝트를 항상 활성 상태로 유지하세요."
image: "/images/20260515-supabase-무료-플랜-프로젝트-1주-휴면-자동-중.webp"
technologies: ["PostgreSQL", "REST API", "Vercel", "GitHub Actions", "Supabase"]
faq:
  - question: "Supabase 무료 플랜 프로젝트 1주 휴면 자동 중지 방지 cron 우회 실전 설정 방법"
    answer: "Supabase 무료 플랜 프로젝트 1주 휴면 자동 중지 방지 cron 우회 실전 설정은 GitHub Actions 스케줄 트리거로 매일 REST API에 ping을 보내거나, cron-job.org 같은 외부 서비스에 Supabase URL을 등록하는 방식으로 구현할 수 있어요. 7일 카운터가 리셋되려면 DB 쿼리, REST 호출, 인증 요청 중 하나라도 발생하면 되므로 간단한 curl 요청으로도 충분해요."
  - question: "Supabase 무료 프로젝트 7일 지나면 자동으로 멈추나요"
    answer: "네, Supabase 무료 플랜은 DB 쿼리나 API 호출 등 어떤 트래픽도 없는 상태가 7일 연속 지속되면 프로젝트를 자동으로 pause 상태로 전환해요. 재개 시 콜드 스타트로 첫 요청이 수십 초 지연되거나, 그 사이 들어온 요청이 전부 실패할 수 있어요."
  - question: "GitHub Actions cron으로 Supabase 휴면 방지하는 yml 설정 예시"
    answer: "`.github/workflows/keep-alive.yml` 파일에 `schedule: cron: '0 0 * * *'`을 설정하고, curl로 Supabase REST 엔드포인트에 anon key를 헤더에 담아 요청을 보내면 매일 자동으로 ping이 나가요. GitHub Secrets에 `SUPABASE_URL`과 `SUPABASE_ANON_KEY`만 등록하면 별도 코드 없이 7일 카운터를 리셋할 수 있어요."
  - question: "Supabase 무료 플랜 프로젝트 1주 휴면 자동 중지 방지 cron 우회 외부 서비스 추천"
    answer: "Supabase 무료 플랜 프로젝트 1주 휴면 자동 중지 방지 cron 우회 실전 설정에서 코드 없이 가장 빠르게 적용할 수 있는 외부 서비스는 cron-job.org나 UptimeRobot이에요. 대시보드에서 Supabase REST 엔드포인트 URL을 등록하고 6일 이하 주기로 설정하면, 별도 코드 작성 없이 휴면을 완전히 방지할 수 있어요."
  - question: "Supabase pg_cron Edge Function 조합으로 휴면 방지 가능한가요"
    answer: "Supabase의 pg_cron 확장과 Edge Function을 조합하면 외부 서비스 없이 DB 내부에서 self-healing 루프를 구성할 수 있어요. 다만 이 방식은 GitHub Actions나 외부 cron 서비스에 비해 설정 복잡도가 높아서, 간단한 사이드 프로젝트라면 GitHub Actions 방식이 더 실용적이에요."
---

Supabase 무료 플랜 프로젝트, 한동안 안 건드렸다가 API 호출이 전부 실패한 경험 있으시죠? 정확히는 **7일 연속 비활성 상태**가 되면 프로젝트가 자동으로 pause돼요. 사이드 프로젝트 하나 믿고 있다가 당황스러운 상황, 충분히 막을 수 있어요. 그리고 생각보다 간단해요.

> **핵심 요약**
> - Supabase 무료 플랜은 7일 동안 아무 요청도 없으면 프로젝트를 자동 일시 중지하며, 재개 시 콜드 스타트로 최대 수십 초 지연이 발생해요.
> - GitHub Actions 또는 외부 cron 서비스를 써서 주기적으로 ping을 보내면 휴면을 방지할 수 있어요.
> - Supabase 자체의 `pg_cron` 확장과 Edge Function을 조합하면 DB 내부에서 self-healing 루틴을 만들 수도 있어요.
> - 2026년 현재 Supabase 무료 티어 이용자는 전 세계적으로 빠르게 늘고 있으며, 이 휴면 정책을 몰라서 프로젝트가 중단되는 사례가 커뮤니티에 꾸준히 올라오고 있어요.
> - 방지 방법은 크게 세 가지(GitHub Actions, 외부 cron 서비스, pg_cron + Edge Function)이며 각각 trade-off가 달라요.

---

## 1. DB가 갑자기 잠기는 이유

Supabase는 PostgreSQL 기반 BaaS(Backend as a Service)예요. 무료 플랜은 사이드 프로젝트나 프로토타입을 올려두기에 꽤 쓸 만한 환경이에요.

문제는 비용 구조예요. Supabase 공식 문서에 따르면 무료 플랜 프로젝트는 **7일 연속 비활성 상태** 시 자동으로 pause 상태로 전환돼요. "비활성"의 기준은 DB 쿼리, REST API 호출, 인증 요청 등 어떤 트래픽도 없는 상태예요.

이 정책이 생긴 이유는 단순해요. Supabase도 서버를 운영해야 하는 회사고, 아무도 안 쓰는 프로젝트에 자원을 무한정 쓸 수는 없죠. 무료 사용자가 늘수록 pause 정책은 오히려 합리적인 설계예요.

사이드 프로젝트 특성상 **주말 이틀 연속 아무것도 안 하면** 어떻게 될까요? 7일 카운터가 돌고 있는 거예요. 2주 휴가를 다녀오면? 당연히 중지 상태죠. 재개 시 콜드 스타트 때문에 첫 요청이 수십 초 걸리는 경우도 있어요.

2026년 기준으로 Supabase는 GitHub Stars 기준 70,000개를 넘어선 프로젝트예요. 전 세계 개발자가 무료 플랜으로 테스트 환경을 만들고 있고, 이 휴면 문제는 커뮤니티 포럼과 Reddit에서 반복적으로 등장하는 단골 질문이에요. 알고 나면 쉽지만, 모르면 꽤 골치 아파요.

---

## 2. 휴면이 발생하는 구조와 타임라인

Supabase의 pause 정책은 [공식 pricing 문서](https://supabase.com/pricing)에 명시돼 있어요. 핵심 흐름은 이래요.

1. 프로젝트에 7일 연속 트래픽 없음
2. Supabase가 자동으로 해당 프로젝트를 pause
3. 대시보드에서 수동으로 resume하거나, API 호출 시 자동 재개 시도
4. 재개 시 콜드 스타트 → 첫 요청 지연

실제로 2주 이상 방치된 무료 플랜 프로젝트가 resume되기까지 대시보드 기준 약 1~2분이 걸렸고, 그 사이에 들어온 요청은 전부 실패했어요.

더 신경 쓰이는 건 **운영 중인 서비스의 경우**예요. 사이드 프로젝트라도 사용자가 붙어 있다면, 주말 동안 아무도 안 들어온 순간 7일 카운터가 돌기 시작해요. 트래픽이 적은 서비스일수록 위험하죠.

이걸 막는 원리는 단순해요. **7일이 되기 전에 주기적으로 DB에 요청을 보내면** 카운터가 리셋돼요. 방법은 세 가지예요.

---

## 3. 세 가지 방지 방법: 설정과 비교

### GitHub Actions로 주기적 ping 보내기

가장 널리 쓰이는 방법이에요. GitHub Actions의 `schedule` 트리거를 써서 일정 간격으로 Supabase REST API에 요청을 보내는 거예요.

```yaml
# .github/workflows/keep-alive.yml
name: Supabase Keep Alive

on:
  schedule:
    - cron: '0 0 * * *'  # 매일 자정 UTC 실행

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Supabase
        run: |
          curl -s "${{ secrets.SUPABASE_URL }}/rest/v1/" \
            -H "apikey: ${{ secrets.SUPABASE_ANON_KEY }}" \
            -H "Authorization: Bearer ${{ secrets.SUPABASE_ANON_KEY }}"
```

GitHub Secrets에 `SUPABASE_URL`과 `SUPABASE_ANON_KEY`를 등록하면 끝이에요. 매일 한 번 ping이 나가고, 7일 카운터는 6일을 넘지 않아요.

단, GitHub Actions의 schedule은 **트래픽이 몰릴 때 최대 수 분 지연**될 수 있어요. 정밀한 실행 보장이 필요하다면 다른 방법을 봐야 해요.

### 외부 cron 서비스(Cron-job.org 등) 사용

cron-job.org, UptimeRobot, Better Uptime 같은 외부 서비스도 자주 써요. 설정은 더 간단해요. 목표 URL(Supabase REST endpoint)을 등록하고 실행 주기만 설정하면 돼요. 무료 플랜으로도 24시간 주기 이하의 스케줄이 가능해요.

cron-job.org로 매 6일마다 ping을 보내는 방식을 쓰면 휴면을 완전히 방지할 수 있어요. 코드 없이 대시보드에서 URL 등록만으로 해결할 수 있다는 게 장점이에요.

### pg_cron + Supabase Edge Function으로 내부 루프 만들기

Supabase 자체 기능인 `pg_cron` 확장과 Edge Function을 조합해서 **DB 내부에서 self-healing 루프**를 만드는 방식이에요.

`pg_cron`은 PostgreSQL 확장으로, DB 레벨에서 cron job을 돌릴 수 있어요. Supabase에서는 SQL 에디터로 바로 설정할 수 있어요.

```sql
-- pg_cron 설정 예시
select cron.schedule(
  'keep-alive-job',
  '0 12 * * *',  -- 매일 낮 12시
  $$select 1$$   -- 가장 가벼운 쿼리
);
```

그런데 이 방법에는 중요한 한계가 있어요. **프로젝트가 이미 pause 상태**라면 pg_cron도 실행되지 않아요. DB가 꺼진 상태에서 DB 내부 스케줄러가 돌 수는 없으니까요. 완전한 "자기치유"는 아니에요. 결국 외부 ping과 병행해야 해요.

### 방법별 비교

| 기준 | GitHub Actions | 외부 cron 서비스 | pg_cron + Edge Function |
|------|---------------|-----------------|------------------------|
| 설정 난이도 | 중간 (YAML 작성) | 쉬움 (UI 설정) | 어려움 (SQL + 함수) |
| 추가 비용 | 무료 (월 2,000분) | 무료 티어 있음 | 무료 |
| 실행 보장 | 지연 가능성 있음 | 대체로 안정적 | pause 상태엔 미작동 |
| pause 상태 대응 | ✅ 가능 | ✅ 가능 | ❌ 불가 |
| 코드 관리 필요 여부 | 필요 | 불필요 | 필요 |
| 추천 대상 | GitHub 쓰는 개발자 | 비개발자 / 빠른 설정 | 고급 DB 관리 목적 |

Supabase 무료 플랜 휴면 방지 목적이라면 **GitHub Actions + 외부 cron 서비스 중 하나로 충분**해요. pg_cron은 이미 활성 상태인 DB의 내부 작업 자동화에 쓰는 게 더 적합해요.

---

## 4. 실제로 적용해야 하는 상황은?

**시나리오 1: 사이드 프로젝트, 트래픽이 거의 없음**
트래픽 없는 날이 연속 7일을 넘을 수 있는 상황이에요. GitHub Actions로 매일 ping 한 번 보내는 설정이 제일 빨라요. 15분이면 끝나고, 이후엔 신경 안 써도 돼요.

**시나리오 2: 팀 내부용 툴, 주말엔 아무도 안 씀**
주 5일 근무 기준으로 주말 이틀 + 주중 며칠만 쉬어도 7일을 넘길 수 있어요. cron-job.org로 매 5일마다 ping을 보내는 게 안전해요. "7일 전에 한 번"이 핵심이거든요.

**시나리오 3: 개발/스테이징 환경, 수시로 중단됨**
개발 환경이라면 오히려 pause 상태가 비용 절약에 도움될 수 있어요. 억지로 깨워둘 필요는 없고, **프로 플랜(월 $25)으로 업그레이드**하는 것도 선택지예요. 프로 플랜은 pause 정책이 없어요.

참고로 챙겨야 할 것들:
- Supabase가 무료 티어 정책을 변경할 가능성 — 2026년 현재 7일 정책이지만, 이용자 급증에 따라 더 짧아질 수도 있어요.
- GitHub Actions free tier의 월 2,000분 한도 — 하루 한 번 ping이면 연간 365분 소비. 여유 있어요.
- `anon_key`를 GitHub Secrets에 저장할 때 read-only 권한만 있는 키를 쓰는 게 보안상 맞아요.

---

## 5. 정리하면

Supabase 무료 플랜의 7일 휴면 자동 중지는 알고 나면 피할 수 있는 문제예요.

핵심만 정리하면:
- **7일 이내에 한 번 ping을 보내면** 카운터가 리셋돼요
- 가장 빠른 방법은 **GitHub Actions YAML 15줄**, 코드 없는 방법은 **cron-job.org**
- pg_cron은 이미 활성 상태인 DB에서만 작동해요 — 단독 사용은 불완전해요
- 트래픽이 꾸준히 있는 서비스라면 사실 신경 안 써도 돼요

앞으로 6~12개월 안에 Supabase가 무료 플랜 정책을 어떻게 바꿀지는 모르지만, 기술적 우회 방법 자체는 더 다양해질 거예요. 이미 커뮤니티에서 Vercel Cron, Railway Cron Task 등 다양한 조합이 실험되고 있어요.

지금 당장 설정해봐요. 10분도 안 걸려요.

---

*이 글에서 다룬 설정 방법 중 어떤 게 여러분 환경에 제일 잘 맞았나요? GitHub Actions 외에 다른 방법을 쓰고 있다면 댓글로 공유해 주세요.*

## 참고자료

1. [Supabase 무료 플랜, 2주면 잠든다? GitHub Actions로 자동 깨우는 법 - 비개발자 하랑의 AI 풀스택 도전기](https://lookfortaste.com/supabase-%EB%AC%B4%EB%A3%8C-%ED%94%8C%EB%9E%9C-2%EC%A3%BC%EB%A9%B4-%EC%9E%A0%EB%93%A0%EB%8B%A4-github-actions%EB%A1%9C-%EC%9E%90%EB%8F%99-%EA%B9%A8%EC%9A%B0%EB%8A%94-%EB%B2%95/)
2. [Building a self-healing cron system with pg_cron and Supabase edge functions - DEV Community](https://dev.to/domoniqueluchin/building-a-self-healing-cron-system-with-pgcron-and-supabase-edge-functions-5420)
3. [Supabase 무료 플랜 7일 비활성화 정책, 자동 활성화로 효율적으로 관리하기 - yangdongi](https://yangdongi.com/programming/supabase-free-plan-auto-activation/)


---

*Photo by [Microsoft Copilot](https://unsplash.com/@microsoftcopilot) on [Unsplash](https://unsplash.com/photos/woman-sitting-on-balcony-with-smartphone-7AoGuVvYO_w)*
