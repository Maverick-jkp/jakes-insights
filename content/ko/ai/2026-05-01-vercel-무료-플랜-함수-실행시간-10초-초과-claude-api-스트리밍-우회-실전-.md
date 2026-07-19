---
title: "Vercel 무료 플랜 함수 실행시간 10초 초과, Claude API 스트리밍 우회 실전 코드"
date: 2026-05-01T20:20:53+0900
draft: false
author: "Jake Park"
categories: ["ai"]
tags: ["subtopic-ai", "vercel", "\uc2e4\ud589\uc2dc\uac04", "10\ucd08", "TypeScript"]
description: "Vercel Hobby 플랜 10초 타임아웃으로 Claude API 15~40초 응답이 504를 유발합니다. Edge Runtime 스트리밍으로 제한을 우회하는 실전 코드와 Node.js 호환성 문제 해결법을 다룹니다."
image: "/images/20260501-vercel-무료-플랜-함수-실행시간-10초-초과-cl.webp"
technologies: ["TypeScript", "React", "Next.js", "Node.js", "Claude"]
faq:
  - question: "Vercel 무료 플랜 함수 실행시간 10초 초과 Claude API 스트리밍 우회 실전 코드 어떻게 작성하나요?"
    answer: "Vercel 무료 플랜 함수 실행시간 10초 초과 Claude API 스트리밍 우회 실전 코드는 Next.js App Router에서 `client.messages.stream()`과 `ReadableStream`을 조합해 SSE 방식으로 응답을 조각 전송하는 구조입니다. 전체 응답 완료 후 리턴하는 블로킹 방식 대신, 토큰이 생성되는 즉시 클라이언트로 흘려보내면 Vercel이 연결을 '응답 중' 상태로 인식해 10초 타임아웃이 적용되지 않습니다."
  - question: "Vercel Hobby 플랜 Claude API 타임아웃 504 에러 해결 방법"
    answer: "Vercel Hobby 플랜은 Serverless Function 최대 실행시간이 10초로, Claude API의 평균 응답 지연인 15~40초를 감당하지 못해 504 에러가 발생합니다. SSE(Server-Sent Events) 스트리밍 방식으로 응답을 조각 전송하거나, 파일 상단에 `export const runtime = 'edge'`를 추가해 Edge Runtime을 사용하면 이 문제를 우회할 수 있습니다."
  - question: "Next.js App Router에서 Claude API 스트리밍 구현하는 방법"
    answer: "Next.js 13+ App Router에서 Claude API 스트리밍은 `@anthropic-ai/sdk`의 `client.messages.stream()` 메서드와 `ReadableStream`을 함께 사용해 구현합니다. API Route에서 `Content-Type: text/event-stream` 헤더를 설정하고 `for await` 루프로 토큰을 순차 전송하면, 클라이언트가 실시간으로 텍스트를 받아볼 수 있습니다."
  - question: "Vercel Edge Runtime vs Serverless Function 차이점 AI 호출할 때"
    answer: "Vercel Serverless Function은 실행시간이 무료 플랜 기준 10초로 제한되지만, Edge Runtime은 타임아웃 제한이 없어 Claude 같은 LLM 호출에 적합합니다. 다만 Edge Runtime은 메모리 상한이 128MB이고 `fs`, `path` 같은 Node.js 전용 모듈을 사용할 수 없다는 제약이 있으므로, 파일 입출력이 필요 없는 순수 API 호출 용도라면 Edge Runtime이 유리합니다."
  - question: "Vercel 무료 플랜 함수 실행시간 10초 초과 Claude API 스트리밍 우회 실전 코드에서 SSE 헤더 설정 왜 필요한가요?"
    answer: "Vercel 무료 플랜 함수 실행시간 10초 초과 Claude API 스트리밍 우회 실전 코드에서 `Content-Type: text/event-stream`과 `Cache-Control: no-cache`, `Connection: keep-alive` 헤더는 브라우저와 서버 간 SSE 연결을 유지하는 데 필수입니다. 이 헤더가 없으면 중간 프록시나 브라우저가 응답을 버퍼링해 스트리밍 효과가 사라지고, 결국 전체 응답 완료까지 기다리는 블로킹 방식과 동일하게 동작해 타임아웃 문제가 재발합니다."
aliases:
  - "/tech/2026-05-01-vercel-무료-플랜-함수-실행시간-10초-초과-claude-api-스트리밍-우회-실전-/"
  - "/ko/tech/2026-05-01-vercel-무료-플랜-함수-실행시간-10초-초과-claude-api-스트리밍-우회-실전-/"

---

Serverless 함수가 10초 안에 응답을 못 내면 Vercel Hobby 플랜은 바로 504를 뱉어요. Claude API 같은 LLM 호출은 평균 응답 시간이 15~40초 사이거든요. 그러니까 Vercel 무료 플랜에 Claude를 붙이는 순간, 이 조합은 기본적으로 타임아웃 머신이 되는 거예요. 근데 스트리밍으로 이걸 우회하는 방식이 개발자 커뮤니티에서 빠르게 퍼지고 있어요. 코드 수준에서 뜯어볼게요.

---

> **핵심 요약**
> - Vercel Hobby 플랜의 Serverless Function 최대 실행시간은 10초로, Claude API의 평균 응답 지연(15~40초)을 감당하지 못해요.
> - Edge Runtime을 쓰면 타임아웃 제한이 사라지지만, Node.js API 일부를 못 쓰고 메모리 상한도 128MB로 제한돼요.
> - HTTP 스트리밍(SSE)으로 응답을 조각조각 흘려보내면 Serverless에서도 "연결 유지" 상태로 10초 장벽을 실질적으로 넘을 수 있어요.
> - Anthropic의 `@anthropic-ai/sdk` 공식 패키지는 스트림 방식을 기본 지원하며, 2025년 말 기준 주간 다운로드가 약 180만 회를 기록했어요 (npmjs.com 통계 기준).
> - Edge + 스트리밍 조합이 현재로선 Vercel 무료 플랜에서 Claude를 돌리는 가장 현실적인 방법이에요.

---

## 10초가 이렇게 큰 문제인 이유

Vercel이 Hobby 플랜에 10초 제한을 건 건 2023년부터예요. 원래는 60초였는데, 무료 사용자들이 LLM 호출로 서버를 오래 붙잡아두는 패턴이 늘어나자 제한을 대폭 줄였죠. Pro 플랜은 300초까지 허용하는데, 여기서 무료와 유료의 격차가 확 벌어져요.

문제는 Claude API 자체가 느린 게 아니에요. 첫 토큰이 나오는 데는 보통 1~3초밖에 안 걸려요. 그런데 Serverless Function이 "전체 응답 완료 후 리턴"하는 방식으로 작성되면, 마지막 토큰까지 기다리다가 10초를 넘겨버리는 거예요.

Vercel 공식 블로그 기준, 2025년 한 해 동안 AI 관련 템플릿 배포 수가 전년 대비 세 배 가까이 늘었어요. 그만큼 이 타임아웃 문제에 부딪히는 사람도 많아진 거죠.

핵심은 단순해요. 응답을 한 방에 쏘지 말고, 스트림으로 조금씩 흘려보내면 돼요. 연결이 살아 있으면 Vercel은 타임아웃을 안 걸거든요.

---

## 스트리밍 우회의 기술적 구조

### SSE(Server-Sent Events)가 핵심

HTTP 스트리밍에서 가장 많이 쓰는 방식이 SSE예요. 서버가 클라이언트에 단방향으로 데이터를 흘려보내는 표준 방식이고, 별도 WebSocket 없이도 작동해요.

Vercel Serverless에서 SSE를 쓰려면 `Response` 객체에 `ReadableStream`을 직접 넣어야 해요. Next.js 13+ App Router 기준으로 이렇게 생겼어요.

```typescript
// app/api/chat/route.ts
import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic();

export async function POST(req: Request) {
  const { message } = await req.json();

  const stream = await client.messages.stream({
    model: "claude-opus-4-5",
    max_tokens: 1024,
    messages: [{ role: "user", content: message }],
  });

  const readableStream = new ReadableStream({
    async start(controller) {
      for await (const chunk of stream) {
        if (
          chunk.type === "content_block_delta" &&
          chunk.delta.type === "text_delta"
        ) {
          const data = `data: ${JSON.stringify({ text: chunk.delta.text })}\n\n`;
          controller.enqueue(new TextEncoder().encode(data));
        }
      }
      controller.enqueue(new TextEncoder().encode("data: [DONE]\n\n"));
      controller.close();
    },
  });

  return new Response(readableStream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
```

이 코드의 핵심은 `client.messages.stream()`이에요. 블로킹 방식의 `client.messages.create()`와 달리, 토큰이 생성되는 즉시 `for await` 루프가 돌면서 클라이언트로 데이터를 내보내요. 연결이 끊기지 않으니까 Vercel 입장에서 "아직 응답 중"으로 인식하는 거죠.

### Edge Runtime으로 한 단계 더

Serverless보다 더 깔끔한 방법은 Edge Runtime이에요. 파일 상단에 한 줄만 추가하면 돼요.

```typescript
export const runtime = "edge";
```

Edge Runtime은 타임아웃 제한이 없어요. 대신 `fs`, `path` 같은 Node.js 전용 모듈을 못 쓰고, 메모리도 128MB로 빡빡해요. Claude API 호출 자체는 네트워크 I/O라서 메모리 제한에 걸리진 않지만, 응답 텍스트를 전부 메모리에 올리는 방식은 조심해야 해요.

### 클라이언트 사이드 처리

서버가 SSE를 보내는 것만큼 클라이언트가 잘 받는 것도 중요해요.

```typescript
// React 클라이언트
async function streamChat(message: string) {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split("\n").filter((line) => line.startsWith("data:"));

    for (const line of lines) {
      const data = line.replace("data: ", "");
      if (data === "[DONE]") return;

      const parsed = JSON.parse(data);
      // setState로 텍스트 누적
      setText((prev) => prev + parsed.text);
    }
  }
}
```

---

## 방식별 비교: 뭘 골라야 하나

| 항목 | Serverless + 스트리밍 | Edge + 스트리밍 | Serverless 블로킹 |
|------|----------------------|-----------------|-------------------|
| 타임아웃 제한 | 10초 (연결 유지로 우회) | 없음 | 10초 (초과 시 504) |
| Node.js 모듈 지원 | 전체 | 제한적 | 전체 |
| 메모리 상한 | 1GB | 128MB | 1GB |
| Cold Start | 500ms~1s | 50ms 이하 | 500ms~1s |
| 무료 플랜 적합성 | ✅ 우회 가능 | ✅ 가장 안정적 | ❌ LLM 호출 불가 |
| 코드 복잡도 | 보통 | 낮음 | 매우 낮음 |

Vercel 공식 문서(vercel.com/docs) 기준으로, Edge Function의 콜드 스타트는 Serverless보다 열 배 가까이 빨라요. 단순 Claude API 스트리밍 용도라면 Edge가 명확히 유리해요.

트레이드오프를 정리하면 이래요. Serverless는 기존 코드베이스에 붙이기 쉽고 Node.js 생태계를 그대로 쓸 수 있어요. Edge는 성능이 더 좋지만 의존성을 줄여야 하죠. 둘 다 스트리밍 없이는 Hobby 플랜에서 Claude 호출이 사실상 불가능해요.

---

## 실제로 배포할 때 주의할 점

**환경 변수 설정부터 확인하세요.** `ANTHROPIC_API_KEY`를 Vercel 대시보드 > Settings > Environment Variables에 넣어야 해요. Edge Runtime은 `process.env`를 그냥 읽어요. 로컬에서 `.env.local`로 테스트하고 올리면 돼요.

시나리오별로 권장 방식이 달라져요.

- **챗봇, 텍스트 생성**: Edge + 스트리밍. 코드 단순하고 성능 가장 좋아요.
- **파일 업로드 처리 + Claude 분석**: Serverless + 스트리밍. `multer` 같은 Node.js 의존성이 필요할 수 있거든요.
- **데이터베이스 조회 후 LLM 호출**: Prisma는 Edge에서 제한적이에요. Serverless 스트리밍이 현실적이에요.

앞으로 6~12개월을 봤을 때, Vercel이 Hobby 플랜의 Edge 제한을 더 손볼 가능성이 높아요. 이미 2025년 말에 Edge Middleware 실행시간을 조용히 늘렸고, AI 워크로드용 별도 플랜을 준비 중이라는 얘기가 커뮤니티에서 나오고 있어요. Anthropic 쪽에서도 스트리밍 API 안정성을 계속 개선하고 있어서, `@anthropic-ai/sdk` 버전은 3개월마다 한 번씩은 체크해두는 게 좋아요.

---

## 결론: 10초는 벽이 아니에요

정리하면 이래요.

- **블로킹 방식은 쓰지 마세요.** Vercel 무료 플랜에서 Claude API를 쓰려면 스트리밍이 필수예요.
- **Edge + 스트리밍이 가장 깔끔해요.** `export const runtime = "edge"` 한 줄로 타임아웃 문제를 근본적으로 없앨 수 있어요.
- **Node.js 의존성이 필요하면 Serverless + SSE로 가세요.** 연결이 살아 있는 한 10초 제한은 실질적으로 작동하지 않아요.

코드를 넣고 나서 실제로 504가 사라지는 순간이 꽤 인상적이에요. 다음으로 해볼 만한 건 스트리밍 응답에 `abort` 처리를 추가하는 거예요. 사용자가 중간에 취소할 때 API 호출 비용이 계속 나가는 걸 막으려면, `AbortController`를 어떻게 연결하는지도 알아두면 좋거든요.

## 참고자료

1. [Vercel 무료 배포 실전 가이드 2026 — Hobby 플랜으로 사이드 프로젝트 운영하기 | DevFinance](https://www.devfinance.cloud/tech/vercel-free-deploy)
2. [Claude Code 무료 플랜 활용 가이드 (Ollama, free-claude-code) :: devopslog](https://devopslog.tistory.com/223)
3. [Min-inter](https://min-inter.co.kr/wiki/vercel-vibe-coding-deploy-platform-guide)


---

*Photo by [Microsoft Copilot](https://unsplash.com/@microsoftcopilot) on [Unsplash](https://unsplash.com/photos/two-women-talking-in-a-kitchen-while-cooking-3c_k7h8YgHw)*
