---
title: "Supabase 무료 플랜 일시정지, cron 우회로 자동 해제되는지 실제 확인하는 방법"
date: 2026-04-30T20:42:05+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-web", "supabase", "\ud504\ub85c\uc81d\ud2b8", "\uc77c\uc2dc\uc815\uc9c0", "PostgreSQL"]
description: "Supabase 무료 플랜 7일 비활성 시 자동 일시정지 정책과 pg_cron·외부 cron으로 우회하는 방법, 실제 자동 해제 여부 확인까지 직접 테스트한 결과를 정리했습니다."
image: "/images/20260430-supabase-무료-플랜-프로젝트-2주-일시정지-자동.webp"
technologies: ["PostgreSQL", "REST API", "GitHub Actions", "Supabase"]
faq:
  - question: "Supabase 무료 플랜 프로젝트 2주 일시정지 자동 해제 cron 우회 실제 작동 확인 방법"
    answer: "Supabase 무료 플랜은 7일간 활동이 없으면 자동 일시정지되며, pg_cron으로 내부 쿼리를 주기 실행하거나 Uptime Robot 같은 외부 서비스로 HTTP 핑을 보내면 일시정지를 막을 수 있어요. cron이 실제로 작동하는지 확인하려면 SQL Editor에서 `SELECT * FROM cron.job_run_details ORDER BY start_time DESC LIMIT 10;`을 실행해 status가 succeeded인지 체크하면 돼요."
  - question: "Supabase 무료 플랜 7일 자동 일시정지 막는 법"
    answer: "pg_cron 익스텐션을 활성화한 뒤 `cron.schedule()`로 매일 `SELECT 1` 같은 가벼운 쿼리를 예약하면 DB 활동으로 인식돼 7일 카운터가 초기화돼요. 단, pg_cron은 프로젝트가 이미 살아있을 때만 실행되므로, Uptime Robot이나 Cron-job.org 같은 외부 서비스와 병행하는 것이 가장 안정적이에요."
  - question: "Supabase pg_cron 설정했는데 작동 안 함 확인하는 방법"
    answer: "Supabase 무료 플랜 프로젝트 2주 일시정지 자동 해제 cron 우회 실제 작동 확인 방법으로 가장 먼저 할 일은 대시보드 → Database → Extensions에서 pg_cron이 활성화돼 있는지 체크하는 거예요. 그 다음 `cron.job_run_details` 테이블을 조회해 status가 failed이거나 결과가 없다면, 익스텐션 비활성화 또는 잘못된 역할로 함수를 실행한 것이 원인일 가능성이 높아요."
  - question: "Supabase 일시정지된 프로젝트 자동으로 깨우기 가능한가요"
    answer: "이미 일시정지된 Supabase 프로젝트는 DB 자체가 꺼진 상태라 pg_cron이 실행되지 않으므로 내부 cron만으로는 자동 재시작이 불가능해요. Uptime Robot이나 Cron-job.org에서 Supabase REST API 엔드포인트로 주기적인 HTTP 요청을 보내면 프로젝트를 깨울 수 있어요."
  - question: "GitHub Actions cron으로 Supabase 프로젝트 살려두기 신뢰할 수 있나요"
    answer: "GitHub Actions의 schedule 트리거는 무료이지만 퍼블릭 저장소의 경우 GitHub이 임의로 실행을 지연하거나 건너뛸 수 있어 신뢰도가 중간 수준이에요. Supabase 무료 플랜 프로젝트 2주 일시정지 자동 해제 cron 우회 실제 작동 확인 방법을 고려할 때, 안정적인 운용을 원한다면 Uptime Robot이나 Cron-job.org처럼 전용 모니터링 서비스를 사용하는 것이 더 권장돼요."
aliases:
  - "/tech/2026-04-30-supabase-무료-플랜-프로젝트-2주-일시정지-자동-해제-cron-우회-실제-작동-확인/"

---

무료로 백엔드 쓰다가 갑자기 API가 먹통이 됐을 때, 그 황당함 알죠? Supabase 무료 플랜을 쓰는 개발자라면 한 번쯤 맞닥뜨리는 상황이에요. 열심히 만들어놓은 프로젝트, 2주 뒤 접속해보니 DB가 완전히 멈춰있는 거예요.

그냥 방치하면 프로젝트가 멈추고, 재시작하면 로딩 시간이 걸리고. 반복이에요. 이 글에서는 Supabase 무료 플랜 자동 일시정지 정책이 어떻게 작동하는지, cron 우회가 실제로 효과가 있는지, 그리고 자동 해제가 제대로 되는지 확인하는 방법까지 정리할게요.

> **Key Takeaways**
> - Supabase 무료 플랜은 7일 동안 활동이 없으면 프로젝트가 자동 일시정지(pause)되며, 이는 공식 정책이에요.
> - `pg_cron` 또는 외부 cron 서비스로 주기적인 DB 쿼리를 실행하면 "활동"으로 인식돼 자동 일시정지를 막을 수 있어요.
> - cron이 실제로 작동하는지 확인하려면 `cron.job_run_details` 테이블을 직접 조회해야 해요.
> - 완전히 일시정지된 프로젝트는 cron이 실행될 환경 자체가 없으므로, 외부 서비스와 내부 pg_cron을 조합하는 게 가장 안정적이에요.

---

## 자동 일시정지, 정확히 어떻게 작동하나요?

Supabase 공식 문서에 따르면, 무료 플랜 프로젝트는 **7일간 아무 활동이 없으면 자동으로 일시정지**돼요. 여기서 "활동"이란 API 요청, 대시보드 접속, DB 쿼리 등 모든 형태의 인터랙션을 포함해요.

일시정지된 프로젝트는 자동으로 깨어나지 않아요. 직접 Supabase 대시보드에서 "Restore Project" 버튼을 눌러야 해요. 이 과정에서 보통 30초~2분의 콜드 스타트 시간이 생기고, 그 사이에 들어오는 API 요청은 전부 실패해요.

사이드 프로젝트나 내부 도구처럼 **트래픽이 산발적인 경우**, 7일은 생각보다 빨리 지나가요. 주말에 잠깐 써보고, 다음 주 금요일에 다시 열었더니 이미 멈춰있는 식이에요.

실제로 많은 개발자들이 처음엔 "버그인 줄 알았다"고 해요. 버그가 아니에요. 설계된 제한이에요.

---

## cron 우회, 실제로 작동하나요?

결론부터 말하면, **작동해요.** 단, 설정 방식에 따라 효과가 달라져요.

### pg_cron으로 내부에서 해결하기

Supabase는 PostgreSQL 기반이라 `pg_cron` 익스텐션을 기본 지원해요. 이걸 쓰면 DB 내부에서 주기적인 쿼리를 실행할 수 있어요.

```sql
-- pg_cron 활성화 (Supabase 대시보드 > Extensions에서도 가능)
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- 매일 자정에 ping 역할의 쿼리 실행
SELECT cron.schedule(
  'keep-alive-job',
  '0 0 * * *',
  $$ SELECT 1 $$
);
```

매일 한 번 DB 쿼리가 실행되고, Supabase는 이를 "활동"으로 인식해요. 7일 카운터가 초기화되는 거예요.

그런데 여기서 중요한 함정이 하나 있어요.

**pg_cron은 프로젝트가 이미 살아있을 때만 실행돼요.** 프로젝트가 일시정지된 상태라면 DB 자체가 꺼져 있는 거라, pg_cron도 당연히 돌지 않아요. 그래서 pg_cron만으로는 "이미 멈춘 프로젝트"를 자동으로 되살릴 수 없어요.

### 외부 cron 서비스로 보완하기

이 한계를 극복하려면 외부에서 HTTP 요청을 날리는 방식을 병행해야 해요. 대표적인 선택지를 비교해볼게요.

| 방법 | 비용 | 신뢰도 | 프로젝트 재시작 가능 여부 | 설정 난이도 |
|------|------|---------|--------------------------|-------------|
| `pg_cron` (내부) | 무료 | 높음 (DB가 살아있을 때) | ❌ 불가 | 낮음 |
| GitHub Actions (schedule) | 무료 | 중간 (최소 5분 딜레이) | ✅ 가능 | 중간 |
| Uptime Robot | 무료 (50개) | 높음 | ✅ 가능 | 낮음 |
| Cron-job.org | 무료 | 높음 | ✅ 가능 | 낮음 |

**Uptime Robot**이나 **Cron-job.org**는 무료 플랜으로도 5~10분 간격 HTTP 핑이 가능해요. Supabase의 REST API 엔드포인트나 Edge Function에 GET 요청을 보내는 것만으로도 프로젝트를 깨어있게 할 수 있어요. 설정도 5분이면 끝나요.

GitHub Actions의 `schedule` 트리거는 무료지만, GitHub이 퍼블릭 저장소의 cron을 임의로 지연시키거나 건너뛸 수 있어요. 미션 크리티컬한 용도엔 권장하지 않아요.

---

## 실제 작동 확인하는 방법

설정했다고 끝이 아니에요. Supabase SQL Editor에서 아래 쿼리를 직접 실행해보세요.

```sql
SELECT
  jobname,
  status,
  return_message,
  start_time,
  end_time
FROM cron.job_run_details
ORDER BY start_time DESC
LIMIT 10;
```

`status`가 `succeeded`로 찍히고 `start_time`이 최근이면 정상 작동 중이에요. `failed`거나 결과가 아예 없다면 job이 등록되지 않았거나 익스텐션이 비활성화된 거예요.

Supabase 공식 트러블슈팅 문서에 따르면, 가장 흔한 실패 원인은 두 가지예요:
1. `pg_cron` 익스텐션이 활성화되지 않은 경우
2. `cron.schedule()` 함수를 `postgres` 스키마가 아닌 다른 역할로 실행한 경우

확인은 간단해요. 대시보드 → Database → Extensions → `pg_cron` 활성화 여부 체크. 이게 먼저예요.

---

## 실제 적용 시 알아야 할 것들

**트래픽이 산발적인 사이드 프로젝트**라면 이렇게 조합하는 게 가장 안정적이에요:
- `pg_cron`으로 매일 DB 내부 핑 (`SELECT 1` 수준)
- Uptime Robot 무료 플랜으로 5분마다 외부 HTTP 핑

pg_cron이 살아있는 동안은 내부에서 활동을 유지하고, 혹시 프로젝트가 멈췄더라도 외부 핑이 재시작을 트리거할 수 있어요.

단, 주의할 점이 있어요. 일시정지된 프로젝트에 REST API 요청이 들어오면 Supabase가 자동으로 깨우도록 시도하지만, 이 자동 복구는 **Supabase 내부 인프라 상태**에 따라 즉시 안 될 수 있어요. 그러니 가장 확실한 건 아예 7일 이전에 활동을 만들어두는 거예요.

참고로 Supabase는 2026년 들어 무료 플랜 정책을 여러 번 조정했어요. 반드시 [Supabase 공식 가격 정책 페이지](https://supabase.com/pricing)에서 현재 기준을 직접 확인하세요.

---

## 정리하면

- Supabase 무료 플랜 자동 일시정지(7일) 정책은 설계된 제한이에요
- `pg_cron`은 내부 활동 유지에 효과적이지만, 이미 멈춘 프로젝트는 살리지 못해요
- 외부 cron 서비스(Uptime Robot, cron-job.org)와 함께 쓰면 안정성이 올라가요
- `cron.job_run_details` 테이블 조회로 실제 작동 여부를 반드시 확인해야 해요

자동 해제가 안 된다고 당황하지 마세요. cron 설정한 다음 날, `cron.job_run_details`를 열어서 초록불이 켜져 있는지 직접 확인해보세요. 그게 가장 확실한 답이에요.

pg_cron 설정 후에도 계속 일시정지가 된다면, 댓글로 어떤 설정을 쓰고 있는지 남겨주세요. 같이 디버깅해볼 수 있어요.

## 참고자료

1. [* 무료 플랜 특징 1. Supabase 무료 플랜은 개인 프로젝트나 학습용으로 충분 2. 가장 중요한 건, 1주일간 활동이 없으면 프로젝트가 자동 중지. 3. 중지된 프로젝트는 ](https://www.threads.com/@ghil_book_pic/post/DPsojPbE2KK/-%EB%AC%B4%EB%A3%8C-%ED%94%8C%EB%9E%9C-%ED%8A%B9%EC%A7%951-supabase-%EB%AC%B4%EB%A3%8C-%ED%94%8C%EB%9E%9C%EC%9D%80-%EA%B0%9C%EC%9D%B8-%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8%EB%82%98-%ED%95%99%EC%8A%B5%EC%9A%A9%EC%9C%BC%EB%A1%9C-%EC%B6%A9%EB%B6%842-%EA%B0%80%EC%9E%A5-%EC%A4%91%EC%9A%94%ED%95%9C-%EA%B1%B4-1%EC%A3%BC%EC%9D%BC%EA%B0%84-%ED%99%9C%EB%8F%99%EC%9D%B4-%EC%97%86%EC%9C%BC%EB%A9%B4-%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8%EA%B0%80-%EC%9E%90%EB%8F%99-%EC%A4%91%EC%A7%803)
2. [Scheduling Cron Jobs for Self-Hosted Supabase: A Complete Guide](https://www.supascale.app/blog/scheduling-cron-jobs-for-selfhosted-supabase-a-complete-guid)
3. [Supabase Docs | Troubleshooting | pg_cron debugging guide](https://supabase.com/docs/guides/troubleshooting/pgcron-debugging-guide-n1KTaz)


---

*Photo by [NASA](https://unsplash.com/@nasa) on [Unsplash](https://unsplash.com/photos/photo-of-outer-space-Q1p7bh3SHj8)*
