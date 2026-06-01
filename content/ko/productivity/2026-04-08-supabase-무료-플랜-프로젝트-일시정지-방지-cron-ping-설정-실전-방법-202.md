---
title: "Supabase 무료 플랜 프로젝트 일시정지 방지: cron ping 실전 설정 방법"
date: 2026-04-08T20:11:18+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-web", "supabase", "\ud504\ub85c\uc81d\ud2b8", "\uc77c\uc2dc\uc815\uc9c0", "Next.js"]
description: "Supabase 무료 플랜은 7일 비활성 시 프로젝트를 자동 일시정지해요. cron-job.org 또는 GitHub Actions로 주기적 HTTP ping을 보내 비활성 카운터를 리셋하는 실전 코드와 함정을 정리했어요."
image: "/images/20260408-supabase-무료-플랜-프로젝트-일시정지-방지-cr.webp"
technologies: ["Next.js", "PostgreSQL", "REST API", "Vercel", "GitHub Actions"]
faq:
  - question: "Supabase 무료 플랜 프로젝트 자동으로 꺼지는 이유"
    answer: "Supabase 무료 플랜은 7일 동안 API 요청이 없으면 프로젝트를 자동으로 일시정지(Pause) 상태로 전환해요. 일시정지되면 DB 연결과 API 호출이 전부 차단되고, 대시보드에서 직접 Restore 버튼을 눌러야 복구할 수 있어요."
  - question: "Supabase 무료 플랜 프로젝트 일시정지 방지 cron ping 설정 실전 방법 2025 GitHub Actions로 하는 법"
    answer: "Supabase 무료 플랜 프로젝트 일시정지 방지 cron ping 설정 실전 방법 2025 기준으로, GitHub Actions에 keep-alive.yml 워크플로우를 만들고 매일 1회 Supabase REST 엔드포인트로 curl 요청을 보내면 돼요. secrets에 SUPABASE_ANON_KEY와 SUPABASE_PROJECT_REF를 등록해두면 자동으로 실행되며, 단 리포지터리가 60일 비활성이면 Actions 자체가 꺼질 수 있으니 주의해야 해요."
  - question: "cron-job.org로 Supabase 프로젝트 일시정지 막는 방법"
    answer: "cron-job.org에 가입 후 Supabase REST 엔드포인트 URL과 apikey 헤더를 등록하고 실행 주기를 매일 1회로 설정하면 5분 안에 설정이 완료돼요. 단, anon key로 접근 가능한 테이블에 Row Level Security(RLS)가 올바르게 설정되어 있는지 반드시 사전에 확인해야 해요."
  - question: "Supabase 일시정지 복구 시간 얼마나 걸리나요"
    answer: "Supabase 무료 플랜에서 일시정지된 프로젝트를 복구하려면 대시보드에서 수동으로 Restore 버튼을 눌러야 하며, 복구 완료까지 최대 수 분에서 수십 분이 걸릴 수 있어요. 데모 발표나 포트폴리오 공유 직전에 이 상황이 발생하면 대응이 어렵기 때문에 사전에 ping 자동화를 설정해두는 것이 중요해요."
  - question: "Supabase 무료 플랜 프로젝트 일시정지 방지 cron ping 설정 실전 방법 2025 가장 간단한 방법"
    answer: "Supabase 무료 플랜 프로젝트 일시정지 방지 cron ping 설정 실전 방법 2025에서 가장 간단한 방법은 cron-job.org를 이용하는 외부 스케줄러 방식이에요. 별도의 코드 작성 없이 URL과 헤더, 실행 주기만 웹에서 등록하면 되기 때문에 개발 환경이 없어도 누구나 5분 안에 설정할 수 있어요."
---

열심히 만든 사이드 프로젝트가 어느 날 갑자기 먹통이 됐다면, 원인은 대부분 하나예요. Supabase 무료 플랜의 자동 일시정지 정책.

이 글은 cron ping으로 일시정지를 막는 방법을 실전 기준으로 정리해요. 어떤 방식이 더 믿을 만한지, 함정은 뭔지, 바로 써먹을 수 있는 코드까지요.

> **핵심 요약**
> - Supabase 무료(Free) 플랜은 7일 연속 비활성 시 프로젝트를 자동으로 일시정지(Pause)해요.
> - 일시정지된 프로젝트는 수동 복구가 필요하고, 복구까지 최대 수 분~수십 분이 걸릴 수 있어요.
> - 외부 cron 서비스(예: cron-job.org)로 주기적인 HTTP ping을 보내면 비활성 카운터가 리셋돼요.
> - GitHub Actions를 cron 스케줄러로 쓰면 무료로 자동화가 가능하지만, 리포지터리 활성 정책 변경에 주의해야 해요.
> - 2026년 현재 Supabase 공식 대시보드에는 이 문제를 직접 해결하는 UI가 없어서, 외부 자동화가 사실상 유일한 현실적 대안이에요.

---

## Supabase 무료 플랜, 7일이면 잠든다

Supabase는 Firebase의 오픈소스 대안으로 자리 잡은 BaaS예요. PostgreSQL 기반 DB, 인증, 스토리지, Edge Function까지 한 번에 쓸 수 있어서 사이드 프로젝트나 MVP 개발에 자주 써요.

그런데 무료 플랜에는 치명적인 조건이 하나 있어요.

**7일 동안 API 요청이 없으면 프로젝트가 자동으로 일시정지돼요.**

공식 문서(2026년 4월 기준)에 따르면, 비활성 상태가 7일 이상 지속되면 자동으로 Paused 상태로 전환돼요. DB 연결도, API 호출도 전부 차단돼요. 복구하려면 대시보드에 직접 들어가서 수동으로 Restore 버튼을 눌러야 해요.

문제는 타이밍이에요. 배포 직후 며칠은 열심히 테스트하다가, 바쁜 일상에 묻혀 2주쯤 지나서 다시 열면 서비스 전체가 다운돼 있어요. 데모 링크 공유한 날 하필 이 상황이 터지면 정말 난감하죠.

그래서 지금 이 얘기가 중요해요. 2026년 들어 Supabase 무료 플랜 사용자가 크게 늘었어요. 공식 블로그에 따르면 2025년 말 기준 누적 프로젝트 수가 100만 개를 넘었고, 그중 상당수가 무료 플랜이에요. 솔로 개발자와 부트캠프 졸업생들이 포트폴리오 프로젝트를 호스팅하는 플랫폼으로 자리 잡으면서, 7일 정책에 발목 잡히는 사람도 그만큼 늘었어요.

---

## cron ping이 뭔지부터 짚고 가요

"ping"은 원래 네트워크 연결을 확인하는 명령어예요. 여기서는 특정 URL로 HTTP GET 요청을 주기적으로 보내는 행위를 가리켜요.

Supabase는 REST API 엔드포인트를 외부에 노출해요. 이 엔드포인트로 단순한 GET 요청만 보내도 시스템 입장에서는 "이 프로젝트가 사용되고 있다"고 인식해요. 비활성 카운터가 리셋되는 거예요.

실제로 ping에 쓸 수 있는 엔드포인트는 두 가지예요.

```
# Supabase REST API 헬스 체크 엔드포인트
GET https://<project-ref>.supabase.co/rest/v1/

# 또는 실제 테이블 조회 (1건만)
GET https://<project-ref>.supabase.co/rest/v1/<table-name>?limit=1
```

첫 번째 방식은 헤더에 `apikey`만 붙이면 되고, 두 번째는 실제 데이터 조회라서 조금 더 확실하게 활성 신호를 줘요.

---

## 세 가지 방법, 실전 비교

### cron-job.org: 가장 간단한 외부 스케줄러

[cron-job.org](https://cron-job.org)는 무료 웹 기반 cron 서비스예요. 회원 가입 후 URL과 주기만 등록하면 끝이에요. 5분이면 설정 완료돼요.

설정 방법:
1. cron-job.org 가입 후 새 Cronjob 생성
2. URL에 Supabase REST 엔드포인트 입력
3. 헤더에 `apikey: <your-anon-key>` 추가
4. 실행 주기를 매일 1회(예: 매일 오전 9시)로 설정

단, anon key는 공개 키라 노출되어도 기능적으로는 괜찮지만, 해당 키로 접근 가능한 테이블의 Row Level Security(RLS)가 제대로 설정되어 있는지 반드시 확인해야 해요.

### GitHub Actions: 코드로 관리하는 자동화

이미 GitHub에 프로젝트가 있다면 GitHub Actions가 제일 깔끔해요.

```yaml
# .github/workflows/keep-alive.yml
name: Supabase Keep Alive

on:
  schedule:
    - cron: '0 9 * * *'  # 매일 오전 9시 UTC
  workflow_dispatch:

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Supabase
        run: |
          curl -s -o /dev/null -w "%{http_code}" \
            -H "apikey: ${{ secrets.SUPABASE_ANON_KEY }}" \
            "https://${{ secrets.SUPABASE_PROJECT_REF }}.supabase.co/rest/v1/"
```

secrets에 `SUPABASE_ANON_KEY`와 `SUPABASE_PROJECT_REF`만 등록해두면 돼요. 코드 형태라서 변경 이력도 남고, 팀 프로젝트라면 PR로 관리할 수 있어요.

**주의할 점**: GitHub Actions는 리포지터리가 60일 동안 비활성이면 자동으로 꺼져요. Supabase 프로젝트는 살렸는데 Actions 자체가 멈추는 상황이 생기는 거예요. 최소 두 달에 한 번은 커밋을 남기거나, `workflow_dispatch`로 수동 실행해서 확인하는 게 좋아요.

### Vercel/Netlify 서버리스 함수: 앱이 있다면 가장 자연스러운 방법

이미 프론트엔드를 Vercel이나 Netlify에 배포 중이라면, 해당 플랫폼의 Scheduled Functions 기능을 쓰는 게 가장 자연스러워요. Vercel의 경우 `vercel.json`에 cron 스케줄을 정의하고, 간단한 API Route만 만들면 돼요.

```js
// app/api/keep-alive/route.ts (Next.js App Router)
export async function GET() {
  const res = await fetch(
    `https://${process.env.SUPABASE_PROJECT_REF}.supabase.co/rest/v1/`,
    { headers: { apikey: process.env.SUPABASE_ANON_KEY! } }
  );
  return Response.json({ status: res.status });
}
```

### 방법별 비교

| 기준 | cron-job.org | GitHub Actions | Vercel Cron |
|------|-------------|---------------|-------------|
| 설정 난이도 | ⭐ (5분) | ⭐⭐ (YAML 작성) | ⭐⭐ (코드 필요) |
| 무료 여부 | 무료 | 무료 (월 2,000분) | 무료 (Hobby 기준) |
| 코드 관리 | 불가 | 가능 (Git) | 가능 (Git) |
| 만료 위험 | 없음 | 60일 비활성 시 중단 | 프로젝트 삭제 시 중단 |
| 적합한 상황 | 단독 DB 프로젝트 | GitHub 사용 프로젝트 | 풀스택 배포 환경 |

---

## 실제로 쓸 때 챙겨야 할 것들

가장 흔한 실수는 ping 주기를 너무 길게 잡는 거예요. 7일 정책이니까 6일마다 한 번 보내면 되지 않냐고 생각할 수 있는데, Supabase 내부 판단 기준이 항상 정확한 24시간 단위가 아닐 수 있어요. 실무에서는 **매일 1회**를 기준으로 잡는 게 안전해요.

**포트폴리오 프로젝트라면**: cron-job.org로 매일 오전 9시 ping 설정. 추가 코드 없이 5분 안에 끝나요. RLS가 제대로 설정된 테이블이 있다면 `/rest/v1/` 루트보다 실제 테이블 조회 URL이 더 확실해요.

**팀 사이드 프로젝트라면**: GitHub Actions 방식을 추천해요. 설정 파일이 코드로 관리되고, 누가 언제 바꿨는지 추적이 돼요. secrets 등록 시 Service Role Key가 아닌 anon key를 써야 해요. Service Role Key는 RLS를 우회하는 강력한 키라서 워크플로우 파일에 쓰기엔 위험해요.

**이미 Vercel에 배포한 Next.js 앱이라면**: Vercel Cron + API Route 조합이 제일 깔끔해요. 인프라를 한 곳에서 관리할 수 있어요.

참고로 ping이 잘 되고 있는지 확인하고 싶다면, Supabase 대시보드의 **Database → Database Health** 탭에서 최근 연결 시간을 확인하거나, cron-job.org의 실행 로그에서 HTTP 200 응답이 오는지 체크해요.

---

## 앞으로 이 방법이 언제까지 통할까

Supabase가 무료 플랜 정책을 바꾸지 않는 한 이 방식은 계속 통해요. 그런데 몇 가지 신호는 주시할 필요가 있어요.

2025년 하반기에 Supabase는 무료 플랜 제한을 일부 강화했어요. 프로젝트당 최대 2개 제한, 스토리지 1GB 상한 조정 등이 있었죠. 정책이 바뀔 때마다 ping 방식의 효과가 달라질 수 있어요. Supabase 공식 변경 로그와 GitHub Discussion(supabase/supabase)은 정기적으로 확인하는 게 좋아요.

**2026년 하반기에 주목할 신호**: Supabase가 Pro 플랜 전환을 유도하는 방식으로 무료 플랜 정책을 더 조이면, 자동화된 ping 요청을 감지해서 비활성 판단에서 제외할 수도 있어요. 실제로 일부 BaaS 플랫폼은 이런 정책을 이미 적용하고 있거든요. 아직 Supabase는 이런 조치를 취하지 않았지만, 사용자 수가 늘수록 가능성은 열려 있어요.

지금 당장 해야 할 건 하나예요. 오늘 안에 cron-job.org 하나 설정해두세요. 5분짜리 작업이 프로젝트 3개월치 안정성을 지켜줘요.

Supabase 무료 플랜 일시정지 방지는 거창한 기술이 아니에요. ping 하나면 돼요.

---

*ping 설정 후 Supabase 대시보드 Database Health 탭에서 마지막 활성 시간을 직접 확인해보세요. 다음엔 Supabase Edge Functions로 keep-alive 로직을 프로젝트 안에 내재화하는 방법도 다룰 예정이에요.*

## 참고자료

1. [[Supabase 시작하기] - 회원 가입부터 기초 CRUD, RAG를 위한 pgvector 활성화 하기 :: 갓대희의 작은공간](https://goddaehee.tistory.com/377)
2. [Supabase 입문 가이드: 오픈소스 Firebase 대안의 모든 것 - [루닥스 블로그] 연습만이 살길이다](https://rudaks.tistory.com/entry/Supabase-%EC%9E%85%EB%AC%B8-%EA%B0%80%EC%9D%B4%EB%93%9C-%EC%98%A4%ED%94%88%EC%86%8C%EC%8A%A4-Firebase-%EB%8C%80%EC%95%88%EC%9D%98-%EB%AA%A8%EB%93%A0-%EA%B2%83)
3. [프리티어 Supabase 프로젝트, 자동으로 살려두는 방법 :: Life Journal](https://inseong1204.tistory.com/183)


---

*Photo by [Microsoft Copilot](https://unsplash.com/@microsoftcopilot) on [Unsplash](https://unsplash.com/photos/two-women-talking-in-a-kitchen-while-cooking-3c_k7h8YgHw)*
