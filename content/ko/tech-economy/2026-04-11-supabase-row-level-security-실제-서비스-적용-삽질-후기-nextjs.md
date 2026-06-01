---
title: "Supabase Row Level Security Next.js 연동 실제 서비스 적용 삽질 후기: 세션 컨텍스트와 UUID 타입 불일치 문제"
date: 2026-04-11T19:52:36+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-security", "supabase", "row", "level", "Next.js"]
description: "Supabase RLS 적용 후 데이터가 사라지는 이유, anon 키와 정책 미설정의 관계부터 Next.js 연동 시 실제 삽질 포인트까지 서비스 경험 기반으로 분석했습니다."
image: "/images/20260411-supabase-row-level-security-실제.webp"
technologies: ["Next.js", "PostgreSQL", "Supabase"]
faq:
  - question: "Supabase RLS 켰는데 데이터가 빈 배열로 오고 에러가 없어요"
    answer: "Supabase Row Level Security를 활성화하면 정책이 없는 테이블은 기본적으로 모든 데이터 접근을 차단하며, 에러 대신 빈 배열을 반환하는 것이 정상 동작입니다. RLS 정책을 명시적으로 생성하거나, 서버 컴포넌트에서 세션 컨텍스트가 올바르게 전달되는지 먼저 확인해야 합니다."
  - question: "Supabase Row Level Security 실제 서비스 적용 삽질 후기 Next.js 연동에서 auth-helpers와 @supabase/ssr 차이가 뭔가요"
    answer: "Supabase Row Level Security 실제 서비스 적용 삽질 후기 Next.js 연동 사례에 따르면, @supabase/auth-helpers-nextjs는 Pages Router 기반으로 설계되어 App Router 서버 컴포넌트에서 세션을 불안정하게 읽습니다. @supabase/ssr 패키지는 Next.js의 cookies() API와 직접 연결되어 서버 컴포넌트에서 auth.uid()가 올바르게 동작하므로, App Router 환경에서는 반드시 @supabase/ssr을 사용해야 합니다."
  - question: "Supabase RLS 정책 있는데도 데이터 안 나오는 이유"
    answer: "RLS 정책이 존재해도 세션 컨텍스트가 서버에 제대로 전달되지 않으면 auth.uid()가 null을 반환해 모든 쿼리가 빈 결과를 돌려줍니다. 또한 user_id 컬럼 타입이 text인데 auth.uid()가 uuid를 반환하는 타입 불일치도 조용히 실패를 유발하므로, 컬럼 타입을 uuid로 맞추거나 명시적 캐스팅(auth.uid()::text)을 적용해야 합니다."
  - question: "Supabase service_role 키 클라이언트에서 써도 되나요"
    answer: "service_role 키는 RLS를 완전히 우회하기 때문에 브라우저 클라이언트에 노출되면 데이터베이스 전체가 보안 위협에 노출됩니다. 반드시 API Route나 Server Action 같은 서버 사이드 환경에서만 사용해야 하며, 환경변수도 NEXT_PUBLIC_ 접두사 없이 서버 전용으로 관리해야 합니다."
  - question: "Supabase Row Level Security 실제 서비스 적용 삽질 후기 Next.js 연동 서버 컴포넌트 세션 읽기 방법"
    answer: "Supabase Row Level Security 실제 서비스 적용 삽질 후기 Next.js 연동 경험을 바탕으로 정리하면, createServerClient를 사용해 Next.js의 cookies()에서 쿠키 값을 읽어 클라이언트를 초기화하는 방식이 공식 권장 패턴입니다. 이렇게 구성해야 서버 컴포넌트에서 인증된 사용자의 세션이 RLS 정책에 올바르게 반영됩니다."
---

RLS 정책을 켰는데 데이터가 하나도 안 나와요. 근데 에러도 없어요.

Next.js에 Supabase를 붙여본 개발자라면 딱 한 번씩은 겪어봤을 거예요. Row Level Security(RLS)는 설정하면 끝나는 게 아니라, "왜 안 되는지"를 이해해야 쓸 수 있는 기능이거든요. 2026년 현재 Supabase는 GitHub 누적 스타 7만 개를 넘어섰고, 스타트업 백엔드 선택지 1-2위를 다투고 있어요. 그만큼 RLS 삽질 사례도 폭발적으로 늘고 있고요. 이 글은 실제 서비스 적용 과정에서 정말 많이 막히는 포인트를 데이터 기반으로 정리한 분석이에요.

> **핵심 요약**
> - Supabase RLS가 적용된 상태에서 `anon` 키로 쿼리하면 정책이 없는 테이블은 데이터를 **전혀 반환하지 않으며**, 이것이 가장 흔한 삽질 원인이에요.
> - Next.js App Router 환경에서는 `@supabase/auth-helpers-nextjs` 대신 `@supabase/ssr` 패키지를 써야 서버 컴포넌트에서 세션이 올바르게 읽혀요 (꾸리 기술 블로그, 2026).
> - RLS 정책은 `service_role` 키를 쓰는 서버 사이드 작업에는 **우회되므로**, 클라이언트 노출 없이 관리 작업을 처리할 수 있어요.
> - 정책 작성 시 `auth.uid()`와 테이블 컬럼 타입 불일치(UUID vs text)가 조용히 실패를 유발하는 두 번째 주요 원인이에요.

---

## RLS가 뭔지는 알겠는데, 왜 이렇게 어려운 거예요?

Row Level Security는 PostgreSQL의 행 단위 접근 제어 기능이에요. 같은 테이블이라도 "누가 보느냐"에 따라 보이는 행이 달라지게 만드는 거죠.

Supabase는 이걸 기본 인증 시스템과 엮어서, `auth.uid()`라는 함수로 현재 로그인한 사용자의 UUID를 가져와요. 그 UUID를 기준으로 "이 행은 이 사람만 볼 수 있다"는 정책을 만드는 구조예요.

문제는 여기서 시작돼요. Supabase의 RLS는 **기본적으로 모든 걸 막아요.** RLS를 켜는 순간, 정책이 없으면 누구도 아무것도 못 봐요. 에러가 나는 게 아니라, 그냥 빈 배열이 와요. `[]`. 이게 너무 조용해서 처음엔 버그인지도 몰라요.

Medium의 debug_senpai 분석에 따르면, RLS 관련 이슈의 절반 이상은 정책 부재가 아니라 **정책은 있는데 세션 컨텍스트가 서버에 제대로 전달되지 않은 경우**라고 해요. Next.js App Router가 도입되면서 이 문제가 더 도드라졌고, 그게 바로 `@supabase/ssr` 패키지가 나온 배경이에요.

### auth-helpers vs @supabase/ssr: 뭐가 다른 거예요?

기존의 `@supabase/auth-helpers-nextjs`는 Pages Router 시절에 설계된 패키지예요. App Router의 서버 컴포넌트는 쿠키를 직접 다루는 방식이 달라서, auth-helpers로는 서버 컴포넌트에서 세션을 읽는 게 불안정했어요.

`@supabase/ssr`은 이 문제를 해결하려고 만들어진 패키지예요. 쿠키 읽기/쓰기를 커스텀할 수 있게 열어줘서, Next.js의 `cookies()` API와 깔끔하게 연결돼요. 꾸리 기술 블로그(2026년 4월)에서 정리한 것처럼, App Router 기준으로는 `@supabase/ssr`이 공식 권장 방식이에요.

```ts
// 서버 컴포넌트용 클라이언트 예시
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

export function createClient() {
  const cookieStore = cookies()
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    { cookies: { get: (name) => cookieStore.get(name)?.value } }
  )
}
```

이렇게 해야 서버 컴포넌트에서 `auth.uid()`가 올바른 값을 가져와요. 이걸 안 하면 RLS 정책이 아무리 맞게 짜여 있어도 세션이 `null`이라 모든 쿼리가 빈 결과를 반환해요.

---

## 실전에서 자주 걸리는 삽질 세 가지

### 삽질 1: UUID 타입 불일치

가장 조용하고 잔인한 버그예요.

```sql
-- 이렇게 짜면 작동 안 해요
CREATE POLICY "user_posts" ON posts
  FOR SELECT USING (user_id = auth.uid());
```

`auth.uid()`는 `uuid` 타입을 반환해요. 근데 `user_id` 컬럼이 `text`로 만들어져 있으면? 에러도 없이 그냥 빈 결과가 와요. PostgreSQL이 암묵적으로 타입을 맞춰줄 것 같지만, RLS 정책에서는 그게 안 돼요. 컬럼 타입을 `uuid`로 바꾸거나, 명시적 캐스팅(`auth.uid()::text`)을 해야 해요.

### 삽질 2: 클라이언트/서버 클라이언트 혼용

Next.js에서 Supabase 클라이언트는 두 종류예요. 브라우저에서 쓰는 것, 서버에서 쓰는 것. 이 둘은 쿠키 처리 방식이 달라서, 서버 컴포넌트에서 브라우저용 클라이언트를 쓰면 세션이 없어요. RLS 정책이 `auth.uid()`를 기준으로 동작하면 전부 막혀요.

### 삽질 3: service_role 키를 클라이언트에 노출

반대 방향 삽질도 있어요. RLS가 안 풀리니까 `service_role` 키로 클라이언트를 만들면 데이터가 나오긴 해요. 그런데 `service_role` 키는 RLS를 **완전히 우회**해요. 이 키가 브라우저에 노출되면 DB 전체가 뚫리는 거예요. 서버 사이드(API Route, Server Action)에서만 써야 해요.

---

## RLS 정책 패턴 비교: 세 가지 접근법

| 패턴 | 사용 위치 | RLS 적용 | 보안 수준 | 적합한 경우 |
|------|----------|----------|----------|------------|
| `anon` 키 + RLS 정책 | 클라이언트/서버 | ✅ 적용 | 높음 | 사용자별 데이터 분리 |
| `service_role` 키 | 서버(API Route만) | ❌ 우회 | 최고 (노출 금지) | 관리자 작업, 마이그레이션 |
| RLS 없이 `anon` 키 | 어디서든 | ❌ 없음 | 매우 낮음 | 공개 읽기 전용 데이터만 |

Supabase 공식 문서는 프로덕션 환경에서 모든 테이블에 RLS를 켜는 걸 권장해요. `anon` 키만으로도 충분히 안전한 서비스를 만들 수 있고, `service_role` 키는 서버에만 격리해야 해요.

---

## 실제 서비스에 적용할 때 순서

**상황 1: 로그인한 사용자만 자기 데이터를 볼 수 있어야 할 때**
- 테이블에 `user_id uuid` 컬럼 추가, 타입 반드시 `uuid`로
- `CREATE POLICY ... USING (user_id = auth.uid())` 작성
- 서버 컴포넌트에서 `@supabase/ssr`로 클라이언트 생성 확인

**상황 2: 공개 게시판인데 쓰기는 로그인한 사람만 할 때**
- SELECT 정책: `USING (true)` — 누구나 읽기 가능
- INSERT 정책: `WITH CHECK (auth.uid() IS NOT NULL)` — 로그인한 사람만 쓰기

**상황 3: 관리자 기능이 있을 때**
- 별도 `roles` 테이블에 관리자 여부 저장
- `USING (EXISTS (SELECT 1 FROM roles WHERE user_id = auth.uid() AND role = 'admin'))` 형태로 작성
- `service_role` 키를 클라이언트에 넘기지 마세요

---

## 앞으로 어떻게 될까요?

Supabase는 2026년 현재 RLS 정책 테스트를 더 쉽게 할 수 있는 대시보드 기능을 베타로 제공하고 있어요. SQL 에디터에서 특정 사용자로 가장해 쿼리를 테스트할 수 있는 기능이에요. 이게 안정화되면 삽질 시간이 절반으로 줄어들 거예요.

Next.js Server Actions가 더 보편화되면서, RLS와 서버 액션을 결합한 패턴이 표준으로 자리잡을 가능성이 높아요. 클라이언트에서 Supabase를 직접 호출하는 방식보다, 서버 액션을 통해 검증 후 호출하는 방식이 더 안전하니까요.

---

한 줄로 요약하면 이거예요. **RLS는 강하지만, Next.js 연동에서는 세션 컨텍스트가 핵심이에요.** `@supabase/ssr` 설정이 맞는지 먼저 확인하고, 그다음에 정책을 짜세요. 순서가 바뀌면 3일이 날아가요.

참고로 지금 바로 확인할 게 하나 있어요. 여러분 팀의 Supabase 설정에서 `service_role` 키가 혹시 프론트엔드 환경변수에 들어가 있진 않은지, 지금 체크해보세요.

## 참고자료

1. [Supabase auth-helpers 말고 @supabase/ssr 써야 하는 이유 (Next.js App Router 기준) - 꾸리](https://www.kko-kkuri.com/2026/04/08/supabase-ssr-vs-auth-helpers-nextjs/)
2. [Supabase Row Level Security Explained With Real Examples | by debug_senpai | Medium](https://medium.com/@jigsz6391/supabase-row-level-security-explained-with-real-examples-6d06ce8d221c)
3. [Supabase, 왜 주목받나?](https://matae0712.tistory.com/30)


---

*Photo by [Drew Williams](https://unsplash.com/@kingswagger) on [Unsplash](https://unsplash.com/photos/flavor-list-life-is-too-short-to-be-bland-screengrab-oD_qxhNrSB8)*
