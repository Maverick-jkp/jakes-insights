---
title: "1인 개발자가 월 3~8달러로 풀스택 서비스 운영하는 법: Fly.io + Cloudflare R2 + Supabase 조합 분석"
date: 2026-03-17T20:09:40+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-cloud", "\uac1c\ubc1c\uc790", "10\ub2ec\ub7ec", "\ud480\uc2a4\ud0dd", "AWS"]
description: "Fly.io, Cloudflare R2, Supabase 조합으로 풀스택 서비스를 월 3~8달러에 운영하는 1인 개발자의 실제 청구서 공개. 이그레스 비용 없는 R2와 PostgreSQL 무료 티어 활용법 정리."
image: "/images/20260317-1인-개발자-월-10달러-이하-풀스택-인프라-flyio.webp"
technologies: ["AWS", "PostgreSQL", "GitHub Actions", "Cloudflare", "Supabase"]
faq:
  - question: "1인 개발자 월 10달러 이하로 풀스택 서비스 운영 가능한가요"
    answer: "1인 개발자 월 10달러 이하 풀스택 인프라 Fly.io Cloudflare R2 Supabase 실제 청구서 공개 사례에 따르면, MAU 1만 명 이하 서비스 기준 세 서비스 합산 월 청구액이 0~5달러 수준입니다. Fly.io shared-cpu-1x 인스턴스 1.94달러, Cloudflare R2 이그레스 비용 0달러, Supabase Free 플랜 조합으로 AWS 동급 구성(월 30~40달러) 대비 5~8배 저렴하게 실서비스를 운영할 수 있습니다."
  - question: "Cloudflare R2 vs AWS S3 비용 차이 얼마나 나나요"
    answer: "AWS S3는 데이터를 꺼낼 때마다 GB당 약 0.09달러의 이그레스 비용이 별도로 부과되지만, Cloudflare R2는 이그레스 비용이 완전히 없습니다. 월 100GB 이미지를 서빙하는 서비스라면 S3에서는 스토리지 비용과 별개로 이그레스만 9달러가 추가되는 반면, R2는 저장 비용(10GB 초과 시 GB당 0.015달러)만 청구되어 트래픽이 많을수록 절감 효과가 커집니다."
  - question: "Supabase 무료 플랜 한계 및 제한 사항"
    answer: "Supabase Free 플랜은 PostgreSQL 500MB, 월 50,000 MAU, Auth, Edge Function을 무료로 제공하지만 7일간 접속이 없으면 프로젝트가 자동 일시정지됩니다. MAU 5만 명 초과 시 월 25달러 Pro 플랜으로 전환해야 하며, PostgreSQL 연결 수 제한이 있어 트래픽이 급증할 경우 연결 풀링 설정이 필요합니다."
  - question: "Fly.io Render 무료 플랜 콜드 스타트 차이점"
    answer: "Fly.io는 Render.com 무료 플랜과 달리 슬립(sleep) 기능이 없어 인스턴스가 항상 실행 상태를 유지합니다. Render 무료 플랜은 일정 시간 요청이 없으면 인스턴스가 잠들어 첫 요청 시 수 초의 콜드 스타트 딜레이가 발생하지만, Fly.io는 shared-cpu-1x 기준 월 1.94달러를 내는 대신 이런 딜레이 없이 안정적인 응답 속도를 보장합니다."
  - question: "1인 개발자 풀스택 인프라 Fly.io Supabase 조합 한국 서비스에 적합한가요"
    answer: "1인 개발자 월 10달러 이하 풀스택 인프라 Fly.io Cloudflare R2 Supabase 실제 청구서 공개 내용에 따르면, 한국 사용자를 대상으로 할 경우 Fly.io 배포 시 기본값인 버지니아(iad) 리전 대신 반드시 도쿄(nrt) 또는 인천(icn) 리전을 선택해야 합니다. 기본 리전으로 배포하면 레이턴시가 200ms 이상 추가되어 체감 속도가 크게 저하될 수 있습니다."
aliases:
  - "/tech/2026-03-17-1인-개발자-월-10달러-이하-풀스택-인프라-flyio-cloudflare-r2-supab/"
  - "/ko/tech/2026-03-17-1인-개발자-월-10달러-이하-풀스택-인프라-flyio-cloudflare-r2-supab/"

---

사이드 프로젝트 시작하려고 AWS 콘솔 열었다가 그냥 닫은 적 있죠? 예상 비용 보고 '나중에 하지 뭐' 했던 거, 맞죠. 그런데 지금은 그 공식이 완전히 바뀌었어요.

> **핵심 요약**
> - Fly.io + Cloudflare R2 + Supabase 조합을 쓰면 초기 트래픽 기준 월 3~8달러 선에서 풀스택 서비스를 운영할 수 있어요.
> - Supabase Free 플랜은 PostgreSQL 500MB + Auth + Edge Function을 포함하며, 2026년 기준 무료 티어가 유지되고 있어요.
> - Cloudflare R2는 월 10GB 저장에 이그레스(데이터 전송) 비용이 없어서, AWS S3 대비 트래픽 비용이 사실상 0에 가까워요.
> - Fly.io는 shared-cpu-1x 256MB 인스턴스를 월 1.94달러에 제공하고, 무료 플랜에서도 앱 3개를 동시에 올릴 수 있어요.
> - 이 세 가지를 조합하면 초기 1인 개발자가 실서비스 수준의 인프라를 커피 두 잔 값으로 굴릴 수 있어요.

---

## 판이 바뀐 배경

2022년 11월, Heroku가 무료 플랜을 종료했어요. 수많은 사이드 프로젝트 개발자들이 이주처를 찾아야 했는데, 그 공백을 파고든 게 Fly.io였어요. 도커 이미지만 있으면 `fly launch` 한 줄로 배포가 끝나는 경험이 입소문을 탔죠.

같은 시기 Cloudflare도 R2 스토리지를 공개하면서 "이그레스 비용 없음"이라는 파격 조건을 내걸었어요. AWS S3에서 데이터를 꺼낼 때마다 붙는 전송 비용, 한 번이라도 청구서 받아보면 알아요. 꽤 무서워요.

Supabase는 Firebase의 오픈소스 대안으로 2020년 등장했어요. PostgreSQL 기반 백엔드에 Auth, Storage, Edge Function까지 묶어서 제공해요. 2026년 3월 현재 Free 플랜은 PostgreSQL 500MB, 월 50,000 MAU까지 무료예요.

세 서비스가 동시에 성숙기에 접어들면서 "월 10달러 이하 풀스택"이 실현 가능한 목표가 됐어요.

---

## 실제 청구서로 보는 세 서비스

### Fly.io: 도커 그대로 올리는 서버

shared-cpu-1x + 256MB 인스턴스가 월 1.94달러예요. 512MB로 올리면 3.83달러고요. 무료 플랜 기준으론 앱 3개, 월 160GB 전송, 3GB 볼륨 스토리지가 포함돼요.

일 평균 방문자 500명 이하인 초기 프로젝트라면 무료 티어로 충분한 경우가 많아요. 한도 초과 시 GB당 0.02달러가 붙는데, 일반적인 API 서버 트래픽에선 체감이 거의 없어요.

하나 짚을 게 있어요. Fly.io는 "슬립(sleep)" 기능이 없어요. Render.com 무료 플랜처럼 요청이 없으면 인스턴스가 잠들었다가 첫 요청에 몇 초 딜레이가 생기는 구조가 아니에요. 항상 떠 있어요. 그래서 1.94달러가 청구되는 거고요. 오히려 좋은 거죠.

### Cloudflare R2: 이그레스 없는 스토리지

AWS S3에서 1GB를 꺼낼 때마다 약 0.09달러의 이그레스 비용이 붙어요. 한 달에 이미지를 100GB 서빙하는 서비스라면 9달러가 스토리지 비용과 별개로 붙는 셈이에요. R2는 이 비용이 없어요.

무료 티어는 월 10GB 저장 + 100만 건 쓰기 + 1,000만 건 읽기를 제공해요. 초기 프로젝트에서 이 한도를 넘기는 쉽지 않아요. 10GB를 넘으면 GB당 0.015달러인데, S3(0.023달러)보다 여전히 저렴해요.

실제로 아바타 이미지, 첨부파일, 정적 에셋을 R2에 붙이면 CDN 비용까지 Cloudflare 엣지 네트워크가 자동으로 처리해요. 청구서에 0달러 찍히는 거 보면 좀 신기해요.

### Supabase: DB + Auth + 백엔드를 한 곳에

Supabase Free 플랜의 진짜 가치는 "쌓여 있는 기능"에 있어요. PostgreSQL만 해도 AWS RDS 최소 인스턴스가 월 13달러 수준인데, Supabase는 500MB까지 무료로 줘요. 거기다 Auth, Row Level Security, Edge Function까지 포함이에요.

제한도 명확해요. 비활성 프로젝트는 7일 후 일시정지돼요. 월 50,000 MAU가 넘으면 Pro 플랜(월 25달러)으로 가야 해요. PostgreSQL 연결 수도 제한적이라 트래픽이 갑자기 튀면 연결 풀링 설정이 필요해요.

---

### 세 서비스 실제 비용 비교

| 항목 | Fly.io | Cloudflare R2 | Supabase |
|------|--------|---------------|---------|
| 무료 한도 | 앱 3개, 160GB 전송 | 10GB 저장, 이그레스 무료 | DB 500MB, MAU 50K |
| 초기 유료 전환 기준 | shared-cpu 1x: $1.94/월 | 10GB 초과 시 $0.015/GB | Pro: $25/월 |
| 이그레스 비용 | $0.02/GB (무료 초과 후) | **없음** | 별도 없음 |
| AWS 동급 서비스 | EC2 t3.micro (~$7.5/월) | S3 (~$0.023/GB + 전송비) | RDS t3.micro (~$13/월) |
| 1인 개발자 실사용 월비용 | $0~$3 | $0 | $0 |

세 가지를 합치면, MAU 1만 명 이하 서비스 기준 월 청구 합계가 0~5달러 수준이에요. AWS 동급 구성이 월 30~40달러인 것과 비교하면 다섯 배에서 여덟 배 차이가 나요.

---

## 실제로 굴릴 때 주의할 점

**Supabase 프로젝트 휴면 관리**부터 짚을게요. Free 플랜에서 7일간 접속이 없으면 프로젝트가 일시정지돼요. GitHub Actions의 cron 트리거로 7일마다 `/api/health` 엔드포인트에 요청을 날려두면 충분해요.

**Fly.io 리전 선택**도 챙겨야 해요. 한국 사용자가 주 타겟이라면 `nrt`(도쿄) 또는 `icn`(인천) 리전을 쓰세요. 기본값인 `iad`(버지니아)로 배포하면 레이턴시가 200ms 이상 붙어요. 체감 속도가 달라요.

**비용 폭탄 방지**를 위해 세 서비스 모두 사용량 알림을 설정해두세요. Cloudflare는 R2 대시보드에서 요청 수 임계값 알림을, Supabase는 MAU 80% 도달 시 알림을 설정할 수 있어요. Fly.io는 월별 지출 한도를 설정하면 초과 시 앱이 자동으로 중단돼요.

**스케일 시나리오**도 미리 생각해두세요. MAU 5만 명을 넘기 시작하면 Supabase Pro(월 25달러)로 이동이 불가피해요. 그 시점엔 이미 서비스가 성장한 거니까 25달러는 합리적인 투자예요. Fly.io도 256MB → 512MB 업그레이드 시 3.83달러로 두 배가 되는데, 트래픽이 그만큼 늘었다면 감당할 수 있는 수준이에요.

---

## 이 스택, 앞으로 어떻게 될까요?

세 서비스 모두 2026년에도 무료 티어를 유지하고 있어요. Fly.io는 2025년 말에 GPU 인스턴스 지원을 확대했고, Supabase는 AI 벡터 검색(pgvector) 기능을 무료 플랜에도 열어줬어요. Cloudflare는 R2에 이어 Workers KV와 D1(SQLite 기반 엣지 DB)을 공격적으로 무료로 풀고 있고요.

가장 큰 변수는 Supabase의 무료 플랜 지속 여부예요. 현재 VC 펀딩으로 운영 중인 만큼 수익화 압력이 커지면 무료 MAU 한도를 조정할 가능성이 있어요. 그래도 최소한 10,000 MAU까지는 무료로 유지될 거라는 게 업계 관측이에요.

지금 사이드 프로젝트를 시작하려는 분이라면, 이 세 가지 조합이 현재 가장 가성비 높은 선택이에요. 월 3~8달러로 실서비스를 운영하다가, PMF(제품-시장 적합성)가 확인되면 그때 스케일 업을 고민하면 돼요.

커피 두 잔 값으로 서비스를 런칭할 수 있는 시대예요. 인프라 비용이 망설임의 이유라면, 그건 이제 유효한 핑계가 아니에요.

---

*참고 자료: Supabase 공식 가격 페이지 (2026년 3월 기준), costbench.com Supabase pricing analysis, Fly.io 공식 가격 문서, Cloudflare R2 공식 가격 페이지*

## 참고자료

1. [Supabase Pricing 2026: Free-$599/User Plans Compared](https://costbench.com/software/database-as-service/supabase/)
2. [풀스택 개발자 1인 외주, 정말 더 저렴할까?](https://zero100dev.tistory.com/entry/%ED%92%80%EC%8A%A4%ED%83%9D-%EA%B0%9C%EB%B0%9C%EC%9E%90-1%EC%9D%B8-%EC%99%B8%EC%A3%BC-%EC%A0%95%EB%A7%90-%EB%8D%94-%EC%A0%80%EB%A0%B4%ED%95%A0%EA%B9%8C)
3. [SDK님과 개발자님은 뭘 만드시는 건지](https://damoang.net/free/4218526)


---

*Photo by [Ales Nesetril](https://unsplash.com/@alesnesetril) on [Unsplash](https://unsplash.com/photos/gray-and-black-laptop-computer-on-surface-Im7lZjxeLhg)*
