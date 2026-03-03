---
title: "innerHTML 보안 취약점과 Firefox 148 setHTML() 마이그레이션 가이드"
date: 2026-02-25T20:03:33+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["innerhtml", "sethtml", "firefox", "subtopic-web"]
description: "innerHTML 보안 취약점을 setHTML API로 해결하는 방법을 알아보세요. Firefox 지원 현황과 실제 마이그레이션 코드 예제로 XSS 공격을 차단하고 더 안전한 웹 앱을 구현하세요."
image: "/images/20260225-innerhtml-보안-취약점-sethtml-firef.webp"
technologies: ["JavaScript", "Go", "Java"]
faq:
  - question: "innerHTML XSS 공격 왜 위험한가요"
    answer: "innerHTML은 사용자 입력값을 HTML로 그대로 파싱해 DOM에 삽입하기 때문에, 입력값 안에 악성 스크립트나 이벤트 핸들러가 포함되어 있어도 브라우저가 그냥 실행합니다. OWASP 기준으로 XSS는 2026년 현재도 웹 취약점 Top 3 안에 드는 위협이며, 2013년 Facebook의 수백만 계정 노출 사고도 innerHTML 취약점이 원인이었습니다. 브라우저가 자체적으로 막아주는 구조가 아니라 개발자가 매번 직접 sanitize 처리를 신경 써야 한다는 점이 근본적인 한계입니다."
  - question: "innerHTML 보안 취약점 setHTML Firefox 마이그레이션 어떻게 준비하나요"
    answer: "Firefox 148에서 setHTML()이 정식 지원되면서 innerHTML을 대체하는 마이그레이션을 준비할 때는 코드 한 줄 교체가 아니라 기존 sanitize 로직 전체를 재검토하는 작업이 필요합니다. Sanitizer 객체에 허용할 태그와 속성 목록을 명시하고 element.setHTML(userInput, { sanitizer }) 형태로 전환하되, Chrome과 Safari의 지원이 불완전한 현재 시점에서는 DOMPurify 래퍼를 병행하는 점진적 전환 전략이 권장됩니다."
  - question: "setHTML() vs DOMPurify 차이점 뭔가요"
    answer: "DOMPurify는 JavaScript 레이어에서 문자열을 먼저 정제한 뒤 결과를 innerHTML에 넘기는 방식이라, 실제 HTML 파싱은 브라우저가 이후에 별도로 수행합니다. 반면 setHTML()은 Sanitizer API와 연동해 파싱과 정제가 브라우저 엔진 수준에서 동시에 일어나기 때문에, sanitize된 HTML이 파서를 통과하면서 다시 위험한 형태로 변형되는 mXSS 공격 벡터를 DOMPurify보다 효과적으로 차단할 수 있습니다."
  - question: "innerHTML 보안 취약점 setHTML Firefox 마이그레이션 브라우저 호환성 문제 어떻게 해결하나요"
    answer: "현재 setHTML()과 Sanitizer API를 안정적으로 지원하는 브라우저는 Firefox 148이 사실상 유일하며, Chrome과 Edge는 실험적 플래그가 필요하고 Safari는 아직 미지원 상태입니다. 이 격차를 해소하려면 setHTML() 지원 여부를 런타임에 감지해 지원되는 환경에서는 setHTML()을 쓰고, 그렇지 않은 환경에서는 DOMPurify를 폴백으로 유지하는 조건부 처리 방식이 현실적인 대안입니다."
  - question: "textContent innerHTML 대신 쓰면 XSS 막을 수 있나요"
    answer: "textContent는 입력값을 HTML이 아닌 순수 텍스트로 처리하기 때문에 파싱 자체가 발생하지 않아 XSS를 방지할 수 있습니다. 다만 이 방식은 HTML 태그 자체가 필요 없는 단순 텍스트 출력 상황에만 적용 가능하며, 서식 있는 HTML을 동적으로 삽입해야 하는 경우에는 setHTML()이나 DOMPurify를 활용한 sanitize 처리가 필요합니다."
---

웹 개발자라면 `innerHTML` 한 번도 안 써본 사람 없죠. 딱 한 줄로 HTML을 동적으로 바꿀 수 있는데, 이게 지난 20년간 XSS(크로스사이트 스크립팅) 공격의 가장 흔한 진입로였어요. OWASP에 따르면 XSS는 2026년 현재도 웹 취약점 Top 3 안에 꾸준히 드는 문제예요.

그런데 Firefox 148이 `setHTML()`이라는 새 API를 정식 지원하면서 상황이 달라지기 시작했어요. 단순한 기능 추가가 아니라, DOM에 HTML을 삽입하는 방식 자체를 다시 설계한 거거든요.

이 글에서 다룰 것들이에요.
- `innerHTML`이 왜 보안 취약점의 온상이 됐는지
- `setHTML()`이 구체적으로 뭐가 다른지
- Firefox 148 마이그레이션을 준비하는 팀이 지금 당장 해야 할 것
- 브라우저 간 호환성 현황과 앞으로의 방향

> **핵심 요약**
> - Mozilla는 2026년 2월 Firefox 148에서 `setHTML()` API를 정식 출시했어요. `innerHTML`의 XSS 취약성을 브라우저 엔진 수준에서 차단하는 첫 번째 주요 구현체예요.
> - `innerHTML`은 스크립트를 포함한 모든 HTML을 그대로 파싱해 삽입하지만, `setHTML()`은 Sanitizer API와 연동해 위험한 태그·속성을 파싱 단계에서 제거해요.
> - Chromium 기반 브라우저(Chrome, Edge)는 Sanitizer API를 실험적으로만 지원하고 있어, 현재는 Firefox가 이 기능의 사실상 유일한 안정 환경이에요.
> - 마이그레이션은 코드 한 줄 교체가 아니라 기존 sanitize 로직 전체를 재검토하는 작업이에요.
> - DOMPurify 같은 서드파티 라이브러리 의존도를 낮출 수 있는 기회지만, 브라우저 지원 격차를 고려한 점진적 전환이 필요해요.

---

## innerHTML이 20년간 문제였던 이유

`innerHTML`은 1990년대 후반 Internet Explorer가 처음 도입한 비표준 API예요. 사실상 표준이 되면서 모든 브라우저가 따라갔고, W3C가 공식 스펙에 포함시킨 건 2011년이에요. 그때부터 지금까지 쭉 써온 거죠.

문제는 이 API가 처음 설계될 때 보안보다 편의성을 우선했다는 거예요. `element.innerHTML = userInput`을 쓰면 브라우저는 `userInput`을 HTML로 파싱해서 DOM에 바로 넣어요. 그 안에 `<script>alert('xss')</script>`가 있어도, `<img src=x onerror="악성코드">` 같은 이벤트 핸들러가 있어도 그냥 다 실행해요.

실제로 Meta(당시 Facebook)는 2013년 innerHTML 취약점으로 인한 XSS를 통해 수백만 계정이 위험에 노출되는 사고를 겪었어요. 이후 자체 HTML sanitizer 개발로 방향을 틀었죠. 이 사례가 웹 보안 커뮤니티에서 "innerHTML은 위험하다"는 인식을 굳힌 결정적 계기였어요.

개발자들이 그동안 써온 대응 방식은 두 가지였어요.

**첫째, DOMPurify.** 가장 많이 쓰인 서드파티 라이브러리로, `innerHTML`에 값을 넣기 전에 HTML을 정제하는 방식이에요. 2026년 기준 npm 주간 다운로드가 5,000만 건을 넘을 정도로 사실상 표준 해결책이었죠.

**둘째, `textContent` 우회.** HTML이 아닌 텍스트로만 다룰 때는 `textContent`를 써서 파싱 자체를 피하는 방법이에요.

두 방법 모두 개발자가 매번 신경 써야 하는 구조예요. 깜빡하면 그냥 뚫려요. 브라우저가 아예 막아주는 구조가 아니라는 게 핵심 한계였어요.

---

## setHTML()이 다른 이유: 파싱 전 차단

`setHTML()`의 핵심 아이디어는 단순해요. HTML을 DOM에 넣기 전에 브라우저 엔진이 먼저 정제한다는 거예요.

Mozilla Hacks의 2026년 2월 발표에 따르면, `setHTML()`은 Sanitizer API와 함께 동작해요. `Sanitizer` 객체를 생성하고 허용할 태그·속성 목록을 명시하면 브라우저가 파싱 단계에서 나머지를 걸러내는 구조예요.

```javascript
// 기존 방식 — 위험
element.innerHTML = userInput;

// setHTML() — 파싱 전 차단
const sanitizer = new Sanitizer({
  allowElements: ['p', 'b', 'em', 'a'],
  allowAttributes: { 'a': ['href'] }
});
element.setHTML(userInput, { sanitizer });
```

여기서 중요한 차이가 있어요. DOMPurify는 JavaScript 레이어에서 문자열을 처리한 뒤 결과를 `innerHTML`에 넘겨요. 파싱은 여전히 브라우저가 나중에 해요. 반면 `setHTML()`은 파싱과 정제가 동시에 일어나요. 이론적으로 우회 경로가 훨씬 좁아지는 거예요.

WebPRONews의 분석에 따르면, 기존 DOMPurify가 놓친 mXSS(mutation XSS) 계열 공격 벡터 일부가 `setHTML()`의 파싱 수준 처리로 차단될 수 있어요. mXSS는 sanitize된 HTML이 브라우저 파서를 통과하면서 다시 위험한 형태로 변형되는 공격 방식인데, DOMPurify도 완벽히 막지 못하는 케이스가 있었거든요.

### 브라우저 지원 현황 비교

| 기준 | innerHTML | setHTML() + Sanitizer API |
|------|----------|--------------------------|
| **XSS 차단** | ❌ 없음 (개발자 책임) | ✅ 파싱 단계에서 차단 |
| **Firefox 148** | 지원 | ✅ 정식 지원 (2026.02) |
| **Chrome 121+** | 지원 | ⚠️ 실험적 플래그 필요 |
| **Safari** | 지원 | ❌ 미지원 |
| **Edge** | 지원 | ⚠️ 플래그 필요 |
| **폴리필 가능 여부** | N/A | 제한적 (DOMPurify 래퍼로 부분 대체) |
| **서드파티 의존 제거** | ❌ 불가 | ✅ 가능 (지원 브라우저 한정) |

지금 당장 모든 환경에서 쓸 수 있는 API가 아니에요. Firefox 148이 처음으로 안정 버전 지원을 시작했고, Chrome과 Safari는 아직이에요. 프로덕션에서 `setHTML()`만 믿고 DOMPurify를 지우면 다른 브라우저 사용자는 무방비 상태가 돼요.

### 마이그레이션 전략: 지금 할 수 있는 것

점진적 접근이 현실적이에요. Feature Detection 패턴을 써보세요.

```javascript
if (typeof element.setHTML === 'function') {
  element.setHTML(userInput, { sanitizer });
} else {
  element.innerHTML = DOMPurify.sanitize(userInput);
}
```

이렇게 하면 Firefox 148 사용자는 네이티브 보호를 받고, 나머지 브라우저는 기존 DOMPurify가 커버해요. 두 레이어를 병행하는 전략인 셈이에요.

---

## 현장에서 실제로 뭐가 달라지나

**개발자 입장**에서 `setHTML()` 도입은 코드 한 줄을 바꾸는 게 아니라 sanitize 정책을 재정의하는 일이에요. 기존에 DOMPurify에 넘기던 허용 태그 목록을 `Sanitizer` 객체 설정으로 옮겨야 하는데, 이 과정에서 "우리가 실제로 뭘 허용하고 있었나"를 돌아보게 돼요.

CMS나 위지윅 에디터를 쓰는 프로젝트라면 허용 태그 목록이 수십 개가 넘는 경우도 있어요. 그걸 `Sanitizer` 스펙에 맞게 다시 정리하는 작업이 필요하고, 설정이 잘못되면 오히려 정상적인 콘텐츠가 깨져서 나올 수 있어요. 성공 사례만 있는 게 아니에요.

**보안팀 입장**에서는 긍정적인 변화예요. 서드파티 라이브러리 의존이 줄면 공급망 공격(Supply Chain Attack) 표면이 좁아지는 효과가 있거든요. DOMPurify도 npm 패키지 체계 안에 있기 때문에 이론적으로 패키지 자체가 오염될 수 있어요. 브라우저 네이티브 기능은 그 위험에서 자유로워요.

**비즈니스 입장**에서 Firefox 사용자 비율이 낮다고 무시할 수 없어요. StatCounter 2026년 1월 데이터 기준 Firefox의 전 세계 데스크톱 점유율은 약 7~8%예요. 기업용 B2B 서비스나 개발자 도구 사이트라면 이 비율이 훨씬 높을 수 있어요. 그리고 Chrome이 Sanitizer API 정식 지원을 시작하면 이 논의는 규모가 완전히 달라져요.

---

## 앞으로 6-12개월, 어떻게 흘러갈까

Firefox 148 정식 지원이 이정표가 된 건 맞아요. 하지만 실제 채택이 가속화되는 시점은 Chrome의 정식 지원이 확정되는 때예요. Google이 Sanitizer API 표준화에 적극적인 만큼, 2026년 하반기 중 Chrome 안정 버전 지원 발표가 나올 가능성이 있어요.

변수는 Safari예요. Apple은 새 Web API 채택 속도가 상대적으로 느린 편이라 Sanitizer API가 Safari에 들어오는 시점은 예측이 어려워요. 이 공백이 폴리필 생태계를 얼마나 버티게 할지가 관건이에요.

그럼 지금 팀이 해야 할 건 세 가지예요.

**단기 (1-3개월):**
- 코드베이스에서 `innerHTML` 사용 위치 전체 감사
- Feature Detection 패턴으로 `setHTML()` 점진적 적용 시작
- DOMPurify는 유지하되, 폴백 레이어로 재포지셔닝

**중기 (6-12개월):**
- Chrome 정식 지원 시점 모니터링 후 DOMPurify 의존도 단계적 축소 계획 수립
- Sanitizer API 허용 목록 정책을 조직 보안 가이드라인으로 문서화

`innerHTML` 보안 취약점 문제는 20년 된 숙제예요. `setHTML()`과 Firefox 148은 그 숙제를 브라우저가 떠맡기 시작하는 신호예요. 지금 당장 전면 전환은 현실적이지 않지만, 이 방향으로 코드베이스를 준비하지 않는 팀은 나중에 훨씬 많은 비용을 치르게 될 거예요.

여러분 팀 코드베이스에 `innerHTML`이 몇 군데나 있는지 지금 바로 검색해보세요. 그 숫자가 이 논의의 시급성을 바로 보여줄 거예요.

---

**참고 자료**
- Mozilla Hacks, "Goodbye innerHTML, Hello setHTML: Stronger XSS Protection in Firefox 148" (2026.02)
- WebPRONews, "The Death of innerHTML: How Firefox 148's setHTML() API Rewrites the Rules on Cross-Site Scripting Defense" (2026)
- StatCounter GlobalStats, Desktop Browser Market Share Report (2026.01)
- OWASP Top 10 Web Application Security Risks (2025 Edition)

## 참고자료

1. [Goodbye innerHTML, Hello setHTML: Stronger XSS Protection in Firefox 148 – Mozilla Hacks - the Web d](https://hacks.mozilla.org/2026/02/goodbye-innerhtml-hello-sethtml-stronger-xss-protection-in-firefox-148/)
2. [The Death of innerHTML: How Firefox 148’s setHTML() API Rewrites the Rules on Cross-Site Scripting D](https://www.webpronews.com/the-death-of-innerhtml-how-firefox-148s-sethtml-api-rewrites-the-rules-on-cross-site-scripting-defense/)
3. [SetHTML en Firefox 148: Nueva protección XSS para developers - El Ecosistema Startup](https://ecosistemastartup.com/sethtml-en-firefox-148-nueva-proteccion-xss-para-developers/)


---

*Photo by [Samuel Angor](https://unsplash.com/@sammysays___) on [Unsplash](https://unsplash.com/photos/a-close-up-of-a-smart-device-on-a-table-wOMyMzNpIZU)*
