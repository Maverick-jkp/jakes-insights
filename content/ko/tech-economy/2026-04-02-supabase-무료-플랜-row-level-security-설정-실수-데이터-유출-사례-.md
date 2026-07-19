---
title: "Supabase RLS 설정 실수로 인한 데이터 유출 사례와 방지 가이드"
date: 2026-04-02T20:01:23+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-security", "supabase", "row", "level", "JavaScript"]
description: "Supabase RLS 미설정 시 전체 유저 데이터가 즉시 노출됩니다. 흔한 실수 패턴 3가지와 복사해서 쓸 수 있는 정책 코드, 프로덕션 배포 전 체크리스트를 정리했습니다."
image: "/images/20260402-supabase-무료-플랜-row-level-secur.webp"
technologies: ["JavaScript", "TypeScript", "PostgreSQL", "Java", "Supabase"]
faq:
  - question: "Supabase RLS 설정 안 하면 어떻게 되나요"
    answer: "Supabase에서 테이블을 생성하면 RLS가 기본값으로 비활성화되어 있어서, anon 키로 접근하는 인증되지 않은 누구나 해당 테이블의 모든 데이터를 읽고 쓸 수 있어요. 이는 즉각적인 데이터 유출 위험으로 이어지며, 실제로 2025년에도 RLS가 꺼진 채 배포된 Supabase 프로젝트 사례가 다수 보고됐어요."
  - question: "Supabase 무료 플랜 Row Level Security 설정 실수 데이터 유출 사례 방지 가이드에서 말하는 가장 위험한 RLS 실수는 뭔가요"
    answer: "가장 흔하고 위험한 실수는 SELECT 정책만 만들고 INSERT, UPDATE, DELETE 정책은 빠뜨리는 경우예요. RLS를 활성화해도 명시적으로 정책을 만들지 않은 동작은 기본적으로 허용되기 때문에, SELECT만 막아도 악의적인 사용자가 데이터를 삽입하거나 수정할 수 있어요."
  - question: "Supabase RLS 활성화했는데 정책이 작동 안 하는 이유"
    answer: "auth.uid()를 사용하는 정책을 생성했더라도 ALTER TABLE 명령으로 RLS 자체를 ENABLE하지 않으면 정책은 실제로 작동하지 않아요. RLS 켜기와 정책 생성은 별개의 작업으로, 반드시 두 가지 모두 실행해야 해요."
  - question: "Supabase 테이블 RLS 활성화 여부 확인하는 방법"
    answer: "Supabase Dashboard의 Table Editor에서 테이블 목록을 보면 각 테이블의 RLS 상태를 한눈에 확인할 수 있고, 열린 자물쇠 아이콘이 표시되면 비활성화 상태예요. SQL Editor에서 pg_tables를 조회해 rowsecurity = false인 테이블을 직접 확인하는 방법도 있어요."
  - question: "Supabase 무료 플랜 Row Level Security 설정 실수 데이터 유출 사례 방지 가이드 프로덕션 배포 전 체크리스트"
    answer: "프로덕션 배포 전에는 모든 public 테이블의 RLS 활성화 여부를 SQL 쿼리로 점검하고, SELECT뿐 아니라 INSERT, UPDATE, DELETE 정책이 각각 존재하는지 확인해야 해요. 가장 확실한 예방법은 배포 전에 anon 역할로 직접 쿼리를 테스트해서 의도치 않은 접근이 가능한지 검증하는 습관을 들이는 거예요."
aliases:
  - "/tech/2026-04-02-supabase-무료-플랜-row-level-security-설정-실수-데이터-유출-사례-/"
  - "/ko/tech/2026-04-02-supabase-무료-플랜-row-level-security-설정-실수-데이터-유출-사례-/"

---

Supabase로 사이드 프로젝트 만들다가 갑자기 이런 순간이 와요.

"어? 내 앱에서 다른 유저 데이터가 보이는데?"

그게 바로 RLS(Row Level Security) 설정을 빠뜨렸을 때 생기는 일이에요. 프로토타입 만들 때 "나중에 설정하지 뭐"하고 넘어갔다가 그대로 프로덕션에 올라가는 패턴, 생각보다 엄청 흔해요. 이 가이드는 Supabase를 처음 쓰거나, 이미 쓰고 있지만 RLS 설정이 불안한 개발자를 위해 썼어요.

읽고 나면 이런 걸 가져갈 수 있어요:
- RLS가 꺼진 테이블이 왜 즉각적인 유출 위험인지
- 가장 흔한 RLS 설정 실수 패턴 3가지
- 실제로 쓸 수 있는 정책 코드와 검증 방법
- 프로덕션 배포 전 체크리스트

---

> **Key Takeaways**
> - Supabase에서 테이블을 만들면 RLS는 기본값으로 **꺼져(disabled)** 있어요. anon key로 접근하면 누구나 모든 행을 읽고 쓸 수 있어요.
> - `auth.uid()`를 쓰는 정책을 만들어도 RLS 자체를 `ENABLE`하지 않으면 정책은 작동하지 않아요.
> - 가장 위험한 실수는 "SELECT 정책만 만들고 INSERT/UPDATE/DELETE는 열어두는 것"이에요.
> - Supabase Dashboard의 **Table Editor → RLS 탭**에서 각 테이블의 RLS 활성화 여부를 한눈에 확인할 수 있어요.
> - 정책을 배포하기 전에 anon 역할로 직접 쿼리 테스트하는 습관이 유출 사고를 예방하는 가장 확실한 방법이에요.

---

## RLS가 뭔지, 왜 지금 더 중요해졌는지

Row Level Security는 PostgreSQL의 기능이에요. 테이블의 각 행(row)에 누가 접근할 수 있는지를 데이터베이스 레벨에서 제어해요. Supabase는 이 기능을 그대로 써요.

2022년쯤만 해도 Supabase는 "개발자 친화적 Firebase 대안" 정도로 알려졌어요. 그런데 2025-2026년 사이 무료 플랜 인지도가 크게 올라가면서, 백엔드 경험이 많지 않은 프론트엔드 개발자나 인디 해커들도 Supabase로 바로 프로덕션 앱을 만들기 시작했어요.

문제는 Supabase 클라이언트 라이브러리(`supabase-js`)가 `anon` 키와 `service_role` 키 두 가지를 제공한다는 거예요. `anon` 키는 브라우저에 노출돼도 되는 키인데, 이 키로 접근할 때 RLS가 꺼져 있으면 **인증되지 않은 누구나 해당 테이블 전체를 볼 수 있어요.** 실제로 GitHub에 공개된 Supabase 프로젝트 코드 중 RLS가 꺼진 채로 배포된 사례가 2025년 한 해에만 다수 보고됐어요. 놀랍죠?

가장 큰 차이는 **기본값**이에요. Firebase는 규칙을 아무것도 안 쓰면 기본적으로 모든 접근을 막아요. Supabase RLS는 비활성화 상태가 기본이에요. 이 차이가 수많은 실수의 원인이에요.

**사전에 알아야 할 것들:**
- SQL 기본 문법 (SELECT, INSERT 정도)
- Supabase 프로젝트 생성 경험
- JavaScript 또는 TypeScript 기초

---

## 단계별 RLS 설정 가이드

### Step 1: RLS 활성화 여부 먼저 확인하기

Supabase Dashboard → Table Editor로 가면 테이블 목록에 각 테이블의 RLS 상태가 보여요. 빨간 자물쇠(🔓)가 보이면 꺼진 거예요.

SQL Editor에서 직접 확인할 수도 있어요:

```sql
-- 현재 프로젝트에서 RLS가 꺼진 테이블 목록 조회
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
  AND rowsecurity = false;
```

이 쿼리 결과가 하나라도 나오면, 그 테이블은 지금 당장 열려 있는 거예요.

---

### Step 2: RLS 켜기 + 기본 정책 만들기

RLS를 켜는 것과 정책을 만드는 것은 별개예요. 둘 다 해야 해요.

```sql
-- 1. posts 테이블에 RLS 활성화
ALTER TABLE public.posts ENABLE ROW LEVEL SECURITY;

-- 2. 자기 데이터만 볼 수 있는 SELECT 정책
CREATE POLICY "본인 게시글만 조회"
ON public.posts FOR SELECT
USING (auth.uid() = user_id);

-- 3. 본인만 삽입 가능한 INSERT 정책
CREATE POLICY "본인 게시글만 작성"
ON public.posts FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- 4. 본인 게시글만 수정
CREATE POLICY "본인 게시글만 수정"
ON public.posts FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- 5. 본인 게시글만 삭제
CREATE POLICY "본인 게시글만 삭제"
ON public.posts FOR DELETE
USING (auth.uid() = user_id);
```

`FOR ALL`로 한 번에 처리할 수 있지만, INSERT에는 `USING`이 아니라 `WITH CHECK`를 써야 해서 분리하는 게 실수를 줄여요.

---

### Step 3: 가장 흔한 실수 — SELECT만 막고 나머지는 열어두기

```sql
-- ❌ 이렇게 하면 SELECT는 막히지만 INSERT는 뚫려 있어요
CREATE POLICY "읽기 제한"
ON public.users FOR SELECT
USING (auth.uid() = id);

-- anon 유저가 이렇게 데이터를 넣을 수 있어요
-- INSERT INTO users (id, email) VALUES ('fake-id', 'hacker@evil.com');
```

정책을 명시적으로 만들지 않은 동작은 **기본적으로 허용**이에요. RLS를 켰다고 자동으로 막히는 게 아니에요. 이게 핵심이에요.

---

### Step 4: anon 역할로 직접 테스트하기

가장 확실한 검증 방법은 anon 역할로 직접 쿼리해보는 거예요:

```sql
SET ROLE anon;
SELECT * FROM public.posts; -- 결과가 비어 있어야 정상

RESET ROLE;
```

클라이언트에서도 확인할 수 있어요:

```javascript
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY // service_role 키 절대 쓰면 안 돼요
)

// 로그인 없이 접근 — 빈 배열이 와야 정상
const { data, error } = await supabase.from('posts').select('*')
console.log('anon 접근 결과:', data) // [] 여야 해요
```

---

## 실전 예시: 공개/비공개 게시글 혼합 정책

```sql
ALTER TABLE public.posts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "공개 게시글은 누구나 조회"
ON public.posts FOR SELECT
USING (
  is_public = true
  OR auth.uid() = user_id
);

CREATE POLICY "인증된 유저만 작성"
ON public.posts FOR INSERT
WITH CHECK (
  auth.uid() IS NOT NULL
  AND auth.uid() = user_id
);
```

`is_public = true`인 행은 anon도 볼 수 있고, 비공개 게시글은 작성자 본인만 볼 수 있어요. INSERT는 로그인한 유저만 가능하고, 자신의 `user_id`로만 데이터를 넣을 수 있어요.

---

## 자주 빠지는 함정과 체크리스트

**피해야 할 패턴들**

- **`service_role` 키를 프론트엔드에 노출하기**: 이 키는 RLS를 완전히 무시해요. `NEXT_PUBLIC_` 접두사 붙은 환경변수에는 절대 넣지 마세요.
- **정책 없이 RLS만 켜기**: 정책이 하나도 없으면 모든 접근이 차단돼요. 앱이 아무것도 못 읽는 상황이 생겨요. RLS 켜고 나서 바로 정책도 같이 만드세요.
- **`FOR ALL` 정책에서 INSERT 체크 누락**: `USING`만 쓰면 INSERT에는 적용 안 돼요. INSERT가 포함된 정책엔 반드시 `WITH CHECK` 추가하세요.

**프로덕션 배포 전 체크리스트**

- [ ] `public` 스키마의 모든 테이블에 RLS 활성화 확인
- [ ] 각 테이블에 SELECT/INSERT/UPDATE/DELETE 정책 모두 명시
- [ ] anon 역할로 테스트 쿼리 실행하고 결과 확인
- [ ] `service_role` 키가 프론트엔드 코드에 없는지 GitHub 검색으로 확인
- [ ] Supabase Dashboard → Authentication → Policies 탭에서 전체 정책 재검토

---

## 마치며

Supabase 무료 플랜으로 빠르게 만들다 보면 RLS는 "나중 일"처럼 느껴져요. 그런데 프로덕션 배포 후 데이터가 열려 있다는 걸 발견하면, 그게 진짜 나중 일이 돼버려요.

세 가지만 기억하세요:
- **RLS 켜는 것과 정책 만드는 것은 별개**
- **정책 없는 동작은 기본 허용**
- **anon 역할로 배포 전 직접 테스트**

지금 당장 SQL Editor에서 RLS 꺼진 테이블 조회 쿼리 한 번 돌려보세요. 결과가 비어 있으면 다행이고, 뭔가 나오면 오늘 막은 거예요.

공식 문서는 [Supabase RLS 가이드](https://supabase.com/docs/guides/database/postgres/row-level-security)에서 더 자세히 볼 수 있어요. 다음엔 Storage 버킷 권한 설정도 같은 방식으로 확인해보면 좋아요.

## 참고자료

1. [Row Level Security | Supabase Docs](https://supabase.com/docs/guides/database/postgres/row-level-security)
2. [Supabase Row Level Security (RLS): Complete Guide 2026](https://vibeappscanner.com/supabase-row-level-security)


---

*Photo by [NASA](https://unsplash.com/@nasa) on [Unsplash](https://unsplash.com/photos/photo-of-outer-space-Q1p7bh3SHj8)*
