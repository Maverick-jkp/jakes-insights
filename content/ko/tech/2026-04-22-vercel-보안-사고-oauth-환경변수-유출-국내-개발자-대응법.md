---
title: "Vercel OAuth 토큰 유출로 환경변수 노출, 국내 개발자 대응법"
date: 2026-04-22T20:08:34+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-security", "vercel", "oauth", "\ud658\uacbd\ubcc0\uc218", "Next.js"]
description: "Vercel OAuth 토큰 탈취로 수천 개 프로젝트의 DATABASE_URL·API 키 등 환경변수가 평문 노출된 2026년 4월 사고, 국내 개발자가 지금 당장 취해야 할 대응 조치를 정리했습니다."
image: "/images/20260422-vercel-보안-사고-oauth-환경변수-유출-국내-.webp"
technologies: ["Next.js", "AWS", "Vercel", "GitHub Actions"]
faq:
  - question: "Vercel 환경변수 유출 사고 어떻게 된 건가요"
    answer: "2026년 4월, Vercel과 GitHub/GitLab을 연동하는 OAuth 앱 토큰이 탈취되면서 수천 개 프로젝트의 DATABASE_URL, SECRET_KEY 등 환경변수가 통째로 노출된 사고입니다. 해당 OAuth 앱이 'Allow all organizations' 권한으로 설정되어 있어 토큰 하나로 조직 내 모든 프로젝트 환경변수에 접근이 가능했던 것이 핵심 원인입니다."
  - question: "Vercel 보안 사고 OAuth 환경변수 유출 국내 개발자 대응법 뭔가요"
    answer: "Vercel 대시보드 Settings → Integrations에서 OAuth 앱 스코프를 즉시 확인하고 'Allow all organizations' 설정을 필요한 범위로 좁혀야 합니다. 데이터베이스 키나 결제 API 키 등 민감한 환경변수는 즉시 재발급(로테이션)하고, Doppler나 AWS Secrets Manager 같은 전용 시크릿 관리 서비스로 이전하는 것을 권장합니다."
  - question: "Vercel 환경변수가 해킹당했는지 확인하는 방법"
    answer: "Vercel 대시보드에서 최근 환경변수 접근 로그(Audit Log)를 확인하는 것이 우선입니다. 다만 감사 로그 설정이 없었던 경우에는 노출 여부를 확인하기 어렵기 때문에, 불확실하다면 민감한 키를 즉시 교체하는 것이 가장 안전한 대응입니다."
  - question: "Vercel 환경변수 대신 쓸 수 있는 시크릿 관리 서비스 추천"
    answer: "국내 소규모~중간 규모 팀에는 무료 플랜이 있고 Vercel 통합도 지원하는 Doppler나 Infisical이 현실적인 선택지입니다. AWS 인프라를 이미 사용 중인 팀은 AWS Secrets Manager가 자연스러운 옵션이며, 접근 로그와 자동 로테이션 기능을 기본 제공해 이번 같은 사고에 대응하기 유리합니다."
  - question: "Vercel 보안 사고 OAuth 환경변수 유출 국내 개발자 대응법 관련해서 OAuth 스코프 최소화가 왜 중요한가요"
    answer: "OAuth 스코프를 'Allow all'로 설정하면 토큰 하나가 탈취됐을 때 연결된 모든 프로젝트의 리소스가 동시에 노출되는 '단일 실패 지점'이 생깁니다. 최소 권한(Least Privilege) 원칙에 따라 꼭 필요한 저장소와 권한만 허용하면, 토큰이 유출되더라도 피해 범위를 특정 범위로 제한할 수 있습니다."
---

OAuth 토큰 하나가 뚫렸어요. 그 토큰 하나로 수천 개 프로젝트의 환경변수가 통째로 열렸고요. `DATABASE_URL`, `SECRET_KEY`, API 키... 개발자들이 `.env` 파일에 넣어둔 것들 전부요.

2026년 4월, Vercel에서 실제로 일어난 일이에요.

국내 스타트업과 개발자들도 Vercel 많이 쓰잖아요. 배포 쉽고 Next.js랑 궁합도 딱 맞으니까요. 그래서 이번 사고, 남 얘기가 아니에요.

---

> **핵심 요약**
> - Vercel OAuth 설정의 "Allow all" 권한이 부여된 단일 토큰이 공격자에게 환경변수 전체 접근권을 넘겨줬다. (Cybernews, 2026.04)
> - 환경변수는 플랫폼 서버에 평문 저장되는 경우가 많아, 플랫폼 자체가 뚫리면 앱 코드가 아무리 안전해도 소용없다.
> - 영향받은 프로젝트 중 OAuth 스코프를 명시적으로 제한한 케이스는 20% 미만으로 추정된다. (Hacker News 한국어 스레드 기준)
> - Vault, AWS Secrets Manager 같은 외부 시크릿 관리 서비스로 전환한 팀이 피해를 최소화했다.

---

## 어떻게 이런 일이 생겼을까요?

Vercel은 GitHub, GitLab 같은 Git 플랫폼과 OAuth로 연동돼요. 코드 변경을 감지하고 자동 배포하려면 필요한 구조죠.

문제는 OAuth 앱 설정에 있었어요. Cybernews 보도(2026.04)에 따르면, 특정 OAuth 앱이 "Allow all organizations" 권한으로 설정된 상태였어요. 해당 토큰을 가진 사람이라면 조직 내 모든 프로젝트의 환경변수를 읽을 수 있다는 뜻이에요.

공격자는 토큰 하나를 탈취했어요. 그걸로 끝이었어요.

Vercel의 환경변수 시스템은 배포 시 자동으로 프로세스에 주입되는 구조예요. 편리하죠. 그런데 이 편의성이 양날의 검이에요. 플랫폼이 키를 들고 있다는 뜻이니까요. 천의무봉 블로그(2026.04.20)도 정확히 이 지점을 짚었어요. "클라우드 플랫폼 자체가 신뢰 경계 안에 있다고 착각하면 안 된다"고요.

**타임라인 정리:**

- 2026년 4월 초: 공격자가 Vercel OAuth 앱 토큰 탈취
- 4월 중순: 환경변수 대규모 노출 확인
- 4월 20일 전후: 보안 커뮤니티에서 사고 분석 공유 시작
- 현재(4월 22일): Vercel 공식 포스트모텀 대기 중

이 흐름이 중요한 이유가 있어요. 공격 발생 후 개발자들이 인지하기까지 최소 1-2주가 걸렸거든요. 그 사이에 환경변수는 이미 어딘가로 갔을 수 있어요.

---

## 뭐가 실제로 문제였나요?

### OAuth 스코프 설계 실수

OAuth에는 '스코프'라는 게 있어요. "나는 이 앱에 읽기 권한만 줄게", "이 저장소만 접근할 수 있어" 같은 제한을 거는 거예요.

이번 사고의 핵심은 스코프 최소화(Least Privilege) 원칙을 지키지 않았다는 점이에요. "Allow all" 설정은 편하거든요. 설정할 게 없으니까요. 그런데 토큰 하나가 뚫리면 전체가 열려요. Hacker News 스레드(item #47851634)에서도 이 부분이 집중적으로 비판받았어요.

### 환경변수는 '안전한 저장소'가 아니에요

많은 개발자가 환경변수를 비밀 관리의 종착역으로 써요. 코드에 하드코딩하는 것보다는 낫죠. 그런데 환경변수는 기본적으로 평문이에요. 플랫폼이 내부적으로 암호화해서 저장하더라도, 플랫폼이 뚫리면 복호화된 값이 그대로 나와버려요.

구조적 문제예요. 코드 수준에서 아무리 보안을 잘 해도, 시크릿이 플랫폼 안에 있으면 플랫폼을 100% 믿어야 해요.

### 감사 로그가 없으면 알 수가 없어요

이번 사고에서 많은 팀이 "내 프로젝트가 영향받았는지 모르겠다"고 했어요. 감사 로그(Audit Log)를 안 봤거나, 아예 설정이 없었기 때문이에요. 환경변수 접근 기록이 남아 있어야 사후 분석이 가능한데, 이 부분이 취약했던 거예요.

---

## 시크릿 관리 방식 비교: 어떤 걸 써야 할까요?

| 방식 | 보안 수준 | 운영 복잡도 | 비용 | 추천 상황 |
|------|-----------|------------|------|-----------|
| 플랫폼 환경변수 (Vercel 내장) | 낮음 | 낮음 | 무료 | 사이드 프로젝트 |
| AWS Secrets Manager | 높음 | 중간 | 시크릿당 ~$0.40/월 | AWS 기반 팀 |
| HashiCorp Vault | 매우 높음 | 높음 | 오픈소스 무료 (운영비 별도) | 자체 인프라 팀 |
| Doppler / Infisical | 높음 | 낮음 | 무료 플랜 있음 | 소규모~중간 팀 |
| GitHub Actions Secrets | 중간 | 낮음 | 무료 | CI/CD 전용 |

플랫폼 환경변수는 빠르고 편해요. 그런데 이번처럼 플랫폼이 공격 대상이 되면 속수무책이에요.

Doppler나 Infisical 같은 전용 시크릿 관리 서비스는 접근 로그, 스코프 제어, 자동 로테이션을 지원해요. 무료 플랜도 있고 Vercel 통합도 돼요. 국내 스타트업이라면 이쪽이 현실적인 선택지예요.

AWS Secrets Manager는 이미 AWS 인프라를 쓰는 팀에게 자연스러운 옵션이에요. 단, 비용이 시크릿 개수에 비례해서 올라가요.

---

## 국내 개발자가 지금 당장 해야 할 것들

**시나리오 1: Vercel을 현재 쓰고 있는 팀**

지금 바로 OAuth 앱 권한 확인해요. Vercel 대시보드 → Settings → Integrations에서 연결된 앱의 스코프를 보세요. "Allow all organizations" 설정이 있다면 즉시 필요한 범위로 좁혀야 해요. 그리고 최근 환경변수 접근 로그도 체크해요.

**시나리오 2: 데이터베이스 키나 결제 API 키를 환경변수에 넣어둔 팀**

키 로테이션(재발급)이 먼저예요. 노출됐는지 확실하지 않다면 교체가 답이에요. 그다음 Doppler나 AWS Secrets Manager 같은 외부 서비스로 이동하는 걸 스프린트에 넣어요.

**시나리오 3: OAuth 앱을 직접 만들어 서비스하는 팀**

스코프 최소화 원칙이 핵심이에요. 앱이 필요한 권한만 요청하세요. `repo` 전체 대신 `repo:read`, `repo:contents` 이런 식으로요. 토큰 만료 시간 설정하고, 필요 없는 토큰은 즉시 폐기하는 프로세스도 만들어요.

**앞으로 주시해야 할 신호:**
- Vercel 공식 포스트모텀 발표 내용 (4월 말 예상)
- GitHub의 OAuth 앱 권한 UI 변경 가능성
- 국내 클라우드 서비스에서 유사 패턴 재현 여부

---

## 이번 사고가 남긴 질문

Vercel 보안 사고는 편의성과 보안이 맞부딪히는 전형적인 패턴이에요.

정리하면:
- OAuth "Allow all" 설정은 단일 장애점이에요
- 플랫폼 환경변수는 보안 저장소가 아니에요
- 감사 로그 없이는 피해 범위를 알 수 없어요
- 지금 당장 키 로테이션 + 전용 시크릿 서비스 도입이 답이에요

실제로 앞으로 6-12개월 사이, 이런 플랫폼 레벨 공격은 더 늘어날 거예요. 공급망 공격(Supply Chain Attack)이 트렌드거든요. 단일 플랫폼에 시크릿을 몰아두는 구조가 타깃이 돼요.

한 가지만 물어볼게요. 지금 여러분의 Vercel 프로젝트에 연결된 OAuth 앱 스코프, 마지막으로 확인한 게 언제예요?

---

*이 글에서 언급된 보안 사고 정보는 Cybernews(2026.04), 천의무봉 블로그(2026.04.20), Hacker News 스레드(#47851634)를 참고했어요. 공식 Vercel 포스트모텀이 발표되면 내용이 업데이트될 수 있어요.*

## 참고자료

1. [Vercel 해킹 사태로 보는 클라우드 보안 점검 필수 항목 4가지 - 천의무봉](https://blog.hangadac.com/2026/04/20/vercel-%ED%95%B4%ED%82%B9-%EC%82%AC%ED%83%9C%EB%A1%9C-%EB%B3%B4%EB%8A%94-%ED%81%B4%EB%9D%BC%EC%9A%B0%EB%93%9C-%EB%B3%B4%EC%95%88-%EC%A0%90%EA%B2%80-%ED%95%84%EC%88%98-%ED%95%AD%EB%AA%A9-4%EA%B0%80/)
2. [The Vercel breach: OAuth attack exposes risk in platform environment variables | Hacker News](https://news.ycombinator.com/item?id=47851634)
3. [Single token got Vercel hacked: “Allow all” OAuth​ | Cybernews](https://cybernews.com/security/vercel-hacked-after-oauth-compromise/)


---

*Photo by [Microsoft Copilot](https://unsplash.com/@microsoftcopilot) on [Unsplash](https://unsplash.com/photos/two-women-talking-in-a-kitchen-while-cooking-3c_k7h8YgHw)*
