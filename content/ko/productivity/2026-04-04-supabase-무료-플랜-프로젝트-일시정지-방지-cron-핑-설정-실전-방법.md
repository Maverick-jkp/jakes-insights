---
title: "Supabase 무료 플랜 프로젝트 일시정지 방지하는 cron 핑 설정 실전 방법"
date: 2026-04-04T19:58:05+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-web", "supabase", "\ud504\ub85c\uc81d\ud2b8", "\uc77c\uc2dc\uc815\uc9c0", "PostgreSQL"]
description: "Supabase 무료 플랜은 7일 비활성 시 프로젝트를 자동 일시정지합니다. pg_cron과 pg_net으로 DB 내부에서 직접 핑을 보내 일시정지를 막는 cron 설정 방법을 단계별로 설명합니다."
image: "/images/20260404-supabase-무료-플랜-프로젝트-일시정지-방지-cr.webp"
technologies: ["PostgreSQL", "REST API", "GitHub Actions", "Supabase"]
faq:
  - question: "Supabase 무료 플랜 프로젝트 일시정지 방지 cron 핑 설정 실전 방법이 뭔가요?"
    answer: "Supabase 무료 플랜 프로젝트 일시정지 방지 cron 핑 설정 실전 방법은 pg_cron과 pg_net 확장을 조합해 데이터베이스 내부에서 직접 외부 URL로 HTTP 요청을 주기적으로 보내는 방식이에요. 대시보드에서 pg_cron을 활성화하고 SQL Editor에서 cron.schedule() 함수로 잡을 등록하면 외부 서비스 없이 완결되는 구조를 만들 수 있어요. 한 번 설정하면 별도 관리 없이 유지 비용 0원으로 일시정지를 방지할 수 있어요."
  - question: "Supabase 무료 플랜 프로젝트 자동 일시정지 언제 되나요?"
    answer: "Supabase 무료 플랜은 7일간 데이터베이스 활동이 없으면 자동으로 pause 상태로 전환돼요. 여기서 활동은 REST API 호출, Auth 요청, Storage 액세스 같은 실질적인 워크로드를 의미하며, 대시보드를 여는 것만으로는 카운트되지 않아요. 일시정지 후 재개하려면 대시보드에서 수동으로 resume 버튼을 눌러야 하고, 콜드 스타트에 수십 초에서 수 분이 걸릴 수 있어요."
  - question: "pg_cron이랑 pg_net 차이가 뭔가요?"
    answer: "pg_cron은 PostgreSQL 내부에서 스케줄을 정의하고 SQL을 주기적으로 실행하는 확장이고, pg_net은 PostgreSQL 내부에서 외부로 HTTP 요청을 비동기로 보낼 수 있게 해주는 확장이에요. pg_cron 단독으로는 외부 HTTP 요청을 보낼 수 없기 때문에 두 확장을 조합해야 셀프 핑 파이프라인을 구성할 수 있어요. Supabase 프로젝트에서 pg_net은 기본 활성화되어 있고, pg_cron은 대시보드 Extensions 메뉴에서 별도로 켜야 해요."
  - question: "Supabase 프로젝트 일시정지 막으려면 핑 주기 얼마나 해야 하나요?"
    answer: "Supabase 무료 플랜 프로젝트 일시정지 방지 cron 핑 설정 실전 방법에 따르면 핑 주기는 3~5일 간격이면 이론상 충분하지만, 실제 운영에서는 매일 1회가 가장 안정적이에요. 네트워크 오류나 일시적인 실패를 감안하면 간격이 짧을수록 안전 마진이 높아져요. 매일 오전 6시(UTC) 기준으로 cron 잡을 등록하는 것이 일반적으로 권장되는 설정이에요."
  - question: "Supabase cron 핑 외부 서비스 없이 설정할 수 있나요?"
    answer: "네, pg_cron과 pg_net 확장을 조합하면 GitHub Actions나 cron-job.org 같은 외부 서비스 없이 Supabase 프로젝트 내부에서 완결되는 핑 구조를 만들 수 있어요. SQL Editor에서 cron.schedule() 함수로 잡을 등록하면 데이터베이스가 직접 지정된 URL로 HTTP 요청을 보내요. 이 방식은 외부 의존성이 없어 유지 비용이 0원이고 별도 관리가 필요 없다는 장점이 있어요."
aliases:
  - "/tech/2026-04-04-supabase-무료-플랜-프로젝트-일시정지-방지-cron-핑-설정-실전-방법/"
  - "/ko/tech/2026-04-04-supabase-무료-플랜-프로젝트-일시정지-방지-cron-핑-설정-실전-방법/"

---

Supabase 무료 플랜 프로젝트는 **7일간 트래픽이 없으면 자동으로 일시정지(pause)** 돼요. 새벽에 열심히 만든 사이드 프로젝트가 갑자기 접속 불가 상태가 되는 건 생각보다 흔한 일이에요. 그런데 이걸 막는 방법이 Supabase 자체 기능 안에 있다는 걸 아는 사람은 많지 않더라고요.

> **핵심 요약**
> - Supabase 무료(Free) 플랜은 7일 비활성 시 프로젝트를 자동 일시정지하며, 재개(resume)까지 최대 수 분의 콜드 스타트 지연이 발생해요.
> - Supabase Cron(pg_cron 기반)은 PostgreSQL 내부에서 직접 스케줄 작업을 실행하는 기능으로, 2024년 GA(정식 출시) 이후 무료 플랜에서도 사용 가능해요.
> - `pg_cron` + `pg_net` 확장을 조합하면 데이터베이스 내부에서 외부 URL로 HTTP 요청을 보내는 "셀프 핑(self-ping)" 파이프라인 구성이 가능해요.
> - 핑 주기는 3~5일 간격이면 충분하지만, 실제 운영에서는 매일 1회가 가장 안정적이에요.
> - 이 방법은 외부 서비스 의존 없이 Supabase 프로젝트 내부에서 완결되는 구조라 유지 비용이 0원이에요.

---

## 내 프로젝트가 갑자기 접속이 안 되는 이유

Supabase 공식 문서에 따르면, 무료 플랜 프로젝트는 **7일간 데이터베이스 활동이 없으면 자동으로 pause 상태**로 전환돼요. 여기서 "활동"이란 REST API 호출, Auth 요청, Storage 액세스 등 실질적인 워크로드를 의미해요. 대시보드를 가끔 여는 것만으로는 카운트가 되지 않아요.

2026년 기준, Supabase 무료 티어는 매달 500MB 데이터베이스, 1GB 파일 스토리지, 50,000 MAU(월간 활성 사용자)를 제공해요. 스펙 자체는 사이드 프로젝트나 MVP에 충분하지만, **비활성 일시정지 정책이 가장 큰 함정**이에요. 특히 초기 사용자가 적은 서비스, 개인 포트폴리오, 내부 툴처럼 트래픽이 산발적인 케이스에서 자주 문제가 돼요.

프로젝트가 pause 상태가 되면? 모든 API 호출이 실패하고, 대시보드에서 수동으로 resume 버튼을 눌러야 해요. 재개 후 콜드 스타트에 수십 초~수 분이 걸리기도 해요. 사용자가 있는 서비스라면 치명적이에요.

해결 방법은 크게 세 가지예요.

- **외부 cron 서비스로 핑** (GitHub Actions, cron-job.org 등)
- **Supabase Edge Functions 스케줄러 사용**
- **Supabase Cron + pg_net으로 내부 핑**

이 글에서는 세 번째 방법, 즉 **Supabase 프로젝트 내부에서 완결되는 cron 핑 설정**에 집중할게요. 외부 의존성이 없고, 한 번 설정하면 건드릴 필요가 없어서 가장 실용적이거든요.

---

## Supabase Cron이 뭔가요? pg_cron과 뭐가 다른가요?

Supabase Cron은 Supabase가 2024년 정식 출시한 스케줄링 기능이에요. 내부적으로는 PostgreSQL 확장인 **`pg_cron`** 을 기반으로 동작해요. 쉽게 말하면, 데이터베이스 안에서 직접 "매일 오전 9시에 이 SQL 실행해" 같은 스케줄을 짤 수 있는 기능이에요.

중요한 건 `pg_cron`만으로는 외부 HTTP 요청을 못 보낸다는 거예요. 여기에 **`pg_net`** 확장이 필요해요. `pg_net`은 PostgreSQL 내부에서 비동기 HTTP 요청을 보낼 수 있게 해주는 확장으로, Supabase 프로젝트에는 기본 활성화되어 있어요.

두 확장의 역할을 정리하면 이렇게요.

| 확장 | 역할 | Supabase 기본 탑재 |
|------|------|-------------------|
| `pg_cron` | 스케줄 정의 및 실행 | ✅ (Cron 활성화 시) |
| `pg_net` | PostgreSQL → HTTP 요청 전송 | ✅ 기본 활성화 |
| `pg_cron` + `pg_net` | DB 내부에서 외부 엔드포인트 주기적 호출 | ✅ 조합 가능 |

Supabase 대시보드 기준으로, **Database → Extensions** 메뉴에서 `pg_cron`이 활성화되어 있는지 먼저 확인해야 해요. 비활성 상태라면 토글 하나로 켤 수 있어요.

---

## 실전: cron 핑 설정 단계별 가이드

### Step 1. pg_cron 활성화 확인

Supabase 대시보드에서 **Database → Extensions**로 이동해요. 검색창에 `cron`을 입력하면 `pg_cron`이 보여요. 활성화 상태가 아니라면 켜주세요. `pg_net`은 따로 검색해서 확인해요.

SQL Editor에서 다음을 실행해서 두 확장이 설치됐는지 체크할 수도 있어요.

```sql
SELECT name, default_version, installed_version
FROM pg_available_extensions
WHERE name IN ('pg_cron', 'pg_net');
```

`installed_version` 컬럼에 버전 번호가 찍히면 준비 완료예요.

### Step 2. 핑 대상 URL 결정

핑을 보낼 엔드포인트가 필요해요. 가장 간단한 방법은 **Supabase REST API의 헬스체크 엔드포인트**를 쓰는 거예요.

```
https://<your-project-ref>.supabase.co/rest/v1/
```

실제로 데이터베이스 활동을 발생시키려면, 간단한 Edge Function을 하나 만들어두고 그 URL을 핑 대상으로 쓰는 게 더 확실해요. Supabase Edge Functions의 `/functions/v1/ping` 같은 엔드포인트에 `return new Response("ok")`만 있어도 충분해요.

### Step 3. cron 잡 등록

SQL Editor에서 다음 쿼리를 실행해요. 매일 오전 6시(UTC)에 프로젝트 URL로 GET 요청을 보내는 cron 잡이에요.

```sql
SELECT cron.schedule(
  'keep-alive-ping',           -- 잡 이름 (고유해야 해요)
  '0 6 * * *',                 -- 매일 UTC 06:00 실행
  $$
    SELECT net.http_get(
      url := 'https://<your-project-ref>.supabase.co/functions/v1/ping',
      headers := '{"Authorization": "Bearer <your-anon-key>"}'::jsonb
    );
  $$
);
```

`<your-project-ref>`와 `<your-anon-key>`는 Supabase 대시보드 **Settings → API**에서 확인할 수 있어요.

### Step 4. 잡 등록 확인

```sql
SELECT * FROM cron.job;
```

`keep-alive-ping` 이름의 잡이 보이면 등록 완료예요. 실행 이력은 `cron.job_run_details` 뷰에서 볼 수 있어요.

```sql
SELECT * FROM cron.job_run_details
ORDER BY start_time DESC
LIMIT 10;
```

`status = 'succeeded'`로 찍히면 정상 작동 중이에요.

---

## 세 가지 방법 비교: 뭘 선택해야 할까요?

| 기준 | pg_cron + pg_net | GitHub Actions | cron-job.org |
|------|-----------------|----------------|--------------|
| 외부 의존성 | 없음 | GitHub 계정 필요 | 외부 서비스 |
| 설정 복잡도 | 중간 (SQL 필요) | 낮음 (YAML) | 매우 낮음 |
| 비용 | 무료 | 무료 (월 2,000분) | 무료 플랜 있음 |
| 신뢰성 | 프로젝트와 함께 종료 위험 | 레포 유지 필요 | 서비스 운영 현황 의존 |
| 모니터링 | DB 내부 로그 | Actions 로그 | 대시보드 |
| **가장 적합한 경우** | DB 중심 프로젝트 | 이미 GitHub Actions 씀 | 빠른 설정 우선 |

주의할 게 하나 있어요. `pg_cron` + `pg_net` 방식은 **프로젝트가 이미 pause 상태가 되면 cron 자체도 실행되지 않아요**. 방어선이 뚫리면 자가복구가 안 된다는 얘기예요. 그래서 핑 주기를 넉넉히(1~3일) 잡는 게 중요해요. 7일 제한보다 훨씬 짧은 주기로 설정하면 이 문제를 실질적으로 피할 수 있어요.

반면 GitHub Actions는 외부에서 실행되니까 프로젝트 상태와 무관하게 핑을 보낼 수 있어요. 이미 레포가 있는 프로젝트라면 `.github/workflows/keep-alive.yml` 파일 하나 추가하는 게 더 간단할 수도 있어요.

---

## 실제로 운영할 때 챙겨야 할 것들

**시나리오 1 — 개인 포트폴리오나 demo 사이트**

트래픽이 아예 없는 날이 많아요. `pg_cron` 방식으로 매일 1회 핑을 설정해두되, 잡 실행 이력을 월 1회 정도 확인하는 습관을 들이세요. Edge Function 없이 REST API 엔드포인트 직접 핑도 충분해요.

**시나리오 2 — 초기 사용자 유치 중인 스타트업 MVP**

트래픽이 간헐적이에요. `pg_cron` + `pg_net`을 기본으로 하되, GitHub Actions로 이중화해두는 게 좋아요. 핑 하나가 실패해도 다른 쪽이 커버해요. 이 구조면 pause될 가능성이 거의 없어요.

**시나리오 3 — 사내 내부 툴**

업무 시간 외에는 완전히 조용한 케이스예요. `cron-job.org` 같은 외부 서비스가 설정이 제일 빠르고, 대시보드에서 성공/실패 알림을 이메일로 받을 수 있어요. 빠르게 설정하고 잊고 싶다면 이 쪽이에요.

**앞으로 주시해야 할 것들**:
- Supabase가 2026년 하반기에 무료 플랜 정책을 변경할 가능성이 있어요. Pro 플랜 전환 유도 차원에서 비활성 기간을 7일에서 5일로 단축할 수 있다는 커뮤니티 논의가 있었어요.
- Supabase Cron UI가 개선되면서 SQL 없이 대시보드에서 잡을 직접 설정하는 기능이 점진적으로 추가되고 있어요. 2026년 안에 노코드 cron 설정이 완성될 가능성이 높아요.

---

## 마무리: 설정 한 번이면 6개월은 걱정 없어요

정리하면 이렇게 돼요.

- Supabase 무료 플랜은 7일 비활성 시 프로젝트를 자동 pause해요.
- `pg_cron` + `pg_net` 조합으로 데이터베이스 내부에서 셀프 핑을 보내는 게 가장 의존성이 적어요.
- 핑 주기는 매일 1회가 실전에서 가장 안정적이고, `cron.job_run_details`로 주기적으로 모니터링하는 게 좋아요.
- 신뢰성이 특히 중요한 프로젝트라면 GitHub Actions와 이중화를 권장해요.

지금 당장 SQL Editor 열고 `SELECT * FROM cron.job;` 한 번 실행해보세요. 잡이 하나도 없다면, 오늘 설정해두는 게 맞아요. 일시정지된 프로젝트를 수동으로 resume하는 건 딱 한 번만 경험해봐도 충분하거든요.

지금 운영 중인 Supabase 프로젝트가 몇 개인지, 그리고 그 중 핑이 설정 안 된 프로젝트가 몇 개인지 한번 세어보세요.

## 참고자료

1. [Cron | Supabase Docs](https://supabase.com/docs/guides/cron)
2. [[Supabase 시작하기] - 회원 가입부터 기초 CRUD, RAG를 위한 pgvector 활성화 하기 :: 갓대희의 작은공간](https://goddaehee.tistory.com/377)
3. [프리티어 Supabase 프로젝트, 자동으로 살려두는 방법 :: Life Journal](https://inseong1204.tistory.com/183)


---

*Photo by [Conny Schneider](https://unsplash.com/@choys_) on [Unsplash](https://unsplash.com/photos/a-blue-background-with-lines-and-dots-xuTJZ7uD7PI)*
