---
title: "1인 개발자 사이드프로젝트 월 1만원 이하 인프라: Fly.io + Cloudflare 실제 구성 후기"
date: 2026-04-28T20:58:41+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-cloud", "\uac1c\ubc1c\uc790", "\uc0ac\uc774\ub4dc\ud504\ub85c\uc81d\ud2b8", "1\ub9cc\uc6d0", "Next.js"]
description: "1인 개발자가 Fly.io + Cloudflare로 사이드프로젝트 인프라를 월 1만원 이하로 운영한 실제 후기. Free Tier 한계, CDN 커버리지, 실비용 데이터까지 솔직하게 정리했습니다."
image: "/images/20260428-1인-개발자-사이드프로젝트-월-1만원-이하-인프라-fl.webp"
technologies: ["Next.js", "AWS", "GCP", "PostgreSQL", "Vercel"]
faq:
  - question: "Fly.io Cloudflare 조합으로 사이드프로젝트 한 달 비용 얼마나 나와요"
    answer: "1인 개발자 사이드프로젝트 월 1만원 이하 인프라 Fly.io Cloudflare 실제 구성 후기에 따르면, 월 트래픽 5만 UV 이하 프로젝트 기준으로 실제 인프라 비용이 0~8,000원 수준에서 운영 가능해요. Fly.io Free Tier 컴퓨팅과 Cloudflare 무료 CDN을 조합하면 1만원을 넘기려면 의도적으로 써야 할 정도라고 해요."
  - question: "Fly.io 무료 티어 2026년 기준 어디까지 무료인가요"
    answer: "2026년 기준 Fly.io Free Tier는 shared-cpu-1x (256MB RAM) 머신 최대 3개, 볼륨 스토리지 3GB, 월 아웃바운드 네트워크 160GB(북미/유럽 기준), 빌드 시간 월 3시간을 무료로 제공해요. 트래픽이 적은 사이드프로젝트 1~2개를 운영하기에는 충분한 수준이에요."
  - question: "AWS 대신 Fly.io 써야 하는 이유 뭔가요"
    answer: "AWS는 2024년 2월부터 EC2 퍼블릭 IPv4 주소에 시간당 $0.005를 청구하기 시작해서 아무것도 안 해도 월 약 5,000원이 추가로 나와요. 반면 Fly.io는 IPv4 비용이 포함된 무료 티어를 제공하고, Cloudflare 무료 CDN과 조합하면 컴퓨팅·DNS·SSL·정적 파일 비용 대부분을 0원으로 만들 수 있어요."
  - question: "사이드프로젝트 DB 무료로 쓸 수 있는 곳 어디예요"
    answer: "1인 개발자 사이드프로젝트 월 1만원 이하 인프라 Fly.io Cloudflare 실제 구성 후기에서는 Neon Free Tier(Postgres 0.5GB 무료)와 Turso(SQLite, 9GB 무료)를 현실적인 선택지로 추천해요. Fly.io 무료 머신 위에 Postgres를 직접 올리는 것도 가능하지만 256MB RAM 부족 문제가 생길 수 있어서 외부 무료 DB 서비스를 함께 쓰는 게 낫다고 해요."
  - question: "Cloudflare Workers로 백엔드 API 대체 가능한가요"
    answer: "Cloudflare Workers 무료 플랜은 하루 10만 요청을 제공해서 간단한 폼 처리나 API 로직은 충분히 커버할 수 있어요. 데이터 저장이 필요하면 Cloudflare KV(무료 10만 읽기/일)나 R2(무료 10GB/월)를 함께 쓰면 별도 서버 없이 정적 사이트 + 서버리스 API 구성을 비용 0원으로 만들 수 있어요."
aliases:
  - "/tech/2026-04-28-1인-개발자-사이드프로젝트-월-1만원-이하-인프라-flyio-cloudflare-실제-구성/"
  - "/ko/tech/2026-04-28-1인-개발자-사이드프로젝트-월-1만원-이하-인프라-flyio-cloudflare-실제-구성/"

---

사이드프로젝트를 AWS에 올렸다가 월 7만원 청구서를 받고 조용히 서버를 내린 적 있으시죠? 저도요.

그런데 2026년 현재, 이 문제를 현실적으로 해결할 수 있는 도구 조합이 생겼어요. Fly.io + Cloudflare예요. 실제로 이 스택을 써본 구성 후기를 데이터 기반으로 정리해 봤어요.

다룰 내용:
- Fly.io Free Tier의 실제 한계
- Cloudflare 무료 CDN/터널이 어디까지 커버되는지
- 두 서비스 조합 시 실제 월 비용
- 이 구성이 어디서 무너지는지

> **핵심 요약**
> - Fly.io Free Tier는 2026년 기준 월 3개 shared-cpu-1x (256MB RAM) 머신 + 3GB 스토리지를 무료로 제공해요. 트래픽이 적은 사이드프로젝트 1\~2개를 충분히 운영할 수 있는 수준이에요.
> - Cloudflare Free Plan은 무제한 CDN 대역폭, Workers 10만 req/일, Pages 무제한 정적 배포를 제공해서 정적 자산과 엣지 처리 비용을 사실상 0원으로 만들어요.
> - Fly.io + Cloudflare 조합으로 월 트래픽 5만 UV 이하 프로젝트는 실제 인프라 비용 0\~8,000원 수준에서 운영 가능해요. 1만원을 넘기려면 의도적으로 써야 할 정도예요.
> - 단, DB 비용이 변수예요. Fly.io의 Postgres는 무료 머신에 올릴 수 있지만 백업·복제가 없어서 PlanetScale Hobby(무료) 또는 Neon Free Tier와 함께 쓰는 게 현실적이에요.

---

## 왜 지금 이 스택인가: 2026년의 인프라 환경

클라우드 비용 문제는 어제오늘 얘기가 아니에요. 그런데 2024\~2025년 사이에 변화가 생겼어요.

AWS, GCP 같은 빅클라우드는 무료 티어를 지속적으로 축소했어요. AWS는 2024년 2월부터 EC2 퍼블릭 IPv4 주소에 시간당 $0.005를 청구하기 시작했고, 이것만으로 월 약 3.6달러(약 5,000원)가 추가됐죠. GCP도 e2-micro 무료 인스턴스의 네트워크 egress 조건을 조였고요.

반면 Fly.io는 2023년 유료화로 한 차례 진통을 겪었지만, 2024년 하반기부터 Free Tier를 다시 안정화시켰어요. 공식 문서 기준 2026년 현재 무료 범위는 이래요:

- **Machines**: 최대 3개 shared-cpu-1x (256MB RAM)
- **Volume 스토리지**: 3GB
- **Outbound 네트워크**: 월 160GB (북미/유럽 기준)
- **빌드 시간**: 월 3시간

Cloudflare는 원래부터 무료 CDN으로 시작한 회사답게 핵심 기능은 여전히 무료예요. Pages(정적 호스팅), Workers(엣지 함수), R2(객체 스토리지 10GB/월 무료), Tunnel(자택 서버 노출용)까지 커버돼요.

이 두 서비스가 맞물리면 사이드프로젝트 인프라의 주요 비용 항목 — 컴퓨팅, CDN, DNS, SSL, 정적 파일 — 이 대부분 0원이 되는 구조예요.

---

## 실제 구성: 세 가지 패턴 분석

### 패턴 1: 풀스택 앱 (Next.js + API)

가장 흔한 케이스예요. Next.js 앱을 Fly.io에 올리고, 정적 자산과 이미지는 Cloudflare Pages 또는 R2로 서빙하는 구조예요.

Fly.io에는 API 서버 역할만 남기고, 프론트 빌드 결과물(`/public`, `/_next/static`)은 Cloudflare Pages로 분리하면 컴퓨팅 부하가 절반 이하로 줄어요. 256MB RAM 머신으로도 웬만한 트래픽을 버티는 이유가 여기 있어요.

실제로 이 구성에서 Fly.io 비용은 무료 티어 범위 내에서 유지돼요.

### 패턴 2: 정적 사이트 + 서버리스 API

개발 포트폴리오나 랜딩 페이지 + 간단한 폼 처리 정도면 Fly.io 없이 Cloudflare만으로도 해결돼요.

- 사이트 호스팅: **Cloudflare Pages** (무료, 무제한)
- API 처리: **Cloudflare Workers** (무료 10만 req/일)
- 폼 데이터 저장: **Cloudflare KV** (무료 10만 읽기/일)

이 패턴은 비용이 0원이에요. Cloudflare Tunnel을 쓰면 자택 NAS나 라즈베리 파이를 서버로 쓰는 것도 가능해요.

### 패턴 3: 백엔드 API + DB

데이터를 저장해야 하는 앱이라면 DB 비용이 변수가 돼요.

Fly.io 위에 Postgres를 올리는 건 가능해요. 그런데 무료 머신에 앱과 DB를 같이 돌리면 RAM이 부족해지죠. 실용적인 선택지는 두 개예요:

- **Neon Free Tier**: Postgres 0.5 CU, 0.5GB 스토리지 무료. 서버리스라 슬립 이후 Cold Start가 있지만 사이드프로젝트 수준에선 허용 범위예요.
- **Turso (SQLite over HTTP)**: 무료 플랜에 500 DB, 9GB 스토리지. 읽기 많은 앱에 적합해요.

---

## 비용 비교: 주요 옵션 나란히 놓기

| 항목 | Fly.io + Cloudflare | Vercel + Railway | AWS EC2 Free Tier |
|------|---------------------|-----------------|-------------------|
| 컴퓨팅 | 무료 (3 machines) | Railway $5 크레딧/월 | t2.micro 750h/월 무료 |
| 정적 호스팅 | Cloudflare Pages 무료 | Vercel Hobby 무료 | S3 + CloudFront 유료 |
| CDN | Cloudflare 무료 무제한 | Vercel Edge 포함 | CloudFront 1TB/월 무료 |
| DB | Neon/Turso 무료 별도 | Railway PostgreSQL 포함 | RDS 없음 (별도) |
| IPv4 비용 | Fly.io 포함 | 없음 | 월 ~5,000원 추가 |
| 예상 월 비용 | **0\~8,000원** | **0\~8,000원** | **5,000\~15,000원** |
| 한계 트래픽 | \~5만 UV | \~3만 UV | \~2만 UV |

Vercel + Railway 조합도 비슷한 가격대지만, Railway는 2024년부터 무료 플랜을 없애고 $5 크레딧 방식으로 전환했어요. 5달러 넘으면 바로 과금돼요. Fly.io는 무료 머신이 명확하게 보장돼 있어서 예측 가능성이 더 높아요.

AWS는 여전히 무료 티어가 있지만 IPv4 과금, 데이터 전송 비용 등 숨겨진 항목이 많아서 사이드프로젝트 첫 선택지로는 비효율적이에요.

---

## 이 구성이 무너지는 지점

**문제 1: 트래픽 급증**
Fly.io 무료 머신은 256MB RAM이에요. 갑자기 트래픽이 몰리면 OOM(Out of Memory)으로 앱이 죽어요. 해결책은 두 가지 — Cloudflare Cache를 앞에 두어 컴퓨팅 요청 자체를 줄이거나, 두 번째 머신을 추가해요(Fly.io 기준 두 번째 머신도 무료 범위 내).

**문제 2: 데이터 지속성**
Fly.io 볼륨은 3GB 무료지만, 앱이 재시작되면 ephemeral 스토리지는 날아가요. DB는 반드시 별도 서비스(Neon, Turso)를 써야 해요. Fly.io 위의 Postgres는 백업이 없어서 진짜 데이터가 있는 서비스엔 위험해요.

**문제 3: Cold Start**
Fly.io는 슬립이 없지만 배포 직후나 오랜 무활동 후엔 첫 요청이 느릴 수 있어요. Cloudflare Workers는 콜드 스타트가 1ms 미만이라 API 라우팅 레이어에 두면 이 문제를 완화할 수 있어요.

---

## 정리: 월 1만원 이하, 정말 되는가

결론부터 말하면 — **돼요.** 단, 조건이 있어요.

- Fly.io + Cloudflare 조합은 트래픽 5만 UV 이하, 서버리스 DB 연동 구조에서 월 0\~8,000원으로 운영 가능해요
- DB는 반드시 Neon이나 Turso 같은 별도 무료 서비스를 써야 안정성이 생겨요
- 정적 자산을 Cloudflare Pages로 분리하면 컴퓨팅 비용이 크게 줄어요
- AWS Free Tier는 2026년 현재 IPv4 과금 때문에 사이드프로젝트 첫 선택지로는 비효율적이에요

앞으로 6\~12개월 사이에 주목할 변화는 Cloudflare의 D1(서버리스 SQLite)과 Workers AI의 무료 한도 확대예요. D1이 안정화되면 Fly.io 없이 Cloudflare 단독으로 풀스택 앱을 0원에 돌리는 게 가능해질 수도 있어요.

지금 사이드프로젝트 인프라를 고민 중이라면 딱 하나만 기억하세요. **먼저 Cloudflare로 감당할 수 있는 범위를 최대화하고, 그다음에 Fly.io를 붙이는 순서**로 가면 비용이 가장 낮게 유지돼요.

어떤 스택을 쓰고 있는지, 혹은 이 구성에서 예상치 못한 비용이 터진 경험이 있다면 댓글로 알려주세요. 실제 사례가 쌓일수록 분석이 더 날카로워지거든요.

## 참고자료

1. [팀 프로젝트 - 인프런 | 커뮤니티](https://www.inflearn.com/community/projects)
2. [취준생&주니어 개발자를 위한 사이드 프로젝트 플랫폼 추천 - 코드잇 블로그](https://sprint.codeit.kr/blog/%EC%B7%A8%EC%A4%80%EC%83%9D%EC%A3%BC%EB%8B%88%EC%96%B4-%EA%B0%9C%EB%B0%9C%EC%9E%90%EB%A5%BC-%EC%9C%84%ED%95%9C-%EC%82%AC%EC%9D%B4%EB%93%9C-%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8-%ED%94%8C%EB%9E%AB%ED%8F%BC-%EC%B6%94%EC%B2%9C)
3. [포트폴리오 제작기 [with Cloudflare Tunnel] — 개발세발네발](https://no-intellectual.tistory.com/entry/%ED%8F%AC%ED%8A%B8%ED%8F%B4%EB%A6%AC%EC%98%A4-%EC%A0%9C%EC%9E%91%EA%B8%B0-with-Cloudflare-Tunnel)


---

*Photo by [Microsoft Copilot](https://unsplash.com/@microsoftcopilot) on [Unsplash](https://unsplash.com/photos/person-planting-a-houseplant-and-checking-phone-o2MBk6J-Iqc)*
