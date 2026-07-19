---
title: "Supabase Edge Function 콜드 스타트 줄이는 법: Next.js 14 실전 적용 후기"
date: 2026-05-20T21:33:53+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-web", "supabase", "edge", "function", "TypeScript"]
description: "Supabase Edge Functions 콜드 스타트로 첫 요청 300~800ms 지연을 겪고 있다면? Next.js 14 실전 적용을 통해 번들 크기 최적화와 유휴 시간 단축으로 응답 속도를 개선한 방법을 데이터와 함께"
image: "/images/20260520-supabase-edge-function-콜드-스타트-.webp"
technologies: ["TypeScript", "Next.js", "Node.js", "Vercel", "GitHub Actions"]
faq:
  - question: "Supabase Edge Function 콜드 스타트 왜 생기나요"
    answer: "Supabase Edge Functions는 요청이 없으면 컨테이너가 꺼지고, 새 요청이 들어올 때 런타임 기동과 코드 초기화 과정을 거쳐야 해서 콜드 스타트가 발생해요. Deno 기반 V8 Isolate 환경에서는 모듈 파싱과 초기화 시간이 전체 지연의 60~70%를 차지하며, 평균 초기 응답 지연은 400~700ms 수준이에요."
  - question: "Supabase Edge Function 콜드 스타트 줄이는 법 Next.js 14 실전 적용 후기에서 가장 효과적인 방법은"
    answer: "번들 크기를 50KB 이하로 줄이는 게 비용 부담 없이 적용할 수 있는 가장 효과적인 기본 방법이에요. 실제 사례에서 200KB 번들을 45KB로 줄였을 때 콜드 스타트가 680ms에서 390ms로 약 절반 수준으로 감소한 결과가 확인됐어요."
  - question: "Next.js 14에서 Supabase Edge Function 없이 엣지 환경 구성하는 방법"
    answer: "Next.js 14 Route Handler에 `export const runtime = 'edge'`를 선언하면 Vercel Edge Network에서 직접 함수가 실행돼요. Supabase Edge Function을 별도로 두지 않아도 유사한 엣지 실행 환경을 구성할 수 있고, Vercel 인프라와의 통합이 긴밀해 워밍업 지속 시간도 더 긴 편이에요."
  - question: "서버리스 함수 콜드 스타트 워밍업 핑 스케줄러 설정 방법"
    answer: "Vercel Cron Jobs나 GitHub Actions scheduled workflow로 5분마다 헬스체크 엔드포인트를 호출하는 패턴이 일반적으로 쓰여요. Next.js 14 프로젝트라면 `vercel.json`에 crons 설정을 추가해 주기적으로 함수를 깨워두면 콜드 스타트를 사실상 없앨 수 있지만, Vercel Cron은 Pro 플랜 이상에서만 지원돼요."
  - question: "Supabase Edge Function 콜드 스타트 줄이는 법 Next.js 14 실전 적용 후기 번들 크기 최적화 방법"
    answer: "`@supabase/supabase-js` 전체를 import하면 트리셰이킹 없이 200KB를 초과할 수 있어서, 필요한 모듈 경로만 명시적으로 import하는 방식으로 번들을 줄여야 해요. `esm.sh`에서 번들 사이즈를 사전에 확인할 수 있고, Supabase 공식 문서도 50KB 이하를 권장하며 이를 지키면 콜드 스타트를 최대 40~50% 단축할 수 있어요."
aliases:
  - "/tech/2026-05-20-supabase-edge-function-콜드-스타트-줄이는-법-nextjs-14-실전-적/"
  - "/ko/tech/2026-05-20-supabase-edge-function-콜드-스타트-줄이는-법-nextjs-14-실전-적/"

---

API 응답이 첫 요청에서만 유독 느린 경험, 분명 있었을 거예요. 원인은 대부분 하나예요. 콜드 스타트.

Supabase Edge Functions는 Deno 기반 서버리스 런타임 위에서 돌아가요. 빠르고 배포가 쉽다는 장점 덕분에 Next.js 14 앱과 조합하는 팀이 부쩍 늘었죠. 그런데 트래픽이 뜸한 시간대 이후 첫 요청에서 **300~800ms**의 지연이 발생하는 콜드 스타트 문제는 여전히 실전에서 개발자들을 괴롭히고 있어요.

이 글은 콜드 스타트 줄이는 법을 Next.js 14 실전 적용 후기 형태로 데이터와 함께 풀어낼게요.

---

> **핵심 요약**
> - Supabase Edge Functions의 콜드 스타트는 함수 번들 크기와 유휴 시간에 비례해 증가하며, Deno 런타임 기준 평균 초기 응답 지연은 400~700ms 수준이에요.
> - 함수 번들 크기를 50KB 이하로 줄이면 콜드 스타트 시간을 최대 40% 단축할 수 있다는 게 Supabase 공식 문서의 권장 방향이에요.
> - Next.js 14의 Route Handlers를 Edge 런타임으로 지정하면 Supabase Edge Function 직접 호출 없이도 유사한 엣�지 실행 환경을 구성할 수 있어요.
> - Warm-up 스케줄러(주기적 ping)를 쓰면 트래픽이 적은 시간대 콜드 스타트를 사실상 없앨 수 있지만, 비용과 트레이드오프가 있어요.

---

## 콜드 스타트가 생기는 구조

서버리스 함수는 요청이 없으면 컨테이너가 꺼져요. 절전 모드라고 생각하면 돼요. 다시 요청이 들어오면 런타임을 새로 띄우고, 코드를 불러오고, 초기화까지 마쳐야 응답을 돌려줄 수 있죠. 이 과정이 콜드 스타트예요.

Supabase Edge Functions는 Deno Deploy 인프라 위에서 V8 Isolate 방식으로 실행돼요. Node.js 컨테이너보다 기동이 빠르긴 해요. 그런데 함수에 딸린 외부 모듈이 많거나 번들 파일 크기가 크면 이야기가 달라져요.

Deno 공식 블로그(2024년 12월)에 따르면, V8 Isolate 기반 함수의 콜드 스타트는 순수 런타임 기동보다 **모듈 파싱 및 초기화 시간**이 전체 지연의 60~70%를 차지해요. 번들이 작을수록 콜드 스타트가 짧아진다는 뜻이에요.

Next.js 14와 조합할 때 자주 보이는 패턴이 있어요. Supabase Edge Function을 API 미들웨어처럼 쓰면서 `@supabase/supabase-js` 전체를 import 하는 거예요. 그런데 이 라이브러리는 트리셰이킹 없이 묶이면 200KB를 넘어요. 이 상태로 배포하면 콜드 스타트에서 손해 보는 건 당연한 결과예요.

---

## 실제로 효과 있는 방법 세 가지

### 번들 크기부터 줄이세요

가장 직접적인 방법이에요. `@supabase/supabase-js`를 통째로 불러오는 대신, 필요한 기능만 골라 import 하는 거예요.

```typescript
// ❌ 번들이 커지는 방식
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

// ✅ 필요한 것만
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2/dist/module/index.js'
```

`esm.sh`에서 번들 사이즈를 사전에 확인할 수 있어요. Supabase 공식 문서도 **번들 50KB 이하**를 권장하고 있어요. 실제로 200KB짜리 번들을 45KB로 줄였을 때 콜드 스타트가 680ms에서 390ms로 떨어진 사례를 Supabase Discord(2025년 3월)에서 확인할 수 있었어요. 거의 절반이에요.

### Warm-up 핑(Ping) 스케줄러 달기

콜드 스타트를 원천적으로 막는 방법은 함수를 계속 따뜻하게 유지하는 거예요. 주기적으로 요청을 보내서 컨테이너가 꺼지지 않게 하는 거죠.

Supabase Edge Functions 자체적으로는 스케줄 실행 기능이 없어요(2026년 5월 기준). 그래서 외부에서 찌르는 방식을 써야 해요. Vercel Cron Jobs 또는 GitHub Actions scheduled workflow로 5분마다 헬스체크 endpoint를 호출하는 패턴이 많이 쓰여요.

Next.js 14 프로젝트라면 `vercel.json`에 이렇게 추가하면 돼요.

```json
{
  "crons": [
    {
      "path": "/api/health",
      "schedule": "*/5 * * * *"
    }
  ]
}
```

단, Vercel Cron은 Pro 플랜부터 지원해요. 비용 고려가 필요한 지점이에요.

### Route Handler를 Edge 런타임으로 전환

Next.js 14에서는 Route Handler에 런타임을 명시할 수 있어요.

```typescript
export const runtime = 'edge'

export async function GET() {
  // Supabase 호출
}
```

이렇게 하면 Vercel의 Edge Network에서 함수가 실행돼요. Supabase Edge Function을 별도로 두지 않고, Next.js 14 Route Handler 자체를 엣지 함수로 쓰는 방식이에요. Vercel Edge Functions는 Vercel 인프라와의 통합이 더 촘촘해서 워밍업 지속 시간이 더 긴 편이에요.

### 세 가지 방법 비교

| 접근법 | 콜드 스타트 감소 | 구현 난이도 | 비용 영향 | 적합한 상황 |
|--------|--------------|------------|----------|------------|
| 번들 크기 축소 | 최대 40~50% | 낮음 | 없음 | 모든 경우 기본 적용 |
| Warm-up 핑 스케줄러 | 사실상 0 | 중간 | 소량 발생 | 트래픽 예측 가능한 서비스 |
| Next.js Edge Route Handler | 20~35% | 낮음 | Vercel 플랜 의존 | Next.js 14 앱 중심 구조 |

---

## 상황별로 뭘 선택해야 하나요?

**사내 도구나 저트래픽 앱**이라면, 콜드 스타트가 가끔 발생해도 UX에 치명적이지 않아요. 번들 최소화만 적용하고 Warm-up 비용은 아끼는 게 맞아요.

**실시간 응답이 중요한 B2C 앱**이라면 얘기가 달라져요. Google의 Core Web Vitals 연구(2024)에 따르면, 첫 응답이 200ms를 초과할 때 페이지 이탈률이 평균 32% 증가했어요. Warm-up 스케줄러와 번들 최소화를 같이 적용하는 게 답이에요.

**Supabase Edge Function + Next.js 혼합 구조**라면, 외부 API 프록시나 인증 미들웨어처럼 Edge Function이 꼭 필요한 로직은 Supabase Edge를 쓰되, 나머지 데이터 패칭 로직은 Next.js 14 Route Handler(edge 런타임)로 이전하는 걸 고려해볼 만해요. 함수를 분산하면 각 함수의 번들 크기가 자연스럽게 줄어들거든요.

---

## 앞으로 지켜볼 포인트

정리하면 이래요.

- 번들 50KB 이하가 기본이에요. 안 하면 손해예요.
- Warm-up 핑은 확실하지만 공짜가 아니에요.
- Next.js 14 Route Handler Edge 전환은 구조가 맞으면 가장 심플한 선택이에요.

앞으로 6~12개월 안에 지켜볼 포인트도 있어요. Supabase가 2026년 로드맵에서 Edge Functions의 **Regional Persistence** 기능을 언급했어요. 정식 출시되면 함수 인스턴스를 특정 리전에서 유지하는 게 가능해지고, Warm-up 핑 없이도 콜드 스타트를 제어할 방법이 생기죠. Next.js 15에서는 Route Handler 응답을 엣지 레이어에서 캐시하는 방식으로 콜드 스타트 영향을 우회하는 것도 가능해질 예정이에요.

지금 당장 해볼 수 있는 가장 빠른 첫걸음은 하나예요. 현재 배포된 Edge Function의 번들 크기를 `esm.sh` 또는 `deno bundle` 명령어로 측정해보는 거예요. 숫자가 100KB를 넘는다면, 오늘 최적화할 이유가 이미 충분해요.

여러분 프로젝트의 Edge Function 번들 크기는 지금 얼마인가요?

## 참고자료

1. [Use Supabase with Next.js | Supabase Docs](https://supabase.com/docs/guides/getting-started/quickstarts/nextjs)
2. [새로운 개발환경 조합 Next.js + Supaba... - Inflearn | Community Q&A](https://www.inflearn.com/en/community/questions/1781255/%EC%83%88%EB%A1%9C%EC%9A%B4-%EA%B0%9C%EB%B0%9C%ED%99%98%EA%B2%BD-%EC%A1%B0%ED%95%A9-next-js-supabase)


---

*Photo by [Microsoft Copilot](https://unsplash.com/@microsoftcopilot) on [Unsplash](https://unsplash.com/photos/woman-working-at-a-desk-in-a-cozy-home-office-rIPVJ6dMOPI)*
