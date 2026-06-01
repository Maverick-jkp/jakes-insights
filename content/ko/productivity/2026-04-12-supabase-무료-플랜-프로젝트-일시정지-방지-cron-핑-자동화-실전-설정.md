---
title: "Supabase 무료 플랜 프로젝트 일시정지 방지: cron 핑 자동화 실전 설정 가이드"
date: 2026-04-12T19:55:43+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-web", "supabase", "\ud504\ub85c\uc81d\ud2b8", "\uc77c\uc2dc\uc815\uc9c0", "PostgreSQL"]
description: "Supabase 무료 플랜 7일 비활동 자동 정지 문제, pg_cron 내장 Cron으로 해결하세요. 외부 서비스 없이 DB 안에서 핑 자동화를 설정하는 실전 방법과 쿼리 한도 주의사항까지"
image: "/images/20260412-supabase-무료-플랜-프로젝트-일시정지-방지-cr.webp"
technologies: ["PostgreSQL", "REST API", "GitHub Actions", "Supabase"]
faq:
  - question: "Supabase 무료 플랜 프로젝트 자동으로 정지되는 이유"
    answer: "Supabase 무료 플랜은 7일 연속으로 API 요청이 없으면 프로젝트를 자동 일시정지 상태로 전환합니다. 정지된 프로젝트는 재활성화까지 수십 초에서 수 분의 콜드 스타트 지연이 발생하며, 트래픽이 간헐적인 사이드 프로젝트나 포트폴리오 사이트에 특히 치명적입니다."
  - question: "Supabase 무료 플랜 프로젝트 일시정지 방지 cron 핑 자동화 실전 설정 방법"
    answer: "Supabase 대시보드의 Database → Cron Jobs 메뉴에서 내장 Cron 기능으로 5일 간격의 핑 자동화를 설정할 수 있습니다. 가장 간단한 방법은 스케줄을 '0 0 */5 * *'로 설정하고 명령어로 'SELECT 1'을 입력하는 것으로, 외부 서비스 없이 DB 연결을 유지할 수 있습니다."
  - question: "Supabase 내장 Cron이랑 GitHub Actions 핑 방법 중 뭐가 더 좋나요"
    answer: "내장 Cron은 외부 인프라 없이 바로 설정 가능하지만, DB가 이미 정지된 상태에서는 실행되지 않는다는 치명적인 한계가 있습니다. 반면 GitHub Actions나 cron-job.org는 외부에서 HTTP 요청을 보내기 때문에 이미 정지된 프로젝트도 깨울 수 있어 신뢰성이 더 높습니다."
  - question: "Supabase cron job 핑 간격 얼마로 설정해야 하나요"
    answer: "Supabase 무료 플랜 프로젝트 일시정지 방지 cron 핑 자동화 실전 설정 기준으로 5~6일 간격이 가장 현실적입니다. 7일 정지 정책을 확실히 피하려면 5일 이하 간격을 권장하며, 내장 Cron의 경우 DB가 정지되면 cron 자체도 실행되지 않으므로 여유 있는 간격 설정이 중요합니다."
  - question: "Supabase pg_net으로 REST API 핑 보내는 방법"
    answer: "pg_net 확장이 활성화된 경우 'SELECT net.http_get(url := 'https://[project-ref].supabase.co/rest/v1/', headers := '{'apikey': '[anon-key]'}'::jsonb)'와 같이 SQL로 REST API 엔드포인트에 직접 GET 요청을 보낼 수 있습니다. 이 방법은 DB뿐 아니라 API 레이어까지 함께 깨우지만, anon key가 코드에 포함되므로 Row Level Security(RLS) 설정이 반드시 되어 있어야 합니다."
---

어렵게 만든 사이드 프로젝트가 월요일 아침마다 접속 불가 상태로 변해 있던 적 있으세요? Supabase 무료 플랜의 7일 비활동 자동 정지 정책 때문인데, 해결책은 생각보다 단순해요.

> **핵심 요약**
> - Supabase 무료 플랜은 7일간 API 요청이 없으면 프로젝트를 자동 일시정지하며, 재활성화까지 최대 수 분의 콜드 스타트 지연이 발생해요.
> - Supabase가 2024년 말 정식 출시한 내장 Cron 기능(pg_cron 기반)을 쓰면 외부 서비스 없이 데이터베이스 안에서 바로 핑 자동화를 구성할 수 있어요.
> - GitHub Actions나 cron-job.org 같은 외부 스케줄러 대비, 내장 Cron은 인프라 추가 없이 설정이 가능하지만 DB 쿼리 실행 횟수 한도를 소모한다는 트레이드오프가 있어요.
> - 핑 간격을 5~6일로 설정하는 게 7일 정지 정책을 확실하게 피하는 현실적인 기준이에요.

---

## 무료 플랜의 자동 정지, 정확히 어떻게 작동하나요

Supabase 공식 문서에 따르면, 무료 플랜(Free Tier) 프로젝트는 **7일 연속으로 API 요청이 없으면 자동 일시정지(pause)** 상태로 전환돼요. 정지된 프로젝트는 대시보드에서 수동으로 재시작하거나, 첫 번째 API 요청이 들어올 때 콜드 스타트 방식으로 깨어나는데, 이 과정이 수십 초에서 몇 분까지 걸릴 수 있어요.

개인 포트폴리오 사이트나 사이드 프로젝트처럼 트래픽이 간헐적인 경우, 이 정책이 꽤 골치아파요. 누군가 링크를 공유해서 갑자기 방문자가 몰렸는데 DB가 잠든 상태라면? 그게 첫인상이 되는 거죠.

Supabase 무료 플랜은 PostgreSQL 데이터베이스 500MB, 월 5GB 대역폭, 50,000건 MAU를 제공해서 개인 프로젝트나 학습 환경으로는 충분한 스펙이에요. 문제는 이 정지 정책이 유독 사이드 프로젝트에 치명적이라는 점이에요. 트래픽이 없는 프로젝트가 정지되는 건 Supabase 입장에서도 합리적인 자원 관리지만, 개발자 입장에서는 매번 대시보드에 들어가 재시작하는 게 번거롭죠.

해결책은 두 갈래예요. **외부 cron 서비스로 주기적으로 HTTP 요청을 보내는 방법**과, **Supabase 내부에서 직접 핑을 날리는 방법**. 지금은 두 번째 방법, 즉 Supabase 내장 Cron 기능이 훨씬 깔끔해요.

---

## Supabase 내장 Cron이 뭔지 먼저 알고 가요

Supabase는 PostgreSQL 확장인 `pg_cron`을 기반으로 한 **내장 Cron 기능**을 제공해요. Supabase 대시보드의 **Database → Cron Jobs** 메뉴에서 직접 스케줄을 만들 수 있어요.

세 가지 작업 유형을 지원해요:

- **SQL 쿼리 실행**: 테이블에 값을 쓰거나 함수를 호출하는 방식
- **Supabase Edge Function 호출**: 서버리스 함수를 주기적으로 트리거
- **HTTP 요청(net.http_get)**: 외부 URL이나 내부 엔드포인트에 GET 요청 발송

핑 자동화에 쓸 방법은 주로 1번(SQL로 `SELECT 1` 같은 가벼운 쿼리 실행)이나 3번(DB의 REST API 엔드포인트에 HTTP 요청)이에요.

### 실전 설정: SQL 쿼리 방식

가장 단순한 방법이에요. Cron Job을 만들 때 아래 설정을 쓰면 돼요:

```sql
-- Supabase Dashboard > Database > Cron Jobs > + New cron job
-- Schedule: 0 0 */5 * *  (5일마다 자정)
-- Command:
SELECT 1;
```

이게 전부예요. `SELECT 1`은 DB에 아무 부담 없이 연결을 확인하는 가장 가벼운 쿼리예요. 5일 간격으로 실행하면 7일 정지 기준을 넉넉하게 통과해요.

### 실전 설정: HTTP 핑 방식

`pg_net` 확장이 활성화된 경우, Supabase REST API 엔드포인트에 직접 핑을 날릴 수 있어요:

```sql
SELECT net.http_get(
  url := 'https://[your-project-ref].supabase.co/rest/v1/',
  headers := '{"apikey": "[your-anon-key]"}'::jsonb
);
```

이 방법은 DB뿐 아니라 REST API 레이어까지 깨우는 효과가 있어요. 단, `anon key`가 코드에 포함되므로 Row Level Security(RLS)가 제대로 설정된 상태에서 써야 해요.

---

## 방법별 비교: 어떤 걸 써야 할까요

| 구분 | Supabase 내장 Cron (SQL) | Supabase 내장 Cron (HTTP) | GitHub Actions | cron-job.org |
|------|--------------------------|---------------------------|----------------|--------------|
| 설정 난이도 | 낮음 | 중간 | 중간 | 낮음 |
| 외부 인프라 필요 | 없음 | 없음 | GitHub 계정 필요 | 외부 계정 필요 |
| 무료 한도 소모 | DB 쿼리 카운트 | DB 쿼리 + net 요청 | 월 2,000분 무료 | 무제한 무료 |
| 신뢰성 | DB 살아있을 때만 실행 | DB 살아있을 때만 실행 | 높음 | 높음 |
| 모니터링 | 대시보드 로그 | 대시보드 로그 | Actions 로그 | 이메일 알림 |
| 추천 대상 | 간단한 개인 프로젝트 | API 레이어까지 관리 필요 시 | CI/CD 이미 쓰는 팀 | 비개발자 포함 팀 |

여기서 주목할 점이 있어요. 내장 Cron은 **DB가 이미 살아있어야 실행**된다는 점이에요. 프로젝트가 정지 상태에 빠진 이후에는 내장 Cron도 깨어나지 않아요. 그래서 정지 직전에 cron이 실행되도록 **5일 이하 간격**을 추천해요.

반면 cron-job.org나 GitHub Actions는 외부에서 HTTP 요청을 보내므로, 이미 정지된 프로젝트도 깨울 수 있어요. 한 번이라도 정지 경험이 있다면 외부 서비스가 더 안전해요.

---

## 실전 시나리오별 권장 설정

**시나리오 A — 개인 포트폴리오, 혼자 쓰는 사이드 프로젝트**

내장 Cron으로 `SELECT 1`을 5일 간격 실행하는 게 딱 맞아요. 설정 5분, 관리 비용 제로예요. cron 표현식은 `0 9 */5 * *` (5일마다 오전 9시)면 충분해요.

**시나리오 B — 팀원이 있거나 외부 사용자가 접근하는 프로젝트**

cron-job.org에서 `/rest/v1/` 엔드포인트에 4일 간격 HTTP 요청을 설정하세요. 무료이고, 실패 시 이메일 알림도 와요. 이미 정지된 상태에서도 프로젝트를 깨울 수 있다는 게 결정적인 이유예요.

**시나리오 C — GitHub Actions를 이미 쓰는 개발팀**

`.github/workflows/keep-alive.yml`에 `schedule: - cron: '0 9 */4 * *'` 트리거를 추가하고, `curl`로 REST API를 호출하면 별도 도구 없이 해결돼요. 팀 워크플로우 안에서 버전 관리도 되고요.

---

## 결론: 7일 정지 정책, 이제 신경 끌 수 있어요

**정리하면 이래요:**

- Supabase 무료 플랜은 7일 비활동 시 자동 정지 → 사이드 프로젝트에 치명적
- 내장 Cron(`SELECT 1`, 5일 간격)이 가장 빠른 해결책이지만, DB가 먼저 정지되면 무용지물
- 외부 서비스(cron-job.org, GitHub Actions)는 이미 정지된 상태도 복구 가능 → 신뢰성 우위
- 프로젝트 성격에 따라 두 방법을 같이 쓰는 것도 방법이에요

앞으로 Supabase가 무료 플랜의 정지 기준을 바꾸거나, 자동 핑 옵션을 대시보드에서 직접 켤 수 있게 해줄 가능성이 있어요. 실제로 Supabase GitHub 이슈 트래커에는 "keep-alive 옵션 추가" 요청이 꾸준히 올라오고 있거든요.

그때까지는 오늘 설명한 cron 핑 자동화 설정이 Supabase 무료 플랜 프로젝트 일시정지를 방지하는 가장 현실적인 방법이에요. 지금 바로 대시보드 열어서 Cron Job 하나 만들어 보세요. 5분이면 끝나요.

---

*이 글에서 다룬 Supabase Cron 공식 문서는 [supabase.com/docs/guides/cron](https://supabase.com/docs/guides/cron)에서 확인할 수 있어요. 무료 플랜 정책 상세 내용은 Supabase 공식 Pricing 페이지를 참고하세요.*

## 참고자료

1. [[Supabase 시작하기] - 회원 가입부터 기초 CRUD, RAG를 위한 pgvector 활성화 하기 :: 갓대희의 작은공간](https://goddaehee.tistory.com/377)
2. [Cron | Supabase Docs](https://supabase.com/docs/guides/cron)
3. [* 무료 플랜 특징 1. Supabase 무료 플랜은 개인 프로젝트나 학습용으로 충분 2. 가장 중요한 건, 1주일간 활동이 없으면 프로젝트가 자동 중지. 3. 중지된 프로젝트는 ](https://www.threads.com/@ghil_book_pic/post/DPsojPbE2KK/-%EB%AC%B4%EB%A3%8C-%ED%94%8C%EB%9E%9C-%ED%8A%B9%EC%A7%951-supabase-%EB%AC%B4%EB%A3%8C-%ED%94%8C%EB%9E%9C%EC%9D%80-%EA%B0%9C%EC%9D%B8-%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8%EB%82%98-%ED%95%99%EC%8A%B5%EC%9A%A9%EC%9C%BC%EB%A1%9C-%EC%B6%A9%EB%B6%842-%EA%B0%80%EC%9E%A5-%EC%A4%91%EC%9A%94%ED%95%9C-%EA%B1%B4-1%EC%A3%BC%EC%9D%BC%EA%B0%84-%ED%99%9C%EB%8F%99%EC%9D%B4-%EC%97%86%EC%9C%BC%EB%A9%B4-%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8%EA%B0%80-%EC%9E%90%EB%8F%99-%EC%A4%91%EC%A7%803)


---

*Photo by [Akshat Sharma](https://unsplash.com/@asphotographypics) on [Unsplash](https://unsplash.com/photos/robotic-arm-with-pincers-in-a-dusty-environment-Au8NdOftMaI)*
