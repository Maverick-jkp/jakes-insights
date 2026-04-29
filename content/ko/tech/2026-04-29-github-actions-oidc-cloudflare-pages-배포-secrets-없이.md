---
title: "GitHub Actions OIDC로 Cloudflare Pages 배포 secrets 없이 설정하는 법과 삽질 기록"
date: 2026-04-29T20:48:10+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "github", "actions", "oidc", "Terraform"]
description: "GitHub Actions OIDC로 Cloudflare Pages를 배포하면 6개월마다 토큰 갱신, 퇴사자 자격증명 교체 작업이 사라져요. 2024년 말 공식 지원된 OIDC 인증 설정 방법과 실제 삽질 기록을 정리"
image: "/images/20260429-github-actions-oidc-cloudflare.webp"
technologies: ["Terraform", "GitHub Actions", "Cloudflare"]
faq:
  - question: "GitHub Actions OIDC Cloudflare Pages 배포 secrets 없이 설정하는 법"
    answer: "GitHub Actions OIDC를 사용하면 CLOUDFLARE_API_TOKEN을 GitHub Secrets에 저장하지 않고 Cloudflare Pages에 배포할 수 있어요. 워크플로우 파일에 'permissions: id-token: write' 블록을 추가하고, cloudflare/wrangler-action v3.4.0 이상에서 apiToken 파라미터를 생략하면 자동으로 OIDC 인증 흐름이 작동해요. 단, Cloudflare 대시보드에서 해당 GitHub 리포지토리에 대한 OIDC 신뢰 설정을 미리 완료해야 해요."
  - question: "GitHub Actions OIDC 설정 id-token write 권한 없으면 어떻게 되나요"
    answer: "id-token: write 권한이 없으면 GitHub Actions는 OIDC 토큰 자체를 발급하지 않아요. 문제는 이때 'permission denied' 같은 명확한 에러가 아니라 단순 인증 실패로 표시돼 원인 파악이 어려워요. GitHub Actions OIDC Cloudflare Pages 배포 secrets 없이 설정하는 법 삽질 기록에서도 이 부분이 가장 흔한 삽질 포인트로 꼽혀요."
  - question: "wrangler-action OIDC 지원 최소 버전 얼마인가요"
    answer: "cloudflare/wrangler-action에서 OIDC 인증을 사용하려면 v3.4.0 이상이 필요해요. 그 미만 버전에서는 apiToken 없이 실행할 경우 OIDC 흐름을 탐색하지 않아 배포가 실패해요. 워크플로우 파일에서 'uses: cloudflare/wrangler-action@v3'로 명시할 때 실제 설치되는 버전을 반드시 확인해야 해요."
  - question: "GitHub Actions OIDC 장기 API 토큰 대비 보안 장점이 뭔가요"
    answer: "OIDC 방식에서 발급되는 JWT 토큰은 워크플로우 실행 시마다 새로 생성되고 수분 내에 만료되기 때문에 유출되더라도 즉각적인 피해가 없어요. 반면 기존 장기 API 토큰은 한 번 유출되면 만료 전까지 전체 배포 권한이 탈취되고, 여러 리포지토리에 공유된 경우 피해 범위가 더 넓어져요. 또한 팀원 퇴사나 토큰 만료 시마다 자격증명을 교체해야 하는 관리 부담도 사라져요."
  - question: "Cloudflare Pages OIDC silent failure 디버깅 방법"
    answer: "GitHub Actions OIDC Cloudflare Pages 배포 secrets 없이 설정하는 법 삽질 기록에 따르면 OIDC 설정 오류 시 에러 없이 조용히 실패하는 silent failure가 발생할 수 있어요. 디버깅 시 가장 먼저 확인할 사항은 permissions 블록의 id-token: write 누락 여부, wrangler-action 버전이 v3.4.0 이상인지, 그리고 Cloudflare 대시보드에서 해당 리포지토리와 브랜치에 대한 OIDC 신뢰 설정이 올바르게 되어 있는지 순서로 점검하는 게 효율적이에요."
---

`CLOUDFLARE_API_TOKEN`을 GitHub Secrets에 넣고, 6개월마다 토큰 만료 걱정하고, 팀원이 퇴사할 때마다 자격증명 교체하던 시절이 있었어요. 그 과정에서 CI/CD 파이프라인 하나를 운영하는 데 드는 보안 관리 비용이 얼마나 큰지 체감했죠. GitHub Actions OIDC와 Cloudflare Pages를 연결하면 이 번거로움을 통째로 없앨 수 있어요. 삽질 기록까지 포함해서 정리해봤어요.

> **핵심 요약**
> - GitHub Actions OIDC는 단기 토큰을 자동 발급해 장기 API 토큰을 저장하지 않아도 Cloudflare Pages에 배포할 수 있게 해줘요.
> - Cloudflare Workers & Pages는 2024년 말부터 OIDC 기반 인증을 공식 지원하며, `wrangler-action` v3 이상에서 `CLOUDFLARE_API_TOKEN` 없이 배포가 가능해졌어요.
> - secrets 없이 배포하는 방식은 토큰 노출 위험을 제거하지만, OIDC 설정 오류 시 침묵하는 실패(silent failure)가 발생해 디버깅 난이도가 높아요.
> - 올바른 `permissions` 블록과 `id-token: write` 설정이 빠지면 OIDC 토큰 발급 자체가 안 되는데, 이걸 모르고 몇 시간을 날릴 수 있어요.

---

## OIDC가 왜 갑자기 필요해졌나

기존 방식을 먼저 짚어볼게요.

Cloudflare Pages에 GitHub Actions로 배포하려면 전통적으로 `CLOUDFLARE_API_TOKEN`과 `CLOUDFLARE_ACCOUNT_ID`를 GitHub Repository Secrets에 저장해야 했어요. 한번 발급하면 만료 기간이 길고, 여러 리포지토리에 복사해서 쓰는 경우도 많죠. OWASP의 CI/CD Security Risks 보고서(2023)에 따르면 파이프라인 시크릿 노출은 공급망 공격의 주요 진입점 중 하나예요.

문제는 여기서 시작돼요.

- 장기 토큰은 한번 유출되면 즉시 모든 배포 권한이 탈취돼요
- 여러 리포지토리에 같은 토큰을 쓰면 하나가 뚫려도 전체가 위험해져요
- 팀 규모가 커질수록 "누가 이 토큰 관리해?" 문제가 반드시 생겨요

OIDC(OpenID Connect)는 이 구조를 바꿔요. GitHub Actions가 워크플로우 실행마다 단기 JWT 토큰을 발급하고, 이 토큰으로 Cloudflare에 인증해요. 토큰은 몇 분 안에 만료되고, 어디에도 저장되지 않아요.

GitHub는 2021년 말부터 Actions에서 OIDC를 지원했고, Cloudflare는 2024년 하반기에 Workers & Pages OIDC 연동을 공식 문서에 포함했어요. 지금이 처음으로 "현실적으로 쓸 수 있는 시점"인 셈이에요.

---

## 설정 구조: 어떻게 작동하는가

### 전체 흐름 이해하기

OIDC 인증은 세 단계예요.

1. GitHub Actions가 `https://token.actions.githubusercontent.com`에서 JWT를 발급받아요
2. 이 JWT를 Cloudflare에 제출하면, Cloudflare가 GitHub의 공개 키로 서명을 검증해요
3. 검증이 통과되면 임시 자격증명으로 배포 작업이 실행돼요

`cloudflare/wrangler-action` 공식 GitHub 저장소(v3.x 이상)를 보면 `apiToken` 파라미터 없이 OIDC 모드로 실행하는 예시가 나와 있어요. 핵심은 워크플로우 파일에 `permissions` 블록을 명시하는 거예요.

```yaml
permissions:
  contents: read
  id-token: write
```

`id-token: write`가 없으면 GitHub Actions는 OIDC 토큰을 아예 발급하지 않아요. 에러 메시지도 불친절해서 "permission denied" 같은 명확한 오류가 아니라, 단순히 인증 실패로 보여요. 가장 흔한 삽질 포인트예요.

### Cloudflare 쪽 설정

Cloudflare 대시보드에서 Workers & Pages → 특정 프로젝트 → Settings → GitHub Actions OIDC 연동을 설정해야 해요. 여기서 어떤 GitHub 리포지토리, 어떤 브랜치에서 오는 요청을 신뢰할지 정의해요.

주의할 점이 하나 있어요. Cloudflare의 공식 문서(developers.cloudflare.com/workers/ci-cd/external-cicd/github-actions)는 Workers 배포 기준으로 작성된 부분이 많아요. Pages 배포 시에는 `wrangler pages deploy` 커맨드를 쓰는데, OIDC 토큰이 자동으로 전달되는지 여부가 `wrangler-action` 버전에 따라 달라요. **v3.4.0 미만이면 OIDC 미지원**이에요.

### 실제 워크플로우 예시

```yaml
name: Deploy to Cloudflare Pages

on:
  push:
    branches: [main]

permissions:
  contents: read
  id-token: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Cloudflare Pages
        uses: cloudflare/wrangler-action@v3
        with:
          command: pages deploy ./dist --project-name=my-project
          # apiToken 없음 - OIDC 사용
```

`apiToken`을 명시하지 않으면 wrangler-action이 자동으로 OIDC 흐름을 탐색해요. 단, Cloudflare 대시보드에서 해당 리포지토리에 대한 OIDC 신뢰 설정이 미리 되어 있어야 해요.

---

## secrets 방식 vs OIDC 방식: 뭐가 다른가

| 항목 | 기존 secrets 방식 | OIDC 방식 |
|------|-----------------|-----------|
| 토큰 저장 위치 | GitHub Secrets (암호화) | 저장 없음 |
| 토큰 만료 | 수동 관리 필요 | 자동 (분 단위) |
| 유출 시 영향 | 즉각적·광범위 | 이미 만료된 토큰 |
| 설정 복잡도 | 낮음 | 중간 (초기 설정) |
| 팀 규모 확장 | 토큰 공유 문제 | 리포지토리별 독립 |
| 디버깅 난이도 | 낮음 | 높음 (silent failure) |
| `wrangler-action` 버전 요구 | 무관 | v3.4.0 이상 |

두 방식의 차이는 명확해요. secrets 방식은 설정이 단순하지만 장기 자격증명 관리 부담이 남아요. OIDC는 초기 설정에 30분 정도 투자하면, 이후 토큰 관리를 완전히 자동화할 수 있어요.

그리고 OIDC 방식은 Cloudflare 대시보드에서 특정 브랜치나 환경 조건을 걸 수 있어요. "main 브랜치에서만 배포 가능"처럼요. secrets 방식은 워크플로우 YAML 안에서만 조건을 걸 수 있어서, 워크플로우 파일 자체가 변조되면 우회가 가능해요. OIDC는 이 조건이 Cloudflare 서버 측에서 검증되니까, 한 층 더 안전해요.

---

## 삽질 기록: 가장 많이 틀리는 세 곳

**첫째, `permissions` 블록 누락.** 앞서 말했지만 제일 많이 걸려요. Reusable Workflow나 Matrix Job에서 permissions를 호출하는 워크플로우 레벨이 아닌 잡 레벨에만 쓰면 토큰이 안 나와요.

**둘째, `wrangler.toml`에 Pages 프로젝트명이 없을 때.** `wrangler pages deploy` 커맨드에 `--project-name`을 명시하거나, `wrangler.toml`에 `name`을 지정해야 해요. 없으면 "project not found" 오류가 나는데, 인증 문제가 아니라 설정 문제라 헷갈릴 수 있어요.

**셋째, Cloudflare OIDC 신뢰 설정의 Subject 불일치.** GitHub OIDC 토큰의 `sub` 클레임은 `repo:owner/repo-name:ref:refs/heads/main` 형식이에요. Cloudflare 대시보드에서 이 Subject를 정확히 매칭하지 않으면 인증이 거부돼요. 모노레포나 브랜치명에 특수문자가 포함되면 이 값이 예상과 다르게 나와요.

---

## 결론: 지금 바꿀 가치가 있나

답은 "팀이 셋 이상이면 그렇다"예요.

혼자 토이 프로젝트를 운영한다면 기존 secrets 방식도 충분해요. 하지만 리포지토리가 다섯 개를 넘거나, 팀원이 바뀌거나, 보안 감사 대상이 된다면 OIDC 방식으로 전환하는 게 훨씬 깔끔해요.

앞으로 6개월 안에 주시할 변화가 두 가지 있어요.

- Cloudflare는 Terraform 기반 OIDC 신뢰 정책 관리를 로드맵에 포함했어요. 대시보드 클릭 없이 코드로 관리할 수 있게 되면 설정 복잡도가 크게 낮아질 거예요.
- GitHub Actions는 `id-token` 권한의 기본값을 보수적으로 조이는 방향으로 정책을 업데이트 중이에요. 지금 설정하면 이 변화에도 이미 대응된 상태예요.

설정에 막힌다면, Cloudflare 대시보드의 OIDC 설정 화면에서 "Test Token" 기능을 먼저 써보세요. 실제 배포 전에 토큰이 올바르게 검증되는지 확인할 수 있어요. 삽질 시간을 절반으로 줄여줄 거예요.

여러분 팀의 파이프라인에서 지금 가장 오래된 secrets는 언제 만들어진 건가요?

## 참고자료

1. [GitHub Actions · Cloudflare Workers docs](https://developers.cloudflare.com/workers/ci-cd/external-cicd/github-actions/)
2. [How to Deploy a Hugo Site to Cloudflare Pages With Github Actions | Caktus Group](https://www.caktusgroup.com/blog/2025/08/20/how-to-deploy-a-hugo-site-to-cloudflare-pages-with-github-actions/)
3. [GitHub - cloudflare/wrangler-action: 🧙‍♀️ easily deploy cloudflare workers applications using wrangl](https://github.com/cloudflare/wrangler-action)


---

*Photo by [Roman Synkevych](https://unsplash.com/@synkevych) on [Unsplash](https://unsplash.com/photos/blue-and-black-penguin-plush-toy-UT8LMo-wlyk)*
