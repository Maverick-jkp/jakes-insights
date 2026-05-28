---
title: "Supabase RLS 적용 후 쿼리 느려짐 원인 분석과 인덱스 전략 실전 트러블슈팅"
date: 2026-05-28T23:16:58+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-web", "supabase", "rls", "/ub290/ub824/uc9d0"]
description: "Supabase RLS 적용 후 쿼리가 2초에서 20초로 느려지는 원인은 인덱스 누락입니다. auth.uid() 정책과 맞물리는 인덱스 전략을 실제 실행 계획 분석과 함께 설명합니다."
image: "/images/20260528-supabase-rls-적용-후-쿼리-느려짐-원인-분석.webp"
technologies: ["Supabase"]
faq:
  - question: "Supabase RLS 적용 후 쿼리 느려짐 원인이 뭔가요"
    answer: "Supabase RLS 적용 후 쿼리 느려짐 원인 분석 인덱스 전략 실전 트러블슈팅에서 핵심으로 꼽는 원인은 auth.uid() 함수가 VOLATILE로 처리되어 매 행마다 새로 평가되는 구조입니다. 인덱스가 이 평가 방식을 따라가지 못하면 Postgres 플래너가 전체 테이블 스캔(Seq Scan)을 선택하게 되고, 테이블 규모가 커질수록 성능이 급격히 떨어집니다."
  - question: "auth.uid() RLS 정책 성능 개선 방법"
    answer: "auth.uid() 대신 (select auth.uid())로 소괄호로 감싸면 Postgres가 해당 값을 쿼리 시작 시점에 딱 한 번만 평가하므로 성능이 크게 개선됩니다. Supabase 공식 문서도 이 패턴을 권장하며, 이 작은 변경만으로도 EXPLAIN ANALYZE 결과에서 수 배의 속도 차이가 나타나는 사례가 보고되고 있습니다."
  - question: "Supabase RLS 인덱스 어떻게 설계해야 하나요"
    answer: "Supabase RLS 적용 후 쿼리 느려짐 원인 분석 인덱스 전략 실전 트러블슈팅 관점에서, user_id 단일 인덱스만으로는 ORDER BY created_at DESC 같은 조건이 붙는 쿼리를 커버하기 어렵습니다. (user_id, created_at DESC) 형태의 복합 인덱스를 사용하면 정렬 비용 없이 인덱스만으로 쿼리를 처리할 수 있고, status 같은 필터가 반복된다면 부분 인덱스(WHERE status = 'published')로 인덱스 크기와 캐시 효율을 추가로 최적화할 수 있습니다."
  - question: "EXPLAIN ANALYZE에서 Rows Removed by Filter가 많으면 문제인가요"
    answer: "Rows Removed by Filter 수치가 실제 반환 행(Rows)보다 수십 배 많다면, 인덱스가 없거나 잘못 설계되어 Postgres가 불필요한 행을 대량으로 읽고 버리고 있다는 신호입니다. 이 경우 EXPLAIN (ANALYZE, BUFFERS)로 Seq Scan 여부를 확인하고, 쿼리 조건에 맞는 복합 인덱스를 추가하는 것이 우선 조치입니다."
  - question: "팀 기반 RLS 정책 쿼리 성능 문제 해결"
    answer: "조직이나 팀 단위 접근 제어 정책은 team_members 같은 중간 테이블을 서브쿼리로 참조하는 구조가 많아, 해당 테이블에 인덱스가 없으면 매 쿼리마다 풀스캔이 발생합니다. 정책이 참조하는 모든 테이블에 (user_id, team_id) 같은 복합 인덱스를 추가해야 하며, 이 부분은 실제 트러블슈팅에서 가장 많이 놓치는 지점으로 꼽힙니다."
---

RLS를 켰더니 쿼리가 열 배 느려졌어요. 코드를 바꾼 건 없는데, 갑자기요.

Supabase에서 Row Level Security(RLS)를 처음 적용하는 팀들이 가장 자주 마주치는 장면이에요. `auth.uid()`를 정책에 넣고 배포했더니 목록 쿼리가 2초에서 20초로 늘어나는 거죠. Supabase를 프로덕션에 도입하는 팀이 빠르게 늘고 있는데, 이 문제로 롤백하거나 RLS 자체를 포기하는 사례도 적지 않아요. 그런데 원인은 거의 하나로 수렴해요. 인덱스가 RLS 정책을 따라가지 못하는 거예요. 어디를 봐야 하는지, 어떤 인덱스를 어떻게 만들어야 하는지를 데이터와 함께 짚어볼게요.

> **핵심 요약**
> - RLS 정책이 `auth.uid()`를 호출할 때, Postgres는 해당 함수를 쿼리마다 새로 평가해요. 인덱스가 없으면 이 평가가 전체 테이블 스캔(Seq Scan)으로 이어져요.
> - `(user_id)` 단일 인덱스만으로는 RLS 정책이 있는 복합 조건 쿼리를 커버하지 못해요. `(user_id, created_at DESC)` 같은 복합 인덱스가 필요한 경우가 많아요.
> - Supabase 공식 문서는 `auth.uid()`를 직접 정책에 넣는 대신 `(select auth.uid())`로 감싸는 패턴을 권장해요. 함수를 한 번만 평가하게 만드는 방식이에요.
> - `EXPLAIN ANALYZE`를 돌려봤을 때 `Rows Removed by Filter`가 `Rows`보다 수십 배 많으면, 인덱스가 없거나 잘못 설계된 거예요.

---

## RLS가 느린 진짜 구조적 이유

RLS는 마법이 아니에요. Postgres 입장에서는 각 행을 반환하기 전에 정책 조건을 평가하는 필터를 하나 더 붙이는 거예요. 조건이 `user_id = auth.uid()`라면, Postgres는 테이블에서 행을 읽을 때마다 `auth.uid()`를 호출해서 현재 사용자의 UUID를 가져오고, 그걸 `user_id`와 비교해요.

문제는 `auth.uid()`가 기본적으로 `VOLATILE` 함수로 처리된다는 거예요. Postgres 쿼리 플래너가 이 함수를 "매 행마다 다른 값을 줄 수 있는 함수"로 간주하는 거죠. 그러면 인덱스를 타기 어려워지고, 최악의 경우 플래너가 Seq Scan을 선택하게 돼요. 테이블에 행이 10만 개라면, 10만 번 조건을 평가하는 셈이에요.

해결책은 명확해요. `auth.uid()` 대신 `(select auth.uid())`를 써요. 소괄호로 감싸면 Postgres는 이 값을 서브쿼리 결과로 취급해서, 쿼리 실행 시작 시점에 딱 한 번만 평가해요. 이 작은 차이가 `EXPLAIN ANALYZE` 결과에서 수 배의 성능 차이로 나타나는 경우가 있어요.

```sql
-- 느린 버전
CREATE POLICY "users_own_data" ON posts
  USING (user_id = auth.uid());

-- 빠른 버전
CREATE POLICY "users_own_data" ON posts
  USING (user_id = (SELECT auth.uid()));
```

---

## 인덱스 전략: 어디에 무엇을 만들어야 하나요

정책을 고쳤는데도 여전히 느리다면, 다음 단계는 인덱스예요.

### 기본 단일 인덱스로는 부족할 때

`user_id`에 단일 인덱스를 만들면 충분할 것 같지만, 실제 쿼리는 거기서 끝나지 않는 경우가 많아요. `ORDER BY created_at DESC LIMIT 20` 같은 조건이 붙으면, Postgres는 인덱스를 탄 뒤에도 정렬을 위해 추가 작업을 해요. 행이 많을수록 이 비용이 커지고요.

이런 경우엔 복합 인덱스가 훨씬 나아요.

```sql
CREATE INDEX idx_posts_user_created
  ON posts (user_id, created_at DESC);
```

이렇게 하면 `WHERE user_id = $1 ORDER BY created_at DESC` 쿼리를 인덱스만으로 처리할 수 있어요. 테이블 자체를 거의 안 건드리는 거예요.

### 부분 인덱스로 더 좁히기

활성 게시물만 보여주는 정책이라면, 전체 행에 인덱스를 걸 필요가 없어요.

```sql
CREATE INDEX idx_posts_active_user
  ON posts (user_id, created_at DESC)
  WHERE status = 'published';
```

부분 인덱스는 인덱스 크기를 줄이고, 캐시 효율도 높여요. `status` 같은 필터가 쿼리마다 반복된다면 확실하게 효과를 볼 수 있어요.

### 복합 정책일 때: 조직 기반 접근 제어

팀 단위나 조직 단위로 데이터를 나누는 경우, 정책이 더 복잡해져요.

```sql
CREATE POLICY "team_access" ON documents
  USING (
    team_id IN (
      SELECT team_id FROM team_members
      WHERE user_id = (SELECT auth.uid())
    )
  );
```

이 경우엔 `team_members` 테이블의 `(user_id, team_id)` 복합 인덱스가 없으면 매 쿼리마다 `team_members`를 풀스캔해요. 의외로 많이 놓치는 부분이에요. 정책이 참조하는 **모든 테이블**에 인덱스가 있어야 해요.

---

## EXPLAIN ANALYZE로 실제로 어디가 문제인지 보기

이론보다 직접 봐야 확신이 생겨요. 느리다고 느끼는 쿼리 앞에 `EXPLAIN (ANALYZE, BUFFERS)`를 붙여서 실행해 보세요.

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM posts
WHERE user_id = (SELECT auth.uid())
ORDER BY created_at DESC
LIMIT 20;
```

결과에서 봐야 할 시그널은 세 가지예요.

| 시그널 | 의미 | 조치 |
|--------|------|------|
| `Seq Scan on posts` | 전체 테이블 스캔 | 인덱스 추가 필요 |
| `Rows Removed by Filter: N` (N이 수천~수만) | 인덱스가 있어도 불필요한 행을 많이 읽음 | 복합 인덱스 또는 부분 인덱스 재설계 |
| `auth.uid()` 호출이 반복적으로 나타남 | VOLATILE 함수 평가 | `(select auth.uid())`로 리팩토링 |

`Seq Scan`과 `Index Scan`의 차이는 단순하지 않아요. 행이 적을 때는 Seq Scan이 더 빠르기도 해요. 그래서 개발 환경(데이터 수백 개)에서 문제없다가 프로덕션(데이터 수십만 개)에서 터지는 거예요. 배포 전에 꼭 확인해야 하는 지점이에요.

### 두 접근법 비교

| 항목 | 단일 인덱스 (`user_id`) | 복합 인덱스 (`user_id, created_at DESC`) |
|------|------------------------|------------------------------------------|
| 인덱스 크기 | 작음 | 중간 |
| 단순 조회 성능 | 좋음 | 좋음 |
| 정렬 포함 조회 | 추가 Sort 발생 | 인덱스로 직접 처리 |
| LIMIT이 있는 페이지네이션 | 비효율 | 효율적 |
| 관리 복잡도 | 낮음 | 약간 높음 |
| 권장 상황 | 단순 존재 확인 쿼리 | 목록 조회, 피드, 대시보드 |

---

## 실전 체크리스트: 배포 전에 이것만 확인해요

**정책 작성 시**
- `auth.uid()` 직접 사용 → `(select auth.uid())`로 교체
- 정책이 참조하는 모든 서브쿼리의 대상 테이블에 인덱스 확인
- 정책 조건과 쿼리 WHERE 절이 일치하는지 확인 (인덱스가 정책 조건을 커버해야 해요)

**인덱스 설계 시**
- 목록 쿼리에는 정렬 컬럼을 포함한 복합 인덱스
- 상태 필터가 고정이면 부분 인덱스 검토
- `EXPLAIN ANALYZE`는 프로덕션 규모의 데이터로 테스트

**운영 중에**
- `pg_stat_user_indexes`로 인덱스 사용 여부 주기적으로 확인
- 사용하지 않는 인덱스는 삭제 (쓰기 성능에 영향)

---

## 앞으로 주시할 것들

Supabase 팀은 2025년 말부터 RLS 정책 분석 도구를 대시보드에 통합하는 작업을 진행 중이에요. 쿼리 플래너가 RLS 정책을 더 잘 인식하도록 Postgres 확장을 개선하는 논의도 GitHub 이슈에서 활발하게 이어지고 있고요.

지금 당장 해야 할 건 하나예요. `EXPLAIN ANALYZE`를 한 번 돌려보세요. 느린 쿼리가 어디서 막히는지 눈으로 보고 나면, 어떤 인덱스를 만들어야 할지 훨씬 명확하게 보여요. RLS 트러블슈팅의 90%는 정책 리팩토링과 인덱스 추가 두 가지로 해결돼요. 복잡한 게 아니에요. 어디를 봐야 하는지를 아는 게 전부예요.

RLS를 끄지 마세요. 인덱스를 추가하세요.

---

*더 알고 싶은 Supabase 성능 이슈나 Postgres 쿼리 분석 패턴이 있다면 댓글로 알려주세요. 다음 글의 주제로 다뤄볼게요.*

## 참고자료

1. [[260402 TIL] 검색 쿼리 최적화 트러블슈팅 - elseif - 티스토리](https://ifelseif.tistory.com/332)
2. [Supabase Postgres Best Practices - 함께해요 바이브 코딩](https://wikidocs.net/339066)
3. [Supabase RLS 성능 경고 해결(auth.uid() 리팩토링)](https://velog.io/@rlaugs15/Supabase-RLS-%EC%84%B1%EB%8A%A5-%EA%B2%BD%EA%B3%A0-%ED%95%B4%EA%B2%B0auth.uid-%EB%A6%AC%ED%8C%A9%ED%86%A0%EB%A7%81)


---

*Photo by [Microsoft Copilot](https://unsplash.com/@microsoftcopilot) on [Unsplash](https://unsplash.com/photos/two-women-talking-in-a-kitchen-while-cooking-3c_k7h8YgHw)*
