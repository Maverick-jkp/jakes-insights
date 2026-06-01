---
title: "1인 개발자 사이드 프로젝트 월 5달러 이하 인프라: Fly.io·Supabase·Cloudflare 실제 구성"
date: 2026-03-26T20:07:58+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-cloud", "\uac1c\ubc1c\uc790", "\uc0ac\uc774\ub4dc", "\ud504\ub85c\uc81d\ud2b8", "Python"]
description: "Fly.io, Supabase, Cloudflare 조합으로 사이드 프로젝트 인프라 비용을 월 0~3달러로 줄이는 실제 구성법. AWS 월 40달러 청구서 없이 글로벌 트래픽과 PostgreSQL 인증까지 한 번에 해결"
image: "/images/20260326-1인-개발자-사이드-프로젝트-월-5달러-이하-인프라-f.webp"
technologies: ["Python", "React", "Next.js", "Node.js", "Docker"]
faq:
  - question: "1인 개발자 사이드 프로젝트 월 5달러 이하로 인프라 운영 가능한가요"
    answer: "Fly.io + Supabase + Cloudflare 조합을 사용하면 1인 개발자 사이드 프로젝트를 월 5달러 이하 인프라로 실제 운영할 수 있습니다. Fly.io Hobby 플랜 무료, Supabase Free Tier, Cloudflare 무료 CDN을 조합하면 도메인 비용 제외 시 월 0~3달러 수준이며, 메모리 업그레이드가 필요해도 월 1.94달러 추가로 해결됩니다."
  - question: "Supabase free tier 7일 비활성 정지 우회 방법"
    answer: "Supabase Free Tier는 7일 이상 활성 쿼리가 없으면 프로젝트가 자동 일시정지됩니다. GitHub Actions를 활용해 7일마다 자동으로 헬스체크 쿼리를 날리는 방식으로 간단하게 우회할 수 있습니다."
  - question: "Fly.io vs Render 무료 티어 차이점 비교"
    answer: "가장 결정적인 차이는 Render 무료 인스턴스는 15분 비활성 시 슬립 모드가 걸리지만, Fly.io는 sleep 정책이 없다는 점입니다. Fly.io 무료 티어는 shared-cpu-1x, 256MB RAM, 자동 HTTPS, 커스텀 도메인을 제공하며 사이드 프로젝트 운영에 더 안정적입니다."
  - question: "Fly.io Supabase Cloudflare 조합 실제 아키텍처 어떻게 구성하나요"
    answer: "1인 개발자 사이드 프로젝트 월 5달러 이하 인프라의 표준 패턴은 Cloudflare Pages에 React/Next.js 프론트엔드를 배포하고, Fly.io는 백엔드 API만 담당하며, Supabase가 DB·인증·파일 스토리지·실시간 구독을 처리하는 3레이어 분리 구조입니다. 이 구성으로 인증, 데이터베이스, 실시간 기능, 엣지 캐싱을 단일 프로젝트에서 모두 무료로 커버할 수 있습니다."
  - question: "인디 SaaS MVP 최소 비용으로 만들 수 있는 기술 스택 추천"
    answer: "월 100~500명 유저 규모의 인디 SaaS MVP라면 Fly.io + Supabase + Cloudflare 조합이 검증된 선택입니다. Supabase의 Row Level Security로 멀티테넌트 데이터 격리가 즉시 가능하고, Stripe 연동도 Fly.io에서 충분히 소화되며, 경쟁 스택인 Render + PlanetScale 조합 대비 월 7달러 이상 절감됩니다."
---

사이드 프로젝트 하나를 AWS에 올렸다가 월 40달러 청구서를 받은 적 있죠? 그 순간 "이거 계속 운영해야 하나..." 고민하게 되는 거, 저도 알아요.

그런데 지금 1인 개발자들 사이에서 검증된 조합이 있어요. Fly.io + Supabase + Cloudflare. 이게 그냥 "무료 티어 짜깁기"가 아니에요. 실제 트래픽을 버티고, 스케일도 되는 구성이에요.

> **핵심 요약**
> - Fly.io Hobby 플랜(무료) + Supabase Free Tier 기준, 월 실비용은 도메인 제외하고 0~3달러 수준이에요.
> - Cloudflare 무료 CDN + Workers는 글로벌 응답 속도 문제를 추가 비용 없이 해결해줘요.
> - Supabase는 PostgreSQL + 인증 + 스토리지 + 실시간 구독을 한 플랫폼에서 제공해서, 백엔드 구축 시간을 절반 이하로 줄여줘요.
> - 실제 한계는 Supabase Free Tier 7일 비활성 정지 정책과 Fly.io 256MB 메모리 제한인데, 둘 다 월 5달러 이하에서 해결책이 있어요.

---

## 왜 지금 이 조합인가

2024년까지만 해도 선택지가 제한적이었어요. Heroku는 2022년 무료 플랜을 없앴고, Render 무료 인스턴스는 15분 비활성 시 슬립 모드가 걸렸죠. Vercel은 프론트엔드에 최적화되어 있어서, 백엔드가 필요한 순간 별도 서비스가 필요했고요.

그러다 세 흐름이 맞물렸어요.

**Fly.io가 컨테이너 배포를 확 간소화했어요.** `fly launch` 명령어 하나로 Docker 컨테이너를 전 세계 30개 이상 리전에 올릴 수 있게 됐거든요. Hobby 플랜 기준 월 3개의 공유 CPU 인스턴스와 256MB RAM이 무료예요.

**Supabase가 오픈소스 Firebase 대안으로 자리잡았어요.** PostgreSQL 그대로 쓰면서 REST API, 실시간 구독, 인증, 파일 스토리지가 함께 나와요. 2024년 기준 GitHub 스타 7만 개를 넘긴 플랫폼이에요.

**Cloudflare Workers가 엣지 컴퓨팅 진입 장벽을 없앴어요.** 월 10만 건 요청까지 무료고, CDN은 기본 제공이에요.

이 세 조합이 2025~2026년 사이 1인 개발자 커뮤니티에서 "검증된 스택"으로 굳어진 배경이에요.

---

## 세 레이어가 각자 하는 일

### Fly.io: 서버 실행 레이어

쉽게 말해 "Docker를 전 세계에 쉽게 띄우는 플랫폼"이에요.

- `fly launch` → Dockerfile 자동 감지 → 리전 선택 → 배포 완료
- 무료 티어: `shared-cpu-1x`, 256MB RAM, 3GB 스토리지
- 자동 HTTPS, 커스텀 도메인 지원

Node.js, Python, Go, Ruby 거의 다 돼요. **Render 무료 티어와 결정적 차이는 sleep이 없다는 점**이에요. 다만 메모리 256MB는 운영 중 병목이 될 수 있어요. 이 경우 월 1.94달러짜리 512MB 업그레이드만으로 해결되는 경우가 대부분이에요.

### Supabase: 데이터 + 인증 레이어

Free Tier가 제공하는 게 생각보다 많아요.

- PostgreSQL 500MB
- 인증 (이메일/소셜 로그인 포함) 무제한
- 파일 스토리지 1GB
- 실시간 구독 (WebSocket 기반)
- REST API + GraphQL 자동 생성

**주의할 정책 하나**: 7일 이상 활성 쿼리가 없으면 프로젝트가 일시정지돼요. 사이드 프로젝트 초기엔 트래픽이 없는 시기가 있거든요. GitHub Actions로 7일마다 자동 헬스체크 쿼리를 날리는 방식으로 간단히 우회할 수 있어요.

### Cloudflare: 엣지 + 보안 레이어

세 가지 역할을 해요.

1. **DNS + CDN**: 정적 에셋 캐싱, HTTPS 자동화
2. **Workers**: 엣지에서 가벼운 로직 실행 (월 10만 요청 무료)
3. **Pages**: 프론트엔드 정적 배포

Cloudflare Pages로 React/Next.js 정적 빌드를 무료 배포하고, Fly.io는 백엔드 API만 담당하는 분리 구조가 이 스택의 표준 패턴이에요.

---

## 경쟁 스택과 실비용 비교

| 항목 | Fly.io + Supabase + Cloudflare | Render + PlanetScale + Vercel | Railway + Neon + Vercel |
|------|-------------------------------|-------------------------------|-------------------------|
| 월 기본 비용 | $0~3 | $7~15 | $5~10 |
| DB 무료 용량 | 500MB (PostgreSQL) | 5GB (MySQL) | 3GB (PostgreSQL) |
| Sleep 정책 | 없음 | 있음 (무료 티어) | 없음 |
| 커스텀 도메인 | 무료 | 유료 | 무료 |
| 실시간 기능 | 내장 | 별도 구성 필요 | 별도 구성 필요 |
| 인증 내장 | 있음 | 없음 | 없음 |
| 학습 곡선 | 중간 | 낮음 | 낮음 |

Render + PlanetScale은 학습 곡선이 낮지만 실비용이 월 7달러 이상으로 올라가요. Railway는 중간 지점이지만 인증과 실시간 기능이 번들되어 있지 않아서 추가 서비스가 필요해지는 경우가 많아요.

이 조합의 가장 큰 강점은 **인증, DB, 실시간, 파일 저장, 엣지 캐싱을 단일 프로젝트에서 전부 무료로 커버**한다는 점이에요.

---

## 어떤 프로젝트에 맞는가

**인디 SaaS MVP**: 월 100~500명 유저 규모의 구독형 웹앱이라면 딱 맞아요. Supabase Row Level Security(RLS)로 멀티테넌트 데이터 격리가 바로 되고, Stripe 연동까지 Fly.io에서 충분히 소화돼요.

**개인 포트폴리오 + 백엔드 API**: Next.js 프론트는 Cloudflare Pages, API 서버는 Fly.io, DB는 Supabase. 이 구성이면 월 0달러도 가능해요. 단, Supabase 7일 정지 정책 때문에 헬스체크 자동화는 필수예요.

**트래픽 급증이 예상되는 경우**: 이 스택의 한계가 드러나는 시점이에요. Supabase Free Tier는 동시 연결 60개 제한이 있고, Fly.io 무료 인스턴스는 트래픽 스파이크에 취약해요. 이 단계부터는 Supabase Pro($25/월) 업그레이드가 현실적인 선택이에요. 그래도 AWS나 GCP 대비 비용은 훨씬 낮아요.

---

## 월 5달러 이하 인프라는 타협이 아니에요

요약하면 이래요.

- **Fly.io**: Sleep 없는 무료 컨테이너 실행, Docker 기반으로 이식성 높음
- **Supabase**: DB + 인증 + 실시간 + 스토리지 올인원, 단 7일 정지 정책 주의
- **Cloudflare**: CDN + Pages + Workers로 엣지 레이어 무료 커버
- **실비용**: 도메인 제외 월 0~3달러, 트래픽 증가 시 단계적 업그레이드 가능

참고로 앞으로 6~12개월 사이 Supabase Free Tier 정책이 바뀌거나 Fly.io가 새 플랜을 낼 가능성이 있어요. 두 서비스 모두 2025~2026년 시리즈 펀딩을 받았고, 수익화 압력이 커지는 시점이거든요.

그래서 지금이 타이밍이에요. 어떤 스택을 쓰느냐보다, 실제로 배포하고 유저 피드백을 받는 게 먼저예요. 만들고 싶은 프로젝트가 있다면, 오늘 `fly launch`부터 쳐보세요.

## 참고자료

1. [Supabase CLI | Supabase Docs](https://supabase.com/docs/guides/local-development/cli/getting-started)
2. [SDK님과 개발자님은 뭘 만드시는 건지](https://damoang.net/free/4218526)
3. [AI 시대, 오픈소스 백엔드의 강자 Supabase](https://brunch.co.kr/@ywkim36/188)


---

*Photo by [NASA](https://unsplash.com/@nasa) on [Unsplash](https://unsplash.com/photos/photo-of-outer-space-Q1p7bh3SHj8)*
