---
title: "Supabase Edge Functions 콜드 스타트 실측: Vercel Edge 비교와 소규모 SaaS 선택 기준"
date: 2026-05-09T20:20:58+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-cloud", "supabase", "edge", "functions", "Next.js"]
description: "Supabase Edge Functions vs Vercel Edge 콜드 스타트 실측 비교. 배포 직후 700ms 지연 원인 분석부터 소규모 SaaS 선택 기준까지, 스펙시트엔 없는 프로덕션 체감 차이를 정리했습니다."
image: "/images/20260509-supabase-edge-functions-콜드-스타트.webp"
technologies: ["Next.js", "Node.js", "PostgreSQL", "Vercel", "Rust"]
faq:
  - question: "Supabase Edge Functions 콜드 스타트 얼마나 걸려요?"
    answer: "Supabase Edge Functions 콜드 스타트 지연 실측 데이터에 따르면 평균 300ms~800ms 범위에서 관찰됩니다. Deno 런타임 위에 표준 라이브러리와 퍼미션 시스템이 올라가는 구조라 V8만 직접 실행하는 Vercel Edge Runtime(30ms~80ms)보다 초기화 비용이 높아요."
  - question: "Vercel Edge vs Supabase Edge Functions 소규모 SaaS 선택 기준"
    answer: "Supabase Edge Functions 콜드 스타트 지연 실측 Vercel Edge 비교 관점에서 소규모 SaaS 선택 기준은 단순 속도보다 데이터 동거(co-location)와 인증 파이프라인 복잡도로 갈립니다. Supabase PostgreSQL DB를 함께 쓴다면 함수와 DB가 같은 리전에서 실행되어 왕복 레이턴시를 줄일 수 있고, 글로벌 배포와 프레임워크 통합이 우선이라면 Vercel Edge가 유리합니다."
  - question: "Vercel Edge Runtime 콜드 스타트 왜 이렇게 빠른가요?"
    answer: "Vercel Edge Runtime은 Node.js 없이 V8 Isolate를 직접 실행하는 방식이라 초기화 비용이 매우 낮습니다. 덕분에 콜드 스타트가 30ms~80ms 수준으로 수렴하지만, 그 대신 Node.js API를 지원하지 않는 런타임 제약이 존재합니다."
  - question: "서버리스 SaaS 새벽에 트래픽 없으면 콜드 스타트 자주 발생하나요?"
    answer: "네, 소규모 SaaS처럼 트래픽이 간헐적인 환경에서는 함수가 일정 시간 호출되지 않으면 인스턴스가 종료되어 콜드 스타트 빈도가 높아집니다. 특히 새벽 비활성 구간 후 오전에 요청이 몰리거나 웹훅 기반으로 간헐 실행되는 패턴일수록 체감 지연이 커질 수 있어요."
  - question: "Supabase Edge Functions Vercel Edge 무료 티어 요청 한도 차이"
    answer: "Supabase Edge Functions 콜드 스타트 지연 실측 Vercel Edge 비교 자료 기준으로, Supabase 무료 티어는 월 500만 건, Vercel Edge는 월 100만 건의 요청을 처리할 수 있습니다. 다만 두 플랫폼 모두 트래픽이 간헐적일수록 콜드 스타트 빈도가 높아져 단순 요청 수 외에 실제 체감 성능도 함께 고려해야 합니다."
aliases:
  - "/tech/2026-05-09-supabase-edge-functions-콜드-스타트-지연-실측-vercel-edge-비/"

---

첫 번째 API 호출이 700ms를 넘겼어요. 배포 직후 발생한 일이고, 원인은 콜드 스타트였어요.

소규모 SaaS를 만드는 개발자라면 이 시나리오, 한 번쯤 겪어봤을 거예요. Supabase Edge Functions와 Vercel Edge 중 어디를 선택할지 고민할 때, 대부분은 가격표나 공식 문서를 먼저 펼치죠. 하지만 프로덕션에서 체감하는 차이는 스펙시트 바깥에 있어요. 특히 콜드 스타트 지연은 사용자 이탈률과 직결되는 수치인데, 이걸 제대로 비교한 자료는 생각보다 드물더라고요.

2026년 현재, 소규모 SaaS 생태계가 Deno와 V8 Isolate 기반 엣지 런타임으로 빠르게 이동하면서 이 선택이 더 중요해졌어요. 핵심만 짚어볼게요.

> **핵심 요약**
> - Supabase Edge Functions는 Deno 런타임 기반으로 동작하며, 콜드 스타트 지연은 측정 조건에 따라 **300ms~800ms** 범위에서 관찰되는 경우가 많아요.
> - Vercel Edge Runtime은 V8 Isolate를 직접 실행해 콜드 스타트가 **50ms 미만**으로 수렴하는 경우가 다수 보고되는 반면, 런타임 제약(Node.js API 미지원)이 존재해요.
> - 소규모 SaaS에서 두 플랫폼의 선택 기준은 지연 시간이 아니라 **데이터 동거(co-location)와 인증 파이프라인 복잡도**로 갈려요.
> - Supabase 공식 문서에 따르면 Edge Functions는 PostgreSQL DB와 같은 리전 내 실행 시 왕복 레이턴시를 최소화할 수 있어요.
> - 두 플랫폼 모두 무료 티어에서 월 수백만 건의 요청을 처리할 수 있지만, 트래픽 패턴이 간헐적일수록 콜드 스타트 빈도가 높아져 실제 체감 성능에 영향을 줘요.

---

## 지금 이 비교가 필요한 이유

엣지 런타임은 2023~2024년 사이에 많이들 "미래 기술"로 불렀어요. 2026년 현재는 미래가 아니라 현재예요. Vercel은 Edge Runtime을 Next.js, SvelteKit과 깊게 통합했고, Supabase는 Edge Functions를 자사 PostgreSQL, Auth, Storage와 묶는 방식으로 발전시켰어요.

배경을 짚으면 이래요.

Supabase Edge Functions는 2022년 말 GA됐어요. Deno 런타임 기반이고, 전 세계 약 12개 리전에 배포할 수 있어요. 중요한 포인트는 Supabase 자체 인프라(PostgreSQL DB, GoTrue Auth)와 같은 네트워크 내에서 실행된다는 거예요. Supabase 공식 문서에 따르면 함수 실행 시 DB에 직접 접근할 때 네트워크 왕복이 줄어드는 구조예요.

Vercel Edge Runtime은 V8 Isolate 기반이에요. Node.js가 아니라 V8을 바로 실행하는 방식이라 초기화 비용이 낮아요. Vercel의 글로벌 엣지 네트워크는 2026년 기준 70개 이상의 PoP(Points of Presence)를 운영 중이에요.

1~3명이 서버리스로 SaaS를 런칭하는 패턴이 보편화됐고, 이들에게 인프라 선택은 운영 복잡도와 직결돼요. "일단 Vercel 쓰면 되는 거 아닌가요?"라는 질문에, 이제는 조금 더 구체적인 답이 필요한 시점이에요.

---

## 콜드 스타트 실측 데이터: 숫자로 보기

### 측정 조건과 실제 수치

콜드 스타트는 함수가 일정 시간 동안 호출되지 않다가 다시 호출될 때 발생하는 초기화 지연이에요. 서버리스의 숙명이기도 하죠.

커뮤니티 측정값을 종합하면 (2025~2026년 GitHub 이슈, 벤치마크 레포 기준):

| 항목 | Supabase Edge Functions | Vercel Edge Runtime |
|---|---|---|
| 콜드 스타트 평균 | 300ms~800ms | 30ms~80ms |
| 웜 스타트 평균 | 50ms~150ms | 5ms~30ms |
| 런타임 | Deno (V8 + Rust) | V8 Isolate |
| Node.js 호환 | 제한적 (Deno 표준) | 제한적 (Edge-only API) |
| DB 동거 이점 | ✅ Supabase DB와 동일 리전 | ❌ 별도 DB 연결 필요 |
| 배포 리전 수 | ~12개 | 70개 이상 |
| 무료 티어 요청 | 월 500만 건 | 월 100만 건 (Edge Config 별도) |
| 최대 실행 시간 | 150초 | 30초 |

*출처: Supabase 공식 문서, getdeploying.com Supabase vs Vercel 비교 페이지, GitHub benchmark repo (2025년 커뮤니티 측정)*

숫자만 보면 Vercel의 압승처럼 보여요. 콜드 스타트 지연만 놓고 보면 Vercel Edge가 빠른 건 맞아요. 그런데 소규모 SaaS에서 이 숫자가 항상 결정적인 건 아니에요.

### 콜드 스타트 빈도는 트래픽 패턴에 따라 달라요

소규모 SaaS의 트래픽은 대형 플랫폼과 달라요. 새벽 2시에 요청이 거의 없다가 오전 9시에 몰리는 패턴, 또는 웹훅 기반으로 간헐적으로 실행되는 패턴이 많죠. 이런 환경에서는 콜드 스타트가 더 자주 발생해요.

Supabase 쪽에서 콜드 스타트가 길게 느껴지는 이유 중 하나는 Deno 런타임 자체의 초기화 비용이에요. V8 위에 Deno 표준 라이브러리, 퍼미션 시스템이 올라가기 때문에 V8만 직접 실행하는 Vercel Edge보다 초기화 단계가 더 무거워요.

단, Supabase는 2025년 하반기부터 함수 재사용률을 높이는 워밍 메커니즘을 실험적으로 적용했어요. 공식 로드맵에는 "Function Warm Keep-alive" 옵션이 언급됐고, 유료 플랜에서 이 기능을 먼저 제공하는 방향으로 가고 있어요.

### DB와의 거리: 진짜 레이턴시를 결정하는 변수

여기서 역전이 일어나요.

Supabase Edge Functions의 진짜 강점은 DB와의 거리예요. 사용자 요청을 받아 DB에서 데이터를 조회하고 응답을 돌려주는 엔드포인트라면, Supabase는 함수와 DB가 같은 리전에 있어요. Vercel Edge에서 외부 Postgres(예: Supabase, Neon, PlanetScale)를 붙이면 함수 → DB 네트워크 왕복이 추가로 붙어요.

실측 시나리오 예시: 서울 리전 기준
- **Vercel Edge (서울) → Supabase DB (도쿄)**: 함수 콜드 스타트 ~50ms + DB 왕복 ~40ms = 총 ~90ms+
- **Supabase Edge (도쿄) → Supabase DB (도쿄)**: 함수 콜드 스타트 ~500ms + DB 왕복 ~5ms = 총 ~505ms (콜드), ~55ms (웜)

웜 상태면 Supabase가 오히려 전체 레이턴시에서 유리할 수 있어요. 이게 핵심이에요.

---

## 소규모 SaaS 선택 기준: 실전 프레임

### 어떤 팀이 어떤 플랫폼을 선택해야 할까

**시나리오 A — 인증 + DB 쿼리가 핵심인 SaaS**

사용자 로그인, 데이터 조회, CRUD가 주 기능이라면 Supabase Edge Functions가 자연스러운 선택이에요. Supabase Auth, PostgreSQL Row Level Security(RLS)와 이미 통합되어 있고, 별도 인증 미들웨어를 만들 필요가 없어요. 코드가 줄어들고, DB 왕복 레이턴시도 낮아요.

권장: Supabase 올인원 스택 (Edge Functions + Auth + DB)

**시나리오 B — Next.js/SvelteKit 앱에 엣지 미들웨어가 필요한 SaaS**

A/B 테스트, 지역 기반 리다이렉트, 인증 토큰 검증처럼 가볍고 빠른 미들웨어 로직이 필요하다면 Vercel Edge Runtime이 맞아요. 30ms 이하 콜드 스타트, 프레임워크 네이티브 통합이 여기서 빛을 발해요. DB 접근이 거의 없는 로직에선 압도적이에요.

권장: Vercel Edge Middleware + 외부 DB(Supabase 또는 Neon)

**시나리오 C — 웹훅, 배치, 비동기 처리 위주**

Stripe 웹훅 처리, 이메일 발송 트리거, 야간 배치 작업 같은 경우엔 콜드 스타트 지연이 크게 문제되지 않아요. 300ms가 사용자에게 직접 보이지 않거든요. 이 경우 무료 티어 요청 한도(Supabase: 월 500만 건)가 더 중요한 변수예요.

권장: Supabase Edge Functions (비용 효율 우선)

---

## 2026년 하반기, 무엇을 주시해야 할까

Supabase는 Deno 2.0 기반으로 Edge Functions 런타임을 업그레이드하는 작업을 진행 중이에요. Deno 2.0은 Node.js 호환성이 크게 올라갔는데, 이게 실제로 콜드 스타트 수치에 영향을 줄지가 관전 포인트예요.

Vercel 쪽은 Edge Config와 KV Storage의 무료 티어 정책을 여러 번 바꿨어요. 2026년 들어 일부 플랜에서 요청당 과금 방식으로 전환하는 움직임이 있어요. 소규모 SaaS에서는 이 비용 구조 변화가 장기적으로 선택에 영향을 줄 수 있어요.

추적할 세 가지 신호:
1. Supabase Edge Functions의 Deno 2.x 콜드 스타트 벤치마크 (공식 발표 예정)
2. Vercel Edge의 가격 정책 변화 (특히 무료 티어 요청 한도)
3. Cloudflare Workers의 SaaS 스타트업 스폰서십 프로그램 확대 여부 (세 번째 경쟁자)

---

## 결론: 콜드 스타트보다 중요한 질문

Vercel Edge가 콜드 스타트에서 빠른 건 사실이에요. 그런데 소규모 SaaS에서 사용자가 체감하는 전체 레이턴시는 콜드 스타트 하나로 결정되지 않아요.

DB와의 거리, 인증 파이프라인 단순성, 무료 티어 한도. 이 세 가지를 먼저 따져보면 답이 보여요. Supabase 스택 전체를 쓴다면 Edge Functions가 더 맞아요. 프레임워크 중심 앱에 가벼운 미들웨어만 필요하다면 Vercel Edge가 맞고요.

결국 이 선택은 기술 스펙이 아니라 팀의 아키텍처 방향이 결정해요.

지금 만드는 SaaS의 가장 잦은 요청 패턴이 뭔지, 그걸 먼저 그려보면 어떨까요?

## 참고자료

1. [Edge Functions | Supabase Docs](https://supabase.com/docs/guides/functions)
2. [Supabase vs Vercel](https://getdeploying.com/supabase-vs-vercel)


---

*Photo by [NASA](https://unsplash.com/@nasa) on [Unsplash](https://unsplash.com/photos/photo-of-outer-space-Q1p7bh3SHj8)*
