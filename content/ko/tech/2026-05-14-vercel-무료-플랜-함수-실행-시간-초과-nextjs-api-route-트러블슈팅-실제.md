---
title: "Vercel 무료 플랜 함수 실행 시간 초과: Next.js API Route 트러블슈팅 실제 사례"
date: 2026-05-14T21:02:39+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-web", "vercel", "next.js", "api", "JavaScript"]
description: "Vercel Hobby 플랜 10초 실행 제한으로 프로덕션에서 Task timed out 에러가 터진 경험, 있으신가요? Next.js API route 타임아웃 원인 패턴과 플랜 업그레이드 없이 해결하는 방법을 실제 사례로"
image: "/images/20260514-vercel-무료-플랜-함수-실행-시간-초과-nextj.webp"
technologies: ["JavaScript", "Next.js", "Node.js", "AWS", "Vercel"]
faq:
  - question: "Vercel 무료 플랜 함수 실행 시간 초과 Next.js API route 어떻게 해결하나요"
    answer: "Vercel Hobby 플랜은 Serverless Function 실행 시간을 최대 10초로 제한하며, 이를 넘기면 Task timed out 에러가 발생합니다. Vercel 무료 플랜 함수 실행 시간 초과 Next.js API route 트러블슈팅 실제 사례에서 가장 효과적인 해결책은 순차 await를 Promise.all로 병렬 처리하거나 Edge Runtime으로 전환하는 것입니다. 플랜 업그레이드 없이도 코드 구조 개선만으로 대부분의 타임아웃 문제를 해결할 수 있습니다."
  - question: "Vercel Hobby 플랜 10초 제한 Pro 플랜 업그레이드 해야 하나요"
    answer: "Vercel Pro 플랜은 최대 60초까지 함수 실행을 허용하지만, 업그레이드가 근본적인 해결책이 아닌 경우가 절반 이상입니다. 타임아웃의 원인이 순차 API 호출, DB 연결 풀 미구성, 무거운 패키지 로딩 같은 코드 구조 문제라면 로직 자체를 먼저 개선하는 것이 더 효과적입니다."
  - question: "Next.js API route 로컬에서는 정상인데 Vercel 배포하면 타임아웃 나는 이유"
    answer: "로컬 환경은 서버가 이미 실행 중인 상태라 콜드 스타트 비용이 없지만, Vercel Serverless Function은 요청마다 컨테이너가 새로 뜨면서 1-2초의 콜드 스타트가 추가됩니다. 여기에 외부 API 순차 호출이나 무거운 패키지 로딩이 겹치면 로컬에서 2-3초이던 작업이 Vercel에서 10초를 쉽게 초과하게 됩니다."
  - question: "Prisma Vercel 배포 연결 느린 이유 해결 방법"
    answer: "Vercel Serverless Function 환경에서 Prisma를 사용할 때 전역 싱글턴 패턴을 적용하지 않으면 요청마다 새로운 DB 연결을 생성하며 1-3초가 낭비됩니다. Vercel 무료 플랜 함수 실행 시간 초과 Next.js API route 트러블슈팅 실제 사례에서도 DB 연결 풀 미구성이 타임아웃의 주요 원인으로 지목되며, PrismaClient를 전역 싱글턴으로 관리하는 것으로 해결할 수 있습니다."
  - question: "Vercel Edge Runtime Serverless Function 차이점 뭔가요"
    answer: "Serverless Function은 Node.js 런타임 기반으로 콜드 스타트가 1-2초 발생하고 Hobby 플랜 기준 최대 10초 실행 제한이 있습니다. Edge Runtime은 V8 기반으로 동작해 콜드 스타트가 거의 없고 응답 속도가 빠르지만, Node.js 전용 API나 일부 npm 패키지를 사용할 수 없다는 제약이 있습니다."
---

배포는 잘 됐어요. 로컬에서도 멀쩡히 돌아가요. 그런데 Vercel에 올리니까 딱 10초 만에 `Task timed out` 에러가 터졌어요. 그것도 프로덕션에서요.

사이드 프로젝트를 Vercel Hobby 플랜으로 운영하다 보면 꽤 자주 마주치는 장벽이에요. 이 함수 실행 시간 초과 문제가 Next.js API route 트러블슈팅에서 가장 흔한 검색 키워드 중 하나가 됐을 정도예요.

이 글에서는 Vercel 무료 플랜의 실행 시간 제한 구조를 뜯어보고, 실제로 어떤 패턴이 타임아웃을 유발하는지, 그리고 플랜 업그레이드 없이 해결할 수 있는 방법을 정리할게요.

> **핵심 요약**
> - Vercel Hobby 플랜은 Serverless Function 실행 시간을 최대 10초로 제한해요. 2026년 현재도 변경되지 않았어요.
> - Next.js API route에서 외부 API 호출, DB 쿼리, 파일 처리가 겹치면 로컬에서 2-3초이던 작업이 Vercel 환경에서 10초를 쉽게 넘겨요.
> - Edge Runtime으로 전환하거나 작업을 비동기 분리하면 플랜 업그레이드 없이도 타임아웃을 피할 수 있어요.
> - Pro 플랜(최대 60초)으로 올리는 건 근본 해결이 아닐 수 있어요. 로직 자체를 손봐야 하는 경우가 절반 이상이에요.

---

## Vercel Hobby 플랜의 실행 시간 제한, 정확히 어디까지인가요?

Vercel 공식 문서(Vercel Docs, 2026) 기준 플랜별 함수 실행 시간 상한은 이래요.

| 플랜 | 최대 실행 시간 | 메모리 | 월 실행 횟수 |
|------|--------------|--------|------------|
| **Hobby (무료)** | 10초 | 1,024 MB | 100,000회 |
| **Pro** | 60초 | 3,008 MB | 1,000,000회 |
| **Enterprise** | 900초 | 3,008 MB | 무제한 |

10초. 생각보다 짧죠. 로컬에서 개발할 때는 느끼지 못하다가 Vercel에 배포하는 순간 바로 체감하는 숫자예요.

그런데 왜 이런 제한이 있을까요? Serverless Function은 요청이 들어올 때만 컨테이너가 뜨고, 응답을 보내면 내려가는 구조예요. 긴 실행 시간을 허용할수록 Vercel 입장에서 인프라 비용이 올라가요. 무료 사용자에게 10초 제한을 두는 건 사업적으로 당연한 선택이에요.

문제는 Next.js API route가 이 제한을 얼마나 쉽게 넘기느냐예요.

---

## 어떤 코드 패턴이 10초를 넘기는가: 실제 사례 분석

### 외부 API 순차 호출의 함정

가장 흔한 패턴이에요. 이런 코드 본 적 있으시죠?

```javascript
// pages/api/dashboard.js
export default async function handler(req, res) {
  const user = await fetchUser(req.query.id);       // ~1.5초
  const orders = await fetchOrders(user.id);         // ~2.0초
  const analytics = await fetchAnalytics(user.id);  // ~3.5초
  const recommendations = await fetchRecommendations(user.id); // ~4.0초

  res.json({ user, orders, analytics, recommendations });
}
```

로컬 환경에서는 각 API 응답이 빨라서 총 7-8초면 끝나요. 그런데 Vercel의 콜드 스타트가 1-2초 추가되면 바로 10초를 넘겨버려요.

Vercel 무료 플랜에서 Next.js API route 트러블슈팅을 할 때 가장 먼저 의심해야 할 패턴이 이거예요. 순차 `await`가 네 개 이상 있으면 무조건 점검 대상이에요.

### 콜드 스타트 + 무거운 패키지

`aws-sdk`, `puppeteer`, `pdf-lib` 같은 패키지를 API route에서 import하면 컨테이너가 뜰 때 패키지 로딩 시간이 붙어요. Vercel Hobby 플랜의 경우 콜드 스타트에서 이 로딩 시간이 2-4초 추가될 수 있어요. 로컬에서는 서버가 이미 실행 중이라 이 비용을 체감 못하는 거예요.

### DB 연결 풀 미구성

PlanetScale, Supabase 같은 외부 DB를 연결할 때 연결 풀을 제대로 설정하지 않으면 요청마다 새 연결을 만들어요. 연결 설정에만 1-3초가 날아가요. Prisma를 쓰는 경우 전역 싱글턴 패턴을 안 쓰면 이 문제가 생기고, Vercel 무료 플랜 함수 실행 시간 초과의 원인이 여기서 나오는 경우가 꽤 많아요.

---

## 플랜 업그레이드 없이 해결하는 방법 3가지

### 방법 1: Promise.all로 병렬 처리

앞서 본 순차 호출 코드는 이렇게 바꿀 수 있어요.

```javascript
export default async function handler(req, res) {
  const user = await fetchUser(req.query.id);

  const [orders, analytics, recommendations] = await Promise.all([
    fetchOrders(user.id),
    fetchAnalytics(user.id),
    fetchRecommendations(user.id)
  ]);

  res.json({ user, orders, analytics, recommendations });
}
```

3개 API를 동시에 쏘니까 가장 느린 것(4.0초) 하나만 기다리면 돼요. 총 실행 시간이 7-8초에서 5-6초대로 떨어지고, 콜드 스타트 1-2초를 더해도 10초 안에 끝날 가능성이 높아지죠.

### 방법 2: Edge Runtime 전환

Next.js의 Edge Runtime은 V8 기반으로 동작하고, Serverless Function과 달리 콜드 스타트가 거의 없어요. Vercel 공식 문서에 따르면 Edge Runtime은 응답 시작까지 수십 밀리초 수준이에요.

```javascript
export const config = {
  runtime: 'edge',
};

export default async function handler(req) {
  // 가벼운 로직만
  return new Response(JSON.stringify({ ok: true }));
}
```

단점도 있어요. Node.js API를 못 쓰고, `fs`, `child_process` 같은 모듈이 안 돼요. DB 직접 연결도 제한적이에요. 가벼운 데이터 변환이나 캐시 레이어 역할로 쓸 때 딱 맞아요.

### 방법 3: 작업을 비동기로 분리

10초 안에 못 끝내는 작업이라면 응답을 먼저 돌려주고, 실제 처리는 백그라운드에서 하는 패턴을 쓸 수 있어요. Vercel 공식 문서에서 소개하는 방식으로, Upstash QStash 같은 큐 서비스와 연계하면 돼요. 응답은 즉시 `202 Accepted`로 보내고, 큐가 처리를 이어가는 구조예요.

---

## Hobby vs Pro: 언제 업그레이드가 맞는가

| 기준 | Hobby 유지 권장 | Pro 업그레이드 권장 |
|------|---------------|-------------------|
| 사용 목적 | 사이드 프로젝트, 포트폴리오 | 실서비스, 유료 고객 |
| 타임아웃 원인 | 코드 최적화로 해결 가능 | 60초 이상 필요한 ML 추론, 파일 변환 |
| 예산 | $0 | 월 $20 |
| SLA 필요 여부 | 불필요 | 필요 |

업그레이드를 고민하기 전에 먼저 확인할 게 있어요. Vercel 대시보드의 **Functions 탭**에서 실행 시간 로그를 보면 어느 route가 얼마나 걸리는지 정확히 나와요. 10초 중 9초를 외부 API가 먹고 있다면, 그건 업그레이드로 해결할 문제가 아니에요. 해당 API 호출 자체를 줄이거나 캐싱을 붙여야 해요.

반대로 이미지 리사이징, PDF 생성, 대용량 CSV 처리처럼 작업 자체가 무거운 경우엔 Pro 플랜의 60초도 부족할 수 있어요. 이럴 땐 해당 작업을 Vercel 바깥으로 빼는 게 맞아요. AWS Lambda의 최대 15분, Cloudflare Workers의 CPU 시간 제한 구조와 비교해보면 Vercel이 장거리 작업에 맞는 플랫폼이 아니라는 게 보여요.

---

## 정리: Vercel 무료 플랜에서 살아남는 법

Vercel 무료 플랜의 함수 실행 시간 초과는 Next.js API route 트러블슈팅 중에서도 해결 방법이 명확한 편이에요.

- **먼저 Vercel Functions 탭에서 실제 실행 시간을 확인하세요.** 추측하지 말고요.
- 순차 `await`가 3개 이상이면 `Promise.all`로 바꿔요.
- 무거운 패키지를 쓴다면 동적 import나 Edge Runtime 전환을 검토해요.
- DB 연결 풀 설정이 빠져 있는지 체크해요. Prisma를 쓴다면 전역 싱글턴 패턴은 필수예요.
- 위 세 가지를 다 해도 안 된다면, 그때 Pro 플랜을 고민하거나 작업을 큐로 분리하는 구조를 잡아요.

사이드 프로젝트에서 Vercel 무료 플랜은 충분히 강력한 선택지예요. 다만 Serverless의 한계를 이해하고 코드를 그 구조에 맞게 짜야 해요. 로컬에서 잘 돌아간다고 Vercel에서도 잘 돌아가는 건 아니거든요.

지금 타임아웃이 나고 있다면, Vercel 대시보드 Functions 탭 먼저 열어보세요. 범인이 어디 있는지 금방 보일 거예요.

## 참고자료

1. [Vercel을 이용한 무료 웹 배포 이용해보기 - 코딩은재밌어](https://allinfor.tistory.com/76)
2. [Vercel 무료 배포 실전 가이드 2026 — Hobby 플랜으로 사이드 프로젝트 운영하기 | DevFinance](https://www.devfinance.cloud/tech/vercel-free-deploy)
3. [Min-inter](https://min-inter.co.kr/wiki/vercel-vibe-coding-deploy-platform-guide)


---

*Photo by [Surface](https://unsplash.com/@surface) on [Unsplash](https://unsplash.com/photos/a-laptop-computer-sitting-on-top-of-a-white-table-F4ottWBnCpM)*
