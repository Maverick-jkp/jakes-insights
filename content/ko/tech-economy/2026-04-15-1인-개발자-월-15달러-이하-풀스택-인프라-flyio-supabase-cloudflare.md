---
title: "1인 개발자가 월 15달러로 굴리는 Fly.io·Supabase·Cloudflare 풀스택 인프라 실제 비용 공개"
date: 2026-04-15T20:13:32+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-cloud", "\uac1c\ubc1c\uc790", "15\ub2ec\ub7ec", "\ud480\uc2a4\ud0dd", "Next.js"]
description: "Fly.io·Supabase·Cloudflare 조합으로 월 15달러 이하 풀스택 인프라를 운영하는 1인 개발자의 실제 청구서를 공개합니다. AWS 대비 70% 절감, Fly.io $0~$5 유지 비결을 수치로 확인"
image: "/images/20260415-1인-개발자-월-15달러-이하-풀스택-인프라-flyio.webp"
technologies: ["Next.js", "Node.js", "AWS", "PostgreSQL", "Cloudflare"]
faq:
  - question: "1인 개발자 월 15달러 이하로 풀스택 인프라 운영 가능한가요"
    answer: "1인 개발자 월 15달러 이하 풀스택 인프라는 Fly.io, Supabase, Cloudflare 조합으로 실제 가능하며, 실제 청구서 기준 월 $8~12 수준에서 운영됩니다. 다만 MAU 1만 명 이하, 쓰기 트랜잭션이 적은 서비스에 적합하며, 규모가 커지면 Supabase Pro($25/월) 업그레이드가 필요합니다."
  - question: "Supabase 무료 플랜 7일 자동 정지 막는 방법"
    answer: "Supabase Free 플랜은 7일간 요청이 없으면 프로젝트가 자동 정지되는데, cron job으로 주기적으로 핑을 보내 활성 상태를 유지하는 방법으로 막을 수 있습니다. 근본적으로 해결하려면 월 $25인 Pro 플랜으로 업그레이드해야 합니다."
  - question: "Fly.io 무료 티어 실제 스펙과 한계"
    answer: "Fly.io 무료 티어는 256MB RAM 공유 CPU VM 3개, 월 160GB 아웃바운드, 3GB 영구 스토리지를 제공합니다. 단, 256MB RAM은 Next.js 같은 앱 빌드 시 메모리 부족으로 실패할 수 있어, 많은 개발자가 월 $3.19인 512MB 플랜으로 업그레이드합니다."
  - question: "Fly.io Supabase Cloudflare 조합 vs AWS 비용 비교"
    answer: "1인 개발자 월 15달러 이하 풀스택 인프라로 주목받는 Fly.io, Supabase, Cloudflare 조합의 실제 청구서는 월 $5~12 수준인 반면, 동급 규모의 AWS EC2+RDS+CloudFront 기본 구성은 월 $60~80이 청구됩니다. 즉 AWS 대비 약 70~85% 비용 절감이 가능합니다."
  - question: "Cloudflare Workers 무료 플랜 한도 초과하면 얼마"
    answer: "Cloudflare Workers 무료 플랜은 하루 10만 요청까지 제공되며, 한도를 초과하거나 안정적인 운영이 필요하면 월 $5 유료 플랜으로 무제한 요청 처리가 가능합니다. CDN 대역폭은 유료 플랜에서도 별도 과금이 없어 트래픽 비용 예측이 쉽습니다."
aliases:
  - "/tech/2026-04-15-1인-개발자-월-15달러-이하-풀스택-인프라-flyio-supabase-cloudflare/"

---

월 15달러. 도메인 하나 사는 값이에요. 그런데 이 돈으로 DB·서버·CDN을 모두 굴리는 1인 개발자들이 실제로 있어요.

과거엔 불가능했어요. AWS EC2 하나 띄우면 최소 월 20~30달러, RDS 붙이면 50달러가 넘었죠. 사이드 프로젝트는 늘 "돈 안 되면 끄자"는 불안함을 안고 있었어요.

그런데 Fly.io, Supabase, Cloudflare가 무료 티어와 저가 플랜을 공격적으로 키우면서 상황이 달라졌어요. 세 도구를 조합하면 월 15달러 이하 풀스택 인프라가 가능하고 — 이건 이론이 아니라 실제 청구서 기반 이야기예요.

---

> **핵심 요약**
> - Fly.io 무료 티어는 256MB RAM VM 3개와 월 160GB 아웃바운드를 제공하며, 실비용은 $0~$5 사이로 유지된다.
> - Supabase Free 플랜은 프로젝트 2개, 500MB DB, 5GB 스토리지를 제공하지만 7일 비활성 시 프로젝트가 자동 정지되는 운영 리스크가 있다.
> - Cloudflare Workers는 하루 10만 요청까지 무료이며, 월 $5 플랜으로 무제한 요청 처리가 가능해 CDN+엣지 기능을 가장 저렴하게 붙일 수 있다.
> - 세 서비스를 조합하면 소규모 SaaS 기준 월 청구액이 $5~$12 사이로 수렴하며, AWS 기본 스택 대비 70~80% 비용 절감이 가능하다.
> - 다만 이 조합은 MAU 1만 명 이하, 쓰기 트랜잭션이 많지 않은 서비스에 적합하며, 그 이상이 되면 Supabase Pro($25/월) 업그레이드가 불가피하다.

---

## 왜 이 조합이 주목받기 시작했나

2022년 11월, Heroku가 무료 플랜을 폐지했어요. 수많은 사이드 프로젝트가 한꺼번에 죽었죠. 이 공백을 메우려는 경쟁이 시작됐어요.

Fly.io는 2020년 컨테이너 기반 엣지 배포로 등장했어요. Supabase는 Firebase 오픈소스 대안으로 2020년 론칭했고, 현재 40만 개 이상의 프로젝트가 올라가 있어요(Supabase 공식 블로그, 2026년 1월 기준). Cloudflare는 Workers와 Pages로 엣지 컴퓨팅 시장에 자리를 잡았고요.

세 서비스가 공통적으로 선택한 방향이 있어요. "무료 티어는 충분히, 유료 전환 문턱은 낮게." 이 전략 덕분에 개발자들이 이 도구들을 합쳐서 쓰기 시작했어요.

---

## 실제 청구서 분석: 각 서비스의 진짜 비용

### Fly.io — 컨테이너 서버, 실제로 얼마 나오나

Fly.io 무료 티어는 생각보다 넉넉해요.

- **공유 CPU VM 3개** (각 256MB RAM)
- **월 160GB 아웃바운드** (2025년 정책 변경 후)
- **3GB 영구 스토리지**
- **PostgreSQL 소형 DB 3개**

문제는 256MB RAM이에요. Next.js 앱을 올리면 빌드 시 메모리 부족으로 죽는 경우가 있어요. 많은 개발자가 512MB RAM으로 업그레이드하는데, 이때부터 비용이 발생해요.

512MB shared-cpu-1x 기준 월 약 **$3.19**. 영구 볼륨이 필요하면 3GB당 $0.15를 더 내요. 일반적인 Node.js API 서버 하나를 굴리면 **월 $3~5** 범위에서 청구가 나와요.

### Supabase — 무료가 진짜 무료인가

Supabase Free 플랜 스펙:

- 프로젝트 2개
- **500MB DB 용량**
- **5GB 파일 스토리지**
- **월 5GB 대역폭**
- Auth 무제한 (MAU 50,000까지)

함정이 하나 있어요. **7일 동안 요청이 없으면 프로젝트가 자동으로 정지돼요.** 사이드 프로젝트를 잠깐 손 놓으면 DB가 꺼지는 거예요. 막으려면 cron job으로 핑을 보내거나, Pro 플랜($25/월)으로 올려야 해요.

500MB DB 용량도 생각보다 빨리 차요. 사용자 로그나 이미지 메타데이터를 DB에 저장하면 6개월 안에 한계에 도달하는 경우가 많아요. Free 플랜을 최대한 유지하고 싶다면 **읽기 중심, 소규모, 활성화 상태 유지**가 핵심이에요.

### Cloudflare — 가장 가성비 좋은 레이어

Cloudflare의 무료 티어는 인심이 제일 좋아요.

- **Workers**: 하루 10만 요청 무료
- **Pages**: 빌드 월 500회, 정적 사이트 무제한
- **CDN**: 대역폭 과금 없음
- **R2 스토리지**: 월 10GB 무료, 이후 $0.015/GB

유료 플랜은 월 $5인데, 이걸 내면 Workers가 무제한 요청으로 바뀌어요. 하루 방문자 수백 명 수준에선 무료로 충분하고, 성장해도 $5면 해결돼요.

---

## 세 서비스 조합 비용 비교

| 구성 | 월 비용 | 적합한 규모 | 주요 한계 |
|------|---------|-----------|---------|
| Fly.io Free + Supabase Free + Cloudflare Free | **$0** | MAU 1,000 이하 | 7일 비활성 정지, 256MB RAM |
| Fly.io 512MB + Supabase Free + Cloudflare Free | **~$3~5** | MAU 3,000 이하 | Supabase 정지 리스크 유지 |
| Fly.io 512MB + Supabase Free + Cloudflare $5 | **~$8~10** | MAU 5,000 이하 | Supabase 500MB 한계 |
| Fly.io 512MB + Supabase Pro + Cloudflare $5 | **~$33~35** | MAU 10,000 이하 | 비용 점프 구간 |
| AWS EC2 t3.small + RDS + CloudFront 기본 | **~$60~80** | 동급 규모 | 설정 복잡, 비용 예측 어려움 |

**이 조합의 핵심 장점**: Supabase Free 상태를 유지하면서 Fly.io와 Cloudflare만 유료로 쓰면 월 $8~10으로 꽤 안정적인 스택이 완성돼요. AWS 기본 구성 대비 약 85% 저렴한 셈이에요.

### 비용이 폭발하는 구간

Supabase Free에서 Pro로 넘어가는 순간 비용이 $25 뛰어요. 이게 이 조합의 가장 큰 단절 구간이에요. 그래서 많은 1인 개발자들이 **Fly.io에 직접 PostgreSQL을 올리는** 방식으로 이 비용 점프를 피하려 해요. DB 비용이 월 $1~2 수준으로 유지되거든요. 단, 백업과 HA(고가용성) 구성은 직접 챙겨야 하는 트레이드오프가 있어요.

---

## 이 조합이 맞는 사람 vs 안 맞는 사람

**잘 맞는 경우:**
- 사이드 프로젝트, MVP 테스트, 포트폴리오 앱
- 읽기 비중이 높고 DB 쓰기가 적은 서비스 (블로그, 링크 모음, 소규모 디렉토리)
- MAU 5,000 이하, 트래픽이 예측 가능한 서비스
- 인프라에 시간을 덜 쓰고 싶은 1인 개발자

**안 맞는 경우:**
- 실시간 채팅, 게임처럼 초당 DB 쓰기가 많은 서비스
- 데이터가 500MB를 빠르게 넘을 것으로 예상되는 경우
- 99.9% 이상 SLA가 필요한 서비스 (Fly.io는 엔터프라이즈 SLA 미제공)
- 권한 관리, 감사 로그가 필요한 팀 개발 환경

Railway나 Render 같은 대안도 있어요. Railway는 Fly.io보다 설정이 단순하고 월 $5 시작 플랜이 있어요. 그런데 Fly.io의 엣지 배포(서울, 도쿄 리전 모두 지원)와 세밀한 가격 조절이 장점이라, 한국 사용자를 대상으로 하는 서비스엔 Fly.io가 더 나을 때가 많아요.

---

## 앞으로 6~12개월, 어떻게 변할까

세 서비스 모두 무료 티어 경쟁을 이어갈 가능성이 높아요. Supabase는 무료 플랜의 비활성 정지 정책을 완화하거나 없앤다는 얘기가 커뮤니티에서 돌고 있어요. 실현되면 이 조합의 가장 큰 리스크가 사라지는 거예요.

Cloudflare는 R2 스토리지를 계속 확장 중이에요. S3 대체 용도로 R2를 쓰면 스토리지 비용을 추가로 줄일 수 있어요. Fly.io는 데이터베이스 제품 강화를 준비 중이어서, 향후엔 Supabase 없이도 Fly.io 하나로 DB까지 해결하는 구성이 더 매끄러워질 거예요.

정리하면:

- **$0~$5**: Fly.io Free + Supabase Free + Cloudflare Free로 가능, 단 운영 리스크 존재
- **$8~$12**: 가장 현실적인 "월 15달러 이하 풀스택" 구간
- **$33~$35**: 프로덕션급으로 올라가는 첫 번째 비용 레벨
- **상한선**: MAU 5,000~10,000이 이 조합의 현실적 한계

지금 사이드 프로젝트를 굴리고 있거나 MVP를 준비 중이라면, 이 세 도구 조합은 가장 빠르게 배포하고 가장 오래 버틸 수 있는 방법이에요.

한 가지만 미리 생각해두세요. 프로젝트가 MAU 1만 명을 넘는 날이 오면 — 그때 이 조합을 유지할 건가요, 아니면 다른 스택으로 갈아탈 준비가 돼 있나요? 그 결정 시점을 미리 정해두는 게, 실제로 성장했을 때 당황하지 않는 유일한 방법이에요.

## 참고자료

1. [풀스택 개발자 1인 외주, 정말 더 저렴할까? - 제로백데브](https://zero100dev.tistory.com/entry/%ED%92%80%EC%8A%A4%ED%83%9D-%EA%B0%9C%EB%B0%9C%EC%9E%90-1%EC%9D%B8-%EC%99%B8%EC%A3%BC-%EC%A0%95%EB%A7%90-%EB%8D%94-%EC%A0%80%EB%A0%B4%ED%95%A0%EA%B9%8C)
2. [1인 개발자의 다수 프로젝트 운영을 위한 Supab... - Inflearn | Community Q&A](https://www.inflearn.com/en/community/questions/1780024/1%EC%9D%B8-%EA%B0%9C%EB%B0%9C%EC%9E%90%EC%9D%98-%EB%8B%A4%EC%88%98-%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8-%EC%9A%B4%EC%98%81%EC%9D%84-%EC%9C%84%ED%95%9C-supabase-%EB%B9%84%EC%9A%A9-%EC%B5%9C%EC%A0%81%ED%99%94-%EC%A0%84%EB%9E%B5-db-%ED%86%B5%ED%95%A9-%EC%97%90-%EB%8C%80%ED%95%B4-%EC%A1%B0%EC%96%B8%EC%9D%84-%EA%B5%AC%ED%95%A9%EB%8B%88%EB%8B%A4)
3. [AI 시대, 오픈소스 백엔드의 강자 Supabase](https://brunch.co.kr/@ywkim36/188)


---

*Photo by [Microsoft Copilot](https://unsplash.com/@microsoftcopilot) on [Unsplash](https://unsplash.com/photos/woman-typing-on-laptop-at-wooden-table-with-breakfast-ghVMdPN33vM)*
