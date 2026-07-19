---
title: "Supabase 무료 플랜 PostgreSQL 연결 수 초과, Supavisor로 해결하는 법"
date: 2026-03-17T20:06:59+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-data", "supabase", "postgresql", "supavisor", "Next.js"]
description: "Supabase 무료 플랜 PostgreSQL 직접 연결(포트 5432)은 최대 60개로 제한돼 Next.js 서버리스 환경에서 쉽게 고갈됩니다. Supavisor 포트 6543 트랜잭션 모드로 전환해 연결 초과"
image: "/images/20260317-supabase-무료-플랜-postgresql-연결-수.webp"
technologies: ["Next.js", "AWS", "PostgreSQL", "Vercel", "Supabase"]
faq:
  - question: "Supabase 무료 플랜 PostgreSQL 연결 수 초과 어떻게 해결하나요"
    answer: "Supabase 무료 플랜 PostgreSQL 연결 수 초과 문제는 Supavisor 설정으로 해결할 수 있어요. Supabase 대시보드의 Settings → Database에서 포트 6543 트랜잭션 모드 Connection Pooler URL로 환경 변수를 교체하면 됩니다. 이렇게 하면 60개 물리 연결로 수천 개의 동시 요청을 처리할 수 있어요."
  - question: "Next.js Vercel 배포 후 DB remaining connection slots are reserved 에러 뜨는 이유"
    answer: "Vercel의 Next.js 서버리스 환경에서는 요청마다 독립적인 Serverless Function 인스턴스가 실행되고, 각 인스턴스가 DB 연결을 새로 맺기 때문이에요. ORM의 연결 풀이 인스턴스 간에 공유되지 않아 트래픽이 조금만 몰려도 Supabase 무료 플랜의 최대 60개 연결 한도를 빠르게 초과합니다."
  - question: "Supavisor 트랜잭션 모드 세션 모드 차이점"
    answer: "트랜잭션 모드(포트 6543)는 쿼리 실행 중에만 DB 연결을 점유하고 트랜잭션이 끝나면 즉시 반납해 서버리스 환경에 적합하지만, Prepared Statement는 지원하지 않아요. 세션 모드(포트 5432)는 클라이언트 세션 내내 연결을 유지해 Prepared Statement와 장기 트랜잭션에는 유리하지만, 무료 플랜에서 연결 초과 위험이 높습니다."
  - question: "Prisma Supabase Supavisor 연결 설정 pgbouncer 파라미터 왜 필요한가요"
    answer: "Prisma는 기본적으로 Prepared Statement를 사용하는데, Supavisor 트랜잭션 모드에서는 이를 지원하지 않아 에러가 발생해요. DATABASE_URL에 `?pgbouncer=true&connection_limit=1`을 추가하면 Prisma가 Prepared Statement를 비활성화하고 연결 수를 제한해 풀러와 호환되도록 동작합니다. 또한 schema.prisma에 `directUrl`을 별도로 설정해야 `prisma migrate` 명령이 정상 실행돼요."
  - question: "Supabase 무료 플랜 Next.js 트러블슈팅 Drizzle ORM 연결 풀 설정 방법"
    answer: "Supabase 무료 플랜 환경에서 Next.js와 Drizzle ORM을 함께 쓸 때는 Supavisor 포트 6543 URL을 사용하되, `max: 1`로 연결 풀 사이즈를 제한하는 것이 서버리스 환경에서 안전해요. Drizzle은 Prisma와 달리 별도의 pgbouncer 파라미터가 필요 없어 설정이 비교적 간단합니다."
aliases:
  - "/tech/2026-03-17-supabase-무료-플랜-postgresql-연결-수-초과-supavisor-설정-트러블/"

---

Next.js 앱을 배포했는데 DB가 갑자기 응답을 멈췄어요. 에러 메시지를 열어보면 `remaining connection slots are reserved`. 무료 플랜인데 연결 수가 넘쳤다는 거죠. 그런데 이 문제, 사실 Supabase의 한계가 아니라 연결 방식의 오해에서 비롯돼요.

> **핵심 요약**
> - Supabase 무료 플랜의 PostgreSQL 직접 연결(포트 5432)은 최대 60개 동시 연결만 허용하며, 초과하면 즉시 연결 거부가 발생해요.
> - Next.js 서버리스 환경(Vercel 등)에서는 함수 호출마다 새 DB 연결을 맺는 구조라 연결 수가 빠르게 고갈돼요.
> - Supavisor는 Supabase가 공식 제공하는 연결 풀러로, 포트 6543 트랜잭션 모드로 전환하면 수천 개의 동시 요청을 처리할 수 있어요.
> - 연결 문자열 하나만 바꿔도 해결되는 경우가 많지만, pgBouncer 방식과 Supavisor의 차이를 모르면 마이그레이션에서 실패해요.

---

## Supabase 무료 플랜이 연결 수 60개를 고집하는 이유

PostgreSQL은 기본적으로 연결마다 별도 프로세스를 생성해요. 연결 하나당 약 5–10MB 메모리를 점유하는 구조죠. Supabase 무료 플랜은 공유 인프라 위에서 돌아가기 때문에, 공식 문서 기준 프로젝트당 **최대 60개 직접 연결**만 허용해요.

문제는 Next.js와 서버리스 배포의 조합이에요. Vercel에 올린 Next.js 앱은 요청마다 Serverless Function이 독립적으로 실행돼요. 각 인스턴스가 시작될 때 DB 연결을 새로 맺고, 함수가 종료되어도 연결이 즉시 닫히지 않는 경우가 많아요. 트래픽이 조금만 몰려도 60개는 순식간에 차요.

`Prisma`, `Drizzle ORM` 같은 ORM을 쓰면 기본 설정에서 연결 풀을 자체 관리하는데, 서버리스 환경에서는 이 풀이 공유되지 않아요. 함수 인스턴스마다 독립 풀이 생기니까 사실상 풀링 효과가 없는 셈이에요.

---

## Supavisor가 뭔지, 기존 pgBouncer와 뭐가 다른지

Supavisor는 2023년 Supabase가 Elixir로 직접 개발한 연결 풀러예요. 기존 pgBouncer를 완전히 대체했고, 공식 문서에 따르면 **수백만 개의 테넌트를 단일 클러스터에서 처리**할 수 있도록 설계됐어요.

연결 모드는 두 가지예요:

| 구분 | 트랜잭션 모드 (포트 6543) | 세션 모드 (포트 5432) |
|------|--------------------------|----------------------|
| **연결 방식** | 트랜잭션 끝나면 연결 반납 | 클라이언트 세션 동안 유지 |
| **서버리스 적합성** | ✅ 높음 | ❌ 낮음 |
| **Prepared Statement** | ❌ 미지원 | ✅ 지원 |
| **장기 트랜잭션** | ❌ 적합하지 않음 | ✅ 적합 |
| **무료 플랜 권장** | ✅ 예 | ❌ 연결 초과 위험 |
| **최대 동시 처리** | 수천 개 이상 | 60개 (무료 플랜) |

트랜잭션 모드가 서버리스에 맞는 이유는 간단해요. DB 연결을 실제 쿼리가 실행되는 동안만 점유하고, 트랜잭션이 끝나면 즉시 풀에 반납해요. 결국 60개의 물리 연결이 수천 개의 동시 요청을 순차적으로 처리할 수 있게 되는 거예요.

단, 트랜잭션 모드에서는 `PREPARE` 구문이 작동하지 않아요. Prisma를 쓴다면 `?connection_limit=1&pgbouncer=true` 파라미터를 연결 문자열에 추가해야 해요. 이걸 빠뜨리면 Prepared Statement 관련 에러가 새로 생겨요.

---

## Next.js + Supabase Supavisor 트러블슈팅 실전 체크리스트

### 연결 문자열부터 바꿔야 해요

Supabase 대시보드에서 **Settings → Database → Connection string**으로 가면 두 가지 URL이 있어요:

- **Direct connection**: `postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres`
- **Connection pooler**: `postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`

무료 플랜에서 Next.js를 Vercel로 배포한다면 환경 변수를 **pooler URL (포트 6543)** 으로 바꿔야 해요.

### Prisma를 쓴다면 이 설정 필수예요

```env
DATABASE_URL="postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres?pgbouncer=true&connection_limit=1"
DIRECT_URL="postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres"
```

`prisma/schema.prisma`에도 `directUrl`을 추가해야 마이그레이션이 정상 작동해요:

```prisma
datasource db {
  provider  = "postgresql"
  url       = env("DATABASE_URL")
  directUrl = env("DIRECT_URL")
}
```

`directUrl`이 없으면 `prisma migrate` 명령이 풀러를 통해 실행되고, Prepared Statement 에러가 발생할 수 있어요.

### Drizzle ORM 사용자라면

Drizzle은 자체적으로 `pgbouncer` 파라미터가 필요 없어요. 대신 연결 풀 사이즈를 `max: 1`로 제한하는 게 서버리스 환경에서 안전해요:

```ts
import { drizzle } from 'drizzle-orm/postgres-js'
import postgres from 'postgres'

const client = postgres(process.env.DATABASE_URL!, { max: 1 })
export const db = drizzle(client)
```

---

## 이 문제가 커지는 시점과 대응 방향

### 트래픽이 없는데도 에러가 난다면

`pg_stat_activity` 뷰를 직접 조회해보세요:

```sql
SELECT count(*), state FROM pg_stat_activity GROUP BY state;
```

`idle` 상태 연결이 수십 개 쌓여 있다면 연결이 제대로 반납되지 않고 있는 거예요. ORM 설정 문제이거나 `connection_limit`을 지정하지 않은 경우예요.

### 프로덕션으로 가기 전 체크할 3가지

1. **환경 변수 확인**: `DATABASE_URL`이 반드시 포트 6543 pooler URL인지 점검해요.
2. **ORM별 파라미터**: Prisma라면 `?pgbouncer=true&connection_limit=1`, Drizzle이라면 `max: 1` 설정.
3. **마이그레이션 분리**: `DIRECT_URL`을 별도로 설정해 마이그레이션은 직접 연결로 실행.

Supabase 무료 플랜 제한은 꽤 빡빡해요. 그런데 Supavisor 트랜잭션 모드로 전환하면 같은 인프라에서 처리 가능한 동시 요청이 60배 이상 늘어요. 연결 문자열 하나만 바꾸는 게 출발점이에요.

---

## 앞으로 주목할 변화

Supabase는 2026년 상반기에 무료 플랜 Supavisor 연결 풀 상한을 조정하는 정책 변경을 검토 중이에요(Supabase GitHub Discussions 참고). 유료 플랜(Pro, $25/월)으로 전환하면 직접 연결 수 제한이 200개로 늘고, Supavisor 풀 설정도 세밀하게 제어할 수 있어요.

- **단기**: 트랜잭션 모드 + `connection_limit=1` 조합이 무료 플랜의 사실상 표준이 될 가능성이 높아요.
- **중기**: Prisma 5.x와 Drizzle의 엣지 런타임 지원이 성숙해지면서 서버리스 DB 연결 패턴이 더 단순해질 거예요.
- **지켜볼 것**: Supabase의 IPv4 주소 부가 요금($4/월) 정책이 무료 플랜 pooler 연결 방식에 어떤 영향을 미치는지예요.

지금 당장 에러를 겪고 있다면 Supabase 대시보드에서 pooler URL을 복사해 환경 변수를 바꾸는 것부터 시작하세요. 코드 변경 없이 해결되는 경우가 대부분이에요. 그래도 반복된다면 `pg_stat_activity`로 유휴 연결 개수를 직접 확인하는 게 다음 단계예요.

---

*이 글에서 언급된 Supabase Supavisor 설정 정보는 [Supabase 공식 문서 - Supavisor FAQ](https://supabase.com/docs/guides/troubleshooting/supavisor-faq-YyP5tI) 기준으로 작성됐어요.*

## 참고자료

1. [Supabase Docs | Troubleshooting | Supavisor FAQ](https://supabase.com/docs/guides/troubleshooting/supavisor-faq-YyP5tI)
2. [[개발일지#013] Supabase PostgreSQL 데이터베이스 연결하기 (가입부터 생성, 연결까지)](https://ddururiiiiiii.tistory.com/709)


---

*Photo by [NASA](https://unsplash.com/@nasa) on [Unsplash](https://unsplash.com/photos/photo-of-outer-space-Q1p7bh3SHj8)*
