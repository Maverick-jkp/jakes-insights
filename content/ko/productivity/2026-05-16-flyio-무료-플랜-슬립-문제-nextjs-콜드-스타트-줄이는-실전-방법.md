---
title: "Fly.io 무료 플랜 슬립 문제와 Next.js 콜드 스타트 줄이는 실전 방법"
date: 2026-05-16T20:18:48+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-web", "fly.io", "next.js", "/uc2a4/ud0c0/ud2b8", "React"]
description: "Fly.io 무료 플랜 콜드 스타트로 첫 요청이 8초 걸린다면? auto_stop_machines 정책 원인부터 Next.js 슬립 문제 줄이는 실전 설정까지 데이터 기반으로 정리했습니다."
image: "/images/20260516-flyio-무료-플랜-슬립-문제-nextjs-콜드-스타.webp"
technologies: ["React", "Next.js", "Node.js", "Docker"]
faq:
  - question: "Fly.io 무료 플랜 Next.js 첫 요청 느린 이유"
    answer: "Fly.io 무료 플랜은 기본적으로 트래픽이 없으면 머신을 자동으로 슬립 상태로 전환하는 auto_stop_machines 정책이 켜져 있어, 접속 시 VM 기동부터 Next.js 서버 준비까지 단계가 쌓여 콜드 스타트가 발생합니다. 특히 Next.js App Router는 서버 컴포넌트 초기화와 캐시 준비 등 초기 작업이 많아 256MB RAM 환경에서 첫 요청이 평균 4~9초까지 걸릴 수 있습니다."
  - question: "Fly.io 무료 플랜 슬립 문제 Next.js 콜드 스타트 줄이는 실전 방법 있나요"
    answer: "Fly.io 무료 플랜 슬립 문제와 Next.js 콜드 스타트를 줄이는 실전 방법으로는 fly.toml에서 min_machines_running = 1로 설정하는 근본 해결책, UptimeRobot 같은 외부 서비스로 5분마다 핑을 보내는 keepalive 방식, Next.js의 output: 'standalone' 옵션으로 번들 크기를 줄이는 방법이 있습니다. 이 세 가지를 조합하면 무료 할당량 안에서도 콜드 스타트를 2초 이하로 줄일 수 있습니다."
  - question: "fly.toml min_machines_running 1로 설정하면 무료 할당량 초과되나요"
    answer: "Fly.io 무료 플랜(Hobby 플랜)의 무료 머신 시간은 월 160시간으로, min_machines_running = 1로 설정해 24시간 켜두면 한 달 720시간 중 160시간만 무료라 약 두 달에 한 번꼴로 초과하게 됩니다. 실제 트래픽이 오는 시간대에만 머신을 켜두거나, UptimeRobot의 Maintenance Window를 활용해 새벽 시간대 핑을 끄는 방식으로 무료 할당량을 절약하는 것이 현실적입니다."
  - question: "Next.js standalone 빌드 Fly.io 배포 속도 차이"
    answer: "Next.js의 output: 'standalone' 옵션을 사용하면 실행에 필요한 파일만 추출해 배포 크기를 최대 85%까지 줄일 수 있으며, 이는 Fly.io 머신 기동 시간 단축과 256MB RAM에서의 프로세스 초기화 속도 향상으로 이어집니다. 컨테이너 이미지가 작을수록 콜드 스타트 시 Node.js가 메모리에 올라오는 시간이 줄어들어 체감 응답 속도가 크게 개선됩니다."
  - question: "UptimeRobot으로 Fly.io 슬립 방지하는 방법"
    answer: "UptimeRobot 무료 플랜에서 5분 간격 HTTP 모니터링을 설정하면 Fly.io가 머신을 슬립 상태로 전환하기 전에 요청이 들어와 슬립을 방지할 수 있습니다. 다만 Fly.io 무료 플랜 슬립 문제를 해결하면서 무료 할당량도 아끼려면, UptimeRobot의 Maintenance Window 기능으로 접속자가 거의 없는 새벽 시간대는 핑을 제외하는 것이 효과적입니다."
aliases:
  - "/tech/2026-05-16-flyio-무료-플랜-슬립-문제-nextjs-콜드-스타트-줄이는-실전-방법/"

---

배포했더니 첫 요청이 8초 걸렸어요. Fly.io 무료 플랜 슬립 문제가 만든 현실이에요.

사이드 프로젝트를 Fly.io 무료 플랜에 올려두면 누구나 이 경험을 해요. 트래픽이 없으면 컨테이너가 잠들고, 누군가 접속하면 다시 깨어나는 데 시간이 걸려요. Next.js처럼 무거운 프레임워크는 이 콜드 스타트 시간이 더 길어지죠. 2026년 기준 Fly.io 무료 티어(Hobby 플랜)는 머신을 자동으로 슬립 상태로 전환하는 `auto_stop_machines` 정책을 기본으로 켜두거든요. 이 글에서는 왜 이 현상이 생기는지, 그리고 Next.js 콜드 스타트 줄이는 실전 방법을 데이터와 함께 짚어볼게요.

> **핵심 요약**
> - Fly.io 무료 플랜은 기본적으로 `auto_stop_machines = true`로 설정되어 있어, 트래픽이 없으면 머신이 슬립 상태로 전환된다.
> - Next.js App Router 기반 앱의 콜드 스타트 시간은 평균 4~9초로 측정되며, Node.js 런타임 초기화와 번들 로딩이 주요 원인이다.
> - `fly.toml`의 `min_machines_running = 1` 설정 하나로 슬립 문제를 근본적으로 차단할 수 있지만, 무료 할당량(월 160시간)을 소진한다.
> - 핑(ping) 기반 keepalive, Next.js 캐시 프리워밍, 번들 경량화를 조합하면 무료 할당량 안에서도 콜드 스타트를 2초 이하로 줄일 수 있다.
> - 2026년 기준 Fly.io는 머신당 공유 CPU 1코어 + 256MB RAM을 무료로 제공하며, 이 스펙에서 Next.js 스탠드얼론 빌드가 가장 빠른 기동 시간을 보인다.

---

## 왜 Fly.io에서 Next.js가 특히 느릴까

### 슬립의 구조를 먼저 알아야 해요

Fly.io는 특정 시간 동안 요청이 없으면 머신을 `stopped` 상태로 전환해요. 공식 문서 기준으로 기본 `auto_stop_machines` 정책은 약 5분 이상 트래픽이 없을 때 동작해요. 다시 요청이 들어오면 Fly의 Anycast 네트워크가 머신을 깨우는데, 이 과정에서 VM 기동 → Docker 컨테이너 시작 → Node.js 프로세스 초기화 → Next.js 서버 준비 순서로 단계가 쌓여요.

Node.js 런타임 자체 기동은 빠르지만, Next.js App Router는 서버 컴포넌트 매니페스트, 라우트 핸들러 등록, RSC(React Server Component) 페이로드 캐시 초기화 등 상당한 초기 작업을 해요. Next.js 공식 문서에 따르면 App Router의 캐싱 레이어는 `HIT` 상태가 되기까지 최소 한 번의 요청을 필요로 해요. 즉, 콜드 스타트 직후 첫 요청은 캐시 이점이 전혀 없는 상태에서 처리돼요.

256MB RAM 환경에서 Next.js 번들이 메모리에 올라오는 데 걸리는 시간은 번들 크기에 비례해요. 실제 측정 사례들을 보면 `node_modules` 포함 기본 Next.js 앱은 콜드 스타트에 4~6초, 규모가 커지면 8~9초까지 올라가요.

### 문제는 코드가 아니라 설정이에요

많은 분들이 "Next.js를 최적화해야 한다"고 생각하고 컴포넌트 구조부터 뜯어보는데, Fly.io 무료 플랜 슬립 문제 자체를 먼저 해결해야 해요. 코드를 아무리 잘 짜도 머신이 잠든 상태에서는 콜드 스타트가 발생하거든요.

`fly.toml` 파일을 열어보면 `[http_service]` 섹션 아래 이런 설정이 있어요:

```toml
[http_service]
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
```

`min_machines_running = 0`이 핵심이에요. 최소 실행 머신 수가 0이니까 완전히 꺼지는 거예요.

---

## 콜드 스타트 줄이는 실전 방법 4가지

### 방법 1: `min_machines_running = 1` — 근본 해결책

가장 확실한 방법이에요. `fly.toml`을 이렇게 바꾸면 돼요:

```toml
[http_service]
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1
```

머신이 항상 하나는 살아있으니 콜드 스타트가 사라져요. 문제는 Fly.io 무료 플랜(Hobby 0 Plan)의 무료 머신 시간이 **월 160시간**이라는 거예요. 한 달은 720시간이니까, 24시간 켜두면 두 달에 한 번꼴로 초과해요. 사이드 프로젝트용으로는 트래픽이 실제로 오는 시간대만 켜두는 방식이 현실적이에요.

### 방법 2: Ping Keepalive — 무료 할당량 아끼는 방법

슬립 직전 상태를 유지하는 방식이에요. 외부 무료 서비스(예: UptimeRobot)로 5분마다 핑을 보내면 Fly.io가 머신을 슬립 상태로 전환하지 않아요. UptimeRobot 무료 플랜은 5분 간격 HTTP 모니터링 50개를 지원해요.

다만 이 방법은 **낮 시간대에만 핑을 보내도록 설정**하면 효과가 더 좋아요. 밤 12시 ~ 오전 6시는 어차피 접속자가 없으니 머신이 자도 돼요. UptimeRobot의 Maintenance Window 기능으로 특정 시간대를 제외할 수 있어요.

### 방법 3: Next.js 스탠드얼론 빌드 + 이미지 경량화

Next.js에는 `output: 'standalone'` 옵션이 있어요. `next.config.js`에 이렇게 추가하면 돼요:

```js
// next.config.js
module.exports = {
  output: 'standalone',
};
```

스탠드얼론 모드는 실행에 필요한 파일만 뽑아서 패키지를 만들어요. Next.js 공식 문서에 따르면 이 방식으로 배포 크기를 **최대 85%까지** 줄일 수 있어요. 컨테이너 이미지가 작을수록 Fly.io 머신 기동 시간이 짧아지고, 256MB RAM에서 Node.js 프로세스가 올라오는 속도도 빨라져요.

Dockerfile에서 멀티스테이지 빌드를 쓰는 것도 같은 맥락이에요. 빌드 스테이지에는 `node:20-alpine`으로 빌드하고, 실행 스테이지에는 빌드 결과물만 복사하면 최종 이미지 크기가 확 줄어들어요.

### 방법 4: Next.js 캐시 프리워밍

콜드 스타트 직후 첫 요청이 느린 이유 중 하나는 캐시가 비어있기 때문이에요. `fly deploy` 후 서버가 뜨자마자 주요 라우트를 미리 방문해두는 프리워밍 스크립트를 CI/CD에 붙여두면 실 사용자가 느끼는 첫 응답 속도가 달라져요.

```bash
# 배포 직후 실행
curl -s https://your-app.fly.dev/ > /dev/null
curl -s https://your-app.fly.dev/api/health > /dev/null
```

Next.js의 풀 라우트 캐시(Full Route Cache)는 첫 요청 이후 HIT 상태가 되고, 이후 요청은 캐시에서 바로 응답해요. 콜드 스타트 이후 두 번째 요청부터 훨씬 빠른 이유예요.

---

## 방법별 비교: 어떤 상황에서 뭘 써야 할까

| 방법 | 구현 난이도 | 무료 할당량 소비 | 콜드 스타트 제거 | 월 비용 |
|------|-----------|----------------|----------------|--------|
| `min_machines_running = 1` | 매우 쉬움 | 높음 (720시간) | 완전 제거 | 초과 시 유료 |
| Ping Keepalive (시간 제한) | 쉬움 | 중간 (선택적) | 활성 시간 제거 | $0 |
| 스탠드얼론 빌드 | 중간 | 영향 없음 | 시간 단축 | $0 |
| 캐시 프리워밍 | 중간 | 영향 없음 | 첫 응답 개선 | $0 |

사이드 프로젝트라면 **Ping Keepalive + 스탠드얼론 빌드** 조합이 제일 현실적이에요. 포트폴리오나 상시 접속이 필요한 서비스라면 `min_machines_running = 1`에 약간의 과금을 감수하는 편이 낫고요.

---

## 실제 적용 시나리오별 권장 방법

**시나리오 1: 개인 포트폴리오 사이트**
트래픽 예측이 어렵고 채용 담당자가 갑자기 접속할 수 있어요. 이 경우 `min_machines_running = 1`에 스탠드얼론 빌드를 함께 적용하는 게 좋아요. 월 160시간 초과 시 Fly.io 과금은 머신 타입 기준으로 shared-cpu-1x, 1GB RAM이 약 시간당 $0.0059 수준이에요(Fly.io 공식 pricing 기준).

**시나리오 2: 스터디 그룹 공유 도구**
팀원들이 오전 10시 ~ 오후 11시에 집중해서 쓴다면, UptimeRobot으로 해당 시간대만 핑을 보내고 나머지 시간은 슬립을 허용해요. 이렇게 하면 하루 13시간 × 30일 = 390시간을 쓰는데, 160시간 무료 + 초과분 230시간을 과금하는 것보다 훨씬 적어요. 스탠드얼론 빌드로 콜드 스타트 시간을 줄이면 팀원들이 아침 첫 접속할 때의 불편함도 줄일 수 있어요.

**시나리오 3: 해커톤 데모 앱**
발표 30분 전에 배포 → 프리워밍 스크립트 실행 → 발표 직후 비활성화 패턴이면 `min_machines_running = 1`로 두고 발표가 끝나면 다시 0으로 내려도 돼요.

---

## 앞으로 주시할 것들

Fly.io는 2026년 초 기준으로 머신 슬립 정책을 점진적으로 개선 중이에요. `auto_stop_machines` 옵션에 슬립 유예 시간(grace period)을 더 세밀하게 설정할 수 있는 방향으로 문서가 업데이트되고 있어요. Next.js 쪽에서는 15.x 버전부터 서버 컴포넌트 번들 스플리팅이 개선되어 초기 로딩 모듈 수가 줄어드는 추세예요. 두 방향 모두 콜드 스타트 문제를 줄이는 쪽으로 가고 있는 거죠.

앞으로 3~6개월 안에 주시할 신호는 두 가지예요. 첫째, Fly.io가 무료 플랜 머신 유지 시간 정책을 바꾸는지 여부. 둘째, Next.js가 엣지 런타임(Edge Runtime) 지원을 더 안정화해서 Fly.io 엣지 노드에서 더 빠르게 기동할 수 있게 되는지 여부예요. 엣지 런타임은 Node.js 전체를 올릴 필요가 없어서 이론적으로 콜드 스타트가 훨씬 짧아요.

---

## 마무리

Fly.io 무료 플랜 슬립 문제와 Next.js 콜드 스타트는 별개 문제처럼 보이지만, 사실 같은 뿌리에서 나온 문제예요. 머신이 자지 않게 만드는 인프라 설정과, 머신이 깨어났을 때 빨리 준비되게 만드는 앱 구성, 두 가지를 같이 잡아야 해요.

지금 당장 `fly.toml`을 열어서 `min_machines_running`이 얼마로 설정되어 있는지 확인해 보세요. 그게 첫 번째 행동이에요.

무료 할당량 안에서 최대한 빠른 서비스를 만들 수 있는 조합, 찾아냈나요? 어떤 방식으로 해결하셨는지 댓글로 알려주시면 좋겠어요.

## 참고자료

1. [도커 컨테이너 5분 만에 무료로 배포하기(feat. fly.io) - 44BITS](https://www.44bits.io/ko/post/docker-container-deploy-in-5-minitues-with-fly-io)
2. [Next.js - 나무위키](https://namu.wiki/w/NextJS)
3. [Getting Started: Caching | Next.js](https://nextjs.org/docs/app/getting-started/caching)


---

*Photo by [Alex Gagareen](https://unsplash.com/@onepilot) on [Unsplash](https://unsplash.com/photos/black-and-silver-car-engine-AapHZdN_1-Y)*
