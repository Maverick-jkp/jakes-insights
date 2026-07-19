---
title: "1인 개발자가 Fly.io·Supabase·Cloudflare로 월 15달러 이하 풀스택 인프라 운영하는 법"
date: 2026-05-13T21:26:51+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-cloud", "/uac1c/ubc1c/uc790", "15/ub2ec/ub7ec", "/ud480/uc2a4/ud0dd", "Python"]
description: "Fly.io·Supabase·Cloudflare 조합으로 월 8~14달러 풀스택 인프라를 운영하는 1인 개발자의 실제 비용 내역. AWS 대비 75% 절감 방법과 각 서비스 무료 한도를 구체적으로 정리했어요."
image: "/images/20260513-1인-개발자-월-15달러-이하-풀스택-인프라-flyio.webp"
technologies: ["Python", "React", "Node.js", "FastAPI", "AWS"]
faq:
  - question: "1인 개발자 풀스택 인프라 월 15달러 이하로 운영 가능한가요"
    answer: "2025년 기준 Fly.io + Supabase + Cloudflare 조합을 사용하면 1인 개발자 월 15달러 이하 풀스택 인프라 운영이 실제로 가능하며, MAU 1,000명 이하 서비스 기준 월 평균 8~14달러가 실측 비용이에요. AWS 최소 구성(EC2 + RDS + CloudFront) 대비 약 75% 절감 효과가 있어서 사이드 프로젝트 초기 단계에서 수익보다 인프라 비용이 먼저 나가는 문제를 피할 수 있어요."
  - question: "Supabase free tier 7일 비활성 정지 해결 방법"
    answer: "Supabase Free Tier는 7일간 API 요청이 없으면 프로젝트가 자동 일시정지되고 수동으로 재개해야 하는데, 이를 피하려면 주기적으로 ping 요청을 보내는 크론잡을 설정하거나 Pro 플랜(월 25달러)으로 업그레이드하는 방법이 있어요. 사이드 프로젝트라면 Free Tier로 개발 단계를 진행하고 실제 사용자가 생긴 시점에 Pro로 전환하는 것이 현실적인 선택이에요."
  - question: "Fly.io 실제 비용 무료 범위 얼마나 되나요"
    answer: "Fly.io는 완전 무료가 아니라 매달 일정 사용량까지 청구되지 않는 Free Allowance 방식으로, 256MB RAM 머신 3대를 24시간 상시 운영하고 월 160GB 아웃바운드 트래픽까지 무료예요. MAU 1,000명 이하 Node.js나 FastAPI 서비스 기준으로 실제 청구 비용은 월 0~5달러 수준이며, Redis나 추가 볼륨이 필요할 경우 월 2~3달러가 추가돼요."
  - question: "Cloudflare Workers 무료 플랜 하루 요청 한도"
    answer: "Cloudflare Workers 무료 플랜은 하루 10만 요청까지 제공되며, 월 5달러 Paid Plan으로 업그레이드하면 하루 1,000만 요청까지 처리할 수 있어요. MAU 5,000명 이하 서비스라면 Free Plan으로도 충분하다는 것이 실제 개발자들의 중론이고, Cloudflare Pages를 함께 사용하면 프론트엔드 배포 비용은 무제한 무료예요."
  - question: "2025년 Fly.io Supabase Cloudflare 조합 vs AWS 비용 비교"
    answer: "1인 개발자 월 15달러 이하 풀스택 인프라 Fly.io Supabase Cloudflare 실제 비용 내역 2025 기준으로, MAU 100명 서비스에서 AWS는 월 25~35달러인 반면 이 조합은 월 0~5달러로 운영 가능해요. MAU 1,000명 기준에서도 AWS가 35~50달러인 데 비해 Fly.io + Supabase + Cloudflare 조합은 5~14달러 수준으로 유지되어 초기 스타트업이나 사이드 프로젝트에 실질적인 비용 절감 효과를 제공해요."
aliases:
  - "/tech/2026-05-13-1인-개발자-월-15달러-이하-풀스택-인프라-flyio-supabase-cloudflare/"
  - "/ko/tech/2026-05-13-1인-개발자-월-15달러-이하-풀스택-인프라-flyio-supabase-cloudflare/"

---

사이드 프로젝트를 AWS에 올렸다가 첫 달 청구서 보고 멈춘 적 있죠? EC2 + RDS + CloudFront 조합이면 트래픽이 거의 없어도 월 60달러는 기본이에요. 그런데 지금은 이야기가 완전히 달라졌어요.

> **핵심 요약**
> - Fly.io + Supabase + Cloudflare 조합으로 월 평균 8~14달러에 풀스택 인프라 운영이 가능하고, AWS 최소 구성 대비 약 75% 절감 효과가 있어요.
> - Supabase Free Tier는 PostgreSQL 500MB + Auth + Storage 1GB를 무료 제공하고, 유료 플랜은 월 25달러부터 시작해요 (2026년 기준).
> - Cloudflare Workers는 하루 10만 요청까지 무료이고, 월 5달러 Paid Plan으로 하루 1,000만 요청까지 처리 가능해요.
> - Fly.io는 무료 Machines(256MB RAM × 3대) 포함, 실사용 기준 월 5~7달러 선에서 Node.js/Python 백엔드 운영이 돼요.
> - 이 스택의 실제 한계는 비용이 아니라 Supabase Free Tier의 7일 비활성 일시정지 정책이에요.

---

## 1. "클라우드는 비싸다"는 공식이 깨진 시점

2022년까지만 해도 1인 개발자가 직접 서버를 구성한다는 건 곧 AWS를 쓴다는 의미였어요. Heroku가 무료 플랜을 폐지한 2022년 11월 이후, 대안을 찾던 커뮤니티에서 Fly.io와 Railway, Render가 빠르게 주목받기 시작했죠.

Supabase는 2020년에 출시됐고, 2023년 시리즈B에서 8,000만 달러를 조달하면서 엔터프라이즈급 안정성을 갖추기 시작했어요. Cloudflare Workers는 2017년 베타로 시작해서 지금은 전 세계 310개 이상 PoP(접속 거점)에서 실행되는 엣지 컴퓨팅 플랫폼이 됐고요.

이 세 서비스가 조합으로 언급되기 시작한 건 2024년 하반기부터예요. Indie Hacker 커뮤니티와 Hacker News 스레드에서 실제 비용 내역이 공유되면서 "정말 월 10달러대가 되냐"는 검증이 시작됐거든요.

그런데 왜 지금 다시 중요할까요? AI 코딩 도구 덕분에 1인 개발자가 만드는 프로덕트의 복잡도가 빠르게 올라갔어요. 백엔드, 인증, DB, CDN을 혼자 다 챙겨야 하는 상황에서 인프라 비용이 수익보다 먼저 나가면 지속이 안 되거든요.

---

## 2. 각 서비스 실제 비용 뜯어보기

### Fly.io: 가장 오해가 많은 과금 구조

Fly.io는 "무료"라고 알려져 있지만, 정확히는 **Free Allowance** 방식이에요. 매달 일정 사용량까지는 청구가 안 되는 구조죠.

2026년 기준 Free Allowance:
- shared-cpu-1x (256MB RAM): 월 2,160시간 (3대 24시간 상시 운영 가능)
- 스토리지: 3GB 볼륨
- 아웃바운드 트래픽: 월 160GB

Node.js나 FastAPI 앱 하나를 256MB로 운영하면 실제 초과 비용이 거의 안 나와요. 다만 Redis나 추가 볼륨이 필요하면 월 2~3달러 추가되고, 트래픽이 월 160GB를 넘으면 GB당 0.02달러가 붙어요. 실측 기준으로 MAU 1,000명 이하 서비스라면 Fly.io 단독 비용은 **월 0~5달러** 사이예요.

### Supabase: Free Tier의 숨겨진 조건

Supabase Free Tier는 명목상 꽤 매력적이에요.
- PostgreSQL 500MB
- Auth (소셜 로그인 포함)
- Storage 1GB
- Edge Functions 500만 호출/월
- Realtime 연결 200개

그런데 **7일 비활성 정지 정책**이 있어요. 7일간 API 요청이 없으면 프로젝트가 일시정지되고, 수동으로 재개해야 해요. 사이드 프로젝트에는 치명적이죠. Pro 플랜은 월 25달러인데, 여기서 8달러짜리 compute add-on을 빼면 실질적으로 월 25달러 + 사용량 과금이에요.

현실적인 선택지는 하나예요. Free Tier로 개발하고, 실제 사용자가 붙기 시작하면 Pro로 넘어가는 것. 총 비용은 **월 0달러(초기) → 25달러(성장기)**.

### Cloudflare: 가장 가성비 좋은 계층

Cloudflare는 구조가 단순해요.

- **Free Plan**: Workers 하루 10만 요청, Pages 무제한 배포, CDN 무제한
- **Paid Plan (월 5달러)**: Workers 하루 1,000만 요청, Workers KV 10억 읽기 포함

프론트엔드를 Cloudflare Pages에 올리면 배포 비용이 0원이에요. Workers로 간단한 API 라우팅이나 미들웨어를 짜면 Fly.io 요청 수를 줄이는 효과도 있고요. Workers 비용을 공유한 개발자들에 따르면, MAU 5,000명 이하에서는 Free Plan으로도 충분하다는 게 중론이에요.

---

## 3. 실제 스택 조합과 월별 비용 시뮬레이션

### 비용 비교 테이블

| 구성 항목 | AWS 최소 구성 | Fly.io + Supabase + Cloudflare |
|-----------|--------------|-------------------------------|
| 백엔드 서버 | EC2 t3.micro: ~$8.50/월 | Fly.io Free Allowance: $0~5 |
| 데이터베이스 | RDS t3.micro: ~$15/월 | Supabase Free: $0 (Pro: $25) |
| CDN/프론트 | CloudFront: $1~5/월 | Cloudflare Pages: $0 |
| 인증 | Cognito: $0.0055/MAU | Supabase Auth 포함 |
| 오브젝트 스토리지 | S3: $0.023/GB | Supabase Storage 1GB 무료 |
| **월 합계 (100 MAU)** | **$25~35** | **$0~5** |
| **월 합계 (1,000 MAU)** | **$35~50** | **$5~14** |
| **월 합계 (5,000 MAU)** | **$50~80** | **$25~40** |

5,000 MAU를 넘어가면 Supabase Pro가 사실상 필수라 비용 차이가 줄어들기 시작해요. 그 지점이 이 스택의 자연스러운 졸업 시점이기도 하고요.

### 실제 운영 시나리오: MAU 500명 SaaS

- Fly.io: Node.js 백엔드, shared-cpu-1x 1대 → **$0** (Free Allowance 내)
- Supabase: Free Tier (DB 50MB, Auth 200명) → **$0**
- Cloudflare Pages: React 프론트엔드 → **$0**
- Cloudflare Workers: API 게이트웨이, 하루 요청 2만건 → **$0**
- 도메인: Cloudflare Registrar 연간 $9 → **월 $0.75**

**월 합계: $0.75.** 도메인 값만 나가는 셈이에요.

---

## 4. 이 스택, 언제 바꿔야 할까

이 조합의 핵심 한계는 세 가지예요.

**첫째, Supabase Free Tier 비활성 정지.** 7일 방치하면 프로젝트가 멈춰요. 해결책은 단순해요. GitHub Actions로 6일마다 ping 요청을 보내는 cron job을 만들어 두면 돼요. 5분짜리 작업이에요.

**둘째, Fly.io 콜드 스타트.** 트래픽이 없으면 머신이 내려갔다가 다시 올라오는 데 2~5초 걸려요. B2B SaaS라면 문제가 될 수 있어요. `fly scale count 1 --region nrt`로 항상 최소 1대를 켜두면 해결되는데, 이러면 월 2~3달러가 추가돼요.

**셋째, Supabase 5,000 MAU 돌파 시점.** Pro 플랜($25/월)으로 넘어가는 게 맞지만, 이때부터는 PlanetScale이나 Neon + 자체 Auth를 검토해볼 만해요. 성장하는 프로덕트라면 DB 이전 비용을 감안해서 일찍 설계해 두는 게 낫거든요.

**참고로 앞으로 주시할 것:** Supabase는 2026년 1분기에 Free Tier 비활성 정책을 14일로 완화하는 방안을 논의 중이에요 (Supabase GitHub Discussions 참조). 이게 확정되면 사이드 프로젝트 실용성이 한 단계 더 올라가요.

---

## 5. 결론: 15달러 이하는 가능하고, 조건도 명확해요

정리하면 이렇게 돼요.

- MAU 500명 이하: 사실상 **월 1달러 미만** (도메인 제외)
- MAU 1,000명대: **월 5~14달러** (Fly.io 소규모 추가 비용)
- MAU 5,000명 돌파: **월 25~40달러** (Supabase Pro 필요)

다음 6~12개월 안에 주목할 변화도 두 가지예요. Cloudflare는 Workers AI를 확장하면서 이 스택에 LLM 추론 레이어를 더하려는 움직임이 있고, Fly.io는 2026년 상반기 중 GPU 머신 가격을 30% 낮추겠다고 발표했어요. 두 변화 모두 이 조합의 활용 범위를 넓히는 방향이에요.

지금 사이드 프로젝트를 멈춰두고 있다면, 인프라 비용 때문이라는 이유는 이제 유효하지 않아요. 15달러 예산이 있으면 오늘 시작할 수 있어요. 그렇다면 남은 질문은 하나예요. 비용 말고, 무엇이 실제로 막고 있나요?

---

*참고: Fly.io Free Allowance 및 과금 구조는 [Fly.io Pricing 공식 문서](https://fly.io/docs/about/pricing/), Supabase 플랜 비교는 [Supabase Pricing](https://supabase.com/pricing), Cloudflare Workers 과금은 [Cloudflare Workers Pricing](https://developers.cloudflare.com/workers/platform/pricing/) 기준입니다. 모든 수치는 2026년 5월 기준이며 변동 가능해요.*

## 참고자료

1. [풀스택 개발자 1인 외주, 정말 더 저렴할까? - 제로백데브](https://zero100dev.tistory.com/entry/%ED%92%80%EC%8A%A4%ED%83%9D-%EA%B0%9C%EB%B0%9C%EC%9E%90-1%EC%9D%B8-%EC%99%B8%EC%A3%BC-%EC%A0%95%EB%A7%90-%EB%8D%94-%EC%A0%80%EB%A0%B4%ED%95%A0%EA%B9%8C)
2. [Cloudflare 가격 완전정복 | 무료부터 엔터프라이즈까지 요금제 비교 및 비용절감 팁](https://notavoid.tistory.com/740)
3. [Cloudflare Workers 비용과 속도 경험기 - 개발한당 | 다모앙 - 종합 커뮤니티](https://damoang.net/development/2488)


---

*Photo by [Ales Nesetril](https://unsplash.com/@alesnesetril) on [Unsplash](https://unsplash.com/photos/gray-and-black-laptop-computer-on-surface-Im7lZjxeLhg)*
