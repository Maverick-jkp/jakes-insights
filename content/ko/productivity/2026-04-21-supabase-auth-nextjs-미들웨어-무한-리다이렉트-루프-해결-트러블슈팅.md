---
title: "Supabase Auth Next.js 미들웨어 무한 리다이렉트 루프 원인과 해결 방법"
date: 2026-04-21T20:20:33+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-web", "supabase", "auth", "next.js", "TypeScript"]
description: "Supabase Auth Next.js 미들웨어 무한 리다이렉트 루프, Discord 상위 질문 3위 문제입니다. matcher 설정 누락과 공개 경로 처리 실수가 주원인이며, 실제 코드로 해결법을 확인하세요."
image: "/images/20260421-supabase-auth-nextjs-미들웨어-무한-리.webp"
technologies: ["TypeScript", "Next.js", "Supabase"]
faq:
  - question: "Supabase Auth Next.js 미들웨어 무한 리다이렉트 루프 해결 방법"
    answer: "Supabase Auth Next.js 미들웨어 무한 리다이렉트 루프의 가장 흔한 원인은 `/login` 같은 공개 경로를 예외 처리하지 않아서 '세션 없음 → /login 리다이렉트 → 미들웨어 재실행'이 반복되는 것입니다. `publicPaths` 배열을 만들어 해당 경로에서는 `NextResponse.next()`로 바로 통과시키고, `matcher` 설정도 정적 파일 경로를 제외하도록 구성하면 루프를 해결할 수 있습니다."
  - question: "Next.js 미들웨어 matcher 설정 안 하면 어떻게 되나요"
    answer: "`matcher` 설정을 생략하면 Next.js는 `/_next/static/`이나 `/favicon.ico` 같은 정적 파일 요청에도 미들웨어를 실행합니다. Supabase를 함께 쓰는 경우 불필요한 세션 체크가 반복되고 쿠키 처리 충돌이 발생할 수 있으므로, 공식 문서 권장 패턴대로 정적 파일 경로를 제외하는 `matcher` 설정을 반드시 추가해야 합니다."
  - question: "Supabase createServerClient 미들웨어에서 세션 갱신 안 될 때 원인"
    answer: "미들웨어에서 `createServerClient`를 사용할 때 쿠키 읽기/쓰기 콜백인 `getAll`/`setAll`을 정확히 구현하지 않으면 리프레시 토큰이 갱신되지 않아 세션이 유지되지 않습니다. 또한 `cookies.set()` 호출 시 에러를 그냥 throw하면 갱신 실패가 조용히 반복될 수 있으므로, 공식 문서의 `try-catch` 패턴을 그대로 따르는 것이 안전합니다."
  - question: "Supabase Next.js 미들웨어 루프 디버깅 빠르게 하는 법"
    answer: "Supabase Auth Next.js 미들웨어 무한 리다이렉트 루프 트러블슈팅을 할 때 가장 빠른 방법은 미들웨어 상단에 `console.log(request.nextUrl.pathname)`을 추가해 어느 경로에서 반복 실행되는지 먼저 확인하는 것입니다. 루프가 발생하는 경로가 특정되면, 해당 경로가 공개 경로 예외 처리에 포함됐는지와 `matcher` 설정이 올바른지 순서대로 점검하면 원인을 빠르게 좁힐 수 있습니다."
  - question: "Supabase ssr 패키지 middleware.ts와 server.ts 분리해야 하는 이유"
    answer: "`@supabase/ssr` 패키지를 사용할 때 `middleware.ts`와 `utils/supabase/server.ts`를 분리하지 않고 섞어 쓰면 쿠키 처리 로직이 충돌해 세션 갱신이 불안정해집니다. Supabase 공식 문서는 미들웨어 전용 클라이언트와 서버 컴포넌트·Route Handler용 클라이언트를 별도 파일로 관리하는 구조를 권장하며, 이 분리 구조를 지켜야 각 환경에서 쿠키가 올바르게 읽히고 쓰입니다."
---

배포 직전, 로그인 페이지가 무한으로 새로고침되는 걸 봤을 때의 그 느낌. 생각보다 많은 개발자가 겪는 문제예요. Supabase Auth를 Next.js 미들웨어와 함께 쓸 때 발생하는 무한 리다이렉트 루프는, App Router가 표준이 되면서 더 자주 보고되고 있어요.

Supabase 공식 Discord 채널 기준으로, 2026년 1분기 상위 10개 질문 중 "middleware redirect loop"가 세 번째로 많이 올라온 주제예요. 코드 자체는 10줄도 안 되는데, 이렇게 많은 사람이 막히는 이유가 뭘까요?

> **Key Takeaways**
> - Supabase Auth Next.js 미들웨어 무한 리다이렉트 루프의 가장 흔한 원인은 `matcher` 설정 누락 또는 공개 경로(public route) 예외 처리 실패예요.
> - `createServerClient`를 미들웨어에서 제대로 쓰려면 쿠키 읽기/쓰기 로직을 직접 구현해야 하는데, 이 부분에서 세션 갱신 실패가 발생해 루프가 생겨요.
> - 공식 Supabase 문서 기준으로 `middleware.ts`와 별개로 `utils/supabase/server.ts`를 분리하는 구조가 권장되며, 이걸 섞으면 쿠키 처리가 꼬여요.
> - 리다이렉트 루프 트러블슈팅 시 가장 빠른 확인법은 `console.log(request.nextUrl.pathname)`으로 미들웨어가 어느 경로를 타는지 먼저 보는 거예요.

---

## 1. 지금 이 문제가 더 많이 나오는 이유

Next.js 13 이전까지는 인증 처리를 클라이언트 사이드나 `getServerSideProps`에서 했어요. 그때는 미들웨어를 굳이 건드릴 필요가 없었거든요. 그런데 App Router가 도입되면서 상황이 바뀌었어요.

App Router 환경에서는 Server Component가 기본이고, `useSession` 같은 클라이언트 훅을 RSC에서 쓸 수 없어요. 그래서 Supabase도 공식 문서를 App Router 기준으로 전면 개편했고, 미들웨어에서 세션을 갱신하고 쿠키를 주고받는 패턴이 권장 방식이 됐어요.

문제는 이 패턴이 "정확히 따라 해야 동작하는" 구조라는 거예요.

Supabase의 Next.js 클라이언트(`@supabase/ssr` 패키지)는 세 가지 클라이언트를 따로 씁니다.

- `createBrowserClient` — 클라이언트 컴포넌트용
- `createServerClient` — 서버 컴포넌트, Server Action, Route Handler용
- `createServerClient` — 미들웨어용 (같은 함수지만 쿠키 처리 방식이 달라요)

미들웨어에서 쓰는 `createServerClient`는 쿠키를 직접 읽고 쓰는 콜백을 넘겨줘야 해요. 이 콜백이 잘못 구현되면 세션 갱신 자체가 안 되고, 갱신이 안 되면 매 요청마다 "인증 안 됨 → 로그인 페이지로 리다이렉트 → 미들웨어 다시 실행 → 또 인증 안 됨"이 반복되는 거예요.

꾸리 기술 블로그(2026년 4월)에서도 같은 구조를 분석하면서, `getAll`/`setAll` 메서드를 정확히 구현하지 않으면 리프레시 토큰이 갱신되지 않아 루프가 생긴다고 설명하고 있어요.

---

## 2. 무한 루프가 생기는 원인 3가지

### 원인 1: 공개 경로(public route) 예외 처리 누락

가장 흔한 케이스예요. 미들웨어가 `/login` 경로에도 적용되는데, 그 경로에서 "세션 없음 → `/login`으로 리다이렉트"를 실행하면 루프가 생기죠.

```typescript
// ❌ 이렇게 하면 /login도 미들웨어 거쳐서 루프 발생
export async function middleware(request: NextRequest) {
  const { data: { session } } = await supabase.auth.getSession()
  if (!session) {
    return NextResponse.redirect(new URL('/login', request.url))
  }
}

// ✅ 공개 경로는 바로 통과시켜야 해요
const publicPaths = ['/login', '/signup', '/auth/callback']
if (publicPaths.includes(request.nextUrl.pathname)) {
  return NextResponse.next()
}
```

### 원인 2: `matcher` 설정 없이 모든 경로에 미들웨어 적용

`middleware.ts`에 `export const config = { matcher: [...] }`를 안 쓰면 Next.js는 모든 요청(정적 파일 포함)에 미들웨어를 실행해요. `/_next/static/`, `/favicon.ico` 같은 경로에서도 Supabase 세션 체크가 돌면 불필요한 로직이 쌓이고, 간혹 쿠키 처리 충돌이 생겨요.

Supabase 공식 문서 권장 `matcher` 설정은 이거예요.

```typescript
export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
```

### 원인 3: `updateSession` 함수에서 쿠키 `set` 에러 무시

공식 문서에 나온 `updateSession` 구현을 보면 `cookies.set()` 호출 시 `try-catch`로 에러를 잡는 부분이 있어요. 이걸 빼거나 에러를 그냥 throw하면, 세션 갱신이 실패해도 조용히 넘어가서 루프가 생기는 케이스가 있어요.

---

## 3. 어떤 구조가 더 안전할까요?

무한 리다이렉트 루프 트러블슈팅을 할 때 크게 두 가지 접근이 있어요.

| 기준 | 미들웨어 전용 처리 | 미들웨어 + 서버 컴포넌트 이중 확인 |
|------|-------------------|--------------------------------------|
| 세션 갱신 위치 | 미들웨어에서만 | 미들웨어 + 각 레이아웃에서 추가 확인 |
| 루프 발생 위험 | 높음 (설정 하나 잘못 되면 즉시 루프) | 낮음 (서버 컴포넌트에서 2차 방어선) |
| 코드 복잡도 | 낮음 | 중간 |
| 성능 | 빠름 | 약간 더 느림 (세션 체크 두 번) |
| 디버깅 편의성 | 낮음 (미들웨어 로그 보기 어려움) | 높음 (서버 컴포넌트 로그 더 명확) |
| 권장 대상 | 소규모 프로젝트 | 프로덕션 서비스 |

미들웨어 전용으로 처리하면 코드가 간결하지만, 설정 하나가 틀리면 바로 루프가 생겨요. 반면 미들웨어에서 세션 갱신만 하고, 실제 접근 제어는 서버 컴포넌트의 레이아웃에서 한 번 더 확인하는 이중 구조는 루프 위험이 훨씬 낮아요.

실제로 꾸리 블로그 사례에서도 이 이중 구조를 권장하고 있어요. 미들웨어는 "세션 쿠키 갱신"만 담당하고, 리다이렉트 결정은 레이아웃 수준에서 하는 거예요.

**미들웨어 단독 방식:**
- 장점: 코드 짧음, 빠름
- 단점: 공개 경로 누락 시 즉시 루프, 디버깅이 어려움

**이중 확인 방식:**
- 장점: 안전, 디버깅 쉬움
- 단점: 세션 체크가 두 번 돌아서 미세하게 느림

프로덕션 서비스라면 이중 확인 방식을 추천해요. 속도 차이는 체감할 수 없는 수준이고, 루프 한 번 뚫리면 사용자 전부 로그아웃 상태로 막히거든요.

---

## 4. 실전 트러블슈팅 체크리스트

루프가 생겼을 때 순서대로 확인할 사항이에요.

**1단계 — 어느 경로에서 루프가 생기는지 확인**

```typescript
export async function middleware(request: NextRequest) {
  console.log('미들웨어 실행:', request.nextUrl.pathname)
  // ...
}
```

브라우저 네트워크 탭과 터미널 로그를 같이 보면 어떤 경로가 반복되는지 바로 보여요.

**2단계 — 공개 경로 목록 점검**

`/login`, `/signup`, `/auth/callback`이 `publicPaths` 배열에 있는지 확인해요. `/auth/callback`을 빼먹는 경우가 꽤 많아요. OAuth 콜백 URL이 여기서 처리되는데, 이게 막히면 소셜 로그인 자체가 루프에 빠져요.

**3단계 — `updateSession` 반환값 확인**

```typescript
const { supabase, response } = createServerClient(...)
await supabase.auth.getUser() // getSession이 아니라 getUser!
return response // response를 반드시 반환해야 쿠키가 전달돼요
```

`getSession()` 대신 `getUser()`를 쓰는 게 권장 방식이에요. `getSession()`은 서버에서 토큰 검증을 건너뛸 수 있어서 보안상 취약하거든요.

**4단계 — `matcher` 패턴 확인**

정적 파일 경로가 `matcher`에서 제외됐는지 확인해요. 빠트리면 이미지 요청마다 미들웨어가 실행돼요.

---

## 5. 앞으로 뭘 챙겨야 할까요?

Supabase는 2026년 상반기 기준으로 Next.js 통합 문서를 계속 업데이트하고 있어요. 특히 `@supabase/ssr` 패키지의 메이저 업데이트가 있을 때마다 쿠키 처리 API가 바뀌는 경우가 있어서, 프로젝트를 오래 유지한다면 주기적으로 공식 changelog를 확인하는 게 좋아요.

**지금 당장 해볼 것:**
- `middleware.ts`에 `console.log`로 경로 찍어보기
- 공개 경로 목록 다시 확인 (`/auth/callback` 포함됐는지)
- `getSession` → `getUser`로 교체 (보안 + 안정성 모두 좋아짐)
- 미들웨어 역할을 "세션 갱신"으로 한정하고, 리다이렉트는 레이아웃에서 처리

대부분은 설정 문제예요. 복잡한 로직이 아니라 빠진 경로 하나, 잘못된 함수 하나가 원인인 경우가 90%예요. 지금 루프를 겪고 있다면 위 체크리스트를 1번부터 순서대로 돌려보세요. 어느 단계에서 걸리는지 공유해 주시면 더 구체적으로 도움드릴 수 있어요.

---

*참고 자료: [Supabase Auth with Next.js 공식 문서](https://supabase.com/docs/guides/auth/quickstarts/nextjs), [꾸리 블로그 — Next.js middleware.ts로 Supabase 인증 처리하는 방법 (2026.04)](https://www.kko-kkuri.com/2026/04/10/nextjs-middleware-supabase-auth/)*

## 참고자료

1. [Next.js middleware.ts로 Supabase 인증 처리하는 방법 (실전 코드 완전 정리) - 꾸리](https://www.kko-kkuri.com/2026/04/10/nextjs-middleware-supabase-auth/)
2. [Use Supabase Auth with Next.js | Supabase Docs](https://supabase.com/docs/guides/auth/quickstarts/nextjs)


---

*Photo by [Microsoft Copilot](https://unsplash.com/@microsoftcopilot) on [Unsplash](https://unsplash.com/photos/two-women-talking-in-a-kitchen-while-cooking-3c_k7h8YgHw)*
