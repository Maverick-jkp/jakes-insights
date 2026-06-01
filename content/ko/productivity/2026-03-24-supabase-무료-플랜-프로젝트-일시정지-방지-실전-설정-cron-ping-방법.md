---
title: "Supabase 무료 플랜 일시정지 방지: cron ping 실전 설정 방법"
date: 2026-03-24T20:17:35+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-web", "supabase", "\ud504\ub85c\uc81d\ud2b8", "\uc77c\uc2dc\uc815\uc9c0", "PostgreSQL"]
description: "Supabase 무료 플랜은 7일 비활성 시 자동 일시정지됩니다. cron-job.org로 4~5일 간격마다 REST API에 ping을 보내 프로젝트 중단을 막는 실전 설정 방법을 단계별로 설명합니다."
image: "/images/20260324-supabase-무료-플랜-프로젝트-일시정지-방지-실전.webp"
technologies: ["PostgreSQL", "REST API", "GitHub Actions", "Supabase"]
faq:
  - question: "Supabase 무료 플랜 프로젝트 자동으로 꺼지는 이유"
    answer: "Supabase 무료 플랜은 7일 연속으로 HTTP 요청이 없으면 프로젝트를 자동으로 일시정지시킵니다. 재개하려면 대시보드에서 수동으로 Restore를 눌러야 하고, 다시 살아나는 데 수 분에서 수십 분이 걸릴 수 있습니다."
  - question: "Supabase 무료 플랜 프로젝트 일시정지 방지 실전 설정 cron ping 방법"
    answer: "cron-job.org 같은 무료 외부 cron 서비스를 이용해 4~5일 간격으로 Supabase REST API 엔드포인트(/rest/v1/)에 GET 요청을 보내면 일시정지를 방지할 수 있습니다. 요청 시 헤더에 anon public key를 apikey 값으로 포함해야 하며, 별도의 테이블이 없어도 엔드포인트에 요청만 도달하면 활성 상태로 인식됩니다."
  - question: "GitHub Actions으로 Supabase 프로젝트 살려두는 방법"
    answer: "GitHub Actions의 schedule 트리거를 사용해 4일마다 Supabase REST API에 curl 요청을 보내는 워크플로우를 설정할 수 있습니다. GitHub Secrets에 SUPABASE_ANON_KEY와 SUPABASE_URL만 등록하면 별도 외부 서비스 없이 코드 레포 안에서 관리가 가능합니다."
  - question: "pg_cron으로 Supabase 비활성 정지 막을 수 있나요"
    answer: "pg_cron 확장을 활성화하고 5일마다 SELECT 1 같은 가벼운 쿼리를 실행하도록 설정하면 외부 서비스 없이 DB 활성 상태를 유지할 수 있습니다. 단, pg_cron은 DB가 이미 정지된 상태에서는 실행되지 않으므로 예방 목적으로만 활용해야 합니다."
  - question: "Supabase 무료 플랜 프로젝트 일시정지 방지 실전 설정 cron ping 방법 중 가장 쉬운 것"
    answer: "세 가지 방법(cron-job.org, pg_cron, GitHub Actions) 중 설정 난이도가 가장 낮은 것은 cron-job.org를 이용한 외부 ping 방식입니다. 무료 계정을 만들고 URL과 헤더 두 가지만 입력하면 바로 동작하며, 별도 코드 작성이나 SQL 설정이 필요하지 않아 빠르게 적용할 수 있습니다."
---

포트폴리오 링크 보냈더니 면접관이 "여기 서버 죽었는데요?"라고 답장을 보내왔어요. Supabase 무료 플랜 쓰는 개발자라면 한 번쯤 겪는 상황이죠.

이유는 단순해요. **7일 동안 HTTP 요청이 없으면 자동으로 일시정지**되거든요. 재개하려면 대시보드에서 수동으로 Restore를 눌러야 하고, 다시 살아나는 데 수 분에서 수십 분이 걸려요.

> **핵심 요약**
> - Supabase 무료 플랜은 7일간 비활성 상태가 지속되면 프로젝트를 자동으로 일시정지시킨다.
> - `cron-job.org` 같은 무료 cron 서비스로 주기적 ping 요청을 보내면 일시정지를 방지할 수 있다.
> - Supabase REST API의 `/rest/v1/` 엔드포인트를 대상으로 4~5일 간격의 HTTP GET 요청이 가장 안정적이다.
> - pg_cron 확장을 쓰면 DB 내부에서 직접 주기적 쿼리를 실행해 추가 외부 서비스 없이도 활성 상태를 유지할 수 있다.
> - 2026년 현재 Supabase Pro 플랜(월 $25)으로 전환하면 일시정지 없이 운영 가능하지만, 소규모 프로젝트라면 ping 방식이 현실적인 선택이다.

---

## 왜 갑자기 프로젝트가 잠길까요?

Supabase는 2026년 현재 무료 플랜으로 PostgreSQL 데이터베이스, Auth, Storage, Edge Functions까지 제공해요. 스타트업 MVP나 개인 프로젝트 용도로는 충분한 스펙이죠.

그런데 **비활성 정지 정책**이 있어요. 공식 문서 기준으로, 무료 플랜 프로젝트는 연속 7일 동안 HTTP 요청이 없으면 자동 일시정지돼요.

실제로 이 문제를 자주 겪는 케이스는 세 가지예요.

1. **사이드 프로젝트** — 주말에만 접속하거나 개발이 잠시 멈춘 경우
2. **포트폴리오 백엔드** — 면접관이 접속할 때만 트래픽이 생기는 경우
3. **내부 관리 툴** — 주중에만 쓰고 주말이 지나면 정지되는 경우

해결책은 간단해요. 7일이 되기 전에 주기적으로 ping을 보내서 "살아있다"는 신호를 주면 돼요. 방법은 세 가지가 있어요.

---

## 핵심 접근법 세 가지

### 1. 외부 Cron 서비스로 주기적 HTTP Ping 보내기

가장 널리 쓰이는 방법이에요. 외부 cron 서비스가 일정 주기로 Supabase REST API에 GET 요청을 보내서 활성 상태를 유지해 주는 거예요.

**세팅 방법 (cron-job.org 기준)**:

1. `cron-job.org`에 무료 계정을 만들어요.
2. 새 cron job을 추가하고, URL에 아래 형식을 넣어요:

```
https://[YOUR_PROJECT_REF].supabase.co/rest/v1/
```

3. 헤더에 두 가지를 추가해요:
   - `apikey`: Supabase 프로젝트의 `anon public key`
   - `Content-Type`: `application/json`

4. 실행 주기는 **5일 이하**로 설정하세요. 7일 정책이니 6일로 잡으면 아슬아슬하고, 4~5일 간격이 안전해요.

요청을 받을 테이블이 없어도 괜찮아요. `/rest/v1/` 엔드포인트에 요청만 와도 활성 상태로 인식되거든요.

참고로, ping 간격이 너무 짧으면(매 1분 같은 경우) 무료 플랜의 월 500MB 데이터베이스 대역폭을 소모할 수 있어요. 하루에 한 번이나 이틀에 한 번 정도가 적당해요.

---

### 2. pg_cron으로 DB 내부에서 직접 처리하기

Supabase는 PostgreSQL 확장인 `pg_cron`을 지원해요. 외부 서비스 없이 데이터베이스 안에서 직접 주기적 쿼리를 실행할 수 있어요.

Supabase 대시보드 → Database → Extensions에서 `pg_cron`을 활성화한 뒤, SQL 에디터에서 이렇게 설정해요:

```sql
SELECT cron.schedule(
  'keep-alive-ping',
  '0 9 */5 * *',  -- 5일마다 오전 9시 실행
  $$SELECT 1$$
);
```

`SELECT 1`처럼 아주 가벼운 쿼리를 실행하는 것만으로도 충분해요. DB에 접근했다는 기록이 남으니까요.

단, 이 방식에는 한계가 있어요. pg_cron 자체도 DB가 활성화된 상태여야 실행돼요. 즉, **이미 정지된 DB는 pg_cron도 실행 못 해요**. 예방용으로만 쓰는 방식이라는 걸 기억해 두세요.

---

### 3. GitHub Actions로 자동화하기

코드베이스를 GitHub에서 관리한다면, `schedule` 트리거를 쓸 수 있어요.

```yaml
name: Supabase Keep Alive
on:
  schedule:
    - cron: '0 9 */4 * *'   # 4일마다 오전 9시 UTC
jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Supabase
        run: |
          curl -s \
            -H "apikey: ${{ secrets.SUPABASE_ANON_KEY }}" \
            "${{ secrets.SUPABASE_URL }}/rest/v1/"
```

GitHub Secrets에 `SUPABASE_ANON_KEY`와 `SUPABASE_URL`만 등록하면 끝이에요. 별도 외부 서비스 없이 코드 레포에서 관리할 수 있다는 게 장점이죠.

---

### 방법별 비교

| 항목 | cron-job.org | pg_cron | GitHub Actions |
|------|-------------|---------|----------------|
| 설정 난이도 | 쉬움 | 보통 | 보통 |
| 외부 의존성 | 있음 | 없음 | GitHub에 의존 |
| 비용 | 무료 | 무료 | 무료 (월 2,000분 한도) |
| 신뢰도 | 높음 | DB 정지 시 미작동 | 높음 |
| 코드 관리 | 불필요 | SQL만 | YAML 파일 |
| **추천 상황** | 빠르게 설정할 때 | DB 내부 관리 선호 시 | CI/CD 이미 있을 때 |

처음 시작하는 개발자라면 `cron-job.org` 방식이 제일 빨라요. 계정 만들고 URL 넣고 저장하면 10분 안에 끝나거든요. GitHub Actions는 이미 레포가 있고 Secrets 관리에 익숙한 분들에게 잘 맞아요.

---

## 실전에서 주의해야 할 포인트

**"ping 설정했는데 그래도 정지됐어요"**

anon key가 만료됐거나 프로젝트 URL이 바뀐 경우예요. Supabase 대시보드 → Settings → API에서 `Project URL`과 `anon public` 키를 다시 확인해 보세요. 프로젝트를 삭제하고 새로 만든 경우 URL prefix가 달라지거든요.

**"anon key를 외부에 노출해도 되나요?"**

`anon` 키는 클라이언트에서도 쓰는 공개 키예요. 그런데 Row Level Security(RLS)가 제대로 설정돼 있어야 해요. RLS 없이 테이블을 열어두면 누구나 데이터를 읽을 수 있어요. Ping 용도라면 어떤 테이블에도 접근 권한을 주지 않아도 되니까 `/rest/v1/` 엔드포인트만 hit하는 게 가장 안전해요.

**"장기적으로 유료 전환을 고민 중이에요"**

Supabase Pro 플랜은 월 $25이고, 일시정지 정책이 없어요. 실제 사용자를 받기 시작했다면 ping 방식보다 플랜 업그레이드가 운영 부담을 훨씬 줄여줘요. 트래픽이 없을 때도 DB가 항상 살아있어야 하는 프로덕션 서비스라면 $25는 합리적인 비용이에요.

---

## 지금 당장 할 일

방법 정리하면 이래요.

- **빠른 설정**: `cron-job.org` → 4~5일 간격 ping → anon key 헤더 추가
- **코드 기반 관리**: GitHub Actions YAML 파일 하나로 처리
- **DB 내부 관리**: pg_cron 확장 켜고 `SELECT 1` 스케줄 등록

세 방법 모두 무료이고, 설정에 걸리는 시간은 10분 이내예요.

앞으로 Supabase가 무료 플랜 정책을 조정할 가능성도 있어요. 실제로 2025년 말부터 커뮤니티에서 비활성 기간을 14일로 늘려달라는 요청이 꾸준히 올라오고 있거든요. Supabase GitHub Discussions와 공식 블로그를 주시해두면 변경 사항을 빨리 잡을 수 있어요.

지금 정지 위험에 있는 프로젝트가 있다면, 대시보드에서 Last Active 날짜부터 확인해 보세요. 6일 이상 지났다면 오늘 바로 cron ping 설정할 타이밍이에요.

## 참고자료

1. [Prevent Supabase Free Tier Pausing (2026 Guide) | Medium](https://shadhujan.medium.com/how-to-keep-supabase-free-tier-projects-active-d60fd4a17263)
2. [백엔드 서버에서 코드로 supabase 서버를 열지않고 활성화 할 수있는 방법 :: bdshi-tec](https://bidshi-tec.tistory.com/415)
3. [[Supabase 시작하기] - 회원 가입부터 기초 CRUD, RAG를 위한 pgvector 활성화 하기 :: 갓대희의 작은공간](https://goddaehee.tistory.com/377)


---

*Photo by [Conny Schneider](https://unsplash.com/@choys_) on [Unsplash](https://unsplash.com/photos/a-blue-background-with-lines-and-dots-xuTJZ7uD7PI)*
