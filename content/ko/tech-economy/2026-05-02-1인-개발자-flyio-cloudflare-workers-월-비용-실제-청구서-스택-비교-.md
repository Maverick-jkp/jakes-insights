---
title: "1인 개발자가 직접 뜯어본 Fly.io vs Cloudflare Workers 월 비용 실제 청구서 비교"
date: 2026-05-02T20:02:24+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-cloud", "\uac1c\ubc1c\uc790", "fly.io", "cloudflare", "Python"]
description: "Fly.io vs Cloudflare Workers 실제 청구서 비교. 무료 플랜 월 300만 요청, Fly.io 소형 VM 월 $1.94~$5 기본 비용 발생. 1인 개발자 트래픽 규모별 실비용 분석."
image: "/images/20260502-1인-개발자-flyio-cloudflare-worker.webp"
technologies: ["Python", "Node.js", "Docker", "PostgreSQL", "Redis"]
faq:
  - question: "1인 개발자 Fly.io Cloudflare Workers 월 비용 실제 청구서 스택 비교 2025 어떻게 돼요"
    answer: "2025년 기준 1인 개발자 Fly.io Cloudflare Workers 월 비용 실제 청구서 스택 비교를 보면, 트래픽이 낮은 사이드 프로젝트는 Cloudflare Workers 무료 플랜(월 300만 요청 무료)으로 $0 유지가 가능해요. 반면 Fly.io는 2024년 말 무료 티어가 사실상 폐지되면서 소형 VM 기준 월 최소 $1.94~$10 수준의 비용이 발생해요."
  - question: "Fly.io 무료 티어 2024 이후 없어졌나요"
    answer: "네, Fly.io는 2024년 말부터 신규 가입자에게 무료 크레딧을 제공하지 않아요. 가장 작은 VM(shared-cpu-1x, 256MB RAM) 기준으로 월 약 $1.94가 청구되고, 볼륨 스토리지와 데이터베이스까지 붙이면 월 $5~$10 이상이 기본으로 나와요."
  - question: "Cloudflare Workers 유료 플랜 월 요금 얼마예요"
    answer: "Cloudflare Workers 유료 플랜(Paid)은 월 $5 고정 요금에 월 1,000만 요청이 포함돼요. 초과 요청은 백만 건당 $0.30이 추가되며, Workers KV 쓰기나 Durable Objects는 별도로 과금되니 상태 관리가 필요한 앱은 이 부분을 반드시 고려해야 해요."
  - question: "Fly.io vs Cloudflare Workers 데이터베이스 비용 비교"
    answer: "Cloudflare Workers의 D1(SQLite 기반)은 하루 읽기 500만 행, 쓰기 10만 행까지 무료이고 초과 시 소량 과금돼요. Fly.io는 Postgres를 직접 붙일 수 있지만 최소 월 $5~$15의 추가 비용이 발생하며, SQL 완전 지원과 마이그레이션 자유도는 D1보다 훨씬 높아요."
  - question: "1인 개발자 사이드 프로젝트 서버 비용 가장 저렴하게 운영하는 방법"
    answer: "월 트래픽이 50만 요청 이하인 사이드 프로젝트라면 1인 개발자 Fly.io Cloudflare Workers 월 비용 실제 청구서 스택 비교 기준으로 Cloudflare Workers 무료 플랜이 가장 저렴해요. 하루 약 1만 6천 요청 수준이면 무료 한도(하루 10만 요청)의 6분의 1에 불과해 비용이 $0이에요. 단, 상태 관리나 DB가 필요하다면 Durable Objects나 KV 비용이 추가될 수 있어 사전에 확인이 필요해요."
aliases:
  - "/tech/2026-05-02-1인-개발자-flyio-cloudflare-workers-월-비용-실제-청구서-스택-비교-/"
  - "/ko/tech/2026-05-02-1인-개발자-flyio-cloudflare-workers-월-비용-실제-청구서-스택-비교-/"

---

매달 청구서를 열 때마다 "이게 맞나?" 싶었던 적 있죠. 1인 개발자들이 가장 많이 묻는 질문 중 하나예요. "Fly.io랑 Cloudflare Workers, 실제로 얼마 나와요?" 공식 문서만 봐서는 감이 안 오니까, 실제 청구서 패턴과 공개된 사례들을 모아 2026년 기준으로 직접 뜯어봤어요.

> **핵심 요약**
> - Cloudflare Workers 무료 플랜은 하루 10만 요청, 월 300만 요청을 무료로 제공해요. 트래픽이 낮은 사이드 프로젝트라면 $0으로 버틸 수 있어요.
> - Fly.io는 무료 티어가 2024년 말부터 사실상 유료화됐어요. 신규 가입자는 크레딧 없이 시작하며, 소형 VM 기준 월 $1.94~$5 수준의 기본 비용이 발생해요.
> - 월 트래픽 1,000만 요청 이상부터는 Cloudflare Workers Paid 플랜($5/월 + $0.30/백만 요청)이 오히려 Fly.io 대비 저렴해지는 구간이 생겨요.
> - 상태(State)가 필요한 앱이라면 Workers KV, Durable Objects 비용이 빠르게 올라가요. 이 부분을 빼고 단순 비교하면 실제 청구서와 달라져요.
> - 선택 기준은 "서버가 필요한가, 엣지 함수로 충분한가"예요. 이 질문 하나로 두 플랫폼의 쓸모가 갈려요.

---

## 두 플랫폼이 주목받는 이유: 2026년 맥락

Vercel, Railway, Render 같은 플랫폼들이 무료 티어를 줄이거나 가격을 올리면서, 1인 개발자들이 대안을 찾기 시작했어요. Fly.io는 2022~2023년 "헤로쿠 대체제"로 급부상했고, Cloudflare Workers는 2024년부터 풀스택 지원이 강화되면서 선택지가 됐죠.

2026년 현재, 두 플랫폼은 완전히 다른 방향으로 진화했어요.

**Fly.io**는 Docker 기반 컨테이너를 전 세계 리전에 배포하는 방식이에요. 쉽게 말하면, 내 앱을 그대로 올릴 수 있는 미니 서버예요. PostgreSQL, Redis 같은 DB도 같이 붙일 수 있고요.

**Cloudflare Workers**는 서버가 없어요. 코드를 Cloudflare의 글로벌 엣지 네트워크에 올리면, 전 세계 300개 이상의 데이터센터에서 요청마다 실행되는 구조예요. V8 엔진 기반이라 Node.js와 비슷하지만, 런타임 제약이 있어요.

그런데 지금 이 비교가 특히 중요한 이유가 있어요. Fly.io가 2024년 말 무료 티어 정책을 바꿨고, Cloudflare Workers는 2025년에 Workers AI, Durable Objects 가격을 조정했거든요. 1년 전 블로그 포스팅 참고해서 예산 짰다간 실제 청구서에서 놀랄 수 있어요.

---

## 실제 청구서 뜯어보기: 세 가지 시나리오

### 시나리오 1: 사이드 프로젝트 (트래픽 낮음, 월 50만 요청 이하)

이 구간에선 Cloudflare Workers가 압도적으로 유리해요.

Cloudflare Workers 무료 플랜 기준(공식 문서):
- 하루 10만 요청 무료
- Workers KV 읽기 월 1,000만 회 무료
- 스크립트 실행 시간 제한 있음 (CPU 10ms/요청)

월 50만 요청이면 하루 약 1만 6천 요청이에요. 무료 한도인 하루 10만 요청의 6분의 1 수준이죠. **비용 $0**이에요.

Fly.io는 다르게 흘러가요. 2024년 말부터 신규 가입자 기준 무료 크레딧이 제거됐어요. 가장 작은 VM(`shared-cpu-1x`, 256MB RAM) 기준으로 월 약 **$1.94** 청구돼요. 여기에 볼륨 스토리지($0.15/GB), 아웃바운드 트래픽(100GB 이후 $0.02/GB)이 붙어요. 데이터베이스까지 붙이면 최소 **$5~$10**은 기본이에요.

사이드 프로젝트 하나 돌리는 데 매달 $5~$10이면, 1년이면 $60~$120이에요. 취미 프로젝트 치고 적지 않죠.

### 시나리오 2: 활성 서비스 (월 500만~1,000만 요청)

이 구간부터 비교가 흥미로워져요.

Cloudflare Workers Paid 플랜($5/월):
- 월 1,000만 요청 포함
- 초과 요청: $0.30/백만 요청
- Workers KV 쓰기: $5/백만 회
- Durable Objects 사용량 별도

월 1,000만 요청이면 $5 고정이에요. 초과 없이요.

Fly.io에서 같은 트래픽을 감당하려면 CPU/메모리를 올려야 해요. `shared-cpu-2x`, 512MB 기준으로 월 약 **$7~$15** 수준이고, 트래픽 스파이크 대응을 위해 자동 스케일링 설정하면 예상치 못한 청구가 붙기도 해요.

단순 API 서버라면 Cloudflare Workers가 비용 면에서 유리해요. 하지만 상태 관리나 DB가 필요하면 Workers KV, D1, Durable Objects 비용이 올라오면서 상황이 달라져요.

### 시나리오 3: DB + 백엔드 풀스택

Cloudflare의 D1(SQLite 기반 서버리스 DB) 무료 한도는 하루 읽기 500만 행, 쓰기 10만 행이에요. 이 범위 안이면 $0이지만, 넘으면 $0.001/만 행(읽기), $1/백만 행(쓰기)이 붙어요.

Fly.io는 Postgres를 직접 붙일 수 있어요. `fly postgres` 클러스터 기준 최소 월 **$5~$15**이에요. SQL 완전 지원, 마이그레이션 자유도는 D1과 비교가 안 될 만큼 높아요.

---

## 비용 비교표: 세 가지 사용 패턴

| 항목 | Cloudflare Workers (무료) | Cloudflare Workers (유료) | Fly.io (소형) |
|------|--------------------------|--------------------------|---------------|
| 월 기본 비용 | $0 | $5 | $1.94~ |
| 포함 요청 수 | 하루 10만 | 월 1,000만 | 트래픽 기반 과금 |
| DB 포함 | D1 무료 한도 제공 | D1 + 초과 과금 | Postgres 별도 $5~ |
| 상태 관리 | Durable Objects (유료) | Durable Objects 포함 | 기본 지원 |
| 컨테이너 지원 | ❌ | ❌ | ✅ |
| 추천 사용 사례 | API, 봇, 리다이렉트 | 중형 API 서비스 | 풀스택 앱, WebSocket |

---

## 어떤 상황에서 뭘 골라야 할까

**Cloudflare Workers를 고르면 좋은 경우:**

- 트래픽 예측이 어려운 사이드 프로젝트 (무료 한도가 여유로움)
- 정적 콘텐츠 + 간단한 API 조합
- 전 세계 지연 시간이 중요한 서비스 (엣지 특성상 latency가 낮음)
- Node.js 없이 JS/TS만으로 빠르게 배포하고 싶을 때

**Fly.io를 고르면 좋은 경우:**

- Docker로 패키징된 앱을 그대로 올리고 싶을 때
- WebSocket, 장기 연결이 필요한 서비스
- PostgreSQL 같은 관계형 DB를 직접 붙여야 할 때
- Python, Go, Ruby 같은 다양한 런타임 사용 시

Workers의 숨어있는 함정 하나만 짚고 갈게요. CPU 시간 제한이에요. 무료 플랜은 요청당 CPU 10ms, 유료는 30초 한도예요. 이미지 리사이징이나 복잡한 연산이 들어가면 제한에 금방 걸려요.

Fly.io는 반대로, 비용이 고정적으로 나간다는 게 예측하기 쉬워요. 트래픽이 없어도 VM이 켜져 있으면 청구가 돼요. 부담이라면 `fly scale count 0`으로 인스턴스를 0개로 줄이거나, `--auto-stop` 설정으로 유휴 시 자동 종료시킬 수 있어요.

---

## 결론: 청구서가 알려주는 선택 기준

두 플랫폼을 한 문장으로 정리하면 이래요.

**Cloudflare Workers는 트래픽이 곧 비용이에요. Fly.io는 시간이 곧 비용이에요.**

사이드 프로젝트나 API 서버라면 Workers로 시작하세요. 무료 한도가 생각보다 넓고, 실제로 $0 청구서가 가능해요. 단, DB나 상태 관리 기능이 붙기 시작하면 요금 구조를 꼼꼼히 따져봐야 해요.

풀스택 앱이거나 컨테이너가 필요하다면 Fly.io가 맞아요. 다만 2026년 현재 무료 시작이 어려워졌다는 점은 감안해야 해요.

앞으로 6개월 안에 주목할 변수는 두 가지예요. Cloudflare Workers의 `nodejs_compat` 플래그 확장(Node.js 호환성이 올라올수록 Workers 적용 범위가 넓어짐)과, Fly.io의 Machines API 가격 정책 변동이에요. 두 플랫폼 모두 가격을 올리는 방향보단 기능을 더 붙이는 방향으로 가고 있어서, 지금 선택한 스택이 6개월 후엔 더 싸질 수도 있어요.

당신 앱에서 가장 먼저 쓰이는 기능이 뭔가요? 거기서부터 역산하면 청구서 예측이 훨씬 쉬워져요.

## 참고자료

1. [Pricing · Cloudflare Workers docs](https://developers.cloudflare.com/workers/platform/pricing/)
2. [클라우드플레어 워커(cloudflare workers)와 AWS 람다(AWS Lambda) 비교 | marinesnow34](https://marinesnow34.github.io/2024/04/25/worker1/)


---

*Photo by [appshunter.io](https://unsplash.com/@appshunter) on [Unsplash](https://unsplash.com/photos/a-pink-phone-sitting-on-top-of-a-wooden-table-Iw9cw80cwQs)*
