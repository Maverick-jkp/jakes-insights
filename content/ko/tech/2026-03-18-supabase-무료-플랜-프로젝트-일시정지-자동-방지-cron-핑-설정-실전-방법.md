---
title: "Supabase 무료 플랜 프로젝트 일시정지 자동 방지 cron 핑 설정 실전 방법"
date: 2026-03-18T20:18:56+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-web", "supabase", "\ud504\ub85c\uc81d\ud2b8", "\uc77c\uc2dc\uc815\uc9c0", "TypeScript"]
description: "Supabase 무료 플랜은 7일 비활성 시 자동 일시정지됩니다. pg_cron과 Edge Function으로 외부 서비스 없이 2~3일 간격 핑을 설정해 프로젝트 중단을 방지하는 실전 방법을 단계별로 정리"
image: "/images/20260318-supabase-무료-플랜-프로젝트-일시정지-자동-방지.webp"
technologies: ["TypeScript", "PostgreSQL", "REST API", "Vercel", "Supabase"]
faq:
  - question: "Supabase 무료 플랜 프로젝트 일시정지 자동 방지 cron 핑 설정 실전 방법 뭐가 제일 좋음?"
    answer: "Supabase 무료 플랜 프로젝트 일시정지 자동 방지 cron 핑 설정 실전 방법 중 가장 권장되는 건 Supabase 자체 pg_cron 기능을 쓰는 방식이에요. 대시보드 Integrations → Cron 메뉴에서 'SELECT 1' 쿼리를 2~3일 간격으로 실행하도록 설정하면 외부 서비스 없이 완전히 해결돼요. UptimeRobot 같은 외부 서비스도 있지만 해당 서비스 장애 시 같이 멈추는 리스크가 있어서 내부 cron이 더 안정적입니다."
  - question: "Supabase 무료 플랜 7일 일시정지 방지하려면 핑 주기 얼마로 설정해야 해?"
    answer: "7일 제한이라고 해서 6일 간격으로 설정하면 위험할 수 있어요. Supabase가 활성 요청을 UTC 기준 캘린더 날짜 단위로 집계하기 때문에 경계 부근에서 타이밍이 어긋나면 간헐적으로 일시정지될 수 있거든요. 안정적으로 운영하려면 2~3일 간격(예: `0 0 */2 * *`)으로 짧게 잡는 걸 권장합니다."
  - question: "Supabase cron job 무료 플랜에서 몇 개까지 만들 수 있어?"
    answer: "Supabase 무료 플랜에서는 프로젝트당 cron job을 최대 2개까지 생성할 수 있어요. 최소 실행 간격은 1분이며, keep-alive 핑용으로 1개를 쓰면 추가 용도로 1개를 더 사용할 수 있습니다."
  - question: "Supabase Edge Function으로 일시정지 방지 핑 보낼 때 주의할 점은?"
    answer: "Edge Function을 cron으로 호출할 때 함수 호출 자체만으로는 일시정지 방지 효과가 없어요. 반드시 함수 내부에서 데이터베이스 쿼리를 실행해야 Supabase가 '활성 요청'으로 인식합니다. 단순 유지 목적이라면 pg_cron으로 'SELECT 1'만 실행하는 게 훨씬 간단하고, Edge Function은 슬랙 알림 같은 부가 기능이 필요할 때 선택하는 게 적합해요."
  - question: "Supabase 프로젝트 일시정지됐을 때 복구하는 방법은?"
    answer: "일시정지된 Supabase 프로젝트는 대시보드에서 수동으로 'Restore' 버튼을 클릭해야 재개할 수 있어요. 복구까지 수 분이 걸릴 수 있고, 그 사이 API 요청은 전부 실패 상태가 됩니다. 이런 상황을 원천 차단하려면 Supabase 무료 플랜 프로젝트 일시정지 자동 방지 cron 핑 설정을 미리 해두는 것이 가장 확실한 방법입니다."
---

무료로 쓰는 Supabase 프로젝트가 어느 날 갑자기 멈춰 있었던 경험, 맞죠? 7일만 접속 안 해도 프로젝트가 통째로 일시정지돼요. 사이드 프로젝트 개발자들 사이에서 꽤 자주 겪는 문제인데, 해결법은 생각보다 단순해요.

> **핵심 요약**
> - Supabase 무료 플랜(Free Tier)은 7일간 활성 요청이 없으면 프로젝트를 자동으로 일시정지(pause)시킨다.
> - Supabase가 2024년 말 공식 제공하기 시작한 `pg_cron` + Edge Function 조합을 쓰면 외부 서비스 없이도 자동 핑 설정이 가능하다.
> - 무료 플랜에서 cron job은 프로젝트당 2개까지 허용되며, 최소 실행 간격은 1분이다.
> - 핑 주기는 5~6일 간격보다 2~3일 간격으로 짧게 잡는 편이 훨씬 안정적이다.
> - 백엔드 코드나 외부 서버 없이 Supabase 대시보드만으로 전체 설정을 완료할 수 있다.

---

## Supabase 무료 플랜이 프로젝트를 멈추는 이유

Supabase는 오픈소스 Firebase 대안으로 2020년 출시됐어요. PostgreSQL 기반 데이터베이스, 인증, 스토리지, Edge Function을 한데 묶은 BaaS(Backend as a Service)죠. 무료 플랜이 제법 넉넉한 덕에 사이드 프로젝트나 프로토타입 용도로 많이 써요.

문제는 비용 구조에 있어요. Supabase 공식 문서 기준으로, 무료 플랜 프로젝트는 **7일 연속으로 데이터베이스에 활성 쿼리가 없으면 자동으로 일시정지**돼요. 이 상태가 되면 API 요청이 전부 실패하고, 재개하려면 대시보드에서 수동으로 "Restore" 버튼을 눌러야 해요. 재개까지 수 분이 걸리기도 하고요.

2026년 현재 무료 플랜 프로젝트 수 상한은 2개예요. 스토리지 500MB, 데이터베이스 0.5GB, 월 50,000 MAU가 기본 제공돼요. 가격 대비 스펙이 나쁘지 않아서 프로 플랜(월 $25)으로 올리기 전까지 꽤 오래 쓰는 경우가 많죠.

그런데 문제가 생기는 건 주로 이런 패턴이에요.

- 주말에만 접속하는 사이드 프로젝트
- 트래픽이 간헐적인 포트폴리오 사이트
- MVP 테스트 후 잠시 방치한 앱

이때 외부 유료 서비스(UptimeRobot, Cron-job.org 등)를 붙이는 방법도 있지만, Supabase 자체 기능만으로 해결하는 게 훨씬 깔끔해요.

---

## 핵심 분석: cron 핑 설정 세 가지 방법 비교

### 방법 1: Supabase Cron + pg_cron (권장)

Supabase는 2024년 말 공식 Cron 기능을 GA(일반 공개)했어요. 내부적으로 PostgreSQL 확장인 `pg_cron`을 쓰는데, 대시보드 UI에서 클릭 몇 번으로 설정할 수 있어요.

**설정 순서**:

1. Supabase 대시보드 → **Integrations** → **Cron** 메뉴 진입
2. "Create a new cron job" 클릭
3. 아래 설정 입력:

```sql
-- Job Name: keep-alive-ping
-- Schedule: 0 0 */2 * *  (2일마다 자정 실행)
-- Command: SELECT 1;
```

`SELECT 1`은 데이터베이스에 "나 살아있어"라고 신호를 보내는 가장 가벼운 쿼리예요. 테이블을 건드리지도 않고, 부하도 사실상 0에 가까워요.

주기 설정에서 주의할 점이 있어요. 7일 제한이니까 6일마다 실행해도 될 것 같죠? 그런데 Supabase가 "활성 요청"을 집계하는 방식이 UTC 기준 캘린더 날짜 단위여서, 경계 부근에서 타이밍이 어긋나면 간헐적으로 일시정지될 수 있어요. **2~3일 간격을 권장하는 이유**가 여기에 있어요.

### 방법 2: Edge Function + HTTP 핑

Edge Function을 만들어서 Deno 런타임으로 주기적으로 자기 자신을 호출하는 방식이에요. 조금 더 복잡하지만, 핑에 부가 로직(슬랙 알림, 헬스 체크 등)을 붙이고 싶을 때 유용해요.

```typescript
// supabase/functions/keep-alive/index.ts
Deno.serve(async () => {
  const { data, error } = await supabase.from('_health').select('1')
  return new Response(JSON.stringify({ alive: true }), { status: 200 })
})
```

이 함수를 cron으로 호출하면 돼요. 단, Edge Function 호출은 데이터베이스 쿼리와 별개라서 **반드시 함수 내부에서 DB 쿼리를 실행**해야 일시정지 방지 효과가 있어요.

### 방법 3: 외부 서비스 (UptimeRobot / Cron-job.org)

Supabase REST API 엔드포인트를 외부 모니터링 도구로 주기적으로 호출하는 방법이에요. 설정이 제일 쉽지만, 별도 서비스 계정 관리가 필요하고 무료 티어 제한이 있어요.

### 방법 비교

| 기준 | pg_cron (방법 1) | Edge Function (방법 2) | 외부 서비스 (방법 3) |
|------|-----------------|----------------------|-------------------|
| 설정 난이도 | 낮음 | 중간 | 낮음 |
| 추가 비용 | 없음 | 없음 | 무료/유료 혼재 |
| 신뢰성 | 높음 | 높음 | 중간 |
| 부가 기능 | 없음 | 슬랙 알림 등 가능 | 다운타임 알림 |
| 외부 의존성 | 없음 | 없음 | 있음 |
| 추천 상황 | 단순 유지 목적 | 모니터링 필요 시 | 빠른 설정 원할 때 |

세 방법 모두 일시정지 방지 목적은 달성할 수 있어요. 다만 외부 서비스에 의존하면 그 서비스가 장애를 겪을 때 같이 멈춰버리는 리스크가 생겨요. 관리 포인트를 줄이려면 pg_cron이 제일 나아요.

### 설정 후 확인해야 할 것들

cron job을 만들고 나면 대시보드 **Cron → History** 탭에서 실행 이력을 확인할 수 있어요. 처음 실행 전에 수동으로 "Run now"를 눌러서 오류 없이 동작하는지 꼭 확인해 보세요. `SELECT 1`이 실패한다면 프로젝트 자체에 접속 문제가 있다는 신호거든요.

---

## 실제로 쓸 때 알아두면 좋은 것들

**무료 플랜 cron 제한**: 무료 플랜에서는 cron job을 최대 2개까지 만들 수 있어요. 이미 다른 용도로 2개를 쓰고 있다면 하나를 핑 겸용으로 바꾸거나, Edge Function 방식으로 대신해야 해요.

**상황별 추천**:

*주말에만 업데이트하는 개인 블로그*: pg_cron으로 `SELECT 1`을 이틀마다 실행하는 게 제일 깔끔해요. 별도 코드 변경 없이 대시보드만으로 끝나요.

*팀원 여럿이 쓰는 내부 도구*: Edge Function에 슬랙 웹훅을 붙여서 "핑 성공 / 실패" 알림을 받는 구조를 권해요. 조용히 실패해도 모르고 넘어가는 상황을 막을 수 있거든요.

*프로 플랜 전환 타이밍을 재고 있을 때*: 월 트래픽이 50,000 MAU를 넘거나 DB가 0.5GB를 채워간다면 핑 설정보다 플랜 업그레이드를 먼저 검토하는 게 맞아요. cron 핑은 일시정지를 막는 임시 방어선이지, 근본 해결책은 아니에요.

**앞으로 주시할 신호들**:
- Supabase가 2026년 중 Free Tier 일시정지 기준을 7일에서 더 짧게 바꿀 가능성 → 공식 블로그와 릴리즈 노트 정기 확인 필요
- `pg_cron` 무료 플랜 할당량 변경 여부 → Supabase 가격 페이지에서 분기마다 확인
- Edge Function 무료 호출 수 상한(현재 월 50만 회) 정책 변경 가능성

---

## 결론: 5분 설정으로 일시정지 걱정 끝내기

정리하면 이래요.

- **Supabase 무료 플랜은 7일 비활성 시 자동 일시정지**돼요.
- **가장 쉬운 해결법은 대시보드 Cron에서 `SELECT 1` job 추가**예요.
- **주기는 2~3일 간격**이 6일보다 훨씬 안정적이에요.
- **모니터링이 필요하다면 Edge Function + 슬랙 알림** 조합을 써요.
- **cron job 2개 한도**를 넘기면 외부 서비스나 기존 job 재활용을 검토해야 해요.

앞으로 6~12개월 안에 Supabase가 Free Tier 정책을 더 조여올 가능성도 있어요. Vercel, Render 같은 경쟁 플랫폼들도 무료 티어 조건을 꾸준히 바꾸고 있거든요. 지금 cron 핑 하나 설정해 두는 건 5분짜리 작업이지만, 나중에 새벽 2시에 "왜 안 되지?" 하며 식은땀 흘리는 상황을 막아줘요. 대시보드 열고 지금 바로 해보세요.

## 참고자료

1. [백엔드 서버에서 코드로 supabase 서버를 열지않고 활성화 할 수있는 방법 :: bdshi-tec](https://bidshi-tec.tistory.com/415)
2. [Cron | Supabase Docs](https://supabase.com/docs/guides/cron)
3. [프리티어 Supabase 프로젝트, 자동으로 살려두는 방법 :: Life Journal](https://inseong1204.tistory.com/183)


---

*Photo by [Ales Nesetril](https://unsplash.com/@alesnesetril) on [Unsplash](https://unsplash.com/photos/gray-and-black-laptop-computer-on-surface-Im7lZjxeLhg)*
