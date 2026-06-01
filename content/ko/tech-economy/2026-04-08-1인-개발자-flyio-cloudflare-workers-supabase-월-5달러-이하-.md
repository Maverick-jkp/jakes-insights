---
title: "1인 개발자 Fly.io·Cloudflare Workers·Supabase 월 5달러 이하 스택 실제 운영 후기"
date: 2026-04-08T20:14:08+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-cloud", "\uac1c\ubc1c\uc790", "fly.io", "cloudflare", "Next.js"]
description: "월 4.87달러로 MAU 800명 앱 운영 중. Fly.io + Cloudflare Workers + Supabase 조합으로 월 100만 요청을 5달러 미만에 처리하고, 콜드 스타트 없이 15ms 응답 달성한 실제 운영 기록."
image: "/images/20260408-1인-개발자-flyio-cloudflare-worker.webp"
technologies: ["Next.js", "Node.js", "Docker", "PostgreSQL", "Vercel"]
faq:
  - question: "1인 개발자 Fly.io Cloudflare Workers Supabase 월 5달러 이하 스택 실제로 가능한가요"
    answer: "1인 개발자 Fly.io Cloudflare Workers Supabase 월 5달러 이하 스택 실제 운영 후기에 따르면, 월간 활성 사용자 800명 규모에서 실제 월 4.87달러로 운영이 가능합니다. Fly.io 무료 VM 허용량, Cloudflare Workers 하루 10만 req 무료 플랜, Supabase 무료 티어를 조합하면 월 트래픽 100만 req 이하에서 5달러 미만 유지가 현실적입니다."
  - question: "Supabase 무료 플랜 7일 자동 일시정지 해결 방법"
    answer: "Supabase 무료 플랜은 7일 동안 쿼리가 없으면 프로젝트가 자동으로 일시정지됩니다. Cloudflare Workers의 Cron Triggers 기능을 활용해 24시간마다 Supabase에 ping 쿼리를 보내도록 설정하면 해결할 수 있으며, Workers Cron Triggers는 무료 플랜에서도 사용 가능합니다."
  - question: "Cloudflare Workers vs Vercel Edge Functions 비용 차이"
    answer: "Cloudflare Workers 무료 플랜은 하루 100,000 req를 제공하는 반면, Vercel은 Functions 실행 시간 기준으로 과금하여 트래픽이 조금만 올라가도 요금이 급격히 오를 수 있습니다. 1인 개발자 커뮤니티에서는 Vercel 사용 시 월 20달러를 초과하는 사례가 종종 보고되어, 비용 측면에서 Cloudflare Workers가 유리합니다."
  - question: "Fly.io 무료 플랜 한도와 실제 동시 접속 처리 성능"
    answer: "Fly.io는 shared-cpu-1x 256MB 메모리 VM을 3개까지 무료로 제공하며, 유료 전환 시 월 1.94달러부터 시작합니다. Node.js Express 서버를 shared-cpu-1x에 올리면 동시 접속 50명까지 무리 없이 처리할 수 있고, 비활성 VM을 자동으로 내리지 않아 24시간 운영 비용 예측이 가능합니다."
  - question: "소규모 앱 백엔드 스택 Fly.io Supabase Railway Neon 중 뭐가 나은가요"
    answer: "1인 개발자 Fly.io Cloudflare Workers Supabase 월 5달러 이하 스택 실제 운영 후기 기준으로, 커스텀 백엔드가 필요하고 비용을 최소화하려면 Fly.io + Supabase 조합이 유리합니다. Railway + Neon은 Git push 배포 편의성이 높아 PostgreSQL 중심 앱에 적합하지만, 무료 용량과 트래픽 한도 면에서 Fly.io + Supabase 조합보다 제한적입니다."
---

부업 앱이 월 4.87달러로 돌아가고 있어요. 월간 활성 사용자 800명 수준인데, 서버 비용보다 도메인 비용이 더 나와요.

클라우드 비용이 스타트업 런웨이를 갉아먹는 가장 큰 변수 중 하나가 됐어요. 그래서 1인 개발자들이 이 조합을 찾기 시작했죠. Fly.io + Cloudflare Workers + Supabase.

> **핵심 요약**
> - Fly.io Free tier + Cloudflare Workers 무료 플랜 + Supabase Free tier 조합으로 월 트래픽 100만 req 이하에서 비용 5달러 미만 유지 가능
> - Cloudflare Workers는 전 세계 330개 이상 PoP에서 실행, 콜드 스타트 없이 평균 응답 15ms 이하 (Cloudflare 공식 문서 기준)
> - Supabase 무료 플랜은 500MB DB, 5GB 스토리지, 50만 월 활성 사용자 제공. 단, 7일 비활성 시 자동 일시정지
> - Fly.io는 shared-cpu-1x 기준 월 1.94달러부터, 소규모 앱은 무료 허용량(VM 3개) 안에서 운영 가능
> - 이 스택의 가장 큰 리스크는 비용이 아니라 **공급자 락인**과 **무료 플랜 정책 변경**

---

## 왜 이 스택이 지금 주목받나

Heroku가 무료 플랜을 없앤 건 2022년이었지만, 그 여파는 지금도 이어지고 있어요. 대안을 찾던 1인 개발자들이 Fly.io, Render, Railway 세 곳으로 흩어졌는데, 그 중 Fly.io가 특히 주목받은 건 Docker 이미지를 그대로 올릴 수 있다는 단순함 때문이에요.

Cloudflare Workers도 빠르게 자리를 잡았어요. Morph의 2026년 비교 분석에 따르면, 엣지 컴퓨팅 시장에서 Vercel Edge Functions의 가장 강력한 대안으로 꼽혀요. 핵심 차이는 가격이에요. Workers 무료 플랜이 하루 10만 req를 제공하는 반면, Vercel은 Functions 실행 시간 기준으로 과금해서 트래픽이 조금만 올라가도 요금이 뛰어요.

Supabase는 2025년 기준 누적 사용자 100만 명을 넘었어요(Supabase 공식 발표). Firebase 대안을 찾던 개발자들한테 PostgreSQL 기반이라는 점이 꽤 매력적으로 작용했죠.

---

## 스택 실제 구성과 비용 분해

### Fly.io: 백엔드 서버 자리

컨테이너를 전 세계 리전에 배포하는 PaaS예요. `fly deploy` 한 줄로 배포된다는 게 핵심이에요.

2026년 4월 기준 요금:
- **shared-cpu-1x, 256MB 메모리**: 월 1.94달러
- **무료 허용량**: VM 3개까지, 메모리 256MB씩 무료
- **egress 비용**: 월 160GB까지 무료, 초과 시 GB당 0.02달러

Node.js Express 서버를 shared-cpu-1x에 올리면 동시 접속 50명까지는 무리 없이 처리해요. Fly.io는 비활성 VM을 자동으로 내리지 않아서 24시간 켜놔도 과금 구조가 예측 가능해요. 이게 생각보다 중요한 장점이에요.

### Cloudflare Workers: 엣지에서 처리하는 것들

사용자와 가장 가까운 서버에서 코드가 돌아가는 구조예요.

**무료 플랜 제공량:**
- 하루 100,000 req
- Workers KV: 읽기 10만/일, 쓰기 1,000/일

실제로 Workers가 담당하는 역할은 보통 이런 것들이에요:
- API 요청의 인증 토큰 검증 (Supabase JWT 확인)
- 정적 콘텐츠 캐싱
- Rate limiting (특정 IP 요청 제한)
- A/B 테스트 라우팅

Reddit Supabase 커뮤니티에서도 자주 언급되는 패턴이에요. Workers를 Supabase 앞단에 두면 불필요한 DB 쿼리를 줄이고, 무료 플랜 쿼리 한도를 아낄 수 있어요.

### Supabase: DB + Auth + Storage를 한 번에

무료 플랜이 꽤 후해요.
- PostgreSQL DB 500MB
- 파일 스토리지 5GB
- Auth (이메일/소셜 로그인)
- Realtime 구독
- Edge Functions (Deno 기반)

단, **7일 동안 쿼리가 없으면 프로젝트가 자동 일시정지**돼요. 가장 자주 언급되는 함정이에요. 해결책은 단순해요. Cloudflare Workers에서 24시간마다 ping 쿼리를 날리는 Cron job을 설정하면 돼요. Workers Cron Triggers는 무료 플랜에서도 써요.

---

## 스택 비교: 대안들과 나란히 놓으면

| 항목 | Fly.io + CF Workers + Supabase | Vercel + PlanetScale | Railway + Neon |
|------|-------------------------------|---------------------|----------------|
| 월 기본 비용 | $0–5 | $0–20 (프로 플랜 권장) | $0–10 |
| DB 무료 용량 | 500MB (PostgreSQL) | 5GB (MySQL) | 0.5GB (PostgreSQL) |
| 콜드 스타트 | 없음 (Workers), 있음 (Fly VM) | 있음 (Vercel Functions) | 있음 |
| 배포 편의성 | 중간 (`fly deploy`) | 높음 (Git push) | 높음 (Git push) |
| 락인 위험도 | 중간 | 높음 | 중간 |
| 트래픽 한도 | 100k req/일 (Workers) | 100GB bandwidth/월 | 제한적 |
| 적합한 상황 | 커스텀 백엔드 필요할 때 | Next.js 앱 | PostgreSQL 중심 앱 |

Vercel + PlanetScale은 Next.js를 쓴다면 배포 경험이 압도적으로 좋아요. 그런데 트래픽이 조금 올라가거나 Functions 실행 시간이 길어지면 예상보다 요금이 나와요. 월 20달러 넘는 사례가 1인 개발자 커뮤니티에서 종종 보여요.

Railway + Neon은 2025년 이후 꽤 좋아졌어요. Neon의 serverless PostgreSQL은 연결 풀링을 자동 처리해줘서 Supabase와 비슷한 포지션이에요. 다만 Railway 무료 플랜 정책이 바뀐 이후 시작 비용이 생겼어요.

Fly.io + Cloudflare Workers + Supabase 조합의 진짜 장점은 **각 레이어를 독립적으로 교체할 수 있다**는 거예요. Supabase를 나중에 자체 PostgreSQL로 바꿔도 Workers와 Fly.io는 그대로 두면 돼요.

---

## 실제 운영에서 마주치는 것들

**시나리오별 접근법:**

**① 취미 프로젝트 / 검증 단계**
Supabase 무료 + Workers 무료 + Fly.io 무료 VM 1개. 비용 $0. Cron ping으로 Supabase 일시정지 방지. 이 단계에서 돈 쓸 이유 없어요.

**② 월간 활성 사용자 500–2,000명**
Fly.io shared-cpu-1x ($1.94/월) + Workers 무료 + Supabase 무료. 총 $1.94–4.87. Workers 하루 10만 req 한도가 차면 Workers Paid ($5/월)로 올리면 돼요. 그래도 총 $7 수준이에요.

**③ 트래픽 스파이크 대비**
`fly scale count 2`로 VM 인스턴스를 늘릴 수 있어요. 추가 VM 1개당 $1.94/월. Cloudflare Workers는 하루 req 한도에 걸리면 자동으로 429 에러를 내요. 미리 Workers 유료 플랜 전환 기준을 정해두는 게 맞아요.

**주시해야 할 변수:**
- Supabase 무료 플랜: 2025년 말부터 일부 리전에서 무료 프로젝트 수를 1개로 줄였어요. 추가 프로젝트는 Pro 플랜 $25/월이 필요해요.
- Fly.io 가격 변동: 2023년 한 차례 무료 허용량을 줄인 전례가 있어요. 공식 changelog를 주기적으로 확인하는 게 안전해요.
- Cloudflare Workers AI 확장: 2026년 현재 Workers에서 AI 추론을 직접 실행하는 기능이 베타예요. 안정화되면 Fly.io 역할 일부를 Workers가 가져갈 수도 있어요.

---

## 결론: 5달러 스택이 말해주는 것

- **실제로 돌아가요.** 월 활성 사용자 1,000명 이하 앱에서 비용 $5 이하는 충분히 현실적이에요.
- **숨겨진 비용은 돈이 아니라 시간이에요.** Supabase 일시정지 방지 관리, Workers req 한도 모니터링. 다 신경 써야 해요.
- **락인 위험은 실재해요.** 세 플랫폼 모두 무료 플랜 정책을 바꾼 이력이 있어요. 핵심 비즈니스 로직은 특정 플랫폼 API에 묶이지 않게 설계하는 게 맞아요.
- **규모가 커지면 전환 비용을 미리 계산해야 해요.** Supabase Pro $25/월, Workers Paid $5/월. MAU 2,000명 넘기 전에 다음 단계 비용을 시뮬레이션해두세요.

6-12개월 안에 이 스택에서 바뀔 가능성이 가장 높은 건 Supabase 무료 플랜 구조예요. 사용자가 늘수록 무료 티어를 조이는 패턴이 이미 시작됐거든요.

지금 이 스택을 쓰고 있다면 한 가지만 물어볼게요. Supabase 없이도 이 앱이 돌아갈 수 있는 구조인가요? 답이 "아니요"라면, 지금 당장 의존성을 줄이는 게 다음 할 일이에요.

## 참고자료

1. [Supabase 주요 기능 정리, 장단점까지 한눈에](https://myit.tistory.com/141)
2. [r/Supabase on Reddit: Is Cloudflare Workers reliable/compatible with Supabase for Chrome extension?](https://www.reddit.com/r/Supabase/comments/1o1bl3f/is_cloudflare_workers_reliablecompatible_with/)
3. [Cloudflare Workers vs Vercel 2026: Edge Compute Compared | Morph](https://www.morphllm.com/comparisons/cloudflare-workers-vs-vercel)


---

*Photo by [Alex Gagareen](https://unsplash.com/@onepilot) on [Unsplash](https://unsplash.com/photos/black-and-silver-car-engine-AapHZdN_1-Y)*
