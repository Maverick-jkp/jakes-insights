---
title: "Supabase 무료 플랜 한계와 Row Limit 초과 대응 방법 실제 운영 후기"
date: 2026-05-02T20:13:26+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-web", "supabase", "\uc11c\ube44\uc2a4", "row", "PostgreSQL"]
description: "Supabase 무료 플랜 7일 비활성 시 자동 일시정지, 콜드 스타트 30초, API 월 50만 건 한계를 실제 운영하며 겪은 문제와 Pro 플랜 전환 기준을 정리했습니다."
image: "/images/20260502-supabase-무료-플랜-한계-실제-서비스-운영-후기.webp"
technologies: ["PostgreSQL", "GitHub Actions", "Cloudflare", "Supabase", "Firebase"]
faq:
  - question: "Supabase 무료 플랜 row limit 얼마나 되나요"
    answer: "Supabase 무료 플랜은 공식적으로 Row 수 자체에 상한선을 두지 않지만, 데이터베이스 용량이 500MB로 제한되어 있어 실질적인 병목이 됩니다. 예를 들어 Row 하나가 평균 1KB라면 50만 건만 쌓여도 이미 500MB를 소진하게 되어, Supabase 무료 플랜 한계 실제 서비스 운영 후기에서 가장 많이 언급되는 패턴입니다."
  - question: "Supabase 무료 플랜 프로젝트 자동 정지 해결 방법"
    answer: "Supabase 무료 플랜은 7일 이상 트래픽이 없으면 프로젝트를 자동으로 일시정지시키며, 이때 사용자는 빈 화면이나 서버 오류를 경험하게 됩니다. GitHub Actions를 활용해 매 5~6일마다 Supabase API에 자동 GET 요청(핑)을 보내는 것이 가장 많이 사용되는 대응 방법으로, 실제로 이 방법으로 3개월 이상 정지 없이 무료 플랜을 유지한 사례가 있습니다."
  - question: "Supabase 무료 플랜 500MB 초과했을 때 대처법"
    answer: "Supabase 무료 플랜 한계 실제 서비스 운영 후기 Row Limit 초과 대응 방법으로 가장 효과적인 것은 pg_cron 확장을 활용한 오래된 데이터 자동 삭제입니다. 예를 들어 30일 이상 된 로그 Row를 매일 자정에 삭제하는 Job을 설정하거나, 이미지·파일을 Supabase Storage 대신 Cloudflare R2(무료 10GB/월)로 분산하면 용량 소진 속도를 크게 줄일 수 있습니다."
  - question: "Supabase 무료 플랜 vs Firebase 무료 어떤 게 더 나은가요"
    answer: "Supabase 무료 플랜은 PostgreSQL 기반 관계형 구조와 월 50만 건 API 요청을 제공하는 반면, Firebase Spark는 비활성 정지가 없고 Firestore 1GB를 제공합니다. 다만 Supabase는 7일 비활성 정지 정책과 용량 관리 등 운영 부담이 있어, 실제 서비스 운영 측면에서는 Firebase Spark보다 관리 비용이 더 높다는 평가가 많습니다."
  - question: "Supabase Pro 플랜 업그레이드 언제 해야 하나요"
    answer: "서비스에 실제 사용자가 생겨 7일 이상 연속 운영이 필요하거나, 데이터베이스 용량이 500MB에 근접하기 시작하면 월 $25의 Pro 플랜 전환을 고려해야 합니다. Pro 플랜은 8GB 데이터베이스와 비활성 정지 없음, 무제한 API 요청을 제공하므로 사이드 프로젝트가 실제 서비스로 전환되는 시점에 현실적인 선택지입니다."
aliases:
  - "/tech/2026-05-02-supabase-무료-플랜-한계-실제-서비스-운영-후기-row-limit-초과-대응-방법/"

---

프로젝트를 배포하고 딱 3주 뒤, 대시보드에 이런 알림이 떴다고 상상해 보세요. "Your project has been paused." 데이터베이스가 통째로 잠겨버린 거예요. 사용자가 접속하면 빈 화면만 보이고, 원인은 단 하나 — Supabase 무료 플랜의 비활성 정책이었어요. 2026년 현재도 수많은 사이드 프로젝트가 조용히 죽는 이유 중 하나예요.

> **핵심 요약**
> - Supabase 무료 플랜은 7일 이상 트래픽이 없으면 프로젝트를 자동 일시정지하며, 복구 시 약 20~30초의 콜드 스타트가 발생해요.
> - 무료 플랜의 Row 수 제한은 공식적으로 명시되지 않지만, Storage 500MB와 월 API 요청 50만 건이 실질적인 병목이에요.
> - 월 $25의 Pro 플랜은 8GB 데이터베이스와 일시정지 없음을 제공해서, 실제 서비스 운영엔 훨씬 현실적인 선택지예요.
> - 무료 플랜에서 버티려면 GitHub Actions 자동 핑, Edge Function 경량화, 오래된 Row 주기적 정리가 핵심 전략이에요.
> - 2026년 기준 Supabase는 Firebase 대비 PostgreSQL 기반 관계형 구조를 제공하지만, 무료 티어 운영엔 Firebase Spark 플랜보다 관리 비용이 훨씬 더 들어요.

---

## Supabase 무료 플랜, 실제로 뭘 제공하나요?

Supabase는 오픈소스 Firebase 대안으로 출발했어요. PostgreSQL을 기반으로 인증, 스토리지, 실시간 구독, Edge Function까지 한 번에 묶어서 제공하죠. "백엔드를 코드 없이"라는 약속이 사이드 프로젝터들에게 너무나 매력적이었거든요.

그런데 무료 플랜 실제 스펙을 보면 이야기가 달라져요. 2026년 현재 공식 문서 기준으로 정리하면 이래요:

- **데이터베이스**: 500MB (shared 인프라)
- **스토리지**: 1GB
- **월간 API 요청**: 50만 건
- **Edge Functions 호출**: 월 50만 건
- **대역폭**: 2GB/월
- **프로젝트 수**: 최대 2개
- **비활성 정지**: 7일 이상 요청 없으면 자동 일시정지

여기서 가장 자주 나오는 오해가 있어요. "Row Limit이 없다고 들었는데요?" 맞아요, Supabase는 공식적으로 Row 수 자체에 상한선을 두지 않아요. 문제는 500MB 데이터베이스 용량이에요. Row가 쌓이면 결국 용량이 먼저 차버려요. 사용자 활동 로그 테이블에서 Row 하나가 평균 1KB라면, 50만 건이 쌓이면 이미 500MB예요. 운영 후기에서 가장 많이 등장하는 패턴이 바로 이거예요.

비활성 정지 정책은 또 다른 함정이에요. 7일간 아무도 서비스를 안 쓰면 프로젝트가 잠겨요. 잠자는 프로젝트를 깨우려면 대시보드에서 수동으로 버튼을 눌러야 하고, 그러면 사용자는 이미 "서버 오류"를 경험한 뒤예요.

---

## 무료 플랜 한계에 부딪히는 세 가지 시나리오

### 시나리오 1: 비활성 정지와 콜드 스타트

가장 빈번하게 발생하는 문제예요. 주말용 커뮤니티 앱이나 사이드 프로젝트는 평일엔 트래픽이 거의 없어요. 7일이 지나면 프로젝트가 자동으로 일시정지되고, 다음 사용자가 접속하면 데이터베이스 연결 자체가 실패해요.

해결 방법은 두 가지예요. 하나는 GitHub Actions를 써서 매 5~6일마다 Supabase API에 자동으로 GET 요청을 보내는 거예요. 핑 역할을 하는 거죠. lookfortaste.com에서 공유된 사례에 따르면, 이 방법으로 무료 플랜 프로젝트를 3개월 이상 정지 없이 유지했어요. 또 다른 방법은 Supabase CLI를 쓰는 건데, 로컬 개발 환경이 갖춰진 경우에 유용해요.

### 시나리오 2: 500MB 한도 초과와 Row 관리

데이터가 계속 쌓이는 서비스라면 결국 용량 한도에 걸려요. 가장 현실적인 대응은 **데이터 보존 정책**을 미리 설계하는 거예요.

- 30일 이상 된 로그 데이터는 자동 삭제 (PostgreSQL의 `pg_cron` 확장 사용)
- JSON 컬럼을 무분별하게 쓰지 않기 (용량을 예상보다 훨씬 많이 잡아먹어요)
- 이미지나 파일은 Supabase Storage 대신 Cloudflare R2(무료 10GB/월)로 분산

`pg_cron`은 Supabase 대시보드 Extensions 탭에서 바로 켤 수 있어요. 예를 들어 매일 자정에 30일 이상 된 `activity_logs` Row를 지우는 Job은 이렇게 설정해요:

```sql
SELECT cron.schedule(
  'cleanup-old-logs',
  '0 0 * * *',
  $$DELETE FROM activity_logs WHERE created_at < NOW() - INTERVAL '30 days'$$
);
```

### 시나리오 3: API 요청 소진

월 50만 건이 많아 보이지만, 실시간 구독이나 Polling 방식을 쓰면 생각보다 빨리 닳아요. 사용자 100명이 앱을 30분씩 쓰면서 10초마다 새 데이터를 가져온다면, 하루에만 1만 8천 건이에요. 한 달이면 54만 건, 이미 한도 초과예요.

대응 방법은 Supabase Realtime 구독을 무분별하게 쓰지 않는 거예요. 변경이 잦지 않은 데이터엔 Polling 대신 캐시를 두거나, SWR 같은 라이브러리로 요청 빈도를 조절하세요.

---

## Supabase 무료 vs Pro vs Firebase 비교

운영 후기를 모아보면 가장 많이 나오는 질문이 "그냥 Pro 가야 하나요?"예요.

| 항목 | Supabase 무료 | Supabase Pro ($25/월) | Firebase Spark (무료) |
|---|---|---|---|
| 데이터베이스 용량 | 500MB | 8GB | 1GB (Firestore) |
| Row/문서 수 제한 | 용량 한도 내 무제한 | 무제한 | 무제한 |
| 비활성 정지 | 7일 | 없음 | 없음 |
| 월간 API 요청 | 50만 건 | 무제한 | 5만 건/일 |
| 스토리지 | 1GB | 100GB | 5GB |
| 대역폭 | 2GB | 250GB | 10GB/월 |
| 백업 | 없음 | 일별 자동 백업 | 없음 |
| 가격 | 무료 | $25/월 | 무료 |

Firebase Spark 플랜은 비활성 정지가 없고, Firestore 1GB 용량도 문서 크기를 잘 관리하면 꽤 오래 버텨요. 반면 Supabase의 강점은 PostgreSQL을 그대로 쓸 수 있다는 거예요. 복잡한 JOIN 쿼리나 pgvector로 벡터 검색을 붙이는 경우엔 Supabase가 압도적으로 유리해요.

그래서 결론은 이래요. **실제 사용자가 있는 서비스라면 Supabase 무료 플랜은 스테이징 환경으로만 써야 해요.** 트래픽이 예측 불가능하고, 사용자 경험에 데이터베이스 정지가 그대로 노출되거든요.

---

## 무료 플랜에서 최대한 버티는 현실적 전략

**시나리오별 권장 방향을 정리하면 이래요:**

**사이드 프로젝트 / MVP 단계**:
- GitHub Actions로 5일마다 자동 핑 설정 (비활성 정지 방지)
- `pg_cron`으로 오래된 데이터 자동 정리
- 이미지/파일은 Cloudflare R2로 분산
- Realtime 구독 최소화, SWR로 요청 최적화

**사용자 100명 이상 / 데이터 증가세**:
- Supabase Pro 전환이 현실적 ($25/월)
- 또는 Self-hosted Supabase (Railway나 Fly.io에 직접 배포) — 인프라 관리 부담이 생기지만 비용은 줄어요

**다음 6개월을 본다면:**
Supabase는 2025년 GA(정식 출시) 이후 엔터프라이즈 기능에 집중하고 있어요. 무료 티어 혜택이 줄어들 가능성을 배제할 수 없어요. 실제로 2024년 말에 무료 플랜 프로젝트 수를 두 개로 제한했던 것처럼요. 지금 무료로 굴리는 프로젝트가 있다면, Pro 전환 기준(사용자 수, 월간 요청 수, DB 용량)을 미리 정해두는 게 나아요.

---

## 지금 당장 체크해야 할 것들

Supabase 무료 플랜 한계를 운영 중에 마주치면 대처할 시간이 없어요. 사용자가 이미 에러를 보고 있을 테니까요.

지금 Supabase 프로젝트가 있다면 이것만 확인해 보세요:

- **대시보드 → Database → Space Used**: 얼마나 찼는지 확인
- **대시보드 → Reports → API**: 이번 달 요청 몇 건인지 확인
- **비활성 정지 방지 워크플로우**: 설정되어 있는지 확인

사실 Row 한도 대응은 복잡하지 않아요. 데이터가 쌓이는 속도를 이해하고, 정리 정책을 자동화하고, 용량 임계점에 도달하기 전에 플랜 전환 여부를 결정하면 돼요.

Supabase를 처음 쓸 때 무료 플랜으로 시작하는 건 맞아요. 문제는 "언제 벗어날지"를 미리 생각하지 않고 시작하는 거예요. 여러분의 프로젝트는 지금 몇 % 찼나요?

## 참고자료

1. [Supabase 무료 플랜, 2주면 잠든다? GitHub Actions로 자동 깨우는 법 - 비개발자 하랑의 AI 풀스택 도전기](https://lookfortaste.com/supabase-%EB%AC%B4%EB%A3%8C-%ED%94%8C%EB%9E%9C-2%EC%A3%BC%EB%A9%B4-%EC%9E%A0%EB%93%A0%EB%8B%A4-github-actions%EB%A1%9C-%EC%9E%90%EB%8F%99-%EA%B9%A8%EC%9A%B0%EB%8A%94-%EB%B2%95/)
2. [[Supabase 시작하기] - 회원 가입부터 기초 CRUD, RAG를 위한 pgvector 활성화 하기 :: 갓대희의 작은공간](https://goddaehee.tistory.com/377)
3. [Supabase 입문 가이드: 오픈소스 Firebase 대안의 모든 것 - [루닥스 블로그] 연습만이 살길이다](https://rudaks.tistory.com/entry/Supabase-%EC%9E%85%EB%AC%B8-%EA%B0%80%EC%9D%B4%EB%93%9C-%EC%98%A4%ED%94%88%EC%86%8C%EC%8A%A4-Firebase-%EB%8C%80%EC%95%88%EC%9D%98-%EB%AA%A8%EB%93%A0-%EA%B2%83)


---

*Photo by [Conny Schneider](https://unsplash.com/@choys_) on [Unsplash](https://unsplash.com/photos/a-blue-background-with-lines-and-dots-xuTJZ7uD7PI)*
