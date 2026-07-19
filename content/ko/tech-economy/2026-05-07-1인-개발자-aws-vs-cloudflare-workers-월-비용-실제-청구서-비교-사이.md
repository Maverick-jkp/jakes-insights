---
title: "1인 개발자 AWS vs Cloudflare Workers 월 비용, 실제 청구서로 비교해봤습니다"
date: 2026-05-07T20:58:59+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-cloud", "\uac1c\ubc1c\uc790", "aws", "cloudflare", "Python"]
description: "1인 개발자 사이드 프로젝트 실제 청구서 비교. Cloudflare Workers 하루 10만 건 무료 vs AWS Lambda 월 100만 건 무료지만 API Gateway·CloudWatch 숨은 비용까지 계산하면 결과가 달라집니다."
image: "/images/20260507-1인-개발자-aws-vs-cloudflare-worke.webp"
technologies: ["Python", "Node.js", "AWS", "REST API", "Cloudflare"]
faq:
  - question: "1인 개발자 사이드 프로젝트 AWS vs Cloudflare Workers 월 비용 실제로 얼마나 차이나요"
    answer: "1인 개발자 AWS vs Cloudflare Workers 월 비용 실제 청구서 비교 기준으로, 동일한 사이드 프로젝트(월 50만 건 API 요청, 간단한 CRUD)를 운영할 때 AWS는 월 $20~25, Cloudflare Workers는 무료~$5 수준이에요. AWS는 Lambda 자체는 무료 구간이어도 API Gateway, CloudWatch, RDS 등 주변 서비스 비용이 누적되기 때문에 실제 청구서가 훨씬 높게 나오는 구조예요."
  - question: "AWS Lambda 프리티어 실제로 무료로 쓸 수 있나요"
    answer: "Lambda 자체는 월 100만 건 무료 호출을 제공하지만, 단독으로는 아무것도 할 수 없어서 API Gateway, CloudWatch Logs, 데이터 전송 비용이 함께 발생해요. 트래픽이 거의 없어도 이 주변 서비스들만으로 월 $10~15가 쉽게 청구되기 때문에 '무료'라고 체감하기 어려운 경우가 많아요."
  - question: "Cloudflare Workers 무료 플랜 한도 얼마나 되나요"
    answer: "Cloudflare Workers 무료 플랜은 하루 10만 건 요청을 제공해, 단순 계산으로 월 300만 건까지 무료로 처리할 수 있어요. 초기 사이드 프로젝트 트래픽 대부분을 커버할 수 있는 수준이며, 유료 플랜으로 전환해도 월 $5 고정에 1,000만 건 요청이 포함돼요."
  - question: "Cloudflare Workers Cold Start 없다는데 사실인가요"
    answer: "Cloudflare Workers는 V8 Isolate 기반으로 동작해 Cold Start가 사실상 0ms예요. 새 프로세스를 시작하는 방식이 아니라 기존 V8 엔진 위에 스크립트를 얹는 구조여서, AWS Lambda의 평균 200~400ms Cold Start와 비교하면 응답 속도 면에서 확실한 차이가 있어요."
  - question: "사이드 프로젝트에 Cloudflare Workers 쓰면 안 되는 경우는 언제인가요"
    answer: "1인 개발자 AWS vs Cloudflare Workers 월 비용 실제 청구서 비교 관점에서 비용은 Workers가 유리하지만, VPC·RDS 연동이 필요하거나 PDF 생성·이미지 리사이징처럼 CPU를 많이 쓰는 작업엔 적합하지 않아요. Workers는 CPU 시간이 유료 플랜 기준 30ms로 제한되고 Node.js 내장 모듈도 지원하지 않아, 복잡한 백엔드 로직이 필요한 경우엔 AWS가 불가피해요."
aliases:
  - "/tech/2026-05-07-1인-개발자-aws-vs-cloudflare-workers-월-비용-실제-청구서-비교-사이/"

---

사이드 프로젝트 런칭하고 첫 달 AWS 청구서 열었다가 멈칫한 적 있죠? 예상의 세 배 숫자가 눈에 들어오는 그 순간. 트래픽은 거의 없는데 고정비는 착실히 쌓이는 구조, 꽤 낯설지 않아요.

지금 1인 개발자 사이에서 AWS vs Cloudflare Workers 월 비용 비교가 다시 뜨거운 이유가 여기 있어요. 실제 청구서 기준으로 어느 쪽이 진짜 이득인지 따져볼게요.

> **핵심 요약**
> - Cloudflare Workers 무료 플랜은 하루 10만 건 요청을 무료로 처리하며, 1인 개발자 사이드 프로젝트 초기 단계 대부분을 커버한다.
> - AWS Lambda는 월 100만 건 무료 호출을 제공하지만, API Gateway·CloudWatch·NAT Gateway 등 주변 서비스 비용이 실제 청구서를 끌어올리는 주범이다.
> - 동일한 사이드 프로젝트(API 서버 + 간단한 CRUD) 기준, Cloudflare Workers 유료 플랜(\$5/월)은 AWS 최소 구성(\$15~30/월) 대비 월 비용이 절반 이하인 경우가 많다.
> - Cold Start와 지역 엣지 실행 측면에서 Cloudflare Workers가 유리하지만, VPC 연동·RDS 접근·복잡한 런타임이 필요한 경우엔 AWS가 불가피하다.

---

## AWS 프리 티어의 함정: "무료"의 실제 의미

AWS는 Lambda에 월 100만 건 무료 호출과 40만 GB-초 컴퓨팅을 제공해요. 숫자만 보면 사이드 프로젝트엔 넘치죠. 그런데 Lambda 단독으론 아무것도 못 해요.

실제 최소 구성을 보면 이렇게 돼요:

- **API Gateway**: 월 100만 요청 이후부터 \$3.50/백만 건 과금
- **CloudWatch Logs**: 기본 로그 저장만 해도 GB당 \$0.50
- **S3**: 버킷 유지 비용 + 요청 건수 과금
- **데이터 전송**: 월 1GB 이후부터 \$0.09/GB

Lambda 자체는 무료 구간 안에 있어도, API Gateway와 CloudWatch만으로 월 \$10~15가 훌쩍 넘어가는 구조예요. 트래픽이 거의 없어도 고정비처럼 느껴지는 이유가 바로 이 "주변 서비스" 비용이에요.

---

## Cloudflare Workers 실제 청구서 구조

Cloudflare Workers 무료 플랜은 **하루 10만 건 요청, 10ms CPU 시간 제한**이에요. 단순 계산으로 월 300만 건까지 무료인 셈이죠.

유료 전환은 Workers Paid 플랜 기준 **\$5/월 고정 + 월 1,000만 건 요청 포함**이에요. 초과분은 백만 건당 \$0.30이고요.

포인트는 **별도 API Gateway가 없다**는 거예요. Workers 자체가 엣지에서 HTTP 요청을 직접 받아 처리해요. KV 스토리지, R2 오브젝트 스토리지, D1 SQLite 데이터베이스도 Workers와 긴밀하게 붙어 있어서 추가 네트워크 비용이 발생하지 않아요.

실제로 간단한 REST API 사이드 프로젝트를 Workers + D1으로 구성하면 유료 플랜 기준 **월 \$5~8 수준**에서 운영이 가능해요. AWS 최소 구성이 동일 트래픽에서 \$15~30 나오는 것과 비교하면 체감 차이가 크죠.

---

## 실제 비용 비교: 시나리오별 청구서

같은 사이드 프로젝트를 두 플랫폼에서 돌린다고 가정하고 비교해 볼게요.

**시나리오: 월 50만 건 API 요청, 간단한 CRUD, SQLite 수준 DB, 로그 기본 설정**

| 항목 | AWS Lambda 구성 | Cloudflare Workers 구성 |
|------|----------------|------------------------|
| 실행 비용 | 무료 (100만 건 이내) | 무료 (Free 플랜) |
| API 진입점 | API Gateway: ~\$1.75 | 포함 (별도 없음) |
| DB 연결 | RDS t3.micro: ~\$15/월 | D1: 무료 (5GB 이내) |
| 로그/모니터링 | CloudWatch: ~\$3~5 | 기본 포함 |
| 데이터 전송 | ~\$1~3 | 무료 (엣지 처리) |
| **월 합계 (예상)** | **\$20~25** | **\$0 (Free) / \$5 (Paid)** |
| Cold Start | 100~500ms | 0ms (V8 Isolate) |
| 실행 환경 | Node.js, Python 등 풀 런타임 | V8 기반 (제한된 API) |
| VPC/RDS 연동 | 가능 | 불가 |
| 복잡한 라이브러리 | 가능 | 일부 제한 |
| **추천 대상** | 복잡한 백엔드, DB 연동 필요 시 | 간단한 API, 엣지 처리 중심 |

트래픽이 적을 때는 Cloudflare Workers가 압도적으로 유리하고, 복잡성이 올라가면 AWS가 불가피해져요.

---

## Cold Start와 실행 제약: 실제로 얼마나 다를까

AWS Lambda의 Cold Start는 Node.js 런타임 기준 평균 200~400ms예요. VPC에 연결하면 더 올라가고요. 사용자 입장에선 눈에 띄는 지연이에요.

Cloudflare Workers는 V8 Isolate 기반이라 Cold Start가 사실상 0ms예요. 프로세스를 새로 시작하는 게 아니라 기존 V8 엔진 위에 스크립트를 얹는 방식이거든요. 응답 속도 면에서는 Workers가 확실히 앞서요.

그런데 Workers의 실행 제약도 명확해요:

- **CPU 시간 제한**: 무료 플랜 10ms, 유료 30ms
- **메모리 상한**: 128MB
- **Node.js 내장 모듈 미지원**: `fs`, `net` 등 사용 불가
- **장시간 실행 불가**: 배치 처리나 무거운 연산엔 부적합

PDF 생성, 이미지 리사이징, ML 추론처럼 CPU를 많이 쓰는 작업엔 Workers가 맞지 않아요. 이 점은 분명히 알고 시작해야 해요.

---

## 어떤 상황에서 뭘 골라야 할까

**Cloudflare Workers가 맞는 경우:**

- 단순 REST API, 인증 미들웨어, 리다이렉트 처리
- 초기 사이드 프로젝트 (트래픽 예측 불가 시 \$0 시작 가능)
- 글로벌 엣지 배포가 필요한 서비스
- D1, KV, R2로 해결 가능한 데이터 구조

**AWS Lambda가 맞는 경우:**

- RDS, ElastiCache 등 VPC 내 서비스 연동
- ffmpeg, puppeteer처럼 무거운 런타임 의존성
- 장시간 실행 필요 (최대 15분)
- 기존 AWS 인프라와 연동된 프로젝트

사이드 프로젝트 초기엔 Cloudflare Workers로 시작하고, 복잡도가 올라갈 때 AWS로 전환하는 게 비용 면에서 가장 합리적인 흐름이에요. 실제로 많은 1인 개발자들이 선택하는 경로이기도 하고요.

---

## 2026년 하반기, 뭘 주시해야 할까

Cloudflare는 2026년 초 D1 데이터베이스 정식 GA와 함께 무료 티어 용량을 5GB로 확대했어요. Workers AI도 무료 추론 크레딧을 늘리는 방향으로 가고 있고요. 이 흐름이 계속된다면 간단한 사이드 프로젝트는 Workers 생태계 안에서 거의 무료로 운영하는 게 가능해질 거예요.

AWS는 Lambda SnapStart를 Node.js로 확장하는 로드맵을 발표했고, Graviton 기반 Lambda로 비용 절감 옵션을 넓히고 있어요. 그래도 API Gateway 과금 구조는 아직 바뀌지 않았어요.

**핵심 정리:**

- 사이드 프로젝트 초기: Cloudflare Workers Free → 월 \$0
- 트래픽 증가 후: Workers Paid \$5/월 vs AWS \$20~25/월
- 복잡한 백엔드 필요 시: AWS Lambda가 여전히 현실적 선택

"어떤 플랫폼이 더 좋냐"보다 "지금 내 프로젝트 복잡도가 어디냐"가 답을 결정해요. 지금 만들고 있는 사이드 프로젝트, Workers로 시작해도 충분한 수준인지 한번 점검해보는 게 어떨까요?

## 참고자료

1. [클라우드플레어 워커(cloudflare workers)와 AWS 람다(AWS Lambda) 비교 | marinesnow34](https://marinesnow34.github.io/2024/04/25/worker1/)
2. [aws...? cloudflare! 그는 신인가?](https://velog.io/@doublezeroman/aws-cloudflare)
3. [Pricing · Cloudflare Workers docs](https://developers.cloudflare.com/workers/platform/pricing/)


---

*Photo by [Christian Palazzolo](https://unsplash.com/@carstocamera) on [Unsplash](https://unsplash.com/photos/race-car-with-cartoon-graphics-and-aws-logo-_Shiom3n3ak)*
