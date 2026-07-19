---
title: "Claude API 스트리밍 응답 Next.js App Router 구현 삽질 기록과 Edge Runtime 주의사항"
date: 2026-05-14T21:04:44+0900
draft: false
author: "Jake Park"
categories: ["ai"]
tags: ["subtopic-web", "claude", "api", "/uc2a4/ud2b8/ub9ac/ubc0d", "TypeScript"]
description: "Vercel 배포 직후 30초 타임아웃으로 Claude API 스트리밍이 먹통된 실제 사례. Next.js App Router에서 edge runtime 설정 두 줄 누락이 원인이었던 삽질과 Response 호환성 이슈 해결법을 공유합니다."
image: "/images/20260514-claude-api-스트리밍-응답-nextjs-app-.webp"
technologies: ["TypeScript", "Next.js", "Node.js", "Claude", "Anthropic"]
faq:
  - question: "Next.js App Router Claude API 스트리밍 Vercel 배포하면 타임아웃 나는 이유"
    answer: "Claude API 스트리밍 응답 Next.js App Router 구현 삽질 기록 edge runtime 주의사항에서 정리된 핵심 원인은 `export const runtime = 'edge'` 설정 누락이에요. 이 설정이 없으면 Vercel의 기본 Node.js Lambda 환경으로 배포되는데, 스트리밍 응답이 제대로 flush되지 않거나 타임아웃으로 끊겨요. 로컬 개발 서버는 폴리필로 동작해서 문제가 없지만, 배포 환경에서만 재현되는 이유가 바로 이 runtime 차이예요."
  - question: "App Router Route Handler edge runtime 설정 방법"
    answer: "`app/api/chat/route.ts` 파일 상단에 `export const runtime = 'edge'`를 추가하면 돼요. 이 두 줄이 없으면 스트리밍에 최적화된 edge 환경 대신 기본 Lambda로 실행되어 buffering이나 타임아웃이 발생해요. Claude API처럼 응답 시간이 긴 스트리밍 요청일수록 이 설정이 필수예요."
  - question: "Claude API 스트리밍 클라이언트 이탈해도 토큰 계속 소비되는 문제 해결"
    answer: "Anthropic SDK의 `messages.stream()` 호출 시 두 번째 인자로 `{ signal: req.signal }`을 전달하면 돼요. 이렇게 하면 클라이언트가 페이지를 이탈하거나 요청을 취소했을 때 서버 사이드 스트림도 함께 종료돼요. AbortSignal 연결을 빠뜨리면 클라이언트가 없어진 후에도 Claude API 호출이 계속 실행되어 불필요한 토큰 비용이 발생해요."
  - question: "Next.js App Router Pages Router 스트리밍 구현 방식 차이"
    answer: "Pages Router는 `res.write()` + `res.end()` 패턴으로 Node.js `http.ServerResponse` 객체를 직접 다뤘지만, App Router의 Route Handler는 Web Standard API 기반의 `new Response(ReadableStream)` 방식으로 바뀌었어요. 검색으로 찾은 예제 코드가 어느 버전 기준인지 확인하지 않고 복붙하면 동작하지 않는 이유가 이 패러다임 차이 때문이에요."
  - question: "EventSource 스트리밍 응답 프론트엔드에서 파싱 안 될 때 확인할 것"
    answer: "Claude API 스트리밍 응답 Next.js App Router 구현 삽질 기록 edge runtime 주의사항에 따르면, `new Response(stream)` 반환 시 `Content-Type: text/event-stream` 헤더를 명시해야 해요. 이 헤더가 없으면 프론트엔드의 `EventSource`가 응답을 올바르게 파싱하지 못해요. headers 객체에 `'Content-Type': 'text/event-stream'`을 추가하는 것만으로 해결되는 경우가 많아요."
aliases:
  - "/tech/2026-05-14-claude-api-스트리밍-응답-nextjs-app-router-구현-삽질-기록-edge/"
  - "/ko/tech/2026-05-14-claude-api-스트리밍-응답-nextjs-app-router-구현-삽질-기록-edge/"

---

배포 당일, AI 채팅 기능이 완전히 먹통이 됐어요. 로컬에서 멀쩡하게 돌아가던 Claude API 스트리밍 응답이 Vercel에 올리자마자 30초 타임아웃으로 죽어버린 거예요. 원인은 단 하나—`runtime` 설정 두 줄이 빠져 있었던 거였어요.

Claude API를 Next.js App Router에 연동하는 팀이 빠르게 늘고 있어요. Anthropic 공식 SDK 다운로드 수는 2025년 초 대비 세 배 이상 늘었고, Next.js 14/15 기반 AI 앱의 절반 이상이 App Router를 채택하고 있다고 Next.js 팀 블로그(2025년 12월 기준)에서 밝혔어요. 그런데 막상 구현하려면 스트리밍, edge runtime, Response 객체 호환성 이슈가 얽혀서 생각보다 훨씬 많이 막혀요.

이 글은 그 삽질의 기록이에요. 잘못된 접근과 올바른 접근을 나란히 놓고, 어디서 왜 터지는지 정리했어요.

> **핵심 요약**
> - Claude API 스트리밍 응답을 App Router Route Handler에서 쓰려면 `export const runtime = 'edge'` 설정이 필수예요—없으면 Vercel 기본 Lambda 환경에서 30초 타임아웃이 발생해요.
> - Node.js runtime과 edge runtime은 사용 가능한 API가 달라서, `ReadableStream`, `TransformStream` 같은 Web Streams API는 edge에서만 안정적으로 동작해요.
> - Anthropic SDK의 `stream()` 메서드는 내부적으로 `fetch` 기반이라 edge 환경에서 더 자연스럽게 동작하지만, `AbortController` 연결을 빠뜨리면 클라이언트 이탈 후에도 스트림이 계속 흘러요.
> - App Router Route Handler에서 `new Response(stream)`을 반환할 때 Content-Type을 `text/event-stream`으로 명시하지 않으면 프론트엔드 `EventSource`가 파싱을 못 해요.

---

## Pages Router 시절과 뭐가 달라졌나요?

Pages Router에서는 AI 스트리밍 응답을 `res.write()` + `res.end()` 패턴으로 구현했어요. Node.js `http.ServerResponse` 객체를 직접 다루는 방식이죠. 코드가 좀 지저분해도 동작은 잘 됐어요.

App Router가 도입되면서 Route Handler(`app/api/route.ts`)로 넘어왔는데, 여기서 패러다임이 바뀌었어요. `Request`/`Response`가 Web Standard API 기반으로 교체됐거든요. 스트리밍 처리 방식도 완전히 달라진 거예요.

```
Pages Router: res.write() → Node.js Stream
App Router: new Response(ReadableStream) → Web Streams API
```

두 방식이 공존하는 마이그레이션 기간에 혼란이 생기는 게 당연해요. Next.js 공식 문서에도 두 방식이 각각 설명되어 있어서, 검색으로 찾은 예제 코드가 어느 버전 기준인지 모르면 그냥 복붙했다가 터지는 거예요.

스트리밍 자체가 긴 HTTP 연결을 유지하는 방식인데, App Router edge runtime의 핵심 주의사항이 바로 이 "연결 지속 시간" 문제예요. 기본 Node.js Lambda 환경은 Vercel 기준 최대 10초(Hobby 플랜) 또는 60초인데, edge runtime은 streaming 응답에 훨씬 최적화되어 있어요.

---

## 실제 삽질 포인트 세 가지

### 1. `runtime = 'edge'` 없이 배포하면 벌어지는 일

로컬 개발 서버에서는 runtime 설정 없이도 스트리밍이 돼요. Node.js 환경이라 `ReadableStream`을 자체 폴리필로 처리하거든요. 문제는 Vercel 같은 서버리스 환경에 올릴 때예요.

설정 없이 배포하면 기본적으로 Node.js Lambda로 동작하는데, 스트리밍 응답이 Lambda 환경에서 제대로 flush되지 않아요. Claude가 응답을 다 생성할 때까지 기다렸다가 한꺼번에 내보내는 buffering이 발생하거나, 아예 타임아웃으로 끊겨요.

```typescript
// app/api/chat/route.ts
export const runtime = 'edge' // 이 한 줄이 없으면 배포 환경에서 터져요

export async function POST(req: Request) {
  // ...
}
```

단순해 보이는 두 줄인데, 빠뜨리면 "로컬에선 되는데 배포하면 안 돼요" 상황이 반복돼요.

### 2. `AbortController` 연결 빠뜨리기

클라이언트가 응답 도중 페이지를 이탈하거나 요청을 취소했을 때, 서버 사이드 스트림도 같이 종료돼야 해요. 안 그러면 Claude API 호출이 계속 흘러서 토큰 비용이 낭비돼요.

```typescript
// 잘못된 패턴
const stream = await anthropic.messages.stream({
  model: 'claude-opus-4-5',
  messages: [...],
})

// 올바른 패턴
const { signal } = req
const stream = await anthropic.messages.stream(
  { model: 'claude-opus-4-5', messages: [...] },
  { signal } // AbortController signal 연결
)
```

Anthropic SDK는 `fetch` 기반이라 `AbortSignal`을 두 번째 인자로 받아요. 이걸 빠뜨리면 고비용 요청이 클라이언트 이탈 후에도 계속 실행되는 거예요.

### 3. Content-Type 헤더 누락

```typescript
return new Response(readableStream, {
  headers: {
    'Content-Type': 'text/event-stream', // 이거 없으면 프론트에서 파싱 못 해요
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
  },
})
```

`text/event-stream` 없이 내보내면 브라우저가 그냥 텍스트 응답으로 받아서 전체가 다 올 때까지 기다려요. 스트리밍의 의미가 사라지는 거죠.

---

## Node.js runtime vs Edge runtime: 뭘 골라야 하나요?

| 비교 항목 | Node.js Runtime | Edge Runtime |
|-----------|----------------|--------------|
| 스트리밍 안정성 | Vercel에서 제한적 | 안정적 |
| 콜드 스타트 | 느림 (100-500ms) | 빠름 (0-50ms) |
| 사용 가능 API | 전체 Node.js API | Web Standard API만 |
| `fs`, `path` 모듈 | 사용 가능 | 사용 불가 |
| 실행 시간 제한 | 60초 (Pro 기준) | 30초 (단, streaming은 예외) |
| DB 직접 연결 | 가능 | 불가 (HTTP 기반 DB만) |
| **추천 상황** | DB 연동 필요 시 | AI 스트리밍 전용 |

Claude API 스트리밍만 처리하는 Route Handler라면 edge runtime이 맞아요. 단, DB 연결이 필요하다면 edge에서는 직접 연결이 안 되니까 Prisma Accelerate나 PlanetScale HTTP Driver 같은 HTTP 기반 솔루션을 써야 해요.

트레이드오프가 명확해요. 스트리밍 AI 응답 엔드포인트는 edge로, DB나 파일 시스템 접근이 필요한 부분은 Node.js runtime Route Handler로 분리하는 게 현실적인 접근이에요.

---

## 실제로 동작하는 구현 패턴

**시나리오 1: 단순 채팅 스트리밍**

가장 흔한 케이스예요. `app/api/chat/route.ts`에서 Claude API를 호출하고 스트림을 그대로 내보내는 패턴이에요.

```typescript
export const runtime = 'edge'

export async function POST(req: Request) {
  const { messages } = await req.json()
  const { signal } = req

  const anthropicStream = await anthropic.messages.stream(
    {
      model: 'claude-opus-4-5',
      max_tokens: 1024,
      messages,
    },
    { signal }
  )

  const readable = new ReadableStream({
    async start(controller) {
      for await (const chunk of anthropicStream) {
        if (chunk.type === 'content_block_delta') {
          controller.enqueue(
            new TextEncoder().encode(chunk.delta.text)
          )
        }
      }
      controller.close()
    },
  })

  return new Response(readable, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
    },
  })
}
```

**시나리오 2: Vercel AI SDK와 함께 쓰기**

Vercel AI SDK의 `StreamingTextResponse`를 쓰면 Content-Type, AbortController 연결을 자동으로 처리해줘요. 반복 코드를 줄이고 싶다면 이 방식이 깔끔해요. 단, SDK 버전 간 호환성 이슈가 가끔 있으니 `@ai-sdk/anthropic` 패키지 버전을 고정하는 걸 권장해요.

---

## 앞으로 주시해야 할 것들

- **Next.js 15 이후 Partial Prerendering(PPR)**: 스트리밍 응답과 PPR이 충돌하는 케이스가 보고되고 있어요. 2026년 하반기 Next.js 메이저 업데이트에서 정리될 가능성이 높아요.
- **Anthropic SDK 2.x 변화**: `messages.stream()` API가 꾸준히 바뀌고 있어요. CHANGELOG를 주기적으로 확인하는 게 제일 확실해요.
- **edge runtime 실행 시간**: Vercel이 edge streaming 제한을 계속 완화하는 추세예요. 현재 스펙보다 여유가 생길 가능성이 있어요.

---

## 마무리

Claude API 스트리밍 응답 App Router 구현에서 대부분의 문제는 세 줄로 압축돼요.

- `export const runtime = 'edge'`
- `AbortController signal` 연결
- `Content-Type: text/event-stream` 헤더

로컬에서 잘 된다고 끝난 게 아니에요. Vercel 배포 환경에서의 동작이 실제 기준이고, edge runtime 주의사항을 미리 체크리스트로 만들어두면 배포 당일 당황하는 일이 없어요.

Next.js App Router가 빠르게 바뀌고 있어서 6개월 전 예제 코드가 지금은 안 되는 경우도 많아요. 구현 전에 Next.js 공식 문서(nextjs.org/docs)의 Route Handler 섹션 날짜를 꼭 확인해 보세요. 여러분 팀은 어떤 패턴으로 스트리밍을 구현하고 있나요? 댓글로 공유해 주세요.

## 참고자료

1. [Routing: API Routes | Next.js](https://nextjs.org/docs/pages/building-your-application/routing/api-routes)
2. [nextjs-best-practices - Skills](https://lobehub.com/skills/haniakrim21-everything-claude-code-nextjs-best-practices)


---

*Photo by [Bernd 📷 Dittrich](https://unsplash.com/@hdbernd) on [Unsplash](https://unsplash.com/photos/a-pixelated-orange-character-with-a-hat-GPPbPWwTHdg)*
