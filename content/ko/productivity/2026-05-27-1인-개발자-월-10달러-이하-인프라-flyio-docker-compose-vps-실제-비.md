---
title: "1인 개발자 월 10달러 이하 인프라: Fly.io vs Docker Compose + VPS 실제 비용 비교"
date: 2026-05-27T22:06:10+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "/uac1c/ubc1c/uc790", "10/ub2ec/ub7ec", "/uc778/ud504/ub77c", "Docker"]
description: "1인 개발자 월 10달러 이하 인프라 실전 비교. Fly.io 무료~$5.70 vs Hetzner VPS $4~$6, Docker Compose 조합까지 2025년 실제 비용과 관리 부담을 숫자로 뜯어봤습니다."
image: "/images/20260527-1인-개발자-월-10달러-이하-인프라-flyio-doc.webp"
technologies: ["Docker", "AWS", "PostgreSQL", "Redis", "Linux"]
faq:
  - question: "1인 개발자 월 10달러 이하로 서비스 운영 가능한가요"
    answer: "1인 개발자 월 10달러 이하 인프라는 Fly.io와 Docker Compose + VPS 조합으로 충분히 가능합니다. Fly.io는 DB를 Supabase 같은 외부 서비스로 분리하면 월 $0~$5.70 수준이고, Hetzner VPS + Docker Compose 조합은 월 $5.35~$6.50 정도면 운영할 수 있어요. 단, 국내 클라우드(NHN, Naver Cloud)는 구조적으로 월 10달러 이하를 맞추기 어렵습니다."
  - question: "Fly.io vs VPS Docker Compose 어떤 게 더 저렴해요 2025"
    answer: "2025년 기준 Fly.io Docker Compose VPS 실제 비용을 비교하면 순수 금액은 비슷하지만 상황에 따라 다릅니다. 트래픽이 불규칙한 초기 단계에서는 Fly.io가 유리하고, 트래픽이 안정된 이후에는 Hetzner 같은 VPS가 동일 스펙 대비 비용 효율이 높아요. 핵심 차이는 Fly.io는 운영 시간이 적게 들고, VPS는 직접 관리 부담이 크다는 점입니다."
  - question: "Fly.io 무료 티어 실제로 얼마나 쓸 수 있나요"
    answer: "Fly.io 무료 티어는 shared-cpu-1x 256MB RAM VM 3개, 월 160GB 아웃바운드 트래픽, 3GB 영구 스토리지를 제공해 토이 프로젝트는 진짜 월 $0이 가능합니다. 단, RAM을 512MB로 올리거나 PostgreSQL DB를 Fly.io 내부에서 함께 돌리면 바로 $7~$15 이상으로 올라가요. DB는 반드시 Supabase나 Turso 같은 외부 서비스로 분리해야 무료 티어를 제대로 활용할 수 있습니다."
  - question: "Hetzner VPS Docker Compose로 사이드 프로젝트 배포하는 법"
    answer: "Hetzner CX21(월 $4.15, 2vCPU 4GB RAM)에 Docker Compose를 올리고 Let's Encrypt로 SSL을 무료 처리하면 도메인 포함 월 $6.50 수준으로 운영할 수 있습니다. 4GB RAM이면 컨테이너 두세 개를 올려도 여유가 있어 소형 사이드 프로젝트에 충분한 스펙입니다. 다만 서버 설정, 장애 대응, 보안 패치를 직접 해야 하므로 Fly.io 대비 운영 시간 비용이 높다는 점을 감안해야 해요."
  - question: "국내 클라우드 NHN Naver Cloud 1인 개발자 사이드 프로젝트에 비싼가요"
    answer: "1인 개발자 월 10달러 이하 인프라를 목표로 한다면 국내 클라우드는 거의 불가능한 선택입니다. NHN Cloud나 Naver Cloud의 가장 저렴한 플랜도 월 10,000~15,000원 수준이고 트래픽 과금이 별도로 붙어요. 동일 스펙 기준으로 Hetzner 같은 유럽 VPS 대비 두 배에서 네 배 비싸기 때문에 글로벌 서비스를 목표로 한다면 해외 옵션이 훨씬 합리적입니다."
---

사이드 프로젝트 하나 올리려고 AWS 콘솔 열었다가 월말 청구서에 뒤통수 맞은 적 있죠? 1인 개발자 커뮤니티에서 2026년에 가장 많이 나오는 질문이 바로 이거예요. "어떻게 하면 월 10달러 이하로 서비스를 굴릴 수 있냐." 실제로 가능한 얘기예요.

Fly.io, Docker Compose + VPS, 그리고 국내외 각종 클라우드 옵션까지. 어떤 조합이 실제로 더 저렴하고 실용적인지 뜯어봤어요.

> **핵심 요약**
> - Fly.io 무료 티어는 월 $0, 트래픽 증가 시 소형 VM 기준 월 $1.94~$5.70 수준이에요.
> - Docker Compose + VPS(Hetzner CX21 기준) 조합은 월 $4~$6 수준으로 Fly.io와 비슷하지만, 관리 부담이 훨씬 크죠.
> - 트래픽이 예측 불가능한 초기 단계라면 Fly.io가 유리하고, 트래픽이 안정된 뒤엔 VPS가 비용 면에서 앞서요.
> - 국내 클라우드(NHN Cloud, Naver Cloud)는 월 10달러 이하로 운영하기 어렵고, 글로벌 옵션과 가격 차이가 두 배에서 네 배 수준이에요.

---

## 왜 지금 이 비교가 의미 있을까요?

2023~2024년 사이 Heroku 무료 티어 폐지, Railway 가격 인상, Render 무료 플랜 제한 강화 등 1인 개발자가 공짜로 쓰던 플랫폼들이 줄줄이 유료화됐어요. 대안을 찾던 개발자들이 몰린 곳이 Fly.io와 저가 VPS 시장이었죠.

2025년 기준 Hetzner, Contabo, Vultr 같은 유럽·미국 VPS 업체들의 가장 저렴한 플랜은 월 $3~$6 선이에요. 동시에 Fly.io는 2023년 무료 티어를 개편하면서 소형 워크로드는 여전히 거의 무료 수준으로 유지하고 있어요. 경쟁이 치열해지면서 1인 개발자 입장에서는 오히려 선택지가 많아진 셈이에요.

그런데 문제가 있어요. 단순히 월정액만 보면 안 된다는 거예요. 운영 시간, 장애 대응, 스케일링 비용까지 포함한 **총 비용(TCO, Total Cost of Ownership)**으로 봐야 진짜 비교가 돼요. 특히 1인 개발자는 시간 자체가 돈이니까요.

국내 개발자들 사이에서 AI 사이드 프로젝트 출시가 급격히 늘어난 것도 이유예요. Kochim Blog 분석처럼 AI 도구 비용을 조정해 월 $100에서 $58.90으로 줄인 사례가 나올 만큼, 인프라 비용 최소화는 이제 선택이 아닌 생존 조건에 가까워요.

---

## 각 옵션, 실제로 얼마나 드는지 뜯어봤어요

### Fly.io: 무료처럼 보이지만 함정이 있어요

Fly.io 공식 무료 범위예요:

- shared-cpu-1x, 256MB RAM VM 3개까지 무료
- 월 160GB 아웃바운드 트래픽 무료
- 3GB 영구 스토리지(Volumes) 무료

트래픽이 거의 없는 토이 프로젝트라면 월 $0이 가능해요. 맞아요, 진짜 $0.

그런데 RAM을 512MB로 올리거나 persistent volume을 늘리면 바로 과금이 시작돼요. `shared-cpu-1x` + 512MB RAM 단일 앱을 24시간 돌리면 공식 가격 기준 월 약 $1.94예요. 여기에 PostgreSQL managed DB까지 붙이면 최소 $7~$10 추가. 순식간에 월 10달러를 넘겨요.

핵심은 이거예요. DB를 Fly.io 안에서 같이 돌리면 비용이 폭발하는 구조예요. DB는 Supabase 무료 티어나 Turso 같은 외부 서비스로 분리하면 월 10달러 이하를 유지할 수 있어요.

### Docker Compose + VPS: 저렴하지만 내가 직접 해야 해요

VPS + Docker Compose 조합의 실제 비용이에요:

| 항목 | 구체적 옵션 | 월 비용 |
|------|------------|---------|
| VPS (Hetzner CX21) | 2 vCPU, 4GB RAM, 40GB SSD | $4.15 |
| VPS (Vultr Regular) | 1 vCPU, 1GB RAM | $6.00 |
| VPS (Contabo VPS S) | 4 vCPU, 8GB RAM | $5.50 |
| 도메인(Namecheap 기준) | .com 1년 | 월 환산 $1.20 |
| SSL | Let's Encrypt | $0 |

Hetzner CX21 + Docker Compose + Let's Encrypt 조합이면 월 $5.35 정도예요. 도메인 포함해도 $6.5 수준이죠. 스펙 대비 가성비는 압도적이에요. 4GB RAM에 두세 개 컨테이너를 올려도 여유가 있어요.

CoderJson의 클라우드 비용 비교 분석에서도 국내 클라우드 대비 Hetzner 같은 유럽 VPS가 동일 스펙 기준 약 두 배에서 네 배 저렴하다는 걸 확인할 수 있어요. 국내 NHN Cloud나 Naver Cloud는 가장 저렴한 플랜도 월 10,000~15,000원 수준이고, 트래픽 과금이 따로 붙는 구조예요. 월 10달러 이하로 맞추기 어렵죠.

---

## 핵심 비교: 진짜 총비용으로 따져봤어요

### 세 가지 옵션을 나란히 놓으면

| 비교 항목 | Fly.io (소형 앱) | Docker Compose + Hetzner VPS | 국내 VPS (NHN 기준) |
|---------|----------------|----------------------------|--------------------|
| 기본 월 비용 | $0~$5.70 | $4.15~$6.50 | $9~$15 |
| DB 포함 시 | $7~$15 | $4.15 (자체 구축) | $12~$20 |
| 배포 난이도 | 낮음 (`fly deploy`) | 중간 (Docker 지식 필요) | 낮음~중간 |
| 스케일링 | 자동 | 수동 | 반자동 |
| 운영 시간 비용 | 낮음 | 높음 | 중간 |
| 글로벌 레이턴시 | 낮음 (다리전 분산) | 단일 리전 | 국내 최적 |
| 월 10달러 이하 가능? | ✅ (DB 외부화 시) | ✅ (단독 운영 시) | ❌ (거의 불가) |

### 그래서 뭘 선택해야 하나요?

두 옵션의 트레이드오프를 정리하면 이래요.

**Fly.io:**
- **유리한 점**: 배포가 빠르고 간단해요. CLI 하나로 거의 모든 게 해결되죠. 트래픽 급증 시 자동 스케일링도 돼요.
- **불리한 점**: DB를 같이 쓰면 비용이 금방 $10를 넘어요. 무료 티어 VM은 cold start 이슈가 있어요(비활성화 후 첫 요청 느림).
- **적합한 경우**: 배포 자동화, CI/CD 연동, 지역 분산이 필요한 초기 단계

**Docker Compose + VPS:**
- **유리한 점**: 스펙 대비 비용이 압도적이에요. DB, 캐시, 앱 서버를 한 서버에 다 올릴 수 있어요.
- **불리한 점**: 서버 장애, 보안 패치, SSL 갱신을 직접 챙겨야 해요. 시간 비용이 월 몇 시간은 나와요.
- **적합한 경우**: Docker에 익숙하고 운영 안정성보다 비용이 우선인 경우

2026년 현재 커뮤니티에서 많이 쓰는 패턴은 이거예요. 초기엔 Fly.io로 빠르게 런칭하고, MAU 500~1,000명을 넘기면 Hetzner VPS로 이전하는 방식. 이렇게 하면 전체 운영 비용을 월 $5~$8 수준으로 유지할 수 있어요.

---

## 월 10달러 이하로 실제 굴리는 스택 예시

이론 말고 실제로 쓸 수 있는 조합이에요.

**조합 A (Fly.io 중심):**
- 앱 서버: Fly.io `shared-cpu-1x` + 256MB → $0
- DB: Supabase 무료 티어(500MB, 50,000 rows) → $0
- 도메인: Porkbun .io 도메인 → 월 $1.5
- **총합: 월 $1.5**. 단, 트래픽이 거의 없을 때 얘기예요.

**조합 B (VPS 중심, 안정적):**
- VPS: Hetzner CX21 → $4.15
- Docker Compose (앱 + PostgreSQL + Nginx)
- SSL: Let's Encrypt (Certbot) → $0
- 도메인: Namecheap → $1.2
- **총합: 월 $5.35**. MAU 수천 명까지 버텨요.

**조합 C (하이브리드):**
- VPS: Hetzner CX11(1 vCPU, 2GB RAM) → $2.96
- DB: Turso (SQLite Edge, 무료 티어) → $0
- 캐시: Upstash Redis 무료 → $0
- **총합: 월 $2.96 + 도메인**. 읽기 중심 서비스에 최적이에요.

세 조합 모두 월 10달러를 넘지 않아요. 허황된 얘기가 아닌 거죠.

---

## 앞으로 6개월, 이 시장은 어떻게 바뀔까요?

몇 가지 방향을 짚을 수 있어요.

- **Fly.io 가격 정책 변화 주시**: 2025년 초 Fly.io가 무료 티어 범위를 조정했어요. 추가 개편 가능성이 있으니 공식 블로그를 모니터링하는 게 좋아요.
- **Hetzner ARM 서버 확대**: 2025년 Hetzner가 Ampere ARM 기반 CAX 시리즈를 출시하면서 가성비가 더 올라갔어요. CAX11 기준 월 $3.79에 2 vCPU + 4GB RAM이에요.
- **국내 클라우드 대응 여부**: NHN, Naver Cloud 모두 글로벌 저가 VPS 대비 경쟁력이 낮아요. 국내 서비스라도 레이턴시가 크리티컬하지 않다면 유럽 VPS가 현실적이에요.

결국 질문은 하나예요. 내 시간이 더 비쌀까, 서버 비용이 더 비쌀까? Docker와 Linux에 자신 있다면 VPS가 정답이에요. 빠른 배포와 운영 편의를 원한다면 Fly.io에서 시작하세요.

지금 당장 해볼 수 있는 첫 단계는 간단해요. Fly.io 무료 티어로 앱을 올리고, Supabase 무료 DB를 연결해보세요. 그게 월 $0짜리 프로덕션의 출발점이에요.

---

*참고: Fly.io 가격은 2026년 5월 공식 홈페이지 기준, Hetzner 가격은 동월 Cloud 콘솔 기준, 국내 클라우드 비교는 CoderJson 클라우드 비용 비교 리포트를 참조했어요.*

## 참고자료

1. [2025 클라우드 비용 비교: 국내 vs 글로벌 :: CoderJson 개발참고서](https://class1119.tistory.com/6)
2. [1인 개발자를 위한 AI 도구 최적화 전략: 월 $100에서 $58.90으로, 성능은 2배로 - Kochim Blog](https://kochim.com/boards/posts/using-glm-20251206/)
3. [전용 서버 vs VPS: 어떤 호스팅이 더 나을까요?](https://www.youstable.com/ko/blog/dedicated-server-vs-vps/)


---

*Photo by [Surface](https://unsplash.com/@surface) on [Unsplash](https://unsplash.com/photos/a-laptop-computer-sitting-on-top-of-a-white-table-F4ottWBnCpM)*
