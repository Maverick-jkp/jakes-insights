---
title: "Supabase RLS 삽질 후기: 멀티테넌트 SaaS 데이터 격리 실무 적용기"
date: 2026-05-25T22:53:36+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-security", "supabase", "row", "level", "PostgreSQL"]
description: "Supabase RLS 기본값 비활성화로 테넌트 간 데이터 노출 사고를 겪은 실제 경험. tenant_id 컬럼 방식과 JWT 클레임 방식의 성능·유지보수 트레이드오프, RLS 정책과 인덱스 병행 설계"
image: "/images/20260525-supabase-row-level-security-실무.webp"
technologies: ["PostgreSQL", "Supabase"]
faq:
  - question: "Supabase RLS 활성화 안 하면 어떻게 되나요"
    answer: "Supabase에서 테이블을 생성하면 RLS가 기본적으로 비활성화 상태라서, 별도로 켜지 않으면 anon 키만 있어도 누구나 테이블 전체 데이터를 읽을 수 있습니다. 멀티테넌트 SaaS 환경에서는 이 설정 하나만 놓쳐도 서로 다른 테넌트의 데이터가 뒤섞여 노출되는 치명적인 데이터 유출로 이어질 수 있습니다."
  - question: "Supabase Row Level Security 실무 적용 멀티테넌트 SaaS 설계에서 tenant_id 인덱스가 왜 필요한가요"
    answer: "'Supabase Row Level Security 실무 적용 멀티테넌트 SaaS 설계 삽질 후기 2025'에서 강조하듯, RLS 정책에서 tenant_id로 필터링할 때 인덱스가 없으면 PostgreSQL이 매 쿼리마다 테이블 전체를 풀스캔합니다. 실제 사례에서 수십만 행 규모의 테이블에 인덱스 하나가 없어 프로덕션 응답 시간이 8초까지 치솟은 경우도 있었으므로, RLS 정책과 인덱스는 반드시 함께 설계해야 합니다."
  - question: "Supabase RLS JWT 클레임 방식 vs 조인 방식 차이점 뭔가요"
    answer: "JWT 클레임 방식은 토큰 파싱만으로 tenant_id를 확인해 속도가 빠르지만, 테넌트 권한 변경 시 사용자가 재로그인해야 반영된다는 단점이 있습니다. 반면 users 테이블 조인 방식은 DB 수정만으로 권한이 즉시 반영되지만 매 쿼리마다 조인이 발생해 트래픽이 몰릴 때 병목이 생길 수 있어, 실무에서는 기본 테넌트 격리는 JWT 클레임으로 처리하고 세밀한 권한은 별도 permissions 테이블로 관리하는 조합 방식이 검증된 패턴입니다."
  - question: "Supabase service_role 키 프론트엔드에 써도 되나요"
    answer: "Supabase의 service_role 키는 RLS를 완전히 우회하기 때문에 절대 클라이언트 사이드나 프론트엔드에 노출해서는 안 됩니다. 이 키는 백엔드 서버의 관리자 작업 전용으로만 사용해야 하며, 프론트엔드에 노출될 경우 모든 RLS 정책이 무력화되어 전체 데이터베이스가 무방비 상태가 됩니다."
  - question: "Supabase Row Level Security 실무 적용 멀티테넌트 SaaS 설계 할 때 기존 테이블 마이그레이션 순서 어떻게 되나요"
    answer: "'Supabase Row Level Security 실무 적용 멀티테넌트 SaaS 설계 삽질 후기 2025'에 따르면, 기존 테이블에 RLS를 적용할 때는 tenant_id 컬럼 추가 및 데이터 채우기 → tenant_id 인덱스 생성 → RLS 활성화 및 정책 작성 → 다른 테넌트 JWT로 직접 쿼리 날려 격리 검증 순서로 진행해야 합니다. 특히 인덱스를 RLS 활성화보다 먼저 만들어야 정책 적용 직후 발생할 수 있는 성능 문제를 예방할 수 있습니다."
---

프로덕션 배포 직전에 테넌트 A 데이터가 테넌트 B 화면에 뜨는 걸 발견했어요. 식은땀이 나더라고요. Supabase RLS를 "대충 켜놓으면 되겠지"라고 생각했던 게 문제였어요.

> **핵심 요약**
> - Supabase RLS는 기본값이 "비활성화"라서, 테이블을 만들고 RLS를 켜지 않으면 모든 행이 노출된다.
> - 멀티테넌트 SaaS에서 `tenant_id` 기반 RLS 정책 없이 `anon` 또는 `authenticated` role만 쓰면, 서로 다른 테넌트가 동일 데이터를 볼 수 있다.
> - `auth.uid()`와 JWT 클레임을 연결하는 방식 vs. 별도 `tenant_id` 컬럼 방식은 성능과 유지보수 면에서 명확한 트레이드오프가 있다.
> - RLS 정책은 인덱스와 함께 설계하지 않으면, 정책 자체가 쿼리 플랜의 병목이 된다.

---

## RLS가 헷갈리는 진짜 이유

Supabase는 PostgreSQL 위에 올라가 있어요. RLS는 PostgreSQL 네이티브 기능인데, **테이블 생성 시 기본으로 꺼져 있어요.** 이게 함정이에요.

Dashboard에서 테이블을 만들면 `Enable RLS` 버튼이 눈에 잘 안 띄어요. 처음 쓰는 팀이라면 열 명 중 일곱은 그냥 지나쳐요. RLS를 활성화하지 않으면, `anon` 키만 있으면 누구나 테이블 전체를 읽을 수 있어요. 공개 API라면 이건 그냥 데이터 유출이에요.

멀티테넌트 SaaS는 상황이 더 복잡해요. 여러 회사가 같은 DB를 공유하는 구조에서, 테넌트 격리를 애플리케이션 레이어에만 맡기면 버그 하나에 전체 격리가 무너져요. RLS를 DB 레이어에서 강제하면, 앱 코드가 잘못돼도 DB가 막아줘요. 이게 핵심이에요.

---

## 삽질의 본론: 세 가지 실수 패턴

### 정책은 켰는데 조건이 없는 경우

이런 정책을 만든 팀들이 꽤 있어요.

```sql
CREATE POLICY "allow all authenticated"
ON public.documents
FOR ALL
USING (auth.role() = 'authenticated');
```

"로그인한 사람만 보게 하면 되지"라는 생각이었는데, 이건 로그인한 모든 사용자가 테이블 전체를 볼 수 있다는 뜻이에요. `authenticated`는 "인증됨"이지 "내 테넌트 사용자"가 아니거든요. 올바른 방향은 이래요.

```sql
CREATE POLICY "tenant isolation"
ON public.documents
FOR ALL
USING (tenant_id = (auth.jwt() ->> 'tenant_id')::uuid);
```

JWT 토큰 안에 `tenant_id` 클레임을 넣고, 각 행의 `tenant_id`와 비교하는 구조예요.

### JWT 클레임 방식 vs. 조인 방식

실무에서 가장 많이 갈리는 지점이에요.

| 비교 항목 | JWT 클레임 방식 | `users` 테이블 조인 방식 |
|-----------|----------------|------------------------|
| 성능 | 빠름 (토큰 파싱만) | 느림 (매 쿼리마다 조인) |
| 유지보수 | 토큰 재발급 필요 | DB만 수정하면 즉시 반영 |
| 테넌트 변경 시 | 재로그인 필요 | 즉시 반영 |
| 추천 규모 | 소규모~중규모 | 대규모, 권한 변경 잦을 때 |

JWT 방식은 빠르지만, 테넌트 권한을 실시간으로 바꿔야 하는 구조에선 불편해요. 사용자가 재로그인해야 변경 사항이 반영되거든요. 반면 조인 방식은 트래픽이 몰릴 때 병목이 생겨요.

실무에서 검증된 패턴은 조합이에요. 기본 테넌트 격리는 JWT 클레임으로 빠르게 처리하고, 세밀한 권한은 별도 `permissions` 테이블로 관리해요.

### 인덱스 없이 RLS 걸면 생기는 일

뒤늦게 발견하는 경우가 많아요. `tenant_id`로 필터링하는데 인덱스가 없으면, PostgreSQL은 매 쿼리마다 테이블 전체를 스캔해요. 행 수가 수십만 개가 넘으면 쿼리 하나에 수 초가 걸리기 시작해요.

```sql
CREATE INDEX idx_documents_tenant_id ON public.documents(tenant_id);
```

이 한 줄이 없어서 프로덕션 응답 시간이 8초까지 튄 사례가 실제로 있어요. RLS와 인덱스는 세트로 설계해야 해요.

---

## 실무 적용: 어디서부터 시작할까

**기존 테이블 마이그레이션**이라면 순서가 중요해요.

1. `tenant_id` 컬럼 추가 후 기존 데이터에 값 채우기
2. `tenant_id` 인덱스 먼저 생성
3. RLS 활성화 후 정책 작성
4. 다른 테넌트 JWT로 쿼리를 직접 날려서 격리 검증

**신규 테이블 설계**라면 처음부터 `tenant_id UUID NOT NULL` 컬럼을 모든 테이블에 박아두는 게 낫고, RLS 정책 템플릿을 팀 내 공유 문서로 만들어두면 실수가 줄어요.

한 가지 더. Supabase의 `service_role` 키는 RLS를 우회해요. 백엔드 서버 관리자 작업에만 써야 하고, 클라이언트 사이드에 절대 노출하면 안 돼요. 이걸 모르고 프론트엔드에 박아둔 팀도 있었어요.

---

## 앞으로 어떻게 될까

Supabase는 현재 RLS 정책 디버깅 도구를 지속 개선 중이에요. `EXPLAIN` 결과에서 RLS 정책 작동 방식을 시각화해주는 기능이 로드맵에 올라와 있어요. 나오면 지금처럼 쿼리 플랜을 직접 파헤쳐야 하는 불편함이 많이 줄어들 거예요.

삽질을 피하는 가장 빠른 방법은 "정책 먼저, 기능 나중"이에요. 인덱스, JWT 설계, 정책 검증을 프로젝트 초기에 잡지 않으면 프로덕션 데이터를 건드리면서 고쳐야 해요. 그게 진짜 삽질이거든요.

**지금 당장 해볼 것**: 현재 운영 중인 Supabase 프로젝트가 있다면, Dashboard에서 각 테이블의 RLS 활성화 여부와 `tenant_id` 인덱스 존재 여부를 확인해 보세요. 생각보다 구멍이 있을 수도 있어요.

여러분 팀은 멀티테넌트 격리를 DB 레이어에서 처리하고 있나요, 아니면 애플리케이션 레이어에 의존하고 있나요?

## 참고자료

1. [Enforcing Row Level Security in Supabase: A Deep Dive into LockIn's Multi-Tenant Architecture - DEV ](https://dev.to/blackie360/-enforcing-row-level-security-in-supabase-a-deep-dive-into-lockins-multi-tenant-architecture-4hd2)
2. [Supabase RLS Guide: Policies That Actually Work](https://designrevision.com/blog/supabase-row-level-security)
3. [Row Level Security | Supabase Docs](https://supabase.com/docs/guides/database/postgres/row-level-security)


---

*Photo by [Houston SEO Directory](https://unsplash.com/@houstonseodirectory123) on [Unsplash](https://unsplash.com/photos/a-group-of-people-standing-next-to-each-other-thhmvPHboM0)*
