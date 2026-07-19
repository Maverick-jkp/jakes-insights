---
title: "Supabase RLS 정책 설정 실수로 생기는 보안 취약점 사례와 점검 체크리스트"
date: 2026-03-22T19:42:58+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-web", "supabase", "rls", "\ucde8\uc57d\uc810", "PostgreSQL"]
description: "Supabase RLS 비활성화 시 전체 데이터 노출, anon·authenticated 권한 혼동 등 실제 보안 취약점 사례와 USING 절 설정 실수를 체크리스트로 점검하세요."
image: "/images/20260322-supabase-rls-정책-설정-실수-보안-취약점-실.webp"
technologies: ["PostgreSQL", "REST API", "Supabase"]
faq:
  - question: "Supabase RLS 활성화했는데 데이터가 안 나오는 이유"
    answer: "RLS를 활성화(ENABLE ROW LEVEL SECURITY)하고 정책을 하나도 추가하지 않으면 Supabase는 기본적으로 모든 행 접근을 차단해요. 정책이 없는 상태 = 데이터 없음이기 때문에, 반드시 SELECT/INSERT/UPDATE/DELETE 각각에 맞는 정책을 명시적으로 생성해야 앱이 정상 동작해요."
  - question: "Supabase RLS 정책 설정 실수 보안 취약점 실제 사례 어떤 게 있나요"
    answer: "Supabase RLS 정책 설정 실수 보안 취약점 실제 사례로 가장 흔한 것은 `TO public` 정책으로 비로그인 사용자에게 전체 데이터를 열어주는 경우, `WITH CHECK` 절 누락으로 타인의 user_id로 데이터를 삽입할 수 있는 경우, 그리고 service_role 키가 프론트엔드 코드나 GitHub에 노출되는 경우예요. 이런 실수들은 RLS 자체를 켜지 않은 것보다 오히려 더 발견하기 어렵기 때문에 배포 전 체계적인 점검이 필수예요."
  - question: "Supabase anon 키 authenticated 키 차이 RLS 정책에서 어떻게 써야 해"
    answer: "`anon`은 로그인하지 않은 사용자에게 부여되는 역할이고, `authenticated`는 로그인한 사용자에게 부여되는 역할이에요. 정책에서 `TO public`으로 설정하면 두 역할 모두 포함되므로, 로그인한 사용자만 접근을 허용하려면 반드시 `TO authenticated`로 명시해야 해요."
  - question: "RLS USING 절이랑 WITH CHECK 절 차이 뭔가요"
    answer: "`USING` 절은 SELECT와 DELETE 시 어떤 행에 접근할 수 있는지를 제어하고, `WITH CHECK` 절은 INSERT와 UPDATE 시 어떤 데이터를 쓸 수 있는지를 제어해요. `WITH CHECK`를 생략하면 읽기는 본인 데이터만 보이더라도 다른 사람의 user_id로 데이터를 삽입하는 게 가능해지므로, 쓰기 작업이 있는 정책에는 반드시 함께 작성해야 해요."
  - question: "Supabase RLS 정책 설정 실수 보안 취약점 점검 체크리스트 배포 전에 뭘 확인해야 해"
    answer: "Supabase RLS 정책 설정 실수 보안 취약점 실제 사례 점검 체크리스트에 따르면, 배포 전에는 `pg_tables`에서 `rowsecurity`가 false인 테이블이 없는지 확인하고, 모든 테이블에 실제 정책이 존재하는지 반드시 점검해야 해요. 특히 service_role 키가 프론트엔드 코드나 Git 저장소에 포함되어 있지 않은지도 함께 확인하는 것이 핵심이에요."
aliases:
  - "/tech/2026-03-22-supabase-rls-정책-설정-실수-보안-취약점-실제-사례-점검-체크리스트/"

---

데이터베이스를 열어놓고 잠근 척하는 거, 알고 계세요?

Supabase 공식 문서에 따르면, 새로 생성한 테이블에 RLS(Row Level Security)를 활성화하지 않으면 **모든 사용자가 모든 데이터에 접근**할 수 있어요. 기본값이 "열림"이라는 거예요. 빠른 개발 사이클 속에서 보안 설정을 "나중에 하지 뭐"라고 미루다가 그대로 프로덕션에 올라가는 경우, 생각보다 많아요.

> **핵심 요약**
> - Supabase는 테이블 생성 시 RLS가 기본적으로 비활성화되어 있어, 활성화 없이 배포하면 전체 데이터가 노출될 수 있어요.
> - `anon` 키와 `authenticated` 키의 권한 차이를 혼동한 정책은 인증되지 않은 사용자에게 데이터를 열어주는 가장 흔한 실수예요.
> - `USING` 절만 있고 `WITH CHECK` 절이 없는 정책은 읽기는 막아도 쓰기는 막지 못해요. 절반만 잠근 자물쇠인 셈이죠.
> - RLS 관련 데이터 노출 이슈의 절반 이상이 정책 미설정보다 잘못된 정책 설정에서 비롯돼요.
> - 배포 전 점검 체크리스트를 한 번만 돌려도 대부분의 문제를 사전에 막을 수 있어요.

---

## RLS가 뭔지, 왜 지금 이게 중요한가

RLS는 PostgreSQL이 제공하는 행 수준 접근 제어 기능이에요. 쉽게 말하면 "이 행(row)은 이 사람만 볼 수 있다"를 데이터베이스 레벨에서 강제하는 거예요. 애플리케이션 코드에서 `WHERE user_id = auth.uid()`를 넣는 것과는 달리, RLS는 코드를 우회해도 적용되는 보안층이에요.

Supabase는 PostgREST를 통해 데이터베이스를 REST API로 노출해요. 클라이언트 SDK를 쓰면 브라우저에서 직접 DB에 쿼리를 날릴 수 있죠. 이 구조에서 RLS 없이 배포하면, 브라우저 콘솔에서 `supabase.from('users').select('*')`만 쳐도 전체 유저 테이블이 반환될 수 있어요. 놀랍죠?

2026년 기준 Supabase 프로젝트 수는 100만 개를 넘어섰고(Supabase 2025 Annual Report 기준), 상당수가 스타트업과 소규모 팀이에요. 그리고 그 팀들 상당수가 지금 이 함정을 밟고 있을 가능성이 있어요.

---

## 실제로 이런 실수들이 일어나요

### 실수 #1: RLS를 켰지만 정책이 하나도 없는 경우

`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`로 활성화했어요. 켰으니 이제 안전하다고 생각하는 거죠. 그런데 Supabase 공식 문서는 명확하게 설명해요. "RLS가 활성화되어 있지만 정책이 없으면, **기본적으로 모든 행이 거부**된다"고요.

결과는 데이터 노출이 아니라 반대로 앱이 아무것도 못 보는 상황이에요. "왜 데이터가 안 나오지?"라며 디버깅하다가 `anon` 역할에 SELECT 권한을 뚫어놓고 그냥 배포하는 거예요. 정책 없이 전체 공개가 되는 아이러니가 생기는 거죠.

### 실수 #2: `anon`과 `authenticated` 역할 혼동

Supabase에는 크게 두 가지 역할이 있어요.

- `anon`: 로그인하지 않은 사람
- `authenticated`: 로그인한 사람

정책을 이렇게 쓰는 경우가 많아요.

```sql
CREATE POLICY "누구나 볼 수 있어요"
ON posts FOR SELECT
TO public
USING (true);
```

`TO public`은 `anon`과 `authenticated` 모두 포함해요. 의도가 "로그인한 사용자만"이었다면 `TO authenticated`로 명시해야 해요. 이 실수 하나로 비로그인 유저가 전체 게시물을 읽을 수 있게 되는 거예요.

### 실수 #3: `USING`만 있고 `WITH CHECK`가 없는 경우

`USING` 절은 SELECT(읽기)와 DELETE에 적용돼요. INSERT와 UPDATE에는 `WITH CHECK`가 필요해요. 이 두 개를 혼동하거나 `WITH CHECK`를 빠뜨리면 읽기는 막혀도 쓰기는 뚫려요.

자기 데이터만 읽도록 정책을 만들었는데 `WITH CHECK`가 없으면, 다른 사람의 `user_id`로 데이터를 INSERT하는 게 가능해져요. 처음 쓰는 사람들이 자주 놓치는 부분이에요.

### 실수 #4: Service Role 키를 클라이언트에 노출

이건 RLS 자체의 문제가 아니라 사용 방식의 문제예요. `service_role` 키는 RLS를 완전히 우회해요. 이 키가 프론트엔드 코드나 Git 저장소에 들어가는 순간, RLS는 없는 거나 마찬가지예요. `.env` 파일 관리 실수로 GitHub에 올라간 `service_role` 키, 실제로 종종 발견되는 케이스예요.

---

## RLS 정책 접근 방식 비교

| 기준 | 정책 미설정 (RLS OFF) | RLS ON + 정책 없음 | RLS ON + 정확한 정책 |
|------|----------------------|-------------------|---------------------|
| **데이터 접근** | 전체 공개 | 전체 차단 | 역할별 제어 |
| **앱 동작** | 정상 (위험하게) | 데이터 없음 | 정상 (안전하게) |
| **디버깅 난이도** | 쉬움 | 헷갈림 | 보통 |
| **보안 수준** | ❌ 없음 | ⚠️ 과잉 차단 | ✅ 의도대로 |
| **적합한 환경** | 절대 없음 | 없음 | 프로덕션 필수 |

세 번째 열이 목표예요. 그런데 두 번째 상태("RLS 켰는데 왜 안 되지?")에서 디버깅하다 첫 번째 상태로 돌아가는 게 가장 흔한 패턴이에요. 체계적인 정책 설계가 유일한 답인 이유가 바로 여기에 있어요.

---

## 배포 전 RLS 점검 체크리스트

**① 모든 테이블 RLS 활성화 확인**
```sql
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public';
```
`rowsecurity`가 `false`인 테이블이 있으면 즉시 활성화하세요.

**② 정책이 실제로 있는지 확인**
```sql
SELECT tablename, policyname, cmd, roles
FROM pg_policies
WHERE schemaname = 'public';
```
RLS가 켜졌는데 정책이 없는 테이블은 전체 차단 상태예요.

**③ `anon` 역할 정책 재검토**
`TO public` 또는 `TO anon`이 포함된 정책을 전수 확인하고, 의도적으로 공개가 맞는지 검토해요.

**④ INSERT/UPDATE 정책에 `WITH CHECK` 확인**
쓰기 작업이 있는 테이블은 반드시 `WITH CHECK (auth.uid() = user_id)` 형태가 들어가야 해요.

**⑤ `service_role` 키 위치 확인**
프론트엔드 코드, Git 히스토리, CI/CD 환경변수에 `service_role` 키가 없는지 체크하세요.

**⑥ 실제 테스트 수행**
로그인하지 않은 상태로 각 엔드포인트를 직접 호출해서, 막혀야 할 데이터가 실제로 막혀있는지 확인해요.

---

## 다음에 뭘 봐야 할까요

Supabase는 2025년 말부터 RLS 정책 설정을 돕는 대시보드 UI를 개선하고 있어요. 정책 없이 RLS를 켰을 때 경고를 띄우는 기능도 베타로 추가됐죠. 앞으로 6-12개월 안에 정책 문법 오류를 배포 전에 잡아주는 린터 기능이 정식 출시될 가능성이 높아요.

그래도 핵심은 하나예요. **보안은 "나중에"가 없어요.**

RLS 정책 실수로 생기는 보안 취약점 사례 대부분이 "알고 있었는데 나중에 하려고 했어요"로 끝나거든요. 지금 바로 위의 체크리스트 SQL 쿼리 두 개만 돌려보세요.

이미 배포된 프로젝트가 있다면, 지금 로그아웃 상태에서 API를 직접 쳐보는 게 가장 빠른 점검법이에요. 데이터가 나와요? 그럼 오늘 고쳐야 할 이유가 생긴 거예요.

---

*이 글에서 참고한 자료: [Supabase 공식 RLS 문서](https://supabase.com/docs/guides/database/postgres/row-level-security)*

## 참고자료

1. [Row Level Security | Supabase Docs](https://supabase.com/docs/guides/database/postgres/row-level-security)
2. [Supabase에서의 RLS(Row-Level Security) :: Bong's Log](https://bong-day.tistory.com/101)


---

*Photo by [Microsoft Copilot](https://unsplash.com/@microsoftcopilot) on [Unsplash](https://unsplash.com/photos/person-working-at-a-desk-with-a-laptop-and-books-Zcp8xN9DnjM)*
