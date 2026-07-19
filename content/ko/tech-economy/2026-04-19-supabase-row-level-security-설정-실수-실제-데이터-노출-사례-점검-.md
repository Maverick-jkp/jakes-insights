---
title: "Supabase RLS 설정 실수로 인한 데이터 노출 사례와 점검 체크리스트"
date: 2026-04-19T20:01:05+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-security", "supabase", "row", "level", "REST API"]
description: "Supabase RLS 미설정 시 전체 테이블이 누구에게나 노출됩니다. 70만 개 프로젝트 중 실제 발생한 데이터 노출 사례와 설정 실수 유형을 체크리스트로 점검하세요."
image: "/images/20260419-supabase-row-level-security-설정.webp"
technologies: ["REST API", "GitHub Actions", "Supabase"]
faq:
  - question: "Supabase RLS 비활성화 상태에서 anon 키로 데이터 접근 가능한가요"
    answer: "네, Supabase는 테이블 생성 시 RLS가 기본적으로 비활성화되어 있어서 anon 키만 있으면 인증 없이 전체 데이터에 접근할 수 있어요. anon 키는 프론트엔드 코드에 그대로 노출되는 사실상 공개 키이기 때문에, RLS를 명시적으로 활성화하지 않으면 누구나 DB 전체를 조회할 수 있는 상태가 됩니다."
  - question: "Supabase Row Level Security 설정 실수 실제 데이터 노출 사례 점검 체크리스트 어디서 확인하나요"
    answer: "Supabase Row Level Security 설정 실수 실제 데이터 노출 사례 점검 체크리스트는 RLS 비활성화 여부, Policy 존재 여부, auth.uid() 비교 누락, USING (true) 설정 오류 등을 항목별로 확인하는 방식으로 구성돼요. 가장 빠른 점검 방법은 anon 역할로 직접 API 호출 테스트를 해보는 것으로, 인증 없이 데이터가 반환되면 즉시 RLS 설정을 수정해야 합니다."
  - question: "Supabase RLS 활성화했는데 앱이 작동 안 하는 이유"
    answer: "RLS를 활성화하면 Policy가 없을 경우 기본 거부(default deny) 상태가 되어 인증된 사용자 본인의 데이터조차 읽을 수 없어요. 이때 급하게 USING (true) Policy를 추가하면 RLS가 사실상 무력화되므로, 반드시 auth.uid() = user_id 형태의 올바른 Policy를 작성해야 합니다."
  - question: "Supabase Row Level Security 설정 실수 유형 중 가장 흔한 것은 무엇인가요"
    answer: "Supabase Row Level Security 설정 실수 실제 데이터 노출 사례 점검 체크리스트에 따르면, auth.uid() 비교 누락, Policy 범위 오설정, service_role 키 노출 세 가지가 전체 RLS 사고의 70% 이상을 차지해요(Vibe App Scanner 2025년 감사 리포트 기준). 특히 컬럼명을 잘못 참조하는 실수는 Policy가 항상 false를 반환하거나 의도치 않은 데이터를 허용하는 결과로 이어질 수 있습니다."
  - question: "Supabase SELECT Policy만 설정하면 INSERT UPDATE DELETE도 막히나요"
    answer: "아니요, Supabase에서 SELECT Policy는 읽기 접근만 제어하며 INSERT, UPDATE, DELETE는 별도의 Policy를 각각 설정해야 해요. SELECT만 막고 나머지를 설정하지 않으면 인증 여부와 관계없이 쓰기 작업이 전체 허용되는 높은 위험 상태가 됩니다."
aliases:
  - "/tech/2026-04-19-supabase-row-level-security-설정-실수-실제-데이터-노출-사례-점검-/"
  - "/ko/tech/2026-04-19-supabase-row-level-security-설정-실수-실제-데이터-노출-사례-점검-/"

---

DB 스키마를 public으로 열어둔 채 배포한 적 있나요? Supabase를 쓰는 팀 중 상당수가 Row Level Security(RLS) 설정 실수로 사용자 데이터를 통째로 노출하고 있어요. 그것도 모르는 채로.

2026년 현재, Supabase는 전 세계 70만 개 이상의 프로젝트에서 쓰이고 있어요(Supabase 공식 데이터 기준). 빠른 프로토타이핑과 관리형 Postgres 덕분에 스타트업부터 엔터프라이즈까지 퍼졌죠. 그런데 성장 속도만큼 RLS 관련 보안 사고도 늘고 있어요. Supabase 공식 문서에서도 "RLS를 활성화하지 않으면 테이블의 모든 행이 누구에게나 노출된다"고 명시하는데, 이걸 읽고 그냥 넘긴 팀이 얼마나 될까요.

이 글에서는 실제로 자주 발생하는 RLS 설정 실수 유형, 데이터 노출로 이어지는 구체적인 시나리오, 그리고 오늘 바로 쓸 수 있는 점검 체크리스트를 다뤄요.

> **핵심 요약**
> - Supabase RLS는 기본적으로 비활성화 상태예요. 테이블 생성 후 명시적으로 켜지 않으면 anon 키만 있어도 전체 데이터에 접근할 수 있어요.
> - RLS를 활성화해도 Policy가 없으면 "모든 접근 차단" 상태가 돼요. 반쪽짜리 설정도 위험해요.
> - `auth.uid()` 비교 누락, Policy 범위 오설정, service_role 키 노출 등 세 가지 실수가 전체 RLS 사고의 70% 이상을 차지해요(Vibe App Scanner, 2025년 RLS 감사 리포트 기준).
> - Supabase Row Level Security 설정 실수를 잡아내는 가장 빠른 방법은 anon 역할로 직접 API 호출 테스트를 해보는 거예요.

---

## RLS가 왜 갑자기 이슈가 됐나요

Supabase는 2020년 출시 이후 빠르게 퍼졌어요. 특히 "클라이언트에서 직접 DB에 붙는" 구조가 인기였는데, 이게 양날의 검이에요.

기존 백엔드 아키텍처라면 API 서버가 중간에서 권한을 걸러줬겠죠. 그런데 Supabase는 클라이언트가 직접 PostgREST API를 통해 DB에 접근해요. 중간 필터가 없다는 거예요. 그 역할을 RLS가 대신해야 하는데, 설정을 잘못하면 막아야 할 문이 열려있는 셈이에요.

2025년 Vibe App Scanner가 공개한 RLS 감사 결과에 따르면, 분석 대상 Supabase 프로젝트 중 약 34%가 하나 이상의 테이블에서 RLS를 아예 비활성화한 상태였어요. 그중 절반은 `users` 또는 `profiles` 테이블이었고요. 이름만 봐도 민감한 데이터들이잖아요.

이유는 단순해요.

- Supabase Dashboard에서 테이블을 만들면 **RLS는 기본 비활성화 상태**예요.
- 공식 문서 퀵스타트 가이드가 RLS 설정을 나중으로 미루게 유도하는 흐름이에요.
- "일단 작동하게 만들자"는 개발 속도 압박이 보안 설정을 뒤로 밀어요.

문제는 이게 프로토타입에서 프로덕션으로 그대로 넘어간다는 거예요.

---

## 실제 데이터 노출이 일어나는 패턴 세 가지

### 패턴 1: RLS 자체가 꺼져 있어요

제일 흔한 케이스예요. 테이블에 RLS가 비활성화된 상태에서 PostgREST에 `anon` 역할로 요청을 보내면 전체 데이터가 반환돼요. 별도 인증 없이요.

```sql
-- 이 상태라면 누구나 전체 rows를 볼 수 있어요
SELECT * FROM profiles; -- RLS 꺼진 테이블에서
```

Supabase 공식 문서는 "RLS가 비활성화된 테이블은 superuser를 포함한 모든 역할에 데이터를 노출한다"고 명시해요. `anon` 키는 사실상 공개 키예요. 프론트엔드 코드에 그냥 박혀 있는 경우가 많죠.

### 패턴 2: RLS는 켰는데 Policy가 없어요

RLS를 활성화하면 "기본 거부(default deny)" 상태가 돼요. Policy가 없으면 아무도 데이터를 못 읽어요. 본인 포함해서요. 그러면 앱이 작동을 안 하니까, 급하게 이런 Policy를 추가하는 경우가 생겨요.

```sql
-- 위험한 Policy 예시: 모든 사용자에게 모든 접근 허용
CREATE POLICY "Allow all" ON profiles
  FOR ALL USING (true);
```

`USING (true)` 하나로 RLS가 사실상 무력화돼요. "켜져 있지만 아무것도 막지 않는" 최악의 상태예요.

### 패턴 3: `auth.uid()` 비교가 빠졌어요

올바른 RLS Policy는 요청한 사람의 ID와 데이터의 소유자 ID를 비교해야 해요.

```sql
-- 올바른 Policy
CREATE POLICY "Users can view own profile" ON profiles
  FOR SELECT USING (auth.uid() = user_id);

-- 잘못된 Policy (컬럼명 참조 미스)
CREATE POLICY "Users can view own profile" ON profiles
  FOR SELECT USING (auth.uid() = id); -- id 컬럼이 user_id가 아닐 때
```

컬럼명 하나 잘못 참조했을 뿐인데, Policy가 항상 false를 반환하거나 예상치 못한 행을 허용할 수 있어요.

### RLS 설정 방식 비교

| 설정 상태 | anon 접근 | 인증 사용자 접근 | 실제 위험도 |
|-----------|-----------|-----------------|------------|
| RLS 비활성화 | 전체 노출 | 전체 노출 | 🔴 매우 높음 |
| RLS 활성화 + Policy 없음 | 완전 차단 | 완전 차단 | 🟡 앱 작동 불가 |
| RLS 활성화 + `USING (true)` | 전체 노출 | 전체 노출 | 🔴 매우 높음 |
| RLS 활성화 + 올바른 Policy | 차단 | 본인 데이터만 | 🟢 안전 |
| RLS 활성화 + INSERT Policy 누락 | 쓰기 전체 허용 | 쓰기 전체 허용 | 🟠 높음 |

INSERT, UPDATE, DELETE는 별도의 Policy가 필요해요. SELECT만 막고 나머지를 열어둔 경우도 자주 발견돼요.

---

## 지금 바로 쓰는 점검 체크리스트

**Step 1 — 모든 테이블 RLS 활성화 여부 확인**

```sql
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public';
```

`rowsecurity`가 `false`인 테이블이 있다면 즉시 활성화해야 해요.

```sql
ALTER TABLE your_table ENABLE ROW LEVEL SECURITY;
```

**Step 2 — Policy 목록 전체 조회**

```sql
SELECT schemaname, tablename, policyname, cmd, qual
FROM pg_policies
WHERE schemaname = 'public';
```

`qual`이 `true`인 Policy가 있다면 경고예요.

**Step 3 — anon 역할로 실제 API 호출 테스트**

```bash
curl 'https://your-project.supabase.co/rest/v1/profiles' \
  -H "apikey: your-anon-key" \
  -H "Authorization: Bearer your-anon-key"
```

데이터가 반환된다면 RLS가 올바르게 설정되지 않은 거예요.

**Step 4 — INSERT/UPDATE/DELETE Policy도 확인**

많은 팀이 SELECT Policy만 설정하고 끝내요. 각 작업별로 Policy가 있는지 확인해요.

```sql
SELECT tablename, cmd, COUNT(*) as policy_count
FROM pg_policies
WHERE schemaname = 'public'
GROUP BY tablename, cmd;
```

**Step 5 — service_role 키가 클라이언트에 노출됐는지 확인**

`service_role` 키는 RLS를 완전히 우회해요. 프론트엔드 코드, 환경변수, GitHub 저장소에 절대로 있으면 안 돼요. `.env.local`을 `.gitignore`에 넣었는지 확인하고, 커밋 이력에 있다면 즉시 키를 재발급해야 해요.

---

## 실제로 이렇게 대응해요: 시나리오별 접근

**시나리오 A — 기존 프로젝트를 점검해야 하는 경우**

Step 1-2 SQL 쿼리부터 실행해요. 노출된 테이블 목록을 뽑은 다음, 민감 데이터(이메일, 결제 정보, 개인 식별 정보)가 있는 테이블부터 우선 처리해요. Policy 작성이 막막하다면 Supabase 공식 문서의 `auth.uid() = user_id` 패턴을 기본으로 삼으세요.

**시나리오 B — 새 프로젝트를 시작하는 경우**

테이블 생성과 동시에 RLS를 켜는 습관을 들이세요. Supabase Dashboard의 Table Editor에는 테이블 생성 시 "Enable Row Level Security" 체크박스가 있어요. 처음부터 체크하고 시작하면 나중에 뒤집는 수고를 덜어요.

**그리고 앞으로 주시해야 할 것들**

- Supabase가 2026년 로드맵에서 "RLS 자동 감사 기능"을 예고했어요. Dashboard에서 잠재적 취약점을 자동으로 경고해주는 방향이에요.
- GitHub Actions나 CI 파이프라인에 `supabase db lint` 명령어를 넣어두면 배포 전에 Policy 누락을 잡을 수 있어요.

---

## 결론: 한 번의 점검이 큰 사고를 막아요

정리하면 이래요.

- RLS는 Supabase에서 유일한 행 단위 접근 제어 수단이에요. 빠지면 다른 것으로 대체할 수 없어요.
- 가장 흔한 RLS 설정 실수는 "RLS 비활성화", "`USING (true)` Policy", "INSERT/UPDATE 누락" 세 가지예요.
- 점검은 SQL 쿼리 세 줄과 anon API 호출 테스트로 10분 안에 끝나요.
- `service_role` 키 노출은 RLS를 완전히 무의미하게 만들어요.

지금 당장 프로젝트 하나만 골라서 Step 1 쿼리를 실행해 보세요. `rowsecurity = false`인 테이블이 나온다면, 오늘 이 글이 꽤 의미 있었던 거예요. RLS 점검은 선택이 아니라 배포 전 기본 체크리스트예요. 여러분 팀의 체크리스트에는 지금 이 항목이 있나요?

## 참고자료

1. [Row Level Security | Supabase Docs](https://supabase.com/docs/guides/database/postgres/row-level-security)
2. [Supabase Row Level Security (RLS) — Test & Fix Your Policies](https://vibeappscanner.com/supabase-row-level-security)


---

*Photo by [Drew Williams](https://unsplash.com/@kingswagger) on [Unsplash](https://unsplash.com/photos/flavor-list-life-is-too-short-to-be-bland-screengrab-oD_qxhNrSB8)*
