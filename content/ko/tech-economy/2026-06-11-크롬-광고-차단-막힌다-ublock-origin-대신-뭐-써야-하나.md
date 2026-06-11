---
title: "크롬 광고 차단 막힌다 - uBlock Origin 대신 뭐 써야 하나"
date: 2026-06-11T23:06:23+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-web", "/ud06c/ub86c /uad11/uace0 /ucc28/ub2e8 /ub9c9/ud78c/ub2e4 - uBlock Origin /ub300/uc2e0 /ubb50 /uc368/uc57c /ud558/ub098"]
description: "2025년 7월 30일 크롬에서 uBlock Origin이 강제 비활성화됐습니다. Manifest V3 전환이 광고 차단 성능에 미치는 영향과 실제 대안 브라우저·확장 프로그램 비교를 정리했습니다."
image: "/images/20260611-크롬-광고-차단-막힌다-ublock-origin-대신.webp"
faq:
  - question: "크롬에서 uBlock Origin이 갑자기 꺼진 이유가 뭔가요?"
    answer: "Google이 확장 프로그램 규격을 Manifest V2에서 V3로 전환하면서 2025년 7월 30일부터 uBlock Origin이 강제 비활성화됐어요. MV3는 광고 차단기가 사용할 수 있는 필터 규칙 수를 대폭 제한해서, 기존 방식으로 설계된 uBlock Origin이 더 이상 작동하지 않게 된 거예요."
  - question: "Firefox로 갈아타면 uBlock Origin 그대로 쓸 수 있나요?"
    answer: "네, Firefox는 MV2를 계속 지원하기 때문에 uBlock Origin이 2024년과 동일하게 작동해요. uBlock Origin 개발자 Raymond Hill 본인도 Firefox를 공식 권고했어요. 북마크와 비밀번호는 Firefox 가져오기 기능으로 한 번에 옮길 수 있어요."
  - question: "Brave에서 uBlock Origin 설치하는 게 실제로 가능한가요?"
    answer: "가능하긴 한데 수동 설치가 필요해요. brave://settings/extensions/v2에서 직접 들어가야 하고, Brave가 자체 백엔드로 MV2를 유지하는 4종 확장 프로그램 중 하나로 uBlock Origin이 포함돼 있어요. 다만 이 지원이 언제까지 유지될지는 Brave 정책에 달려 있어요."
  - question: "uBlock Origin Lite가 기존이랑 얼마나 다른가요?"
    answer: "이름은 비슷하지만 성능 차이가 꽤 커요. 개발자 본인이 'uBO의 자동 대안이 될 수 없다'고 공식적으로 밝혔고, 커스텀 필터 작성이나 동적 차단 규칙 같은 고급 기능은 MV3 제약으로 빠져 있어요. 가끔 광고 차단하는 정도면 쓸 만하지만, 기존 uBO 파워유저라면 바로 한계를 느끼게 돼요."
  - question: "크로미움 계열 브라우저 고집해야 한다면 어떤 선택지가 남아 있나요?"
    answer: "현실적으로는 Brave가 지금 가장 나은 선택이에요. MV2 백엔드를 자체적으로 유지하면서 uBlock Origin 설치를 지원하고 있거든요. AdGuard MV3 버전도 일반 사용자 경험은 괜찮은 편이지만, uBO 수준의 정밀한 트래킹 차단이나 커스터마이징은 기대하기 어려워요."
---

크롬에서 uBlock Origin이 조용히 사라졌어요. 2025년 7월 30일, 아무 팝업도 없이 그냥 비활성화됐죠.

수년간 전 세계 수천만 명이 믿고 쓴 광고 차단기가 하루아침에 작동을 멈췄어요. 이유는 단 하나 — Google이 확장 프로그램 규격을 바꿨기 때문이에요. 그런데 이게 단순한 업데이트 문제가 아니에요. 브라우저 생태계 전체에서 광고 차단이 가능한지 불가능한지를 Google이 결정할 수 있다는 걸 보여준 사건이거든요.

지금 이 질문은 단순한 IT 팁이 아니에요. 어떤 브라우저를, 어떤 철학으로 쓸지에 대한 선택이에요.

**이 글에서 다룰 것들:**
- Manifest V3 전환이 실제로 광고 차단 성능에 어떤 영향을 주는가
- uBlock Origin Lite, AdGuard, Firefox, Brave — 각각의 현실적 한계
- 지금 당장 쓸 수 있는 대안 비교 및 권고

---

> **핵심 요약**
> - 2025년 7월 30일부터 Google Chrome 안정 버전에서 Manifest V2 기반 uBlock Origin이 영구 비활성화됐다.
> - Manifest V3는 광고 차단기가 쓸 수 있는 규칙 수를 제한하고, 코스메틱 필터링 같은 고급 기능을 차단한다.
> - uBlock Origin 개발자 Raymond Hill은 uBlock Origin Lite가 "uBO의 자동 대안이 될 수 없다"고 직접 밝혔다.
> - Firefox는 MV2를 계속 지원하며, Raymond Hill 본인도 "uBlock Origin은 Firefox에서 가장 잘 작동한다"고 인정했다.
> - Brave는 2025년 7월 11일부터 자체 백엔드를 통해 uBlock Origin을 포함한 MV2 확장 프로그램 4종을 수동 설치 방식으로 지원하기 시작했다.

---

## Manifest V3가 뭐길래 이 난리인가

확장 프로그램에는 규격이 있어요. 쉽게 말하면 "브라우저가 허용하는 확장 프로그램의 설계도"예요.

기존 규격이 **Manifest V2(MV2)**, 새 규격이 **Manifest V3(MV3)**예요. Google은 보안과 성능을 이유로 MV3 전환을 추진했어요. 그런데 [AdGuard 공식 블로그](https://adguard.com/ko/blog/ublock-origin-disabled-chrome.html)에 따르면, MV3는 광고 차단 기능에 직접적인 제한을 걸어요.

구체적으로 뭐가 달라지냐면:

- **동적 규칙 수 제한**: MV2에선 수십만 개의 필터 규칙을 실시간으로 적용할 수 있었어요. MV3에선 정적 규칙 최대 3만 개, 동적 규칙 최대 5,000개로 묶여요.
- **코스메틱 필터 약화**: 광고 흔적(빈 공간, 레이아웃 깨짐 등)을 숨기는 기능이 크게 줄어요.
- **네트워크 요청 차단 방식 변경**: 확장 프로그램이 직접 요청을 막는 게 아니라 브라우저 엔진에 "차단 목록"을 넘기는 방식으로 바뀌어요. 더 느리고 덜 정밀해요.

파워유저에겐 치명적인 변화예요. 일반 배너 광고 차단 정도는 어느 MV3 확장 프로그램으로도 되지만, 유튜브 광고 우회·트래킹 스크립트 정밀 차단·커스텀 필터 작성 — 이런 기능들은 MV3에서 눈에 띄게 성능이 떨어지거든요.

타임라인도 알아두면 좋아요:
- **2024년 초**: Chrome Dev·Canary 채널에서 MV2 비활성화 시작
- **2025년 6월**: 기업용 정책(`ExtensionManifestV2Availability`) 유예 기간 종료
- **2025년 7월 30일**: Chrome 안정 버전에서 uBlock Origin 영구 비활성화

이 시점부터 "uBlock Origin 대신 뭐 써야 하나"가 가장 많이 검색된 질문 중 하나가 됐어요.

---

## 대안 비교: 뭐가 진짜 쓸만한가

### uBlock Origin Lite — 이름만 같을 뿐

uBOL은 uBO의 MV3 호환 버전이에요. 이름은 같지만 개발자 Raymond Hill 본인이 "uBO의 자동 대안이 될 수 없다"고 공식 블로그에 못 박았어요.

가끔 광고 차단하는 정도로 쓰는 사람이라면 그럭저럭 괜찮아요. 그런데 커스텀 필터, 특정 도메인 예외 설정, 동적 차단 규칙 같은 기능을 쓰던 사람이라면 직접 써보면 금방 한계를 느끼게 돼요.

### AdGuard MV3 버전 — 첫 번째 주자

[AdGuard](https://adguard.com/ko/blog/ublock-origin-disabled-chrome.html)는 2024년 9월 MV3 호환 버전을 내놨어요. MV3 제약 안에서 가장 빠르게 적응한 광고 차단기예요. 코스메틱 필터도 어느 정도 지원하고, 일반 사용자 경험은 꽤 좋아요. 다만 uBO 수준의 파워유저 커스터마이징은 여전히 어렵고, 무료 버전은 기능이 제한돼요.

### Firefox — Raymond Hill의 공식 권고

Raymond Hill이 직접 "uBlock Origin은 Firefox에서 가장 잘 작동한다"고 밝혔어요. Firefox는 MV2를 계속 지원하고 있어서, uBlock Origin을 설치하면 지금도 2024년과 똑같이 작동해요.

단점은 브라우저 자체를 바꿔야 한다는 거예요. 북마크·확장 프로그램·저장된 패스워드를 마이그레이션하는 게 귀찮을 수 있어요. 그래도 Firefox의 가져오기 기능으로 한 번에 처리되긴 해요.

### Brave — MV2 백엔드를 자체적으로 유지

Brave는 2025년 7월 11일부터 uBlock Origin, AdGuard, uMatrix, NoScript — 이 네 가지에 한해 자체 백엔드로 MV2 지원을 유지하기 시작했어요. `brave://settings/extensions/v2`에서 수동으로 설치해야 하는 번거로움이 있지만, Chromium 기반 브라우저를 포기하지 않고 싶은 사람에겐 지금으로선 가장 현실적인 선택이에요.

다만 Brave의 MV2 지원도 "언제까지"라는 보장은 없어요. 정책 변경 한 번으로 언제든 끊길 수 있다는 점은 알아두어야 해요.

---

### 대안 선택 가이드: 상황별 비교

| 기준 | uBlock Origin Lite | AdGuard (MV3) | Firefox + uBO | Brave + uBO |
|------|--------------------|--------------:|--------------|------------|
| 크롬에서 작동 | ✅ | ✅ | ❌ | ❌ |
| uBO 수준 필터링 | ❌ | △ | ✅ | ✅ |
| 파워유저 커스터마이징 | ❌ | △ | ✅ | ✅ |
| 브라우저 변경 필요 | 없음 | 없음 | Firefox로 전환 | Brave로 전환 |
| 장기 안정성 | △ (MV3 의존) | △ (MV3 의존) | ✅ | △ (정책 변동 가능) |
| 추천 대상 | 캐주얼 사용자 | 일반~중급 사용자 | 파워유저 | Chromium 선호 파워유저 |

---

## 그래서 지금 뭘 해야 하나

상황별로 나눠볼게요.

**크롬을 절대 못 바꾼다면** — AdGuard MV3 버전이 지금 당장 쓸 수 있는 가장 현실적인 선택이에요. uBO만큼은 아니지만, MV3 제약 안에서 가장 잘 만들어진 광고 차단기예요. 유튜브 광고나 배너 차단은 충분히 돼요.

**파워유저라면** — Firefox로 갈아타는 걸 진지하게 고려해야 할 때예요. Raymond Hill의 권고가 단순한 말이 아니에요. MV2 지원 여부가 광고 차단 품질에 직결되니까요.

**Chromium 기반을 포기하지 못하는 파워유저라면** — Brave가 지금 가장 나은 선택이에요. `brave://settings/extensions/v2` 경로를 통한 수동 설치가 필요하고, MV2 지원 지속 여부를 주기적으로 확인하는 게 좋아요.

**시스템 레벨에서 해결하고 싶다면** — Windows/macOS용 AdGuard 앱처럼 브라우저 외부에서 작동하는 광고 차단 솔루션도 있어요. 브라우저 정책 변화에 독립적이라 가장 안정적인 장기 해결책이에요. 다만 유료이고, 설정이 복잡할 수 있어요.

**앞으로 지켜봐야 할 것:**
- **Mozilla의 MV2 지원 기간**: Firefox가 MV2를 얼마나 더 유지할지 공식 발표는 없어요. 현재로선 계속 지원 의사를 밝히고 있지만, 오픈소스 생태계 동향을 주시해야 해요.
- **Brave의 MV2 정책 변화**: 자체 백엔드 지원이 언제까지 유지될지 불명확해요.
- **Opera의 독자 노선**: Opera는 2024년 MV2 독립 지원 지속을 선언했는데, 실제 구현 상태와 업데이트 빈도는 직접 확인해봐야 해요.

---

## 정리: 지금은 브라우저 선택이 광고 차단 수준을 결정한다

핵심을 다시 짚을게요.

- **크롬에서 uBlock Origin은 2025년 7월 30일부로 영구 비활성화됐어요.** MV2 지원 종료가 직접 원인이에요.
- **uBlock Origin Lite는 대체재가 아니에요.** 개발자 본인이 그렇게 말했어요.
- **파워유저의 현실적 선택지는 Firefox 또는 Brave예요.** AdGuard는 일반 사용자에게 적합해요.
- **시스템 수준 광고 차단은 브라우저 정책에 영향받지 않는 유일한 방법이에요.**

결국 이 질문의 답은 "어떤 브라우저를 쓸 것인가"로 귀결돼요. Google이 MV3로 광고 차단 생태계를 제어할 수 있는 구조를 만든 이상, 크롬 안에서의 해결책은 태생적으로 한계가 있어요.

지금 당장 브라우저 변경이 귀찮더라도, 한 번쯤은 생각해볼 필요가 있어요 — 내가 쓰는 브라우저가 나를 위해 일하는지, 아니면 그 반대인지.

---

*이 글에서 인용한 기술 사양 및 날짜는 [AdGuard 공식 블로그](https://adguard.com/ko/blog/ublock-origin-disabled-chrome.html) 및 Raymond Hill의 공개 발언을 기반으로 작성됐어요.*

---

*Photo by [Microsoft Copilot](https://unsplash.com/@microsoftcopilot) on [Unsplash](https://unsplash.com/photos/two-women-talking-in-a-kitchen-while-cooking-3c_k7h8YgHw)*
