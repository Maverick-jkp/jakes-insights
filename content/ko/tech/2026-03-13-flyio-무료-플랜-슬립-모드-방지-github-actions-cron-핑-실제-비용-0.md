---
title: "Fly.io 무료 플랜 슬립 모드 방지: GitHub Actions cron 핑으로 실제 비용 0원 유지하는 방법"
date: 2026-03-13T19:59:09+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "fly.io", "github", "actions", "GitHub Actions"]
description: "Fly.io 무료 플랜 슬립 모드로 인한 5~15초 콜드 스타트, GitHub Actions cron으로 5~10분 간격 HTTP 핑을 보내 완전히 차단하세요. 추가 비용 0원으로 항상 깨어있는 앱을 유지하는"
image: "/images/20260313-flyio-무료-플랜-슬립-모드-방지-github-ac.webp"
technologies: ["GitHub Actions"]
faq:
  - question: "Fly.io 무료 플랜 슬립 모드 방지 GitHub Actions cron 핑 실제 비용 0원 유지 방법이 뭔가요?"
    answer: "Fly.io 무료 플랜 슬립 모드 방지 GitHub Actions cron 핑 실제 비용 0원 유지 방법은 `.github/workflows` 폴더에 YAML 파일 하나를 추가해 10~15분마다 앱에 HTTP 요청을 자동 전송하는 것입니다. GitHub Actions의 `schedule` 이벤트는 공개 리포지토리 기준 무제한 무료로 제공되며, 비공개 리포지토리도 월 2,000분 한도 내에서 15분 간격으로 설정하면 추가 비용 없이 운영 가능합니다."
  - question: "Fly.io 앱 접속할 때 10초 이상 로딩 되는 이유"
    answer: "Fly.io Hobby Plan(무료 티어)은 약 10~15분간 HTTP 요청이 없으면 컨테이너를 자동으로 슬립 상태로 전환하기 때문입니다. 이후 첫 요청이 들어오면 컨테이너를 다시 깨우는 콜드 스타트가 발생하며, 이 과정에서 보통 5~15초의 응답 지연이 생깁니다."
  - question: "GitHub Actions cron 최소 실행 간격 얼마나 되나요"
    answer: "GitHub Actions의 cron 스케줄은 최소 5분 간격이 권장 하한선입니다. Fly.io 슬립 모드 방지 목적으로는 15분 간격이 가장 현실적인데, 하루 96회 실행 기준 월 약 1,440~2,880분으로 비공개 리포지토리의 무료 한도(월 2,000분) 안에서 안정적으로 운영할 수 있습니다."
  - question: "UptimeRobot vs GitHub Actions 슬립 모드 방지 어떤 게 더 나은가요"
    answer: "UptimeRobot은 별도 코드 없이 GUI로 빠르게 설정할 수 있지만 GitHub 인프라만큼 안정성이 보장되지 않고 무료 플랜에서 SMS 알림 등 일부 기능이 제한됩니다. 반면 GitHub Actions는 이미 리포지토리를 사용하는 개발자라면 별도 계정 없이 기존 인프라 안에서 해결할 수 있어 Fly.io 무료 플랜 슬립 모드 방지 GitHub Actions cron 핑 실제 비용 0원 유지 방법으로 가장 현실적인 선택입니다."
  - question: "fly.toml auto_stop_machines false 설정하면 비용 발생하나요"
    answer: "`fly.toml`에서 `auto_stop_machines = false`를 지정하면 슬립 모드 없이 앱을 항상 실행 상태로 유지할 수 있는 근본적인 해결책입니다. 다만 이 옵션은 일부 플랜에서 추가 비용이 발생할 수 있어 반드시 본인 플랜 조건을 확인해야 하며, 비용 부담 없이 해결하려면 GitHub Actions cron 핑 방식이 더 안전한 대안입니다."
---

Fly.io 무료 플랜으로 앱을 올렸는데, 다음 날 접속하면 10초씩 멈추는 경험. 한 번쯤 해봤죠? 슬립 모드 때문이에요. 그런데 이걸 GitHub Actions cron 핑 하나로 완전히 막을 수 있어요. 추가 비용 없이.

> **핵심 요약**
> - Fly.io 무료 플랜은 일정 시간 트래픽이 없으면 컨테이너를 자동으로 슬립 상태로 전환하며, 첫 요청 응답까지 5~15초의 콜드 스타트가 발생해요.
> - GitHub Actions의 `schedule` 이벤트(cron)를 사용하면 **완전 무료**로 5~10분 간격 HTTP 핑을 보낼 수 있어요.
> - 2026년 현재 Fly.io 무료 티어(Hobby Plan)는 월 3달러 크레딧 + 소형 VM을 제공하며, 핑 방식으로 슬립 모드 없이 유지해도 추가 청구는 없어요.
> - 대안으로 UptimeRobot, Render 등이 있지만 무료 한도와 제약이 있어 GitHub Actions 방식이 개발자에게 가장 현실적인 선택이에요.

---

## Fly.io 슬립 모드가 생기는 이유

Fly.io는 도커 컨테이너를 몇 분 만에 전 세계 엣지 노드에 배포할 수 있는 게 강점이에요. 그래서 사이드 프로젝트나 포트폴리오 서버를 띄워두는 개발자들 사이에서 특히 인기가 높죠.

문제는 슬립 모드예요.

Hobby Plan(무료 티어)은 일정 시간 HTTP 요청이 없으면 앱을 자동으로 일시 정지시켜요. 정확한 기준은 공식 문서에 명시되어 있진 않지만, 커뮤니티 경험 기준으로 **보통 10~15분 비활성 상태** 이후 슬립 상태로 진입해요. 이후 첫 요청이 들어오면 컨테이너를 다시 깨우는 콜드 스타트가 발생하고, 보통 5~15초 딜레이로 이어지는 거예요.

포트폴리오 사이트나 API 서버를 이런 상태로 면접관이나 클라이언트에게 보여주면 첫인상이 영 좋지 않아요. 실제로 Reddit r/webdev에서도 "슬립 모드 때문에 Fly.io를 포기하고 Render로 갔다"는 사례가 종종 올라와요. 그런데 방법은 있어요. 그것도 공짜로.

---

## GitHub Actions cron 핑: 작동 원리와 설정법

핵심 아이디어는 단순해요. 앱이 잠들기 전에 주기적으로 HTTP 요청을 보내면 돼요.

GitHub Actions는 `schedule` 이벤트로 cron 문법을 지원해요. 리포지토리에 워크플로 파일 하나를 추가하면 끝이에요. GitHub이 지정한 주기마다 자동으로 실행해 주거든요.

아래가 실제 설정이에요.

```yaml
# .github/workflows/keep-alive.yml

name: Keep Fly.io Alive

on:
  schedule:
    - cron: '*/10 * * * *'  # 10분마다 실행

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Fly.io app
        run: curl -f https://your-app.fly.dev/health || echo "Ping failed"
```

이게 전부예요. 10분마다 GitHub 서버가 여러분 앱에 GET 요청을 보내는 거예요. 앱 입장에서는 트래픽이 들어온 거니까 슬립 상태로 안 넘어가요.

몇 가지 포인트가 있어요.

- **`/health` 엔드포인트**: 앱에 별도 헬스체크 라우트를 만들어두면 좋아요. 단순히 `200 OK`만 반환하면 돼요. 없으면 루트 경로(`/`)를 써도 되는데, 렌더링 비용이 들 수 있어요.
- **cron 간격**: GitHub Actions의 cron은 최소 5분 간격이 권장 하한이에요. 10분 간격이면 월 약 70~140분 정도로 충분히 여유 있어요.
- **`-f` 플래그**: curl에 `-f` 옵션을 주면 HTTP 에러 코드 발생 시 실패로 처리해요. 앱이 다운됐을 때 알아차릴 수 있어요.

---

## 슬립 모드 방지 방법 비교: 어떤 게 진짜 0원인가

| 방법 | 비용 | 설정 난이도 | 신뢰도 | 주의사항 |
|------|------|------------|--------|---------|
| **GitHub Actions cron** | 무료 (월 2,000분 한도) | 낮음 (YAML 1개) | 높음 | 한도 초과 시 유료 |
| **UptimeRobot** | 무료 (5분 간격, 50개 모니터) | 매우 낮음 | 중간 | 무료 플랜은 SMS 알림 없음 |
| **Fly.io Machines API 직접 설정** | 무료 ~ 유료 | 높음 | 높음 | `auto_stop = false` 옵션 필요 |
| **Render 무료 플랜** | 무료 | 낮음 | 낮음 | 15분 슬립, Fly.io보다 느림 |
| **Fly.io 유료 플랜 업그레이드** | 월 $5~ | 없음 | 매우 높음 | 슬립 없음, 가장 간단 |

결국 세 가지 선택지로 압축돼요.

**GitHub Actions cron**은 이미 리포지토리가 있는 개발자에게 가장 자연스러운 방법이에요. 별도 계정이나 서비스 없이 기존 인프라 안에서 해결되거든요. 월 2,000분 무료 한도는 개인 프로젝트에선 넘기기 어려운 수준이에요.

**UptimeRobot**은 코딩 없이 GUI로 설정 가능하다는 게 장점이에요. 빠르게 세팅하고 싶을 때 적합하지만, GitHub 인프라만큼 안정성이 보장되진 않아요.

**`fly.toml`에서 `auto_stop_machines = false`를 지정**하는 방법도 있어요. 앱 자체 설정이라 가장 근본적인 해결책이지만, 일부 플랜에서는 비용이 발생할 수 있어서 확인이 필요해요.

---

## 실제 비용 계산과 장기 유지 전략

GitHub Actions 무료 한도는 공개 리포지토리의 경우 **무제한**, 비공개 리포지토리는 **월 2,000분**이에요. 핑 워크플로는 한 번 실행에 약 20~30초 걸려요. 10분 간격으로 돌리면 하루 144회, 한 달에 약 4,320회예요. 1회당 30초면 월 약 2,160분으로 한도를 살짝 넘어요.

그래서 **15분 간격**을 추천해요. 하루 96회, 월 2,880회, 30초 기준 1,440분으로 한도 안에 들어와요. Fly.io 슬립 진입 기준이 10~15분이니, 15분 간격 핑도 실제로 충분히 잘 작동해요.

```yaml
cron: '*/15 * * * *'  # 15분마다 - 무료 한도 최적
```

참고로 공개 리포지토리로 전환하면 Actions가 무제한이에요. 포트폴리오 프로젝트라면 어차피 공개 리포지토리일 가능성이 높으니, 이 경우엔 5분 간격도 문제없어요.

---

## 앞으로 주목할 것들

지금 당장은 GitHub Actions cron + Fly.io 조합이 개인 개발자에게 가장 합리적인 선택이에요. 다만 몇 가지 변수가 있어요.

- **Fly.io 슬립 정책 변경**: Fly.io는 2025년 초 Machines API 정책을 한 차례 바꿨어요. 무료 플랜의 슬립 모드 기준이 바뀔 수 있으니 공식 문서를 주기적으로 확인하세요.
- **GitHub Actions 한도 정책**: Microsoft가 Actions 무료 한도를 조정한 사례가 있어요. 비공개 리포지토리 사용자는 정책 변경을 주시해야 해요.
- **대안 플랫폼 성장**: Railway, Render, Koyeb 등 유사 플랫폼이 무료 티어를 강화하는 추세예요. 슬립 모드 없는 무료 플랜이 등장하면 판이 바뀔 수도 있어요.

결론은 간단해요.

- `.github/workflows/keep-alive.yml` 파일 하나 추가
- cron을 `*/15 * * * *`로 설정
- 앱 URL 넣고 커밋

이게 전부예요. 복잡하게 생각할 필요 없어요. 지금 당장 워크플로 파일 하나 만들어보세요.

---

*이 글에서 다룬 Fly.io 무료 플랜 정책과 GitHub Actions 한도는 2026년 3월 기준이에요. 공식 문서([fly.io/docs](https://fly.io/docs), [docs.github.com/actions](https://docs.github.com/en/actions))에서 최신 정보를 확인하세요.*

## 참고자료

1. [Automating Fly.io Deployments with GitHub Actions](https://cosminirimescu.com/automate-flyio-deployments-github-actions/)
2. [도커 컨테이너 5분 만에 무료로 배포하기(feat. fly.io) - 44BITS](https://www.44bits.io/ko/post/docker-container-deploy-in-5-minitues-with-fly-io)
3. [r/webdev on Reddit: Simple and reliable infra for my web app - render, fly, versel or coolify?](https://www.reddit.com/r/webdev/comments/1l23vrt/simple_and_reliable_infra_for_my_web_app_render/)


---

*Photo by [Pedro Henrique Santos](https://unsplash.com/@phcsantos) on [Unsplash](https://unsplash.com/photos/brown-and-black-guitar-hero-controller-ACS_PhO_iZI)*
