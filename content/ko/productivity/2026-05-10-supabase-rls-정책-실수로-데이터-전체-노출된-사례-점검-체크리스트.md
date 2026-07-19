---
title: "Supabase RLS 정책 실수로 데이터 전체 노출된 사례 점검 체크리스트"
date: 2026-05-10T20:15:28+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-web", "supabase", "rls", "\uc2e4\uc218\ub85c", "Next.js"]
description: "Supabase RLS 정책 실수로 프로덕션 DB 전체가 노출되는 사고, 2025년에도 반복되고 있습니다. GDPR 위반까지 이어질 수 있는 설정 오류 유형과 실전 점검 체크리스트를 확인하세요."
image: "/images/20260510-supabase-rls-정책-실수로-데이터-전체-노출된.webp"
technologies: ["Next.js", "PostgreSQL", "Supabase"]
faq:
  - question: "Supabase RLS 활성화했는데 데이터가 빈 배열로 반환되는 이유"
    answer: "RLS를 활성화한 후 정책을 하나도 작성하지 않으면 PostgreSQL 기본값에 의해 모든 행이 차단되어 빈 배열이 반환됩니다. 'Supabase RLS 정책 실수로 데이터 전체 노출된 사례 점검 체크리스트'에서도 이 패턴이 가장 흔한 실수 중 하나로 꼽히며, RLS 활성화 후 반드시 SELECT·INSERT·UPDATE·DELETE 각각에 대한 명시적 정책을 작성해야 합니다."
  - question: "Supabase service_role 키 프론트엔드에 넣으면 안 되는 이유"
    answer: "service_role 키는 RLS를 완전히 우회하도록 설계된 서버 전용 키로, 클라이언트 코드에 포함되면 브라우저에서 그대로 노출되어 DB 전체 데이터에 인증 없이 접근 가능해집니다. 특히 Next.js에서 NEXT_PUBLIC_ 접두사를 붙이면 빌드 결과물에 포함되므로, 반드시 서버 사이드 환경변수로만 관리해야 합니다."
  - question: "Supabase anon 키로 전체 테이블 데이터 조회되는 문제 해결법"
    answer: "'Supabase RLS 정책 실수로 데이터 전체 노출된 사례 점검 체크리스트'에 따르면, 이 문제는 RLS가 비활성화된 테이블에 anon 키로 API를 호출할 때 발생합니다. Supabase 대시보드에서 해당 테이블의 RLS를 즉시 활성화하고, auth.uid() = user_id 조건의 정책을 각 작업(SELECT, INSERT, UPDATE, DELETE)별로 추가해야 합니다."
  - question: "Supabase RLS USING true 정책 위험한가요"
    answer: "USING (true) 조건의 정책은 인증 여부와 관계없이 모든 사용자가 해당 테이블의 전체 행을 읽을 수 있게 허용하므로 프로덕션 환경에서는 절대 사용하면 안 됩니다. 개발 편의를 위해 임시로 추가한 뒤 삭제를 잊어버리는 경우가 많아, 배포 전 정책 목록을 반드시 재검토해야 합니다."
  - question: "Supabase RLS INSERT UPDATE 정책 빠뜨리면 어떻게 되나요"
    answer: "SELECT 정책만 설정하고 INSERT나 UPDATE 정책을 누락하면, 로그인하지 않은 사용자가 데이터를 삽입하거나 다른 사용자의 행을 덮어쓸 수 있는 심각한 보안 취약점이 생깁니다. 각 작업마다 auth.uid() = user_id 조건을 적용하되, INSERT와 UPDATE는 USING과 WITH CHECK를 함께 사용하는 것이 권장됩니다."
aliases:
  - "/tech/2026-05-10-supabase-rls-정책-실수로-데이터-전체-노출된-사례-점검-체크리스트/"
  - "/ko/tech/2026-05-10-supabase-rls-정책-실수로-데이터-전체-노출된-사례-점검-체크리스트/"

---

프로덕션 DB에 저장된 사용자 데이터가 통째로 외부에 노출된다면? 이건 그냥 버그가 아니에요. RLS 설정 실수 하나가 GDPR 위반, 개인정보보호법 제재, 그리고 서비스 신뢰도 붕괴로 이어질 수 있거든요. Supabase를 쓰는 스타트업과 인디 개발자가 폭발적으로 늘면서 이 문제가 조용히, 하지만 빠르게 퍼지고 있어요.

Supabase는 PostgreSQL 기반의 오픈소스 백엔드 플랫폼이에요. 편리한 만큼 RLS(Row Level Security) 정책을 잘못 설정하면 테이블 전체 데이터가 아무 인증 없이 읽히는 상황이 생겨요. 개발자 커뮤니티 GitHub Issue 트래커와 Reddit의 r/Supabase 스레드를 보면, 2025년 한 해에만 RLS 미설정이나 잘못된 정책으로 인한 데이터 노출 관련 보고가 수십 건 올라왔죠.

> **핵심 요약**
> - Supabase에서 RLS를 활성화하지 않으면 anon 키만 있어도 테이블 전체 데이터를 조회할 수 있어요.
> - 가장 흔한 실수는 "RLS 활성화 후 정책 미작성" 패턴으로, 이 경우 아무도 데이터를 읽지 못하거나 반대로 누구나 읽게 돼요.
> - `auth.uid()`를 쓴 정책이라도 service_role 키와 함께 쓰면 RLS가 우회(bypass)돼요.
> - Supabase 공식 문서는 2025년 말 기준 RLS 설정 가이드를 대폭 개편했고, 테이블 생성 시 RLS 기본값을 "비활성화"로 두는 구조 자체가 실수를 유발하는 설계상 문제예요.

---

## RLS가 이렇게 자주 틀리는 이유

Supabase의 매력은 빠른 프로토타이핑이에요. 대시보드에서 테이블 만들고 API 키 넣으면 바로 데이터를 읽고 쓸 수 있죠. 근데 이게 함정이에요.

PostgreSQL은 테이블을 만들 때 기본적으로 RLS가 꺼져 있어요. Supabase도 마찬가지예요. 그래서 `anon` 키(공개 키)로 API를 쓰면, RLS가 꺼진 테이블은 인증 없이도 전부 조회돼요. Supabase 공식 문서에서도 이 점을 명확히 경고하고 있어요.

실제로 커뮤니티에서 반복되는 패턴은 딱 세 가지예요.

**첫째, RLS 자체를 안 켠 케이스.** 개발 중엔 편의상 꺼두고, 프로덕션 배포 때 켜는 걸 잊어버리는 거예요.

**둘째, RLS는 켰는데 정책을 하나도 안 만든 케이스.** 이러면 PostgreSQL 기본값 때문에 아무도 데이터를 못 읽어요. "API가 갑자기 빈 배열을 반환한다"는 질문의 절반 이상이 여기서 나와요.

**셋째, `service_role` 키를 클라이언트 코드에 직접 박은 케이스.** 이 키는 RLS를 우회하도록 설계됐어요. 서버 사이드 전용이어야 하는데 프론트엔드 `.env` 파일에 넣어버리면 사실상 전체 DB가 공개되는 거예요.

---

## 주요 취약 패턴 심층 분석

### 패턴 1: "RLS 활성화 + 정책 없음" 조합의 역설

많은 개발자가 "RLS 켰으니까 안전하겠지"라고 생각해요. 틀렸어요.

RLS를 활성화하면 PostgreSQL은 명시적 정책이 없는 한 기본적으로 모든 행을 차단해요. 앱은 동작하는 것처럼 보이지만 제대로 안 돌아가고, 여기서 개발자가 "일단 다 허용하는 정책"을 추가하면 문제가 생겨요.

```sql
-- 이 정책은 프로덕션에 절대 쓰면 안 돼요
CREATE POLICY "allow_all" ON profiles
  FOR SELECT USING (true);
```

`USING (true)`는 "누구나 모든 행을 읽어요"라는 뜻이에요. 개발 편의로 추가하고 지우는 걸 잊으면, 프로덕션에서 전체 사용자 프로필이 공개되는 사태가 발생해요.

### 패턴 2: `auth.uid()` 정책을 제대로 안 쓰는 경우

올바른 RLS 정책은 보통 이렇게 생겼어요.

```sql
CREATE POLICY "users_own_data" ON profiles
  FOR SELECT USING (auth.uid() = user_id);
```

그런데 개발자들이 자주 빠지는 함정이 있어요. `INSERT`나 `UPDATE` 정책을 빠뜨리는 거예요. `SELECT`에만 정책을 걸고 `INSERT`엔 정책이 없으면 로그인 안 한 사용자도 데이터를 삽입할 수 있어요. `UPDATE` 정책이 누락되면 다른 사용자의 행을 덮어쓸 수도 있고요.

| 작업 | 정책 미설정 시 동작 | 권장 정책 조건 |
|------|-------------------|---------------|
| SELECT | 전체 차단 (RLS 켜진 경우) | `auth.uid() = user_id` |
| INSERT | 전체 허용 또는 전체 차단 | `auth.uid() = user_id` (WITH CHECK) |
| UPDATE | 전체 차단 또는 타인 행 수정 가능 | `auth.uid() = user_id` (USING + WITH CHECK) |
| DELETE | 전체 차단 또는 타인 행 삭제 가능 | `auth.uid() = user_id` |

### 패턴 3: service_role 키 클라이언트 노출

이건 가장 치명적이에요. `service_role` 키는 JWT에 `"role": "service_role"` 클레임이 포함되는데, Supabase는 이 역할이 감지되면 RLS를 완전히 건너뛰어요.

Next.js 앱에서 `.env.local`에 `NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY`라고 써두면 빌드 결과물에 그대로 포함돼서 브라우저에서 읽힐 수 있어요. `NEXT_PUBLIC_` 접두사가 붙으면 클라이언트에 노출된다는 걸 모르고 쓰는 경우가 많아요.

### Supabase RLS 설정 방식 비교

| 방식 | 보안 수준 | 설정 난이도 | 실수 가능성 | 추천 상황 |
|------|----------|------------|------------|----------|
| RLS 비활성화 | ❌ 없음 | 쉬움 | 높음 | 개발 초기 로컬 전용 |
| RLS 활성화 + 정책 없음 | ⚠️ 데이터 차단 | 중간 | 높음 | 피해야 함 |
| RLS + 세밀한 정책 | ✅ 높음 | 어려움 | 낮음 | 프로덕션 필수 |
| RLS + Edge Functions | ✅ 매우 높음 | 어려움 | 낮음 | 복잡한 권한 로직 |

---

## 점검 체크리스트: 지금 바로 확인하세요

배포 전에 이 항목들을 순서대로 확인해 보세요.

**[필수 점검 항목]**

- `[ ]` 모든 테이블에 RLS가 활성화돼 있나요? (`SELECT relname, relrowsecurity FROM pg_class WHERE relkind = 'r'`로 확인 가능해요)
- `[ ]` SELECT, INSERT, UPDATE, DELETE 각각에 정책이 존재하나요?
- `[ ]` `USING (true)` 또는 `WITH CHECK (true)` 정책이 프로덕션 코드에 남아있지 않나요?
- `[ ]` `service_role` 키가 클라이언트 번들에 포함되지 않았나요?
- `[ ]` `anon` 키로 직접 API 호출 시 민감 데이터가 반환되지 않나요? (Table Editor의 "Preview as anon" 기능으로 바로 확인 가능해요)
- `[ ]` Storage 버킷에도 RLS 정책이 적용돼 있나요? (테이블만 챙기고 Storage는 빠뜨리는 경우 많아요)
- `[ ]` Edge Function 내 Supabase 클라이언트가 `service_role` 키를 쓸 때, 그 함수가 외부 요청을 그대로 신뢰하지 않나요?

---

## 앞으로 뭘 봐야 하나요?

이 문제의 핵심은 "개발 편의"와 "보안 기본값" 사이의 긴장이에요.

Supabase 팀은 2025년 12월 업데이트에서 새 테이블 생성 UI에 RLS 기본 활성화 옵션을 추가했어요. 하지만 CLI나 SQL로 직접 테이블을 만들 때는 여전히 기본값이 비활성화예요. 이 불일치가 2026년에도 계속 사고를 만들 가능성이 있어요.

**당장 해야 할 것:** 프로젝트 대시보드에서 "Database > Tables"로 가서 각 테이블의 RLS 상태를 확인하세요. Table Editor 상단의 "Preview as anon" 버튼으로 인증 없이 어떤 데이터가 보이는지 직접 눈으로 확인하는 게 제일 빠른 방법이에요.

**6개월 내 주시할 것:** Supabase가 발표한 "Security Advisor" 기능이 2026년 중 정식 출시될 예정이에요. RLS 미설정 테이블을 자동으로 감지하고 경고를 띄워줘요. 출시되면 이 체크리스트의 절반은 자동화될 수 있어요.

---

## 마무리: 한 번 뚫리면 되돌릴 수 없어요

정리하면 이래요.

- RLS 활성화는 필요조건이지 충분조건이 아니에요. 정책까지 작성해야 해요.
- `service_role` 키는 서버 사이드 전용이에요. 클라이언트에 절대 노출시키면 안 돼요.
- 테이블만 챙기지 말고 Storage 버킷도 함께 점검하세요.
- `USING (true)` 정책은 개발 단계에서만 쓰고, 배포 전 반드시 제거하세요.

앞으로 6-12개월 안에 Supabase의 자동 보안 스캔 기능이 자리잡으면 이런 실수가 줄어들 거예요. 그런데 그 기능이 나오기 전까지 수천 개의 Supabase 프로젝트가 지금 이 순간에도 RLS 없이 돌아가고 있어요.

지금 당장 프로젝트 대시보드를 열어보세요. "Preview as anon"으로 뭐가 보이는지 확인하는 데 30초면 충분해요. 그 30초가 나중에 수백만 원의 벌금과 사용자 신뢰를 지킬 수 있어요.

---

*References: Supabase Official Documentation — RLS Simplified (supabase.com/docs/guides/troubleshooting/rls-simplified), PostgreSQL Row Security Policies (postgresql.org/docs/current/ddl-rowsecurity.html)*

## 참고자료

1. [Supabase Docs | Troubleshooting | RLS Simplified](https://supabase.com/docs/guides/troubleshooting/rls-simplified-BJTcS8)


---

*Photo by [NASA](https://unsplash.com/@nasa) on [Unsplash](https://unsplash.com/photos/photo-of-outer-space-Q1p7bh3SHj8)*
