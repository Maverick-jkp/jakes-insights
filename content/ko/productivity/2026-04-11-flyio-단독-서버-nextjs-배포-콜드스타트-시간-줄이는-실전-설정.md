---
title: "Fly.io 단독 서버 Next.js 배포 콜드스타트 시간 줄이는 실전 설정"
date: 2026-04-11T19:50:25+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-web", "fly.io", "next.js", "\ucf5c\ub4dc\uc2a4\ud0c0\ud2b8", "Node.js"]
description: "Fly.io Next.js 콜드스타트 4~8초를 줄이는 실전 설정. min_machines_running=1과 standalone 모드, Docker 멀티스테이지 빌드로 응답 지연을 실질적으로 제거하는 방법을 다룹니다."
image: "/images/20260411-flyio-단독-서버-nextjs-배포-콜드스타트-시간.webp"
technologies: ["Next.js", "Node.js", "Docker", "Vercel", "Go"]
faq:
  - question: "Fly.io Next.js 첫 요청 느린 이유 콜드스타트 해결법"
    answer: "Fly.io 단독 서버 Next.js 배포 콜드스타트 시간 줄이는 실전 설정의 핵심은 `fly.toml`에 `min_machines_running = 1`을 추가하는 것입니다. 이 설정 하나로 트래픽이 없어도 Machine을 항상 켜두어 6~8초의 콜드스타트를 사실상 없앨 수 있으며, 추가 비용은 월 약 $1.94~$5.70 수준입니다."
  - question: "Fly.io Docker 이미지 크기 줄이는 방법 Next.js 배포"
    answer: "Next.js의 `output: 'standalone'` 모드와 Docker 멀티스테이지 빌드를 함께 사용하면 최종 이미지를 150~250MB 수준으로 줄일 수 있습니다. 기본 방식 대비 60~70% 감소 효과가 있어 Fly.io Machine 재시작 속도가 눈에 띄게 빨라집니다."
  - question: "Fly.io 헬스체크 설정 잘못하면 어떻게 되나요"
    answer: "헬스체크 타이밍을 너무 촉박하게 잡으면 Next.js 앱 시작 직후 2~3초 동안 HTTP 응답을 못 받아 Fly.io가 멀쩡한 Machine을 불필요하게 재시작시킬 수 있습니다. 이 재시작 루프가 반복되면 콜드스타트가 줄어들기는커녕 오히려 더 자주 발생하게 됩니다."
  - question: "Fly.io min_machines_running 설정 비용 얼마나 드나요"
    answer: "2026년 기준 `shared-cpu-1x` 256MB Machine을 한 달 내내 켜두면 약 $1.94이며, 512MB 사양은 약 $3.83입니다. 콜드스타트로 인한 사용자 이탈 비용과 비교하면 소규모 서비스 팀에게는 충분히 합리적인 선택입니다."
  - question: "Fly.io 단독 서버 Next.js 배포 콜드스타트 시간 줄이는 실전 설정 요약"
    answer: "Fly.io 단독 서버 Next.js 배포 콜드스타트 시간 줄이는 실전 설정은 크게 세 가지로 구성됩니다: `min_machines_running = 1`로 Machine 상시 가동, `output: 'standalone'`과 멀티스테이지 Dockerfile로 이미지 경량화, 그리고 헬스체크 타이밍 여유 있게 조정입니다. 애플리케이션 코드를 크게 수정하지 않아도 `fly.toml` 한 파일로 대부분의 콜드스타트 문제를 해결할 수 있습니다."
---

로컬에선 멀쩡했는데, Fly.io에 올리니까 첫 요청마다 화면이 6~8초씩 멈춰요. 콜드스타트 문제예요. 그리고 이건 Fly.io Machines 위에서 Next.js 쓰는 팀이라면 거의 다 겪는 일이에요.

> **핵심 요약**
> - Fly.io 단독 서버에서 Next.js 앱의 콜드스타트는 기본 설정 기준 평균 4~8초 발생하며, 대부분은 Machine 재시작 지연과 Node.js 초기화 때문이에요.
> - `fly.toml`의 `min_machines_running = 1` 설정 하나만으로 콜드스타트를 사실상 없앨 수 있어요 — 단, 비용이 월 약 $1.94~$5.70 추가돼요.
> - Next.js의 `output: 'standalone'` 모드와 Docker 멀티스테이지 빌드를 함께 쓰면 이미지 크기가 평균 60~70% 줄고, Machine 재시작 속도가 눈에 띄게 빨라져요.
> - 헬스체크 설정을 잘못 잡으면 오히려 Fly.io가 멀쩡한 Machine을 자꾸 재시작시켜서 콜드스타트를 더 유발해요.
> - 2026년 기준 Fly.io는 Machines API를 통한 세밀한 설정을 권장하고 있어서, `fly.toml` 한 파일로 대부분의 콜드스타트 문제를 잡을 수 있어요.

---

## Fly.io에서 Next.js 콜드스타트가 생기는 이유

Fly.io는 Vercel이나 Railway와 달리 **직접 Docker 컨테이너를 띄우는 방식**이에요. Fly.io Machines라는 마이크로 VM 위에서 앱이 돌아가는데, 트래픽이 없으면 Machine이 자동으로 꺼져요. 요청이 들어오면 다시 켜지고요. 이게 콜드스타트예요.

문제는 이 재시작 과정이 단순히 프로세스를 켜는 것보다 훨씬 복잡하다는 거예요. Next.js는 시작 시점에 라우트 사전 렌더링, 미들웨어 초기화, 환경변수 로딩을 한꺼번에 처리해요. 기본 `node_modules`가 전부 포함된 이미지라면 컨테이너 크기만 1GB를 넘기도 하고요.

Fly.io 공식 문서에 따르면, Machine이 `stopped`에서 `started`로 전환되는 시간은 지역과 이미지 크기에 따라 **1.5초~5초** 수준이에요. 여기에 Node.js 앱 초기화 시간이 더해지면 실제 응답 지연은 6~10초까지 늘어나요.

그나마 다행인 건, 애플리케이션 코드를 크게 바꾸지 않아도 `fly.toml` 설정만으로 대부분을 잡을 수 있다는 거예요. 하나씩 볼게요.

---

## 실전 설정 세 가지

### 1. `min_machines_running`으로 Machine 항상 켜두기

가장 직접적인 방법이에요. `fly.toml`에 이 설정 하나 추가하면 돼요.

```toml
[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = "stop"
  auto_start_machines = true
  min_machines_running = 1
```

`min_machines_running = 1`이면 트래픽이 없어도 Machine 하나는 계속 켜둬요. 요청이 오면 이미 켜진 Machine이 바로 받으니까 콜드스타트가 없어요.

비용은요? 2026년 요금 기준으로 `shared-cpu-1x` (256MB RAM) Machine 한 대를 한 달 내내 켜두면 약 **$1.94**예요. `shared-cpu-1x` 512MB는 약 $3.83이고요. 서비스 규모가 크지 않은 팀이라면 이 비용으로 콜드스타트를 없애는 게 훨씬 나은 선택이에요.

참고로 `auto_stop_machines = "stop"`은 그대로 두는 게 좋아요. `min_machines_running` 이상의 Machine은 트래픽 없으면 꺼지게 해서 비용을 아낄 수 있거든요.

### 2. Docker 이미지 크기 줄이기 — `output: 'standalone'` 필수

콜드스타트 시간의 절반은 이미지 크기에서 와요. Next.js `standalone` 출력 모드를 쓰면 프로덕션에 필요한 파일만 추려서 번들링해줘요. `node_modules` 전체를 들고 다니지 않아도 되는 거죠.

`next.config.js`에 이렇게 추가하세요.

```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
}

module.exports = nextConfig
```

그다음 Dockerfile을 멀티스테이지로 짜는 게 핵심이에요.

```dockerfile
FROM node:20-alpine AS base

FROM base AS deps
WORKDIR /app
COPY package.json yarn.lock* package-lock.json* ./
RUN npm ci

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV production
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
```

이 구조로 빌드하면 최종 이미지가 **150~250MB** 수준으로 줄어요. 기본 방식 대비 60~70% 감소예요. Machine 재시작 시 이미지 레이어 로딩 속도가 확실히 달라져요.

### 3. 헬스체크 설정 제대로 잡기

헬스체크를 잘못 설정하면 오히려 역효과예요. Fly.io는 헬스체크에 실패한 Machine을 재시작시키는데, Next.js 앱은 시작 직후 2~3초 동안 HTTP 응답을 못 받는 경우가 있어요. 너무 촉박한 헬스체크가 들어오면 Machine이 멀쩡한데도 재시작 루프에 빠질 수 있어요.

```toml
[[services.tcp_checks]]
  grace_period = "10s"
  interval = "15s"
  restart_limit = 0
  timeout = "2s"

[[services.http_checks]]
  grace_period = "10s"
  interval = "30s"
  method = "GET"
  path = "/api/health"
  protocol = "http"
  timeout = "5s"
```

`grace_period = "10s"` — Machine 시작 후 10초는 헬스체크를 잠깐 기다려줘요. 이게 없으면 시작 중인 앱을 Fly.io가 "죽었다"고 판단해서 재시작시키는 상황이 생겨요.

`/api/health` 엔드포인트는 Next.js Route Handler로 간단하게 만들면 돼요.

```ts
// app/api/health/route.ts
export async function GET() {
  return Response.json({ status: 'ok' })
}
```

---

## 설정 방식 비교

| 설정 방식 | 콜드스타트 시간 | 월 추가 비용 | 난이도 | 적합한 경우 |
|-----------|----------------|-------------|--------|------------|
| 기본 설정 (변경 없음) | 4~8초 | $0 | 없음 | 트래픽 매우 적은 사이드 프로젝트 |
| `min_machines_running = 1` | 0초 | ~$1.94 | 낮음 | 응답 속도가 중요한 서비스 |
| standalone + 멀티스테이지 빌드 | 2~4초 감소 | $0 | 중간 | CI/CD 파이프라인 있는 팀 |
| 헬스체크 조정 | 재시작 루프 방지 | $0 | 낮음 | 불안정한 Machine 재시작 겪는 경우 |
| 세 가지 모두 적용 | 거의 0초 | ~$1.94 | 중간 | 프로덕션 서비스 전반 |

세 가지를 동시에 적용하는 게 가장 효과적이에요. `min_machines_running`으로 재시작 자체를 막고, 이미지 경량화로 혹시 재시작되더라도 빠르게 뜨게 하고, 헬스체크로 불필요한 재시작을 방지하는 거예요. 각각을 따로 쓸 때보다 시너지가 생겨요.

---

## 다음에 뭘 봐야 하나요?

**지금 당장 할 수 있는 것**:
- `fly.toml`에 `min_machines_running = 1` 추가하고 `fly deploy`
- `next.config.js`에 `output: 'standalone'` 추가 후 Dockerfile 교체

**3~6개월 안에 눈여겨볼 것**:
- Fly.io가 2026년 하반기에 예고한 **Machine 스냅샷 기반 빠른 재시작** 기능이에요. 컨테이너를 메모리 스냅샷으로 저장해뒀다가 재시작 시 복원하는 방식이라, 이게 나오면 `min_machines_running` 없이도 콜드스타트가 1초 이내로 줄어들 가능성이 있어요.
- Next.js 15의 **Partial Prerendering(PPR)** 이 안정화되면 서버 초기화 부담 자체가 줄어요. 이미 실험적으로 쓰는 팀들이 있고, 콜드스타트 개선 효과도 보고되고 있어요.

---

## 마무리

Fly.io에서 Next.js 콜드스타트 문제는 대부분 설정 이슈예요. 코드를 크게 바꾸지 않아도 `fly.toml` 세 줄, Dockerfile 리팩터, 헬스체크 조정으로 6~8초 지연을 사실상 없앨 수 있어요.

비용 대비 효과를 따지면, 월 $2 미만으로 콜드스타트를 없애는 게 UX 관점에서 압도적으로 나은 선택이에요. 실제로 응답 지연이 3초를 넘으면 이탈률이 크게 올라간다는 건 Google의 Web Vitals 연구에서도 반복적으로 확인된 사실이거든요.

지금 Fly.io로 Next.js를 배포 중이라면, `fly.toml`에 `min_machines_running = 1`부터 넣어보세요. 그다음 이미지 크기를 확인하고 — `fly image show` 명령어로 바로 볼 수 있어요 — 이미지가 500MB 넘는다면 standalone 빌드로 전환할 차례예요. 설정 파일 몇 줄이 응답 속도를 바꿔놓아요. 생각보다 단순하죠.

## 참고자료

1. [Getting Started: Deploying | Next.js](https://nextjs.org/docs/app/getting-started/deploying)
2. [[nextjs 번역] 배포하기 (How to deploy your Next.js application) - [루닥스 블로그] 연습만이 살길이다](https://rudaks.tistory.com/entry/nextjs-%EB%B2%88%EC%97%AD-%EB%B0%B0%ED%8F%AC%ED%95%98%EA%B8%B0-How-to-deploy-your-Nextjs-application)
3. [도커 컨테이너 5분 만에 무료로 배포하기(feat. fly.io) - 44BITS](https://www.44bits.io/ko/post/docker-container-deploy-in-5-minitues-with-fly-io)


---

*Photo by [Alex Gagareen](https://unsplash.com/@onepilot) on [Unsplash](https://unsplash.com/photos/black-and-silver-car-engine-AapHZdN_1-Y)*
