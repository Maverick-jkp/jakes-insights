---
title: "1인 개발자가 Fly.io·Cloudflare Workers·Supabase 무료 플랜 조합으로 월 1만원 이하 인프라 실제 운영하기"
date: 2026-04-01T20:08:44+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-cloud", "\uac1c\ubc1c\uc790", "1\ub9cc\uc6d0", "\uc778\ud504\ub77c", "Python"]
description: "Fly.io·Cloudflare Workers·Supabase 무료 플랜 조합으로 사이드 프로젝트 인프라 비용을 월 9,000원대로 줄인 1인 개발자들의 실제 운영 경험. Supabase 7일 비활성화 자동 중지 등 실무"
image: "/images/20260401-1인-개발자-월-1만원-이하-인프라-flyio-clou.webp"
technologies: ["Python", "Node.js", "Docker", "AWS", "PostgreSQL"]
faq:
  - question: "1인 개발자 월 1만원 이하 인프라 Fly.io Cloudflare Workers Supabase 무료 플랜 조합 실제 운영 가능한가요"
    answer: "1인 개발자 월 1만원 이하 인프라로 Fly.io, Cloudflare Workers, Supabase 무료 플랜 조합을 실제 운영하는 것은 MAU 500명 이하, 일 요청 5만 건 이하 규모에서는 충분히 가능합니다. 세 서비스 모두 사용량 기반 과금 구조라 소규모 사이드 프로젝트나 MVP 단계에서는 실질적인 비용이 0원에 수렴해요. 다만 Supabase의 7일 비활성화 자동 중지 함정을 반드시 Uptime Robot 등으로 대응해야 합니다."
  - question: "Supabase 무료 플랜 7일 비활성화 자동 중지 해결 방법"
    answer: "Supabase 무료 플랜은 7일간 비활성 상태가 지속되면 프로젝트가 자동으로 중지되며, 재시작에 최대 수 분이 걸려 프로덕션 서비스에는 치명적입니다. 가장 많이 쓰는 해결책은 Uptime Robot 같은 무료 모니터링 서비스나 Cloudflare Workers Cron 트리거로 Supabase REST API를 주기적으로 호출하는 방법입니다. 자동 중지 없이 안정적으로 운영하려면 월 $25짜리 Pro 플랜으로 업그레이드하는 것도 선택지입니다."
  - question: "Fly.io 무료 티어 콜드 스타트 시간 얼마나 걸리나요"
    answer: "Fly.io 무료 티어 VM은 유휴 상태에서 자동 슬립 처리되며, 첫 요청 시 발생하는 콜드 스타트는 실측 기준 약 2~4초 수준입니다. 슬립을 방지하려면 주기적 핑을 보내면 되지만, 그만큼 무료 대역폭(월 160GB)을 소모하게 됩니다. 콜드 스타트가 없는 Cloudflare Workers를 API 게이트웨이로 앞단에 배치하면 사용자 체감 지연을 크게 줄일 수 있습니다."
  - question: "Cloudflare Workers 무료 플랜 하루 요청 한도 초과하면 어떻게 되나요"
    answer: "Cloudflare Workers 무료 플랜은 하루 10만 건(월 약 300만 건) 요청까지 무료로 처리하며, 한도 초과 시 추가 요청이 차단될 수 있습니다. MAU 800명, 일 요청 8만 건 수준이 되면 무료 한도에 근접하기 시작해 유료 전환을 검토해야 하는 시점이 됩니다. 요청 수를 줄이려면 Workers KV 캐싱을 적극 활용해 불필요한 백엔드 호출을 줄이는 것이 효과적입니다."
  - question: "사이드 프로젝트 서버비 줄이는 법 AWS 대신 쓸 수 있는 무료 인프라"
    answer: "AWS 프리티어와 달리 Fly.io, Cloudflare Workers, Supabase는 12개월 후 자동 과금 전환 없이 사용량 기반으로만 비용이 청구되어 사이드 프로젝트 서버비를 크게 줄일 수 있습니다. 1인 개발자 월 1만원 이하 인프라로 Fly.io, Cloudflare Workers, Supabase 무료 플랜 조합을 실제 운영한 사례에서는 뉴스레터 구독 관리나 소규모 SaaS MVP를 월 청구 0원으로 운영한 경우도 있습니다. 스케일링 임계점은 대략 MAU 1,000명 수준으로, 그 이전까지는 세 서비스 조합만으로도 충분히 프로덕션 운영이 가능합니다."
---

매달 서버비가 걱정되던 사이드 프로젝트, 혹시 있었나요?

"또 AWS 청구서 왔어. 이번 달도 10만원이네."

사이드 프로젝트 하나 돌리는 데 10만원. 수익은 0원인데요. 그런데 이걸 월 9,000원 수준으로 낮춘 개발자들이 2026년 현재 꽤 많아졌어요. Fly.io, Cloudflare Workers, Supabase 조합으로요.

> **핵심 요약**
> - Fly.io 무료 티어: 공유 CPU VM 3개(각 256MB RAM), 월 160GB 아웃바운드 대역폭 무료
> - Cloudflare Workers 무료 플랜: 하루 10만 건 요청 처리, Workers KV 스토리지 1GB 무료
> - Supabase 무료 플랜: 500MB DB + 1GB 스토리지. 단, **7일 비활성화 시 자동 중지**가 최대 함정
> - 세 서비스 조합 시 MAU 500명 이하, 일 요청 5만 건 이하에서는 실제 비용 0원에 수렴
> - 스케일링 임계점(월 $10 초과)은 대략 MAU 1,000명 수준

---

## 이 조합이 주목받게 된 이유

2022~2023년, Heroku 무료 플랜이 종료됐어요. Railway 무료 티어도 축소됐고요. 대안을 찾던 개발자들 사이에서 엣지 컴퓨팅 기반 서비스들이 떠올랐어요.

Cloudflare Workers는 2017년 출시됐지만, 무료 플랜 한도가 2022년 이후 대폭 올라가면서 실질적인 선택지가 됐어요. Fly.io는 2020년 창업해 2023년 시리즈 B로 $60M을 조달하며 글로벌 엣지 배포 인프라를 꾸준히 늘렸고요. Supabase는 2020년 오픈소스 Firebase 대안으로 출발해 지금은 월간 활성 프로젝트 100만 개 이상을 보유하고 있어요.

세 서비스의 공통점이 있어요. **무료 플랜을 실제 프로덕션 수준으로 운영 가능하게 설계했다는 거예요.** AWS 프리티어처럼 12개월 후 자동 과금 전환이 아니라, 사용량 기반이에요. 안 쓰면 안 내도 되는 구조죠.

2025년 하반기부터 한국 개발자 커뮤니티에서도 이 조합 실사용기가 늘고 있어요. 단순 소개가 아니라 "3개월 운영 후기", "비용 청구서 공개" 형태로요.

---

## 세 서비스, 실제 스펙은 이래요

### Fly.io: 컨테이너를 엣지에서 돌린다

Fly Machines 단위로 컨테이너를 25개 이상 글로벌 리전에서 실행해요. 무료 티어(Hobby Plan) 스펙은 이렇고요.

- 공유 CPU, 256MB RAM VM 3개
- 월 160GB 아웃바운드 대역폭
- 3GB 볼륨 스토리지

Docker 이미지를 그대로 올리면 되니까 Node.js, Python, Go 뭐든 돌아가요. 다만 무료 VM은 유휴 상태에서 자동 슬립이 돼요. 첫 요청 시 콜드 스타트가 발생하는데, 실측 기준 약 2~4초예요. 주기적 핑으로 슬립을 방지할 수 있지만, 그러면 대역폭을 쓰게 되죠.

### Cloudflare Workers: 엣지에서 실행하는 서버리스

V8 엔진 기반으로 전 세계 300개 이상 PoP에서 코드를 실행해요. 무료 플랜 스펙은 아래와 같아요.

- 일 10만 건 요청 (월 약 300만 건)
- CPU 시간: 요청당 10ms
- Workers KV: 100만 읽기/일, 1,000 쓰기/일, 1GB 스토리지

진짜 장점은 **콜드 스타트가 사실상 없다는 거예요**. V8 인스턴스가 전 세계에 상시 대기 중이라 p99 레이턴시가 50ms 이하예요. API 라우팅, 인증 미들웨어, 정적 에셋 캐싱에 딱 맞아요. 다만 CPU 10ms 제한 때문에 복잡한 연산은 못 해요.

### Supabase: PostgreSQL + Auth + Storage를 한 번에

무료 플랜 제공 내역은 이래요.

- PostgreSQL 500MB
- Auth: 무제한 사용자
- Storage: 1GB
- Edge Functions: 50만 건/월

**핵심 제약은 7일 비활성화 시 자동 프로젝트 중지예요.** 중지된 프로젝트는 재시작에 최대 수분이 걸려요. 프로덕션 서비스라면 치명적이에요. 해결법은 두 가지예요. Uptime Robot 같은 무료 모니터링 서비스로 주기적 핑을 보내거나, Pro 플랜(월 $25)으로 올리는 거예요.

---

## 조합 비교: 어떤 아키텍처가 현실적인가요?

| 항목 | Fly.io 단독 | Workers + Supabase | 세 서비스 조합 |
|------|------------|-------------------|--------------|
| 월 비용 (소규모) | $0 | $0 | $0 |
| 콜드 스타트 | 2~4초 | 없음 | 없음 (엣지 라우팅) |
| DB 내장 | ❌ 별도 필요 | ✅ Supabase | ✅ Supabase |
| 커스텀 런타임 | ✅ Docker | ❌ V8만 | ✅ 분리 운영 |
| 스케일링 한계 | RAM 256MB | CPU 10ms | 복잡도 증가 |
| 슬립 문제 | 있음 | 없음 | DB만 주의 |
| 적합한 규모 | API 서버 | 가벼운 엣지 처리 | MAU 500 이하 |

실제로 가장 많이 쓰는 패턴은 이래요. **Cloudflare Workers가 API 게이트웨이** 역할을 하고, 무거운 비즈니스 로직은 **Fly.io**, 데이터는 **Supabase**에 저장하는 구조예요. Workers가 앞단에서 인증 체크, 캐싱, 라우팅을 처리하니까 Fly.io VM이 받는 요청 수가 줄어요. Supabase 자동 중지 문제는 Workers Cron 트리거로 주기적으로 Supabase REST API를 호출해 해결하는 경우가 많고요.

---

## 실제로 어디서 돈이 나올까요?

**시나리오 1: 뉴스레터 구독 관리 서비스 (MAU 200명)**
Workers로 구독 폼 처리, Supabase로 이메일 목록 저장, Fly.io에서 발송 로직 실행. 세 서비스 모두 무료 한도 안이에요. 월 청구 $0.

**시나리오 2: 소규모 SaaS MVP (MAU 800명, 일 요청 8만 건)**
Workers 무료 한도(일 10만 건)에 근접해요. Fly.io 대역폭도 월 100GB 수준으로 올라오고요. 이 시점부터 Workers $5/월 Paid Plan을 고려하게 돼요. 총 월 $5~10 수준이에요.

**시나리오 3: 트래픽 스파이크 (하루 50만 건 요청)**
Workers Paid Plan 초과 요청이 과금되기 시작해요($0.30/100만 건). 하루 50만 건이면 월 1,500만 건, 초과분 약 1,200만 건 → $3.6 추가. 그래도 월 $10 이하예요. 이게 이 조합의 진짜 강점이에요.

그다음 주시해야 할 신호 세 가지예요.
- Supabase Pro 전환 시점: DB가 400MB를 넘는 순간
- Fly.io 유료 전환: VM 3개로 부족하거나 볼륨 3GB 초과 시
- Workers R2 추가: 이미지나 파일 스토리지가 필요해질 때 ($0.015/GB/월)

---

## 이 조합이 맞는 사람 vs 아닌 사람

명확한 스위트 스팟이 있어요.

- **잘 맞는 경우**: MAU 500 이하, 초기 MVP 검증, 사이드 프로젝트 장기 운영
- **안 맞는 경우**: 실시간 게임 서버, 머신러닝 추론, 대용량 파일 처리

앞으로 변수도 있어요. 경쟁 서비스 Neon(서버리스 PostgreSQL)이 자동 중지 없는 무료 플랜으로 빠르게 성장하고 있거든요. Supabase가 자동 중지 정책을 완화할 가능성도 있어요. Fly.io도 2025년에 GPU 지원을 무료 티어에 일부 포함하는 방향을 검토 중이라고 밝혔고요.

하나만 기억하면 돼요. **Supabase 7일 비활성 중지는 반드시 사전에 대비해야 해요.** 서비스가 조용히 죽어있는 걸 사용자가 먼저 발견하면, 그때는 이미 늦으니까요.

이 조합으로 직접 뭔가 만들어보고 있나요? 어떤 규모에서 첫 과금을 맞닥뜨렸는지 궁금하네요.

## 참고자료

1. [* 무료 플랜 특징 1. Supabase 무료 플랜은 개인 프로젝트나 학습용으로 충분 2. 가장 중요한 건, 1주일간 활동이 없으면 프로젝트가 자동 중지. 3. 중지된 프로젝트는 ](https://www.threads.com/@ghil_book_pic/post/DPsojPbE2KK/-%EB%AC%B4%EB%A3%8C-%ED%94%8C%EB%9E%9C-%ED%8A%B9%EC%A7%951-supabase-%EB%AC%B4%EB%A3%8C-%ED%94%8C%EB%9E%9C%EC%9D%80-%EA%B0%9C%EC%9D%B8-%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8%EB%82%98-%ED%95%99%EC%8A%B5%EC%9A%A9%EC%9C%BC%EB%A1%9C-%EC%B6%A9%EB%B6%842-%EA%B0%80%EC%9E%A5-%EC%A4%91%EC%9A%94%ED%95%9C-%EA%B1%B4-1%EC%A3%BC%EC%9D%BC%EA%B0%84-%ED%99%9C%EB%8F%99%EC%9D%B4-%EC%97%86%EC%9C%BC%EB%A9%B4-%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8%EA%B0%80-%EC%9E%90%EB%8F%99-%EC%A4%91%EC%A7%803)
2. [1인 개발자의 다수 프로젝트 운영을 위한 Supab... - Inflearn | Community Q&A](https://www.inflearn.com/en/community/questions/1780024/1%EC%9D%B8-%EA%B0%9C%EB%B0%9C%EC%9E%90%EC%9D%98-%EB%8B%A4%EC%88%98-%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8-%EC%9A%B4%EC%98%81%EC%9D%84-%EC%9C%84%ED%95%9C-supabase-%EB%B9%84%EC%9A%A9-%EC%B5%9C%EC%A0%81%ED%99%94-%EC%A0%84%EB%9E%B5-db-%ED%86%B5%ED%95%A9-%EC%97%90-%EB%8C%80%ED%95%B4-%EC%A1%B0%EC%96%B8%EC%9D%84-%EA%B5%AC%ED%95%A9%EB%8B%88%EB%8B%A4)
3. [Cloudflare 가격 완전정복 | 무료부터 엔터프라이즈까지 요금제 비교 및 비용절감 팁](https://notavoid.tistory.com/740)


---

*Photo by [Microsoft Copilot](https://unsplash.com/@microsoftcopilot) on [Unsplash](https://unsplash.com/photos/woman-working-at-desk-with-coffee-8UnGiO4yesk)*
