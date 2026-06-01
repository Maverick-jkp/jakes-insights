---
title: "Claude API 스트리밍이 Next.js 14 서버 액션에서 끊기는 문제와 해결 방법"
date: 2026-04-16T20:18:37+0900
draft: false
author: "Jake Park"
categories: ["ai"]
tags: ["subtopic-web", "claude", "api", "\uc2a4\ud2b8\ub9ac\ubc0d", "TypeScript"]
description: "Next.js 14 서버 액션은 응답을 직렬화해 반환하므로 Claude API ReadableStream 스트리밍과 구조적으로 충돌합니다. Route Handler로 전환하면 토큰 끊김 없이 스트리밍을 구현할 수 있습니다."
image: "/images/20260416-claude-api-스트리밍-응답-nextjs-14-a.webp"
technologies: ["TypeScript", "React", "Next.js", "Claude", "Anthropic"]
faq:
  - question: "Next.js 14 서버 액션에서 Claude API 스트리밍 응답이 끊기는 이유"
    answer: "Claude API 스트리밍 응답 Next.js 14 App Router 서버 액션 적용 시 끊기는 문제는 구조적 충돌 때문이에요. 서버 액션은 React 직렬화 레이어를 통해 결과를 한 번에 묶어서 반환하는 방식이라, Claude API의 ReadableStream을 클라이언트로 실시간 전달하지 못해요. 결과적으로 응답이 완전히 끝난 후 한 번에 오거나, 첫 청크만 오고 끊기거나, 빈 응답이 오는 세 가지 증상 중 하나로 나타나요."
  - question: "Next.js App Router에서 Claude API 스트리밍 구현하는 가장 좋은 방법"
    answer: "Claude API 스트리밍 응답 Next.js 14 App Router 서버 액션 적용 시 끊기는 문제를 해결하려면 서버 액션 대신 Route Handler(/app/api/chat/route.ts)를 사용하는 방법이 가장 권장돼요. Route Handler는 ReadableStream을 직접 지원해서 추가 패키지 없이 토큰 단위의 매끄러운 스트리밍이 가능하고, App Router와도 충돌 없이 동작해요."
  - question: "Vercel AI SDK streamText 서버 액션 스트리밍 실제로 작동하나요"
    answer: "Vercel AI SDK의 streamText와 createStreamableValue를 조합하면 서버 액션에서도 스트리밍 비슷한 동작을 구현할 수 있어요. 다만 내부적으로 폴링 방식을 사용하기 때문에 Route Handler 방식의 진짜 토큰 단위 스트리밍보다는 약간 덜 매끄럽고, ai와 @ai-sdk/anthropic 패키지 의존성이 추가돼요."
  - question: "Next.js Route Handler SSE 스트리밍 헤더 설정 방법"
    answer: "Next.js Route Handler에서 SSE 스트리밍을 구현할 때는 Content-Type을 text/event-stream으로, Cache-Control은 no-cache로, Connection은 keep-alive로 설정해야 해요. 이 헤더 조합이 없으면 브라우저가 응답을 스트림이 아닌 일반 HTTP 응답으로 처리해서 버퍼링이 발생할 수 있어요."
  - question: "Claude API anthropic.messages.stream 클라이언트 fetch로 읽는 방법"
    answer: "서버에서 Claude API의 stream.toReadableStream()을 Response로 반환하면, 클라이언트에서는 fetch()로 해당 엔드포인트를 호출한 뒤 response.body를 ReadableStream으로 읽으면 돼요. 이렇게 하면 서버에서 토큰이 생성되는 즉시 청크 단위로 받아서 화면에 실시간으로 표시할 수 있어요."
---

스트리밍 붙였는데 토큰이 뚝뚝 끊겨요. 아니면 아예 응답이 안 오거나.

Next.js 14 App Router에서 Claude API 스트리밍을 서버 액션으로 연결하려는 개발자들이 지금도 가장 많이 겪는 문제예요.

근데 이건 코드 실수가 아니에요. 구조적 충돌이에요.

> **핵심 요약**
> - Next.js 14 서버 액션은 스트리밍 응답 전송에 구조적으로 맞지 않아요. 응답을 한 번에 직렬화해서 반환하는 방식이기 때문이에요.
> - Claude API의 스트리밍은 `ReadableStream`을 쓰는데, 서버 액션은 이 스트림을 클라이언트로 그대로 넘기지 못해요.
> - Route Handler(`/api` 경로)는 스트리밍을 직접 지원하고, App Router와 함께 써도 충돌이 없어요.
> - Vercel AI SDK의 `streamText`를 쓰면 서버 액션에서도 스트리밍 흉내를 낼 수 있지만, 진짜 토큰 단위 스트리밍은 아니에요.
> - 2026년 기준 가장 안정적인 방법은 Route Handler + `ReadableStream` 조합이에요.

---

## 왜 서버 액션에서 스트리밍이 끊기나요?

서버 액션은 HTTP POST 요청으로 실행되고, React의 직렬화 레이어를 통해 결과를 반환해요. 쉽게 말하면, 함수 실행이 끝난 후 결과를 한 번에 묶어서 보내는 구조예요. `ReadableStream` 객체를 반환해도 클라이언트 입장에서는 이미 버퍼링된 덩어리로 받게 돼요.

Claude API는 다르게 작동해요. `anthropic.messages.stream()`을 호출하면 서버에서 토큰이 생성될 때마다 즉시 청크를 보내요. SSE(Server-Sent Events) 방식이에요. 서버 액션이 이 스트림을 잡아서 클라이언트로 넘기려 하면, React 직렬화 레이어가 스트림을 닫아버리거나 끊어버려요.

결과는 세 가지 중 하나예요.

- 응답이 완전히 끝난 후 한 번에 툭 튀어나오거나
- 첫 청크만 오고 뚝 끊기거나
- 빈 응답이 오거나

설계 철학 자체가 달라요. 서버 액션은 "실행하고 결과 받기"고, Claude 스트리밍은 "계속 흘려보내기"예요. 이 둘을 억지로 붙이면 당연히 충돌이 생기죠.

---

## 세 가지 해결 방법 비교

### Route Handler 방식 (가장 권장)

`/app/api/chat/route.ts` 파일을 만들고 Claude API를 여기서 호출하는 방법이에요.

```typescript
// app/api/chat/route.ts
import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic();

export async function POST(req: Request) {
  const { messages } = await req.json();

  const stream = await client.messages.stream({
    model: "claude-opus-4-5",
    max_tokens: 1024,
    messages,
  });

  return new Response(stream.toReadableStream(), {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
```

클라이언트에서는 `fetch()`로 이 엔드포인트를 호출하고, `response.body`를 `ReadableStream`으로 읽으면 돼요. 토큰이 오는 대로 화면에 뿌려지죠.

### Vercel AI SDK `streamText` 방식

`ai` 패키지의 `streamText`를 쓰면 서버 액션과 비슷한 형태로 스트리밍을 구현할 수 있어요. Vercel AI SDK는 내부적으로 React Server Components와 잘 맞도록 설계돼 있어요.

```typescript
// app/actions.ts
"use server";
import { streamText } from "ai";
import { anthropic } from "@ai-sdk/anthropic";
import { createStreamableValue } from "ai/rsc";

export async function chat(prompt: string) {
  const stream = createStreamableValue("");

  (async () => {
    const { textStream } = await streamText({
      model: anthropic("claude-opus-4-5"),
      prompt,
    });

    for await (const delta of textStream) {
      stream.update(delta);
    }
    stream.done();
  })();

  return { output: stream.value };
}
```

작동은 해요. 그런데 내부적으로 폴링을 사용하기 때문에 진짜 토큰 단위 스트리밍보다 약간 덜 매끄러워요.

### 비교 분석

| 기준 | Route Handler | Vercel AI SDK (서버 액션) | 서버 액션 + 직접 스트림 |
|------|--------------|--------------------------|------------------------|
| 스트리밍 품질 | 토큰 단위, 매끄러움 | 거의 토큰 단위 | ❌ 작동 안 함 |
| 구현 복잡도 | 낮음 | 중간 | 높음 (결국 실패) |
| App Router 호환성 | 완전 지원 | 지원 | 부분적 |
| 의존성 추가 | 없음 | `ai`, `@ai-sdk/anthropic` | 없음 |
| 에러 처리 | 표준 HTTP | SDK 내장 | 불안정 |
| 2026년 권장 여부 | ✅ 강력 권장 | ✅ 권장 | ❌ |

Route Handler는 추가 패키지 없이 Next.js 기본 기능만으로 돌아가요. 서버 액션의 편리함을 포기해야 하지만, 스트리밍 안정성은 압도적이에요. Vercel AI SDK는 서버 액션 형태를 유지하면서 스트리밍을 구현하고 싶을 때 쓰는 대안이에요. 다만 Vercel 생태계에 묶이는 게 단점이에요.

---

## 실제 배포에서 놓치기 쉬운 세 가지

문제를 해결하고 나서도 여기서 막히는 경우가 많아요.

**헤더 설정.** Route Handler에서 `Content-Type: text/event-stream`을 빠뜨리면 브라우저가 스트림을 버퍼링해요. Vercel 앞단에 프록시가 있으면 `X-Accel-Buffering: no` 헤더도 추가해야 해요.

**에러 처리.** 스트리밍 중간에 에러가 나면 클라이언트는 연결이 그냥 끊긴 걸로 봐요. 에러 메시지를 스트림 안에 넣거나, 별도의 에러 청크를 보내서 클라이언트가 상태를 알 수 있게 해야 해요.

**연결 타임아웃.** Claude API가 응답을 시작하기까지 시간이 걸려요. Vercel 기본 타임아웃은 10초라, 긴 프롬프트를 처리하다 보면 연결이 끊기기도 해요. `maxDuration` 옵션으로 늘려줄 수 있어요.

세 가지 중 하나라도 놓치면 로컬에서는 되는데 배포하면 안 되는 상황이 생겨요. 맞죠?

---

## 앞으로 주시해야 할 것들

React 팀이 2026년 하반기에 스트리밍 친화적인 서버 액션 API를 실험 중이에요. GitHub RFC를 보면 `use stream` 지시어 형태로 논의되고 있어요. 아직 확정된 건 아니지만, 이게 들어오면 Route Handler 없이도 깔끔한 스트리밍이 가능해질 거예요.

**핵심 정리:**

- 서버 액션은 스트리밍용이 아니에요. 구조적 한계예요.
- Route Handler가 Claude API 스트리밍을 Next.js 14 App Router에서 쓰는 가장 안정적인 방법이에요.
- Vercel AI SDK는 서버 액션 형태를 유지하고 싶을 때 대안이에요.
- 헤더, 에러 처리, 타임아웃 세 가지는 배포 전 반드시 확인하세요.

지금 당장 이 문제를 겪고 있다면 Route Handler로 이전하는 게 가장 빠른 길이에요. 코드 한 파일 추가하는 수준이니까요.

구현하다가 막히는 부분이 있으면 댓글로 남겨주세요. 어떤 설정에서 끊기는지 환경 정보랑 함께 주시면 더 정확하게 답드릴 수 있어요.

## 참고자료

1. [문제 해결 - Claude Code Docs](https://code.claude.com/docs/ko/troubleshooting)
2. [nextjs-developer • claude-skills • jeffallan • Skills • Registry • Tessl](https://tessl.io/registry/skills/github/jeffallan/claude-skills/nextjs-developer)
3. [Routing: API Routes | Next.js](https://nextjs.org/docs/pages/building-your-application/routing/api-routes)


---

*Photo by [Bernd 📷 Dittrich](https://unsplash.com/@hdbernd) on [Unsplash](https://unsplash.com/photos/computer-screen-displaying-code-and-text-XIpm0bnYOQE)*
