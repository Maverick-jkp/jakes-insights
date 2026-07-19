---
title: "Next.js 14 Vercel 무료 플랜 함수 실행시간 초과, Edge Runtime 전환 실험과 제약 정리"
date: 2026-05-24T20:35:58+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-cloud", "next.js", "vercel", "/uc2e4/ud589/uc2dc/uac04", "Node.js"]
description: "Vercel 무료 플랜 10초 제한으로 504 오류를 겪는다면? Next.js 14에서 Edge Runtime 전환 시 25초까지 확보 가능하지만 fs·crypto 미지원 등 실제 제약과 실험 결과를 정리했습니다."
image: "/images/20260524-nextjs-14-vercel-무료-플랜-함수-실행시간.webp"
technologies: ["Next.js", "Node.js", "GPT", "OpenAI", "Anthropic"]
faq:
  - question: "Vercel 무료 플랜 함수 실행시간 제한 몇 초야"
    answer: "Vercel Hobby(무료) 플랜의 Serverless Function 최대 실행시간은 10초예요. 10초를 넘으면 Vercel이 강제로 연결을 끊고 사용자에게 504 Gateway Timeout 오류가 발생해요."
  - question: "Next.js 14 Vercel 무료 플랜 함수 실행시간 초과 edge runtime 전환 실험 어떻게 해"
    answer: "Next.js 14에서 Edge Runtime으로 전환하려면 해당 라우트 파일에 `export const runtime = 'edge';` 한 줄만 추가하면 돼요. 단, Edge Runtime은 Node.js API를 지원하지 않아서 fs, path, Prisma 같은 Node.js 의존 패키지가 있으면 그대로 전환이 안 되고 빌드 오류나 런타임 에러가 발생할 수 있어요."
  - question: "Vercel edge runtime 실행시간 제한 serverless랑 다른가요"
    answer: "Vercel Hobby 플랜 기준으로 Serverless Function은 최대 10초지만, Edge Function은 Streaming 포함 최대 25초까지 허용돼요. 이 차이 때문에 Next.js 14 Vercel 무료 플랜 함수 실행시간 초과 edge runtime 전환 실험이 OpenAI 같은 AI API를 사용하는 사이드 프로젝트 개발자들 사이에서 활발하게 시도되고 있어요."
  - question: "edge runtime에서 Prisma ORM 사용 가능한가요"
    answer: "Vercel Edge Runtime은 V8 기반으로 Node.js 전용 API를 지원하지 않기 때문에 Prisma, TypeORM, pg, mysql2 같은 전통적인 Node.js DB 드라이버는 Edge Runtime에서 동작하지 않아요. DB 연결이 필요한 로직은 Edge Runtime 대신 Serverless Function을 유지하거나 Edge 호환 드라이버로 교체해야 해요."
  - question: "Vercel 무료 플랜에서 OpenAI 스트리밍 10초 제한 우회하는 방법"
    answer: "Edge Runtime과 ReadableStream을 조합해 응답을 스트리밍 방식으로 전환하면 실질적으로 10초 벽을 우회할 수 있어요. 응답이 완전히 끝날 때까지 기다리는 구조가 아니라 토큰이 하나씩 클라이언트로 전달되는 구조로 바뀌기 때문에, Vercel Hobby 플랜의 Edge Function 25초 제한 안에서 LLM 응답을 처리할 수 있어요."
aliases:
  - "/tech/2026-05-24-nextjs-14-vercel-무료-플랜-함수-실행시간-초과-edge-runtime-전환-/"
  - "/ko/tech/2026-05-24-nextjs-14-vercel-무료-플랜-함수-실행시간-초과-edge-runtime-전환-/"

---

Vercel 무료 플랜을 쓰다가 갑자기 `504 Gateway Timeout`을 만난 적 있으세요? 10초 제한. 그 벽 앞에서 많은 사이드 프로젝트가 멈춰요. Next.js 14 기반 프로젝트에서 이 문제는 개발자 커뮤니티의 단골 이슈예요. 그리고 그 해법으로 Edge Runtime 전환 실험이 활발하게 시도되고 있죠.

> **핵심 요약**
> - Vercel Hobby 플랜의 Serverless Function 실행시간 상한은 10초, Edge Runtime은 최대 25초(Streaming 포함)까지 허용돼요.
> - Edge Runtime은 Node.js API 일부를 지원하지 않아 `fs`, `crypto` 등 의존 패키지가 있으면 그대로 전환이 안 돼요.
> - 실행시간 초과의 가장 흔한 원인은 DB 콜드 커넥션, 무거운 외부 API 요청, 대용량 데이터 직렬화 세 가지예요.
> - Edge Runtime 전환으로 평균 응답시간이 줄어드는 케이스는 있지만, 항상 빠른 건 아니에요. 런타임 제약을 먼저 확인해야 해요.

---

## Vercel 무료 플랜, 그 10초 벽의 실체

Vercel은 플랜별로 Serverless Function의 최대 실행시간을 다르게 제한해요.

| 플랜 | Serverless 최대 실행시간 | Edge Function 최대 실행시간 | 월 무료 호출 수 |
|------|--------------------------|-----------------------------|----|
| Hobby (무료) | **10초** | 25초 (streaming 포함) | 100GB-hrs |
| Pro | 60초 | 25초 | 1,000GB-hrs |
| Enterprise | 900초 | 25초 | 무제한 협의 |

출처: Vercel 공식 플랜 비교 페이지 (docs.vercel.com/functions/runtimes, 2026년 5월 기준)

`/api` 라우트나 서버 컴포넌트에서 실행되는 코드가 10초를 넘으면 Vercel이 강제로 연결을 끊어버려요. 사용자 입장에서는 흰 화면이나 에러 페이지가 뜨는 거고요.

문제는 여기서 시작돼요. OpenAI, Anthropic 같은 외부 AI API를 호출하거나, Supabase에서 콜드 커넥션이 발생하거나, 대용량 JSON을 파싱하는 순간 10초는 생각보다 금방 채워져요. Next.js GitHub Discussions에서 2025년 하반기부터 이 이슈 관련 스레드가 눈에 띄게 늘었는데, 특히 LLM 기반 기능을 무료 플랜에 올리려는 사이드 프로젝트 개발자들이 많이 부딪혔어요.

그래서 커뮤니티가 찾아낸 우회로가 **Edge Runtime 전환 실험**이에요.

---

## Edge Runtime이 다른 이유

Edge Runtime은 Vercel이 V8 기반으로 제공하는 실행 환경이에요. Node.js 런타임이 아니에요. 이 차이가 전부를 바꿔요.

Next.js 14에서 특정 라우트를 Edge Runtime으로 전환하는 건 한 줄이면 돼요.

```ts
// app/api/my-route/route.ts
export const runtime = 'edge';
```

그런데 이게 전부가 아니에요. Edge Runtime은 **Web API 표준 기반**으로 동작해요. `fetch`, `Request`, `Response`, `ReadableStream`, `TextEncoder`는 쓸 수 있어요. 반면 Node.js 전용 API인 `fs`, `path`, `child_process`, `Buffer`(일부)는 쓸 수 없어요. 지원되지 않는 패키지를 import하면 빌드 타임에 오류가 나거나 런타임에 예기치 않게 터져요.

그럼 Edge에서 더 빠를 수 있는 이유가 뭐냐고요? Edge Function은 사용자와 물리적으로 가까운 서버(엣지 노드)에서 실행돼요. Leapcell 기술 블로그 분석에 따르면, 일반 Serverless Function 대비 네트워크 레이턴시가 평균 40~60ms 줄어드는 케이스가 보고됐어요. 단, 컴퓨팅 작업이 가벼울 때 얘기예요.

---

## 전환 실험: 되는 케이스 vs 막히는 케이스

### 전환이 잘 되는 케이스

간단한 API 프록시, AI API Streaming, 경량 인증 로직이 여기 해당해요.

OpenAI Streaming 응답을 Edge Runtime으로 처리하면 Vercel Hobby 플랜에서도 25초 안에 토큰을 계속 스트리밍할 수 있어요. Edge Runtime + `ReadableStream` 조합으로 응답을 끊지 않고 조각씩 보내면, 실질적으로 10초 벽을 우회하는 거예요. "실행이 끝날 때까지 기다리는" 구조가 아니라 "글자가 하나씩 나타나는" 구조로 바뀌는 셈이죠.

```ts
export const runtime = 'edge';

export async function POST(req: Request) {
  const { prompt } = await req.json();
  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ model: 'gpt-4o', messages: [{ role: 'user', content: prompt }], stream: true }),
  });
  return new Response(response.body, { headers: { 'Content-Type': 'text/event-stream' } });
}
```

### 전환이 막히는 케이스

Prisma, TypeORM 같은 전통적 ORM을 쓰는 DB 연결 로직은 Edge Runtime에서 안 돌아요. `pg`, `mysql2` 같은 Node.js 드라이버도 마찬가지예요. 내부적으로 Node.js 네이티브 모듈에 의존하거든요.

대안은 이렇게 정리돼요.

| 접근 방식 | 대표 도구 | Edge 호환 | 주의점 |
|----------|----------|----------|--------|
| HTTP 기반 DB 클라이언트 | Supabase JS SDK, PlanetScale HTTP driver | ✅ | 쿼리 API 제한 있음 |
| 기존 ORM 그대로 사용 | Prisma, TypeORM | ❌ | Edge 불가, Node.js 전용 |
| Edge 호환 ORM | Drizzle ORM (HTTP mode), Kysely | ✅ | 설정 추가 필요 |
| 라우트 분리 | API 분리 후 일부만 Edge 처리 | ✅ | 아키텍처 복잡도 증가 |

---

## 시나리오별 접근법

**시나리오 1: AI 기능을 무료 플랜에 올리고 싶다**

LLM API 호출은 응답이 느려요. Streaming + Edge Runtime 조합이 가장 깔끔한 답이에요. `runtime = 'edge'` 선언하고, `ReadableStream`으로 응답 파이프라인을 구성하면 Hobby 플랜에서도 챗봇을 올릴 수 있어요. 외부 API 키는 반드시 환경변수로 관리하세요.

**시나리오 2: DB 조회가 포함된 라우트가 느리다**

DB 콜드 커넥션 문제라면 Edge Runtime 전환보다 **커넥션 풀링 레이어**(PgBouncer, Supabase Connection Pooling)를 먼저 확인하는 게 나아요. Edge Runtime으로 전환해도 DB 드라이버가 호환 안 되면 빌드도 못 해요.

**시나리오 3: 빌드는 되는데 특정 패키지가 런타임 오류를 낸다**

`next.config.js`에서 해당 패키지를 `serverExternalPackages`로 지정하거나, 라우트를 `nodejs` 런타임으로 명시해요. Edge와 Node.js를 라우트별로 섞어 쓰는 게 Next.js 14의 장점 중 하나예요.

---

## 앞으로 뭘 봐야 하냐고요

세 가지만 짚을게요.

- **Vercel의 Fluid Compute**: 기존 Serverless와 Edge의 경계를 허무는 실험적 런타임 모델이에요. 2025년 말 발표 기준, 2026년 하반기 GA가 예상돼요. 안정화되면 지금의 10초/25초 이분법이 바뀔 수 있어요.
- **Drizzle ORM의 Edge 지원 성숙도**: 2025년 기준 HTTP 기반 쿼리를 Edge에서 쓸 수 있게 지원하기 시작했어요. 생태계가 빠르게 커지고 있어요.
- **대안 플랫폼 압력**: Cloudflare Workers + D1, Deno Deploy 등이 Vercel Hobby의 제약 없이 비슷한 경험을 무료로 제공해요. 이 경쟁이 Vercel을 어디로 움직일지가 흥미로운 지점이에요.

---

## 전환 전에 이것만 체크하세요

Edge Runtime 전환으로 실행시간 초과를 풀려면, 먼저 이 세 가지를 확인하세요.

- 라우트가 Node.js 전용 패키지를 직접 import하나요?
- DB 연결이 포함돼 있나요?
- Streaming으로 응답 구조를 바꿀 수 있나요?

첫 번째나 두 번째가 "예"라면 전환이 복잡해요. 세 번째가 "예"라면 전환이 가장 빠른 해법이에요.

Edge Runtime은 만능 해결사가 아니에요. 제약을 먼저 파악하고, 딱 맞는 라우트에만 쓰는 게 핵심이에요. 지금 실행시간 초과를 겪고 있다면, `export const runtime = 'edge'` 한 줄 추가보다 **어떤 작업이 시간을 잡아먹는지** 로그로 확인하는 게 더 빠른 길이에요.

라우트 중 Edge Runtime으로 옮겨볼 만한 게 있다면, 댓글로 공유해 주세요. 어떤 케이스에서 막혔는지, 어떻게 풀었는지—그 경험이 다른 개발자에게 더 실용적인 자료가 될 거예요.

## 참고자료

1. [API Reference: Edge Runtime | Next.js](https://nextjs.org/docs/pages/api-reference/edge)
2. [Next.js 미들웨어 및 엣지 함수를 사용하여 엣지에서 웹 애플리케이션 가속 | Leapcell](https://leapcell.io/blog/ko/nextjs-mideware-edge-function-web-app-acceleration)


---

*Photo by [Đào Hiếu](https://unsplash.com/@hieu101193) on [Unsplash](https://unsplash.com/photos/a-close-up-of-a-black-amplifier-with-a-red-background-Q0UmpdvmCE0)*
