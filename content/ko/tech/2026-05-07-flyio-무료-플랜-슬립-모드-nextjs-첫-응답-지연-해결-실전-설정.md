---
title: "Fly.io 무료 플랜 슬립 모드로 인한 Next.js 첫 응답 지연 해결 실전 설정"
date: 2026-05-07T21:08:53+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-web", "Fly.io \ubb34\ub8cc \ud50c\ub79c \uc2ac\ub9bd \ubaa8\ub4dc Next.js \uccab \uc751\ub2f5 \uc9c0\uc5f0 \ud574\uacb0 \uc2e4\uc804 \uc124\uc815", "TypeScript", "React"]
description: "Fly.io 무료 플랜 슬립 모드로 Next.js 첫 응답이 8~15초 지연되는 문제, 원인과 실전 해결 설정을 단계별로 정리했습니다. Cold Start 없이 빠른 응답 유지하는 방법을 확인하세요."
image: "/images/20260507-flyio-무료-플랜-슬립-모드-nextjs-첫-응답-.webp"
technologies: ["TypeScript", "React", "Next.js", "Docker", "Vercel"]
faq:
  - question: "Fly.io 무료 플랜 Next.js 첫 응답 느린 이유"
    answer: "Fly.io 무료 플랜은 약 5분간 트래픽이 없으면 컨테이너를 자동으로 슬립 상태로 전환하기 때문에, 다음 요청 시 VM 부팅부터 Next.js 앱 초기화까지 평균 8~15초의 Cold Start 지연이 발생해요. 이 문제는 Fly.io 무료 플랜 슬립 모드 Next.js 첫 응답 지연 해결 실전 설정을 통해 외부 핑이나 경량 헬스체크 엔드포인트로 해결할 수 있어요."
  - question: "Fly.io 무료 플랜에서 슬립 모드 비활성화 방법"
    answer: "Fly.io 무료 플랜 슬립 모드 Next.js 첫 응답 지연 해결 실전 설정에서 가장 효과적인 무료 방법은 Cron-job.org 같은 외부 서비스로 5분 이내 주기마다 앱의 `/api/ping` 엔드포인트에 HTTP 요청을 보내는 거예요. 이렇게 하면 컨테이너가 슬립 상태로 진입하기 전에 계속 깨어있는 상태를 유지할 수 있어요."
  - question: "Fly.io fly.toml min_machines_running 설정 방법"
    answer: "fly.toml 파일에서 `auto_stop_machines = false`와 `min_machines_running = 1`을 함께 설정하면 트래픽이 없어도 최소 1개의 머신이 항상 켜진 상태로 유지돼요. 단, 이 설정은 유료 플랜($5/월~)에서만 작동하며, 무료 플랜에서는 적용이 되지 않아요."
  - question: "Next.js 헬스체크 api/ping 엔드포인트 만드는 방법"
    answer: "`app/api/ping/route.ts` 파일을 생성하고 `export async function GET() { return new Response('ok', { status: 200 }); }` 코드만 추가하면 돼요. DB 쿼리나 렌더링 없이 단순히 응답만 반환하기 때문에 컨테이너를 깨워두는 용도로 사용해도 앱에 부담이 없어요."
  - question: "Cold Start 지연 줄이는 방법 Next.js 스트리밍"
    answer: "Cold Start 자체를 없애기 어렵다면 Next.js App Router의 Suspense와 스트리밍 렌더링을 활용해 체감 지연을 줄이는 방법이 현실적인 대안이에요. 데이터가 느리게 로드되는 영역에 스켈레톤 UI를 적용하면 페이지 자체는 빠르게 표시되고 데이터만 나중에 채워지는 방식으로 사용자 경험을 개선할 수 있어요."
---

무료로 Next.js 앱을 배포했는데, 첫 방문자가 8~15초를 기다려야 한다면? 그게 바로 Fly.io 무료 플랜 슬립 모드가 만드는 현실이에요.

Fly.io는 개인·사이드 프로젝트 개발자들에게 많이 쓰이는 배포 플랫폼이에요. Docker 컨테이너 기반으로 Next.js 앱을 올리기도 쉽고, 무료 플랜(Hobby Plan)이 있어 비용 부담도 없죠. 그런데 무료 플랜에는 치명적인 함정이 하나 있어요. 일정 시간 트래픽이 없으면 컨테이너가 자동으로 잠드는 슬립 모드(Sleep Mode)가 작동해요. 다음 요청이 들어오면 컨테이너를 새로 깨워야 하는데, 이게 첫 응답 지연(Cold Start)으로 이어지는 거예요.

이 글에서 다룰 내용을 미리 볼게요:

- 슬립 모드가 왜 발생하고, 얼마나 느려지는지
- 무료 플랜에서 쓸 수 있는 실전 해결법 세 가지
- 각 방법의 트레이드오프 비교
- 지금 당장 적용할 수 있는 설정 코드

> **핵심 요약**
> - Fly.io 무료 플랜은 약 5분간 트래픽이 없으면 컨테이너를 슬립 상태로 전환하며, 재시작 시 Next.js 앱 기준 평균 8~15초의 Cold Start 지연이 발생해요.
> - 외부 핑(Uptime Kuma, Cron-job.org 등)으로 5분 이내 주기로 헬스체크를 보내면 무료 플랜에서도 슬립을 막을 수 있어요.
> - Fly.io 유료 플랜($5/월~)에서는 `min_machines_running = 1` 설정으로 항상 켜진 상태를 보장할 수 있어요.
> - Next.js의 `/api/ping` 같은 경량 헬스체크 엔드포인트를 별도로 만들면, 앱 전체를 깨우는 비용 없이 컨테이너를 활성 상태로 유지할 수 있어요.
> - Cold Start 자체를 없애기 어렵다면, Next.js의 스트리밍 렌더링과 로딩 UI로 체감 지연을 줄이는 방법이 현실적 대안이에요.

---

## Fly.io 슬립 모드, 정확히 무슨 일이 일어나는 걸까요?

Fly.io는 앱을 Firecracker 기반의 마이크로VM 위에서 돌려요. 무료 플랜은 이 VM 인스턴스에 대한 상시 가동 비용을 받지 않는 대신, 일정 시간 유휴 상태면 자동으로 컨테이너를 내려버려요. 공식 문서에는 명시적 시간이 없지만, Reddit(`r/nextjs`) 커뮤니티와 실제 테스트 데이터를 보면 **약 5분** 이상 요청이 없으면 슬립 모드로 진입하는 패턴이 일관되게 관찰돼요.

문제는 그다음이에요. 슬립 상태에서 첫 요청이 들어오면 Fly.io는 VM을 다시 부팅해요. 이 과정에서 다음 단계가 순차적으로 일어나요:

1. **VM 부팅**: ~1~2초
2. **Docker 컨테이너 시작**: ~2~4초
3. **Next.js 앱 초기화**: ~3~8초 (앱 크기, 의존성에 따라 달라져요)

결국 사용자 입장에서는 화면이 완전히 하얀 채로 8초에서 길면 15초 이상 기다려야 해요. 포트폴리오 사이트나 데모 프로젝트를 처음 보여줄 때 이 지연이 있으면, 상대방은 "사이트가 고장났나?" 하고 이미 탭을 닫고 있을 거예요.

참고로 이 문제는 Fly.io만의 이야기가 아니에요. Render, Railway, Koyeb 등 무료 플랜을 제공하는 PaaS 대부분이 비슷한 슬립 메커니즘을 써요. 비용을 안 받는 대신 자원을 아끼는 방식이니까요.

---

## 세 가지 실전 해결 방법

### 1. 외부 핑으로 컨테이너 깨워두기

가장 간단하고 무료로 쓸 수 있는 방법이에요. 슬립에 들어가기 전에 주기적으로 앱에 HTTP 요청을 보내면 컨테이너가 계속 깨어있어요.

**Cron-job.org**를 쓰면 1분 단위 주기의 HTTP GET 요청을 무료로 설정할 수 있어요. 타겟 URL은 `https://your-app.fly.dev/api/ping`처럼 가벼운 엔드포인트로 잡는 게 좋아요.

Next.js에서 이 엔드포인트를 만드는 건 두 줄이면 끝이에요:

```typescript
// app/api/ping/route.ts
export async function GET() {
  return new Response('ok', { status: 200 });
}
```

이 방법의 핵심은 **앱의 핵심 로직을 건드리지 않는다**는 점이에요. DB 쿼리도 없고, 렌더링도 없어요. 그냥 "살아있어요"라고 응답하는 것만으로 컨테이너 슬립을 막아줘요.

**Uptime Kuma**를 셀프 호스팅으로 쓰고 있다면, 모니터링과 핑을 동시에 해결할 수도 있어요. 5분 이하 간격으로 헬스체크를 설정하면 돼요.

### 2. Fly.io 설정 파일에서 최솟값 지정하기

Fly.io 유료 플랜을 쓴다면, `fly.toml`에서 직접 항상 켜진 머신 수를 지정할 수 있어요.

```toml
[[services]]
  internal_port = 3000
  protocol = "tcp"

  [services.concurrency]
    hard_limit = 25
    soft_limit = 20

[[vm]]
  memory = "256mb"
  cpu_kind = "shared"
  cpus = 1

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = false  # 슬립 모드 비활성화
  min_machines_running = 1    # 항상 최소 1개 유지
```

`auto_stop_machines = false`와 `min_machines_running = 1`의 조합이 핵심이에요. 이렇게 하면 트래픽이 없어도 컨테이너가 내려가지 않아요. 대신 $5/월부터 시작하는 비용이 발생해요. 사이드 프로젝트 수준에서는 감당 가능한 금액이에요.

### 3. 체감 지연 줄이기: 스트리밍 렌더링

Cold Start 자체를 없앨 수 없는 상황이라면, 사용자가 기다리는 느낌을 줄이는 게 현실적이에요.

Next.js App Router는 서버 컴포넌트에서 `Suspense`와 스트리밍을 기본 지원해요. 데이터가 느리게 오는 부분에 로딩 스켈레톤을 넣으면, 페이지 자체는 빠르게 뜨고 데이터만 나중에 채워지는 것처럼 느껴져요.

```tsx
// app/page.tsx
import { Suspense } from 'react';
import { ProductList } from './ProductList';
import { ProductSkeleton } from './ProductSkeleton';

export default function Page() {
  return (
    <main>
      <h1>상품 목록</h1>
      <Suspense fallback={<ProductSkeleton />}>
        <ProductList />
      </Suspense>
    </main>
  );
}
```

이 방법은 실제 Cold Start 시간을 줄이진 않지만, 사용자 이탈을 막는 데 효과적이에요. Vercel의 2025년 성능 보고서에 따르면, 로딩 상태 UI가 있는 페이지는 없는 페이지보다 사용자 이탈률이 약 35% 낮았어요.

---

## 방법별 트레이드오프 비교

| 방법 | 비용 | 설정 난이도 | Cold Start 제거 | 부작용 |
|---|---|---|---|---|
| 외부 핑(Cron-job.org) | 무료 | 낮음 | 실질적 제거 | 핑 서비스 의존, 앱 슬립 여전히 발생 가능 |
| `min_machines_running = 1` | $5~/월 | 낮음 | 완전 제거 | 비용 발생 |
| Next.js 스트리밍 UI | 무료 | 중간 | 제거 안 됨 | 체감 개선만 |
| 유료 플랫폼 전환(Vercel 등) | $20~/월 | 낮음 | 완전 제거 | 비용 크게 증가 |

외부 핑 방법은 "비용 없이 슬립을 피하는" 현실적 선택이에요. 그런데 Cron 서비스 자체가 다운되거나, 응답 시간이 짧은 요청이 몰리는 시간대에는 여전히 슬립이 걸릴 수 있어요. `min_machines_running = 1`은 안정성이 가장 높지만, 월 비용이 생겨요. 포트폴리오나 데모 목적이라면 외부 핑이 충분하고, 실제 서비스 수준이라면 유료 설정을 쓰는 게 맞아요.

---

## 지금 바로 적용할 수 있는 체크리스트

**무료 플랜을 유지하고 싶다면:**

1. `app/api/ping/route.ts`에 경량 헬스체크 엔드포인트 추가
2. Cron-job.org에서 4~5분 주기 GET 요청 등록
3. 응답 타임아웃을 3초로 설정해 실패 감지 빠르게

**유료 플랜으로 간다면:**

1. `fly.toml`에 `auto_stop_machines = false` 추가
2. `min_machines_running = 1` 설정
3. `fly deploy`로 재배포

**체감 UX도 함께 잡고 싶다면:**

1. 무거운 데이터 로딩 컴포넌트에 `Suspense` 추가
2. 스켈레톤 UI 컴포넌트 작성
3. Next.js `loading.tsx` 파일로 라우트 단위 로딩 상태 처리

---

## 마무리: 무료가 진짜 공짜는 아니에요

Fly.io 무료 플랜 슬립 모드 문제는 결국 트레이드오프를 어디서 감수할지의 문제예요.

- 비용 0원을 지키려면 외부 핑 + 경량 엔드포인트로 충분해요
- Cold Start를 완전히 없애고 싶으면 월 $5~는 써야 해요
- 어떤 방법을 쓰든, 실전 설정 없이는 사용자가 먼저 지쳐요

Fly.io는 무료 플랜의 슬립 정책을 지금도 유지하고 있고, 당분간 바뀔 기미는 없어 보여요. 그래도 Firecracker VM의 부팅 속도 개선 작업은 꾸준히 진행 중이에요. 올해 하반기 안에 Cold Start 시간이 현재의 절반 수준으로 줄어들 가능성도 있어요.

지금 당장 Cron-job.org에서 설정 하나만 추가해도, 첫 방문자가 느끼는 앱의 인상이 완전히 달라질 거예요. 8초짜리 흰 화면이 2초짜리 로딩 UI로 바뀌는 것, 작은 차이처럼 보이지만 실제로는 꽤 크더라고요.

## 참고자료

1. [Getting Started: Deploying | Next.js](https://nextjs.org/docs/app/getting-started/deploying)
2. [r/nextjs on Reddit: Thoughts on Fly.io?](https://www.reddit.com/r/nextjs/comments/1o2bu9c/thoughts_on_flyio/)
3. [I/O 때문에 UI가 멈춘다면 | rhei.me](https://rhei.me/blog/cse/async-io)


---

*Photo by [Alex Gagareen](https://unsplash.com/@onepilot) on [Unsplash](https://unsplash.com/photos/black-and-silver-car-engine-AapHZdN_1-Y)*
