---
title: "Vercel 무료 플랜 함수 실행 시간 10초 초과 OpenAI API 타임아웃, Edge Runtime 우회 전략 정리"
date: 2026-03-17T20:12:07+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-ai", "vercel", "10\ucd08", "openai", "TypeScript"]
description: "Vercel Hobby 플랜 10초 제한으로 OpenAI GPT-4o 호출 시 504 타임아웃 발생 시 Edge Runtime과 ReadableStream 스트리밍을 조합하면 무료 플랜에서도 25초 이상 응답을 처리할 수 있습니다."
image: "/images/20260317-vercel-무료-플랜-함수-실행-시간-10초-초과-o.webp"
technologies: ["TypeScript", "Next.js", "Node.js", "GPT", "OpenAI"]
faq:
  - question: "Vercel 무료 플랜 함수 실행 시간 10초 초과 OpenAI API 타임아웃 어떻게 해결하나요"
    answer: "Vercel 무료 플랜 함수 실행 시간 10초 초과 OpenAI API 타임아웃 문제는 Edge Runtime과 ReadableStream 조합으로 우회할 수 있습니다. route.ts 파일에 'export const runtime = edge'를 선언하면 실행 시간 제한 없이 스트림이 닫힐 때까지 연결이 유지됩니다. OpenAI SDK 대신 fetch를 직접 사용해 응답 스트림을 클라이언트에 그대로 통과시키는 방식이 핵심입니다."
  - question: "Vercel Hobby 플랜 serverless function 10초 제한 스트리밍 켜도 타임아웃 나는 이유"
    answer: "Vercel Serverless Function은 스트리밍 설정과 무관하게 응답을 버퍼에 모아 한 번에 반환하는 구조라, stream: true를 설정해도 10초 제한이 그대로 적용됩니다. 즉, OpenAI에서 청크 단위로 데이터가 오더라도 함수 자체가 10초를 초과하면 504 오류가 발생합니다. 이 문제를 해결하려면 Serverless Function 대신 Edge Runtime으로 전환해야 합니다."
  - question: "Next.js Edge Runtime OpenAI 스트리밍 연동 코드 예시"
    answer: "Next.js app/api/chat/route.ts에서 'export const runtime = edge'를 선언하고, fetch로 OpenAI API를 stream: true 옵션과 함께 호출한 뒤 response.body를 그대로 new Response로 반환하면 됩니다. 이 구조에서는 Edge Runtime이 스트림이 흐르는 동안 연결을 유지하므로 실행 시간 제한에 걸리지 않습니다. openai npm 패키지 일부 기능이 Edge에서 제한될 수 있으므로 SDK 대신 fetch를 직접 사용하는 것이 권장됩니다."
  - question: "Vercel 무료 플랜 AI 기능 한계 Render 프록시로 우회 가능한가요"
    answer: "Render 무료 플랜의 Web Service는 실행 시간 제한이 없어 Vercel 무료 플랜 함수 실행 시간 10초 초과 OpenAI API 타임아웃 Edge Runtime 우회 전략의 대안으로 활용할 수 있습니다. Vercel 앱에서 Render 서버로 요청을 보내고 Render가 OpenAI를 호출하는 프록시 구조로 Vercel 제약을 완전히 우회합니다. 단, Render 무료 인스턴스는 15분 비활동 후 슬립 상태로 전환되어 콜드 스타트가 최대 50초까지 걸릴 수 있다는 새로운 UX 문제가 생깁니다."
  - question: "Vercel Edge Runtime 단점 Node.js API 사용 제한 어떤 것들이 있나요"
    answer: "Edge Runtime은 V8 Isolate 기반으로 동작해 fs, crypto 일부, 일부 npm 패키지를 사용할 수 없습니다. Vercel 공식 문서에 따르면 fetch, ReadableStream, TextEncoder 등 Web API 표준만 안정적으로 지원됩니다. 따라서 파일 시스템 접근이나 Node.js 전용 모듈이 필요한 기능은 Edge Runtime으로 마이그레이션하기 어렵습니다."
---

Vercel 무료 플랜에 Next.js 앱 올리고 OpenAI 붙였는데 `504 Gateway Timeout` 뜬 적 있죠? 원인은 단순해요. Vercel Hobby 플랜의 함수 실행 시간 한도는 **10초**인데, GPT-4o 같은 무거운 모델은 그 이상 걸리는 경우가 많거든요.

> **핵심 요약**
> - Vercel Hobby 플랜 Serverless Function 실행 시간 한도는 10초, 초과하면 즉시 `504` 반환
> - OpenAI 스트리밍 미사용 시 GPT-4o 응답 생성은 요청 복잡도에 따라 5~25초 범위
> - Edge Runtime은 실행 시간 제한 없는 대신 Node.js 전체 API 미지원
> - 스트리밍(`ReadableStream`) + Edge Runtime 조합이 무료 플랜에서 가장 현실적인 우회법
> - Render 같은 외부 서버 분리는 제약 없지만 아키텍처 복잡도가 높아짐

---

## Vercel 무료 플랜, 뭐가 달라졌나

Vercel은 2024년 말 플랜 구조를 개편하면서 Hobby 플랜 함수 실행 시간 상한을 **10초**로 못 박았어요. Pro는 60초, Enterprise는 무제한이죠. 단순한 숫자 차이가 아니에요. AI API를 끌어다 쓰는 앱이 늘어난 지금, 10초 제한은 "제대로 된 AI 기능을 무료로 쓰지 말라"는 말이나 다름없어요.

Serverless Function은 Node.js 런타임에서 요청당 독립 인스턴스가 뜨는 구조예요. 반면 **Edge Runtime**은 Cloudflare Workers와 유사한 V8 Isolate 기반으로 동작해요. 실행 시간 제한 자체가 없고 콜드 스타트도 거의 없어요. 대신 `fs`, `crypto` 일부, npm 패키지 일부를 쓸 수 없다는 트레이드오프가 있어요.

두 런타임의 설계 철학이 다른 거예요. Serverless Function은 "완료까지 기다려라", Edge Function은 "일단 응답을 흘려보내라". OpenAI의 스트리밍 기능(`stream: true`)과 Edge Runtime을 합치면 이 제약을 자연스럽게 넘길 수 있어요.

---

## 세 가지 우회 방법 심층 분석

### Serverless + 스트리밍만 쓰는 경우의 한계

흔히 쓰는 패턴부터 볼게요. Node.js Serverless Function에서 `stream: true`로 OpenAI를 호출하면 응답이 청크 단위로 오긴 해요. 그런데 Vercel Serverless Function은 **응답을 버퍼에 모아서 한 번에 반환하는 방식**이라, 스트리밍처럼 보여도 10초 제한은 그대로 적용돼요. 결국 스트리밍 설정 여부와 무관하게 함수가 10초를 넘기면 끊겨요.

"스트리밍 켰는데 왜 타임아웃이 나요?"라는 질문이 개발자 커뮤니티에 계속 올라오는 이유가 바로 이거예요.

### Edge Runtime + ReadableStream 조합

Edge Runtime에서 `ReadableStream`을 반환하면 작동 방식이 달라져요. 엣지 함수는 **응답을 시작하는 순간부터 연결을 열어두고 데이터를 청크로 흘려보낼 수 있어요.** 실행 시간 제한이 아니라 스트림이 닫히는 시점에 연결이 끝나는 구조예요.

Next.js 기준 코드 패턴은 아래처럼 돼요:

```typescript
// app/api/chat/route.ts
export const runtime = 'edge';

export async function POST(req: Request) {
  const { messages } = await req.json();
  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'gpt-4o',
      messages,
      stream: true,
    }),
  });
  return new Response(response.body, {
    headers: { 'Content-Type': 'text/event-stream' },
  });
}
```

`export const runtime = 'edge'` 한 줄이 전부예요. OpenAI 응답 스트림을 그대로 클라이언트에 통과시키는 구조라, 함수가 "실행 중"인 시간이 아니라 스트림이 흐르는 동안 연결이 유지돼요.

단, Edge Runtime에서는 `openai` npm 패키지 일부 기능이 제한될 수 있어요. Vercel 공식 문서는 Edge Runtime에서 Web API 표준(`fetch`, `ReadableStream`, `TextEncoder` 등)만 안정적으로 지원된다고 명시해요. `openai` SDK 대신 `fetch`를 직접 쓰는 이유가 여기 있어요.

### 외부 백엔드 분리 (Render 프록시 활용)

세 번째 방법은 OpenAI 호출 자체를 Vercel 밖으로 빼내는 거예요. Render 무료 플랜은 실행 시간 제한 없는 Web Service를 제공해요. 단, 무료 인스턴스는 15분 비활동 시 슬립 상태로 전환돼요. Vercel 앱에서 Render 서버로 요청을 보내고, Render가 OpenAI를 호출해 스트리밍 응답을 반환하는 프록시 구조예요.

Vercel 제약을 완전히 우회하지만, 아키텍처가 복잡해지고 Render 무료 플랜의 콜드 스타트(최대 50초)가 새로운 UX 문제를 만들어요.

### 방법별 비교

| 항목 | Serverless + Stream | Edge + ReadableStream | Render 프록시 |
|------|---------------------|-----------------------|---------------|
| 실행 시간 제한 | 10초 (초과 시 504) | 사실상 없음 | 없음 |
| 구현 난이도 | 낮음 | 중간 | 높음 |
| Node.js API 지원 | 전체 | 제한적 | 전체 |
| 콜드 스타트 | 있음 | 거의 없음 | 있음 (무료 플랜) |
| 비용 | 무료 | 무료 | 무료 (제한 있음) |
| 가장 적합한 경우 | 응답 빠른 API | AI 스트리밍 앱 | 복잡한 서버 로직 |

---

## 상황별로 뭘 선택해야 하나

**시나리오 1 — MVP 빠르게 띄우고 싶은 경우**
Edge + ReadableStream 조합이 답이에요. `fetch` 기반으로 OpenAI 스트리밍을 연결하는 코드는 30줄 이내로 끝나고, Vercel 무료 플랜에서 추가 비용 없이 돌아요. 다만 `openai` SDK 대신 Web API를 직접 다뤄야 하니, SSE 파싱 로직을 손수 짜야 해요.

**시나리오 2 — 서버 사이드 로직이 복잡한 경우**
데이터베이스 쿼리, 파일 처리, npm 패키지 의존성이 많다면 Edge Runtime은 맞지 않아요. Render나 Railway에 Express 서버를 올리고 Vercel은 프론트만 담당하게 분리하는 게 나아요. Render 슬립 문제는 무료 플랜을 쓰는 한 어느 정도 감수해야 해요.

**시나리오 3 — 트래픽이 늘어날 것 같은 경우**
사실 이 경우엔 Vercel Pro(월 $20)로 업그레이드하는 게 제일 빠른 해결책이에요. 실행 시간이 60초로 늘어나고, 대부분의 AI API 호출은 여기서 커버돼요.

---

## 앞으로 주시할 것들

**Vercel AI SDK의 `streamText` 함수**: Vercel이 직접 만든 AI SDK는 Edge Runtime 호환성을 공식 보장하면서 계속 업데이트되고 있어요. 2026년 현재 v3 버전이 안정화 단계인데, 이걸 쓰면 스트리밍 파싱 로직을 직접 짜지 않아도 돼요.

**Cloudflare Workers Free 플랜**: Vercel Edge Runtime과 비슷한 V8 기반이지만, 무료 플랜에서 하루 10만 요청이 가능하고 CPU 시간 제한(10ms/요청)이 별도로 있어요. AI 스트리밍처럼 I/O 대기가 대부분인 작업엔 CPU 한도가 사실상 걸림돌이 안 돼요. Vercel이 너무 빡빡하게 느껴진다면 비교해볼 만해요.

10초 제한은 Vercel이 의도적으로 유료 전환을 유도하는 구조예요. 그런데 Edge Runtime 스트리밍이라는 공식 지원 방법이 있는 만큼, 무료 플랜에서도 AI 기능을 제대로 돌릴 수 있어요. 지금 당장 `export const runtime = 'edge'` 한 줄을 API route에 추가하고 결과를 확인해보세요. 그걸로 해결이 안 된다면, 그때가 아키텍처를 다시 그려야 할 시점이에요.

---

*이 글에서 다룬 Vercel 플랜 스펙은 2026년 3월 기준 Vercel 공식 문서(vercel.com/docs)와 Edge Functions 런타임 문서를 참조했어요. 플랜 정책은 변경될 수 있으니 배포 전 공식 문서를 직접 확인해보세요.*

## 참고자료

1. [Render 을 사용하여 프록시 구현하기](https://j2su0218.tistory.com/1734)
2. [Edge Functions](https://vercel.com/docs/functions/runtimes/edge/edge-functions.rsc)
3. [Vercel을 이용한 무료 웹 배포 이용해보기](https://allinfor.tistory.com/76)


---

*Photo by [Possessed Photography](https://unsplash.com/@possessedphotography) on [Unsplash](https://unsplash.com/photos/robot-playing-piano-U3sOwViXhkY)*
