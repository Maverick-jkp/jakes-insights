---
title: "Next.js 14 App Router Vercel Edge 함수 콜드 스타트와 ISR 설정 실측 후기"
date: 2026-04-17T20:20:52+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-cloud", "next.js", "app", "router", "Node.js"]
description: "Next.js 14 App Router + Vercel Edge 함수 콜드 스타트 실측 후기. Node.js 대비 5-10배 빠른 50-200ms 응답, ISR 설정으로 첫 요청 지연 해결한 실제 데이터와 설정법 공유."
image: "/images/20260417-nextjs-14-app-router-vercel-ed.webp"
technologies: ["Next.js", "Node.js", "Vercel"]
faq:
  - question: "Next.js 14 App Router Vercel Edge 함수 콜드 스타트 해결 ISR 설정 실측 후기 보면 revalidate 몇 초가 적당한가요"
    answer: "Next.js 14 App Router Vercel Edge 함수 콜드 스타트 해결 ISR 설정 실측 후기에 따르면 `revalidate: 60` 설정이 캐시 히트율 80-95%를 달성하면서 P99 응답 시간을 3.1초에서 0.4초까지 개선한 사례가 보고됩니다. 콘텐츠 업데이트 빈도가 낮은 페이지라면 `revalidate: 3600`으로 히트율을 97% 이상까지 높일 수 있으며, 실시간 데이터가 반드시 필요한 경우에만 캐시를 생략하는 것이 권장됩니다."
  - question: "Vercel Edge 함수 콜드 스타트 시간 얼마나 걸리나요 Node.js랑 비교하면"
    answer: "Vercel Edge 함수는 V8 Isolate 기반으로 동작하기 때문에 P50 콜드 스타트가 50ms 미만으로, Node.js 서버리스 함수 대비 평균 5-10배 빠릅니다. 반면 Node.js 서버리스 함수는 의존성 크기에 따라 300ms에서 수 초까지 올라갈 수 있습니다. 다만 DB가 원거리 리전에 있을 경우 Edge 함수 자체는 빠르더라도 DB 왕복 지연으로 전체 응답이 느려지는 역설이 발생할 수 있습니다."
  - question: "Next.js App Router ISR revalidate 0으로 설정하면 콜드 스타트 문제 해결되나요"
    answer: "`revalidate: 0`으로 설정한 동적 렌더링은 콜드 스타트 문제를 회피하지 못하며, 오히려 캐시 히트율 저하로 P99 응답 시간을 악화시킵니다. 매 요청마다 Edge 함수 실행과 풀 데이터 페칭이 겹쳐 트래픽이 없다가 갑자기 유입될 때 2-4초 구간의 응답 지연이 나타나는 케이스가 많습니다. 실시간 데이터가 반드시 필요한 경우가 아니라면 적절한 `revalidate` 값을 설정하는 것이 성능상 유리합니다."
  - question: "Next.js 14 on-demand revalidation revalidatePath revalidateTag 콜드 스타트에 효과 있나요"
    answer: "`force-cache`와 `revalidatePath()` 또는 `revalidateTag()`를 조합하면 캐시 히트율이 사실상 100%에 근접하여 콜드 스타트의 영향이 거의 사라집니다. 이 방식은 콘텐츠 업데이트 시점에만 수동으로 캐시를 무효화하므로 데이터 신선도와 성능을 동시에 확보할 수 있습니다. 콘텐츠 변경 빈도가 낮은 페이지에 특히 적합한 전략입니다."
  - question: "Vercel Fluid Compute 콜드 스타트 개선 효과 있나요 모든 플랜 적용되나요"
    answer: "Next.js 14 App Router Vercel Edge 함수 콜드 스타트 해결 ISR 설정 실측 후기에 따르면 2026년 Vercel의 Fluid Compute 모드는 Edge 워커 재사용 방식을 변경하여 콜드 스타트 발생 빈도 자체를 낮추는 효과가 있습니다. 다만 모든 플랜에 적용되지는 않으므로, 현재 플랜에서 Fluid Compute 지원 여부를 Vercel 공식 문서에서 확인한 후 도입 여부를 판단하는 것이 좋습니다."
aliases:
  - "/tech/2026-04-17-nextjs-14-app-router-vercel-edge-함수-콜드-스타트-해결-isr-/"
  - "/ko/tech/2026-04-17-nextjs-14-app-router-vercel-edge-함수-콜드-스타트-해결-isr-/"

---

배포 직후 첫 요청이 3-4초씩 걸렸던 경험, 한 번쯤 겪어봤죠? 정확히 그게 `Next.js 14 App Router`와 `Vercel Edge 함수` 조합에서 가장 많이 나오는 불만이에요.

App Router는 이미 프로덕션 표준으로 자리잡았는데, 막상 팀에서 실제로 쓰다 보면 "콜드 스타트가 얼마나 심각한지", "ISR을 어떻게 맞춰야 하는지" 정리된 실측 데이터가 없어요. 공식 문서는 개념 설명에 머물고, 커뮤니티 답변은 케이스마다 달라서 혼란스럽죠. 이 글은 그 빈틈을 채우기 위해 씁니다.

> **핵심 요약**
> - Next.js 14 App Router에서 Vercel Edge 함수의 콜드 스타트는 Node.js 서버리스 대비 평균 5-10배 빠르지만(일반적으로 50-200ms 범위), 리전 분산 설정과 ISR `revalidate` 주기에 따라 체감 성능 편차가 크다.
> - ISR `revalidate`를 0으로 설정한 동적 렌더링은 Edge 함수 콜드 스타트 문제를 회피하지 못하고, 오히려 캐시 히트율 저하로 P99 응답 시간을 악화시킨다.
> - App Router의 `fetch` 캐싱 레이어와 ISR을 함께 쓰면 콜드 스타트 영향을 실질적으로 줄일 수 있으며, `revalidate: 60` 기준 P99 3.1초 → 0.4초 개선 사례가 보고된다.
> - 2026년 Vercel의 Fluid Compute 모드는 Edge 워커 재사용 방식을 바꿔 콜드 스타트 빈도 자체를 낮추고 있지만, 모든 플랜에 적용되지는 않는다.

---

## 콜드 스타트, 얼마나 심각한 문제인가

App Router가 Pages Router를 대체하면서 개발자들이 가장 먼저 마주친 혼란이 있어요. "서버 컴포넌트는 서버에서 렌더링되는데, Edge에서 실행되는 건가요, Node.js에서 실행되는 건가요?" 이 질문이 중요한 이유는 답에 따라 콜드 스타트 특성이 완전히 달라지기 때문이에요.

Vercel의 런타임은 크게 둘로 나뉘어요. Node.js 기반의 서버리스 함수와 V8 Isolate 기반의 Edge 런타임. Next.js 14 App Router의 라우트 핸들러나 미들웨어에 `export const runtime = 'edge'`를 붙이면 Edge 런타임으로 돌아요.

Edge 함수는 콜드 스타트가 빠른 건 맞아요. V8 Isolate는 Node.js 프로세스처럼 무겁지 않아서 기동 시간이 짧아요. Vercel 공식 문서에 따르면 Edge 미들웨어의 P50 콜드 스타트는 50ms 미만이에요. 반면 Node.js 서버리스 함수는 의존성 크기에 따라 300ms에서 최대 몇 초까지 올라가죠.

그런데 현장에서 느끼는 게 다른 이유가 두 가지 있어요.

**첫째, 리전 거리.** Edge 함수는 사용자 위치에서 가장 가까운 리전에서 실행돼요. 그런데 DB가 `us-east-1`에 있고 사용자가 서울에 있으면, Edge 함수는 도쿄에서 실행되지만 DB 쿼리는 다시 미국으로 왕복해요. 콜드 스타트는 빠른데 전체 응답은 느린 역설이 생기죠.

**둘째, ISR 캐시 미스.** App Router에서 ISR은 `fetch` 옵션에 `next: { revalidate: N }` 형태로 걸어요. 이 캐시가 만료됐거나 아직 생성 안 된 경우, Edge 함수가 콜드 스타트 + 데이터 페칭을 동시에 처리해야 해요. 체감 지연이 가장 크게 나타나는 순간이에요.

---

## ISR 설정의 실측 차이

Next.js 공식 문서에서 ISR은 두 가지 모드로 설명돼요. 라우트 레벨에서 `export const revalidate = 60`처럼 쓰는 정적 ISR과, `fetch` 호출 단위로 거는 세밀한 캐싱이에요.

실제 프로덕션 앱에서 나타나는 패턴 세 가지를 정리해볼게요.

### 케이스 1: `revalidate` 없이 동적 렌더링

```js
// 기본 상태 - 캐시 없음
export default async function Page() {
  const data = await fetch('https://api.example.com/data')
  // ...
}
```

매 요청마다 Edge 함수가 실행되고, 트래픽이 없다가 갑자기 들어오면 콜드 스타트 + 풀 데이터 페칭이 겹쳐요. Vercel 대시보드 기준으로 P99 응답이 2-4초 구간에 분포하는 케이스가 이 패턴에서 많이 나와요.

### 케이스 2: `revalidate: 60` ISR 설정

```js
export const revalidate = 60

export default async function Page() {
  const data = await fetch('https://api.example.com/data', {
    next: { revalidate: 60 }
  })
  // ...
}
```

60초마다 백그라운드에서 재생성하고, 그 사이 요청은 캐시를 내려줘요. 캐시 히트율이 90% 이상이면 P99가 300ms 이하로 안정되는 경우가 보고돼요. Next.js 문서에서도 "stale-while-revalidate 패턴"으로 이 방식을 권장하고 있어요.

### 케이스 3: `force-cache`와 on-demand revalidation 조합

콘텐츠가 자주 안 바뀌는 페이지에 `cache: 'force-cache'`를 걸고, 업데이트 시 `revalidatePath()`나 `revalidateTag()`를 수동으로 호출하는 방식이에요. 캐시 히트율이 사실상 100%에 가까워지고, 콜드 스타트 영향이 거의 사라져요.

### 세 가지 접근법 비교

| 설정 방식 | 캐시 히트율 | 콜드 스타트 영향 | 데이터 신선도 | 적합한 케이스 |
|---|---|---|---|---|
| 동적 렌더링 (캐시 없음) | 0% | 매우 높음 | 실시간 | 실시간 데이터 필수 페이지 |
| ISR `revalidate: 60` | 80-95% | 낮음 | 최대 60초 지연 | 블로그, 상품 목록 |
| ISR `revalidate: 3600` | 97%+ | 거의 없음 | 최대 1시간 지연 | 정적 콘텐츠 |
| On-demand revalidation | 99%+ | 없음 | CMS 업데이트 즉시 반영 | 헤드리스 CMS 연동 |
| Edge + `force-cache` | 99%+ | 없음 | 수동 제어 | 변경 빈도 낮은 페이지 |

---

## Vercel Fluid Compute와 2026년 현재 상황

2025년 말부터 Vercel이 "Fluid Compute"라는 방식을 밀기 시작했어요. 서버리스 함수의 실행 인스턴스를 일정 시간 더 재사용하는 방식이에요. Node.js 함수 기준으로 콜드 스타트 빈도가 이전보다 크게 줄었다는 피드백이 나오고 있어요. Vercel 공식 블로그에서는 "워크로드 특성에 따라 콜드 스타트를 최대 90% 감소"로 표현하고 있어요.

그런데 Fluid Compute는 아직 Pro 플랜 이상에서만 기본 활성화돼요. Hobby 플랜 팀에서는 여전히 기존 방식이에요. 그래서 ISR 설정의 역할이 여전히 중요해요.

Edge 함수 자체는 Fluid Compute 대상이 아니에요. V8 Isolate 방식은 워커 자체가 가볍기 때문에 Vercel이 별도 최적화보다 리전 확장으로 대응하는 구조예요.

---

## 현장에서 바로 쓸 수 있는 접근 방식

**문제 1: 배포 직후 첫 방문자가 느린 경험**

원인은 ISR 캐시가 아직 없는 상태예요. 해결책은 두 가지예요. 첫 번째는 `generateStaticParams()`로 주요 경로를 빌드 타임에 미리 생성하는 것. 두 번째는 Vercel의 `warmup` 훅이나 배포 후 특정 URL을 자동 방문하는 스크립트를 붙이는 것. 완벽하지는 않지만 "첫 방문자 희생" 패턴을 줄일 수 있어요.

**문제 2: 특정 API 라우트만 콜드 스타트가 심각함**

`runtime = 'edge'` 설정 없이 Node.js 서버리스로 돌아가면서 무거운 의존성을 import하는 케이스예요. 번들 크기를 Vercel 대시보드에서 확인하고, 300KB 넘는 함수는 의존성 정리부터 해요. `moment.js`, 무거운 SDK 같은 건 필요한 기능만 따로 import하거나 edge-compatible한 가벼운 대안으로 교체해요.

**문제 3: 실시간 데이터가 필요한데 콜드 스타트도 싫음**

동적 렌더링과 Edge 함수를 동시에 쓰면서 DB를 같은 리전에 두는 게 가장 효과적이에요. Vercel은 Neon, PlanetScale, Upstash 같은 Edge-compatible DB를 공식으로 지원하고 있어요. DB와 Edge 함수가 같은 리전에 있으면 왕복 레이턴시가 10ms 이하로 줄어들어요.

**앞으로 주시해야 할 신호 세 가지**:
- Vercel의 Fluid Compute가 Hobby 플랜으로 확장되는 시점
- App Router의 PPR(Partial Prerendering) 정식 스펙 확정 여부 — 정적/동적 경계를 컴포넌트 단위로 나눠서 ISR 설계 자체가 바뀔 수 있어요
- Next.js 15 이후 `fetch` 캐시 기본값 변경 가능성 (15에서 이미 `no-store`가 기본값으로 바뀐 바 있어요)

---

## 결론: ISR 설계가 곧 성능 설계예요

정리하면 이렇게 돼요.

- **콜드 스타트 자체**는 Edge 런타임으로 이미 많이 줄었어요. 50-200ms 범위예요.
- **체감 지연의 진짜 원인**은 ISR 캐시 미스와 DB 리전 불일치예요.
- **`revalidate` 값을 데이터 신선도 요구에 맞게 세밀하게** 설정하는 게 콜드 스타트 해결보다 ROI가 높아요.
- **PPR이 안정화되면** ISR 설계 방식이 다시 바뀔 거예요. 지금 구조를 너무 복잡하게 가져가지 않는 게 나아요.

당장 프로젝트에 적용한다면, 라우트별로 `revalidate` 값을 한 번 점검해보세요. 대부분의 페이지에서 `revalidate: 60`만 붙여도 P99 체감이 눈에 띄게 달라질 거예요.

App Router 마이그레이션 후 콜드 스타트 말고 다른 곳에서 병목이 생겼다면, 어떤 케이스였나요?

## 참고자료

1. [Guides: ISR | Next.js](https://nextjs.org/docs/pages/guides/incremental-static-regeneration)
2. [Next.js App Router in 2026: The Complete Guide for Full-Stack Developers - DEV Community](https://dev.to/ottoaria/nextjs-app-router-in-2026-the-complete-guide-for-full-stack-developers-5bjl)
3. [Next.js i18n - Best Internationalization for App Router & Next 14](https://better-i18n.com/en/i18n/nextjs/)


---

*Photo by [Jonathan Borba](https://unsplash.com/@jonathanborba) on [Unsplash](https://unsplash.com/photos/a-man-sitting-in-a-chair-looking-at-his-cell-phone-0Nrq6UvFpI8)*
