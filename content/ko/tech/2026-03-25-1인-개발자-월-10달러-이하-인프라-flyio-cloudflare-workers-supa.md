---
title: "1인 개발자가 Fly.io·Cloudflare Workers·Supabase로 월 10달러 이하 인프라 운영하는 법 실제 비용 후기"
date: 2026-03-25T20:14:10+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-cloud", "\uac1c\ubc1c\uc790", "10\ub2ec\ub7ec", "\uc778\ud504\ub77c", "AWS"]
description: "Fly.io·Cloudflare Workers·Supabase 조합으로 월 10달러 이하 인프라 구축 가능할까요? 무료 티어 한계와 실제 비용이 발생하는 지점을 데이터로 분석했습니다."
image: "/images/20260325-1인-개발자-월-10달러-이하-인프라-flyio-clo.webp"
technologies: ["AWS", "Cloudflare", "Supabase"]
faq:
  - question: "1인 개발자 월 10달러 이하로 실제 서비스 운영 가능한가요"
    answer: "1인 개발자 월 10달러 이하 인프라 Fly.io Cloudflare Workers Supabase 실제 비용 후기에 따르면, 트래픽이 낮은 초기 서비스 기준으로 월 0~7달러 수준이 현실적으로 가능해요. Fly.io 무료 머신 3대, Cloudflare Workers 월 300만 요청 무료, Supabase DB 500MB 무료를 조합하면 특정 임계점 전까지는 거의 비용 없이 운영할 수 있어요. 단, 트래픽이 늘거나 DB 용량이 차면 비용이 비선형으로 올라가는 구조라 초기 설계가 중요해요."
  - question: "Fly.io 무료 플랜 한도 초과하면 얼마나 나오나요"
    answer: "Fly.io 무료 플랜은 공유 CPU 머신 3대, 월 160GB 아웃바운드 트래픽을 제공하며, 한도를 넘기면 공유 CPU 머신 1대 기준 월 약 1.94달러가 청구돼요. 가장 예상치 못한 비용이 발생하는 지점은 아웃바운드 트래픽으로, 160GB 초과 시 GB당 0.02달러가 붙어요. 이미지나 동영상을 직접 서빙하는 구조라면 Cloudflare 캐싱을 함께 사용하는 것이 비용 관리에 효과적이에요."
  - question: "Supabase 무료 플랜 2주 비활성 정지 피하는 방법"
    answer: "Supabase 무료 플랜은 2주간 활동이 없으면 프로젝트가 자동으로 일시 정지되는 조건이 있어요. 이를 피하려면 주기적으로 DB에 쿼리를 보내는 간단한 핑(ping) 스크립트를 Cloudflare Workers나 외부 크론 서비스로 자동화하는 방법이 자주 사용돼요. 사이드 프로젝트를 장기간 방치할 계획이라면 이 부분을 반드시 미리 설정해두는 것이 좋아요."
  - question: "Cloudflare Workers 무료 티어 실제로 개인 프로젝트에 충분한가요"
    answer: "Cloudflare Workers 무료 플랜은 하루 10만 요청, 월 환산 약 300만 요청을 제공해 개인 서비스 초기 단계에서는 오히려 남는 수준이에요. 비용이 발생하는 구간은 KV 쓰기가 하루 1,000회를 초과할 때로, 쓰기가 잦은 실시간 기능을 Workers KV에 의존하는 구조에서 유료 전환이 발생해요. API 게이트웨이나 엣지 로직 용도로만 사용한다면 사실상 0달러로 운영이 가능해요."
  - question: "AWS 대신 Fly.io Supabase 조합 쓰는 이유 비용 비교"
    answer: "1인 개발자 월 10달러 이하 인프라 Fly.io Cloudflare Workers Supabase 실제 비용 후기에서 비교한 데이터에 따르면, 동일 워크로드 기준 AWS EC2 t3.micro는 월 약 8~10달러인 반면 Fly.io 공유 CPU 머신은 월 1.94달러 수준이에요. AWS는 모르는 사이 청구서가 불어나는 구조인 반면, Fly.io·Cloudflare Workers·Supabase 조합은 무료에서 유료로 넘어가는 임계점이 명확해 비용 예측이 쉬운 것이 가장 큰 차이예요."
---

사이드 프로젝트를 AWS에 올렸다가 첫 달 청구서 보고 멈칫한 적 있죠? 월 10달러 이하로 실제 서비스를 운영하는 게 가능할까요? Fly.io, Cloudflare Workers, Supabase를 조합해 실제로 굴리는 1인 개발자들이 꽤 있어요. 이 조합이 정말 말이 되는지, 어디서 지갑이 열리는지 데이터 기반으로 풀어볼게요.

> **핵심 요약**
> - Fly.io 무료 플랜은 공유 CPU 3대, 메모리 256MB, 월 160GB 아웃바운드 트래픽을 제공하며 경량 백엔드 앱 운영에 충분한 수준이에요.
> - Cloudflare Workers 무료 티어는 하루 10만 요청, 스크립트당 10ms CPU 제한을 제공해 월 0달러로 엣지 API를 띄울 수 있어요.
> - Supabase 무료 플랜은 Postgres DB 500MB, 월 5GB 스토리지, 2주 비활성 시 프로젝트 일시 정지 조건이 붙어요.
> - 세 서비스를 조합하면 트래픽이 낮은 초기 서비스 기준 월 0~7달러 수준이 현실적이에요. 단, 특정 임계점을 넘으면 비용이 비선형으로 올라가요.

---

## 왜 지금 이 조합인가: 2026년 1인 개발자 인프라 지형

2023~2024년까지만 해도 선택지는 단순했어요. Heroku 유료화 이후 Railway나 Render로 갔다가, 거기서도 비용이 오르면 VPS로 내려오는 패턴이 반복됐죠.

그런데 2025년 이후 지형이 달라졌어요. Cloudflare Workers의 엣지 런타임이 성숙했고, Fly.io는 Machine API를 정식 출시하면서 컨테이너 관리가 단순해졌어요. Supabase는 2024년 GA를 선언한 뒤 무료 플랜 조건을 안정화했고요.

Philip Mutua가 Medium에서 정리한 클라우드 비용 분석에 따르면, 동일 워크로드 기준 AWS EC2 t3.micro 월 비용은 약 8~10달러인 반면 Fly.io 공유 CPU 머신은 월 1.94달러 수준이에요. SLA나 네트워크 품질 차이는 있지만, 트래픽이 하루 수천 건 이하인 초기 서비스라면 그 차이가 체감되는 경우는 드물어요.

Reddit의 Supabase 커뮤니티에서도 Cloudflare Workers를 Supabase 앞단에 놓아 Rate Limiting을 처리하는 패턴이 2025년 중반부터 실제 운영 사례로 자주 등장했어요. API 서버를 별도로 띄우지 않고, Workers가 요청을 검증한 뒤 Supabase에 넘기는 구조예요.

세 서비스 모두 "무료 → 유료 전환 임계점"이 명확해서 비용 예측이 가능해요. 모르는 사이 청구서가 불어나는 AWS 구조와 다른 점이 바로 이거예요.

---

## 서비스별 실제 비용 분해

### Fly.io: 컨테이너를 가장 싸게 띄우는 방법

Fly.io 무료 플랜(Hobby Free)은 2026년 3월 현재 다음을 제공해요:

- 공유 CPU-1x, 256MB RAM 머신 3대
- 월 160GB 아웃바운드 트래픽
- 3GB 영구 볼륨 스토리지

무료 한도를 넘기면 과금이 시작돼요. 공유 CPU 머신 기준 시간당 약 $0.0000022, 메모리는 GB당 시간당 $0.0000035예요. 한 달 내내 켜놓아도 공유 CPU 1대가 약 $1.94인 셈이에요.

주의할 건 트래픽이에요. 아웃바운드 160GB를 넘으면 GB당 $0.02가 붙어요. 이미지나 동영상을 직접 서빙하는 구조라면 여기서 예상치 못한 비용이 생길 수 있어요. 정적 파일은 Cloudflare에 캐싱하는 게 맞는 이유가 바로 이거예요.

### Cloudflare Workers: 사실상 0달러 API 레이어

Cloudflare Workers 무료 플랜은:

- 하루 10만 요청 (월 300만 요청)
- 요청당 CPU 10ms 제한
- Workers KV 읽기 10만 회/일, 쓰기 1,000회/일

월 300만 요청이면 개인 서비스 초기엔 오히려 남아도는 수준이에요. 비용이 발생하는 지점은 KV 쓰기 1,000회/일 한도를 넘겼을 때예요. 쓰기가 잦은 실시간 기능을 Workers KV에 의존하면 유료로 넘어가요.

Cloudflare 공식 요금 문서 기준, 유료 전환 시 Workers Paid는 월 $5부터 시작해요. 요청 1,000만 건과 KV 작업 1,000만 건이 포함돼요. 개인 서비스 수준에서는 무료 플랜으로 거의 다 해결되는 구조예요.

### Supabase: 편한 대신 조건이 있어요

Supabase 무료 플랜의 핵심 제한은 세 가지예요:

1. **Postgres DB 500MB** — 텍스트 기반 앱이면 충분하지만, 파일이나 이미지 메타데이터가 쌓이면 빠르게 찰 수 있어요.
2. **월 5GB 스토리지 대역폭** — 파일 다운로드가 많은 서비스는 여기서 막혀요.
3. **2주 비활성 시 프로젝트 일시 정지** — 사이드 프로젝트를 방치하면 갑자기 DB가 잠겨요.

실제 비용 후기로 가장 많이 올라오는 패턴은 이거예요. "무료로 잘 쓰다가 DB 500MB 꽉 차서 Pro($25/월)로 올렸다"는 케이스. 처음부터 데이터 사이즈를 추정하고 인덱스 관리를 해두면 6개월~1년은 무료로 버틸 수 있어요.

---

## 세 서비스 비교 분석

| 항목 | Fly.io | Cloudflare Workers | Supabase |
|------|--------|-------------------|----------|
| 무료 한도 | 머신 3대, 160GB 트래픽/월 | 요청 300만/월, KV 읽기 300만/월 | DB 500MB, 스토리지 5GB |
| 유료 시작 가격 | 사용량 기반 (~$1.94/머신) | $5/월 (Workers Paid) | $25/월 (Pro) |
| 비용 예측 가능성 | 중간 (트래픽 변동에 민감) | 높음 (요청 수 예측 쉬움) | 높음 (저장 용량 기준) |
| 콜드 스타트 | 있음 (수초) | 거의 없음 (<50ms) | 해당 없음 (DB) |
| 주요 리스크 | 아웃바운드 트래픽 초과 | KV 쓰기 한도 초과 | 2주 비활성 정지, DB 용량 |
| 추천 역할 | 백엔드 서버, 작업 처리 | API 게이트웨이, 엣지 로직 | 데이터베이스, 인증, 파일 |

트레이드오프를 한 줄로 정리하면 이렇게 돼요. Fly.io는 "내가 원하는 코드 뭐든 돌아가는 유연함", Cloudflare Workers는 "요청 응답이 가장 빠르고 비용 예측이 가능한 레이어", Supabase는 "DB + 인증 + 스토리지를 한 번에 묶어주는 대신 확장 시 비용 점프가 있는 구조"예요.

세 가지를 전부 쓰는 게 아니라 역할에 맞게 고르는 게 맞아요. 인증과 DB만 필요하면 Supabase 단독으로 충분해요. Workers를 쓰는 이유는 응답 속도나 Rate Limiting 같은 "API 앞단 로직"이 필요할 때예요.

---

## 실제 운영 시나리오: 얼마나 버틸 수 있을까

**시나리오 1: 노션 클론 (읽기 많음, 쓰기 적음)**
- 구조: Supabase (DB + 인증) + Cloudflare Workers (API 캐싱)
- 예상 비용: 월 $0~$5 (Supabase 무료 + Workers 무료)
- 권장 행동: Supabase Row Level Security 설정하고 Workers로 읽기 캐시. DB 읽기 횟수 줄이면 무료 플랜 오래 버텨요.

**시나리오 2: SaaS MVP (사용자 100~500명)**
- 구조: Fly.io (백엔드 API) + Supabase (DB) + Cloudflare (CDN/DNS)
- 예상 비용: Fly.io $1.94~$4 + Supabase $0 = 월 $2~$7
- 권장 행동: Fly.io에서 `fly scale count 1`로 머신 수를 최소화하고, DB 쿼리 느린 부분은 인덱스로 먼저 잡아야 해요.

**시나리오 3: 파일 업로드 서비스**
- 구조: Cloudflare R2 (스토리지) + Supabase (메타데이터)
- 예상 비용: R2 무료 티어 10GB 포함 + Supabase 무료 = 월 $0
- 권장 행동: Supabase Storage 대신 Cloudflare R2를 스토리지로 쓰면 5GB 대역폭 제한을 우회할 수 있어요. R2는 이그레스(다운로드) 비용이 없거든요.

---

## 결론: 월 10달러 이하, 조건부로 가능해요

허황된 얘기가 아니에요. 실제로 가능한 범위가 있어요.

- 트래픽이 하루 수천~수만 건 이하인 경우, 세 서비스 조합으로 **월 $0~$7**이 현실적
- DB 500MB, 스토리지 대역폭 5GB, Workers KV 쓰기 1,000회/일이 **실제 무료 한계선**
- Fly.io 아웃바운드 트래픽과 Supabase DB 용량이 **가장 먼저 터지는 지점**

앞으로 6개월 안에 볼 변화도 있어요. Cloudflare Workers가 Durable Objects 무료 한도를 확장하면 상태 저장 로직도 Workers에서 처리 가능해질 거예요. Supabase는 2026년 상반기 중 "Branching" 기능 정식 출시를 예고하고 있어서, 팀 협업 기능이 강화되면 Pro 플랜 전환 압박이 커질 수도 있어요.

결국 핵심은 이거예요. **지금 당장 비용을 0으로 만드는 게 목표가 아니라, 서비스가 성장할 때 어디서 비용이 올라가는지 미리 알고 있는 것**이에요.

당신의 서비스에서 가장 먼저 한도에 닿을 지점은 어디일 것 같으세요?

## 참고자료

1. [Cloudflare 가격 완전정복 | 무료부터 엔터프라이즈까지 요금제 비교 및 비용절감 팁](https://notavoid.tistory.com/740)
2. [💰 Ranking Cloud Providers: From Cheapest to Most Expensive (A Developer’s Perspective) | by Philip M](https://medium.com/@philip.mutua/ranking-cloud-providers-from-cheapest-to-most-expensive-a-developers-perspective-2fa8ed49b538)
3. [r/Supabase on Reddit: Rate limiting with nodejs or cloudflare workers](https://www.reddit.com/r/Supabase/comments/1k9oyct/rate_limiting_with_nodejs_or_cloudflare_workers/)


---

*Photo by [Microsoft Copilot](https://unsplash.com/@microsoftcopilot) on [Unsplash](https://unsplash.com/photos/woman-planting-a-small-houseplant-in-a-pot-MJLy1fUvX_w)*
