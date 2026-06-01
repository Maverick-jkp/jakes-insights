---
title: "1인 개발자 월 10달러 이하 인프라: Fly.io, Railway, Docker Compose 실제 청구서 비교"
date: 2026-05-08T20:27:56+0900
draft: false
author: "Jake Park"
categories: ["ai"]
tags: ["subtopic-ai", "\uac1c\ubc1c\uc790", "10\ub2ec\ub7ec", "\uc778\ud504\ub77c", "Node.js"]
description: "1인 개발자 월 10달러 예산으로 Fly.io($5–8), Railway($5 고정 크레딧), Docker Compose VPS 실제 청구서를 비교했습니다. 광고 문구 아닌 데이터로 가장 저렴한 선택을 찾아보세요."
image: "/images/20260508-1인-개발자-월-10달러-이하-인프라-flyio-doc.webp"
technologies: ["Node.js", "Docker", "PostgreSQL", "Redis"]
faq:
  - question: "1인 개발자 월 10달러 이하로 앱 운영 가능한 인프라 뭐가 있나요"
    answer: "2025년 기준 1인 개발자 월 10달러 이하 인프라로는 Fly.io, Railway, VPS+Docker Compose 세 가지가 현실적인 선택지예요. Fly.io는 앱+DB 기준 월 $4–8, Railway Starter는 $5 고정 크레딧, Hetzner VPS+Docker Compose는 월 $3.5 고정으로 모두 10달러 이하가 가능하지만, DB 추가나 트래픽 증가 시 Railway와 Fly.io는 $15–25까지 올라갈 수 있어요."
  - question: "Fly.io vs Railway 실제 청구서 비교 2025"
    answer: "1인 개발자 월 10달러 이하 인프라를 Fly.io, Docker Compose, Railway 실제 청구서로 비교하면, Fly.io는 shared-cpu-1x VM 기준 최소 $1.94에서 시작해 앱+DB 조합 시 월 $4–8 수준이에요. Railway는 Starter Plan $5 고정 크레딧을 제공하지만 PostgreSQL을 Railway 내부에서 함께 운영하면 월 $10–15를 초과하는 사례가 빈번해, 외부 무료 DB 서비스와 조합하는 것이 $5 이내 유지의 핵심이에요."
  - question: "Railway PostgreSQL 같이 쓰면 비용 얼마나 나와요"
    answer: "Railway에서 앱과 PostgreSQL을 함께 운영하면 DB가 상시 실행되어 RAM 사용량이 높아지기 때문에 $5 Starter 크레딧을 빠르게 초과하고 월 $10–15 이상 청구되는 경우가 많아요. 비용을 $5 이내로 유지하려면 Railway 앱 + Neon 무료 티어나 PlanetScale 무료 티어 같은 외부 DB를 조합하는 방식이 효과적이에요."
  - question: "VPS Docker Compose 1인 개발자 직접 운영 장단점"
    answer: "Hetzner CX11 기준 월 $3.5 고정 비용으로 앱, Nginx, PostgreSQL, Redis를 모두 올려도 추가 과금이 없어, 앱이 여러 개로 늘어도 비용이 일정하게 유지되는 것이 가장 큰 장점이에요. 단, SSL 설정·Nginx 리버스 프록시·DB 백업 자동화를 직접 구성해야 하는 초기 세팅 부담이 있고, Kamal 같은 도구를 써도 처음 환경 구성에 반나절 이상 소요될 수 있어요."
  - question: "2025년 소규모 사이드 프로젝트 서버 비용 가장 저렴하게 유지하는 방법"
    answer: "1인 개발자 월 10달러 이하 인프라 기준으로, 단기적으로 비용 예측이 쉬운 선택은 Railway Starter($5 고정)이지만 장기 운영 시 총비용 면에서는 VPS+Docker Compose 조합이 가장 유리해요. 플랫폼 정책 변경 위험도 없고 앱 수가 늘어도 비용이 고정되기 때문에, 초기 세팅 공수를 감수할 수 있다면 Hetzner 같은 저가 VPS에 Docker Compose를 올리는 방식이 장기적으로 가장 경제적이에요."
---

월 10달러. 커피 두 잔 값이에요.

그 돈으로 앱 하나를 진짜 운영할 수 있을까요? 2026년엔 가능해요. Fly.io, Railway, VPS 위에 Docker Compose까지 선택지가 생겼거든요. 근데 "더 싸다"는 광고 문구 말고, 실제 청구서가 어떻게 나오는지가 문제죠. 세 가지 옵션의 비용 구조를 데이터 기반으로 뜯어볼게요.

> **핵심 요약**
> - Fly.io는 무료 티어 종료(2024년 중반) 이후 최소 월 $1.94 수준의 소형 shared CPU VM을 제공하며, 트래픽이 적은 1인 프로젝트 기준 월 $5–8 범위가 현실적이에요.
> - Railway는 2026년 기준 Starter Plan $5/월 고정 크레딧 + 사용량 초과 시 과금 구조로, 소규모 앱은 $5 이내 유지가 되지만 PostgreSQL 연결이 추가되면 빠르게 초과해요.
> - VPS(Hetzner CX11 등) + Docker Compose 조합은 월 $3.5–6 수준의 고정 비용으로, 설정 공수를 감수하면 가장 예측 가능한 청구서를 만들어요.
> - 세 옵션 모두 "월 10달러 이하"는 가능하지만, 트래픽 증가·DB 추가·에러 로그 조회 같은 부가 기능이 붙으면 Fly.io와 Railway는 $15–25로 올라갈 수 있어요.
> - 2026년 기준 1인 개발자에게 가장 비용 예측이 쉬운 선택지는 Railway Starter이지만, 장기 운영은 VPS + Docker Compose가 총비용에서 유리해요.

---

## 이 비교가 지금 필요한 이유

2023년까지만 해도 Heroku 무료 티어가 1인 개발자의 기본값이었어요. 그게 사라지면서 시장이 빠르게 재편됐죠. Fly.io는 "Heroku 대안"을 전면에 내세웠고, Railway는 심플한 UX로 빠르게 점유율을 가져갔어요. VPS 위에 Docker Compose를 직접 올리는 방식은 예전부터 있었지만, Kamal(37signals의 배포 도구)이 2024년 주목받으면서 다시 관심을 끌기 시작했어요.

결정적인 변화는 Fly.io가 2024년 6월 무료 VM을 사실상 축소하면서 생겼어요. Railway도 2024년 초 Hobby Plan 가격을 $5/월로 올렸고요. 두 플랫폼 모두 "공짜는 없다"는 방향으로 정리됐어요.

getdeploying.com의 플랫폼 비교 데이터에 따르면, 2026년 기준 Fly.io의 `shared-cpu-1x` + 256MB RAM VM은 월 약 $1.94이고, 여기에 1GB 스토리지와 아웃바운드 트래픽 3GB가 추가되면 총 $5–7 수준이에요. Railway Docs 기준, Starter Plan은 월 $5 크레딧이 기본으로 제공되고 초과분은 CPU·RAM·네트워크 사용량에 따라 과금돼요.

반면 Hetzner의 CX11 VPS는 1vCPU, 2GB RAM, 20GB SSD 기준 월 €3.29(약 $3.5) 고정이에요. Docker Compose로 앱 여러 개를 올려도 비용은 그대로고요. 이게 VPS 방식의 핵심 매력이에요.

---

## 실제 청구서 분석: 세 옵션의 비용 구조

### Fly.io: 예측 가능하지만 변수가 있어요

Fly.io는 컨테이너를 **Machine** 단위로 실행해요. 가장 작은 `shared-cpu-1x, 256MB` Machine은 시간당 약 $0.0001이에요. 한 달(720시간) 기준 $0.07 수준이지만, 최소 사용량(minimum billing)이 있어서 실제로 월 $1.94부터 시작해요.

여기에 Postgres DB를 붙이면 달라져요. Fly.io의 Postgres는 별도 Machine으로 돌아가고, 동일 스펙 기준 추가 $1.94. 합산하면 앱 + DB만으로 월 $4 근처예요.

아웃바운드 트래픽은 월 160GB까지 무료(North America·Europe 기준)예요. 1인 프로젝트라면 거의 걸릴 일 없어요. 결국 앱 하나 + DB 하나 운영 기준 **월 $4–8** 범위가 현실적이에요.

단점은 sleep 모드가 없다는 점이에요. Railway는 트래픽 없으면 앱을 내리는데, Fly.io는 계속 돌아가요. 이게 비용이기도 하고, 응답 속도 면에서 장점이기도 해요.

### Railway: 가장 쉽지만 DB가 변수예요

Railway의 Starter Plan은 월 $5 고정 크레딧을 줘요. 공식 문서(Railway Docs) 기준으로 이 크레딧 안에서 RAM, CPU, 네트워크를 쓰는 구조예요.

소형 Node.js 앱 하나만 올리면 $5 크레딧으로 충분해요. 그런데 PostgreSQL 서비스를 Railway 안에서 돌리면 얘기가 달라져요. DB는 상시 실행이라 RAM 사용량이 꽤 나오거든요. R. Thompson의 Medium 분석 기사에 따르면, Railway에서 앱 + DB 조합을 운영할 경우 월 $10–15를 초과하는 사례가 빈번하다고 해요.

해결책은 Railway 앱 + 외부 DB(PlanetScale 무료 티어, Neon 무료 티어 등) 조합이에요. 이렇게 하면 $5 크레딧 안에서 유지가 돼요.

### VPS + Docker Compose: 예측 가능한 청구서

Hetzner CX11 기준 월 €3.29. 여기에 Docker Compose로 앱, Nginx, PostgreSQL, Redis 전부 올려도 비용은 변하지 않아요. 이게 핵심이에요.

단, 진입 비용이 있어요. SSL 설정, Nginx reverse proxy 구성, DB 백업 자동화까지 직접 해야 해요. Kamal을 쓰면 배포 자동화는 어느 정도 해결되지만, 처음 세팅에 반나절 이상은 잡아야 해요.

장점은 명확해요. 앱이 두 개, 세 개로 늘어도 비용이 같아요. 그리고 Fly.io나 Railway처럼 플랫폼 정책이 바뀌어서 갑자기 가격이 올라갈 위험도 없어요.

### 비용 비교표

| 항목 | Fly.io | Railway | VPS + Docker Compose |
|------|--------|---------|---------------------|
| 최소 월 비용 | $1.94 (VM만) | $5 (Starter Plan) | $3.5 (Hetzner CX11) |
| 앱 1개 + DB | $4–8 | $10–15 | $3.5 (고정) |
| 앱 3개 + DB | $10–18 | $20–30 | $3.5–7 (VPS 업그레이드) |
| 트래픽 과금 | 160GB 무료 | 크레딧 내 포함 | 서버 업체 정책 따라 |
| Sleep 모드 | 없음 | 있음 (비활성 시) | 없음 |
| 설정 난이도 | 낮음 | 매우 낮음 | 높음 |
| 비용 예측성 | 보통 | 낮음 (초과 과금) | 높음 |
| 추천 상황 | 빠른 배포, 단일 앱 | MVP 프로토타이핑 | 앱 여러 개, 장기 운영 |

---

## 실전 시나리오별 선택 가이드

**시나리오 A: 사이드 프로젝트 초기 단계**

아직 유저가 없고, DB는 필요하지만 트래픽은 거의 없어요. 이 경우 Railway Starter + Neon 무료 DB 조합이 가장 빠르고 저렴해요. 월 $5 안에 해결 가능하고, GitHub 연동 배포도 2분이면 설정 끝이에요.

**시나리오 B: MAU 500명 이상, 안정적인 운영 필요**

트래픽이 어느 정도 있고 DB가 상시 필요하면 Fly.io가 현실적이에요. 앱 응답 속도도 안정적이고, $5–8 범위에서 운영 가능해요. Railway의 Sleep 모드는 응답 지연을 만들 수 있어서 이 단계에선 불리해요.

**시나리오 C: 앱 2개 이상, 6개월 이상 장기 운영**

VPS + Docker Compose로 넘어가야 할 시점이에요. Hetzner CX21(2vCPU, 4GB RAM, $6.5/월)이면 앱 서너 개도 충분히 올릴 수 있어요. 초기 설정 시간을 투자하면 총비용 면에서 Fly.io 대비 연간 $60–120 아낄 수 있어요.

**주시해야 할 신호들:**
- Railway가 Starter Plan 크레딧을 줄이거나 과금 정책을 바꾸면 VPS 전환 타이밍이에요
- Fly.io의 소형 Machine 가격이 올라가는지 확인하세요 (2025년에 한 차례 조정 있었어요)
- Kamal 2.x 업데이트가 Docker Compose 배포를 얼마나 쉽게 만드느냐가 VPS 진입 장벽을 결정할 거예요

---

## 결론: 월 10달러 이하, 조건이 있어요

세 줄로 정리하면 이래요.

- **MVP/초기**: Railway Starter + 외부 무료 DB → 월 $5
- **안정적 단일 앱**: Fly.io `shared-cpu-1x` + Fly Postgres → 월 $5–8
- **다중 앱/장기**: Hetzner VPS + Docker Compose → 월 $3.5–7 고정

월 10달러 이하 인프라는 2026년에도 충분히 현실이에요. 단, "DB를 어디에 붙이느냐"가 가장 큰 비용 변수예요. Railway는 내부 DB 쓰는 순간 $10을 넘기 쉽고, Fly.io는 Machine 수가 늘면 금방 올라가요. VPS는 설정 공수를 내면 가장 예측 가능한 청구서를 줘요.

지금 프로젝트가 어느 단계인지 먼저 확인하세요. 그리고 6개월 뒤 비용을 역산해보면, 어떤 선택이 맞는지 보일 거예요.

---

*참고 자료: Railway Docs "Compare to Fly.io" (2026), getdeploying.com "Fly.io vs Railway" 비교 데이터, R. Thompson "Railway vs Fly.io vs Render" (Medium/AI Disrupt)*

## 참고자료

1. [Railway vs. Fly | Railway Docs](https://docs.railway.com/platform/compare-to-fly)
2. [Railway vs Fly.io vs Render: Which Cloud Gives You the Best ROI? | by R. Thompson (PhD) | AI Disrupt](https://medium.com/ai-disruption/railway-vs-fly-io-vs-render-which-cloud-gives-you-the-best-roi-2e3305399e5b)
3. [Fly.io vs Railway](https://getdeploying.com/flyio-vs-railway)


---

*Photo by [NASA](https://unsplash.com/@nasa) on [Unsplash](https://unsplash.com/photos/photo-of-outer-space-Q1p7bh3SHj8)*
