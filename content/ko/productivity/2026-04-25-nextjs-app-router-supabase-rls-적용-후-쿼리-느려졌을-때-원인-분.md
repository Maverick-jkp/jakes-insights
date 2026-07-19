---
title: "Next.js App Router Supabase RLS 적용 후 쿼리 느려졌을 때 원인 분석과 트러블슈팅"
date: 2026-04-25T20:00:19+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-web", "next.js", "app", "router", "TypeScript"]
description: "Next.js App Router에서 Supabase RLS 적용 후 쿼리가 3배 느려지는 원인을 분석합니다. RSC 환경에서 인증 토큰 검증이 매 요청마다 반복되는 구조적 문제와 실전 해결 방법을 다룹니다."
image: "/images/20260425-nextjs-app-router-supabase-rls.webp"
technologies: ["TypeScript", "React", "Next.js", "PostgreSQL", "Supabase"]
faq:
  - question: "Next.js App Router Supabase RLS 적용 후 쿼리 느려졌을 때 원인 분석 트러블슈팅 방법"
    answer: "Next.js App Router Supabase RLS 적용 후 쿼리 느려졌을 때 원인 분석 트러블슈팅의 핵심은 서버 컴포넌트마다 별도의 Supabase 클라이언트 인스턴스를 생성하는 패턴을 확인하는 거예요. React의 `cache()` 함수를 활용해 `createServerClient` 호출을 요청 단위로 캐싱하면, 동일 요청 내에서 세션 파싱이 반복되는 문제를 해결할 수 있어요. 이 방법만으로도 평균 쿼리 시간이 2-4배 단축되는 사례가 보고되어 있어요."
  - question: "Supabase RLS 켜면 쿼리 3배 느려지는 이유"
    answer: "RLS를 활성화하면 매 쿼리마다 PostgreSQL이 정책 조건을 평가하면서 `auth.uid()` 함수를 반복 호출하기 때문에 DB 부하가 급증해요. 특히 RLS 정책 SQL에서 `auth.uid()`를 서브쿼리로 감싸면 쿼리 플래너가 이를 상수로 처리하지 못해 행 수에 비례해 속도가 떨어져요. `USING (user_id = auth.uid())`처럼 직접 호출 방식으로 변경하면 수십만 행 테이블에서도 쿼리 시간을 절반 이하로 줄일 수 있어요."
  - question: "Next.js App Router 서버 컴포넌트에서 Supabase 클라이언트 중복 생성 방지하는 법"
    answer: "Next.js App Router에서는 서버 컴포넌트가 트리 곳곳에서 독립적으로 실행되기 때문에, 컴포넌트마다 `createServerClient`를 호출하면 쿠키 파싱과 세션 검증이 계속 반복돼요. 해결책은 `lib/supabase/server.ts` 같은 유틸 파일에서 React의 `cache()` 함수로 클라이언트 생성 로직을 감싸, 하나의 요청 안에서 동일한 인스턴스를 재사용하도록 만드는 거예요. 이렇게 하면 한 페이지 렌더링에서 발생하던 10회 이상의 중복 세션 검증을 1회로 줄일 수 있어요."
  - question: "Supabase RLS auth.uid() 서브쿼리 성능 차이"
    answer: "`USING (user_id = (SELECT auth.uid()))`처럼 서브쿼리로 감싸면 PostgreSQL 쿼리 플래너가 이를 상수로 인식하지 못해 매 행마다 함수를 평가하는 비효율이 발생해요. 반면 `USING (user_id = auth.uid())`로 직접 호출하면 플래너가 해당 값을 상수로 처리해 인덱스를 정상적으로 활용할 수 있어요. 테이블 규모가 클수록 이 차이는 극명하게 나타나며, 단순 수정만으로 쿼리 시간이 절반 이하로 줄어드는 경우도 있어요."
  - question: "Next.js App Router Supabase RLS 적용 후 쿼리 느려졌을 때 cookies() API 중복 호출 문제"
    answer: "Next.js App Router Supabase RLS 적용 후 쿼리 느려졌을 때 원인 중 하나로 `cookies()` API를 여러 서버 컴포넌트에서 중복 호출하는 패턴이 있어요. 이 경우 세션 파싱이 요청마다 반복되어 평균 쿼리 시간이 2-4배 늘어날 수 있어요. `createServerClient`를 `cache()`로 감싼 유틸 함수로 일원화하면 `cookies()` 호출도 자연스럽게 요청당 한 번으로 줄어들어요."
aliases:
  - "/tech/2026-04-25-nextjs-app-router-supabase-rls-적용-후-쿼리-느려졌을-때-원인-분/"

---

RLS를 켰더니 쿼리가 세 배 느려졌어요. 로그를 보니 인증 토큰 검증이 매 요청마다 반복되고 있었죠. Next.js App Router와 Supabase를 함께 쓰는 개발팀이라면 한 번쯤 마주치는 문제예요.

2026년 현재, Next.js App Router는 React 서버 컴포넌트(RSC)를 기본으로 채택하면서 Supabase와의 연동 패턴도 크게 달라졌어요. 기존 Pages Router에서 잘 작동하던 RLS 설정이 App Router에서 성능 병목을 만들어내는 사례가 개발 커뮤니티에서 꾸준히 보고되고 있죠. 문제는 에러가 나는 게 아니라, 조용히 느려진다는 거예요.

이 글에서는 Next.js App Router Supabase RLS 적용 후 쿼리 느려졌을 때의 원인을 구조적으로 분석하고, 실제로 적용 가능한 트러블슈팅 방법을 정리해요.

---

> **핵심 요약**
> - RLS 적용 후 쿼리 성능 저하의 가장 흔한 원인은 서버 컴포넌트마다 별도의 Supabase 클라이언트 인스턴스를 생성하는 패턴이에요. 매 요청마다 `auth.uid()` 검증이 새로 실행되면서 DB 부하가 증가해요.
> - Next.js App Router의 `cookies()` API는 요청당 한 번만 호출해야 해요. 여러 컴포넌트에서 중복 호출하면 세션 파싱이 반복되고 평균 쿼리 시간이 2-4배 늘어나는 패턴이 보고되어 있어요.
> - Supabase의 `createServerClient`는 서버 액션, 라우트 핸들러, 서버 컴포넌트 각각에서 올바른 방식으로 초기화해야 해요. 잘못된 클라이언트 타입 사용이 RLS 정책을 우회하거나 불필요한 재인증을 유발해요.
> - RLS 정책 자체의 쿼리 비용도 원인이에요. `auth.uid()`를 조인 조건 안에서 반복 호출하는 정책은 인덱스를 타지 못하고 풀 스캔을 유발할 수 있어요.

---

## RLS가 느리게 느껴지는 배경: App Router의 구조적 특성

Supabase의 RLS(Row Level Security)는 PostgreSQL의 정책 기반 행 접근 제어 기능이에요. 간단히 말해, "이 유저는 자기 데이터만 볼 수 있다"는 규칙을 DB 레벨에서 강제하는 거예요. 보안 측면에서는 탁월한 선택이지만, Next.js App Router와 만나면 예상치 못한 성능 이슈가 생겨요.

이유는 App Router의 렌더링 방식에 있어요. Pages Router에서는 `getServerSideProps` 하나에서 세션을 받아 Supabase 클라이언트를 초기화했어요. 반면 App Router에서는 서버 컴포넌트가 트리 곳곳에서 독립적으로 실행돼요. 각 컴포넌트가 데이터를 직접 패치하는 구조죠.

이 패턴 자체는 나쁘지 않아요. 그런데 문제는 Supabase 클라이언트 초기화 방식을 잘못 쓰면 매 컴포넌트마다 세션 파싱과 쿠키 읽기가 반복된다는 점이에요. Supabase 공식 문서에 따르면, `@supabase/ssr` 패키지의 `createServerClient`는 요청 컨텍스트 내에서 올바르게 공유되어야 해요. 그렇지 않으면 하나의 페이지 렌더링에서 같은 세션 검증이 열 번 이상 실행될 수도 있어요.

2026년 기준, Next.js 15와 Supabase `@supabase/ssr` 0.5.x 이상을 함께 쓰는 환경에서 이 문제가 가장 자주 보고되고 있어요.

---

## 원인 분석: 어디서 느려지는 걸까요?

### 클라이언트 인스턴스 중복 생성

가장 흔한 원인이에요. 서버 컴포넌트 A와 B가 각각 `createServerClient`를 호출하면, 쿠키에서 세션 토큰을 파싱하는 작업이 두 번 실행돼요.

```typescript
// ❌ 이렇게 하면 각 컴포넌트마다 새 클라이언트가 생겨요
// app/dashboard/page.tsx
const supabase = createServerClient(...)

// app/dashboard/sidebar.tsx  
const supabase = createServerClient(...)
```

수정 방법은 클라이언트 생성 로직을 별도 유틸 함수로 분리하고, 요청 단위로 캐싱하는 거예요. Next.js의 `cache()` 함수를 쓰면 동일 요청 내에서 인스턴스를 재사용할 수 있어요.

```typescript
// ✅ lib/supabase/server.ts
import { cache } from 'react'
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

export const createClient = cache(() => {
  const cookieStore = cookies()
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    { cookies: { getAll() { return cookieStore.getAll() } } }
  )
})
```

### RLS 정책 자체의 비효율

두 번째 원인은 RLS 정책 SQL이에요. 아래 패턴은 실제로 느려요.

```sql
-- ❌ 매 행마다 auth.uid()를 서브쿼리로 호출
CREATE POLICY "user_posts" ON posts
  USING (user_id = (SELECT auth.uid()));
```

`auth.uid()`는 PostgreSQL 세션 변수에서 읽어오는 함수예요. 서브쿼리로 감싸면 플래너가 이를 인라인으로 처리하지 못해서, 행 수가 많을수록 선형적으로 느려져요. 수정은 간단해요.

```sql
-- ✅ 직접 호출로 변경 (플래너가 상수로 처리)
CREATE POLICY "user_posts" ON posts
  USING (user_id = auth.uid());
```

이 차이 하나로 수십만 행 테이블에서 쿼리 시간이 절반 이하로 줄어드는 경우가 있어요.

### Middleware에서 세션 갱신 타이밍 문제

Supabase Auth의 세션은 JWT 토큰 기반이에요. 만료 직전 토큰은 미들웨어에서 갱신되어야 해요. 그런데 미들웨어가 올바르게 설정되지 않으면, 서버 컴포넌트에서 만료된 토큰으로 RLS 정책을 검증하다가 재인증 루프에 빠질 수 있어요.

Supabase 문서에서 권장하는 `middleware.ts` 패턴을 보면, `updateSession()` 호출이 필수예요. 이걸 빠트리면 로그인은 되어 있는데 RLS에서 `auth.uid()`가 `null`을 반환해서, 데이터가 하나도 안 오거나 에러 없이 빈 배열만 돌아와요. 조용한 실패(silent failure)죠.

---

## 원인별 비교: 어떤 케이스가 더 심각한가요?

| 원인 | 체감 성능 저하 | 디버깅 난이도 | 수정 복잡도 | 주로 나타나는 환경 |
|------|--------------|-------------|------------|-----------------|
| 클라이언트 중복 생성 | 2-5배 느려짐 | 보통 | 낮음 | 컴포넌트 많은 대시보드 |
| RLS 정책 서브쿼리 | 5-20배 느려짐 | 높음 | 낮음 | 데이터 많은 테이블 |
| 미들웨어 세션 갱신 누락 | 간헐적 전체 실패 | 매우 높음 | 보통 | 장시간 세션 유지 |
| anon key vs service key 혼용 | RLS 우회 또는 오류 | 높음 | 낮음 | 서버 액션, API 라우트 |

RLS 정책 서브쿼리 문제가 성능 충격이 가장 크고, 클라이언트 중복 생성은 규모가 커질수록 누적 효과로 심각해져요. 미들웨어 문제는 재현이 어려워서 디버깅에 시간이 제일 많이 걸리는 편이에요.

---

## 실제로 트러블슈팅할 때 이렇게 접근하세요

**시나리오 1: 대시보드 첫 로드가 3초 이상 걸릴 때**

Supabase Dashboard의 쿼리 로그(Database → Logs → Postgres Logs)에서 같은 `auth.uid()` 검증이 반복 실행되고 있는지 확인하세요. 동일 요청에서 같은 쿼리가 5회 이상 보인다면 클라이언트 중복 생성이 원인이에요. `cache()` 래퍼로 클라이언트를 단일 인스턴스로 만드는 것만으로 해결돼요.

**시나리오 2: 데이터가 많아질수록 점점 느려질 때**

테이블에 행이 늘어날수록 선형적으로 느려진다면 RLS 정책의 서브쿼리가 원인일 가능성이 높아요. `EXPLAIN ANALYZE`로 실행 계획을 확인하면 `Filter` 단계에서 `auth.uid()` 호출 횟수가 보여요. 정책을 직접 호출 방식으로 바꾸고, `user_id` 컬럼에 인덱스가 걸려 있는지도 함께 확인하세요.

**시나리오 3: 며칠에 한 번씩 갑자기 데이터가 안 올 때**

높은 확률로 세션 만료 + 미들웨어 갱신 누락이에요. `middleware.ts`에 `updateSession()` 호출이 있는지, 그리고 `matcher` 설정이 API 라우트와 서버 액션을 포함하는지 확인하세요. Supabase `@supabase/ssr` 공식 예제의 미들웨어 코드를 기준으로 비교해보면 금방 찾을 수 있어요.

**지금 당장 확인할 체크리스트:**
- `createClient`가 `React.cache()`로 감싸져 있나요?
- RLS 정책에 서브쿼리가 아닌 직접 `auth.uid()` 호출을 쓰고 있나요?
- `middleware.ts`에 `updateSession()` 호출이 있나요?
- 서버 액션에서 `service_role` 키를 실수로 쓰고 있진 않나요?

---

## 정리: RLS는 느린 게 아니라, 잘못 쓰면 느려요

- Next.js App Router에서 Supabase 클라이언트는 반드시 `React.cache()`로 단일 인스턴스를 유지해야 해요
- RLS 정책의 `auth.uid()` 서브쿼리 패턴은 대용량 테이블에서 치명적이에요. 직접 호출로 바꾸면 플래너가 최적화해요
- 미들웨어의 세션 갱신 로직은 필수예요. 빠트리면 조용한 실패가 생겨요
- 트러블슈팅 순서: DB 로그 확인 → 클라이언트 인스턴스 점검 → RLS 정책 실행 계획 확인 → 미들웨어 검증

앞으로 6-12개월 안에 Next.js와 Supabase 양쪽 모두 서버 컴포넌트 컨텍스트에서의 인증 클라이언트 관리를 더 간소화하는 방향으로 갈 거예요. Supabase는 이미 `@supabase/ssr`의 캐싱 전략을 개선하는 작업을 진행 중이고, Next.js 측에서도 `after()` API처럼 요청 생명주기를 더 명확하게 제어하는 도구가 나오고 있으니까요.

Next.js App Router Supabase RLS 적용 후 쿼리 느려졌을 때, 생각보다 간단한 코드 한 줄에서 출발하는 경우가 많아요. DB 로그 한번 열어보는 것부터 시작해 보세요.

---

*참고: Supabase 공식 클라이언트 라이브러리 문서 및 `@supabase/ssr` 초기화 패턴은 [supabase.com/ui/docs/nextjs/client](https://supabase.com/ui/docs/nextjs/client)에서 확인할 수 있어요.*

## 참고자료

1. [[트러블슈팅] Supabase Auth를 활용한 다양한 환경에서의 세션 유지](https://inyoung.dev/troubleshooting-supabase-auth/)
2. [Lobehub](https://lobehub.com/ko/skills/adaptationio-skrillz-supabase-troubleshooting)
3. [Supabase Client Libraries](https://supabase.com/ui/docs/nextjs/client)


---

*Photo by [Jonathan Borba](https://unsplash.com/@jonathanborba) on [Unsplash](https://unsplash.com/photos/a-man-sitting-in-a-chair-looking-at-his-cell-phone-0Nrq6UvFpI8)*
