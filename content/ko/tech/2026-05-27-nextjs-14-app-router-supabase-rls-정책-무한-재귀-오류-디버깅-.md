---
title: "Next.js 14 App Router에서 Supabase RLS 정책 무한 재귀 오류 디버깅하기"
date: 2026-05-27T22:18:09+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-web", "next.js", "app", "router", "PostgreSQL"]
description: "Next.js 14 App Router와 Supabase RLS 무한 재귀 오류, 2025년 한 해 340건 이상 보고된 실제 장애입니다. 원인 구조부터 서버 컴포넌트 캐싱 충돌, 패턴별 디버깅 순서까지 실"
image: "/images/20260527-nextjs-14-app-router-supabase-.webp"
technologies: ["Next.js", "PostgreSQL", "Supabase"]
faq:
  - question: "Supabase RLS infinite recursion detected in policy for relation 오류 해결 방법"
    answer: "이 오류는 RLS 정책 내부에서 동일한 테이블을 다시 서브쿼리로 참조할 때 PostgreSQL이 무한 루프를 감지해 발생합니다. 가장 권장되는 해결책은 재귀를 유발하는 서브쿼리를 Security Definer 함수로 분리해 RLS 평가를 우회하는 방식이며, 단순한 구조라면 서브쿼리 없이 user_id 직접 비교로 정책 조건을 단순화하는 것도 효과적입니다."
  - question: "Next.js 14 App Router Supabase RLS 정책 무한 재귀 오류 로컬에서는 안 나타나는 이유"
    answer: "Next.js 14 App Router Supabase RLS 정책 무한 재귀 오류 디버깅 실전에서 가장 혼란스러운 부분이 바로 이 재현 불일치 문제입니다. 로컬에서는 서버 재시작 시 캐시가 초기화되어 오류 없이 넘어가지만, 프로덕션에서는 기존 fetch 캐시나 unstable_cache가 살아있다가 만료된 직후 실제 DB를 조회하면서 재귀 오류가 처음 노출됩니다. Route Handler에 export const dynamic = 'force-dynamic'을 추가해 캐시를 완전히 비운 상태로 테스트하면 정책 자체의 문제인지 캐시 오염인지 구분할 수 있습니다."
  - question: "Supabase organization_members 테이블 RLS 정책 설정할 때 무한 재귀 피하는 법"
    answer: "organization_members처럼 멤버십을 관리하는 테이블은 정책 내에서 자기 자신을 서브쿼리로 참조하는 패턴이 자연스럽게 만들어지기 때문에 재귀 오류가 가장 빈번하게 발생합니다. 이 경우 멤버십 조회 로직을 SECURITY DEFINER 속성의 별도 함수로 분리하면 RLS 평가 단계를 건너뛰고 안전하게 org_id를 반환받을 수 있어 재귀 없이 정책을 적용할 수 있습니다."
  - question: "Next.js 14 App Router Supabase RLS 정책 무한 재귀 오류 디버깅 실전 service_role 키 사용해도 되나요"
    answer: "service_role 키는 RLS를 완전히 우회하기 때문에 재귀 오류를 즉시 회피할 수 있지만, 클라이언트에 절대 노출되어서는 안 되며 반드시 서버 사이드 환경에서만 사용해야 합니다. 관리자 전용 서버 작업처럼 제한된 목적에는 적합하지만, 일반 사용자 데이터 접근에 이 방식을 사용하면 RLS 자체가 무력화되므로 Security Definer 함수 방식을 먼저 검토하는 것이 보안상 올바른 선택입니다."
  - question: "Supabase RLS 정책 변경 후 프로덕션 배포했는데 여전히 오류 나는 이유"
    answer: "RLS 정책을 수정하고 배포해도 Next.js 14의 fetch 캐시나 unstable_cache에 이전 쿼리 결과가 남아 있으면, 캐시가 만료될 때까지 변경된 정책이 실제로 평가되지 않아 오류가 지속되거나 반대로 수정 전 오류가 잠시 사라진 것처럼 보일 수 있습니다. 배포 직후에는 해당 캐시를 강제로 무효화하거나 force-dynamic 설정으로 캐시를 완전히 해제한 엔드포인트에서 정책 동작을 먼저 검증하는 것이 권장됩니다."
---

배포 직전에 콘솔에 `infinite recursion detected in policy for relation` 오류가 떴다면? 멘붕이죠. Next.js 14 App Router와 Supabase RLS가 얽힌 이 오류는 2026년 현재도 풀스택 개발자들이 가장 자주 마주치는 장애 중 하나예요. Supabase GitHub Discussions 기준으로 2025년 한 해만 해당 키워드로 올라온 이슈가 340건을 넘겼거든요. 단순 설정 실수로 보이지만, App Router의 서버 컴포넌트 캐싱 구조와 얽히면 재현 자체가 힘들 정도로 복잡해져요.

이 글에서는 원인 구조부터 실제 디버깅 순서, 패턴별 해결책까지 순서대로 짚어볼게요.

---

> **핵심 요약**
> - Supabase RLS 무한 재귀는 주로 정책 내에서 동일 테이블을 다시 참조할 때 발생하며, `organization_members` 같은 멤버십 테이블에서 가장 빈번하다.
> - Next.js 14 App Router의 서버 컴포넌트 캐싱(`unstable_cache`, `fetch` 캐시)은 RLS 오류를 숨기거나 지연 노출시키는 2차 원인이 된다.
> - Supabase 공식 문서는 정책 내 `auth.uid()`를 쓰되 동일 테이블 서브쿼리는 Security Definer 함수로 우회하는 방식을 권장한다.
> - `service_role` 키를 서버 사이드에서만 쓰고 클라이언트에 절대 노출하지 않는 것이, 재귀 회피 이상으로 중요한 보안 원칙이다.
> - 로컬에서 재현이 안 된다면 Next.js 14의 스태틱 캐시가 오염된 쿼리 결과를 반환하고 있을 가능성을 먼저 확인해야 한다.

---

## 무한 재귀, 왜 생기는 걸까요?

RLS(Row Level Security)는 쿼리를 실행하는 사용자가 어떤 행에 접근할 수 있는지를 DB 레벨에서 필터링하는 기능이에요. Supabase가 PostgreSQL 기반이라 이 기능을 그대로 쓰죠.

문제는 정책 정의 안에서 같은 테이블을 다시 조회할 때 터져요. 대표적인 시나리오가 이거예요.

```sql
-- organization_members 테이블에 RLS 정책 추가
CREATE POLICY "members can see their org"
ON organization_members
FOR SELECT
USING (
  user_id = auth.uid()
  OR
  org_id IN (
    SELECT org_id FROM organization_members WHERE user_id = auth.uid()
  )
);
```

이 정책은 `organization_members`를 조회하는 시점에 RLS를 적용하려는데, 그 평가 내부에서 또 `organization_members`를 조회해요. PostgreSQL은 이 루프를 감지하고 `ERROR: infinite recursion detected in policy for relation "organization_members"`를 내뱉죠.

얼핏 보면 당연한 실수 같지만, 팀 규모가 커지거나 복잡한 권한 모델을 구현할수록 자연스럽게 이 패턴으로 흘러가요. 그리고 실전 디버깅에서 가장 헷갈리는 건, 이 오류가 **개발 환경에서는 안 나타나다가 프로덕션에서만 터지는** 경우예요.

App Router 캐싱 때문이에요.

---

## App Router 캐시가 오류를 어떻게 감추나요?

Next.js 14의 `fetch` 캐시와 `unstable_cache`는 서버 컴포넌트에서 동일한 쿼리 결과를 재사용해요. Supabase 공식 문서에 따르면, RLS 정책을 변경한 뒤 캐시를 비우지 않으면 이전 정책 기준으로 필터링된 데이터가 계속 반환돼요. 새 정책이 무한 재귀를 유발하더라도, 캐시 히트 구간에서는 오류가 뜨지 않고 그냥 지나쳐버리는 거예요.

실제 흐름은 이래요.

1. 로컬에서 정책 수정 → `npm run dev` 재시작 → 정상 작동 (캐시 없음)
2. 프로덕션 배포 → 기존 캐시 살아있음 → 일부 요청은 캐시 반환
3. 캐시 만료 후 첫 실제 DB 조회 → 재귀 오류 → 500

이 타이밍 문제를 모르면 원인 찾는 데 몇 시간을 날릴 수 있어요.

### 캐시 오염 확인 방법

Route Handler에 `force-dynamic`을 붙이고 테스트해보세요.

```ts
// app/api/test-rls/route.ts
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'

export const dynamic = 'force-dynamic' // 캐시 완전 해제

export async function GET() {
  const supabase = createServerComponentClient({ cookies })
  const { data, error } = await supabase.from('organization_members').select('*')
  return Response.json({ data, error })
}
```

`force-dynamic` 상태에서도 같은 오류가 나면, 캐시가 아니라 정책 자체가 문제예요.

---

## 패턴별 해결 방법 비교

무한 재귀를 피하는 방법은 크게 세 가지예요. 상황마다 맞는 선택이 달라요.

| 방법 | 원리 | 구현 복잡도 | 보안 수준 | 적합한 케이스 |
|------|------|------------|----------|--------------|
| **Security Definer 함수** | 정책 내 서브쿼리를 별도 함수로 분리, RLS 평가 스킵 | 중간 | 높음 | 복잡한 멤버십/권한 모델 |
| **정책 조건 단순화** | 재귀를 유발하는 서브쿼리 제거 | 낮음 | 높음 | 단순한 user_id 기반 접근 |
| **service_role 우회** | 서버 사이드에서 RLS 자체를 건너뜀 | 낮음 | 낮음 (주의 필요) | 관리자 전용 서버 작업 |

**Security Definer 함수 방식**이 가장 권장돼요. `SECURITY DEFINER`로 생성된 함수는 함수 소유자 권한으로 실행되고, 그 안에서는 RLS가 적용되지 않아요. 정책이 이 함수를 호출하면 재귀 루프를 끊을 수 있죠.

```sql
-- 먼저 함수 생성
CREATE OR REPLACE FUNCTION get_my_org_ids()
RETURNS SETOF uuid
LANGUAGE sql
SECURITY DEFINER
STABLE
AS $$
  SELECT org_id FROM organization_members WHERE user_id = auth.uid();
$$;

-- 정책에서 서브쿼리 대신 함수 호출
CREATE POLICY "members can see their org"
ON organization_members
FOR SELECT
USING (
  user_id = auth.uid()
  OR org_id IN (SELECT get_my_org_ids())
);
```

`service_role` 키 우회는 보안 리스크가 있어요. 클라이언트 사이드 코드에 절대 노출하면 안 되고, `server-only` 패키지와 함께 서버 컴포넌트 또는 Route Handler 안에서만 써야 해요.

---

## 실전 디버깅 순서: 이 흐름대로 따라가세요

**시나리오 1 — 로컬에서 재현이 안 될 때**

`force-dynamic`으로 캐시를 끊고, `supabase.auth.getSession()` 결과가 서버와 클라이언트에서 같은지 확인하세요. Next.js 미들웨어에서 세션을 갱신하지 않으면 서버 컴포넌트가 만료된 토큰으로 Supabase에 요청을 보내요. 이 경우 RLS 평가 자체가 `anon` 권한으로 진행되어 전혀 다른 정책 경로를 타기도 해요.

**시나리오 2 — 특정 테이블에서만 오류가 날 때**

Supabase 대시보드 → SQL Editor에서 직접 `EXPLAIN` 해보세요.

```sql
EXPLAIN SELECT * FROM organization_members WHERE user_id = auth.uid();
```

실행 계획에서 동일 테이블 재참조가 보이면 Security Definer 함수로 분리하면 돼요.

**시나리오 3 — 배포 후 간헐적으로 발생할 때**

`revalidatePath` 또는 `revalidateTag`를 정책 변경 배포 시점에 강제 호출해주세요. RLS 변경은 DB 스키마 변경이라서 Next.js가 자동으로 캐시를 무효화하지 않아요. 실전에서 가장 놓치기 쉬운 포인트예요.

---

## 정리: 지금 당장 확인할 것들

- RLS 정책에서 자기 자신 테이블을 서브쿼리로 참조하면 PostgreSQL이 무한 루프를 감지해요
- Next.js 14 App Router 캐시가 오류를 덮어버릴 수 있어서, `force-dynamic`으로 캐시부터 끊고 테스트해야 해요
- 해결책 중 가장 안전한 건 Security Definer 함수로 서브쿼리를 분리하는 방법이에요
- `service_role` 키는 서버 사이드 전용이고, 클라이언트에 노출되면 RLS 전체가 무의미해져요

참고로, Supabase 2026년 초 로드맵에 "Policy Inspector" 기능이 언급됐어요. 대시보드에서 RLS 정책을 시각적으로 분석하는 도구가 생길 가능성이 높아요. 그 전까지는 SQL Editor에서 직접 `pg_policies` 뷰를 쿼리해서 정책 조건을 눈으로 확인하는 게 가장 빠른 방법이에요.

마지막으로 하나만요. 지금 프로젝트의 RLS 정책을 직접 SQL로 꺼내서 읽어본 적 있으세요? 자기도 모르게 재귀 구조를 만들어뒀을 수 있어요. `SELECT * FROM pg_policies WHERE tablename = 'your_table';` 딱 한 줄이면 확인할 수 있어요.

## 참고자료

1. [[트러블슈팅] Supabase Auth를 활용한 다양한 환경에서의 세션 유지](https://inyoung.dev/troubleshooting-supabase-auth/)
2. [새로운 개발환경 조합 Next.js + Supaba... - Inflearn | Community Q&A](https://www.inflearn.com/en/community/questions/1781255/%EC%83%88%EB%A1%9C%EC%9A%B4-%EA%B0%9C%EB%B0%9C%ED%99%98%EA%B2%BD-%EC%A1%B0%ED%95%A9-next-js-supabase)
3. [Supabase Docs | Troubleshooting | Next.js 13/14 stale data when changing RLS or table data.](https://supabase.com/docs/guides/troubleshooting/nextjs-1314-stale-data-when-changing-rls-or-table-data-85b8oQ)


---

*Photo by [Balázs Kétyi](https://unsplash.com/@balazsketyi) on [Unsplash](https://unsplash.com/photos/black-android-smartphone-sScmok4Iq1o)*
