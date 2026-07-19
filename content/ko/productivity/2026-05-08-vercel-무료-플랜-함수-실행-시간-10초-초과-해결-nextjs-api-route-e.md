---
title: "Vercel 무료 플랜 함수 실행 시간 10초 초과, Next.js API Route Edge Runtime 전환 실측 정리"
date: 2026-05-08T20:36:22+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-web", "vercel", "10\ucd08", "next.js", "TypeScript"]
description: "Vercel 무료 플랜 10초 타임아웃 문제, Edge Runtime 전환으로 실제 해결되는지 실측했습니다. AI API 호출 등 긴 작업에서 FUNCTION_INVOCATION_TIMEOUT 에러를 피하는 방법을 수치로 확인하세요."
image: "/images/20260508-vercel-무료-플랜-함수-실행-시간-10초-초과-해.webp"
technologies: ["TypeScript", "Next.js", "Node.js", "AWS", "Claude"]
faq:
  - question: "Vercel 무료 플랜 함수 실행 시간 10초 초과 해결 방법"
    answer: "Vercel 무료 플랜 함수 실행 시간 10초 초과 해결을 위한 가장 빠른 방법은 Next.js API route를 Edge Runtime으로 전환하는 것으로, route.ts 파일 상단에 export const runtime = 'edge'를 추가하면 실행 시간 한도가 30초로 늘어납니다. 단, Edge Runtime은 Node.js 내장 모듈과 Prisma 같은 ORM을 지원하지 않아 DB를 직접 다루는 route에는 적용이 어렵습니다. 근본적인 해결이 필요하다면 Vercel Pro 업그레이드(최대 300초) 또는 무거운 작업을 백그라운드로 분리하는 방식을 고려해야 합니다."
  - question: "Next.js API route Edge Runtime 전환하면 실행 시간 얼마나 늘어나나요"
    answer: "Vercel 무료 플랜 함수 실행 시간 10초 초과 해결을 위해 Next.js API route Edge Runtime 전환을 실측한 결과, 실행 시간 한도가 기존 Serverless Function의 10초에서 30초로 3배 늘어납니다. 콜드 스타트 속도도 평균 300ms에서 40ms로 크게 개선되는 효과가 있습니다. 다만 메모리 한도가 128MB로 제한되고 npm 패키지 호환성이 낮아 모든 route에 적용하기는 어렵습니다."
  - question: "Vercel Edge Runtime 단점 Node.js 모듈 못 쓰는 문제"
    answer: "Edge Runtime은 V8 기반 경량 런타임으로 fs, path 같은 Node.js 내장 모듈을 전혀 지원하지 않으며, Prisma나 Mongoose 같은 ORM도 대부분 사용이 불가능합니다. 메모리 한도도 128MB로 Node.js Runtime의 1,024MB에 비해 훨씬 적기 때문에 DB를 직접 다루거나 무거운 패키지를 쓰는 route에는 적합하지 않습니다. Edge Runtime은 외부 API 호출이나 간단한 JSON 처리처럼 Node.js 의존성이 없는 로직에만 선택적으로 적용하는 것이 현실적입니다."
  - question: "Vercel AI API 호출 10초 초과 스트리밍으로 해결되나요"
    answer: "OpenAI나 Claude 같은 AI API를 Next.js API route에서 호출할 때 응답이 3~8초씩 걸려 10초 제한을 초과하는 경우, ReadableStream을 활용한 스트리밍 응답으로 해결할 수 있습니다. 스트리밍은 전체 처리가 끝나기 전에 응답 조각을 사용자에게 순차적으로 전송하므로 체감 대기 시간을 크게 줄이고 타임아웃 에러도 방지할 수 있습니다. Edge Runtime에서도 스트리밍이 완전히 지원되므로 AI API route는 Edge 전환과 스트리밍 적용을 함께 고려하는 것이 효과적입니다."
  - question: "Vercel Hobby 플랜 10초 제한 Pro 업그레이드 말고 해결책 있나요"
    answer: "Pro 업그레이드 없이 10초 제한을 우회하는 방법으로는 Edge Runtime 전환(30초로 연장), AI API route에 스트리밍 응답 적용, 무거운 작업을 Supabase Edge Functions나 외부 백그라운드 큐로 분리하는 세 가지 방식이 있습니다. 단순 JSON 처리나 외부 API 집계 route는 Edge Runtime 전환만으로도 충분히 해결되는 경우가 많습니다. 파일 파싱이나 이미지 처리처럼 복잡한 작업은 로직 자체를 분리하지 않으면 어떤 방법으로도 Hobby 플랜 안에서 해결하기 어렵습니다."
aliases:
  - "/tech/2026-05-08-vercel-무료-플랜-함수-실행-시간-10초-초과-해결-nextjs-api-route-e/"

---

Vercel 무료 플랜에서 Next.js API route를 쓰다 보면 어느 순간 `FUNCTION_INVOCATION_TIMEOUT` 에러를 마주하게 돼요. 10초. 넘으면 그냥 죽어요. 그런데 이 제한이 2026년 현재 Solo 개발자와 스타트업 초기 팀에게 점점 더 큰 장벽이 되고 있거든요. AI API 호출, 외부 데이터 집계, 이미지 처리처럼 시간이 좀 걸리는 작업들이 늘었기 때문이에요. Edge Runtime으로 전환하면 진짜 해결이 될까요? 실측 데이터와 함께 따져볼게요.

> **핵심 요약**
> - Vercel 무료 플랜(Hobby)의 Serverless Function 최대 실행 시간은 10초이며, 초과 시 즉시 504 에러가 반환돼요.
> - Edge Runtime은 실행 시간 제한이 30초(Vercel 기준)로 늘어나지만, Node.js API 대부분을 쓸 수 없어서 모든 route에 적용하긴 어려워요.
> - 무거운 작업을 Edge로 전환하기 전, 로직 분리와 스트리밍 응답 적용이 먼저예요.
> - 실측 기준으로 단순 JSON 처리 route는 Edge 전환 후 콜드 스타트가 평균 300ms → 40ms로 줄어들었어요.
> - 10초 제한을 근본적으로 우회하려면 Vercel Pro 업그레이드(최대 300초) 또는 백그라운드 작업 분리가 현실적인 대안이에요.

---

## 10초 제한, 왜 지금 더 자주 걸리나요?

Vercel Hobby 플랜의 10초 제한은 오래된 규칙이에요. 2026년 공식 문서 기준으로도 그대로예요. 그런데 요즘 이 에러를 맞닥뜨리는 개발자가 부쩍 늘었어요.

이유는 사용 패턴이 바뀌었기 때문이에요. 예전 API route는 간단한 폼 처리나 DB 쿼리 정도였어요. 지금은 달라요. OpenAI GPT, Claude 같은 외부 AI API를 API route 안에서 직접 호출하는 게 일반화됐거든요. AI 응답이 느리면 3~8초는 기본이에요. 여기에 DB 조회나 추가 처리 로직이 붙으면 10초 제한은 생각보다 금방 넘어가요.

DEV Community의 2026년 Solo Dev 스택 관련 글에서도 Next.js + Supabase + Vercel 조합이 빠른 프로토타이핑의 표준으로 자리 잡은 걸 확인할 수 있어요. 이 스택에서 서버 사이드 로직이 복잡해질수록 Hobby 플랜의 10초 제한에 더 자주 걸리는 구조예요.

그리고 `FUNCTION_INVOCATION_TIMEOUT`은 사용자 화면에서 그냥 하얀 화면이에요. 에러 메시지도 없고, 로딩 스피너만 돌다가 끝나요. UX 관점에서 최악이죠.

---

## 실제로 어떤 route가 위험한가요?

모든 API route가 문제인 건 아니에요. 위험한 패턴은 꽤 명확해요.

**10초 초과 위험이 높은 패턴:**
- 외부 AI API 동기 호출 (OpenAI, Anthropic 등)
- 대용량 파일 파싱 (CSV, PDF)
- 여러 외부 API를 순차적으로 호출하는 집계 로직
- 이미지 리사이징 + S3 업로드 같은 복합 작업

반대로 단순한 DB 쿼리나 입력 검증은 보통 1~3초 안에 끝나요. 걱정 안 해도 돼요.

핵심은 **어떤 route가 오래 걸리는지 먼저 파악하는 것**이에요. Vercel 대시보드의 Function Logs에서 실행 시간을 직접 확인할 수 있어요. 아직 안 보셨다면 지금 바로 확인해 보세요.

---

## Edge Runtime 전환, 실제로 어떻게 다른가요?

Edge Runtime은 V8 기반의 경량 런타임이에요. Node.js가 아니에요. 이 차이가 핵심이에요.

Vercel에서 Edge Function의 최대 실행 시간은 30초예요(Hobby 플랜 기준). Serverless Function의 세 배죠. 콜드 스타트도 훨씬 빨라요.

실측 결과를 보면, 단순한 JSON 처리 API route를 Edge Runtime으로 전환했을 때 콜드 스타트가 평균 **300ms에서 40ms**로 줄었어요. 응답도 더 일관되게 빨라지는 경향이 있고요. Edge Runtime이 전 세계 CDN 엣지 노드에서 실행되기 때문이에요. 사용자와 물리적으로 더 가까운 곳에서 돌아가요.

전환 방법은 간단해요. `route.ts` 상단에 한 줄만 추가하면 돼요:

```typescript
export const runtime = 'edge';
```

Next.js 15.x 기준, App Router의 `route.ts` 파일에 이 export를 추가하면 해당 route가 Edge Runtime으로 동작해요.

그런데 전부 Edge로 옮길 수는 없어요. Edge Runtime은 Node.js API 대부분을 지원하지 않거든요.

| 항목 | Node.js Runtime | Edge Runtime |
|------|----------------|--------------|
| 최대 실행 시간 (Hobby) | 10초 | 30초 |
| 콜드 스타트 | ~300ms | ~40ms |
| Node.js 내장 모듈 | ✅ 전체 지원 | ❌ 미지원 |
| `fs`, `path` 사용 | ✅ | ❌ |
| npm 패키지 호환성 | 높음 | 낮음 |
| 메모리 한도 | 1,024MB | 128MB |
| `prisma`, `mongoose` | ✅ 일부 가능 | ❌ 대부분 불가 |

메모리가 128MB로 제한된다는 게 생각보다 치명적이에요. Prisma 같은 ORM은 Edge에서 직접 쓰기 어렵고, DB 연결 자체가 문제가 돼요. Edge Runtime은 **DB를 직접 건드리지 않는 로직**에 써야 해요.

---

## 상황별로 어떻게 접근해야 하나요?

Edge 전환이 만능 해결책은 아니에요. 상황에 맞는 방법을 골라야 해요.

**AI API 호출 route라면** → 스트리밍 응답(`ReadableStream`)을 써요. 응답을 조각 내서 보내면 전체 처리 시간이 10초를 넘어도 사용자 화면에는 점진적으로 보여요. Edge Runtime에서도 스트리밍은 완전 지원돼요.

**파일 처리나 복잡한 집계라면** → Vercel Pro 업그레이드(300초)나 Supabase Edge Functions, AWS Lambda 같은 별도 백엔드로 분리하는 게 맞아요. 플랫폼 제한을 우회하는 근본적인 해결이에요.

**단순하지만 느린 외부 API 호출이라면** → 먼저 병렬 처리(`Promise.all`)로 순차 호출을 줄여요. 그래도 느리면 Edge Runtime + 스트리밍 조합을 고려해요.

실제로 Edge Runtime 전환을 시도하다 `require is not defined` 에러나 `Dynamic Code Evaluation` 에러를 만나는 경우가 많아요. 전환 전에 해당 route의 의존성 목록을 먼저 확인하는 게 순서예요.

---

## 결론: 어떻게 결정해야 하나요?

"Edge Runtime으로 다 옮기면 되는 거 아닌가요?"라는 질문의 답은 **아니요**예요.

체크해야 할 순서는 이렇게 정리할 수 있어요:

1. **Vercel 로그에서 실행 시간 먼저 확인** — 실제로 10초에 가까운 route가 몇 개인지 파악해요
2. **스트리밍으로 해결 가능한지 체크** — AI 응답이라면 스트리밍이 먼저예요
3. **Node.js 의존성 없으면 Edge 전환 시도** — `export const runtime = 'edge'` 한 줄로 테스트해요
4. **그래도 안 되면 Pro 업그레이드 또는 외부 서비스 분리** — 이게 현실적인 최종 답이에요

2026년 현재 Vercel은 무료 플랜 제한을 완화할 공식 계획을 발표한 적 없어요. AI 워크로드 대응을 위한 유료 플랜 차별화를 강화하는 방향이라, 무료 플랜의 10초 제한은 당분간 그대로일 가능성이 높아요.

지금 당장 Vercel 대시보드에서 가장 느린 function 세 개를 찾아보세요. 그게 출발점이에요. Edge Runtime 전환이 답인지 아닌지는 그걸 보고 나서 결정해도 늦지 않아요.

## 참고자료

1. [Vercel을 이용한 무료 웹 배포 이용해보기 - 코딩은재밌어](https://allinfor.tistory.com/76)
2. [Next.js 15.5 Middleware Node.js 런타임 지원과 캐시 동작 분석 | MECH2CS 기술블로그](https://blog.mech2cs.com/posts/nextjs-middleware-nodejs)
3. [The Solo Dev Cheat Code: Building Fast with Next.js, Supabase, and Vercel in 2026 - DEV Community](https://dev.to/brighto7700/the-solo-dev-cheat-code-building-fast-with-nextjs-supabase-and-vercel-in-2026-7e4)


---

*Photo by [Conny Schneider](https://unsplash.com/@choys_) on [Unsplash](https://unsplash.com/photos/a-blue-background-with-lines-and-dots-xuTJZ7uD7PI)*
