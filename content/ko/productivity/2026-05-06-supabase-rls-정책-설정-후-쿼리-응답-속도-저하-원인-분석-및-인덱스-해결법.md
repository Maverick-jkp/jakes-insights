---
title: "Supabase RLS 정책 설정 후 쿼리 응답 속도 저하 원인과 인덱스 해결법"
date: 2026-05-06T21:07:37+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-web", "supabase", "rls", "\uc778\ub371\uc2a4", "PostgreSQL"]
description: "Supabase RLS 활성화 후 쿼리가 5배 느려지는 원인은 auth.uid() 컬럼의 인덱스 누락으로 인한 Seq Scan입니다. 100만 행 테이블에서 수 초까지 늘어나는 병목을 인덱스로 해결하"
image: "/images/20260506-supabase-rls-정책-설정-후-쿼리-응답-속도-.webp"
technologies: ["PostgreSQL", "Supabase"]
faq:
  - question: "Supabase RLS 켰더니 쿼리 갑자기 느려진 이유"
    answer: "RLS를 활성화하면 PostgreSQL이 각 행마다 정책 표현식을 평가하는데, user_id 같은 필터 컬럼에 인덱스가 없으면 테이블 전체를 읽는 Seq Scan이 발생합니다. 100만 행 기준으로 인덱스 없이 800ms~2초씩 걸리던 쿼리가 인덱스 하나만 추가해도 3~15ms로 줄어드는 경우가 일반적입니다."
  - question: "Supabase RLS 정책 설정 후 쿼리 응답 속도 저하 원인 분석 및 인덱스 해결법이 궁금해요"
    answer: "Supabase RLS 정책 설정 후 쿼리 응답 속도 저하 원인 분석 및 인덱스 해결법의 핵심은 EXPLAIN ANALYZE로 실행 계획을 확인해 Seq Scan 여부를 파악한 뒤, RLS 정책의 USING 절에 사용된 컬럼(예: user_id)에 인덱스를 추가하는 것입니다. 단일 컬럼 인덱스만 적용해도 응답 시간을 10분의 1 이하로 줄인 사례가 다수 보고되고 있습니다."
  - question: "PostgreSQL EXPLAIN ANALYZE에서 Seq Scan 나오면 어떻게 해야 하나요"
    answer: "Seq Scan은 인덱스를 타지 못하고 테이블 전체를 읽고 있다는 신호로, WHERE 조건이나 RLS 정책에 사용된 컬럼에 인덱스가 없을 때 발생합니다. 해당 컬럼에 CREATE INDEX를 적용하면 실행 계획이 Index Scan으로 바뀌면서 쿼리 속도가 크게 개선됩니다."
  - question: "RLS 정책에 서브쿼리 쓰면 성능에 문제 생기나요"
    answer: "RLS 정책의 USING 절에 서브쿼리를 포함하면 쿼리가 실행될 때마다 서브쿼리도 함께 실행되어 성능이 크게 저하될 수 있습니다. 서브쿼리가 참조하는 테이블에도 인덱스가 없으면 여러 테이블을 동시에 풀스캔하게 되므로, 가능하면 단순 컬럼 비교로 정책을 작성하고 관련 컬럼에 인덱스를 추가하는 것이 좋습니다."
  - question: "Supabase RLS 정책 설정 후 쿼리 응답 속도 저하 원인 분석 및 인덱스 해결법 실무 적용 순서"
    answer: "Supabase RLS 정책 설정 후 쿼리 응답 속도 저하 원인 분석 및 인덱스 해결법을 실무에 적용할 때는 먼저 EXPLAIN ANALYZE로 느린 쿼리의 실행 계획을 확인하고, Seq Scan이 발생하는 컬럼을 파악한 뒤 단일 컬럼 인덱스부터 순차적으로 추가하는 것이 권장됩니다. 정렬 조건이 포함된 쿼리라면 복합 인덱스나 부분 인덱스까지 고려하면 추가적인 성능 향상을 기대할 수 있습니다."
aliases:
  - "/tech/2026-05-06-supabase-rls-정책-설정-후-쿼리-응답-속도-저하-원인-분석-및-인덱스-해결법/"

---

RLS를 켰더니 쿼리가 5배 느려졌어요. 보안을 강화했을 뿐인데 앱이 갑자기 버벅거리기 시작해요. Supabase를 쓰는 팀들이 가장 많이 겪는 퍼포먼스 병목 중 하나가 바로 이 문제예요. 원인은 생각보다 단순하지만, 모르면 며칠을 날릴 수 있어요.

> **Key Takeaways**
> - RLS 정책을 활성화하면 PostgreSQL이 각 행마다 정책 표현식을 평가하며, 인덱스가 없을 경우 전체 테이블 스캔(Seq Scan)이 발생해 쿼리 속도가 수 배 느려진다.
> - `auth.uid()`나 `user_id` 같은 필터 컬럼에 인덱스가 없으면, 100만 행 테이블에서 단순 SELECT 하나가 수백 밀리초에서 수 초까지 늘어날 수 있다.
> - Supabase 공식 Database Advisors(Performance Advisor)는 RLS 비활성화 테이블과 인덱스 누락을 자동 감지해 경고를 띄운다.
> - `EXPLAIN ANALYZE`로 실행 계획을 확인하면 문제 지점을 정확히 잡을 수 있고, 적절한 인덱스 하나로 응답 시간을 10분의 1 이하로 줄인 사례가 다수 보고되고 있다.

---

## RLS가 느려지는 이유, 맥락부터 짚어볼게요

Row Level Security(RLS)는 PostgreSQL이 제공하는 행 단위 접근 제어 기능이에요. Supabase는 이걸 기본 보안 레이어로 쓰고, 공개 테이블에 RLS가 꺼져 있으면 Database Advisors가 경고(`0013_rls_disabled_in_public`)를 띄울 정도로 중요하게 다뤄요.

그런데 RLS를 켜는 순간 PostgreSQL 내부에서 뭔가 달라져요. 쿼리를 실행할 때마다 해당 사용자가 각 행에 접근할 수 있는지를 정책 표현식으로 검사해요. 예를 들어 이런 정책이 있다고 해봐요.

```sql
CREATE POLICY "user can view own data"
ON posts
FOR SELECT
USING (user_id = auth.uid());
```

겉으로는 단순해 보이죠. 그런데 PostgreSQL 입장에선 `posts` 테이블을 훑으면서 모든 행에 대해 `user_id = auth.uid()`를 평가해야 해요. `user_id` 컬럼에 인덱스가 없으면? 테이블 전체를 처음부터 끝까지 읽어야 하는 Seq Scan이 발생해요.

Supabase가 RLS를 본격적으로 밀기 시작한 건 2023년 이후예요. 그 전엔 많은 팀이 `service_role` 키로 모든 걸 처리하거나, 아예 애플리케이션 레이어에서 필터링했거든요. 그러다 Supabase가 Auth와 RLS를 더 깊게 통합하면서 자연스럽게 RLS 사용이 늘었고, 덩달아 이 성능 문제도 수면 위로 올라왔어요. 2026년 현재 Supabase는 월간 활성 프로젝트 수가 100만 개를 넘어선 상황이고(Supabase 공식 블로그, 2025년 11월 기준), 그만큼 RLS 관련 퍼포먼스 이슈도 커뮤니티에서 가장 자주 올라오는 주제 중 하나예요.

---

## 원인 해부: 어디서 느려지는 건가요?

### Seq Scan vs Index Scan: 실행 계획이 말해주는 것

느림의 핵심은 쿼리 실행 계획이에요. RLS 정책이 붙은 쿼리를 `EXPLAIN ANALYZE`로 뜯어보면 바로 보여요.

```sql
EXPLAIN ANALYZE
SELECT * FROM posts WHERE true;
```

결과에 `Seq Scan on posts`가 보이면 인덱스를 못 타고 있다는 신호예요. PostgreSQL은 RLS 정책의 `USING` 절을 쿼리의 `WHERE` 조건처럼 처리하는데, 그 조건에 쓰인 컬럼에 인덱스가 없으면 전체 스캔이에요.

10만 행 테이블에서 Seq Scan이 발생하면 보통 50~200ms 정도 걸려요. 100만 행이면 500ms~2초도 나와요. 반면 인덱스를 타면 같은 쿼리가 1~5ms로 줄어드는 경우가 일반적이에요. 거의 100배 차이죠.

### `auth.uid()` 함수 호출 비용

두 번째 원인은 `auth.uid()` 자체예요. 이 함수는 매 쿼리 실행마다 현재 JWT에서 사용자 ID를 파싱해요. 보통 한 번 호출하는 비용은 작지만, RLS 정책이 여러 테이블에 걸쳐 있고 조인이 복잡할수록 호출 횟수가 늘어요. PostgreSQL 15 이후론 이 함수가 `STABLE`로 최적화되어 같은 트랜잭션 내에선 한 번만 평가되지만, 구버전 Supabase 인스턴스나 특정 설정에선 여전히 반복 호출이 발생해요.

### 정책 표현식의 복잡도

정책이 단순한 컬럼 비교가 아니라 서브쿼리를 포함할 때 문제가 심각해져요.

```sql
-- 이렇게 쓰면 위험해요
USING (
  user_id IN (
    SELECT user_id FROM team_members WHERE team_id = auth.uid()
  )
);
```

이런 정책은 쿼리마다 서브쿼리를 실행해요. `team_members`에 인덱스가 없으면 두 테이블을 동시에 풀스캔해요. 페이지 하나 로드하는 데 쿼리가 5개만 붙어도 서버가 버텨내기 힘들어요.

### 인덱스 전략 비교

| 인덱스 전략 | 적용 상황 | 예시 쿼리 속도 (100만 행 기준) | 주의사항 |
|-------------|-----------|-------------------------------|----------|
| 인덱스 없음 | 기본 상태 | 800ms ~ 2,000ms | RLS 켜는 순간 즉시 느려짐 |
| 단일 컬럼 인덱스 (`user_id`) | 대부분의 기본 RLS 정책 | 3ms ~ 15ms | 가장 빠른 개선, 첫 번째로 적용 |
| 복합 인덱스 (`user_id`, `created_at`) | 정렬 포함 쿼리 | 2ms ~ 10ms | 컬럼 순서가 성능에 영향 |
| 부분 인덱스 (Partial Index) | 특정 조건의 데이터만 접근 | 1ms ~ 5ms | `WHERE is_deleted = false` 같은 조건과 조합 시 효과적 |
| 함수 기반 인덱스 | `auth.uid()` 직접 비교 | 2ms ~ 8ms | PostgreSQL 버전에 따라 지원 범위 다름 |

---

## 실제로 이렇게 고쳐요

### 가장 먼저: 인덱스 추가

RLS 정책의 `USING` 절에서 쓰는 컬럼에 인덱스를 붙여요. 이게 전부예요. 정말 단순해요.

```sql
-- user_id 기반 정책이라면
CREATE INDEX idx_posts_user_id ON posts(user_id);

-- 정렬까지 포함한다면
CREATE INDEX idx_posts_user_id_created ON posts(user_id, created_at DESC);
```

Supabase의 Database Advisors(`performance_advisor`)는 이런 인덱스 누락을 자동으로 감지해서 대시보드에 표시해줘요. Supabase 공식 문서(database-advisors)에 따르면, 어드바이저가 추천하는 인덱스를 적용했을 때 평균 쿼리 시간이 절반 이하로 줄어드는 경우가 보고돼요.

### `security_definer` 함수로 복잡한 정책 분리

서브쿼리가 들어간 복잡한 정책은 함수로 빼는 게 좋아요.

```sql
CREATE OR REPLACE FUNCTION is_team_member(team_id uuid)
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
STABLE
AS $$
  SELECT EXISTS (
    SELECT 1 FROM team_members
    WHERE team_members.team_id = $1
    AND team_members.user_id = auth.uid()
  );
$$;

-- 정책에선 이렇게 간단하게
CREATE POLICY "team member access"
ON posts FOR SELECT
USING (is_team_member(team_id));
```

`STABLE` 표시를 붙이면 같은 트랜잭션 내에서 PostgreSQL이 함수 결과를 캐싱해요. 반복 호출 비용을 줄일 수 있어요.

### EXPLAIN ANALYZE를 습관으로

코드 리뷰할 때 RLS 정책을 추가하면 반드시 `EXPLAIN ANALYZE`를 같이 붙여서 실행 계획을 확인하는 걸 팀 컨벤션으로 잡는 게 좋아요. Seq Scan이 보이면 인덱스부터 의심해요.

---

## 실무 적용: 어떤 순서로 접근할까요?

**첫 번째 시나리오: 기존 프로젝트에 RLS를 처음 켰을 때**

이미 데이터가 쌓인 테이블에 RLS를 켜면 즉시 느려져요. 가장 먼저 Supabase 대시보드 → Database → Advisors에서 퍼포먼스 경고를 확인하세요. 어드바이저가 인덱스 추천을 자동으로 만들어줘요. 추천대로 인덱스를 만들고 `EXPLAIN ANALYZE`로 검증하면 돼요.

**두 번째 시나리오: 신규 프로젝트에서 처음부터 RLS를 설계할 때**

스키마를 짤 때부터 RLS 정책에서 쓸 컬럼을 정하고, 그 컬럼에 인덱스를 미리 붙여요. 나중에 고치는 것보다 훨씬 쉬워요. 특히 `user_id`, `org_id`, `tenant_id` 같은 멀티테넌시 키 컬럼은 인덱스를 달아야 해요.

**세 번째 시나리오: 복잡한 조인과 RLS가 얽힐 때**

여러 테이블을 조인하는 쿼리에 각 테이블마다 RLS가 붙으면 실행 계획이 폭발적으로 복잡해져요. 이땐 뷰(View)나 `security_definer` 함수로 정책을 격리하는 방법을 써요. 복잡도를 한 곳에서 관리하면 디버깅도 쉬워지고 성능도 잡을 수 있어요.

**지켜봐야 할 신호:**
- Supabase 대시보드의 Slow Query 로그에 같은 쿼리가 반복 등장하면 RLS 정책을 먼저 의심해요.
- 신규 기능 출시 후 갑자기 API 응답이 느려졌다면 그 기능에 추가된 정책 표현식을 뜯어봐요.

---

## 마무리: 보안과 속도는 트레이드오프가 아니에요

한 줄로 요약하면 이래요. **정책이 필터링하는 컬럼에 인덱스가 없으면 느려진다.**

- RLS는 PostgreSQL의 `WHERE` 조건처럼 작동하고, 인덱스 없는 컬럼은 Seq Scan을 유발해요.
- `EXPLAIN ANALYZE`로 Seq Scan을 확인하고, 해당 컬럼에 인덱스를 추가하면 대부분 해결돼요.
- 복잡한 서브쿼리 정책은 `STABLE` + `SECURITY DEFINER` 함수로 분리해요.
- Supabase Database Advisors를 주기적으로 확인하면 문제가 생기기 전에 잡을 수 있어요.

앞으로 6~12개월 안에 Supabase는 RLS 정책 분석 툴을 더 강화할 가능성이 높아요. 이미 Performance Advisor가 자동 인덱스 추천을 제공하고 있고, 쿼리 단위 RLS 비용 측정 기능도 로드맵에 올라와 있거든요. 도구가 더 좋아지더라도, 인덱스 설계를 제대로 이해하는 개발자가 훨씬 빠르게 문제를 잡아낼 수 있어요.

지금 여러분 프로젝트의 `EXPLAIN ANALYZE` 결과에 Seq Scan이 몇 개나 있나요?

## 참고자료

1. [Performance and Security Advisors | Supabase Docs](https://supabase.com/docs/guides/database/database-advisors?lint=0013_rls_disabled_in_public)


---

*Photo by [Microsoft Copilot](https://unsplash.com/@microsoftcopilot) on [Unsplash](https://unsplash.com/photos/woman-planting-a-small-houseplant-in-a-pot-MJLy1fUvX_w)*
