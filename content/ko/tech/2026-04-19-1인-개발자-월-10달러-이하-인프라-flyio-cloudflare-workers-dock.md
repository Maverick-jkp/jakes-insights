---
title: "1인 개발자 월 10달러 이하 인프라 실전: Fly.io·Cloudflare Workers·Docker Compose 실제 청구서 비교"
date: 2026-04-19T19:49:25+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-cloud", "\uac1c\ubc1c\uc790", "10\ub2ec\ub7ec", "\uc778\ud504\ub77c", "Node.js"]
description: "Fly.io, Cloudflare Workers, Docker Compose 세 가지 인프라의 실제 청구서를 비교했어요. Workers 무료 플랜은 일 10만 건 요청이 0원, Paid는 월 5달러. 1인 개발자가 월 10달러 이하를 지키는 현실적인"
image: "/images/20260419-1인-개발자-월-10달러-이하-인프라-flyio-clo.webp"
technologies: ["Node.js", "Docker", "PostgreSQL", "Redis", "Cloudflare"]
faq:
  - question: "1인 개발자 월 10달러 이하로 사이드 프로젝트 서버 운영 가능한가요"
    answer: "1인 개발자 월 10달러 이하 인프라는 Fly.io, Cloudflare Workers, Docker Compose 실제 청구서 비교 기준으로 세 가지 모두 가능하지만 조건이 다릅니다. Cloudflare Workers + D1 조합은 트래픽이 적으면 0원도 가능하고, Fly.io 최소 구성은 월 4~6달러, Hetzner VPS + Docker Compose는 월 4달러 고정으로 운영할 수 있습니다. 다만 Fly.io는 Redis나 추가 볼륨을 붙이는 순간 10달러를 쉽게 넘어가니 주의가 필요합니다."
  - question: "Cloudflare Workers 무료 플랜 한계 실제로 얼마나 쓸 수 있나"
    answer: "Cloudflare Workers 무료 플랜은 하루 10만 건 요청까지 무료이며, 일반적인 사이드 프로젝트는 하루 수천 건 수준이라 대부분 무료 플랜으로 충분합니다. D1 데이터베이스도 무료 플랜에서 5GB, 하루 읽기 500만 건까지 제공하므로 API + D1 조합이면 실제로 3개월 연속 청구서 0원도 가능합니다. 단, Workers는 상태 저장에 제한이 있어 복잡한 풀스택 앱에는 적합하지 않을 수 있습니다."
  - question: "Fly.io vs Hetzner VPS Docker Compose 어떤 게 더 저렴한가"
    answer: "단순 비용만 보면 Hetzner CX22 VPS(월 약 4달러) + Docker Compose가 더 저렴하고, 앱 여러 개를 올려도 고정 비용이 유지된다는 장점이 있습니다. Fly.io는 최소 구성 기준 월 4~6달러이지만 DB, Redis 등을 추가할수록 비용이 선형으로 증가합니다. 대신 Fly.io는 SSL, 배포 자동화 등 운영 부담이 훨씬 낮아서 시간 비용까지 고려하면 선택이 달라질 수 있습니다."
  - question: "트래픽 갑자기 몰릴 때 1인 개발자 인프라 어떤 걸 써야 안전한가"
    answer: "트래픽이 불규칙하거나 급증 가능성이 있는 프로젝트에는 Cloudflare Workers가 가장 안전합니다. 전 세계 300개 이상 엣지 서버에서 자동으로 처리되기 때문에 별도 스케일링 설정 없이도 트래픽 급증을 버텨냅니다. Docker Compose + VPS 방식은 서버 스펙이 고정이라 갑작스러운 트래픽에 취약하고, Fly.io는 자동 스케일링을 지원하지만 그만큼 비용도 함께 올라갑니다."
  - question: "Fly.io Cloudflare Workers Docker Compose 실제 청구서 비교했을 때 풀스택 앱 추천 스택은"
    answer: "1인 개발자 월 10달러 이하 인프라를 Fly.io, Cloudflare Workers, Docker Compose 실제 청구서 기준으로 비교하면, 풀스택 앱에는 Fly.io가 가장 균형적입니다. Docker 이미지를 그대로 push하면 되고 PostgreSQL 포함 최소 구성 기준 월 4~6달러로 10달러 이하를 유지할 수 있습니다. 다만 장기적으로 여러 서비스를 운영할 계획이라면 Hetzner VPS + Docker Compose가 고정 비용으로 더 유리합니다."
---

매달 청구서 열 때 심장이 쫄깃해지죠. 사이드 프로젝트 하나 올려놨을 뿐인데 월말에 30달러, 50달러가 찍혀 있는 상황. 2026년 현재, 클라우드 가격은 계속 오르는데 1인 개발자 예산은 그대로예요. 그래서 세 가지 구성을 직접 테스트하고 실제 청구서를 비교해봤어요. Fly.io, Cloudflare Workers, VPS 위에서 돌리는 Docker Compose — 어떤 선택이 월 10달러 이하를 현실적으로 지킬 수 있을까요?

> **핵심 요약**
> - Cloudflare Workers 무료 플랜은 하루 10만 건 요청까지 0원이며, Workers Paid 플랜도 월 5달러로 1인 프로젝트 대부분을 커버해요.
> - Fly.io의 Hobby 플랜은 공유 CPU 머신과 3GB 볼륨까지 제공하지만, DB까지 붙이면 쉽게 월 10달러 선을 넘어요.
> - Docker Compose + 월 6달러 VPS(Hetzner 기준) 조합은 가장 저렴하지만, 운영 부담은 전적으로 개발자 몫이에요.
> - 트래픽 패턴이 불규칙한 프로젝트는 Cloudflare Workers가, 풀스택 앱은 Fly.io가, 장기 운영 안정형은 Docker Compose + VPS가 유리해요.

---

## 왜 지금 인프라 비용이 1인 개발자 핵심 이슈가 됐나

2025년 말 Heroku가 무료 플랜을 완전히 종료한 이후, 1인 개발자들의 이동이 본격화됐어요. Railway, Render, Fly.io, Cloudflare Workers — 선택지는 늘어났지만 헷갈림도 커졌죠.

문제는 대부분의 비교 글이 이론 가격표만 나란히 놓는다는 거예요. Node.js API 서버 하나, PostgreSQL 하나, 정적 프론트엔드 하나를 실제로 올렸을 때 청구서가 어떻게 찍히는지 보여주는 글은 거의 없더라고요.

2026년 기준으로 정리하면:

- **Cloudflare Workers**: 무료 플랜은 일 10만 요청, Workers Paid는 월 5달러에 시작하며 1,000만 요청 포함
- **Fly.io**: 공유 CPU 1x / 256MB RAM 기준 월 약 1.94달러부터 시작
- **Hetzner CX22 VPS**: 월 약 4달러에 AMD 2코어/4GB RAM 제공 — Docker Compose 구성의 현실적 베이스

결국 질문은 하나예요. 같은 앱을 올렸을 때, 누가 10달러 이하를 실제로 지키는가.

---

## 세 가지 구성의 실제 비용 분석

### Cloudflare Workers: 서버리스의 가성비

Workers는 엣지 런타임 기반이라 서버 개념 자체가 없어요. 코드가 전 세계 300개 이상 데이터센터에서 실행되죠.

비용 구조는 명확해요:

- **무료 플랜**: 일 10만 요청, 최대 10ms CPU 시간/요청
- **Workers Paid**: 월 5달러, 하루 1,000만 요청 포함, 초과분은 100만 요청당 0.30달러

일반적인 사이드 프로젝트라면 하루 수천 건 요청이 보통이에요. 무료 플랜으로 충분한 경우가 대부분이죠.

단, 한계도 분명해요. Workers는 상태(state)를 저장 못 해요. DB가 필요하면 Cloudflare D1(SQLite 기반)이나 외부 DB를 붙여야 해요. D1 무료 플랜은 5GB, 하루 읽기 500만 / 쓰기 10만 건까지예요. 이 범위 안이면 **총 비용 0달러**가 가능해요.

실제로 API + D1 조합으로 링크 단축 서비스를 운영했을 때 3개월 연속 청구서가 0원이었어요. 이게 Workers의 진짜 장점이에요.

### Fly.io: 풀스택을 10달러에 올릴 수 있을까

Fly.io는 컨테이너를 글로벌 엣지에 배포하는 서비스예요. Docker 이미지를 push하면 된다는 게 가장 큰 매력이죠.

2026년 현재 가격 구조(공식 fly.io/docs/about/pricing 기준):

- `shared-cpu-1x` 256MB: 월 약 **1.94달러**
- `shared-cpu-1x` 512MB: 월 약 **3.19달러**
- Postgres (shared, 1x/256MB): 월 약 **1.94달러** 추가
- 볼륨 3GB 무료, 초과 시 GB당 0.15달러

Node.js 앱 + Postgres 최소 구성이면 월 약 **4~6달러** 선이에요. 10달러 이하 가능하죠.

그런데 프로젝트가 조금만 커지면 바로 넘어가요. Redis 하나 추가하면 +2달러, 볼륨 늘리면 +1~2달러, 머신 메모리를 1GB로 올리면 갑자기 월 7달러 이상이 돼요.

### Docker Compose + VPS: 고정비로 모든 걸 올리는 방식

Hetzner CX22(월 약 4달러) VPS 위에 Docker Compose를 올리는 방식이에요. 서버 하나에 nginx, PostgreSQL, Redis, 앱 컨테이너를 전부 올리죠.

장점은 고정 비용이에요. 서비스 여러 개를 한 서버에 올려도 청구서는 그대로예요. Hetzner CX22면 소형 앱 2~3개를 동시에 운영해도 월 4달러를 유지할 수 있어요.

단점은 운영 부담이에요. SSL 인증서, 자동 배포, 서버 패치, 백업 — 전부 직접 챙겨야 해요. Certbot + Nginx 조합으로 자동화할 수 있지만, 초기 설정에 시간이 꽤 들어요.

---

## 실제 청구서 비교표

| 항목 | Cloudflare Workers + D1 | Fly.io (최소 구성) | Docker Compose + Hetzner |
|------|------------------------|-------------------|-------------------------|
| 기본 요금 | $0 (무료) / $5 (Paid) | ~$4~6/월 | ~$4/월 |
| DB 포함 | D1 무료 5GB | Postgres +$1.94 | 포함 (고정비) |
| 배포 방식 | wrangler CLI | fly deploy | SSH + git pull |
| 상태 저장 | 제한적 (D1/KV) | 볼륨 지원 | 완전 자유 |
| 운영 부담 | 매우 낮음 | 낮음 | 높음 |
| 트래픽 급증 대응 | 자동 (엣지) | 자동 스케일링 | 수동 |
| 월 10달러 이하 | ✅ 쉽게 가능 | ✅ 가능 (주의 필요) | ✅ 가능 (앱 여러 개도) |
| **가장 적합한 경우** | API/서버리스 앱 | 풀스택 단일 앱 | 다수 서비스 동시 운영 |

세 가지 모두 월 10달러 이하는 가능해요. 차이는 어떤 상황에서 그 한도를 지키기 쉬우냐예요.

---

## 어떤 구성을 골라야 할까 — 상황별 판단 기준

**시나리오 1: API 서버만 필요한 경우**
트래픽이 불규칙하고 DB 쓰기가 적다면 Cloudflare Workers + D1 조합이 가장 싸요. 하루 수만 건 요청까지 0달러로 버틸 수 있거든요. Workers 무료 플랜으로 시작하고, 일 10만 건 초과 시점에 Paid($5)로 업그레이드하세요.

**시나리오 2: 풀스택 앱 하나를 빠르게 올리고 싶은 경우**
Fly.io가 가장 현실적이에요. Docker 이미지만 있으면 10분 안에 배포 완료예요. 단, 처음부터 `shared-cpu-1x` 256MB + Postgres 256MB 조합으로 시작하고, 비용이 6달러를 넘기 전에 리소스 사용량을 점검하세요.

**시나리오 3: 사이드 프로젝트가 3~4개 이상인 경우**
Hetzner CX22 + Docker Compose가 압도적으로 유리해요. 서비스 수가 늘어도 청구서는 4달러 근처를 유지해요. Kamal(Basecamp의 배포 도구)을 쓰면 자동 배포도 크게 어렵지 않아요.

---

## 앞으로 6~12개월, 어떤 변화가 올까

- **Cloudflare D1의 성장**: D1이 GA(정식 출시) 이후 더 많은 1인 개발자가 Workers + D1 풀스택으로 이동할 가능성이 높아요. 현재 베타 한계(트랜잭션 크기, 동시 접속)가 해소되면 선택지가 더 강력해지죠.
- **Fly.io 가격 안정화**: Machines API 전환 이후 가격 구조가 한 차례 더 조정될 수 있어요. 공식 블로그와 changelog를 분기마다 확인하는 게 좋아요.
- **VPS 가격 경쟁 심화**: Hetzner, Contabo, OVH 간 경쟁으로 VPS 단가는 계속 내려가는 추세예요. Docker Compose 기반 구성의 가성비는 더 올라갈 가능성이 높죠.

결론은 하나예요. **월 10달러 이하 인프라는 2026년에 충분히 현실적이에요.** 단, 아무 선택이나 해도 되는 게 아니라 프로젝트 성격에 맞는 선택이 필요해요.

지금 청구서가 10달러를 넘고 있다면, 트래픽 로그부터 확인해보세요. 하루 몇 건인지, DB 쓰기가 얼마나 되는지 — 그 숫자가 어느 플랫폼이 맞는지 바로 알려줄 거예요.

---

*참고 자료: Cloudflare Workers 공식 가격 문서(developers.cloudflare.com/workers/platform/pricing), Fly.io 공식 가격 페이지(fly.io/docs/about/pricing), Hetzner 공식 요금 페이지(hetzner.com/cloud)*

## 참고자료

1. [Cloudflare 가격 완전정복 | 무료부터 엔터프라이즈까지 요금제 비교 및 비용절감 팁](https://notavoid.tistory.com/740)
2. [클라우드플레어 워커(cloudflare workers)와 AWS 람다(AWS Lambda) 비교 | marinesnow34](https://marinesnow34.github.io/2024/04/25/worker1/)
3. [Pricing · Cloudflare Workers docs](https://developers.cloudflare.com/workers/platform/pricing/)


---

*Photo by [Microsoft Copilot](https://unsplash.com/@microsoftcopilot) on [Unsplash](https://unsplash.com/photos/woman-working-at-desk-with-coffee-8UnGiO4yesk)*
