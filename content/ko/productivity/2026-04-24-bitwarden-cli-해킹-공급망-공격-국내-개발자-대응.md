---
title: "Bitwarden CLI 해킹으로 본 npm 공급망 공격과 국내 개발자 대응"
date: 2026-04-24T20:12:28+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "bitwarden", "cli", "\uacf5\uae09\ub9dd", "Node.js"]
description: "2026년 4월 npm `@bitwarden/cli` 버전 2026.4.0에 백도어가 삽입된 공급망 공격 분석. 국내 개발자가 즉시 취해야 할 패키지 점검 및 대응 절차를 정리했습니다."
image: "/images/20260424-bitwarden-cli-해킹-공급망-공격-국내-개발자.webp"
technologies: ["Node.js", "Docker", "AWS", "GitHub Actions"]
faq:
  - question: "Bitwarden CLI 해킹 공급망 공격 국내 개발자 대응 어떻게 해야 하나요"
    answer: "2026년 4월 npm 레지스트리에서 @bitwarden/cli 패키지 버전 2026.4.0에 백도어가 삽입된 사실이 확인됐으므로, 현재 사용 중인 버전과 해시값을 즉시 점검해야 합니다. CI/CD 파이프라인이나 Docker 빌드 환경에서 해당 패키지를 사용 중이라면, AWS 키·GitHub 토큰·데이터베이스 비밀번호 등 환경 변수에 저장된 자격증명을 전부 교체하는 것이 필수입니다."
  - question: "npm 공급망 공격이란 무엇인가요 개발자가 왜 위험한가요"
    answer: "공급망 공격(Supply Chain Attack)은 신뢰받는 오픈소스 패키지 자체를 탈취해 악성 코드를 심어 배포하는 방식으로, npm install만 실행해도 감염될 수 있어 탐지가 매우 어렵습니다. 이번 Bitwarden CLI 해킹 사례처럼 공격 직후에는 npm audit에도 경고가 뜨지 않아, 개발자가 npm 레지스트리를 무조건 신뢰하는 관행 자체가 취약점이 됩니다."
  - question: "@bitwarden/cli 악성 버전 감염됐을 때 어떤 정보가 유출되나요"
    answer: "악성 버전은 Node.js의 process.env 값, 즉 환경 변수 전체를 외부 C2 서버로 전송하도록 설계됐습니다. CI/CD 파이프라인에서 단 한 번의 빌드 실행만으로도 AWS 키, GitHub 토큰, 데이터베이스 비밀번호 같은 민감한 자격증명이 유출될 수 있으며, 패키지를 제거한 이후에도 자격증명을 교체하지 않으면 피해가 지속됩니다."
  - question: "패키지 버전 고정하면 공급망 공격 막을 수 있나요"
    answer: "버전 고정(lock file)은 자동 업데이트로 인한 감염을 차단하는 첫 번째 방어선이지만, 이번 Bitwarden CLI 해킹 공급망 공격 국내 개발자 대응 사례처럼 정식 버전 네임스페이스 자체가 탈취된 경우에는 버전 고정만으로는 보호가 불충분합니다. 해시 검증(Integrity Hash)을 함께 적용하거나, 규모 있는 팀이라면 프라이빗 레지스트리 미러링까지 도입해 외부 레지스트리 접근을 차단하는 것이 더 안전합니다."
  - question: "TeamPCP Shai-Hulud 캠페인이 뭔가요"
    answer: "TeamPCP는 npm 레지스트리에서 신뢰받는 패키지를 탈취해 백도어를 심는 방식의 공격을 반복하는 해킹 그룹으로, 이번 @bitwarden/cli 공격은 'Shai-Hulud'라는 이름으로 추적되는 세 번째 변종 캠페인입니다. JFrog, OX Security, Endor Labs 세 곳의 보안 연구팀이 공격을 분석했으며, 이전 두 차례 공격보다 기법이 더 정교해진 형태로 재등장한 것이 특징입니다."
aliases:
  - "/tech/2026-04-24-bitwarden-cli-해킹-공급망-공격-국내-개발자-대응/"
  - "/ko/tech/2026-04-24-bitwarden-cli-해킹-공급망-공격-국내-개발자-대응/"

---

2026년 4월, npm 레지스트리에서 조용히 백도어가 배포됐어요. 타깃은 전 세계 개발자들이 일상적으로 쓰는 `@bitwarden/cli` 패키지였고, 피해 규모는 지금도 파악 중이에요. 공급망 공격(Supply Chain Attack)이 다시 한번 현실이 됐습니다.

그냥 "또 해킹이네" 하고 넘기면 안 돼요. Bitwarden CLI 해킹은 단순한 악성코드 배포가 아니라, 신뢰받는 패키지를 탈취해 개발자 환경 자체를 감염 경로로 바꿔버리는 방식이거든요. 국내 개발자 대응이 특히 중요한 이유가 바로 여기 있어요.

> **핵심 요약**
> - 2026년 4월, `@bitwarden/cli` 패키지가 npm에서 악성 버전으로 교체됐으며, 버전 `2026.4.0`에 백도어가 포함된 사실이 JFrog, OX Security, Endor Labs 세 곳의 보안 연구팀에 의해 확인됐어요.
> - 이번 공격은 "Shai-Hulud"라는 이름으로 추적되는 TeamPCP 캠페인의 세 번째 변종으로, 이전 공격에서 쓰인 기법이 더 정교해진 형태로 재등장했어요.
> - 악성 버전은 npm 공식 레지스트리를 통해 배포됐기 때문에, `npm install`만 실행해도 감염될 수 있었어요.
> - 국내 CI/CD 파이프라인이나 Docker 기반 빌드 환경에서 이 패키지를 쓰는 팀이라면, 지금 즉시 버전과 해시값 점검이 필요해요.

---

## 이 공격이 특별한 이유: 배경과 타임라인

공급망 공격은 어제오늘 얘기가 아니에요. 2020년 SolarWinds, 2021년 ua-parser-js, 2022년 node-ipc까지, 개발자들이 매일 쓰는 패키지가 공격 벡터가 된 사례는 꾸준히 늘어왔어요.

그런데 이번 Bitwarden CLI 해킹은 맥락이 좀 달라요. Bitwarden은 오픈소스 패스워드 매니저예요. CLI 버전은 개발팀이 스크립트나 자동화 파이프라인에서 비밀번호나 API 키를 관리할 때 쓰죠. 즉, 이 패키지가 감염됐다는 건 개발자의 자격증명(credential)이 직접 노출될 수 있다는 뜻이에요.

JFrog 보안 연구팀이 최초로 이상 징후를 발견했고, 이후 OX Security와 Endor Labs가 분석을 이어받아 공격의 전체 그림을 그렸어요. 연구팀이 이 캠페인을 "Shai-Hulud"라고 부르는 건, 같은 공격 그룹(TeamPCP)이 이전에도 비슷한 방식으로 두 차례 공격을 성공시킨 전례가 있기 때문이에요. 세 번째 변종인 셈이죠.

공격 방식은 이랬어요. npm 레지스트리에 정식 패키지와 동일한 이름(`@bitwarden/cli`)으로 악성 버전을 올리고, 버전 번호는 `2026.4.0`으로 최신처럼 보이도록 설정했어요. 버전 고정 없이 `latest`나 범위 지정(`^`)으로 의존성을 관리하는 프로젝트는 자동 업데이트 과정에서 감염 버전을 그대로 끌어당기게 돼요.

Endor Labs의 분석에 따르면, 악성 버전에는 시스템 정보와 환경 변수를 외부 서버로 유출하는 코드가 포함됐어요. 환경 변수에는 AWS 키, GitHub 토큰, 데이터베이스 비밀번호 같은 민감한 정보가 들어있을 가능성이 높죠. CI/CD 파이프라인에서 이 패키지를 쓴다면, 빌드 환경 전체가 공격자의 가시권 안에 들어간 거예요.

---

## 공격의 세 가지 핵심 포인트

### 버전 네임스페이스 탈취: 탐지가 어려운 이유

이번 공격이 더 무서운 건 눈에 안 띄기 때문이에요. 악성 패키지의 이름, 배포 채널, 버전 형식이 정식 패키지와 동일해요. `npm audit`은 알려진 취약점 데이터베이스를 기반으로 동작하는데, 공격 직후에는 아직 데이터베이스에 등록되지 않아서 아무 경고도 안 뜨거든요.

OX Security 보고서는 악성 버전이 짧은 시간 안에 실제 다운로드를 기록했다고 밝혔어요. npm 레지스트리를 무조건 신뢰하는 개발자 관행이 그대로 취약점이 된 거예요.

### 환경 변수 유출: 실제 피해 범위

백도어가 주로 노린 건 `process.env` 값이에요. Node.js 환경에서 환경 변수는 애플리케이션 비밀 정보를 전달하는 표준 방식이에요. Bitwarden CLI를 CI/CD에서 쓰는 팀들은 대부분 이 방식으로 마스터 패스워드나 세션 키를 주입하거든요.

공격자는 이 값들을 외부 C2(Command and Control) 서버로 전송했어요. Endor Labs에 따르면, 단 하나의 빌드 실행만으로도 자격증명이 빠져나갈 수 있는 구조였어요. 한 번 유출되면 피해는 패키지 제거 이후에도 계속돼요. 자격증명 자체를 교체하지 않으면요.

### 국내 개발 환경의 노출 지점

국내 개발팀이 특히 주의해야 할 이유가 따로 있어요. 많은 팀이 DevOps 파이프라인에서 비밀번호 관리 도구를 자동화에 엮어 쓰거든요. Bitwarden CLI는 무료 오픈소스이기 때문에, 스타트업부터 중견기업까지 폭넓게 쓰이고 있어요.

GitHub Actions, GitLab CI, Jenkins 파이프라인에서 `@bitwarden/cli`를 의존성으로 직접 참조하는 경우, 또는 Docker 이미지 빌드 과정에서 패키지를 설치하는 경우 모두 위험 지점이에요.

### 패키지 보안 접근법 비교

공급망 공격에 대응하는 방법은 여러 가지예요. 팀 상황에 맞게 고르는 게 중요해요.

| 기준 | 버전 고정(Lock File) | 해시 검증(Integrity Hash) | 프라이빗 레지스트리 미러링 |
|------|---------------------|--------------------------|--------------------------|
| 구현 난이도 | 낮음 | 중간 | 높음 |
| 보호 범위 | 자동 업데이트 차단 | 파일 무결성 검증 | 외부 레지스트리 차단 |
| 유지 비용 | 낮음 (lock 파일 커밋) | 낮음 (자동화 가능) | 높음 (인프라 운영 필요) |
| 제로데이 대응 | ❌ 취약 | ⚠️ 부분적 | ✅ 강함 |
| 국내 팀 현실성 | ✅ 바로 적용 가능 | ✅ 바로 적용 가능 | ⚠️ 규모 있는 팀에 적합 |

버전 고정만으로는 부족해요. 이번 공격처럼 정식 버전 네임스페이스를 탈취하는 경우, 고정된 버전 자체가 악성일 수 있거든요. 해시 검증을 함께 써야 해요. `package-lock.json`의 `integrity` 필드가 변경됐다면, 패키지 내용이 바뀐 거예요. 경고 신호예요.

중장기적으로 규모 있는 팀은 Artifactory나 AWS CodeArtifact 같은 프라이빗 미러를 두고, 검증된 패키지만 내부 레지스트리에 올리는 방식이 가장 강력해요. 단기 비용은 높지만, 공급망 공격 전체 클래스를 막는 구조적 해결책이에요.

---

## 지금 당장 해야 할 것들: 시나리오별 대응

**시나리오 1 — 이미 `@bitwarden/cli`를 쓰고 있는 팀**

가장 먼저 할 일은 버전 확인이에요. `npm list @bitwarden/cli`로 현재 설치된 버전을 봐요. `2026.4.0`이라면 즉시 제거하고, 공식 Bitwarden GitHub 릴리스 페이지에서 확인된 안전한 버전으로 교체해요. 그다음, 해당 패키지가 실행된 환경에서 쓰인 모든 API 키, 토큰, 비밀번호를 교체해요. 유출 여부를 확인하기 전에 먼저 교체하는 게 맞아요.

**시나리오 2 — CI/CD 파이프라인에서 npm 패키지를 자동 설치하는 팀**

파이프라인 로그를 역추적해서 문제 버전이 설치된 시점을 특정해요. 이후 해당 빌드에서 사용된 환경 변수 목록을 뽑고, 전부 교체 대상으로 보는 게 안전해요. 앞으로는 `npm ci` 명령어를 써요. `npm install`과 달리 `package-lock.json`을 엄격하게 따르고, lock 파일 없으면 실행 자체를 막아요.

**시나리오 3 — 아직 Bitwarden CLI를 안 쓰는 팀**

지금 당장 위험에 노출된 건 아니에요. 그런데 이번 사건은 Bitwarden만의 문제가 아니에요. npm 레지스트리에 올라오는 어떤 패키지든 타깃이 될 수 있어요. 의존성 보안 스캔 도구(Dependabot, Snyk, Socket.dev)를 파이프라인에 넣어두는 게 다음 공격을 막는 현실적 방어선이에요.

**앞으로 주시해야 할 신호들:**
- TeamPCP 캠페인의 네 번째 변종 등장 여부 (보안 커뮤니티 모니터링 권장)
- npm 레지스트리의 패키지 게시 정책 강화 발표
- 국내 KISA(한국인터넷진흥원)의 공급망 보안 가이드라인 업데이트

---

## 마무리: 신뢰의 문제예요

이번 사건이 보여주는 건 기술적 취약점이 아니에요. 신뢰의 문제예요. 매일 쓰는 패키지, 매일 돌리는 파이프라인, 매일 당연하게 여기는 의존성 설치 과정. 그 신뢰가 공격면(Attack Surface)이 됐어요.

**핵심 정리:**
- 악성 버전 `2026.4.0`은 환경 변수 유출 코드를 포함하고 있었어요
- 자동 업데이트나 버전 범위 지정을 쓰는 팀이 주 피해 대상이에요
- 버전 고정 + 해시 검증 조합이 가장 현실적 방어책이에요
- 자격증명 교체는 감염 여부 확인 전에 먼저 해야 해요

6~12개월 안에 비슷한 공급망 공격은 더 자주 나올 거예요. npm뿐 아니라 PyPI, RubyGems, Maven 전체가 타깃이 될 수 있어요. 국내 개발자 대응의 출발점은 지금 이 시점에, 내 파이프라인에 어떤 패키지가 들어오는지 한 번 들여다보는 것이에요.

자, 마지막으로 하나만 물어볼게요. 지금 팀의 CI/CD가 어떤 버전의 패키지를 끌어오는지 정확히 알고 있나요?

---

*참고: 이 글은 JFrog Security Research, OX Security, Endor Labs의 공개 보안 분석 보고서를 바탕으로 작성됐어요. 각 연구팀의 원본 보고서 링크는 글 상단 참조를 통해 확인할 수 있어요.*

## 참고자료

1. [The Bitwarden CLI Supply Chain Attack: What Happened and What to Do | Blog | Endor Labs](https://www.endorlabs.com/learn/shai-hulud-the-third-coming----inside-the-bitwarden-cli-2026-4-0-supply-chain-attack)
2. [Shai-Hulud: The Third Coming — Bitwarden CLI Backdoored in Latest Supply Chain Campaign - OX Securit](https://www.ox.security/blog/shai-hulud-bitwarden-cli-supply-chain-attack/)
3. [TeamPCP Campaign Spreads to npm via a Hijacked Bitwarden CLI - JFrog Security Research](https://research.jfrog.com/post/bitwarden-cli-hijack/)


---

*Photo by [Microsoft Copilot](https://unsplash.com/@microsoftcopilot) on [Unsplash](https://unsplash.com/photos/woman-meditating-on-yoga-mat-with-phone-and-drink-G94PWBjH-Yo)*
