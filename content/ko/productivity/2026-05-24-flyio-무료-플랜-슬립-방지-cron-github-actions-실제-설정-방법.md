---
title: "Fly.io 무료 플랜 슬립 방지 GitHub Actions cron 실제 설정 방법"
date: 2026-05-24T20:33:33+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "fly.io", "cron", "github", "Python"]
description: "Fly.io 무료 플랜 앱, 15분 비활성 시 슬립→30초 콜드 스타트 문제를 GitHub Actions schedule cron으로 비용 0원에 해결하는 실제 설정법을 다룹니다."
image: "/images/20260524-flyio-무료-플랜-슬립-방지-cron-github-.webp"
technologies: ["Python", "JavaScript", "Node.js", "AWS", "GitHub Actions"]
faq:
  - question: "Fly.io 무료 플랜 슬립 방지 cron GitHub Actions 실제 설정 방법"
    answer: "Fly.io 무료 플랜 슬립 방지 cron GitHub Actions 실제 설정 방법은 .github/workflows/ 디렉토리에 YAML 파일을 생성하고 schedule 트리거에 cron 표현식을 입력해 주기적으로 앱의 헬스체크 엔드포인트에 curl 요청을 보내는 방식입니다. 예를 들어 '*/10 * * * *'으로 설정하면 10분마다 자동 ping이 실행되어 Fly.io 머신이 슬립 상태로 전환되지 않습니다. GitHub Actions 무료 플랜 월 2,000분 한도 내에서 10분 간격이면 월 약 70-100분만 사용하므로 비용 없이 운영할 수 있습니다."
  - question: "Fly.io 무료 플랜 앱 콜드 스타트 시간 얼마나 걸리나요"
    answer: "Fly.io 무료 플랜에서 앱이 슬립 상태로 진입한 후 첫 요청에 응답하는 콜드 스타트 시간은 일반적인 Node.js 또는 Python 기반 앱 기준으로 20-40초 수준입니다. 트래픽이 없으면 약 10-15분 비활성 후 머신이 자동 종료되며, 무료 플랜에서는 auto_stop_machines 옵션을 false로 변경할 수 없어 코드 레벨에서 슬립을 원천 차단하는 것이 불가능합니다."
  - question: "GitHub Actions cron 최소 실행 간격 몇 분인가요"
    answer: "GitHub Actions 공식 문서에 따르면 schedule 트리거의 cron 최소 실행 간격은 5분입니다. 5분 미만으로 설정할 경우 무시되거나 지연 실행될 수 있으며, Fly.io 슬립 방지 용도로는 8-10분 간격이 무료 한도 소진을 피하면서 슬립을 막을 수 있는 현실적인 최적값으로 권장됩니다."
  - question: "Fly.io 슬립 방지 GitHub Actions vs UptimeRobot 뭐가 더 나은가요"
    answer: "UptimeRobot은 설정이 간단하고 별도 코드 작업이 필요 없는 반면, 추가 서드파티 계정을 만들어야 한다는 단점이 있습니다. GitHub Actions 방식은 설정 복잡도는 다소 높지만 이미 GitHub를 사용하는 개발자라면 추가 계정 없이 코드베이스 안에서 모든 설정을 관리할 수 있다는 점에서 코드 친화적인 선택입니다. 두 방법 모두 무료로 사용 가능하므로 기존 스택과의 통합 편의성을 기준으로 선택하면 됩니다."
  - question: "Fly.io 무료 플랜 슬립 방지 cron GitHub Actions 실제 설정 방법에서 헬스체크 엔드포인트 꼭 만들어야 하나요"
    answer: "Fly.io 무료 플랜 슬립 방지 cron GitHub Actions 실제 설정 방법을 적용할 때 별도의 /health 엔드포인트가 없으면 curl 요청 시 404 또는 에러가 반환될 수 있어 엔드포인트를 추가하는 것이 권장됩니다. Express 기준으로 res.status(200).json({ status: 'ok' }) 형태의 가벼운 응답만 반환하면 충분하며, DB 조회 같은 무거운 작업은 포함하지 않는 것이 중요합니다."
---

무료로 배포한 서버가 밤새 잠들어 있었어요. 첫 요청에 30초. 두 번째 방문자는 이미 떠났죠.

Fly.io 무료 플랜을 쓰는 개발자라면 한 번쯤 겪는 상황이에요. 2026년 현재, Fly.io는 무료 티어에서 **트래픽이 없으면 앱을 자동으로 슬립(sleep) 상태**로 전환해요. 공식 문서 기준으로 약 10-15분 비활성 시 머신이 종료되고, 재시작까지 최소 20-30초가 걸려요. 포트폴리오 사이트, 사이드 프로젝트, 데모 앱을 운영하는 개발자들한테 이건 꽤 치명적인 UX 문제거든요.

GitHub Actions의 `schedule` 트리거를 쓰면 이 문제를 **비용 0원**으로 해결할 수 있어요. cron 표현식 하나로 주기적으로 서버를 깨워두는 거예요.

이 글에서는 실제 설정 방법을 데이터와 함께 살펴볼게요:
- Fly.io 슬립 메커니즘의 정확한 작동 방식
- GitHub Actions cron 설정 방법 (실제 코드 포함)
- 슬립 방지 방법별 비용·효과 비교
- 실무에서 주의해야 할 함정들

> **핵심 요약**
> - Fly.io 무료 플랜은 10-15분 비활성 시 자동 슬립되며, 콜드 스타트는 20-30초로 측정된다.
> - GitHub Actions의 `schedule` cron 트리거는 무료 한도(월 2,000분) 내에서 슬립 방지 ping을 자동 실행할 수 있다.
> - 외부 모니터링 서비스(UptimeRobot 등)와 비교 시, GitHub Actions 방식은 설정 복잡도는 높지만 추가 서드파티 계정이 필요 없다는 점에서 우위가 있다.
> - cron 주기를 5분 이하로 설정하면 GitHub Actions 무료 한도를 초과할 수 있어, 8-10분 간격이 현실적인 최적값이다.
> - 2026년 기준 Fly.io 유료 플랜(Pro)에서는 `[fly]` 섹션 `auto_stop_machines = false` 설정으로 슬립 자체를 비활성화할 수 있다.

---

## Fly.io가 앱을 재우는 이유: 슬립 메커니즘 이해하기

Fly.io는 마이크로VM 기반 컨테이너 플랫폼이에요. AWS Lambda처럼 서버리스는 아니지만, 무료 플랜에서는 비용 절감을 위해 **유휴 상태 머신을 자동으로 정지**시키는 기능을 기본으로 켜두고 있어요.

공식 Fly.io 문서(`fly.toml` 설정 기준)에 따르면, `auto_stop_machines` 옵션이 `true`로 설정된 경우 트래픽이 없으면 머신이 종료돼요. 무료 플랜에서는 이 값을 `false`로 바꿀 수 없어요. 유료 플랜 전환 없이는 코드 레벨에서 슬립을 막는 게 불가능한 구조죠.

콜드 스타트 시간은 앱 크기와 리전에 따라 다르지만, 일반적인 Node.js 또는 Python 기반 앱 기준으로 **20-40초** 수준이에요. Fly.io 커뮤니티 포럼의 2026년 1분기 스레드들에서 반복적으로 언급되는 숫자거든요.

슬립을 방지하려면 결국 **주기적으로 HTTP 요청을 보내** 앱이 살아있다고 인식하게 만드는 수밖에 없어요. 이때 쓸 수 있는 선택지가 여럿 있는데, GitHub Actions는 그중 가장 코드 친화적인 방법이에요.

---

## GitHub Actions cron으로 슬립 방지 설정하기

### 기본 구조: workflow 파일 작성

GitHub Actions는 `.github/workflows/` 디렉토리에 YAML 파일을 두는 방식으로 동작해요. `schedule` 트리거를 쓰면 cron 표현식으로 주기 실행이 가능하고요.

아래는 실제 동작하는 슬립 방지 workflow 예시예요:

```yaml
# .github/workflows/keep-alive.yml
name: Fly.io Keep Alive

on:
  schedule:
    - cron: '*/10 * * * *'  # 10분마다 실행

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Fly.io App
        run: |
          curl -s -o /dev/null -w "%{http_code}" https://your-app-name.fly.dev/health
```

`curl` 명령 하나로 앱의 헬스체크 엔드포인트를 호출하면, Fly.io 머신이 활성 상태를 유지해요. 단순하죠.

### cron 표현식 설정 주의사항

GitHub Actions의 cron 스케줄에는 중요한 제약이 있어요.

**UTC 기준**으로 동작해요. 한국 시간(KST)은 UTC+9이기 때문에, 새벽 3시(KST)는 UTC 18시예요. 업무 시간 중심으로 슬립을 방지하고 싶다면 시간대를 계산해서 넣어야 해요.

그리고 GitHub 공식 문서에 따르면 **`schedule` 트리거는 최소 5분 간격만 지원**해요. `*/1`이나 `*/3` 같은 짧은 주기는 무시되거나 지연 실행돼요.

GitHub Actions 무료 플랜은 **월 2,000분**이 한도예요. 10분마다 실행하면 하루 144회, 한 달이면 약 4,320회인데 각 실행이 1분 미만으로 끝나도 합산 시간이 누적돼요. 현실적으로 10분 간격이면 월 70-100분 수준이라 여유가 있어요. 그러나 5분 간격으로 여러 workflow를 동시에 돌리면 한도에 근접할 수 있으니 주의하세요.

### 헬스체크 엔드포인트 추가하기

curl 타깃이 되는 `/health` 엔드포인트가 없으면 404나 에러가 떨어져요. 앱에 가볍게 추가해두는 게 좋아요.

Node.js(Express) 기준:

```javascript
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok', timestamp: new Date().toISOString() });
});
```

응답 크기를 최소화하는 게 포인트예요. DB 조회 같은 무거운 작업은 넣지 않는 게 좋아요.

---

## 슬립 방지 방법 비교: 어떤 걸 골라야 할까요?

세 가지 대표 방법을 나란히 놓고 보면 선택이 쉬워져요.

| 항목 | GitHub Actions cron | UptimeRobot (무료) | Cron-job.org (무료) |
|------|--------------------|--------------------|---------------------|
| **설정 복잡도** | 중간 (YAML 작성) | 낮음 (UI 설정) | 낮음 (UI 설정) |
| **최소 실행 간격** | 5분 | 5분 | 1분 |
| **추가 계정 필요** | ❌ (GitHub만) | ✅ (별도 가입) | ✅ (별도 가입) |
| **무료 한도** | 월 2,000분 | 모니터 50개 | 무제한 (제한적) |
| **알림 기능** | GitHub 이메일 | SMS/이메일 | 이메일 |
| **코드 관리** | ✅ (Git 추적 가능) | ❌ | ❌ |
| **추천 대상** | 개발자/팀 프로젝트 | 빠른 설정 원할 때 | 고빈도 핑 필요 시 |

GitHub Actions 방식의 가장 큰 장점은 **코드베이스 내에서 관리된다**는 거예요. 팀 프로젝트라면 PR로 리뷰하고 Git 히스토리로 추적할 수 있어요. 반면 UptimeRobot은 5분이면 설정이 끝나고, 앱이 다운됐을 때 알림도 바로 오죠. 용도에 따라 골라 쓰는 게 맞아요.

---

## 실무에서 자주 빠지는 함정들

**함정 1: workflow가 실행돼도 앱이 안 깨는 경우**

Fly.io 앱 URL이 틀렸거나, 앱이 배포 안 된 상태면 curl은 그냥 실패해요. `curl`에 `-f` 플래그를 추가하면 HTTP 에러 코드에서 exit code 1을 반환해서 GitHub Actions에서 실패로 표시돼요. 디버깅이 쉬워지죠.

**함정 2: GitHub Actions 스케줄 지연**

GitHub는 `schedule` 트리거가 **수요가 많을 때 최대 수십 분 지연될 수 있다**고 공식 문서에 명시하고 있어요. 정확한 인터벌이 중요한 경우엔 적합하지 않아요. 슬립 방지 용도로는 10-15분 지연이 가끔 있어도 큰 문제가 없어요.

**함정 3: 개인 레포지토리의 Actions 비활성화**

새로 만든 private repo에서 Actions가 기본 비활성화된 경우가 있어요. Settings → Actions → General에서 활성화 상태를 확인해야 해요.

---

## 결론: 설정 10분, 슬립 걱정 0분

- Fly.io 무료 플랜은 15분 내 비활성 시 자동 슬립, 콜드 스타트는 20-40초
- GitHub Actions cron으로 10분 주기 ping을 설정하면 슬립 없이 앱을 유지할 수 있어요
- 월 2,000분 한도 내에서 충분히 동작하고, 코드로 관리된다는 게 팀 프로젝트에서 강점이에요
- 빠른 설정이 우선이라면 UptimeRobot이 더 나아요

앞으로 6-12개월 안에 Fly.io가 무료 플랜 정책을 어떻게 바꿀지는 지켜봐야 해요. 2025년 말 기준 이미 무료 플랜 머신 수 제한을 조정한 전례가 있거든요. 슬립 방지 cron 설정 자체는 플랫폼이 바뀌어도 다른 서비스에 그대로 적용할 수 있는 패턴이에요.

지금 당장 `.github/workflows/keep-alive.yml` 파일 하나 만들어보세요. 설정 시간은 10분. 그리고 다시는 "내 서버가 왜 30초씩 걸리죠?"라는 질문은 안 하게 될 거예요.

Fly.io 이외의 플랫폼에서도 비슷한 슬립 문제를 경험하고 있다면, 어떤 방법으로 해결하고 있는지 댓글로 알려주세요.

## 참고자료

1. [Automating Fly.io Deployments with GitHub Actions](https://cosminirimescu.com/automate-flyio-deployments-github-actions/)
2. [GitHub Action - 나무위키](https://namu.wiki/w/GitHub%20Action)
3. [깃허브 액션(GitHub Actions) 완전 정복 - Miracle's Dev Log](https://miracle-tech.tistory.com/9)


---

*Photo by [Alex Gagareen](https://unsplash.com/@onepilot) on [Unsplash](https://unsplash.com/photos/black-and-silver-car-engine-AapHZdN_1-Y)*
