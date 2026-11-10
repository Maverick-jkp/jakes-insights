---
title: "오픈소스 슬랙 대안, 소규모 팀 셀프호스팅으로 써볼 만한가 — Cloudflare 활용 비교"
date: 2026-11-11T02:42:00+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-cloud", "/uc624/ud508/uc18c/uc2a4", "cloudflare", "/uc140/ud504/ud638/uc2a4/ud305"]
description: "Slack Pro 50인 연 522만 원 vs VPS 월 2만 원 셀프호스팅. Mattermost·Rocket.Chat·Zulip 2026년 실사용 비교와 Cloudflare 연동 소규모 팀 도입 판단 기준을 정리했어요."
image: "/images/20261111-오픈소스-슬랙-대안-cloudflare-셀프호스팅.webp"
faq:
  - question: "Zulip 셀프호스팅 실제로 VPS 하나에 올라가나요?"
    answer: "2 GB RAM VPS 한 대면 100명 미만 팀은 돌아가요. 사용자 수 상한도 메시지 보관 한도도 없고, SSO도 무료라서 소규모 팀 기준으론 현재 오픈소스 옵션 중 제약이 가장 적어요."
  - question: "Rocket.Chat 무료로 쓰다가 갑자기 막히는 경우가 있나요?"
    answer: "네, 두 가지 벽이 있어요. 동시 접속 100명 제한과 월 푸시 알림 10,000건 상한인데, 10명짜리 팀도 메시지 많이 나누면 알림 한도가 생각보다 빨리 차요. 거기에 MongoDB 때문에 최소 8 GB RAM이 필요해서 싼 VPS엔 애초에 올리기 힘들어요."
  - question: "Mattermost 오픈소스 버전에서 구글 로그인도 이제 안 되나요?"
    answer: "2025년 10월 v11.0 업데이트로 Team Edition에서 SSO가 완전히 빠졌어요. GitHub이나 Google 로그인 하나만 붙이려 해도 지금은 엔터프라이즈 라이선스가 필요해요."
  - question: "Cloudflare로 슬랙 대체 메신저 돌리는 게 현실적인가요?"
    answer: "보조 인프라로 붙이는 건 운영 부담을 줄이는 데 효과가 있어요. 다만 실시간 메시지 영속성이나 대용량 파일 처리는 Cloudflare만으로 완전히 해결이 안 돼서, 메신저 서버 자체를 100% 대체하는 건 아직 프로덕션 수준이 아니에요."
  - question: "50명 팀이 셀프호스팅으로 바꾸면 실제로 얼마나 아끼나요?"
    answer: "Slack Pro 기준 50명이면 연간 580만 원 수준인데, VPS는 월 1.5~4만 원 고정이에요. 팀이 커져도 서버 비용은 그대로라서 1년이면 500만 원 넘게 차이 날 수 있어요. 대신 운영·유지보수 시간은 직접 감당해야 해요."
---

Slack Pro를 50명이 쓰면 연간 약 580만 원이에요. 근데 같은 기능을 월 2~4만 원짜리 VPS 한 대로 돌릴 수 있다면요? 2026년 현재, 개발자 커뮤니티에서 오픈소스 슬랙 대안 논쟁이 다시 뜨거워지고 있어요. Mattermost, Rocket.Chat, Zulip, Matrix/Synapse 중 어디에 올라타야 할지 — 데이터 기반으로 뜯어봤어요.

---

> **핵심 요약**
> - Slack Pro는 50인 팀 기준 연간 약 522만 원이지만, 셀프호스팅은 VPS 월 1.5~4만 원으로 팀 규모에 무관하게 고정 비용이에요.
> - Mattermost v11.0(2025년 10월)에서 오픈소스 Team Edition의 SSO가 제거됐고, Enterprise 무면허 설치는 메시지 10,000건 상한이 생겼어요.
> - Rocket.Chat Community는 월 푸시 알림 10,000건 상한과 동시 접속 100명 제한이 있어 소규모 팀에서도 의외로 금방 벽에 부딪혀요.
> - Zulip은 사용자 수 상한도, 메시지 보관 상한도 없는 유일한 완전 오픈소스 옵션이고, 2026년 4월 버전 12.0에서 E2E 암호화 푸시 알림을 추가했어요.
> - Cloudflare Workers/Pages를 보조 인프라로 붙이면 소규모 팀의 운영 부담이 눈에 띄게 줄지만, 메신저 서버 자체를 Cloudflare만으로 완전 대체하는 건 아직 현실적이지 않아요.

---

## Slack 비용 문제와 2026년 셀프호스팅 흐름

Slack Pro 플랜은 1인당 월 $7.25예요. 50인 팀이면 연간 $4,350, 한화로 580만 원이 훌쩍 넘어가요. 스타트업이나 사이드 프로젝트 팀한테는 꽤 아픈 금액이죠.

그래서 "우리가 직접 올리면 안 돼?"라는 움직임이 개발자 커뮤니티를 중심으로 꾸준히 이어졌어요. SSD Nodes의 2026년 비교 리포트에 따르면, 대표적인 오픈소스 슬랙 대안 네 가지 — Mattermost, Rocket.Chat, Matrix/Synapse, Zulip — 모두 채널, 스레드, 검색, 파일 업로드, 모바일 앱을 지원해요. 겉보기엔 Slack이랑 거의 비슷해요.

2026년 중반엔 Cloudflare 생태계에서 셀프호스팅을 더 쉽게 하려는 오픈소스 프로젝트들도 늘었어요. Cloudflare Workers, Pages, R2, D1을 엮어서 SaaS 도구들을 자체 계정 위에서 돌리는 접근법이 주목받고 있죠. 다만 팀 메신저 같은 무거운 실시간 서비스를 Cloudflare 인프라만으로 완전 대체하는 건 아직 성숙 단계가 아니에요.

Kevin Rose가 X에서 $0 비용의 Cloudflare 기반 Slack 클론 Ember를 오픈소스로 공개한 것도 이 흐름의 연장선이에요. 소규모 팀에서 가볍게 테스트하기엔 흥미로운 시도지만, 프로덕션 운영에 필요한 메시지 영속성이나 대용량 파일 처리는 별도로 설계해야 해요.

---

## 플랫폼별 진짜 한계: 스펙 뒤에 숨은 것들

### RAM과 DB — 숫자보다 현실이 더 가혹해요

벤더 공식 최소 사양을 보면 꽤 차이가 나요.

- **Synapse(Matrix)**: 1 GB RAM (PostgreSQL 별도)
- **Mattermost**: 1~1,000명 기준 2 GB / 단일 vCPU
- **Zulip**: 100명 미만 2 GB, 100명 이상 4 GB + 2 CPU
- **Rocket.Chat**: 최소 8 GB (앱 4 GB + MongoDB 4 GB)

Rocket.Chat의 MongoDB WiredTiger 캐시는 2 GB 환경에서 메시지 히스토리가 쌓일수록 OOM(메모리 부족) 킬이 발생할 수 있어요. 초반엔 멀쩡히 돌아가다가 몇 달 후에 갑자기 서버가 죽는 패턴이에요. 2 GB VPS에 Rocket.Chat을 올리는 건 그냥 시한폭탄을 심는 거예요.

### 푸시 알림 — 셀프호스팅의 가장 큰 함정

셀프호스팅 서버는 iOS/Android 푸시 알림을 직접 보낼 수 없어요. 각 벤더의 클라우드 게이트웨이를 거쳐야 하는데, 여기서 무료 한도가 발목을 잡아요.

- **Rocket.Chat Community**: 월 10,000건 상한
- **Zulip**: 무료 플랜은 10명 이하만, 그 이상은 유료
- **Mattermost**: 무료 테스트 서비스는 SLA 없음, 상업적 운영 불가
- **Matrix/Element**: 메타데이터만 노출하는 게이트웨이 사용, Android는 UnifiedPush로 자체 게이트웨이 구성 가능

10명짜리 팀도 하루 평균 메시지를 나누다 보면 월 10,000건은 금방이에요. 놀랍죠?

### SSO 정책 변화 — 2025년 10월이 분기점이었어요

Mattermost는 2025년 10월 v11.0에서 오픈소스 Team Edition의 SSO(SAML/OIDC)를 완전히 제거했어요. GitHub나 Google 로그인 하나만 붙이려 해도 엔터프라이즈 라이선스가 필요한 구조가 된 거예요.

Rocket.Chat도 버전 9.0.0부터 LDAP/SAML을 Starter+ 유료 플랜으로 제한할 예정이에요. Zulip과 Synapse는 아직 SSO를 무료로 제공하는 몇 안 되는 선택지예요.

---

## 플랫폼 비교: 소규모 팀 기준

| 항목 | Mattermost Team Ed. | Rocket.Chat Community | Zulip | Matrix/Synapse |
|------|-------------------|----------------------|-------|----------------|
| 최소 RAM | 2 GB | 8 GB | 2 GB | 1 GB (DB 별도) |
| 무료 사용자 한도 | 250명 | 동시 100명 | 없음 | 없음 |
| 메시지 보관 한도 | 없음 | 없음 | 없음 | 없음 |
| SSO 무료 여부 | ❌ (v11부터 제거) | 곧 제거 예정 | ✅ | ✅ |
| 푸시 알림 | SLA 없는 무료 | 월 10,000건 | 10명 초과 시 유료 | 메타데이터만 |
| DB | PostgreSQL 15+ | MongoDB 8.0 | PostgreSQL | PostgreSQL |
| 적합한 팀 | GitLab 연동 개발팀 | 50명 이하 소팀 | 비동기 협업 팀 | 외부 연합 필요 팀 |

Zulip이 메시지 상한도, 사용자 상한도 없이 SSO까지 무료로 주는 가장 숨겨진 강자예요. 2026년 4월 릴리즈된 Zulip 12.0은 E2E 암호화 푸시 알림까지 더했어요.

---

## 실전 선택 가이드: 팀 상황별로 다르게 봐야 해요

자, 이제 실제로 어디서 시작해야 하는지 짚어볼게요.

50명 이하 소규모 팀이고 운영 부담을 최소화하고 싶다면 Rocket.Chat Starter를 먼저 고려할 수 있어요. 무료에 사용자 50명 상한, 푸시 알림 무제한이에요. 단, MongoDB 8 GB 요구사양 때문에 VPS 비용이 올라가요.

GitLab을 쓰는 개발팀이라면 Mattermost Team Edition이 맞아요. GitLab CI/CD 파이프라인 알림 연동이 Slack 수준으로 돼요. SSO가 없다는 게 아쉽지만, 개발팀 특성상 이메일/비밀번호 로그인으로 버티는 경우가 많죠.

비동기 협업이 중요하고 팀이 분산된 구조라면 Zulip이 가장 현실적인 답이에요. 스레드 기반 대화 구조가 Slack보다 오히려 체계적이에요. 100명 이상이 되면 VPS 사양을 올려야 하지만, 그 외 제약이 거의 없어요.

**Cloudflare 연동** 측면에서는, 메신저 서버 자체를 Cloudflare로 대체하기보다 Cloudflare Tunnel을 써서 내부 서버를 외부에 안전하게 노출하거나, Workers를 웹훅 처리용으로 붙이는 방식이 현실적이에요. 도메인 설정, SSL 관리, DDoS 방어를 Cloudflare 무료 플랜으로 커버할 수 있거든요.

---

## 앞으로 6개월: 뭘 주시해야 할까요

지금 셀프호스팅 메신저 시장은 라이선스 정책이 조여드는 과도기예요. Mattermost와 Rocket.Chat 모두 무료 티어를 슬금슬금 줄이고 있는 반면, Zulip은 반대 방향으로 가고 있어요.

2027년 상반기까지 주목할 신호 세 가지예요.

첫째, **Rocket.Chat 9.0.0 출시 시점**이에요. LDAP/SAML이 유료로 넘어가면 오픈소스 커뮤니티 반발이 클 거예요. 포크 프로젝트가 나올 가능성도 있어요.

둘째, **Zulip의 클라우드 게이트웨이 정책**이에요. 오픈소스 프로젝트들이 UnifiedPush 같은 자체 게이트웨이를 보편화하면 현재의 10명 초과 유료 제약이 사라질 수 있어요.

셋째, **Cloudflare의 Durable Objects 성숙도**예요. 실시간 웹소켓 처리를 Cloudflare 엣지에서 돌리는 게 안정화되면, Ember 같은 접근이 진짜 프로덕션 수준이 될 수도 있어요.

그럼 지금 당장 넘어가고 싶다면 순서는 이렇게 가세요. Zulip으로 테스트 서버를 올리고 (2 GB VPS면 충분해요), Cloudflare Tunnel로 외부 접속을 열고, 푸시 알림 한도가 문제가 되는 시점에 대안을 찾으면 돼요. 처음부터 완벽한 구성을 목표로 하다가 운영 복잡도에 치여서 Slack으로 돌아가는 팀을 꽤 많이 봤거든요.

오픈소스 슬랙 대안, 셀프호스팅 소규모 팀에서 써볼 만한가라는 질문에 대한 솔직한 답은 이거예요. 써볼 만해요. 단, Zulip부터 시작하고, Cloudflare는 보조 도구로 쓰고, 푸시 알림 정책은 반드시 먼저 확인하세요.

---

*팀에서 실제로 셀프호스팅 메신저를 도입하거나 검토 중이라면, 어떤 부분에서 막혔는지 댓글로 남겨주세요. 다음 편에서 구체적인 설치·운영 가이드로 이어갈게요.*

## 참고자료

1. [Mailflare: Open Source Alternative to Fastmail](https://www.opensourcealternatives.to/item/mailflare)
2. [Kevin Rose on X: "Want your own Slack for $0? I open-sourced Ember. It deploys to @Cloudflare’s free](https://x.com/kevinrose/status/2119814745138315687)
3. [9 Best Self Hosted & Open Source Slack Alternatives in 2026](https://www.mirrorfly.com/blog/slack-alternatives/)


---

*Photo by [Portraits of Modern Dairy](https://unsplash.com/@portraitsofmoderndairy) on [Unsplash](https://unsplash.com/photos/female-dairy-farmer-in-a-cowboy-hat-and-with-a-phone-overlooking-dairy-cows-b9ls9x1Uqlg)*
