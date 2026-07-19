---
title: "Next.js App Router Edge Runtime에서 Claude 스트리밍 응답이 느린 원인과 Node Runtime 전환 비교"
date: 2026-05-28T23:05:17+0900
draft: false
author: "Jake Park"
categories: ["ai"]
tags: ["subtopic-ai", "next.js", "app", "router", "TypeScript"]
description: "Next.js App Router에서 Claude 스트리밍 응답이 3-5초 지연되는 원인은 Edge Runtime 비호환성입니다. Node Runtime 전환으로 첫 토큰 응답 속도를 개선하는 방법을 실제 설정 코드와 함께 설명합니다."
image: "/images/20260528-nextjs-app-router-edge-runtime.webp"
technologies: ["TypeScript", "Next.js", "Node.js", "Claude", "Anthropic"]
faq:
  - question: "Next.js App Router Edge Runtime Claude 스트리밍 응답 느린 이유"
    answer: "Next.js App Router Edge Runtime에서 Claude 스트리밍 응답이 느린 핵심 원인은 SDK 호환성 문제입니다. @anthropic-ai/sdk는 내부적으로 Node.js의 stream API와 node-fetch를 사용하도록 설계됐는데, Edge Runtime은 이를 지원하지 않아 Web Streams API로 변환하는 과정에서 버퍼링이 발생합니다. 실제 측정 사례에 따르면 Edge Runtime의 Claude 스트리밍 TTFB는 Node Runtime 대비 평균 2-4배 높게 나타납니다."
  - question: "Next.js route handler edge runtime node runtime 스트리밍 성능 차이"
    answer: "Next.js App Router Edge Runtime과 Node Runtime의 Claude 스트리밍 응답 지연 원인 및 비교 관점에서 보면, TTFB 기준으로 Edge Runtime은 1,800~4,500ms, Node Runtime은 400~900ms로 Node Runtime이 현저히 빠릅니다. 콜드 스타트는 Edge Runtime이 50~100ms로 유리하지만, AI 챗봇 사용자는 첫 글자 출력 속도에 더 민감하기 때문에 실질적인 체감 성능은 Node Runtime이 우수합니다."
  - question: "Next.js edge runtime 최대 실행시간 제한 AI 응답 끊김"
    answer: "Vercel 기준 Edge Runtime의 최대 실행 시간은 30초로 제한되어 있습니다. 긴 문서 요약이나 코드 분석처럼 Claude가 응답 생성에 시간이 걸리는 작업은 이 제한을 초과해 스트림이 강제로 끊길 수 있습니다. 반면 Node Runtime은 Pro 플랜 기준 최대 300초까지 허용되므로, 장문 생성이 필요한 AI 기능에는 Node Runtime이 적합합니다."
  - question: "claude sdk edge runtime 지원 여부 anthrophic"
    answer: "@anthropic-ai/sdk v0.20 이후 버전부터 Edge 환경을 일부 지원하기 시작했지만, ReadableStream 처리 방식의 차이로 인해 청크 손실이 간헐적으로 발생할 수 있어 완전한 지원이 아닙니다. Anthropic SDK는 Node.js 네이티브 API를 기반으로 설계되었기 때문에, 안정적인 스트리밍을 위해서는 Node Runtime 환경에서 사용하는 것을 권장합니다."
  - question: "Next.js AI 스트리밍 edge runtime 유지하면서 안정성 높이는 방법"
    answer: "Vercel Edge Network의 이점을 포기하지 않으면서 Claude 스트리밍 안정성을 확보하려면 하이브리드 구조가 현실적인 선택입니다. Claude API를 호출하는 Route Handler는 Node Runtime으로 설정하고, CDN 캐싱이나 인증 처리 같은 경량 작업만 Edge Runtime에 맡기는 방식입니다. 실제로 Next.js 공식 문서도 2026년 초부터 AI 스트리밍 예시의 기본 Runtime을 Node로 명시하기 시작했습니다."
aliases:
  - "/tech/2026-05-28-nextjs-app-router-edge-runtime-claude-스트리밍-응답-지연-원/"
  - "/ko/tech/2026-05-28-nextjs-app-router-edge-runtime-claude-스트리밍-응답-지연-원/"

---

Claude API로 스트리밍 응답을 구현했는데, 첫 토큰이 나오기까지 3-5초씩 걸린다면? Edge Runtime을 쓰고 있을 가능성이 높아요.

Next.js App Router에 AI 기능을 얹는 팀이 급격히 늘었어요. Vercel 생태계 기준으로 AI 관련 Route Handler 배포 수가 전년 대비 두 배 이상 증가했다는 건 업계에서 공공연한 얘기죠. 그런데 막상 구현하다 보면 이상하게 응답이 느리고, 간헐적으로 스트림이 끊기는 문제를 맞닥뜨리게 돼요.

문제의 핵심은 하나예요. **Anthropic의 Claude SDK는 Edge Runtime 환경에서 정상적으로 동작하도록 설계되지 않았어요.** 그걸 모르고 기본 설정 그대로 쓰다 보면, 성능 병목이 어디서 왔는지도 모른 채 며칠을 날리게 되는 거예요.

> **핵심 요약**
> - Next.js App Router의 Route Handler는 기본값으로 Node.js Runtime을 쓰지만, `export const runtime = 'edge'`를 선언하는 순간 Claude SDK가 의존하는 Node.js 네이티브 API(`node-fetch`, `stream`)가 전부 차단돼요.
> - Edge Runtime에서 Claude 스트리밍 응답의 TTFB는 Node Runtime 대비 평균 2-4배 높게 측정되는 사례가 보고되고 있어요.
> - `@anthropic-ai/sdk` v0.20 이후 버전은 Edge 환경을 일부 지원하지만, `ReadableStream` 처리 방식 차이로 인해 여전히 청크 손실이 발생할 수 있어요.
> - Node Runtime으로 전환하면 콜드 스타트는 소폭 증가하지만, 스트리밍 안정성과 완성도는 확연히 개선돼요.
> - Vercel Edge Network를 포기하지 않으면서 안정적인 스트리밍을 원한다면, Route Handler는 Node Runtime으로 두고 CDN 레이어만 Edge에 맡기는 하이브리드 구조가 현실적인 선택이에요.

---

## Edge Runtime이 뭔지, 왜 선택했는지부터

Next.js의 Runtime 선택은 파일 하나에서 결정돼요. Route Handler나 Middleware에 `export const runtime = 'edge'`를 적으면 해당 파일은 V8 기반의 경량 런타임에서 실행돼요. Node.js가 아니에요.

Edge Runtime의 장점은 분명해요. 전 세계 PoP(Point of Presence)에서 실행되니까 지연이 낮고, 콜드 스타트가 수십 밀리초 수준이에요. 정적 콘텐츠를 가공하거나, 인증 토큰을 검사하거나, 간단한 리다이렉트 처리하는 데는 이보다 나은 게 없어요.

그런데 **"가벼운 환경"이라는 게 곧 "제한된 환경"**이라는 뜻이기도 해요.

Edge Runtime에서 금지된 것들만 봐도 감이 와요.

- `fs`, `path`, `crypto` 같은 Node.js 코어 모듈 전부 사용 불가
- `node-fetch` 기반의 HTTP 클라이언트 불가 (Web Fetch API만 허용)
- `Buffer` 객체 제한적 지원
- `stream` 모듈 불가

바로 이 지점에서 Claude SDK가 걸리는 거예요. `@anthropic-ai/sdk`는 내부적으로 Node.js `stream` API와 `node-fetch`를 조건부로 써요. Edge 환경을 감지하면 Web Streams API로 폴백하는 로직이 있긴 한데, 이게 완벽하지 않아요.

실제로 2026년 초, Next.js 공식 문서도 AI 스트리밍 예시에서 기본 Runtime을 Node로 명시하기 시작했어요. 이 변화 자체가 시사하는 바가 있죠.

---

## 지연이 실제로 어떻게 생기는가

### 스트림 초기화 비용의 차이

Edge Runtime에서 Claude API를 호출하는 과정을 보면 이해가 쉬워요.

1. Edge 함수가 Anthropic 서버에 요청을 보내요.
2. Anthropic 서버는 스트리밍 응답을 `text/event-stream`으로 돌려줘요.
3. Edge 함수가 이걸 받아서 클라이언트에 전달해야 해요.

여기서 Edge Runtime은 Web `ReadableStream`만 써요. 그런데 `@anthropic-ai/sdk`의 스트리밍 응답 객체는 내부적으로 Node.js `Readable` 스트림을 기반으로 설계됐어요. SDK가 Edge를 감지해서 변환을 시도하는데, 이 변환 레이어에서 버퍼링이 생겨요.

쉽게 말하면, 수도꼭지(Anthropic 서버)에서 물이 나오는데, 파이프(SDK) 규격이 달라서 어댑터를 끼우다 보니 물줄기가 끊기는 셈이에요.

### 콜드 스타트 vs 스트리밍 안정성 트레이드오프

실제 수치를 보면 직관적이에요.

| 항목 | Edge Runtime | Node Runtime |
|------|-------------|-------------|
| 콜드 스타트 (Vercel) | ~50-100ms | ~300-800ms |
| TTFB (Claude 스트리밍) | 1,800-4,500ms | 400-900ms |
| 청크 손실 빈도 | 간헐적 발생 | 거의 없음 |
| SDK 완전 지원 여부 | 부분 지원 | 완전 지원 |
| 최대 실행 시간 | 30초 (Vercel 기준) | 300초 (Pro 플랜) |
| 메모리 한도 | 128MB | 1,024MB (Pro) |

*출처: Vercel Edge Runtime 공식 제한 사항 문서 (2026.03 기준), Medium의 "Edge Runtime vs Node Runtime in Next.js" 실험 결과 참조*

콜드 스타트만 보면 Edge가 압도적이에요. 그런데 스트리밍 TTFB로 넘어가면 역전돼요. AI 챗봇 특성상 사용자가 느끼는 체감 속도는 콜드 스타트보다 첫 글자가 언제 나오느냐에 훨씬 민감하거든요.

### 최대 실행 시간 문제

이게 더 결정적이에요. Claude로 긴 문서를 요약하거나 코드를 분석하는 경우, 응답 생성에 30초를 훌쩍 넘기는 일이 생겨요. Vercel 기준으로 Edge Runtime은 최대 30초 실행 제한이 있어요. Node Runtime은 Pro 플랜에서 300초까지 가능하죠.

길게 쓸 것 같은 작업에 Edge를 붙이면, 응답 중간에 그냥 잘려요.

---

## Node Runtime으로 전환하는 방법

마이그레이션 자체는 간단해요. Route Handler 파일 상단에서 `runtime` 선언을 지우거나 명시적으로 Node로 바꾸면 돼요.

```typescript
// app/api/chat/route.ts

// 이걸 지우거나 아래처럼 바꾸기
export const runtime = 'nodejs' // 또는 아예 선언 삭제 (기본값이 nodejs)

export async function POST(req: Request) {
  const { messages } = await req.json()

  const stream = await anthropic.messages.stream({
    model: 'claude-opus-4-5',
    max_tokens: 2048,
    messages,
  })

  return new Response(stream.toReadableStream(), {
    headers: { 'Content-Type': 'text/event-stream' },
  })
}
```

`stream.toReadableStream()`은 SDK v0.20 이후에 추가된 메서드예요. Node 환경에서는 이게 Web Streams API 호환 `ReadableStream`을 바로 반환해줘서, `TransformStream`으로 따로 변환할 필요가 없어요.

---

## 그래서 어떤 구조를 써야 할까

**시나리오 1 — 간단한 챗봇, 응답 길이 짧음 (500 토큰 이하)**

Edge Runtime도 충분히 작동해요. 단, SDK 대신 Fetch API로 직접 Anthropic API를 호출하는 방식을 권해요. SDK 의존성을 제거하면 Edge 호환성 문제가 크게 줄어들거든요.

**시나리오 2 — 문서 분석, 코드 리뷰, 긴 요약 작업**

Node Runtime이에요. 실행 시간 제한과 스트리밍 안정성 모두 Node가 필요한 조건이에요. 콜드 스타트 증가는 Lambda Warming이나 Vercel Fluid Compute 설정으로 어느 정도 상쇄할 수 있어요.

**시나리오 3 — 글로벌 서비스, 지연 최소화가 핵심**

하이브리드 구조를 쓰세요. Route Handler는 Node Runtime으로 특정 리전(예: `iad1`)에 고정하고, 그 앞단의 인증/라우팅 미들웨어만 Edge로 유지하는 거예요. 사용자 요청은 가장 가까운 Edge PoP에서 빠르게 라우팅되고, 실제 AI 처리는 Node에서 안정적으로 돼요.

---

## 앞으로 주시해야 할 것들

지금 당장 Claude 스트리밍을 쓰는 Next.js 프로젝트가 있다면, `route.ts` 파일에 `runtime = 'edge'`가 있는지 확인해보세요. 있으면 지우는 게 먼저예요.

앞으로 6-12개월 사이 이 구조가 어떻게 바뀔지는 두 가지를 보면 돼요.

첫째, Vercel의 Fluid Compute 기능이 Node Runtime의 콜드 스타트를 얼마나 줄이는지예요. 이 격차가 좁혀지면 "Edge를 써야 할 이유" 자체가 AI 라우트에서는 거의 사라져요.

둘째, Anthropic이 공식적으로 Edge-native SDK를 내놓을지예요. 현재 `@anthropic-ai/sdk`의 GitHub 이슈를 보면 Edge 지원 요청이 꾸준히 올라오고 있어요. 공식 지원이 생기면 이 글의 전제 자체가 바뀔 수도 있죠.

결국 핵심 질문은 이거예요. "내 AI 라우트가 Edge의 어떤 장점을 실제로 쓰고 있나요?" 대답이 없다면, Node Runtime이 맞는 선택이에요.

## 참고자료

1. [Next.js에서 Edge Runtime은 언제 쓰는 걸까? (Node.js와 비교 정리)](https://velog.io/@do_dam/Next.js%EC%97%90%EC%84%9C-Edge-Runtime%EC%9D%80-%EC%96%B8%EC%A0%9C-%EC%93%B0%EB%8A%94-%EA%B1%B8%EA%B9%8C-Node.js%EC%99%80-%EB%B9%84%EA%B5%90-%EC%A0%95%EB%A6%AC)
2. [Lobehub](https://lobehub.com/ko/skills/davila7-claude-code-templates-nextjs-best-practices)
3. [Edge Runtime vs Node Runtime in Next.js (Complete Practical Guide) | by Chandan | Full-Stack Develop](https://medium.com/codetodeploy/edge-runtime-vs-node-runtime-in-next-js-complete-practical-guide-b853dea38751)


---

*Photo by [Balázs Kétyi](https://unsplash.com/@balazsketyi) on [Unsplash](https://unsplash.com/photos/black-android-smartphone-sScmok4Iq1o)*
