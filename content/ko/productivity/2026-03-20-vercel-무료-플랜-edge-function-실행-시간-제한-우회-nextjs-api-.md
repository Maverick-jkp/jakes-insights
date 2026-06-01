---
title: "Vercel 무료 플랜 Edge Function 실행 시간 제한과 Next.js API Route 대안 설계 실전 접근법"
date: 2026-03-20T20:03:13+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-web", "vercel", "edge", "function", "Next.js"]
description: "Vercel Hobby 플랜 Edge Function 25초 제한에 막혔다면, Node.js 런타임 전환으로 60초까지 확보하세요. Next.js API Route 설계 변경으로 실행 시간 제한을 실용적으로 우회하는 방법을 다룹니다."
image: "/images/20260320-vercel-무료-플랜-edge-function-실행-.webp"
technologies: ["Next.js", "Node.js", "AWS", "OpenAI", "Vercel"]
faq:
  - question: "Vercel 무료 플랜 Edge Function 실행 시간 제한 우회 Next.js API Route 대안 설계 방법"
    answer: "Vercel 무료 플랜 Edge Function 실행 시간 제한 우회를 위한 Next.js API Route 대안 설계의 핵심은 route 파일 상단에 'export const runtime = nodejs'와 'export const maxDuration = 60'을 선언해 Serverless Function으로 전환하는 것입니다. 이렇게 하면 Hobby 플랜에서도 최대 60초까지 실행 시간을 확보할 수 있으며, Node.js 생태계 패키지도 그대로 사용 가능합니다. 작업이 60초를 초과한다면 Upstash QStash나 Inngest 같은 외부 큐를 활용해 작업을 분리하는 패턴도 고려해야 합니다."
  - question: "Vercel Function exceeded maximum duration 오류 해결 방법"
    answer: "이 오류는 Vercel의 플랫폼 실행 시간 제한에 걸렸을 때 발생하며, 코드 버그가 아닌 플랜별 제약입니다. Edge Function은 Pro 플랜으로 업그레이드해도 25초 한도가 동일하므로, 실행 시간이 긴 작업은 처음부터 Node.js Serverless Function(최대 60초)으로 설계하는 것이 효과적입니다. API Route에 'export const runtime = nodejs'를 선언하거나, 작업을 큐에 위임해 즉시 202 응답을 반환하는 패턴으로 해결할 수 있습니다."
  - question: "Vercel Edge Function과 Serverless Function 차이점 실행 시간 비교"
    answer: "Edge Function은 V8 isolate 기반 경량 런타임으로 CDN 엣지에서 실행되어 응답이 빠르지만 Node.js API 사용이 불가하고 모든 플랜에서 최대 25초로 제한됩니다. Serverless Function은 AWS Lambda 위에서 동작하며 Hobby 플랜 60초, Pro 플랜 300초, Enterprise 플랜 900초까지 실행이 가능하고 Node.js 생태계를 그대로 활용할 수 있습니다. 콜드 스타트 지연이 있다는 단점이 있지만, 외부 API 다중 호출이나 대용량 데이터 처리 같은 무거운 작업에는 Serverless Function이 적합합니다."
  - question: "Next.js API Route 60초 이상 긴 작업 처리하는 방법"
    answer: "60초를 초과하는 작업은 API Route에서 직접 처리하지 않고, 큐 패턴을 활용해 작업을 분리하는 구조를 설계해야 합니다. API Route는 작업 접수 후 즉시 202 Accepted를 반환하고, 실제 처리는 Upstash QStash나 Inngest 같은 외부 큐 워커에 위임하면 Vercel 실행 시간 제한 자체에 걸릴 일이 없어집니다. 클라이언트는 폴링이나 웹훅 방식으로 처리 결과를 수신하도록 구현하면 됩니다."
  - question: "Vercel 무료 플랜 LLM API 스트리밍 타임아웃 문제 해결"
    answer: "Vercel 무료 플랜 Edge Function에서 LLM 스트리밍을 프록시하면 전체 연결 유지 시간이 실행 시간에 포함되어 25초 한도에 빠르게 걸립니다. 이 문제는 'export const runtime = nodejs'로 Node.js Serverless Function으로 전환하고 ReadableStream을 활용해 스트리밍 응답을 구현하면 최대 60초까지 연결을 유지할 수 있습니다. 응답이 더 길어질 가능성이 있다면 큐 패턴을 결합해 백그라운드에서 처리하는 구조를 고려하는 것이 좋습니다."
---

Vercel 무료 플랜으로 사이드 프로젝트 배포하다가 "Function exceeded maximum duration" 오류 만난 적 있죠? 처음엔 코드 버그인 줄 알고 한참 뒤졌는데, 알고 보면 플랫폼 제한이에요. Vercel 무료 플랜(Hobby tier)의 Edge Function 실행 시간은 **최대 25초**. 이 한계에 부딪히면 선택지가 생각보다 넉넉하지 않아요.

그런데 포기하긴 이르거든요. Next.js API Route 설계를 조금만 바꾸면 꽤 멀리 갈 수 있어요.

> **핵심 요약**
> - Vercel Hobby 플랜의 Edge Function 실행 시간 한도는 25초. Node.js 런타임 Serverless Function은 최대 60초까지 허용된다.
> - Edge Runtime은 V8 기반 경량 런타임이라 Node.js API(파일 시스템, 일부 npm 패키지)를 못 쓰는 제약이 있다.
> - Next.js 15.x부터 Middleware가 Node.js 런타임을 실험적으로 지원하기 시작해, 라우팅 전략 선택지가 넓어졌다.
> - 긴 작업은 Edge에 두지 말고, 큐·배치 패턴이나 `runtime = 'nodejs'` 설정으로 Serverless Function에 넘기는 게 실질적인 해법이다.

---

## Edge Function과 Serverless Function, 뭐가 다른가요?

많은 분들이 이 둘을 헷갈려요. 이름도 비슷하고, 둘 다 Vercel에서 돌아가니까요.

**Edge Function**은 Cloudflare Workers처럼 V8 isolate 위에서 돌아가는 경량 런타임이에요. CDN 엣지 노드에서 실행되니까 응답 속도가 빠르죠. 그 대신 Node.js의 `fs`, `child_process` 같은 API는 못 써요. npm 패키지도 Node.js 환경을 전제로 만든 건 안 돌아가는 경우가 많아요.

**Serverless Function (Node.js 런타임)**은 AWS Lambda 위에서 돌아가는 일반적인 서버리스예요. 실행 위치가 엣지보다 멀어서 콜드 스타트 지연이 있지만, 실행 시간이 더 길고 Node.js 생태계를 그대로 쓸 수 있어요.

Vercel 공식 문서 기준, 2026년 3월 현재 플랜별 한도를 정리하면:

| 항목 | Hobby (무료) | Pro | Enterprise |
|---|---|---|---|
| Edge Function 최대 실행 시간 | 25초 | 25초 | 25초 |
| Serverless Function 최대 실행 시간 | 60초 | 300초 | 900초 |
| Serverless Function 메모리 | 1,024 MB | 3,009 MB | 3,009 MB |
| 월간 Edge Function 호출 | 50만 회 | 100만 회 | 무제한 |
| Serverless Function 실행 시간 | 100 GB-hours | 1,000 GB-hours | 무제한 |

눈에 띄는 게 있죠? Edge Function은 Pro 플랜으로 올려도 25초 한도가 동일해요. 반면 Serverless Function은 Hobby에서도 60초까지 주거든요. 긴 작업이라면 처음부터 Serverless Function을 쓰는 게 맞는 구조인 셈이에요.

---

## 실행 시간 제한을 만나는 세 가지 상황

어떤 작업에서 주로 이 한도에 걸릴까요? 크게 세 가지 패턴이에요.

**외부 API를 여러 개 연달아 부르는 경우.** LLM API나 외부 서드파티 서비스를 여러 번 순차 호출하면 금방 쌓여요. OpenAI API 첫 번째 토큰이 나오기까지 3-5초, 다음 처리 단계가 또 몇 초. 25초는 생각보다 빨리 차요.

**데이터 집약적인 처리.** CSV 파싱, 이미지 메타데이터 읽기, 대규모 JSON 가공 같은 작업이요. Edge 런타임은 메모리도 상대적으로 제한적이라 이런 작업에 맞지 않아요.

**스트리밍 응답이 길어지는 경우.** 스트리밍으로 응답을 보낸다고 해도 전체 연결 유지 시간이 실행 시간에 포함돼요. LLM 스트리밍 응답을 Edge Function에서 그냥 프록시하면 생각보다 빨리 타임아웃 나는 이유가 이거예요.

---

## Next.js API Route 대안 설계: 실전 접근법 세 가지

### 접근법 1: `runtime` 설정을 바꿔서 Serverless Function으로 이동

가장 단순한 해법이에요. Next.js API Route 파일 상단에 한 줄 추가하면 끝이거든요.

```ts
// app/api/heavy-task/route.ts
export const runtime = 'nodejs'; // 기본값은 'edge'가 아니지만 명시 권장
export const maxDuration = 60;   // Hobby 플랜 최대값
```

`runtime = 'nodejs'`로 설정하면 해당 Route Handler는 Node.js Serverless Function으로 배포돼요. Hobby 플랜에서 최대 60초를 쓸 수 있고, Node.js 생태계 패키지도 그대로 쓰죠. 단, 콜드 스타트 지연이 생기고, 엣지 캐싱 혜택을 잃어요.

Next.js 15.5 기준으로 Middleware도 Node.js 런타임을 `experimental` 플래그로 지원하기 시작했는데, 이 기능은 아직 프로덕션 안정성을 꼼꼼히 확인해야 하는 단계예요.

### 접근법 2: 작업을 쪼개는 큐 패턴

60초도 모자라다면, 작업 자체를 나눠야 해요. 전형적인 패턴은 이래요.

1. API Route는 작업 접수만 하고 즉시 `202 Accepted` 반환
2. 실제 처리는 외부 큐(예: Upstash QStash, Inngest)에 위임
3. 클라이언트는 폴링이나 웹훅으로 결과 수신

이 구조면 API Route 자체는 1-2초면 끝나고, 무거운 처리는 별도 워커가 담당해요. Vercel 제한을 우회하는 게 아니라 아예 제한에 걸릴 일이 없게 만드는 거죠.

### 접근법 3: 스트리밍 응답으로 연결 유지

LLM 응답처럼 결과가 점진적으로 나오는 경우라면, `ReadableStream`으로 응답을 스트리밍하면 사용자 경험도 좋아지고 타임아웃 압박도 줄어요.

```ts
export async function POST(req: Request) {
  const stream = new ReadableStream({
    async start(controller) {
      // 청크별로 enqueue
      controller.close();
    }
  });
  return new Response(stream, {
    headers: { 'Content-Type': 'text/event-stream' }
  });
}
```

다만, Edge Function에서 쓸 때 전체 스트리밍 시간이 25초를 넘으면 여전히 끊겨요. 스트리밍 자체가 실행 시간 한도를 없애주진 않으니까요. 긴 스트리밍이 필요하다면 `runtime = 'nodejs'`와 함께 쓰는 게 맞아요.

---

## 상황별로 뭘 써야 할까요?

**LLM API 프록시를 Vercel 무료 플랜으로 만드는 경우**
→ `runtime = 'nodejs'` + `maxDuration = 60` + 스트리밍 응답. 대부분의 LLM 응답은 60초 안에 끝나고, 스트리밍으로 UX도 챙길 수 있어요.

**이미지나 파일 처리 작업**
→ Vercel에서 처리하지 말고 큐 패턴으로 외부 워커에 위임하세요. Hobby 플랜 GB-hours 한도(100 GB-hours/월)도 같이 고려해야 해요. 메모리 1GB짜리 함수가 100시간 돌면 한도가 꽉 차거든요.

**빠른 응답이 핵심인 API (인증, 라우팅 처리 등)**
→ Edge Function이 맞아요. 25초가 넘을 일이 없고, 전 세계 엣지 노드에서 빠르게 응답하니까요. 월 50만 회 호출 한도도 대부분의 사이드 프로젝트엔 충분해요.

---

## 2026년 하반기, 어디로 흘러갈까요?

Next.js 15.x에서 시작된 Middleware Node.js 런타임 지원이 안정화 단계로 들어오면, 지금보다 라우팅 계층에서 더 무거운 로직을 처리할 수 있게 돼요. Edge Function의 포지션은 점점 "빠른 라우팅·A/B 테스트·인증 토큰 검증"으로 좁아지고, 데이터 처리는 Serverless Function이나 외부 큐로 이동하는 방향이에요.

Vercel이 Hobby 플랜 한도를 올릴 가능성은 낮아요. Pro 전환 유도를 위한 설계니까요. 그렇다면 무료 플랜 안에서 잘 설계하는 능력 자체가 개발자의 실력이 되는 셈이에요.

**핵심 요약:**
- Edge Function 25초 한도는 Pro로 올려도 안 바뀌어요. Serverless Function(60초)이 Hobby에서 더 관대해요.
- `runtime = 'nodejs'` 설정 한 줄이 많은 문제를 해결해요.
- 60초도 부족하다면 큐 패턴으로 아키텍처 자체를 바꿔야 해요.
- Edge는 빠른 로직에만, 무거운 건 Node.js 런타임 Serverless Function으로 분리하는 원칙을 지키면 돼요.

지금 당신의 API Route, `runtime` 설정이 어떻게 되어 있는지 확인해봤나요?

## 참고자료

1. [Next.js 15.5 Middleware Node.js 런타임 지원과 캐시 동작 분석 | MECH2CS 기술블로그](https://blog.mech2cs.com/posts/nextjs-middleware-nodejs)
2. [Vercel을 이용한 무료 웹 배포 이용해보기](https://allinfor.tistory.com/76)
3. [Edge Functions in Next.js: What They Are and When to Use Them | by Beenish Khan | Medium](https://medium.com/@vdsnini/edge-functions-in-next-js-what-they-are-and-when-to-use-them-14d0e1662cf4)


---

*Photo by [Logan Voss](https://unsplash.com/@loganvoss) on [Unsplash](https://unsplash.com/photos/3d-text-that-says-digital-with-fiery-texture-rdG4_6Xo3lo)*
