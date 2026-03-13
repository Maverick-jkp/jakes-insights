---
title: "Supabase RLS 실무 적용 실수 모음과 서비스 키 클라이언트 노출 사고 후기"
date: 2026-03-13T19:50:23+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-security", "supabase", "row", "level", "Next.js"]
description: "Supabase RLS 설정 실수와 service_role 키 클라이언트 노출 사고 후기. 프로덕션 배포 후 DB 전체가 열린 실제 사례로, 반복되는 3가지 실수 패턴과 키 노출이 일어나는 구체적 원인을"
image: "/images/20260313-supabase-row-level-security-실무.webp"
technologies: ["Next.js", "PostgreSQL", "Vite", "Supabase"]
faq:
  - question: "Supabase RLS 켰는데 앱이 전혀 안 될 때 해결법"
    answer: "RLS를 활성화하면 기본값이 '모든 접근 거부(DEFAULT DENY)'로 작동하기 때문에, 정책(Policy)을 별도로 만들지 않으면 앱이 데이터를 전혀 불러오지 못해요. 'Supabase Row Level Security 실무 적용 실수 모음 서비스 키 클라이언트 노출 사고 후기'에서 지적하듯, RLS 활성화와 정책 생성은 완전히 별개 작업이에요. SELECT 접근을 허용하려면 'CREATE POLICY ... FOR SELECT USING (auth.uid() = user_id)' 형태로 허용 정책을 직접 작성해야 해요."
  - question: "Supabase service_role 키 프론트엔드에 넣으면 안 되는 이유"
    answer: "service_role 키는 RLS를 완전히 우회하도록 설계된 서버 전용 키라서, 클라이언트 코드에 포함되는 순간 브라우저 DevTools나 소스 코드에서 누구나 꺼낼 수 있어요. 키를 획득한 외부인은 RLS 정책과 무관하게 데이터베이스 전체에 무제한 접근이 가능해요. 특히 Next.js에서 NEXT_PUBLIC_ 접두사로 환경 변수를 설정하면 클라이언트에 자동 노출되므로 절대 사용하면 안 돼요."
  - question: "Supabase service_role 키 GitHub에 올라갔을 때 대처 방법"
    answer: "'Supabase Row Level Security 실무 적용 실수 모음 서비스 키 클라이언트 노출 사고 후기'에 따르면 키가 노출된 즉시 Supabase 대시보드 Settings → API에서 키를 롤(rotate)해 기존 키를 무효화해야 해요. GitHub에서 파일을 삭제해도 git history에 키가 남아있으므로 삭제만으로는 충분하지 않아요. 키 재발급 후 서버 환경 변수를 새 키로 업데이트하고, 노출 기간 동안의 접근 로그를 반드시 점검해야 해요."
  - question: "Supabase RLS USING (true) 정책 써도 되나요"
    answer: "USING (true)는 해당 테이블의 모든 행에 대해 접근을 허용하는 설정으로, RLS를 켜놓은 것과 사실상 동일한 효과를 내요. 임시로 앱을 동작시키려고 쓰는 경우가 많지만 프로덕션에 그대로 배포되는 사례가 반복되고 있어요. 올바른 방법은 'USING (auth.uid() = user_id)' 처럼 인증된 사용자가 본인 데이터만 접근하도록 명시적으로 제한하는 거예요."
  - question: "Supabase JOIN 쿼리할 때 RLS 우회되는 문제 해결법"
    answer: "한 테이블에만 RLS를 적용하고 연관 테이블에는 적용하지 않으면, JOIN 시 RLS가 없는 테이블의 데이터가 필터링 없이 그대로 반환돼요. 예를 들어 orders 테이블에 RLS를 걸었더라도 products 테이블에 RLS가 없으면 JOIN을 통한 우회 접근이 가능해요. 비공개 데이터를 담은 모든 테이블에 빠짐없이 RLS 정책을 적용하는 것이 유일한 해결책이에요."
---

프로덕션 배포 다음 날, 데이터베이스 전체가 열려 있다는 걸 알게 됐어요. RLS를 켜놨다고 생각했는데, 실제로는 꺼진 상태였거든요. 국내 개발팀에서 Supabase 도입이 빠르게 늘면서 이런 사고가 반복되고 있어요. 특히 `service_role` 키를 클라이언트 코드에 그대로 박아두는 실수가 가장 치명적이에요.

RLS(Row Level Security)는 PostgreSQL의 행 단위 접근 제어 기능이에요. "이 사람은 자기 데이터만 볼 수 있어"를 데이터베이스 레벨에서 강제하는 거죠. Supabase가 이걸 기본으로 제공하는데, 설정을 잘못하면 RLS가 켜져 있어도 아무 의미가 없어요.

이 글에서는 실제로 반복되는 실수 패턴 세 가지와, 서비스 키 노출 사고가 어떻게 일어나는지를 짚어볼게요.

> **핵심 요약**
> - Supabase `service_role` 키는 RLS를 완전히 우회해요. 클라이언트 코드에 포함되는 순간 모든 보안 설정이 무효가 돼요.
> - RLS를 테이블에 활성화했더라도 정책(Policy)을 하나도 만들지 않으면, 기본값은 '모든 접근 거부'가 아닌 '아무 정책 없음'으로 작동해요. 이 차이가 생각보다 미묘해요.
> - `anon` 키는 클라이언트용, `service_role` 키는 서버 전용이에요. 용도가 완전히 달라요.
> - 바이브코딩 트렌드 확산과 함께 Supabase를 처음 쓰는 팀이 늘었고, 이 패턴에서 비롯된 보안 취약점 신고도 덩달아 증가하고 있어요.

---

## RLS, 켜놨다고 끝이 아니에요

Supabase는 새 테이블을 만들 때 RLS가 기본 비활성화 상태예요. Dashboard에서 "Enable RLS" 버튼을 눌러야 켜지는데, 여기서 첫 번째 오해가 생겨요.

많은 팀이 RLS를 켰으니 안전하다고 생각해요. 그런데 RLS를 켜는 것과 정책을 만드는 건 완전히 별개예요. RLS를 활성화만 하고 아무 정책도 안 만들면, 해당 테이블은 모든 접근이 막혀요. `anon` 유저든, 로그인한 유저든 전부 조회 불가가 되는 거죠. 그럼 "앱이 안 된다"는 버그 리포트가 오고, 급하게 `service_role` 키로 우회하는 선택을 하게 돼요. 이게 사고의 시작이에요.

Supabase 공식 문서에 따르면, 정책 없이 RLS를 켜면 `DEFAULT DENY`로 작동해요. 정책은 허용할 행을 명시하는 거지, "금지 목록"을 만드는 게 아니에요. 이 방향이 반대라고 생각하는 팀이 의외로 많아요.

타임라인으로 보면 이렇게 돼요.

1. 테이블 생성 → RLS 비활성화 (기본값)
2. 개발 중 빠른 테스트를 위해 `service_role` 키 사용
3. 배포 전 RLS 활성화 → 정책 미설정으로 앱 전체 오류
4. 빠른 수정을 위해 클라이언트에 `service_role` 키 그대로 놔둠
5. 서비스 키 클라이언트 노출 상태로 프로덕션 배포

이 흐름이 놀랍도록 공통적이에요.

---

## 세 가지 핵심 실수 패턴

### `service_role` 키를 프론트엔드에 넣는 실수

`service_role` 키는 RLS를 완전히 무시해요. Supabase가 의도적으로 설계한 거예요. 서버 사이드 관리 작업(배치 처리, 어드민 기능)을 위해 만든 키거든요.

문제는 이 키가 클라이언트 번들에 들어가면, 브라우저 DevTools → Network 탭 또는 소스 코드에서 바로 꺼낼 수 있어요. 생각보다 훨씬 쉽게요. 환경 변수 이름을 `NEXT_PUBLIC_SUPABASE_SERVICE_KEY`로 해뒀다면, `NEXT_PUBLIC_` 접두사 자체가 "이 값은 클라이언트에 노출됩니다"를 의미해요. Next.js 기준으로요.

서비스 키 클라이언트 노출 사고의 절반 이상이 이 패턴에서 나와요.

### RLS 정책을 너무 넓게 쓰는 실수

정책을 이렇게 만드는 경우가 있어요.

```sql
CREATE POLICY "allow_all" ON messages
FOR ALL USING (true);
```

`USING (true)`는 "모든 행에 대해 허용"이에요. RLS를 켰지만 사실상 끈 것과 같아요. 보통 "일단 되게 만들고 나중에 정책 다듬자"는 의도로 쓰는데, 그 나중이 오지 않는 경우가 많죠.

올바른 패턴은 `auth.uid()`를 기준으로 본인 데이터만 접근하게 제한하는 거예요.

```sql
CREATE POLICY "users_own_data" ON messages
FOR SELECT USING (auth.uid() = user_id);
```

딱 이 차이예요.

### 비교: 키 종류별 RLS 동작 방식

| 항목 | `anon` 키 | `service_role` 키 |
|------|-----------|-------------------|
| RLS 적용 여부 | 적용됨 | 우회함 |
| 클라이언트 사용 | 권장 | 절대 금지 |
| 인증 없는 접근 | 정책에 따라 제한 | 무제한 |
| 용도 | 일반 앱 쿼리 | 서버 어드민, 배치 |
| 노출 시 위험도 | 낮음 (정책 존재 시) | 매우 높음 |

`anon` 키가 노출돼도 RLS 정책이 제대로 설정돼 있으면 피해가 제한적이에요. 하지만 `service_role` 키가 노출되면 RLS 자체가 의미 없어져요. 이 차이를 이해하는 게 첫 단계예요.

### 테이블 관계에서 생기는 RLS 구멍

`orders` 테이블에 RLS를 걸었는데 `products` 테이블에는 안 걸었어요. `orders`를 조회할 때 JOIN을 쓰면, `products` 쪽 데이터가 필터링 없이 딸려와요. 테이블 하나에만 RLS를 걸면 관련 테이블을 통한 우회 접근이 생기는 거예요.

모든 비공개 테이블에 RLS를 걸어야 해요. 하나라도 빠지면 그게 구멍이 돼요.

---

## 사고 후 팀들이 공통으로 취한 조치

**서비스 키가 이미 GitHub에 올라간 경우**
Supabase 대시보드에서 키를 즉시 롤(rotate)해야 해요. `service_role` 키는 Settings → API에서 재발급할 수 있어요. GitHub에 올라간 키는 삭제해도 git history에 남으니까, 키 롤이 먼저예요.

**정책 없이 RLS를 켜놨던 경우**
이미 운영 중인 서비스라면 정책을 하나씩 추가하면서 각 역할별 접근을 검증해야 해요. 한꺼번에 바꾸면 어디서 오류 났는지 추적하기 어려워요. `SELECT`, `INSERT`, `UPDATE`, `DELETE`를 분리해서 정책 만드는 게 나아요.

**앞으로 주시할 신호들**
Supabase가 RLS 정책 테스트 도구를 대시보드에 통합한다고 밝혔어요. 이 기능이 나오면 배포 전 정책 검증이 훨씬 편해질 거예요. Next.js, SvelteKit 등 프레임워크와 Supabase를 같이 쓸 때의 서버 컴포넌트 vs 클라이언트 컴포넌트 키 분리 패턴도 정리가 잘 되어가고 있어요.

---

## 지금 당장 확인할 것들

체크리스트 세 개만 먼저 확인해 보세요.

- **`NEXT_PUBLIC_` 또는 `VITE_` 접두사가 붙은 환경 변수 중 `service_role` 키가 있나요?** → 있으면 즉시 서버 전용으로 옮겨야 해요.
- **RLS를 켠 테이블에 정책이 하나 이상 있나요?** → 없으면 `DEFAULT DENY` 상태예요. 정책을 추가하거나, RLS를 끄고 목적을 다시 정해야 해요.
- **JOIN하는 테이블 전부에 RLS가 걸려 있나요?** → 하나라도 빠져 있으면 그 테이블이 우회 경로가 돼요.

요약하면, Supabase RLS는 켜는 것보다 정책을 올바르게 만드는 게 더 중요해요. 서비스 키는 서버에만. `anon` 키는 클라이언트에. 그리고 JOIN하는 테이블 전부에 정책을 걸어야 해요.

향후 Supabase 대시보드에 정책 시뮬레이터와 보안 감사 기능이 추가될 가능성이 높아요. 그 전까지는 직접 쿼리로 정책을 검증하는 습관이 필요해요.

지금 운영 중인 서비스에 `service_role` 키가 클라이언트 번들에 들어가 있지 않은지, 한 번만 확인해보세요.

## 참고자료

1. [Row Level Security | Supabase Docs](https://supabase.com/docs/guides/database/postgres/row-level-security)
2. [바이브코딩 Supabase 환경설정 API 키 찾는 방법](https://www.mybiznow.kr/%EB%B0%94%EC%9D%B4%EB%B8%8C%EC%BD%94%EB%94%A9-supabase-%ED%99%98%EA%B2%BD%EC%84%A4%EC%A0%95-api-%ED%82%A4-%EC%B0%BE%EB%8A%94-%EB%B0%A9%EB%B2%95/)


---

*Photo by [Caroline Attwood](https://unsplash.com/@_carolineattwood) on [Unsplash](https://unsplash.com/photos/a-black-room-with-a-blue-light-in-it-i3zxRs0ppho)*
