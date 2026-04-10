---
title: "Vercel Edge Function vs Cloudflare Workers 콜드스타트 차이와 실무 선택 기준"
date: 2026-04-10T20:13:32+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-cloud", "vercel", "edge", "function", "JavaScript"]
description: "Vercel Edge Function과 Cloudflare Workers가 콜드스타트 없는 이유는 다릅니다. V8 Isolate 구조 차이부터 Node.js API 제약, Next.js 통합 깊이까지 실무 선택 기준을 구체적으로 비교합니다."
image: "/images/20260410-vercel-edge-function-vs-cloudf.webp"
technologies: ["JavaScript", "Next.js", "Node.js", "AWS", "Vercel"]
faq:
  - question: "Vercel Edge Function vs Cloudflare Workers 콜드스타트 없는 이유 차이점이 뭔가요"
    answer: "두 플랫폼 모두 V8 Isolate 기반으로 동작하기 때문에 컨테이너 기동 없이 격리된 실행 컨텍스트를 바로 생성해 콜드스타트가 구조적으로 발생하지 않습니다. 다만 Cloudflare Workers는 전 세계 300개 이상 PoP에서 p50 응답시간 약 5ms를 기록하는 반면, Vercel Edge Function은 Next.js 네이티브 통합에 강점을 두고 있어 실무 선택 기준이 달라집니다."
  - question: "엣지 함수 첫 요청 느린 이유 콜드스타트 아닌가요"
    answer: "Vercel Edge Function과 Cloudflare Workers는 V8 Isolate 구조 덕분에 전통적인 콜드스타트가 없지만, 지리적으로 가까운 PoP에 아직 요청이 라우팅되지 않았거나 네트워크 레이턴시가 원인인 경우가 많습니다. AWS Lambda처럼 컨테이너를 새로 띄우는 방식이 아니기 때문에, 느린 첫 요청은 런타임 초기화보다 DNS나 TLS 핸드셰이크 같은 네트워크 단계를 먼저 확인하는 것이 좋습니다."
  - question: "Cloudflare Workers Next.js 같이 쓸 수 있나요"
    answer: "사용은 가능하지만 Vercel처럼 네이티브 통합은 아니라서 별도 설정이 필요합니다. `export const runtime = 'edge'` 한 줄로 엣지 실행이 되는 Vercel과 달리, Cloudflare Workers에서 Next.js를 쓰려면 추가 어댑터 구성이 필요해 Next.js 중심 팀이라면 생산성 차이가 체감됩니다."
  - question: "Cloudflare Workers 무료 플랜 한도 얼마예요"
    answer: "Cloudflare Workers 무료 플랜은 하루 10만 요청을 지원하고, CPU 시간은 요청당 10ms로 제한됩니다. 반면 Vercel Edge Function 무료 플랜은 월 50만 엣지 실행을 허용하므로, 트래픽 패턴이 일별로 고른지 월별로 집중되는지에 따라 비용 효율이 달라집니다."
  - question: "엣지 함수에서 jsonwebtoken 같은 npm 패키지 못 쓰는 이유"
    answer: "엣지 런타임은 완전한 Node.js 환경이 아니라 Web API 표준을 따르기 때문에, Node.js 내장 `crypto` 모듈에 의존하는 `jsonwebtoken` 같은 패키지는 그대로 동작하지 않습니다. 이 경우 Web Crypto API 기반의 대체 라이브러리로 교체하거나, Cloudflare Workers의 `nodejs_compat` 플래그를 활용하는 방식으로 리팩토링이 필요합니다."
---

엣지 함수를 처음 써본 개발자들이 공통으로 하는 말이 있어요. "콜드스타트가 없다고 했는데, 왜 첫 요청이 이렇게 느리죠?" Vercel Edge Function과 Cloudflare Workers는 둘 다 "콜드스타트 없음"을 내세우지만, 그 이유가 달라요. 같은 결론처럼 보여도 내부 구조가 다르면 실제 성능과 제약도 달라지는 셈이에요.

> **핵심 요약**
> - Cloudflare Workers는 V8 Isolate 기반으로 워커가 상시 준비 상태를 유지해, 콜드스타트가 구조적으로 발생하지 않는다.
> - Vercel Edge Function은 Next.js와의 통합 깊이와 글로벌 CDN 연동에서 우위를 가지지만, 런타임 제약(Node.js 일부 API 미지원)이 실무 병목이 되는 사례가 있다.
> - Cloudflare Workers의 무료 플랜은 일 10만 요청을 지원하고, Vercel Edge Function은 무료 플랜에서 월 50만 엣지 실행을 허용한다.
> - 실무에서는 Next.js 중심 팀이라면 Vercel, 멀티 프레임워크나 API 레이어 중심이라면 Cloudflare Workers가 현실적인 선택이다.

---

## 1. 엣지 컴퓨팅, 왜 지금 이 논쟁이 뜨거운가

전통적인 서버리스 함수의 고질병은 콜드스타트였어요. AWS Lambda 기준으로 Node.js 런타임의 콜드스타트는 평균 200~500ms, 최악의 경우 1~2초까지 튀는 경우도 있었죠. Lambda 함수가 완전히 warm 상태를 유지하려면 꾸준한 트래픽이나 Provisioned Concurrency 설정이 필요했고, 이건 곧 비용 문제로 이어졌어요.

엣지 컴퓨팅은 이 문제를 "사용자 근처에서 실행"이라는 개념으로 돌파하려 했는데요. 그런데 2026년 시점에서 보면, 단순히 "가까운 곳에서 빠르게"가 전부가 아니에요. 런타임 구조 자체가 콜드스타트를 없애는 방식으로 설계되었는지가 핵심이거든요.

이 글은 두 플랫폼의 구조적 차이를 뜯어보고, 어떤 상황에서 뭘 골라야 하는지 실무 기준으로 정리해요.

---

## 2. 콜드스타트가 없는 진짜 이유

### V8 Isolate: Cloudflare Workers의 구조적 장점

Cloudflare Workers의 핵심은 V8 Isolate예요. 일반적인 서버리스 함수가 요청마다 컨테이너나 프로세스를 띄우는 것과 달리, Workers는 V8 JavaScript 엔진 위에서 격리된 실행 컨텍스트를 만들어요. 컨테이너 기동이 없으니 콜드스타트가 구조적으로 존재할 수 없어요.

Morph의 2026년 엣지 컴퓨팅 비교 리포트에 따르면, Cloudflare Workers의 p50 응답 시간은 약 5ms 수준이고, 전 세계 300개 이상의 PoP에서 워커가 상시 대기 상태를 유지해요. 격리 단위가 프로세스가 아닌 Isolate이기 때문에, 동시에 수천 개의 요청을 처리해도 메모리 오버헤드가 작아요.

단, 트레이드오프가 있어요. V8 Isolate는 Node.js 런타임이 아니라 Web API 표준을 따르는 환경이에요. `fs`, `path` 같은 Node.js 내장 모듈을 그냥 쓸 수 없고, 특정 npm 패키지가 동작하지 않을 수 있어요.

### Vercel Edge Function: Next.js와의 통합에 베팅

Vercel Edge Function도 내부적으로 V8 Isolate 기반이에요. 그래서 콜드스타트 없음의 이유는 같아요. 그런데 Vercel이 차별화하는 지점은 다른 데 있어요.

Next.js `middleware.ts`, `edge` 런타임을 쓰는 API Route, App Router의 서버 컴포넌트 스트리밍 — 이 모든 게 Vercel Edge Function 위에서 자연스럽게 돌아요. `export const runtime = 'edge'` 한 줄로 엣지 실행이 되거든요. 팀이 Next.js 중심으로 돌아간다면, 이건 꽤 큰 생산성 차이예요.

반면, Vercel 엣지 환경에서는 Node.js 호환성이 Workers보다 더 제한적인 경우가 있어요. 2025년 말 기준으로 일부 Web Crypto API와 Fetch API를 지원하도록 확장했지만, 여전히 완전한 Node.js 환경은 아니에요.

---

## 3. 실무에서 드러나는 차이점

### 성능 비교: 수치로 보면

| 비교 항목 | Vercel Edge Function | Cloudflare Workers |
|-----------|---------------------|-------------------|
| 콜드스타트 | 없음 (V8 Isolate) | 없음 (V8 Isolate) |
| p50 응답시간 | ~10-15ms | ~5ms |
| PoP 수 | 100+ (Vercel CDN) | 300+ |
| 런타임 | Edge Runtime (Node.js 서브셋) | Workers Runtime (Web API) |
| 무료 한도 | 월 50만 실행 | 일 10만 요청 |
| 메모리 한도 | 128MB | 128MB |
| CPU 시간 | 50ms/요청 | 10ms/요청 (무료), 50ms (유료) |
| Next.js 통합 | 네이티브 | 별도 설정 필요 |
| 로컬 개발 환경 | Next.js DevServer | Miniflare |

### Node.js 호환성: 실제로 뭐가 안 되나

가장 많이 막히는 부분은 npm 패키지 의존성이에요. 예를 들어, `jsonwebtoken` 같은 라이브러리는 Node.js 내장 `crypto` 모듈에 의존하는데, 엣지 환경에서는 Web Crypto API로 대체해야 해요. Cloudflare Workers는 `nodejs_compat` 플래그를 켜면 일부 Node.js API를 쓸 수 있게 해주는데, Vercel 엣지 환경은 이 방식이 다르게 동작해요.

실무적으로 보면, Node.js 생태계에 깊이 의존하는 백엔드 로직을 엣지로 옮길 때 두 플랫폼 모두 리팩토링이 필요해요. 차이는 Cloudflare가 호환성 레이어를 더 공격적으로 확장하고 있다는 거예요.

### 가격 구조: 규모가 커지면 달라져요

Cloudflare Workers의 유료 플랜(월 $5)은 월 1,000만 요청을 포함해요. Vercel은 Pro 플랜 기준으로 엣지 함수 실행이 월 100만 건까지 포함되고, 초과분은 100만 건당 과금 구조예요. 트래픽이 많은 API 서버라면 Cloudflare Workers가 비용 면에서 유리한 경우가 많아요.

---

## 4. 어떤 팀이 뭘 골라야 하는가

**Next.js 팀이라면 Vercel이 자연스러운 선택이에요.** `middleware.ts`로 인증, A/B 테스트, 지역 기반 라우팅을 엣지에서 처리하는 패턴이 Vercel에서 가장 매끄럽게 돌아가요. 별도의 인프라 설정 없이 배포 파이프라인과 엣지 함수가 하나로 연결되는 게 큰 강점이에요.

**API 레이어나 멀티 프레임워크 환경이라면 Cloudflare Workers를 봐야 해요.** Workers는 특정 프레임워크에 묶이지 않아요. Hono 같은 경량 프레임워크와 조합하면 아주 빠른 API 서버를 낮은 비용으로 운영할 수 있어요. KV, R2, D1 같은 Cloudflare 자체 스토리지와의 연동도 Workers 생태계 안에서 자연스럽게 이어져요.

그리고 두 플랫폼을 같이 쓰는 팀도 있어요. Vercel에서 Next.js 프론트엔드를 운영하면서, 고빈도 API 요청은 Cloudflare Workers로 처리하는 구성이 2026년 현재 꽤 현실적인 아키텍처예요.

결국 선택 기준은 하나로 수렴해요. **코드가 어디서 쓰이는지, 어떤 생태계에 묶여 있는지를 먼저 보세요.** 성능 수치는 두 번째 문제예요. 지금 팀에서 엣지 함수를 처음 도입한다면, 두 플랫폼의 무료 플랜을 동시에 써보는 걸 권해요. 직접 겪은 제약이 스펙 문서보다 훨씬 정확하게 선택 기준을 잡아줄 거예요.

## 참고자료

1. [Cloudflare Workers vs Vercel 2026: Edge Compute Compared | Morph](https://www.morphllm.com/comparisons/cloudflare-workers-vs-vercel)
2. [r/webdev on Reddit: Vercel Edge vs Cloudflare Workers: My Benchmarks Show Theo (T3) Might Be Fooling](https://www.reddit.com/r/webdev/comments/1ntfake/vercel_edge_vs_cloudflare_workers_my_benchmarks/)
3. [Spinny](https://www.spinny.dev/en/blog/serverless-aws-lambda-vercel-cloudflare)


---

*Photo by [NASA](https://unsplash.com/@nasa) on [Unsplash](https://unsplash.com/photos/photo-of-outer-space-Q1p7bh3SHj8)*
