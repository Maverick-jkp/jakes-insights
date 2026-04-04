---
title: "1인 개발자 월 5달러 이하 풀스택 배포 가능한가 — Fly.io·Supabase·Cloudflare 실제 비용 후기"
date: 2026-04-04T19:48:00+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-cloud", "\uac1c\ubc1c\uc790", "5\ub2ec\ub7ec", "\ud480\uc2a4\ud0dd", "Next.js"]
description: "Fly.io·Supabase·Cloudflare 조합으로 월 5달러 이하 풀스택 운영이 실제 가능한지 검증했습니다. 256MB RAM 무료 VM, 500MB DB, 하루 10만 요청 무료 등 2026년 실제 비용 수치를 낱"
image: "/images/20260404-1인-개발자-월-5달러-이하-풀스택-배포-flyio-s.webp"
technologies: ["Next.js", "Docker", "AWS", "PostgreSQL", "Cloudflare"]
faq:
  - question: "1인 개발자 월 5달러 이하 풀스택 배포 Fly.io Supabase Cloudflare 실제 비용 후기 믿을 수 있나요"
    answer: "실제 사용자 1,000명 미만 기준으로 Fly.io + Supabase + Cloudflare 조합은 월 0~5달러 운영이 현실적으로 가능합니다. 다만 Supabase의 7일 비활성 프로젝트 정지 정책, Fly.io 볼륨 삭제 누락 과금 같은 숨어 있는 함정을 미리 알아야 실제로 저비용 유지가 됩니다."
  - question: "Supabase 무료 플랜 7일 비활성 정지 우회 방법"
    answer: "많은 1인 개발자들이 크론잡으로 5분마다 Supabase 엔드포인트에 ping을 보내는 방식으로 비활성 정지를 우회하고 있습니다. Cloudflare Workers의 무료 Cron Trigger 기능을 활용하면 추가 비용 없이 이 방법을 구현할 수 있습니다."
  - question: "Fly.io 무료 티어 VM 3개로 Next.js 풀스택 앱 운영 가능한가요"
    answer: "Next.js 앱, API 서버, 스케줄러 각각 하나씩 올리면 무료 VM 3개가 딱 차는 구조라 여유가 없습니다. 볼륨 스토리지도 3GB를 초과하면 GB당 0.15달러가 추가 청구되며, 앱을 내려도 볼륨을 명시적으로 삭제하지 않으면 요금이 계속 부과되는 점을 주의해야 합니다."
  - question: "Cloudflare Workers vs 일반 서버리스 함수 콜드 스타트 차이"
    answer: "Cloudflare Workers는 V8 Isolate 기반으로 동작해 일반 서버리스 함수와 달리 콜드 스타트가 사실상 없습니다. 첫 요청에도 빠르게 응답하기 때문에 트래픽이 드문드문 발생하는 1인 개발자 사이드 프로젝트에 특히 유리합니다."
  - question: "1인 개발자 월 5달러 이하 풀스택 배포 Fly.io Supabase Cloudflare 실제 비용 후기 월 2000명 사용자도 가능한가요"
    answer: "월 2,000 MAU 구간에서는 Fly.io 리소스를 소폭 늘려야 해 합계 비용이 3~7달러 수준으로 올라갑니다. Supabase를 Free 플랜으로 유지하면 5달러 이하가 가능하지만, 이 시점부터 월 25달러 Pro 플랜 전환을 진지하게 고민해야 하는 단계입니다."
---

AWS 청구서 보고 멈칫한 적 있죠? 사이드 프로젝트 올렸더니 첫 달에 예상보다 몇 배가 나왔을 때 그 기분. 월 5달러 이하로 풀스택 서비스를 운영하는 게 진짜 가능한지, 아니면 그냥 마케팅 문구인지 — 2026년 현재 실제 숫자로 따져봤어요.

> **핵심 요약**
> - Supabase Free 플랜은 월 500MB 데이터베이스 + 1GB 스토리지를 제공하고, Pro 플랜은 월 25달러부터 시작해요.
> - Fly.io는 256MB RAM 공유 CPU VM 3개 + 3GB 영구 볼륨을 무료로 제공해서, 소규모 백엔드 실행에 실질적인 선택지예요.
> - Cloudflare Workers는 하루 10만 요청까지 무료라서, 트래픽이 낮은 1인 개발자 앱에는 사실상 비용 제로예요.
> - 세 서비스를 잘 묶으면 월 활성 사용자 1,000명 미만 앱 기준 월 0~5달러 운영이 현실적으로 가능해요.

---

## 왜 이 조합이 지금 주목받는가

1인 개발자 커뮤니티에서 가장 자주 등장하는 스택 조합이 있어요. `Fly.io + Supabase + Cloudflare`. 소위 "무료 티어 스택"이라 불리는 이 조합은 Hacker News, Indie Hackers, X 개발자 스레드에서 반복적으로 등장하고 있어요.

배경은 단순해요. Heroku가 2022년 무료 티어를 없앤 이후, 소규모 프로젝트 올릴 곳을 잃은 개발자들이 대안을 찾기 시작했거든요. Railway, Render, Fly.io 같은 서비스들이 그 공백을 빠르게 채웠고, 2024~2025년을 거치며 실제 사용 후기들이 쌓였어요.

그리고 2026년에 특히 주목받는 이유가 하나 더 있어요. AI 도구 덕분에 1인 개발자가 혼자서도 풀스택 앱을 빠르게 만들 수 있게 됐거든요. 만드는 건 쉬워졌는데, 올리는 비용이 높으면 수익이 나기 전에 지갑이 먼저 닫혀요.

---

## 서비스별 실제 비용 구조 분석

### Supabase: 무료 티어의 진짜 한계

Supabase는 PostgreSQL DB + 인증 + 스토리지 + 실시간 기능을 하나로 묶어주는 BaaS예요.

Free 플랜 실제 스펙:
- PostgreSQL DB: 500MB
- 파일 스토리지: 1GB
- Auth: 월 50,000 MAU
- Edge Functions: 월 50만 호출
- 대역폭: 5GB

결정적인 문제는 **비활성 프로젝트 일시 정지 정책**이에요. 7일 동안 접속이 없으면 프로젝트가 잠겨요. 재활성화는 가능하지만, 사용자가 앱에 접근했을 때 즉시 응답이 안 돼요. 트래픽이 드문드문 있는 사이드 프로젝트에는 꽤 치명적이죠.

월 25달러 Pro로 전환하면 8GB DB, 100GB 스토리지, 일시 정지 없음이 제공돼요. 실제 사용자가 생기기 시작했다면, 그때 올리는 게 맞아요.

### Fly.io: 숨어 있는 과금 포인트

Fly.io는 Docker 컨테이너 기반으로 앱을 배포하는 서비스예요. Heroku의 자리를 직접 노리고 만든 서비스죠.

무료 한도:
- 공유 CPU-1x + 256MB RAM VM 3개
- 3GB 영구 볼륨
- 160GB 아웃바운드 트래픽/월

실제로 쓰다 보면 VM 3개가 생각보다 금방 차요. Next.js 앱 하나, API 서버 하나, 스케줄러 하나 올리면 딱 찰 때. 볼륨 스토리지도 3GB를 넘기면 GB당 0.15달러가 추가로 붙어요.

핵심 장점은 글로벌 리전이에요. 도쿄, 싱가포르, 프랑크푸르트 등 30개 이상 리전에서 실행할 수 있고, 한국 사용자 기준으로 도쿄 리전이 레이턴시가 가장 낮아요.

### Cloudflare: 가장 관대한 무료 플랜

세 서비스 중 무료 티어가 가장 넉넉해요.

| 기능 | 무료 한도 |
|------|----------|
| Workers (서버리스 함수) | 하루 10만 요청 |
| Pages (정적/SSR 배포) | 무제한 사이트, 월 500 빌드 |
| R2 스토리지 | 월 10GB 저장, 100만 읽기 |
| KV 스토리지 | 월 10만 읽기 |

Workers는 콜드 스타트가 없어요. 일반 서버리스 함수들이 첫 요청에 느린 반면, Cloudflare Workers는 V8 Isolate 기반이라 응답이 빠르게 떠요. 이게 실제 사용에서 느껴지는 가장 큰 차이예요.

---

## 규모별 예상 비용

| 구분 | 개발 중 | 월 500 MAU | 월 2,000 MAU |
|------|--------|-----------|-------------|
| Supabase | 무료 (비활성 주의) | 무료 | 무료 |
| Fly.io | 무료 | 무료~1달러 | 3~5달러 |
| Cloudflare | 무료 | 무료 | 무료~2달러 |
| **합계** | **$0** | **$0~1** | **$3~7** |

월 2,000 MAU 시점에서 Fly.io 리소스를 살짝 늘려야 하는 경우가 생겨요. Supabase Pro로 올리지 않는다면 5달러 이하 유지가 가능해요. 단, 비활성 정지 이슈를 크론잡으로 우회(5분마다 ping)하는 방식을 많은 개발자들이 쓰고 있어요.

---

## 시나리오별 현실 점검

**시나리오 1: 포트폴리오/데모 앱**
Cloudflare Pages + Supabase Free로 충분해요. 비용 제로. 단, 7일 이상 아무도 안 들어오면 Supabase가 잠기니까 알림 설정은 해두는 게 나아요.

**시나리오 2: 실제 사용자가 있는 사이드 프로젝트**
Fly.io 도쿄 리전 + Supabase Free + Cloudflare Workers 조합이에요. 여기서 주의할 게 하나 있어요. Fly.io 볼륨은 명시적으로 삭제하지 않으면 과금이 계속돼요. 앱을 내려도 볼륨 요금은 따로 붙어요. 실제로 이걸 몰라서 한 달 3달러씩 나간 사례가 Fly.io 포럼에 반복적으로 올라와요.

**시나리오 3: 수익화 직전 단계 (월 500~2,000 사용자)**
이 구간이 가장 까다로워요. Supabase Free의 한계가 보이기 시작하고, Fly.io도 리소스를 조금 늘려야 해요. Supabase Pro 25달러 전환을 고민하게 되는 시점인데, 첫 유료 결제 전에 수익 지표를 먼저 확인하는 게 나아요.

---

## 결론: 가능하지만, 조건이 있어요

Supabase + Fly.io + Cloudflare 조합으로 월 1,000명 미만 앱은 실제로 0~3달러 운영이 가능해요. 그런데 세 가지 함정을 조심해야 해요. 비활성 정지, 볼륨 과금, 트래픽 급증 시 예상치 못한 청구서 — 이 세 가지가 가장 자주 당하는 지점이에요.

참고로 2026년 하반기에 Supabase가 무료 티어 비활성 정책을 완화할 가능성이 거론되고 있어요. srvrlss.io 분석에 따르면 경쟁 압박으로 인해 정책 조정 가능성이 있어요.

수익이 생기기 시작하면 Pro 전환을 주저하지 말아요. 5달러 아끼려다 사용자 경험을 깎는 건 좋은 거래가 아니에요.

앞으로 주시할 건 하나예요. Cloudflare가 D1(서버리스 SQLite)을 Workers와 통합 심화하면, Supabase 없이 Cloudflare 단독 풀스택이 더 현실적인 선택지가 될 거예요. 지금도 간단한 앱은 D1만으로 가능하거든요. 그 시점이 오면 비용 구조가 또 한 번 바뀔 거예요.

비용보다 먼저 고민해야 할 건 사실 하나예요. 7일 안에 누군가 다시 들어올 만한 앱을 만들었느냐 — 그게 먼저예요.

## 참고자료

1. [Supabase | Review, Pricing & Alternatives](https://getdeploying.com/supabase)
2. [Supabase Review 2026 - Features, Pricing & Alternatives | srvrlss](https://www.srvrlss.io/provider/supabase/)


---

*Photo by [NASA](https://unsplash.com/@nasa) on [Unsplash](https://unsplash.com/photos/photo-of-outer-space-Q1p7bh3SHj8)*
