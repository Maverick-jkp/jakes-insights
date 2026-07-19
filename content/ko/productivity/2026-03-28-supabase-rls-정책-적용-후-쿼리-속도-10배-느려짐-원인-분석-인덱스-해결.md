---
title: "Supabase RLS 정책 적용 후 쿼리 속도 10배 느려짐: 원인 분석과 인덱스 해결법"
date: 2026-03-28T19:49:37+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-web", "supabase", "rls", "10\ubc30", "PostgreSQL"]
description: "Supabase RLS 정책 적용 후 쿼리가 200ms에서 2초로 느려졌다면 인덱스 부재가 원인입니다. auth.uid() 조건에 B-tree 인덱스를 추가해 풀 테이블 스캔을 차단하는 방법을 설명합니"
image: "/images/20260328-supabase-rls-정책-적용-후-쿼리-속도-10배.webp"
technologies: ["PostgreSQL", "Supabase"]
faq:
  - question: "Supabase RLS 정책 적용 후 쿼리 속도 10배 느려짐 원인 분석 인덱스 해결 방법"
    answer: "Supabase RLS 정책 적용 후 쿼리 속도 10배 느려짐 원인 분석 인덱스 해결의 핵심은 RLS 조건 컬럼에 인덱스가 없어서 발생하는 풀 테이블 스캔(Seq Scan)이에요. RLS 정책은 모든 쿼리에 WHERE 조건을 자동으로 추가하기 때문에, `user_id`처럼 필터링에 쓰이는 컬럼에 B-tree 인덱스가 없으면 행 수만큼 비교 연산이 반복돼요. `CREATE INDEX idx_messages_user_id ON messages(user_id);` 한 줄로 대부분의 경우 쿼리 속도를 원래 수준으로 되돌릴 수 있어요."
  - question: "Supabase auth.uid() RLS 정책 쿼리 느려지는 이유"
    answer: "`auth.uid()`를 RLS 조건으로 사용하면 PostgreSQL이 매 요청마다 해당 UUID로 테이블 전체를 순회하는 Seq Scan이 발생할 수 있어요. `auth.uid()` 함수 자체의 오버헤드는 미미하지만, 조건을 적용할 `user_id` 컬럼에 인덱스가 없을 때 테이블 데이터가 수십만 행을 넘어서는 순간 성능이 급격히 저하돼요. `EXPLAIN ANALYZE`로 실행 계획을 확인해 Seq Scan이 뜨는지 확인하고, 인덱스를 추가하면 해결돼요."
  - question: "PostgreSQL EXPLAIN ANALYZE Seq Scan Index Scan 차이 확인하는 법"
    answer: "`EXPLAIN ANALYZE SELECT * FROM 테이블명;` 명령어를 실행하면 쿼리 실행 계획에서 Seq Scan(순차 탐색)과 Index Scan(인덱스 탐색) 여부를 바로 확인할 수 있어요. Seq Scan이 출력되면 해당 테이블에 적절한 인덱스가 없다는 신호이며, 인덱스를 추가한 뒤 다시 실행해 Index Scan으로 바뀌는지 검증하면 돼요. RLS 정책 적용 후 갑자기 느려졌다면 이 명령어로 원인을 빠르게 파악할 수 있어요."
  - question: "Supabase RLS 복합 인덱스 적용 방법 user_id created_at"
    answer: "RLS 조건에 `user_id`와 날짜 범위 필터를 함께 사용하는 경우 `CREATE INDEX idx_messages_user_created ON messages(user_id, created_at);`처럼 복합 인덱스를 적용하면 단일 인덱스보다 10~20배 이상의 성능 개선을 기대할 수 있어요. 복합 인덱스는 컬럼 순서가 중요하며, RLS 정책의 필터 조건에서 먼저 사용되는 컬럼을 앞에 배치해야 인덱스가 제대로 활용돼요. 인덱스 추가 후 쓰기 속도가 소폭 저하될 수 있으므로 트레이드오프를 고려해 적용하세요."
  - question: "Supabase RLS 정책 OR 조건 서브쿼리 성능 저하 해결"
    answer: "RLS 정책에 OR 조건이나 서브쿼리를 포함하면 행마다 서브쿼리가 반복 실행되어 성능이 크게 저하될 수 있어요. 예를 들어 `team_members` 테이블을 서브쿼리로 조회하는 정책의 경우 `team_members.user_id` 컬럼에 인덱스가 없으면 서브쿼리가 수백만 번 실행되는 최악의 상황이 발생해요. 서브쿼리에 사용되는 모든 조건 컬럼에 인덱스를 추가하고, 가능하면 복잡한 OR 조건을 분리된 정책으로 나눠 관리하는 것이 좋아요."
aliases:
  - "/tech/2026-03-28-supabase-rls-정책-적용-후-쿼리-속도-10배-느려짐-원인-분석-인덱스-해결/"

---

쿼리 하나가 200ms에서 2초로 늘어났어요. RLS 정책 하나 추가했을 뿐인데요.

착각이 아니에요. Supabase RLS(Row Level Security) 정책을 적용한 뒤 쿼리 속도가 10배 느려지는 현상은 수많은 개발자들이 실제로 겪는 문제예요. 프로덕션에서 갑자기 이 상황을 마주치면 당황하기 십상이죠. 그런데 원인을 알면 해결은 생각보다 간단해요. 인덱스 설계가 핵심이에요.

> **핵심 요약**
> - Supabase RLS 정책은 모든 쿼리에 WHERE 조건을 자동 삽입하는 방식으로 작동해요. 해당 컬럼에 인덱스가 없으면 풀 테이블 스캔이 발생해 쿼리 속도가 10배 이상 느려질 수 있어요.
> - `auth.uid()`를 RLS 조건으로 쓸 때 `user_id` 컬럼에 B-tree 인덱스가 없으면 PostgreSQL은 매 요청마다 전체 테이블을 순회해요.
> - `EXPLAIN ANALYZE` 명령어로 쿼리 실행 계획을 확인하면 Seq Scan(순차 탐색) vs. Index Scan(인덱스 탐색) 여부를 바로 파악할 수 있어요.
> - RLS 정책의 조건 컬럼에 복합 인덱스(Composite Index)를 적용하면 대부분의 경우 쿼리 속도가 원래 수준으로 돌아오거나 그 이상으로 개선돼요.

---

## RLS가 정확히 뭘 하는 건가요?

Supabase는 PostgreSQL의 RLS 기능을 기반으로 데이터 접근 제어를 구현해요. 쉽게 말하면, 사용자가 자신의 데이터만 볼 수 있도록 데이터베이스 레벨에서 자동으로 필터를 거는 거예요.

예를 들어 이런 정책을 만들었다고 해볼게요.

```sql
CREATE POLICY "users_own_data" ON messages
  FOR SELECT
  USING (user_id = auth.uid());
```

이 정책이 활성화되는 순간, 누군가 `SELECT * FROM messages`를 실행하면 PostgreSQL 내부에서 자동으로 이렇게 변환돼요.

```sql
SELECT * FROM messages WHERE user_id = auth.uid();
```

사용자는 WHERE 조건 없이 쿼리를 날렸지만, 데이터베이스는 모르게 조건을 붙이는 거예요. Supabase 공식 문서에 따르면 이 정책 평가는 쿼리 최적화 단계에서 자동으로 일어나요.

여기서 문제가 시작돼요. `user_id` 컬럼에 인덱스가 없으면 PostgreSQL은 해당 값을 찾기 위해 테이블 전체를 읽어야 해요. 행이 1만 개면 1만 번 비교, 100만 개면 100만 번 비교예요. 이게 바로 Seq Scan, 풀 테이블 스캔이에요.

RLS 없이는 이 문제가 드러나지 않아요. RLS 없이 쿼리를 날리면 애플리케이션 레벨에서 이미 특정 `user_id`를 명시하는 경우가 많고, 그 경우엔 개발자가 인덱스를 챙기거든요. 반면 RLS는 정책이 자동으로 조건을 추가하니까, "이 컬럼에도 인덱스가 필요하다"는 걸 놓치기 쉬워요.

---

## 10배 느려지는 원인, 세 가지로 정리

### 1. `auth.uid()` 호출 비용과 Seq Scan의 조합

`auth.uid()`는 현재 인증된 사용자의 UUID를 반환하는 함수예요. 이 함수 자체의 오버헤드는 미미해요. 진짜 문제는 이 값으로 필터링할 때 인덱스가 없다는 점이에요.

Lobehub의 Supabase 트러블슈팅 가이드에서도 이 패턴을 대표적인 성능 저하 원인으로 꼽아요. 특히 `messages`, `posts`, `orders`처럼 데이터가 빠르게 쌓이는 테이블에서 치명적이에요. 테이블이 작을 땐 괜찮아 보이다가, 수십만 행이 넘어가는 순간 갑자기 속도가 곤두박질쳐요.

### 2. 정책 조건이 복잡할수록 실행 비용 증가

RLS 정책을 여러 개 겹치거나, OR 조건으로 연결하면 상황이 더 나빠져요.

```sql
-- 이 정책은 생각보다 비싸요
CREATE POLICY "team_access" ON documents
  FOR SELECT
  USING (
    owner_id = auth.uid()
    OR team_id IN (
      SELECT team_id FROM team_members WHERE user_id = auth.uid()
    )
  );
```

여기서 서브쿼리(`team_members` 테이블 조회)가 매 행 평가마다 실행될 수 있어요. `team_members.user_id`에 인덱스가 없으면, 행 100만 개짜리 테이블에서는 서브쿼리도 100만 번 돌아가는 셈이에요.

### 3. JOIN과 RLS의 만남

RLS는 참조되는 모든 테이블에 각각 적용돼요. `messages` 테이블과 `attachments` 테이블을 JOIN할 때 두 테이블에 모두 RLS가 걸려 있다면, 각각의 정책이 독립적으로 평가돼요. 인덱스가 없는 상태라면 스캔이 두 배로 늘어나는 셈이에요.

---

## 인덱스로 해결하기: 방법별 비교

### 핵심 해결책 비교

| 상황 | 적용할 인덱스 | 예상 개선 효과 | 주의사항 |
|------|--------------|----------------|----------|
| 단순 `user_id = auth.uid()` | B-tree 단일 인덱스 | 5~15배 개선 | 쓰기 속도 소폭 저하 |
| `user_id` + 날짜 범위 필터 | 복합 인덱스 (user_id, created_at) | 10~20배 개선 | 컬럼 순서가 중요함 |
| 텍스트 검색 포함 RLS | GIN 인덱스 | 검색에 한해 3~8배 개선 | 일반 필터에는 비효율 |
| 멀티 테넌트 구조 | 복합 인덱스 (tenant_id, user_id) | 15배 이상 개선 가능 | 설계 단계 고려 필수 |

#### B-tree 단일 인덱스 (가장 빠른 해결책)

```sql
-- RLS 정책이 user_id를 쓴다면, 이 한 줄로 많은 걸 해결해요
CREATE INDEX idx_messages_user_id ON messages(user_id);
```

`EXPLAIN ANALYZE`로 확인하면 `Seq Scan` 대신 `Index Scan`이 뜨는 걸 볼 수 있어요. 이것만으로도 대부분의 케이스에서 10배 이상 차이가 나요.

#### 복합 인덱스 (더 정밀한 해결책)

RLS 정책 조건에 추가 필터가 자주 붙는다면 복합 인덱스가 더 효과적이에요.

```sql
-- "내 메시지 중 최근 것" 같은 쿼리에 최적
CREATE INDEX idx_messages_user_created ON messages(user_id, created_at DESC);
```

복합 인덱스에서 컬럼 순서는 왼쪽부터 적용돼요. `user_id`가 먼저 와야 RLS 필터가 인덱스를 타고, 그다음 `created_at`으로 정렬까지 인덱스 안에서 해결돼요. 순서를 바꾸면 RLS 필터에서 인덱스를 못 써요.

---

## 실전 진단: `EXPLAIN ANALYZE` 쓰는 법

```sql
EXPLAIN ANALYZE
SELECT * FROM messages
WHERE created_at > NOW() - INTERVAL '7 days';
```

결과에서 봐야 할 것:
- `Seq Scan` → 인덱스 없음, 개선 필요
- `Index Scan` → 인덱스 타고 있음, 양호
- `Bitmap Heap Scan` → 중간 상태, 데이터 규모에 따라 괜찮을 수도 있음
- `cost=` 뒤 숫자가 크면 클수록 비싼 쿼리

한 가지 주의할 점이 있어요. RLS가 적용된 상태에서는 Supabase 대시보드의 SQL Editor에서 실행해야 실제 RLS 조건이 반영된 실행 계획을 볼 수 있어요. `service_role`로 실행하면 RLS를 우회하기 때문에 실제 성능과 달라 보여요. 이걸 모르고 "인덱스 달았는데 왜 똑같지?" 하는 경우가 꽤 많아요.

---

## 지금 당장 해야 할 것들

**즉시 확인 (이번 주)**:
- `EXPLAIN ANALYZE`로 RLS가 걸린 주요 테이블의 쿼리 실행 계획 확인
- RLS 정책 WHERE 조건에 쓰이는 컬럼에 인덱스 존재 여부 점검
- Supabase 대시보드 → Database → Indexes 탭에서 현재 인덱스 목록 확인

**중기 대응 (1~2개월)**:
- 멀티 테넌트 구조라면 `tenant_id + user_id` 복합 인덱스 설계를 스키마 단계에서 반영
- OR 조건이 들어간 복잡한 RLS 정책은 서브쿼리 대신 별도 테이블이나 함수로 분리 검토
- Supabase의 `pg_stat_statements` 확장으로 느린 쿼리 주기적으로 모니터링

참고로, Supabase 로드맵에는 성능 어드바이저 기능이 예정돼 있어요. 인덱스 부재를 자동으로 감지해주는 방향으로 발전할 거예요. 그래도 지금은 개발자가 직접 챙겨야 해요.

---

## 마무리: 설계 단계에서 막는 게 최선이에요

- RLS 정책의 조건 컬럼 = 반드시 인덱스가 있어야 하는 컬럼
- `auth.uid()` 쓰면 `user_id` 인덱스는 필수
- 복잡한 OR 조건 RLS는 서브쿼리 없이 설계할 방법을 먼저 찾기
- `EXPLAIN ANALYZE`는 RLS 디버깅의 시작이자 끝

원인이 명확하면 해결도 명확해요. 데이터베이스가 느려졌을 때 제일 먼저 의심해야 할 건 네트워크도 서버도 아니에요. 쿼리 실행 계획이에요.

지금 프로젝트에 RLS를 쓰고 있다면, 오늘 `EXPLAIN ANALYZE` 한 번만 돌려보세요. 결과가 어떻게 나왔나요?

## 참고자료

1. [AI Prompt: Database: Create RLS policies | Supabase Docs](https://supabase.com/docs/guides/getting-started/ai-prompts/database-rls-policies)
2. [Lobehub](https://lobehub.com/ko/skills/adaptationio-skrillz-supabase-troubleshooting)


---

*Photo by [Microsoft Copilot](https://unsplash.com/@microsoftcopilot) on [Unsplash](https://unsplash.com/photos/woman-cooking-on-a-stovetop-in-a-kitchen-eoTvdke70Vw)*
