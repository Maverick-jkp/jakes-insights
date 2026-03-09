---
title: "1인 개발자, AWS 대신 Fly.io·Hetzner 조합으로 월 15달러 이하 풀스택 인프라 구성하기"
date: 2026-03-09T19:54:07+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-cloud", "\uac1c\ubc1c\uc790", "aws", "fly.io", "Node.js"]
description: "Fly.io 무료 VM 3개와 Hetzner CX22 월 4.3유로로 AWS 대비 80% 절감하는 1인 개발자 풀스택 인프라 실제 구성법. 월 15달러 이하로 프로덕션 수준 운영한 설정을 공개합니다"
image: "/images/20260309-1인-개발자-aws-대신-flyio-hetzner-조합.webp"
technologies: ["Node.js", "AWS", "PostgreSQL", "Go", "Cloudflare"]
faq:
  - question: "1인 개발자 AWS 대신 Fly.io Hetzner 조합으로 월 15달러 이하 인프라 구성 가능한가요"
    answer: "네, 1인 개발자 AWS 대신 Fly.io Hetzner 조합으로 월 15달러 이하 풀스택 인프라 실제 구성이 가능해요. Fly.io 무료 티어(공유 VM 3개 + 3GB 볼륨)와 Hetzner CX22 서버(월 약 6달러)를 합치면 도메인 비용 포함해도 월 12~13달러 수준이에요. 동일 스펙 AWS 구성 대비 최대 80~85% 저렴하게 프로덕션 수준의 환경을 운영할 수 있어요."
  - question: "Hetzner CX22 PostgreSQL 보안 설정 방법"
    answer: "Hetzner CX22에 PostgreSQL을 설치하면 기본적으로 5432 포트가 공개 인터넷에 열려 있어 반드시 방화벽 설정이 필요해요. Fly.io 아웃바운드 IP만 허용하거나, Fly.io가 기본 제공하는 WireGuard 기반 프라이빗 네트워크(flycast)로 연결하는 방법이 권장돼요. WireGuard 구성을 사용하면 별도의 복잡한 설정 없이 두 서비스 간 보안 통신을 구현할 수 있어요."
  - question: "Fly.io 무료 티어 한계 Node.js API 서버 운영 가능한가"
    answer: "Fly.io 무료 티어는 shared-cpu-1x VM 3개와 VM당 256MB RAM을 제공하는데, Node.js나 Go로 작성된 경량 API 서버라면 충분히 운영 가능해요. 단, 월 아웃바운드 트래픽이 160GB를 초과하거나 메모리 사용량이 많은 애플리케이션은 유료 플랜으로 전환이 필요해요. MAU 10만 이하의 사이드 프로젝트나 초기 스타트업 수준에서는 무료 티어만으로 충분한 경우가 많아요."
  - question: "한국 사용자 대상 서비스인데 Hetzner 레이턴시 문제 어떻게 해결하나"
    answer: "Hetzner 데이터센터는 유럽(독일, 핀란드)과 미국(버지니아, 오리건)에만 있어 한국 사용자 기준으로 레이턴시가 AWS 서울 리전 대비 높을 수 있어요. 현실적인 대안은 Cloudflare 무료 CDN을 앞단에 붙여 정적 리소스와 캐시 가능한 응답의 레이턴시를 커버하는 방식이에요. API 응답 속도가 핵심인 서비스라면 이 조합보다 AWS 서울 리전을 고려하는 것이 나을 수 있어요."
  - question: "Fly.io Hetzner 조합이 Railway Render보다 나은 이유"
    answer: "1인 개발자 AWS 대신 Fly.io Hetzner 조합 월 15달러 이하 풀스택 인프라 실제 구성의 가장 큰 장점은 슬립 모드가 없고 비용 예측이 가능하다는 점이에요. Render는 비활성 시 서버가 중지되는 슬립 모드 문제가 있고, Railway는 사용량 한도 초과 시 예상치 못한 과금이 발생한다는 사례가 커뮤니티에서 꾸준히 보고돼요. Fly.io + Hetzner는 설정 복잡도가 다소 높지만 안정적인 운영과 비용 통제 면에서 두 서비스보다 우위에 있어요."
---

AWS 청구서를 처음 받아보고 멈칫한 적 있으세요? 작은 사이드 프로젝트 하나 돌렸을 뿐인데 월말에 80~120달러가 빠져나가는 경험은 1인 개발자라면 누구나 한 번쯤 겪는 통과의례예요. 그런데 지금, 같은 기능을 월 15달러 이하로 구성하는 방법이 꽤 널리 쓰이고 있어요. Fly.io와 Hetzner를 합친 구성이 바로 그 답이에요.

이게 단순한 절약 팁이 아니에요. 클라우드 시장 구조 자체가 바뀌고 있다는 신호거든요.

> **핵심 요약**
> - Fly.io의 무료 티어(3개 공유 VM + 3GB 볼륨)와 Hetzner CX22 서버(월 약 4.3유로)를 합치면 월 15달러 이하로 프로덕션 수준의 풀스택 인프라를 구성할 수 있어요.
> - r/webdev 커뮤니티에서 공개된 클라우드 가격 비교 계산기에 따르면, 동일 스펙 기준 AWS 대비 Fly.io는 약 70~80% 저렴하고, Hetzner는 최대 85% 저렴해요.
> - 1인 개발자 창업에서 인프라 비용이 초기 6개월 생존율에 직접 영향을 미친다는 게 개발자 커뮤니티의 공통된 경험이에요.
> - Hetzner는 데이터센터가 유럽(독일, 핀란드)과 미국(버지니아, 오리건)에 있어, 한국 타깃 서비스라면 레이턴시 고려가 필요해요.

---

## 지금 이 조합이 주목받는 이유

2024년 말부터 1인 개발자 커뮤니티에서 "탈 AWS" 움직임이 두드러지기 시작했어요. 배경은 단순해요. AWS는 여전히 강력하지만, 소규모 프로젝트에 맞게 설계된 서비스가 아니에요.

EC2 t3.micro 하나, RDS db.t3.micro 하나, 기본 S3 버킷과 CloudFront를 붙이면 트래픽이 거의 없어도 월 50~80달러는 기본이에요. 여기에 데이터 전송 비용, NAT 게이트웨이 비용이 붙으면 100달러를 넘는 건 시간문제예요.

반면 Heroku는 2022년 무료 플랜을 폐지했고, Render는 슬립 모드(비활성 시 서버 중지) 문제가 계속 지적돼요. Railway는 합리적이지만 월 사용량 한도 초과 시 갑작스러운 과금이 Reddit r/webdev에서 꾸준히 보고되고 있어요.

이 틈새를 파고든 게 Fly.io + Hetzner 조합이에요. Fly.io가 컨테이너 기반 애플리케이션 레이어를, Hetzner가 데이터베이스와 스토리지를 맡는 식으로 역할이 명확히 분리돼요.

---

## 실제 구성: 월 15달러 이하 아키텍처 해부

### 레이어 1: Fly.io로 앱 서버 구성

Fly.io 무료 티어는 `shared-cpu-1x` VM 3개, 3GB 볼륨, 160GB 아웃바운드 트래픽/월을 제공해요. VM당 RAM이 256MB라 작아 보이지만, Node.js나 Go로 짠 API 서버라면 충분해요.

무료 티어 기준:
- `shared-cpu-1x` VM × 3개
- 3GB 볼륨 스토리지
- 160GB 아웃바운드 트래픽/월
- PostgreSQL 소형 인스턴스 1개 (256MB)

PostgreSQL을 Fly.io에 올리면 무료지만, 스토리지가 커지거나 백업이 중요해지면 Hetzner로 분리하는 게 나아요.

### 레이어 2: Hetzner로 데이터베이스 서버 구성

Hetzner CX22는 월 약 4.3유로(약 6달러)예요. 스펙은 2 vCPU, 4GB RAM, 40GB SSD로, AWS t3.small(월 약 15달러)보다 훨씬 저렴하면서 스펙은 오히려 높아요. 여기에 PostgreSQL을 직접 올리고, `pg_dump` 스크립트로 일일 백업을 Hetzner Object Storage(월 약 1달러)에 저장하면 돼요.

최종 월 비용 계산:
- Fly.io: **$0** (무료 티어 유지 시)
- Hetzner CX22: **~$6**
- Hetzner Object Storage (250GB): **~$5**
- 도메인 + Cloudflare Free: **~$1 (연간 비용 월할)**
- **합계: 약 $12~13/월**

### 레이어 3: 자주 놓치는 운영 이슈

가장 많이 실패하는 포인트는 Hetzner 방화벽 설정이에요. 기본 설정을 그대로 두면 PostgreSQL 포트(5432)가 공개 인터넷에 열려요. 방화벽에서 Fly.io 아웃바운드 IP만 허용하거나, WireGuard로 프라이빗 네트워크를 구성하는 게 필수예요. 그런데 Fly.io는 자체적으로 WireGuard 기반 프라이빗 네트워크(`flycast`)를 제공하기 때문에 이 연결이 생각보다 간단해요.

---

## 클라우드 서비스 비교: 1인 개발자 기준

| 항목 | AWS (기본 구성) | Fly.io + Hetzner | Render (무료) | Railway (Hobby) |
|---|---|---|---|---|
| 월 비용 | $50~120 | $0~15 | $0 (제한적) | $5~20 |
| DB 포함 여부 | 별도 과금 | 포함 가능 | 별도 | 포함 |
| 슬립 모드 | 없음 | 없음 | 있음 | 없음 |
| 레이턴시 (아시아) | 낮음 (서울 리전) | 중간 | 중간 | 중간 |
| 스케일 가능성 | 매우 높음 | 중간 | 낮음 | 중간 |
| 설정 복잡도 | 높음 | 중간 | 낮음 | 낮음 |

r/webdev 가격 비교 계산기 데이터 기준, 동일 트래픽(월 10GB 아웃바운드, 2 vCPU, 4GB RAM)에서 AWS가 가장 비싸고 Hetzner가 가장 저렴해요. Fly.io는 무료 티어 한도 내에서는 비교 자체가 무의미할 만큼 유리해요.

핵심 트레이드오프는 이거예요. AWS는 관리가 편하고 한국 리전이 있어서 레이턴시가 낮아요. 반면 Fly.io + Hetzner는 훨씬 저렴하지만 네트워크 구성을 직접 해야 하고, Hetzner 서버는 유럽·미국에만 있어요. 한국 사용자가 주 타깃이라면 Cloudflare CDN으로 레이턴시 일부를 커버하는 게 현실적인 대안이에요.

---

## 이 구성을 써야 할 때, 쓰지 말아야 할 때

**맞는 경우:**
- MAU 10만 이하의 사이드 프로젝트나 초기 스타트업
- 인프라 비용을 6개월 이상 최소화해야 하는 부트스트랩 창업
- API 서버 + PostgreSQL + 간단한 파일 스토리지가 전부인 서비스

**맞지 않는 경우:**
- 한국 사용자 대상 실시간 서비스 (레이턴시 50~100ms 증가를 감수해야 해요)
- 컴플라이언스 요구사항이 있는 금융·의료 서비스 (Hetzner의 GDPR은 유럽 기준)
- 갑작스러운 트래픽 폭증이 예상되는 서비스 (무료 티어 한도 초과 시 대응 시간 필요)

항상 답은 아니에요. 하지만 초기 단계에서 비용 부담 없이 프로덕션 환경을 유지하는 데는 지금까지 나온 선택지 중 가장 현실적이에요.

---

## 앞으로 6~12개월 내에 올 변화

이 구성이 더 쉬워질 신호가 보여요.

- **Fly.io의 Machines API 고도화**: 2026년 들어 Fly.io가 GPU 인스턴스와 스케줄러 기능을 강화하고 있어요. AI 추론 서버를 동일 구조에 얹는 것도 시간문제예요.
- **Hetzner의 아시아 리전 소문**: 개발자 커뮤니티에서는 Hetzner가 2026~2027년 내 싱가포르 리전을 검토 중이라는 얘기가 돌아요. 확인된 공식 발표는 없지만, 실현되면 한국 타깃 서비스에도 이 조합이 진지한 선택지가 돼요.
- **클라우드 가격 전쟁**: AWS, Google Cloud가 소규모 사용자를 잡기 위해 무료 티어를 확대하는 추세예요. 경쟁이 심해질수록 개발자에게 유리해요.

지금 사이드 프로젝트가 있다면, 직접 계산해보는 게 가장 빠른 답이에요. Fly.io 무료 티어로 API 서버를 올리고, Hetzner CX22 하나 켜서 PostgreSQL을 붙여보세요. 월 청구서가 어떻게 바뀌는지 보이면, 그게 바로 이 구성이 맞는지 아닌지를 알려주는 제일 정직한 데이터예요.

---

*참고 자료: r/webdev Fly.io/Heroku/Render/Railway 가격 비교 계산기 (2025), Hetzner 공식 가격표 (cloud.hetzner.com), Fly.io 공식 프리 티어 정책 (fly.io/docs/about/pricing)*

## 참고자료

1. [풀스택 개발자 1인 외주, 정말 더 저렴할까?](https://zero100dev.tistory.com/entry/%ED%92%80%EC%8A%A4%ED%83%9D-%EA%B0%9C%EB%B0%9C%EC%9E%90-1%EC%9D%B8-%EC%99%B8%EC%A3%BC-%EC%A0%95%EB%A7%90-%EB%8D%94-%EC%A0%80%EB%A0%B4%ED%95%A0%EA%B9%8C)
2. [r/webdev on Reddit: Price comparison calculator for Fly.io, Heroku, Render, and Railway](https://www.reddit.com/r/webdev/comments/1j8vace/price_comparison_calculator_for_flyio_heroku/)
3. [1인 개발자 창업의 핵심은 '풀스택 개발' 역량 강화](https://hyunil.tistory.com/4)


---

*Photo by [Christian Palazzolo](https://unsplash.com/@carstocamera) on [Unsplash](https://unsplash.com/photos/race-car-with-cartoon-graphics-and-aws-logo-_Shiom3n3ak)*
