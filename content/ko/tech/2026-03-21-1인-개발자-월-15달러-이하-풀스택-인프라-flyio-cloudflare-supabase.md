---
title: "1인 개발자가 월 15달러로 풀스택 운영하는 법: Fly.io + Cloudflare + Supabase 실제 구성"
date: 2026-03-21T19:40:52+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-cloud", "\uac1c\ubc1c\uc790", "15\ub2ec\ub7ec", "\ud480\uc2a4\ud0dd", "Python"]
description: "1인 개발자가 Fly.io, Cloudflare, Supabase 조합으로 월 10~15달러에 풀스택 SaaS 인프라를 실제 구성한 후기. AWS 없이 인증·DB·스토리지를 한 번에 해결하는 현실적인 방법을 공유합"
image: "/images/20260321-1인-개발자-월-15달러-이하-풀스택-인프라-flyio.webp"
technologies: ["Python", "JavaScript", "TypeScript", "Next.js", "Node.js"]
faq:
  - question: "1인 개발자 월 15달러 이하로 풀스택 서비스 운영 가능한가요"
    answer: "1인 개발자 월 15달러 이하 풀스택 인프라 Fly.io Cloudflare Supabase 실제 구성 후기 2025에 따르면, 이 세 플랫폼 조합으로 월 10~15달러 수준의 풀스택 SaaS 인프라 운영이 실제로 가능합니다. Cloudflare는 CDN과 프론트엔드 호스팅을 사실상 무료로 제공하고, Supabase 무료 플랜과 Fly.io 소형 인스턴스를 합치면 초기 비용을 최소화할 수 있습니다."
  - question: "Fly.io Supabase Cloudflare 조합 AWS랑 비용 비교하면 얼마나 차이나요"
    answer: "1인 개발자 월 15달러 이하 풀스택 인프라 Fly.io Cloudflare Supabase 실제 구성 후기 2025 분석에 따르면, 이 조합의 초기 월 비용은 10~15달러인 반면 AWS 기본 구성(EC2 + RDS + CloudFront)은 30~50달러 수준으로 약 세 배 차이가 납니다. 초기 DevOps 설정 시간도 AWS는 10~20시간이 걸리는 데 비해 이 조합은 2~4시간으로 훨씬 짧습니다."
  - question: "Supabase 무료 플랜 한도가 어느 정도인지 궁금합니다"
    answer: "Supabase 무료 플랜은 500MB 데이터베이스, 1GB 스토리지, 월 5만 MAU 인증을 제공합니다. 소규모 SaaS나 사이드 프로젝트라면 이 범위 안에서 충분히 운영할 수 있으며, 트래픽이 늘어나면 월 25달러 Pro 플랜으로 선형적으로 확장할 수 있습니다."
  - question: "Cloudflare Workers 무료 플랜 하루 요청 한도 얼마예요"
    answer: "Cloudflare Workers 무료 플랜은 하루 10만 요청이 포함되어 있으며, 초과 시 100만 요청당 0.50달러가 부과됩니다. 1인 개발자 기준으로는 간단한 API 라우팅, 인증 미들웨어, 리다이렉트 처리를 무료 범위 안에서 충분히 소화할 수 있습니다."
  - question: "Fly.io 무료 플랜 없어졌나요 2024년 이후 요금이 어떻게 되나요"
    answer: "Fly.io는 2024년에 무료 플랜을 폐지하여 처음부터 비용이 발생합니다. 가장 작은 shared-cpu-1x 인스턴스에 256MB 메모리 기준으로 월 약 1.94달러이며, 스토리지를 포함한 소규모 API 서버 운영 시 월 5~7달러 수준이 됩니다."
---

월 15달러로 풀스택을 돌린다고 하면 대부분 "그게 돼?" 하는 반응이에요. 됩니다. Fly.io + Cloudflare + Supabase 조합으로요.

AWS 없이도 제대로 된 서비스를 운영할 수 있냐는 질문, 1인 개발자 커뮤니티에서 반복해서 나오는 얘기예요. 대답부터 하자면: 가능해요. 비용과 복잡도 문제를 동시에 건드리는 구성이라서 조용히 퍼지고 있는 거고요.

> **핵심 요약**
> - Fly.io + Cloudflare + Supabase 조합은 월 10~15달러 수준으로 풀스택 SaaS 인프라를 운영할 수 있는 가장 현실적인 선택지 중 하나예요.
> - Supabase는 PostgreSQL 기반 BaaS로, 인증·실시간DB·스토리지를 단일 플랫폼에서 제공해요. 무료 플랜으로 시작해 월 25달러 Pro 플랜까지 선형적으로 확장돼요.
> - Cloudflare Workers + Pages는 CDN, 엣지 함수, 도메인 관리를 사실상 무료 수준에서 처리해요. 무료 플랜 기준 하루 10만 요청이 포함돼요.
> - Fly.io는 컨테이너 기반 백엔드 서버·API 운영에 쓰이며, 소규모 앱 기준 월 5~7달러 수준이에요.
> - 이 구성의 핵심은 "관리할 서버가 없다"는 거예요. DevOps 없이 개발에 집중할 수 있는 구조죠.

---

## 이 조합이 퍼진 이유

AWS나 GCP가 강력하긴 한데, 초기 단계 서비스에서는 설정 비용과 운영 부담이 문제예요. IAM 정책, VPC 구성, EC2 인스턴스 관리… 이걸 혼자 다 하면서 개발까지 병행하는 건 현실적으로 안 돼요.

그 빈틈을 Supabase, Fly.io, Cloudflare가 채웠어요. 셋 다 개발자 경험을 최우선으로 설계된 플랫폼이고, 무료 플랜이 넉넉해서 검증 단계에서 부담이 없어요.

Supabase는 2020년 오픈소스 Firebase 대안으로 시작했고, 2026년 현재 월간 활성 프로젝트가 100만 개를 넘었다고 자체 발표했어요. PostgreSQL을 그대로 쓸 수 있다는 점이 개발자들한테 특히 잘 평가받아요. 독점 API에 종속되지 않고, 나중에 다른 DB로 마이그레이션할 수 있거든요.

Fly.io는 Docker 컨테이너를 전 세계 엣지 리전에 배포하는 플랫폼이에요. 서울 리전도 있어서 국내 사용자 대상 서비스에도 쓸 수 있어요. Cloudflare는 CDN으로 이미 유명하지만, Workers와 Pages가 엣지 컴퓨팅 레이어를 거의 공짜로 제공한다는 게 실제 장점이에요.

---

## 실제 구성은 이렇게 생겼어요

### 레이어 1: 데이터와 인증 → Supabase

모든 구성의 중심에 Supabase가 있어요. 데이터베이스(PostgreSQL), 인증(이메일·OAuth·Magic Link), 스토리지(파일 업로드), 실시간 구독까지 한 플랫폼에서 돼요.

무료 플랜 기준으로 500MB DB, 1GB 스토리지, 월 5만 MAU 인증이 포함돼요. 소규모 SaaS나 사이드 프로젝트라면 이 범위에서 충분히 운영할 수 있어요. 트래픽이 늘어서 Pro 플랜으로 올리면 월 25달러인데, 그 단계쯤이면 이미 수익이 나고 있을 가능성이 높아요.

Row Level Security(RLS)가 내장돼 있어서 별도 인증 미들웨어 없이 DB 레벨에서 접근 제어가 가능해요. 서버리스 환경에서 특히 효과적인 구조예요.

### 레이어 2: 백엔드 로직 → Fly.io

API 서버나 백그라운드 작업이 필요하면 Fly.io에 컨테이너로 올려요. Node.js, Python, Go 뭐든 Docker로 감싸면 배포할 수 있어요.

요금 구조는 사용한 만큼 내는 방식이에요. 가장 작은 `shared-cpu-1x` + 256MB 메모리 인스턴스 하나면 월 약 1.94달러예요. 여기에 스토리지 몇 GB 더하면 소규모 API 서버 운영 비용이 5~7달러 수준이 돼요.

단점도 있어요. 콜드 스타트가 있고, 무료 플랜이 2024년에 폐지됐어요. 처음부터 비용이 나가요. 그래서 간단한 API는 Cloudflare Workers로 넘기고, 상태가 있는 서버나 장시간 실행 작업만 Fly.io에 올리는 식으로 역할을 나누는 게 효율적이에요.

### 레이어 3: 프론트엔드와 엣지 → Cloudflare

Cloudflare Pages는 정적 사이트와 Next.js·SvelteKit 같은 프레임워크를 무료로 호스팅해요. 빌드 횟수 제한이 월 500회인데, 1인 개발자 기준으로는 거의 신경 쓸 필요 없는 수준이에요.

Cloudflare Workers는 JavaScript/TypeScript로 엣지 함수를 실행해요. 무료 플랜에 하루 10만 요청이 포함돼 있고, 초과하면 100만 요청당 0.50달러예요. 간단한 API 라우팅이나 인증 미들웨어, 리다이렉트 처리를 여기서 다 처리하면 Fly.io 부하를 크게 줄일 수 있어요.

도메인 관리, DNS, SSL 인증서도 Cloudflare에서 다 돼요. 추가 비용 없이요.

### 비용 비교: 이 조합 vs 기존 방식

| 항목 | Fly.io + Cloudflare + Supabase | AWS 기본 구성 |
|------|-------------------------------|---------------|
| 컴퓨팅 | Fly.io ~$5-7 | EC2 t3.micro ~$8-10 |
| DB | Supabase 무료/25달러 | RDS t3.micro ~$15-20 |
| CDN/엣지 | Cloudflare 무료 | CloudFront + WAF ~$5-15 |
| 인증 | Supabase 포함 | Cognito ~$0.0055/MAU |
| 총 월비용 (초기) | **$10-15** | **$30-50** |
| DevOps 설정 시간 | 2-4시간 | 10-20시간 |
| 관리 부담 | 낮음 | 중간-높음 |
| 벤더 종속 위험 | 중간 (Supabase) | 높음 |

숫자가 꽤 차이 나죠? AWS 조합이 세 배 가까이 비싸요. 초기 설정 시간까지 더하면 격차가 더 벌어져요.

---

## 실제로 쓸 때 맞닥뜨리는 것들

### 잘 됐던 부분

Supabase의 JavaScript 클라이언트 라이브러리는 진짜 잘 만들어져 있어요. 인증부터 데이터 조회까지 10줄 안에 끝나거든요. Fly.io는 `fly deploy` 명령 하나로 배포가 끝나요. Cloudflare Pages는 GitHub 연동하면 PR 올릴 때마다 미리보기 URL이 자동 생성돼요.

전체 구성을 처음 세팅하는 데 약 3~4시간 걸려요. AWS 학습 곡선이랑 비교하면 이건 거의 없는 수준이에요.

### 주의해야 할 부분

Supabase 무료 플랜은 7일 비활성 시 DB가 일시정지돼요. 사이드 프로젝트라서 트래픽 없는 기간이 생기면 갑자기 서비스가 안 될 수 있어요. Fly.io는 무료 플랜이 없으니 처음부터 비용 계획이 필요해요.

Cloudflare Workers는 Node.js API 전체를 지원하지 않아요. `fs`, `path` 같은 네이티브 모듈은 못 써요. 이걸 모르고 기존 Express 앱을 그대로 올리려다가 막히는 경우가 많아요. 실제로 이 부분에서 삽질하는 사람이 꽤 돼요.

---

## 어떤 프로젝트에 맞는 구성인가?

**잘 맞는 경우:**
- MAU 1만 명 이하 SaaS 초기 단계
- 1인 개발 사이드 프로젝트
- PostgreSQL이 필요한 서비스
- DevOps에 시간을 쓰기 싫은 경우

**안 맞는 경우:**
- 대용량 파일 처리나 미디어 스트리밍
- 복잡한 마이크로서비스 아키텍처
- 컴플라이언스 요구사항이 강한 B2B 서비스 (금융, 의료)
- 트래픽이 갑자기 수백만 단위로 급증할 수 있는 서비스

---

## 앞으로 6개월, 뭘 지켜봐야 할까?

- **Supabase Edge Functions 성숙도**: 현재 베타 수준인 기능들이 안정화되면 Fly.io 없이도 구성이 가능해질 수 있어요.
- **Cloudflare D1 확장**: SQLite 기반 Cloudflare D1이 더 강력해지면 Supabase를 대체하는 초저비용 구성도 가능해질 수 있어요.
- **Fly.io 가격 정책 변화**: 2024년 무료 플랜 폐지 이후 추가 요금 조정 가능성이 있어요. 장기 운영 전에 Render나 Railway 같은 대안도 같이 봐두는 게 좋아요.

결론은 단순해요. 1인 개발자가 월 15달러 이하 풀스택 인프라를 찾는다면, Fly.io + Cloudflare + Supabase 조합은 검증된 선택지예요. 단, 스케일이 커지는 시점에 어떤 병목이 생기는지는 지금부터 머릿속에 그려둬야 해요.

아직 검증 전 단계라면, 이 구성으로 시작하는 게 가장 빠른 방법이에요.

## 참고자료

1. [풀스택 개발자 1인 외주, 정말 더 저렴할까?](https://zero100dev.tistory.com/entry/%ED%92%80%EC%8A%A4%ED%83%9D-%EA%B0%9C%EB%B0%9C%EC%9E%90-1%EC%9D%B8-%EC%99%B8%EC%A3%BC-%EC%A0%95%EB%A7%90-%EB%8D%94-%EC%A0%80%EB%A0%B4%ED%95%A0%EA%B9%8C)
2. [AI 시대, 오픈소스 백엔드의 강자 Supabase](https://brunch.co.kr/@ywkim36/188)
3. [Supabase 주요 기능 정리, 장단점까지 한눈에](https://myit.tistory.com/141)


---

*Photo by [NASA](https://unsplash.com/@nasa) on [Unsplash](https://unsplash.com/photos/photo-of-outer-space-Q1p7bh3SHj8)*
