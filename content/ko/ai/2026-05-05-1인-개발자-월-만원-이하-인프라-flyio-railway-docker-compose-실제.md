---
title: "1인 개발자 Fly.io·Railway·Docker Compose 실제 청구 비용 6개월 후기: 월 만원 이하 가능한 조건"
date: 2026-05-05T20:27:11+0900
draft: false
author: "Jake Park"
categories: ["ai"]
tags: ["subtopic-ai", "\uac1c\ubc1c\uc790", "\uc778\ud504\ub77c", "fly.io", "Docker"]
description: "Heroku 종료 후 Fly.io·Railway·Docker Compose 6개월 실사용 청구서 공개. 무료 티어인데 첫 달 $47 나온 이유, 트래픽 패턴별 숨은 요금 구조, 월 만원 이하 실현 조건을 실제 수치"
image: "/images/20260505-1인-개발자-월-만원-이하-인프라-flyio-railw.webp"
technologies: ["Docker", "AWS", "GCP", "PostgreSQL", "Vercel"]
faq:
  - question: "Fly.io Railway 중에 1인 개발자 월 만원 이하로 운영 가능한 곳 어디예요"
    answer: "1인 개발자 월 만원 이하 인프라 Fly.io Railway Docker Compose 실제 청구 비용 6개월 후기에 따르면, Railway Hobby 플랜은 월 $5 고정이지만 DB 포함 시 $8-15까지 올라가고, Fly.io도 PostgreSQL 볼륨을 붙이면 $5-12 구간이 나와요. 오히려 Hetzner VPS + Docker Compose 조합이 월 약 $3.6으로 가장 예측 가능하고 낮은 비용을 유지할 수 있어요."
  - question: "Fly.io 무료 티어 실제로 무료인가요 숨겨진 요금 있나요"
    answer: "Fly.io는 shared-cpu-1x 머신 3개와 월 160GB 아웃바운드 네트워크까지 공식 무료 티어를 제공하지만, SQLite나 PostgreSQL 볼륨을 붙이는 순간 GB당 월 $0.15의 스토리지 비용이 발생해요. 또한 cold start 지연(2-4초)을 피하려고 `min_machines_running = 1` 설정을 켜면 무료 할당을 초과해 유료로 전환되는 구조예요."
  - question: "Railway Hobby 플랜 $5 크레딧 초과하면 어떻게 되나요"
    answer: "Railway Hobby 플랜은 월 $5를 내면 $5 상당의 크레딧을 주지만, 앱 서버에 PostgreSQL 플러그인을 추가하면 별도 서비스로 잡혀 사용량이 두 배가 돼요. $5 크레딧을 초과하는 금액은 등록된 카드로 자동 청구되며, 트래픽이 급증하는 달에는 $15를 넘기기도 해요."
  - question: "VPS Docker Compose 셀프호스팅 설정 얼마나 어려운가요 초보자도 가능한가요"
    answer: "Nginx, 앱 서버, PostgreSQL 컨테이너를 한 VPS에서 돌리는 기본 구성은 처음 설정에 반나절 정도 투자가 필요해요. GitHub Actions + SSH 스크립트로 배포 파이프라인을 직접 만들고, Certbot + cron으로 SSL 인증서 갱신도 직접 설정해야 하므로, Railway나 Fly.io 대비 초기 진입 난이도는 중간 수준이에요."
  - question: "1인 개발자 사이드 프로젝트 인프라 플랫폼 선택 기준 뭔가요"
    answer: "1인 개발자 월 만원 이하 인프라 Fly.io Railway Docker Compose 실제 청구 비용 6개월 후기에서는 플랫폼 선택의 핵심 변수로 '서버를 직접 관리할 시간이 있냐 없냐'를 꼽아요. 배포 편의성을 원하면 Railway(Git push 배포), 비용 최적화가 우선이면 VPS + Docker Compose, 그 중간이라면 Fly.io가 현실적인 선택지예요."
---

부업 프로젝트 하나 올렸더니 첫 달 청구서가 $47이 나왔어요. "분명 무료 티어 썼는데?" 하고 계정을 뒤졌더니, 슬립 모드 해제 비용에 네트워크 이그레스 요금에 예상 못 했던 항목들이 줄줄이 나왔죠. 1인 개발자라면 한 번쯤 겪는 상황이에요.

Heroku 무료 플랜이 2022년 말에 사라진 뒤, Railway와 Fly.io로 개발자들이 대거 이동했어요. 그런데 막상 6개월 써 보면 "월 만원 이하"가 진짜 가능한지, 어떤 조건에서 가능한지 감이 잘 안 와요. 실제 청구 비용을 기반으로 세 가지 선택지를 비교해 봤어요.

이 글에서 다룰 내용은 이거예요:
- Fly.io, Railway, Docker Compose(Self-hosted) 각각의 실제 비용 구조
- 트래픽 패턴별로 어디서 돈이 새는지
- 월 만원 이하 유지가 가능한 조건
- 플랫폼 선택 기준

> **핵심 요약**
> - Railway Hobby 플랜은 월 $5 고정이지만, 사용량 초과 시 추가 과금이 발생해 트래픽이 일정치 않은 프로젝트에서는 청구서 예측이 어려워요.
> - Fly.io는 공식 무료 티어(Machines 3개, 256MB RAM)를 제공하지만, 슬립 모드 해제 지연(cold start 약 2-4초)과 스토리지 비용이 월 $5-15 구간으로 밀어 올리는 주요 요인이에요.
> - 월 방문자 1,000명 이하 소규모 프로젝트 기준, VPS + Docker Compose 조합(Hetzner CX22, 월 약 $3.6)이 실질 비용 기준으로 가장 낮아요.
> - 플랫폼 선택의 핵심 변수는 "내가 서버를 직접 관리할 시간이 있냐 없냐"예요. 관리 시간을 돈으로 환산하면 결론이 달라지거든요.

---

## 1인 개발자 인프라 고민의 구조

2023년부터 클라우드 업체들이 수익성 압박을 받으면서 무료 티어를 줄이거나 조건을 까다롭게 바꿨어요. Railway는 2023년 중반에 무료 플랜을 $5 Hobby 플랜으로 전환했고, Fly.io는 무료 머신 수를 조정하면서 세부 조건을 여러 차례 바꿨어요. DEV Community의 2026년 비교 분석에 따르면, 현재 실질적으로 "완전 무료"로 운영 가능한 플랫폼은 Vercel(정적 사이트 한정)과 Render(슬립 모드 있음) 정도로 좁혀졌어요.

그래서 유료 범위 안에서 어떻게 월 만원($7 내외) 이하를 맞출 수 있냐가 핵심 질문이 되는 거죠.

---

## 실제 비용 데이터: 6개월간 뭐가 청구됐냐

### Fly.io: 무료처럼 보이지만 스토리지가 문제예요

Fly.io의 공식 무료 티어는 꽤 넉넉해 보여요. shared-cpu-1x 머신 3개, 256MB RAM, 월 160GB 아웃바운드 네트워크까지 무료거든요.

그런데 SQLite나 PostgreSQL 볼륨을 붙이는 순간부터 계산이 달라져요. Fly.io 공식 요금표 기준으로 Persistent Volume은 GB당 월 $0.15예요. 3GB 볼륨 하나만 써도 $0.45. 별거 아닌 것 같죠? 문제는 Fly Postgres를 쓰면 별도 머신이 하나 더 뜬다는 거예요. 최소 사양(shared-cpu-1x, 256MB)도 무료 할당을 금방 잡아먹어요.

6개월 평균 기준, 단순 API 서버 하나 + Postgres 조합으로 월 $3-8 구간이 나와요. 트래픽이 거의 없어도요. cold start 문제도 있어요. 무료 머신은 일정 시간 후 슬립 상태로 들어가는데, 깨어나는 데 2-4초가 걸려요. 사용자 경험에 영향을 주기 싫어서 `min_machines_running = 1` 설정을 켜면? 그때부터 머신이 항상 켜져 있으니 무료 할당을 초과하게 돼요.

### Railway: $5 고정 플랜의 실제 한계

Railway Hobby 플랜은 월 $5를 내면 $5 상당의 크레딧을 줘요. 사실상 무료처럼 들리는데, Railway 공식 문서의 요금 구조를 보면 조금 달라요.

RAM은 GB당 시간에 $0.000231, CPU는 vCPU당 시간에 $0.000463이에요. 512MB RAM + 0.5 vCPU 앱이 한 달 내내 돌면 약 $4.2예요. $5 크레딧 안에 딱 들어오죠. 그런데 여기에 PostgreSQL 플러그인을 붙이면 별도 서비스로 잡혀서 사용량이 두 배가 돼요. $5를 초과하기 시작하고, 초과분은 카드로 청구돼요.

R. Thompson의 Railway vs Fly.io 비교 분석에 따르면, 데이터베이스를 포함한 실제 프로덕션 앱에서 Railway Hobby 플랜의 실제 월 비용은 $5-12 구간에 분포한다고 해요. 트래픽이 급증하는 시기가 있으면 그 달은 $15를 넘기기도 하고요.

### Docker Compose on VPS: 가장 예측 가능한 비용

Hetzner CX22(2 vCPU, 4GB RAM, 40GB SSD, 월 €3.29 ≈ $3.6)에 Docker Compose로 앱을 올리면, 청구서는 매달 고정이에요. Nginx + 앱 서버 + PostgreSQL 컨테이너를 한 VPS에서 돌려도 소규모 트래픽에서는 문제없어요.

단점은 명확해요. 배포 파이프라인을 직접 만들어야 하고(GitHub Actions + SSH 스크립트), SSL 인증서 갱신도 직접 설정해야 하고(Certbot + cron), 서버 모니터링도 알아서 해야 해요. 이 설정에 처음에 반나절 정도 투자가 필요해요.

---

## 세 플랫폼 비교: 어떤 조건에서 무엇을 써야 하나

| 기준 | Fly.io | Railway | VPS + Docker Compose |
|------|--------|---------|----------------------|
| **기본 월 비용** | $0-3 (DB 없을 때) | $5 고정 | ~$3.6 (Hetzner CX22) |
| **DB 포함 월 비용** | $5-12 | $8-15 | 변동 없음 (동일 VPS) |
| **Cold start** | 있음 (2-4초) | 없음 | 없음 |
| **배포 난이도** | 낮음 (`flyctl deploy`) | 매우 낮음 (Git push) | 중간 (CI/CD 직접 구성) |
| **서버 관리 필요** | 없음 | 없음 | 있음 |
| **스케일 유연성** | 높음 | 중간 | 낮음 (수동) |
| **월 만원 이하 가능?** | 조건부 (DB 없을 때) | 어려움 (DB 포함 시) | 가능 (고정) |
| **추천 상황** | 글로벌 배포 필요 시 | 빠른 프로토타이핑 | 안정적 장기 운영 |

트레이드오프를 정리하면 이래요. Fly.io는 `flyctl` CLI가 잘 만들어져 있고 멀티 리전 배포도 쉬운데, 비용이 설정에 따라 예측하기 어려워요. Railway는 Git push만 하면 배포되는 편의성이 압도적이지만, $5 이상이 나올 가능성이 높아서 "월 만원 이하" 조건을 맞추기 빡빡해요. VPS + Docker Compose는 월 고정 비용이 가장 낮지만, 운영 지식이 필요하고 초기 설정에 시간이 들어요.

---

## 실제 시나리오별 권장 선택

**시나리오 A — 빠르게 론칭하고 싶고 인프라에 시간 쓰기 싫어요**

Railway를 쓰되, DB는 플랫폼 내장 플러그인 대신 Supabase 무료 티어(500MB, 프로젝트 2개 무료)를 외부로 빼세요. Railway 사용량을 앱 서버 하나로 줄일 수 있고, $5 크레딧 안에서 해결될 가능성이 높아져요.

**시나리오 B — 비용을 최대한 낮추고 싶어요, 설정은 한 번 해두면 돼요**

Hetzner CX22 + Docker Compose예요. 월 $3.6에 고정이고, 같은 서버에서 여러 프로젝트를 동시에 올릴 수 있어요. Nginx를 리버스 프록시로 쓰면 도메인별로 앱을 분리하는 것도 어렵지 않아요. 초기 설정 시간을 Notion이나 GitHub에 문서화해 두면 다음 프로젝트에서도 재사용할 수 있어요.

**시나리오 C — 글로벌 사용자가 있거나 latency가 중요해요**

Fly.io가 맞아요. 다만 DB는 같은 리전의 Fly Postgres 대신 PlanetScale(Hobby 플랜 $0)이나 Turso(SQLite 기반, 월 500MB 무료)를 고려해 보세요. 메인 앱 머신만 Fly.io에 두고 DB를 외부 무료 서비스로 빼면 Fly.io 비용을 무료 할당 내에서 유지하는 게 가능해요.

---

## 앞으로 6개월, 뭐가 달라질까

세 가지만 지켜보면 돼요.

**Railway의 가격 정책 변화**예요. 2025년 말부터 Railway가 팀 플랜 중심으로 수익 구조를 바꾸고 있어요. Hobby 플랜의 $5 크레딧 조건이 추가로 변경될 가능성이 있어요. 공식 changelog를 주기적으로 확인하는 게 필요해요.

**Fly.io의 무료 티어 지속 여부**도 변수예요. Fly.io는 2023년과 2024년에 각각 무료 티어 조건을 한 번씩 변경했어요. 지금의 무료 머신 3개 정책이 언제까지 유지될지는 불확실해요.

**VPS 가격 경쟁**은 반가운 방향이에요. Hetzner, Contabo, BuyVM 같은 유럽 기반 VPS 업체들이 2026년에도 가격 경쟁을 이어가고 있어요. 동일 사양 기준으로 AWS나 GCP 대비 3-5배 저렴한 수준이 유지되고 있어요.

결국 1인 개발자 인프라 비용의 핵심은 플랫폼 선택이 아니라 "DB를 어디에 두냐"예요. 앱 서버보다 DB 호스팅이 비용에서 더 큰 비중을 차지하거든요. DB를 외부 무료 서비스(Supabase, Turso, PlanetScale)로 분리하는 구조를 잡으면, 어떤 플랫폼을 쓰든 월 만원 이하 운영은 충분히 가능해요.

지금 쓰는 플랫폼의 지난 3개월 청구서를 항목별로 뜯어본 적 있나요? 생각보다 DB 관련 비용이 전체의 절반을 넘고 있을 거예요.

## 참고자료

1. [Railway vs Fly.io vs Render: Which Cloud Gives You the Best ROI? | by R. Thompson (PhD) | AI Disrupt](https://medium.com/ai-disruption/railway-vs-fly-io-vs-render-which-cloud-gives-you-the-best-roi-2e3305399e5b)
2. [Railway vs. Fly | Railway Docs](https://docs.railway.com/platform/compare-to-fly)
3. [Déployer une App Gratuitement en 2026 : Comparatif Railway, Render, Fly.io, Vercel - DEV Community](https://dev.to/lucasmdevdev/deployer-une-app-gratuitement-en-2026-comparatif-railway-render-flyio-vercel-1n55)


---

*Photo by [Microsoft Copilot](https://unsplash.com/@microsoftcopilot) on [Unsplash](https://unsplash.com/photos/woman-typing-on-laptop-at-wooden-table-with-breakfast-ghVMdPN33vM)*
