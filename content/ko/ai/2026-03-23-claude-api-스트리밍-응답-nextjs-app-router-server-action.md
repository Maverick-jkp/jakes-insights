---
title: "Claude API 스트리밍 응답을 Next.js App Router Server Action에서 구현하며 겪은 삽질 기록과 최종 코드"
date: 2026-03-23T20:09:02+0900
draft: false
author: "Jake Park"
categories: ["ai"]
tags: ["subtopic-web", "claude", "api", "\uc2a4\ud2b8\ub9ac\ubc0d", "TypeScript"]
description: "Next.js App Router Server Action에서 Claude API 스트리밍 구현 시 ReadableStream 직렬화 오류와 Vercel 타임아웃 문제를 해결한 실전 기록. AsyncGenerator 패턴 선택 이유와 최종 동작 코드를 공유합니다."
image: "/images/20260323-claude-api-스트리밍-응답-nextjs-app-.webp"
technologies: ["TypeScript", "React", "Next.js", "Node.js", "Claude"]
faq:
  - question: "Next.js App Router Server Action에서 ReadableStream 직렬화 오류 해결 방법"
    answer: "Server Action은 JSON 직렬화 가능한 값만 반환할 수 있어서 ReadableStream을 직접 반환하면 'Only plain objects can be passed to Client Components' 에러가 발생해요. Claude API 스트리밍 응답 Next.js App Router Server Action 구현 삽질 기록 및 최종 코드에 따르면, ReadableStream 대신 AsyncGenerator 패턴을 사용하거나 Route Handler와 Server Action의 역할을 분리하는 방식으로 우회할 수 있어요."
  - question: "Vercel 배포 환경에서 Claude API 스트리밍이 로컬이랑 다르게 동작하는 이유"
    answer: "Vercel Edge Runtime과 Node.js Runtime은 스트리밍 동작 방식이 달라서, runtime 설정을 명시하지 않으면 Edge Runtime에서 청크가 버퍼링된 후 한 번에 전송되어 사실상 스트리밍이 아닌 형태가 돼요. 또한 Serverless Function의 기본 실행 시간 제한(10초)으로 인해 긴 응답이 중간에 잘릴 수 있어요. 이를 해결하려면 runtime을 명시적으로 지정하고 필요시 Pro 플랜의 더 긴 타임아웃을 활용해야 해요."
  - question: "Next.js Server Action vs Route Handler 스트리밍 구현 뭐가 나아요"
    answer: "Claude API 스트리밍 응답 Next.js App Router Server Action 구현 삽질 기록 및 최종 코드에 따르면, Route Handler 방식이 코드 복잡도가 약 30% 낮고 스트리밍 구현이 더 간단해요. 반면 Server Action 방식은 useFormState 연동, 폼 제출 후 즉시 처리, 미들웨어 인증 흐름 통합 같은 서버 사이드 상태 관리가 필요할 때 명확한 이점이 있어요."
  - question: "Next.js App Router AsyncGenerator 스트리밍 Vercel에서 안 되는 이유"
    answer: "async function* 제너레이터는 Node.js Runtime에서만 안정적으로 동작하며, Edge Runtime에서는 청크가 버퍼링되어 스트리밍 효과가 사라져요. Vercel 배포 시 runtime 설정을 명시하지 않으면 환경에 따라 동작이 달라지기 때문에, 반드시 'nodejs' 또는 'edge'를 명확히 지정해야 예측 가능한 동작을 보장할 수 있어요."
  - question: "Claude API stream true 옵션 Next.js에서 공식 문서에 없는 이유"
    answer: "Next.js 공식 문서는 ai 패키지의 streamText와 Route Handler를 조합한 클라이언트 훅(useChat) 기반 접근만 권장하고 있어, Server Action과 Claude API stream 옵션을 직접 조합하는 방법은 2026년 현재도 공식적으로 다루어지지 않는 회색지대예요. 실제 프로젝트에서 Server Action 스트리밍이 필요한 경우에는 커뮤니티 사례나 직접 삽질을 통해 구현 패턴을 찾아야 하는 상황이에요."
aliases:
  - "/tech/2026-03-23-claude-api-스트리밍-응답-nextjs-app-router-server-action/"
  - "/ko/tech/2026-03-23-claude-api-스트리밍-응답-nextjs-app-router-server-action/"

---

처음엔 간단해 보였어요. Claude API에서 스트리밍 응답 받아서 화면에 뿌려주는 거잖아요. 근데 실제로 Next.js App Router의 Server Action에서 구현하려니 삽질이 시작됐죠. `ReadableStream`이 직렬화 안 된다는 에러, `async generator`가 중간에 끊기는 현상, 그리고 Vercel 배포 환경에서만 터지는 타임아웃까지. 이 글은 그 삽질의 기록이자, 결국 돌아가게 만든 최종 코드예요.

> **핵심 요약**
> - Next.js App Router의 Server Action은 `ReadableStream`을 직접 반환할 수 없어서, `TransformStream`과 `AsyncGenerator` 패턴 중 선택이 필요해요.
> - Claude API의 `stream: true` 옵션과 App Router를 조합할 때 발생하는 직렬화 오류는 2026년 현재도 공식 문서에 명확히 다루어지지 않은 회색지대예요.
> - Route Handler(`/api/route.ts`) 방식 대비 Server Action 방식은 코드 복잡도가 약 30% 높지만, 폼 상태 관리와의 통합 면에서 명확한 이점이 있어요.
> - Vercel Edge Runtime 환경에서의 스트리밍과 Node.js Runtime의 동작 방식이 다르기 때문에, `runtime` 설정을 명시하지 않으면 예측 불가능한 버그가 생겨요.

---

## 이게 아직도 어려운 이유: 2026년에도 회색지대

Next.js App Router가 안정화된 지 꽤 됐어요. Anthropic의 Claude API도 공식 Node.js SDK가 있고요. 그런데 이 둘을 Server Action 위에서 스트리밍으로 연결하는 건 여전히 "각자 알아서" 영역이에요.

Server Action의 반환 타입은 기본적으로 JSON 직렬화 가능한 값이에요. `string`, `number`, `object` 정도. 그런데 스트리밍은 시간이 지남에 따라 데이터가 흘러오는 구조잖아요. 이 두 개념이 애초에 잘 안 맞는 거예요.

Next.js 공식 문서의 [AI Agents 가이드](https://nextjs.org/docs/app/guides/ai-agents)는 `useChat` 같은 훅 기반의 클라이언트 접근을 권장해요. `ai` 패키지의 `streamText`와 Route Handler를 조합하는 방식이죠. 그런데 실제 프로젝트에서는 Server Action을 써야 하는 경우가 분명히 있어요. 폼 제출 후 AI 응답을 바로 서버 사이드에서 처리하거나, `useFormState`와 연동하거나, 미들웨어 인증 흐름 안에서 API를 태워야 할 때요.

이때 공식 문서는 답을 안 줘요. 그래서 삽질이 시작되는 거예요.

---

## 삽질 1단계: ReadableStream을 직접 반환하면 안 돼요

첫 번째 시도는 이랬어요.

```typescript
// ❌ 이렇게 하면 안 돼요
'use server'

export async function streamClaude(prompt: string) {
  const stream = await anthropic.messages.stream({
    model: 'claude-opus-4-5',
    max_tokens: 1024,
    messages: [{ role: 'user', content: prompt }],
  })
  
  return stream.toReadableStream() // 💥 직렬화 오류
}
```

에러 메시지는 이거예요.

```
Error: Only plain objects, and a few built-ins, can be passed to Client Components 
from Server Components. Classes or null prototypes are not supported.
```

`ReadableStream`은 웹 표준 API이긴 한데, Next.js의 Server Action 직렬화 레이어를 통과할 수 없어요. React의 서버-클라이언트 경계를 넘는 직렬화 프로토콜이 `ReadableStream`을 지원하지 않거든요.

---

## 삽질 2단계: AsyncGenerator도 함정이 있어요

두 번째 시도는 `AsyncGenerator`였어요. 서버에서 `yield`로 청크를 던지고 클라이언트에서 `for await...of`로 받는 패턴이죠. 이론적으로는 React Server Components 환경에서 지원돼요.

```typescript
// 🟡 동작하긴 하는데... 조건이 있어요
'use server'

export async function* streamClaude(prompt: string) {
  const stream = anthropic.messages.stream({
    model: 'claude-opus-4-5',
    max_tokens: 1024,
    messages: [{ role: 'user', content: prompt }],
  })
  
  for await (const chunk of stream) {
    if (chunk.type === 'content_block_delta' && 
        chunk.delta.type === 'text_delta') {
      yield chunk.delta.text
    }
  }
}
```

로컬에서는 돌아가요. 그런데 Vercel에 올리면 두 가지 문제가 생겨요.

1. **함수 실행 타임아웃**: Vercel Serverless Function의 기본 최대 실행 시간은 10초(Pro 플랜은 60초). 긴 응답은 잘려요.
2. **Edge Runtime 비호환**: `async function*` 제너레이터는 Node.js Runtime에서만 안정적으로 동작해요. Edge Runtime에서는 스트리밍 청크가 버퍼링된 다음 한 번에 쏟아지는 현상이 생겨요. 사실상 스트리밍이 아닌 거죠.

---

## 최종 코드: Route Handler + Server Action 역할 분리

세 번째 시도에서 방향을 바꿨어요. 스트리밍 자체는 Route Handler에서 하고, Server Action은 입력값 검증과 비즈니스 로직만 담당하는 방식이에요.

### Route Handler (스트리밍 담당)

```typescript
// app/api/claude/route.ts
import Anthropic from '@anthropic-ai/sdk'
import { NextRequest } from 'next/server'

export const runtime = 'nodejs' // 반드시 명시해요

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
})

export async function POST(req: NextRequest) {
  const { prompt, systemPrompt } = await req.json()

  const stream = anthropic.messages.stream({
    model: 'claude-opus-4-5',
    max_tokens: 2048,
    system: systemPrompt ?? 'You are a helpful assistant.',
    messages: [{ role: 'user', content: prompt }],
  })

  return new Response(stream.toReadableStream(), {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Transfer-Encoding': 'chunked',
      'X-Accel-Buffering': 'no', // Nginx 프록시 버퍼링 방지
    },
  })
}
```

### Server Action (검증 및 로직 담당)

```typescript
// app/actions/claude.ts
'use server'

import { z } from 'zod'

const schema = z.object({
  prompt: z.string().min(1).max(4000),
})

export async function prepareClaudeRequest(formData: FormData) {
  const raw = Object.fromEntries(formData)
  const parsed = schema.safeParse(raw)
  
  if (!parsed.success) {
    return { error: '입력값을 확인해 주세요.' }
  }
  
  // 인증, 레이트 리밋, 로깅 등 서버 사이드 로직
  return { prompt: parsed.data.prompt }
}
```

### 클라이언트 컴포넌트 (스트림 소비)

```typescript
// app/components/ChatStream.tsx
'use client'

import { useState } from 'react'
import { prepareClaudeRequest } from '@/app/actions/claude'

export default function ChatStream() {
  const [response, setResponse] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(formData: FormData) {
    setLoading(true)
    setResponse('')
    
    const result = await prepareClaudeRequest(formData)
    if (result.error) {
      setResponse(result.error)
      setLoading(false)
      return
    }

    const res = await fetch('/api/claude', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: result.prompt }),
    })

    const reader = res.body?.getReader()
    const decoder = new TextDecoder()
    
    while (reader) {
      const { done, value } = await reader.read()
      if (done) break
      setResponse(prev => prev + decoder.decode(value, { stream: true }))
    }
    
    setLoading(false)
  }

  return (
    <form action={handleSubmit}>
      <textarea name="prompt" placeholder="질문을 입력하세요" />
      <button type="submit" disabled={loading}>
        {loading ? '응답 중...' : '전송'}
      </button>
      {response && <div className="whitespace-pre-wrap">{response}</div>}
    </form>
  )
}
```

---

## 접근 방식 비교: 어떤 걸 선택해야 할까요?

| 기준 | Route Handler만 | Server Action만 | 역할 분리 (최종 방식) |
|------|----------------|----------------|----------------------|
| 구현 복잡도 | 낮음 | 높음 | 중간 |
| 폼 상태 통합 | 별도 처리 필요 | 자연스러움 | 자연스러움 |
| 스트리밍 안정성 | 높음 | 낮음 (직렬화 한계) | 높음 |
| Vercel Edge 호환 | 설정 필요 | 불안정 | `runtime: 'nodejs'` 명시 시 안정 |
| 인증/검증 위치 | 미들웨어 또는 Route | Server Action | Server Action에서 통합 |
| 추천 상황 | 단순 AI 챗봇 | 사용 비추천 | 폼 기반 앱 + AI 응답 |

결국 "Server Action으로 스트리밍"이라는 목표 자체를 조금 바꿔야 해요. Server Action이 잘하는 건 서버 사이드 검증과 상태 관리예요. 스트리밍이 잘 되는 건 Route Handler예요. 이 둘을 억지로 하나에 넣으려고 하면 삽질이 반복돼요.

---

## 배포 환경에서 꼭 확인해야 할 세 가지

첫 번째, **`runtime` 명시 없이 배포하면 청크가 버퍼링돼요.** Route Handler 파일 최상단에 `export const runtime = 'nodejs'`를 반드시 써주세요. 안 쓰면 Vercel이 Edge Runtime으로 배포하고, 스트리밍이 버퍼링되다가 한 번에 응답이 와요.

두 번째, **Nginx 뒤에 배포한다면 `X-Accel-Buffering: no` 헤더가 필요해요.** 이게 없으면 프록시가 응답을 모았다가 한 번에 보내버려요. 결과적으로 사용자 화면에는 스트리밍이 아닌 딜레이 후 전체 텍스트가 뜨죠.

세 번째, **긴 응답은 타임아웃을 예상하고 설계해야 해요.** Vercel Pro 기준 60초 타임아웃이에요. Claude의 응답이 길어질 것 같다면 `max_tokens`를 적절히 제한하거나, `vercel.json`에 `maxDuration`을 명시해야 해요.

```json
// vercel.json
{
  "functions": {
    "app/api/claude/route.ts": {
      "maxDuration": 60
    }
  }
}
```

---

## 마무리: "되는 코드"보다 "왜 안 됐는지"가 더 중요해요

Claude API 스트리밍을 Next.js App Router Server Action으로 구현하면서 얻은 가장 큰 교훈은 이거예요. 추상화 계층이 많아질수록 "원칙적으로 가능한 것"과 "실제로 되는 것" 사이에 간격이 생겨요.

Server Action의 직렬화 한계, Edge Runtime의 스트리밍 버퍼링, Vercel 타임아웃. 이 세 가지는 공식 문서에 흩어져 있거나 아예 명시가 안 돼 있어요. 누군가 한 번은 직접 부딪혀서 정리해야 하는 내용이죠.

다음에 비슷한 스택에서 AI 스트리밍을 구현한다면, 처음부터 역할 분리 패턴으로 시작하세요. "Server Action으로 스트리밍"보다 "Server Action으로 검증하고, Route Handler로 스트리밍"이 훨씬 빠른 길이에요.

어떤 방식으로 풀었나요? 다른 패턴이 있다면 댓글로 남겨주세요.

## 참고자료

1. [How to Use Claude Code for Next.js Development | Beam Terminal Organizer](https://getbeam.dev/blog/claude-code-nextjs-development.html)
2. [Guides: AI Coding Agents | Next.js](https://nextjs.org/docs/app/guides/ai-agents)
3. [nextjs-reviewer skill by physics91/claude-vibe](https://playbooks.com/skills/physics91/claude-vibe/nextjs-reviewer)


---

*Photo by [Vitaly Gariev](https://unsplash.com/@silverkblack) on [Unsplash](https://unsplash.com/photos/beekeeper-in-protective-suit-examining-honeycomb-frame-g1e3dtCrIC4)*
