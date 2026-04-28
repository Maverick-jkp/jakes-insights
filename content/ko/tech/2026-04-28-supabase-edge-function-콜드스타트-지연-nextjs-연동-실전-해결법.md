---
title: "Supabase Edge Function 콜드스타트 지연, Next.js 연동 실전 해결법"
date: 2026-04-28T21:05:16+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-web", "supabase", "edge", "function", "TypeScript"]
description: "Supabase Edge Function 콜드스타트로 Next.js 첫 요청이 2~4초 지연된다면, Route Handler와 Server Actions 연동 방식만 바꿔도 체감 지연을 3배까지 줄일 수 있습니다. 800ms~2.5초 콜드스타트 원인과"
image: "/images/20260428-supabase-edge-function-콜드스타트-지.webp"
technologies: ["TypeScript", "Next.js", "Node.js", "PostgreSQL", "Vercel"]
faq:
  - question: "Supabase Edge Function 콜드스타트 왜 이렇게 오래 걸리나요"
    answer: "Supabase Edge Function은 Deno Deploy 기반으로 실행되며, 일정 시간 요청이 없으면 컨테이너가 종료되고 다음 요청 시 다시 부팅하는 구조 때문에 콜드스타트가 발생해요. 평균 800ms~2.5초 수준의 지연이 발생하며, 함수 번들 크기와 import하는 패키지 무게에 따라 지연이 더 크게 벌어질 수 있어요. 불필요한 패키지 제거와 단일 책임 원칙을 적용하면 콜드스타트 시간을 줄이는 데 효과적이에요."
  - question: "Supabase Edge Function 콜드스타트 지연 Next.js 연동 실전 해결법 어떤 게 있나요"
    answer: "Supabase Edge Function 콜드스타트 지연 Next.js 연동 실전 해결법으로는 크게 두 가지가 실무에서 많이 쓰여요. 첫째는 Cron 기반으로 5~10분마다 Edge Function에 핑을 보내는 워밍 전략이고, 둘째는 Next.js Route Handler에서 응답을 캐시하고 짧은 revalidate 주기로 백그라운드 워밍 효과를 내는 방식이에요. 2026년 현재 Supabase의 keepalive 워밍 전략과 Vercel Edge Middleware 조합이 프로덕션 수준 해결책으로 가장 많이 채택되고 있어요."
  - question: "Next.js Server Actions에서 Supabase Edge Function 호출하는 게 제일 빠른가요"
    answer: "호출 위치별로 체감 지연이 다른데, Server Actions에서 functions.invoke()를 사용하는 방식이 인증 토큰 전달과 콜드스타트 제어 면에서 가장 유연하게 다룰 수 있어요. 다만 절대적인 속도 기준으로는 Vercel Edge Middleware에서 fetch로 직접 호출하는 방식이 실행 환경 제약이 있지만 가장 낮은 지연을 보여줘요. 클라이언트 컴포넌트에서 직접 호출하는 방식은 사용자가 콜드스타트 지연을 그대로 체감하기 때문에 프로덕션에서는 피하는 것이 좋아요."
  - question: "Supabase Edge Function 콜드스타트 지연 Next.js 연동 실전 해결법 중 Route Handler 캐싱은 어떻게 작동하나요"
    answer: "Next.js Route Handler에서 Edge Function 응답에 revalidate와 cache: 'force-cache' 옵션을 적용하면 사용자는 항상 캐시된 응답을 받고, 백그라운드에서만 실제 Edge Function이 호출되는 구조가 만들어져요. 이렇게 하면 사용자 입장에서는 콜드스타트 지연이 보이지 않고, 캐시 갱신 시점에 자동으로 워밍 효과까지 생겨서 일석이조예요. revalidate 주기를 너무 길게 잡으면 데이터 신선도가 떨어지므로 서비스 특성에 맞게 조정이 필요해요."
  - question: "Supabase Edge Function에서 npm 패키지 import 할 때 주의할 점"
    answer: "Supabase Edge Function은 Deno 환경에서 실행되므로 npm: prefix로 무거운 패키지를 불러오면 콜드스타트 시 모듈 전체를 로드해야 해서 지연이 커져요. 특히 Edge Function 내부에서 @supabase/supabase-js 전체를 다시 import하는 건 이미 Supabase 서버 환경 안에서 실행되기 때문에 불필요한 무게를 더하는 행위예요. 필요한 모듈만 선택적으로 import하고, 외부 패키지 대신 Deno 표준 라이브러리를 우선 사용하는 것이 콜드스타트 최적화의 기본 원칙이에요."
---

Next.js 앱에 Supabase Edge Function을 붙였는데, 첫 요청이 **2~4초씩 걸린다**는 이슈를 겪고 있다면 아직 해결 가능한 부분이 많이 남아 있어요.

> **핵심 요약**
> - Supabase Edge Function의 콜드스타트는 평균 800ms~2.5초 수준이며, 트래픽이 없는 시간대 직후 첫 요청에서 집중 발생해요.
> - Next.js의 `Route Handler`와 `Server Actions` 중 Edge Function을 연동하는 방식에 따라 체감 지연 차이가 세 배까지 벌어질 수 있어요.
> - Deno 기반의 Edge Runtime은 Node.js 기반 Serverless Function보다 콜드스타트가 빠르지만, 특정 npm 패키지 호환성 제약이 여전히 존재해요.
> - 2026년 현재 Supabase가 제공하는 `keepalive` 방식의 워밍 전략과 Vercel Edge Middleware 조합이 프로덕션 수준의 해결책으로 가장 많이 쓰이고 있어요.

---

## Edge Function 콜드스타트, 왜 지금 문제인가

Next.js는 App Router를 중심으로 서버 컴포넌트와 Server Actions가 기본 패턴으로 자리잡았어요. 여기에 Supabase를 백엔드로 붙이는 구성이 스타트업과 인디 개발자 사이에서 빠르게 늘고 있고요. Reddit의 r/nextjs 스레드에서 2025년 말부터 Supabase Edge Function 관련 질문이 눈에 띄게 늘었는데, 대부분 같은 문제를 이야기해요. "첫 요청이 유독 느려요."

이건 단순한 느낌이 아니에요. Deno Deploy 기반의 Supabase Edge Function은 일정 시간 요청이 없으면 컨테이너가 종료되고, 다음 요청 때 다시 부팅하는 구조예요. 이게 콜드스타트(Cold Start)죠. Deno 자체가 Node.js보다 기동 속도가 빠른 건 맞지만, 함수 코드 크기, import 경로, 의존성 로드 방식에 따라 지연이 생각보다 크게 벌어져요.

Supabase 공식 문서 기준으로 Edge Function은 `supabase/functions/{function-name}/index.ts` 구조로 배포되고, Next.js 앱에서는 `fetch`를 통해 직접 호출하거나 Supabase 클라이언트의 `functions.invoke()` 메서드를 쓰는 두 가지 방법이 있어요. 어떤 방식을 쓰느냐가 콜드스타트 대응 전략에 직접 영향을 미쳐요.

그런데 지금 이 문제가 더 부각되는 이유가 있어요. Next.js의 Server Actions와 Supabase Edge Function을 동시에 쓰는 구성이 늘면서, 둘 다 서버 사이드에서 실행되는 레이어가 겹치게 됐거든요. 불필요한 레이어를 줄이느냐, 아니면 캐싱과 워밍 전략으로 커버하느냐. 선택이 필요한 시점이에요.

---

## 콜드스타트 지연, 정확히 어디서 발생하나

### 함수 번들 크기와 import 구조

콜드스타트의 핵심 변수는 **함수 번들 크기**예요. Supabase Edge Function은 Deno로 실행되기 때문에, Node.js 방식의 `require()` 대신 URL import나 npm specifier를 써요. 여기서 많은 개발자가 함정에 빠지는데, `npm:` prefix로 무거운 패키지를 그냥 불러오면 콜드스타트 때 해당 모듈 전체를 로드해야 해요.

예를 들어 `npm:zod` 같은 가벼운 라이브러리는 큰 문제가 없지만, `npm:@supabase/supabase-js` 전체를 Edge Function 내에서 다시 import하는 건 의미 없는 무게를 더하는 거예요. Edge Function은 이미 Supabase 서버 환경 안에서 실행되기 때문에, `createClient`를 다시 부를 필요가 없거든요.

간단한 원칙은 이거예요.

- 필요한 것만 import, `* as` 금지
- 외부 패키지 대신 Deno 표준 라이브러리 우선
- 함수 하나당 단일 책임, 불필요한 의존성 제거

### Next.js 연동 방식에 따른 지연 차이

어디서 호출하느냐가 중요해요.

| 호출 위치 | 방식 | 콜드스타트 체감 | 주의사항 |
|-----------|------|----------------|----------|
| Client Component | `fetch()` 직접 호출 | 그대로 노출 | 클라이언트에서 직접 요청 |
| Route Handler | `fetch()` 서버 측 호출 | 부분 완화 가능 | 서버 캐싱 적용 가능 |
| Server Actions | `functions.invoke()` | 가장 제어 용이 | 인증 토큰 전달 주의 |
| Middleware (Edge) | `fetch()` at edge | 최소 지연 | 실행 환경 제약 있음 |

클라이언트 컴포넌트에서 직접 호출하면 사용자가 콜드스타트를 그대로 기다려야 해요. 반면 Route Handler에서 호출하면 Next.js 서버 측 캐싱(`revalidate`, `cache: 'force-cache'`)을 씌울 수 있고, 워밍 전략과도 자연스럽게 연결돼요.

### 워밍(Warming) 전략의 실제 효과

콜드스타트를 근본적으로 없애는 건 어렵지만, 발생 빈도를 크게 줄일 수 있어요. 프로덕션에서 가장 많이 쓰이는 방법은 두 가지예요.

**방법 1: Cron 기반 주기적 핑**
Supabase의 `pg_cron` 확장이나 외부 스케줄러(예: GitHub Actions 무료 플랜)로 5~10분마다 Edge Function에 빈 요청을 보내는 방식이에요. 단점은 비용이 조금씩 쌓이고, Supabase Free Tier에서는 실행 횟수 한도가 있어요.

**방법 2: Next.js Route Handler + `revalidate` 조합**
Route Handler에서 Edge Function 응답을 캐시해두고, `revalidate` 주기를 짧게 설정하면 캐시 갱신 시점에 자동으로 워밍 효과가 생겨요. 사용자는 항상 캐시된 응답을 받고, 백그라운드에서만 실제 함수가 호출되는 구조죠.

```typescript
// app/api/my-edge/route.ts
export const revalidate = 300; // 5분마다 갱신

export async function GET() {
  const res = await fetch(`${process.env.SUPABASE_FUNCTIONS_URL}/my-function`, {
    headers: { Authorization: `Bearer ${process.env.SUPABASE_ANON_KEY}` },
  });
  const data = await res.json();
  return Response.json(data);
}
```

코드 변경 없이 캐싱 레이어만으로 체감 성능이 크게 달라져요. 그래서 이 패턴이 실전 해결책으로 자주 언급되는 거고요.

---

## 상황별 해결 시나리오

**인증이 필요한 API 요청이라면?**
`Server Actions` 안에서 `supabase.functions.invoke()`를 써요. 세션 토큰이 서버 측에서 자동으로 붙고, 클라이언트에 토큰이 노출될 위험도 없어요. 단, Server Action 자체도 서버 측 실행이라 두 레이어의 지연이 합산될 수 있으니, 응답 크기를 최소화하는 게 좋아요.

**실시간 데이터가 필요하다면?**
Edge Function 대신 Supabase의 Realtime 채널이나 PostgreSQL 함수(`rpc`)를 직접 쓰는 걸 고려해봐요. 콜드스타트 지연 자체를 피할 수 있거든요. Edge Function이 꼭 필요한 로직(외부 API 연동, 무거운 데이터 가공)이 아니라면 굳이 Edge Function을 거칠 이유가 없어요.

**무거운 연산이 반드시 필요하다면?**
Supabase Background Tasks(현재 베타)나 Vercel의 `waitUntil`로 비동기 처리를 분리하는 방법이 있어요. 핵심은 사용자 응답 경로에서 무거운 작업을 빼내는 거예요.

---

## 2026년 하반기, 무엇을 지켜봐야 하나

Supabase는 2026년 초 Edge Function의 지역(region) 선택 옵션을 확대했어요. 한국 리전이 정식 지원되면서 물리적 레이턴시 자체가 줄었고, 콜드스타트의 절대적인 영향이 전보다 작아졌어요. 다음 분기에는 함수 실행 유지(Warm Instance) 옵션이 Pro 플랜 이상에서 정식 출시될 가능성이 높아요. Supabase GitHub 공개 로드맵에 해당 이슈가 올라와 있고, 커뮤니티 투표 수도 꽤 많이 쌓여 있거든요.

정리하면, 콜드스타트 대응의 핵심은 세 가지예요.

- **함수 번들 경량화**: 불필요한 import 제거
- **호출 레이어 선택**: 클라이언트 직접 호출 대신 Route Handler나 Server Actions 경유
- **캐싱·워밍 전략**: 응답 경로에서 콜드스타트 노출 최소화

지금 당장 프로덕션에 적용한다면, Route Handler + `revalidate` 조합부터 시작하는 게 변경 비용 대비 효과가 가장 빠른 선택이에요.

그리고 한 발짝 물러서서 생각해볼 필요도 있어요. 모든 API 로직을 Edge Function으로 옮기는 게 목표가 아니라, **꼭 거기서 실행해야 하는 로직만** 남기는 게 더 나은 설계일 수 있거든요. 그 판단 기준을 잡는 게 2026년 Next.js 아키텍처의 진짜 숙제예요.

## 참고자료

1. [Background Jobs and Async Task Patterns with Next.js and Supabase | Developer Guides | Iloveblogs.bl](https://www.iloveblogs.blog/guides/nextjs-supabase-background-jobs-async-patterns)
2. [r/nextjs on Reddit: Supabase edge functions usage](https://www.reddit.com/r/nextjs/comments/1nnakdc/supabase_edge_functions_usage/)
3. [Use Supabase with Next.js | Supabase Docs](https://supabase.com/docs/guides/getting-started/quickstarts/nextjs)


---

*Photo by [NASA](https://unsplash.com/@nasa) on [Unsplash](https://unsplash.com/photos/photo-of-outer-space-Q1p7bh3SHj8)*
