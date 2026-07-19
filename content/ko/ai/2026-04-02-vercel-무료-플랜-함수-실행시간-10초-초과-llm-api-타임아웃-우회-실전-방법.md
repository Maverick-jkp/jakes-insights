---
title: "Vercel 무료 플랜 10초 타임아웃, LLM API 연동 시 우회하는 실전 방법"
date: 2026-04-02T20:16:07+0900
draft: false
author: "Jake Park"
categories: ["ai"]
tags: ["subtopic-ai", "vercel", "\uc2e4\ud589\uc2dc\uac04", "10\ucd08", "TypeScript"]
description: "Vercel 무료 플랜 10초 함수 제한으로 GPT-4o 응답이 중단된다면? Edge Function 25초 활용, 스트리밍 응답 분할, 외부 큐 우회까지 LLM 타임아웃을 실제로 해결한 방법을 정리했습니"
image: "/images/20260402-vercel-무료-플랜-함수-실행시간-10초-초과-ll.webp"
technologies: ["TypeScript", "React", "Node.js", "FastAPI", "GPT"]
faq:
  - question: "Vercel 무료 플랜 함수 실행시간 10초 초과 LLM API 타임아웃 우회 실전 방법"
    answer: "Vercel Hobby 플랜에서 LLM API 타임아웃을 우회하는 가장 실용적인 방법은 Edge Function과 SSE 기반 스트리밍을 조합하는 것입니다. `export const runtime = 'edge'` 한 줄 선언 후 Vercel AI SDK의 `streamText`를 사용하면 25초 한도 내에서 토큰을 실시간으로 전달해 체감 타임아웃을 사실상 없앨 수 있습니다. 응답이 25초를 초과하는 경우에는 Render 같은 외부 서비스에 프록시 서버를 별도로 두는 구조적 대안을 고려해야 합니다."
  - question: "Vercel 무료 플랜 serverless function 10초 제한 늘리는 방법"
    answer: "Vercel Hobby 플랜의 Serverless Function 실행시간 한도는 10초로 고정되어 있으며, 이를 직접 늘리려면 월 $20의 Pro 플랜으로 업그레이드해 300초까지 확장해야 합니다. 비용 없이 우회하려면 `/api` 라우트를 Edge Function으로 전환하면 Hobby 플랜에서도 25초 한도를 사용할 수 있습니다. 단, Edge Function은 V8 런타임 기반이라 일부 Node.js API를 사용할 수 없다는 점을 고려해야 합니다."
  - question: "Vercel AI SDK streamText Edge Runtime 사용 방법"
    answer: "Vercel AI SDK의 `streamText`는 Edge Runtime에서 바로 동작하며, 라우트 파일 상단에 `export const runtime = 'edge'`를 선언한 뒤 `streamText`와 `toDataStreamResponse()`를 조합하면 단 5줄 내외의 코드로 스트리밍 응답 구조를 완성할 수 있습니다. 내부적으로 SSE(Server-Sent Events) 방식으로 토큰을 실시간 전달하며, 프론트엔드에서는 `useChat` 훅 하나로 연결을 유지할 수 있습니다. 스트리밍 중인 함수는 Vercel이 타임아웃으로 처리하지 않기 때문에, GPT 첫 토큰이 500ms 안에 도달하면 25초 제한 내에서 사실상 끊김 없이 응답을 받을 수 있습니다."
  - question: "ChatGPT API Vercel 배포 502 에러 타임아웃 해결"
    answer: "Vercel에서 OpenAI API를 `await fetch()`로 호출할 때 응답이 10초를 초과하면 함수가 강제 종료되며 502 에러가 발생합니다. GPT-4o 응답은 보통 15~25초, 긴 문서 요약은 40초 이상 걸리는 경우도 있어 Hobby 플랜 Serverless Function에서는 이 문제가 빈번하게 나타납니다. 해결책은 해당 라우트를 Edge Function으로 전환하고 스트리밍 방식으로 응답을 처리하는 것이며, Vercel 무료 플랜 함수 실행시간 10초 초과 LLM API 타임아웃 우회 실전 방법을 다룬 가이드에서 구체적인 코드 패턴을 확인할 수 있습니다."
  - question: "Render 무료 플랜 LLM 프록시 서버 Vercel 연동 콜드스타트 문제"
    answer: "Render 무료 Web Service는 기본 실행시간 제한이 없어 Vercel 25초 한도를 초과하는 LLM 배치 작업이나 멀티스텝 체인 처리에 적합한 외부 프록시 대안입니다. 다만 15분 비활성 상태 이후 컨테이너가 슬립에 빠지며, 첫 요청 시 콜드 스타트로 30~50초의 지연이 발생할 수 있습니다. 저트래픽 환경에서는 이 콜드 스타트 지연을 사전에 인지하고 UX 처리를 별도로 고려해야 합니다."
aliases:
  - "/tech/2026-04-02-vercel-무료-플랜-함수-실행시간-10초-초과-llm-api-타임아웃-우회-실전-방법/"
  - "/ko/tech/2026-04-02-vercel-무료-플랜-함수-실행시간-10초-초과-llm-api-타임아웃-우회-실전-방법/"

---

ChatGPT API를 Vercel에 붙였더니 함수가 10초 만에 죽어버렸어요. GPT-4o 응답 하나 받는 데 보통 15~25초, 긴 문서 요약은 40초도 넘는데 말이죠. Vercel 무료 플랜의 10초 벽은 LLM을 서버리스로 돌리려는 개발자들에게 가장 먼저 마주치는 장벽이에요.

사이드 프로젝트 규모의 AI 앱을 Vercel 무료 플랜 위에서 굴리려는 시도가 요즘 폭발적으로 늘었어요. Vercel 공식 문서 기준으로, Hobby 플랜의 Serverless Function 최대 실행시간은 **10초**, Edge Function은 **25초**로 고정돼 있어요. Pro 플랜으로 올리면 300초까지 늘어나지만, 월 $20 비용이 발생하죠. LLM API를 쓰는 프로젝트 입장에서 이 제약은 꽤 현실적인 고통이에요.

이 글에서 다룰 것들:

- Vercel 타임아웃 구조를 정확히 이해하는 법
- Edge Function + Streaming으로 우회하는 핵심 패턴
- 외부 프록시(Render 등)를 쓰는 구조적 대안
- 각 방법의 트레이드오프 비교

---

> **핵심 요약**
> - Vercel Hobby 플랜 Serverless Function은 10초, Edge Function은 25초 제한이 있으며, LLM API 응답 대기시간이 이를 초과하는 경우가 빈번하다.
> - SSE(Server-Sent Events) 기반 스트리밍을 적용하면 Edge Function 25초 한도 안에서 토큰을 실시간으로 전달해 체감 타임아웃을 사실상 없앨 수 있다.
> - Vercel AI SDK의 `streamText` API는 Edge Runtime에서 바로 동작하며, 설정 5줄로 스트리밍 응답 구조를 만들 수 있다.
> - 응답이 25초를 초과하거나 배치 처리가 필요한 경우, Render 무료 티어에 별도 프록시 서버를 두는 방식이 실질적 대안이다.

---

## Vercel 타임아웃 구조: 10초 벽의 정확한 위치

Vercel에는 함수 유형이 두 가지예요. Serverless Function과 Edge Function이에요.

`/api` 경로에 `.js`, `.ts` 파일을 놓으면 기본으로 Serverless Function으로 배포돼요. Hobby 플랜에서 최대 실행시간은 **10초**예요. OpenAI API를 `await fetch(...)`로 호출하면 응답 자체가 10초를 넘기는 순간 그냥 잘려요. 502 에러 하나 달랑 뜨고요.

Edge Function은 달라요. V8 런타임 기반이라 Node.js 일부 API를 못 쓰지만, Hobby 플랜에서도 최대 실행시간이 **25초**예요. 그리고 결정적으로, **스트리밍 응답을 지원해요.**

스트리밍의 핵심은 이거예요. 함수가 살아있는 동안 데이터를 조금씩 계속 내보내면, 브라우저 입장에서는 연결이 유지된 채로 토큰을 받는 거예요. GPT가 첫 토큰을 500ms 안에 돌려주기 시작하면 함수는 타임아웃 없이 계속 흘러요. 25초 제한이 있긴 하지만, 스트리밍 중에는 "응답 없음" 상태가 아니거든요.

---

## 핵심 우회 패턴: Edge + Streaming 실전 적용

### Edge Runtime 선언과 스트리밍 핸들러 구성

`/app/api/chat/route.ts` 파일 상단에 딱 한 줄 추가해요.

```typescript
export const runtime = 'edge';
```

이걸 선언하면 Vercel이 이 라우트를 Edge Function으로 배포해요. 그다음 Vercel AI SDK의 `streamText`를 쓰면 돼요.

```typescript
import { streamText } from 'ai';
import { openai } from '@ai-sdk/openai';

export const runtime = 'edge';

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = await streamText({
    model: openai('gpt-4o'),
    messages,
  });

  return result.toDataStreamResponse();
}
```

Vercel AI SDK 공식 문서 기준으로, `streamText`는 내부적으로 SSE(Server-Sent Events) 방식으로 응답을 흘려보내요. `toDataStreamResponse()`가 연결을 유지하면서 토큰이 올 때마다 클라이언트에 밀어주는 구조예요.

### 클라이언트 사이드 연결 유지

프론트에서는 `useChat` 훅 하나면 돼요.

```typescript
import { useChat } from 'ai/react';

export default function Chat() {
  const { messages, input, handleInputChange, handleSubmit } = useChat();
  // ...
}
```

이 패턴의 장점은 타임아웃을 "늘리는" 게 아니라 "측정 방식을 바꾸는" 거예요. 스트리밍 중인 함수는 응답을 내보내고 있는 상태라 Vercel이 타임아웃으로 처리하지 않아요.

---

## 25초도 부족할 때: 외부 프록시 구조

LLM으로 긴 문서를 요약하거나, 멀티스텝 체인을 돌리거나, 배치 작업을 하면 25초도 짧아요. 이 경우엔 Vercel 바깥으로 연산을 빼는 게 맞아요.

Render의 무료 Web Service는 기본 타임아웃이 없어요. Express나 FastAPI로 프록시 서버를 만들어서, Vercel 프론트가 그쪽으로 요청을 넘기는 구조예요. Vercel은 UI와 라우팅만 담당하고, 실제 LLM 호출은 Render 서버가 처리하는 거죠.

다만 Render 무료 티어는 15분 비활성 상태면 컨테이너가 슬립 상태로 빠져요. 첫 요청에 콜드 스타트가 30~50초 걸릴 수 있어요. 배포 직후나 저트래픽 시간대에 첫 요청이 느릴 수 있다는 점은 감안해야 해요.

---

## 방법별 트레이드오프 비교

| 기준 | Serverless Function (기본) | Edge Function + Streaming | Render 프록시 |
|------|---------------------------|--------------------------|--------------|
| 최대 실행시간 | 10초 | 25초 (스트리밍 시 실질적 연장) | 제한 없음 |
| 설정 복잡도 | 낮음 | 낮음 (SDK 지원) | 중간 |
| Node.js API 지원 | 전체 | 제한적 (V8 런타임) | 전체 |
| 스트리밍 지원 | 제한적 | 네이티브 지원 | 직접 구현 |
| 비용 (Vercel 기준) | 무료 | 무료 | 무료 (Render 별도) |
| 콜드 스타트 | 없음 | 없음 | 15분 비활성 시 30~50초 |
| **추천 용도** | 짧은 API 호출 | LLM 스트리밍 | 장시간 배치/복잡한 체인 |

Edge Function + Streaming이 대부분의 사이드 프로젝트에 맞는 선택지예요. 설정이 간단하고, Vercel AI SDK가 복잡한 부분을 처리해주거든요. Render 프록시는 스트리밍으로도 감당 안 되는 작업에 쓰는 플랜 B예요.

---

## 실제 적용 시나리오별 권장 흐름

**시나리오 A — 채팅 앱, 짧은 Q&A 응답:**
Edge Function + `streamText` 조합으로 충분해요. 설정 10분이면 동작해요. 타임아웃 문제를 가장 빠르게 우회하는 경로예요.

**시나리오 B — PDF 요약, 긴 문서 처리:**
입력 문서를 청크(chunk)로 나눠서 여러 번 Edge Function 호출로 처리하거나, Render 프록시로 넘기는 방식을 써요. 단일 함수 호출 하나에 전체 문서를 밀어넣는 구조는 타임아웃을 피하기 어려워요.

**시나리오 C — 멀티스텝 에이전트, 툴 호출 체인:**
이건 Vercel 위에서 무료로 돌리기 어려운 케이스예요. Render나 Railway의 유료 티어, 혹은 백그라운드 잡 서비스(Inngest, Trigger.dev 등)를 쓰는 게 현실적이에요.

---

## 정리

- **Edge Function + Streaming**은 Vercel 무료 플랜에서 LLM API 타임아웃 우회의 가장 실용적인 방법이에요.
- **Vercel AI SDK**의 `streamText` + `runtime: 'edge'` 조합은 설정 최소화 + 즉시 동작이에요.
- 25초 초과 작업은 구조적으로 분리하거나 Render 프록시로 넘기는 게 맞아요.
- 무료 플랜 내에서 해결이 안 된다면, 작업 단위를 나누는 게 비용을 쓰는 것보다 먼저예요.

참고로 Vercel 팀은 2026년 초 블로그에서 Edge Middleware의 스트리밍 개선을 언급했어요. 향후 Hobby 플랜에서 스트리밍 제한이 더 완화될 가능성도 있어요. 지금은 Edge + Streaming이 정답에 가장 가까운 조합이에요.

지금 만들고 있는 LLM 앱에서 단일 요청당 평균 응답시간이 얼마나 되나요? 그 숫자가 어떤 구조를 선택할지를 결정해요.

## 참고자료

1. [Vercel을 이용한 무료 웹 배포 이용해보기 - 코딩은재밌어](https://allinfor.tistory.com/76)
2. [Render 을 사용하여 프록시 구현하기](https://j2su0218.tistory.com/1734)
3. [Vercel AI SDK 사용법: 초보자 가이드](https://apidog.com/kr/blog/vercel-ai-sdk-kr/)


---

*Photo by [Luca Bravo](https://unsplash.com/@lucabravo) on [Unsplash](https://unsplash.com/photos/turned-on-gray-laptop-computer-XJXWbfSo2f0)*
