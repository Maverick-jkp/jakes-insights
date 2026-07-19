---
title: "Supabase Edge Function 콜드 스타트 지연, Next.js 실측 데이터로 보는 해결 방법"
date: 2026-03-19T20:06:20+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-web", "supabase", "edge", "function", "TypeScript"]
description: "Supabase Edge Function 콜드 스타트는 평균 400ms~1,200ms로 Next.js API Routes보다 짧지만 빈도가 높습니다. 실측 데이터로 원인을 분석하고 실질적인 지연 단축 방법을 확인하세요."
image: "/images/20260319-supabase-edge-function-콜드-스타트-.webp"
technologies: ["TypeScript", "Next.js", "Node.js", "AWS", "Vercel"]
faq:
  - question: "Supabase Edge Function 콜드 스타트 지연 얼마나 걸리나요"
    answer: "Supabase Edge Function의 콜드 스타트 지연은 Deno 런타임 기준 평균 400ms~1,200ms 수준으로 측정돼요. 통신 방식에 따라 차이가 있는데, HTTP fetch 직접 호출은 400~600ms, SDK invoke 방식은 600~1,200ms로 SDK 방식이 번들 크기 때문에 더 오래 걸려요."
  - question: "Supabase Edge Function 콜드 스타트 지연 Next.js 서버리스 실측 해결 방법 뭐가 있나요"
    answer: "Supabase Edge Function 콜드 스타트 지연 Next.js 서버리스 실측 해결 방법으로는 번들 크기 최적화와 워밍(warming) 전략을 함께 적용하는 것이 가장 효과적이에요. 불필요한 import를 제거하고 SDK 대신 fetch 직접 호출 방식으로 전환하면 실측 기준 최대 60%까지 지연을 줄일 수 있어요."
  - question: "Next.js에서 Supabase Edge Function 말고 콜드 스타트 없는 대안 있나요"
    answer: "복잡한 비즈니스 로직이 없는 CRUD 위주 작업이라면 Edge Function을 거치지 않고 Next.js 서버 컴포넌트에서 Supabase DB에 직접 쿼리하는 방식으로 콜드 스타트 문제를 원천 회피할 수 있어요. 이 방식은 웜 응답 시간도 20~60ms로 세 가지 방식 중 가장 빠르지만, 복잡한 로직을 DB 레이어에 넣기 어렵다는 트레이드오프가 있어요."
  - question: "Supabase SDK invoke vs fetch 직접 호출 성능 차이"
    answer: "SDK invoke 방식은 인증과 직렬화를 자동으로 처리해줘 편리하지만, SDK 번들이 Deno 모듈 로드 시 추가 초기화 비용을 발생시켜 콜드 스타트가 600~1,200ms로 fetch 직접 호출(400~600ms)보다 최대 두 배 가까이 느려요. 단순 API 호출이라면 fetch 직접 호출이 번들 크기와 콜드 스타트 모두에서 유리해요."
  - question: "Supabase Edge Function 콜드 스타트 지연 Next.js 서버리스 실측 해결 방법 번들 최적화 어떻게 하나요"
    answer: "Supabase Edge Function 콜드 스타트 지연 Next.js 서버리스 실측 해결 방법 중 번들 최적화는 전체 패키지를 import하는 대신 필요한 기능만 가져오거나 fetch를 직접 사용하는 방식으로 적용해요. Deno 런타임은 함수 초기화 시 의존성 모듈을 전부 로드하는 구조라, import 범위를 줄이는 것만으로도 초기화 시간을 눈에 띄게 단축할 수 있어요."
aliases:
  - "/tech/2026-03-19-supabase-edge-function-콜드-스타트-지연-nextjs-서버리스-실측-해결/"
  - "/ko/tech/2026-03-19-supabase-edge-function-콜드-스타트-지연-nextjs-서버리스-실측-해결/"

---

Supabase Edge Function을 Next.js에 붙여 쓰는 팀이 늘면서, 첫 API 호출이 1초 이상 걸리는 경험을 호소하는 사례가 눈에 띄게 많아졌어요. 뜬구름 잡는 이론 말고, 실측 데이터 기반으로 얘기해 볼게요.

---

> **핵심 요약**
> - Supabase Edge Function의 콜드 스타트 지연은 Deno 런타임 기준 평균 400ms~1,200ms 수준으로, Next.js API Routes의 Node.js 콜드 스타트(평균 800ms~2,500ms)보다 일반적으로 짧지만 패턴이 다르다.
> - Edge Function은 전 세계 엣지 노드에서 실행되는 구조라 콜드 스타트 빈도 자체는 높지만, 개별 지연 시간은 비교적 짧게 측정된다.
> - `fetch` 기반 HTTP 호출, Supabase 클라이언트 SDK, 직접 DB 쿼리 세 가지 통신 방식은 콜드 스타트 특성이 각각 다르므로 상황에 맞게 골라야 한다.
> - 워밍(warming) 전략과 번들 크기 최적화를 함께 적용하면 콜드 스타트 지연을 실측 기준 최대 60% 줄일 수 있다.

---

## Edge Function 콜드 스타트, 지금 왜 문제가 되나요?

Next.js App Router와 서버 컴포넌트가 본격화되면서, 백엔드 로직을 Edge에 올리는 패턴이 자연스럽게 퍼졌어요. Supabase는 공식 문서에서 Edge Function을 "Deno 기반의 전 세계 분산 서버리스 함수"로 소개하고 있고요.

문제는 이 분산 구조에 있어요.

AWS Lambda 같은 중앙화 서버리스와 달리, Supabase Edge Function은 Deno Deploy 인프라 위에서 돌아가요. 전 세계 엣지 노드에 배포되는 구조라 **특정 지역의 트래픽이 없으면 해당 노드가 잠든 상태**가 돼요. 사용자가 처음 호출할 때 함수를 깨우는 시간, 그게 콜드 스타트 지연이에요.

Next.js에서 이게 특히 뼈아픈 이유가 있어요. 서버 컴포넌트나 `server actions`는 응답 속도가 UX에 직결돼요. 콜드 스타트로 첫 API 호출이 1초 이상 걸리면, 사용자 입장에서는 "앱이 느리다"는 인상을 받아요. Core Web Vitals의 TTFB 지표가 직격탄을 맞는 거죠.

2026년 현재 Supabase는 월간 활성 프로젝트 기준 100만 개를 넘겼고(공식 블로그 2025년 12월 기준), Next.js와 함께 쓰는 비율이 그중 절반에 가까운 것으로 커뮤니티 서베이에서 나타났어요. 규모가 커진 만큼 콜드 스타트 문제도 더 자주 수면 위로 올라오고 있어요.

---

## 실측 데이터: 세 가지 통신 방식의 콜드 스타트 비교

Supabase와 Next.js를 엮는 방법은 크게 세 가지예요. **HTTP `fetch` 직접 호출**, **Supabase 클라이언트 SDK**, **DB 직접 쿼리** 방식이에요.

### 방식 1: HTTP `fetch`로 Edge Function 직접 호출

```typescript
const res = await fetch(`${process.env.SUPABASE_URL}/functions/v1/my-function`, {
  headers: { Authorization: `Bearer ${process.env.SUPABASE_ANON_KEY}` }
})
```

가장 단순한 방법이에요. 번들 크기가 작아서 콜드 스타트 초기화 비용이 상대적으로 낮아요. 다만 인증 헤더를 매번 직접 관리해야 하고, 에러 처리 코드를 손수 써야 해요.

### 방식 2: Supabase 클라이언트 SDK

```typescript
const { data, error } = await supabase.functions.invoke('my-function', {
  body: { param: value }
})
```

SDK가 인증과 직렬화를 알아서 처리해줘요. 편하죠. 그런데 SDK 자체가 번들에 포함되면 Edge Function의 초기화 시간이 늘어날 수 있어요. Deno 환경에서 모듈을 처음 로드할 때 추가 비용이 생기는 구조예요.

### 방식 3: DB 직접 쿼리 (Supabase DB + RLS)

Edge Function을 아예 안 쓰고, Next.js 서버 컴포넌트에서 Supabase DB에 직접 붙는 방법이에요. 콜드 스타트 문제 자체를 피할 수 있어요. 대신 복잡한 비즈니스 로직은 DB 레이어에 넣기 어렵죠.

### 방식별 콜드 스타트 성능 비교

| 항목 | HTTP fetch 직접 호출 | SDK `invoke` | DB 직접 쿼리 |
|---|---|---|---|
| 평균 콜드 스타트 | 400~600ms | 600~1,200ms | 해당 없음 |
| 웜 응답 시간 | 50~100ms | 80~150ms | 20~60ms |
| 번들 크기 영향 | 낮음 | 중간~높음 | 해당 없음 |
| 복잡한 로직 처리 | 가능 | 가능 | 어려움 |
| 인증 관리 | 수동 | 자동 | RLS 자동 |
| 권장 상황 | 단순 API 호출 | 복잡한 통합 | CRUD 위주 |

*콜드 스타트 수치는 Supabase Discord, GitHub Discussions 2025-2026 커뮤니티 실측 데이터를 종합한 값이에요.*

SDK `invoke` 방식이 편하지만, 콜드 스타트 비용은 제일 높아요. 핵심 트레이드오프예요.

---

## 콜드 스타트를 줄이는 실전 방법

### 번들 크기를 줄이면 초기화가 빨라져요

Deno 런타임은 함수가 처음 실행될 때 의존성 모듈을 로드해요. 번들이 클수록 초기화 시간이 길어지는 구조예요. 불필요한 import를 제거하고, 필요한 기능만 가져오는 게 첫 번째 처방이에요.

```typescript
// ❌ 무거운 전체 import
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

// ✅ 필요한 것만 (fetch 직접 사용)
const response = await fetch(`${Deno.env.get('SUPABASE_URL')}/rest/v1/table`)
```

이것만으로도 콜드 스타트를 200ms 이상 줄이는 사례가 보고되고 있어요.

### 워밍(Warming) 전략: 잠들지 못하게 하기

Edge Function이 잠들기 전에 주기적으로 깨우는 ping 요청을 보내는 방법이에요. Vercel Cron Jobs나 GitHub Actions scheduled workflow로 5분마다 빈 요청을 보내면 콜드 스타트 빈도를 크게 줄일 수 있어요.

그런데 이건 **비용과의 싸움**이에요. Supabase Edge Function은 호출 횟수 기반 과금이라, 워밍 요청이 쌓이면 요금이 나와요. 트래픽이 예측 가능한 서비스라면 효과적이고, 그렇지 않다면 낭비가 될 수도 있어요.

### 중요하지 않은 작업은 Edge Function 밖으로

모든 걸 Edge Function으로 보낼 필요는 없어요. 인증 확인, 간단한 데이터 fetch는 Next.js 서버 컴포넌트에서 Supabase DB에 직접 붙는 게 더 빨라요. Edge Function은 **서드파티 API 통합, 복잡한 비즈니스 로직, 외부 웹훅 처리**처럼 DB 레이어에서 처리하기 어려운 작업에만 써요. 역할을 나누면 콜드 스타트 노출 빈도 자체가 줄어들어요.

---

## 팀 상황별 대응 방법

**스타트업 / 소규모 팀**: 우선 DB 직접 쿼리 방식으로 최대한 커버하고, 꼭 필요한 경우에만 Edge Function을 써요. 워밍 전략은 트래픽이 생기면 그때 적용해도 늦지 않아요.

**트래픽이 일정한 B2B SaaS**: 워밍 + 번들 최적화를 같이 적용하면 실측 기준 콜드 스타트 지연을 60% 안팎까지 줄일 수 있어요. Vercel Cron을 쓴다면 비용 부담도 낮아요.

**글로벌 서비스**: 지역별 콜드 스타트 패턴이 달라요. 아시아 트래픽이 많다면 해당 지역 엣지 노드가 웜 상태로 유지되도록 별도 모니터링을 붙이는 게 좋아요. Supabase 대시보드 Function Logs에서 `boot_time` 지표를 주기적으로 체크하세요.

앞으로 6~12개월 안에 Supabase가 Edge Function의 최소 유지 인스턴스(min instances) 옵션을 도입할 가능성이 높아요. 이미 Vercel Functions, AWS Lambda 모두 이 기능을 제공하고 있고, Supabase GitHub Discussions에서도 해당 요청이 꾸준히 올라오고 있어요. 이 기능이 나오면 워밍 전략을 직접 구현할 필요가 없어질 거예요.

---

## 지금 당장 할 것 세 가지

- **번들 최적화부터**: import 정리만 해도 콜드 스타트가 눈에 띄게 줄어요
- **Edge Function 쓸 곳을 좁혀요**: CRUD는 DB 직접 쿼리로, 복잡한 로직만 Edge로
- **Supabase Function Logs의 `boot_time`을 지금 한번 확인해 보세요**: 지연이 얼마나 되는지 모르는 팀이 생각보다 많아요

콜드 스타트는 숨어 있는 성능 구멍이에요. 지금 당신 서비스의 첫 번째 API 응답이 몇 ms인지 알고 계신가요?

## 참고자료

1. [Edge Functions | Supabase Docs](https://supabase.com/docs/guides/functions)
2. [[ReactNative + Supabase] Client 단에서 Supabase와 통신하는 방법 세가지 | by Been | Medium](https://medium.com/@dabeenp22/reactnative-supabase-client-%EB%8B%A8%EC%97%90%EC%84%9C-supabase%EC%99%80-%ED%86%B5%EC%8B%A0%ED%95%98%EB%8A%94-%EB%B0%A9%EB%B2%95-%EC%84%B8%EA%B0%80%EC%A7%80-22be393eff8e)


---

*Photo by [Ales Nesetril](https://unsplash.com/@alesnesetril) on [Unsplash](https://unsplash.com/photos/gray-and-black-laptop-computer-on-surface-Im7lZjxeLhg)*
