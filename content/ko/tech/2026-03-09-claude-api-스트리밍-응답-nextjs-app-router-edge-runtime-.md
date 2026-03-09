---
title: "Next.js App Router Edge Runtime에서 Claude API 스트리밍 한국어 깨짐 해결"
date: 2026-03-09T20:03:50+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-web", "claude", "api", "\uc2a4\ud2b8\ub9ac\ubc0d", "TypeScript"]
description: "Edge Runtime에서 한국어 깨짐의 원인은 UTF-8 멀티바이트 처리 방식에 있습니다. TextEncoder/TextDecoder 사용과 charset=utf-8 헤더 명시로 Claude API 스트리밍 응답을 올바르게 출력하는 방법을 설명합니다."
image: "/images/20260309-claude-api-스트리밍-응답-nextjs-app-.webp"
technologies: ["TypeScript", "Next.js", "Node.js", "Claude", "Anthropic"]
faq:
  - question: "Next.js App Router Edge Runtime에서 Claude API 스트리밍 한국어 깨짐 해결 방법"
    answer: "Claude API 스트리밍 응답을 Next.js App Router Edge Runtime에서 사용할 때 한국어가 깨지는 문제는 TextDecoderStream을 사용하고 Content-Type 헤더에 charset=utf-8을 명시하면 해결됩니다. Edge Runtime은 Node.js의 Buffer API를 지원하지 않아 UTF-8 멀티바이트 문자(한국어는 글자당 3바이트)가 청크 경계에서 잘릴 수 있기 때문입니다. 클라이언트 측에서도 String.fromCharCode 대신 TextDecoder를 사용해야 멀티바이트 문자를 안전하게 처리할 수 있습니다."
  - question: "로컬에서는 한국어 정상인데 Vercel 배포하면 깨지는 이유"
    answer: "로컬 개발 환경의 next dev는 기본적으로 Node.js 런타임으로 실행되어 Buffer API가 UTF-8 인코딩을 자동으로 처리해주지만, Vercel 배포 시 Edge Runtime으로 전환되면 Web Standard API만 사용 가능해 동일한 처리가 불가능합니다. 즉, 런타임 환경의 차이가 원인이며 Edge Runtime 환경에 맞는 TextEncoder/TextDecoder 기반 코드로 교체해야 합니다."
  - question: "Edge Runtime에서 TextDecoder와 String.fromCharCode 차이점"
    answer: "String.fromCharCode는 바이트를 단순히 문자로 1:1 변환하기 때문에 UTF-8 멀티바이트 시퀀스를 해석하지 못해 한국어 같은 멀티바이트 문자가 모두 깨집니다. 반면 TextDecoder는 UTF-8 인코딩 규칙에 따라 멀티바이트 시퀀스를 올바르게 해석하므로 스트리밍 환경에서 청크가 글자 중간에 잘려도 안전하게 처리할 수 있습니다."
  - question: "Next.js App Router 스트리밍 응답 Content-Type charset utf-8 설정 왜 필요한가"
    answer: "Content-Type 헤더에 charset=utf-8을 명시하지 않으면 브라우저가 인코딩 방식을 자체적으로 추측하게 되어 잘못된 인코딩으로 한국어를 렌더링할 수 있습니다. Claude API 스트리밍 응답을 Next.js App Router Edge Runtime에서 한국어 깨짐 없이 처리하려면 반드시 text/event-stream; charset=utf-8 형태로 헤더를 설정해야 합니다."
  - question: "Vercel Edge Runtime TransformStream TextDecoderStream 어떤 걸 써야 하나"
    answer: "일반적인 스트리밍 상황에서는 Web Standard API인 TextDecoderStream이 코드가 단순하고 Edge Runtime과 완전히 호환되어 권장됩니다. 다만 청크를 직접 파싱하거나 변환 로직이 복잡한 경우에는 TransformStream과 수동 디코딩 조합이 더 유연하게 대응할 수 있으며, Vercel Edge Network 기준으로 두 방법 모두 안정적으로 동작합니다."
---

Next.js App Router로 Claude API 스트리밍을 붙였는데, 한국어가 `?`나 `▯`로 깨져서 나왔어요. 로컬에서는 멀쩡한데 Vercel에 배포하면 터지는 그 패턴, 맞죠? 원인은 생각보다 명확해요. Edge Runtime의 인코딩 처리 방식 때문이에요.

> **핵심 요약**
> - Edge Runtime은 Node.js `Buffer` API를 지원하지 않아서, UTF-8 멀티바이트 문자(한국어 포함)가 바이트 경계에서 잘리면 깨진 문자로 출력된다.
> - Next.js App Router의 `Response` 스트리밍은 `TextEncoder`/`TextDecoder`를 써야 안전하며, `Content-Type: text/event-stream; charset=utf-8` 헤더 명시가 필수다.
> - Claude API의 `stream: true` 옵션은 SSE 청크를 순차 전송하는데, 각 청크가 멀티바이트 경계에서 잘릴 수 있어 클라이언트 측 `TextDecoder` 설정이 핵심이다.
> - Vercel Edge Network 기준으로 `TransformStream` + `TextDecoderStream` 조합이 가장 안정적인 해결책으로 확인됐다.

---

## Edge Runtime에서 문자가 깨지는 이유

Node.js 환경에서는 `Buffer.from(chunk).toString('utf-8')`처럼 익숙한 방식으로 인코딩을 처리해요. 그런데 Edge Runtime은 달라요. Cloudflare Workers와 동일한 V8 기반 런타임이라서 Node.js의 `Buffer`, `fs`, `path` 같은 API를 쓸 수 없어요. Next.js 공식 문서에 따르면 Edge Runtime은 Web Standard API만 지원해요.

문제는 여기서 시작돼요.

Claude API 스트리밍 응답을 받으면 데이터가 청크 단위로 와요. 영어는 한 글자가 1바이트라 청크가 어디서 잘려도 문자가 온전해요. 반면 한국어는 UTF-8 기준으로 글자당 3바이트예요. 청크 경계가 글자 중간에 걸리면, 그 글자는 절반짜리 바이트 덩어리가 되어 디코딩할 수 없는 상태가 돼요. 그래서 `?`나 `▯`로 출력되는 거예요.

로컬에서 안 깨지는 이유도 간단해요. `next dev`는 기본적으로 Node.js 런타임으로 실행되거든요. `Buffer`가 있어서 알아서 처리해줘요. 배포 환경에서 Edge Runtime으로 전환되는 순간 문제가 터지는 거예요.

---

## 문제가 생기는 코드 패턴

```typescript
// ❌ 이렇게 하면 한국어 깨져요
export const runtime = 'edge';

export async function POST(req: Request) {
  const stream = await anthropic.messages.stream({
    model: 'claude-opus-4-5',
    max_tokens: 1024,
    messages: [{ role: 'user', content: '안녕하세요' }],
  });

  return new Response(stream.toReadableStream(), {
    headers: { 'Content-Type': 'text/event-stream' }, // charset 빠짐
  });
}
```

여기서 두 가지가 문제예요. 첫째, `Content-Type`에 `charset=utf-8`이 없어요. 브라우저가 인코딩을 추측하다가 틀리기도 해요. 둘째, 클라이언트에서 청크를 받을 때 단순히 `Uint8Array`를 `String`으로 변환하면 멀티바이트 문자가 잘려요.

```typescript
// ❌ 클라이언트 - 이것도 위험해요
reader.read().then(({ value }) => {
  const text = String.fromCharCode(...value); // 멀티바이트 무시
  setOutput(prev => prev + text);
});
```

`String.fromCharCode`는 바이트를 그냥 문자로 변환해요. UTF-8 멀티바이트 시퀀스를 해석하지 않으니까 한국어가 다 깨지죠.

---

## 해결책 세 가지 비교

| 방법 | 복잡도 | Edge 호환 | 권장 상황 |
|------|--------|-----------|-----------|
| `TextDecoderStream` (Web API) | 낮음 | ✅ 완전 | 대부분의 경우 |
| `TransformStream` + 수동 디코딩 | 중간 | ✅ 완전 | 커스텀 파싱 필요 시 |
| Node.js 런타임으로 전환 | 낮음 | N/A | Edge 불필요 시 |

### 방법 1: `TextDecoderStream` — 가장 깔끔해요

```typescript
// ✅ 서버 - route.ts
export const runtime = 'edge';

export async function POST(req: Request) {
  const encoder = new TextEncoder();

  const readableStream = new ReadableStream({
    async start(controller) {
      const stream = anthropic.messages.stream({
        model: 'claude-opus-4-5',
        max_tokens: 1024,
        messages: [{ role: 'user', content: await req.text() }],
      });

      for await (const chunk of stream) {
        if (
          chunk.type === 'content_block_delta' &&
          chunk.delta.type === 'text_delta'
        ) {
          controller.enqueue(encoder.encode(chunk.delta.text));
        }
      }
      controller.close();
    },
  });

  return new Response(readableStream, {
    headers: {
      'Content-Type': 'text/event-stream; charset=utf-8', // ← 이게 핵심
      'Cache-Control': 'no-cache',
    },
  });
}
```

```typescript
// ✅ 클라이언트 - { stream: true } 옵션이 포인트
const decoder = new TextDecoder('utf-8', { fatal: false });

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  const text = decoder.decode(value, { stream: true }); // stream: true 필수
  setOutput(prev => prev + text);
}
```

`{ stream: true }` 옵션이 핵심이에요. 이걸 넣어야 `TextDecoder`가 청크 경계에서 잘린 멀티바이트 시퀀스를 다음 청크까지 버퍼에 들고 있다가, 온전한 문자가 완성되는 시점에 출력해줘요. 빠진다면, 경계에서 잘린 바이트를 그냥 처리하려다 깨져요.

### 방법 2: `TransformStream` — 더 세밀하게 제어할 때

SSE 형식으로 가공하거나 메타데이터를 붙여야 한다면 `TransformStream`이 맞아요.

```typescript
const { readable, writable } = new TransformStream();
const writer = writable.getWriter();
const encoder = new TextEncoder();

(async () => {
  for await (const chunk of stream) {
    if (chunk.type === 'content_block_delta') {
      const data = `data: ${JSON.stringify({ text: chunk.delta.text })}\n\n`;
      await writer.write(encoder.encode(data));
    }
  }
  await writer.close();
})();
```

### 방법 3: Node.js 런타임 전환 — Edge가 필수가 아닐 때

Edge Runtime이 꼭 필요하지 않다면 이게 제일 빠른 해결책이에요.

```typescript
export const runtime = 'nodejs'; // 명시적으로 Node.js로
```

실제로 AI 스트리밍처럼 응답 자체가 수 초 걸리는 경우라면, Edge Runtime이 주는 수십 밀리초 지연 감소가 UX에 거의 영향 없어요. 한국어 깨짐이 훨씬 큰 문제니까요.

---

## 상황별 체크리스트

**로컬은 되는데 Vercel 배포 후 깨지는 경우**: `export const runtime = 'edge'` 선언이 있는지 확인하세요. 있다면 클라이언트 `TextDecoder`에 `{ stream: true }` 옵션 추가가 첫 번째예요.

**일부 문자만 깨지는 경우**: 특정 청크 크기에서만 재현되는 패턴이에요. `fatal: true`로 설정하면 디코딩 실패 시 예외가 발생해서 어느 지점에서 깨지는지 정확히 알 수 있어요. 디버깅할 때만 `fatal: true`로 바꿔보는 걸 권장해요.

**Anthropic SDK를 쓰는데도 깨지는 경우**: `@anthropic-ai/sdk` 0.20 이후 버전은 Edge Runtime용 Web Streams API를 내부적으로 지원해요. 그런데 SDK가 서버 쪽을 처리해줘도 클라이언트 디코딩은 개발자 몫이에요. `{ stream: true }` 옵션은 여전히 필요해요.

---

## 정리하면

- Edge Runtime에서 한국어가 깨지는 건 버그가 아니라 Web Standard API의 특성이에요.
- `TextDecoder`에 `{ stream: true, fatal: false }` 두 옵션 넣으면 대부분 해결돼요.
- `Content-Type: text/event-stream; charset=utf-8` 헤더 명시는 선택이 아니에요.
- Edge Runtime이 꼭 필요한 게 아니라면 Node.js 런타임이 훨씬 단순해요.

지금 쓰는 `TextDecoder` 인스턴스에 `stream: true` 옵션 들어가 있는지 먼저 확인해보세요. 없다면, 그게 깨짐의 원인일 가능성이 높아요.

---

*이 글에서 다룬 코드는 Next.js 15.x, `@anthropic-ai/sdk` 0.24.x, Vercel Edge Runtime 기준이에요. SDK 버전별로 스트림 API가 달라질 수 있으니 공식 문서와 함께 확인하세요.*

## 참고자료

1. [Claude Code 기능 10개, 중요한 순서대로 정리했다 (1/2) - DEV Community](https://dev.to/ji_ai/claude-code-gineung-10gae-jungyohan-sunseodaero-jeongrihaessda-12-1540)
2. [Routing: API Routes | Next.js](https://nextjs.org/docs/pages/building-your-application/routing/api-routes)
3. [Next.js Optimization Recipes | Cursor, Claude Code & Codex | Developer Toolkit](https://developertoolkit.ai/en/cookbook/frontend-recipes/nextjs-patterns/)


---

*Photo by [Vitaly Gariev](https://unsplash.com/@silverkblack) on [Unsplash](https://unsplash.com/photos/beekeeper-in-protective-suit-examining-honeycomb-frame-g1e3dtCrIC4)*
