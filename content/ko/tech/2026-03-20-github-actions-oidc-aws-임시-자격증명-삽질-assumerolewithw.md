---
title: "GitHub Actions OIDC AWS 임시 자격증명 AssumeRoleWithWebIdentity 403 원인과 해결"
date: 2026-03-20T20:00:43+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "github", "actions", "oidc", "AWS"]
description: "GitHub Actions OIDC로 AWS 임시 자격증명을 발급할 때 만나는 AssumeRoleWithWebIdentity 403 에러, 원인은 대부분 IAM 신뢰 정책 조건 3가지 중 하나예요. CI/CD 키 유출 사고 40%를 막는 설정법"
image: "/images/20260320-github-actions-oidc-aws-임시-자격증.webp"
technologies: ["AWS", "GitHub Actions", "Rust"]
faq:
  - question: "GitHub Actions OIDC AssumeRoleWithWebIdentity 403 에러 원인이 뭔가요"
    answer: "GitHub Actions OIDC AWS 임시 자격증명 삽질에서 AssumeRoleWithWebIdentity 403 해결의 핵심은 세 가지 원인을 확인하는 것입니다. 워크플로 파일에 `id-token: write` 권한 누락, IAM 신뢰 정책의 `sub` Condition 오류, IAM OIDC Provider의 Audience 값 혼동이 가장 흔한 원인입니다. 이 세 가지를 순서대로 점검하면 대부분 해결됩니다."
  - question: "GitHub Actions OIDC 설정할 때 id-token write 권한 왜 필요한가요"
    answer: "`id-token: write` 권한은 GitHub Actions 워크플로가 OIDC 토큰(JWT)을 발급받기 위해 반드시 필요한 설정입니다. 이 권한이 없으면 AWS STS에 전달할 토큰 자체가 생성되지 않아 `configure-aws-credentials` 단계에서 `Credentials could not be loaded` 에러가 발생합니다. 에러 메시지만으로는 권한 문제임을 바로 알기 어렵기 때문에 놓치기 쉬운 원인입니다."
  - question: "AWS IAM OIDC Provider Audience 값 sts.amazonaws.com으로 설정하는 이유"
    answer: "GitHub Actions OIDC AWS 임시 자격증명 설정 시 IAM OIDC Provider의 Audience 값은 반드시 `sts.amazonaws.com`으로 설정해야 합니다. `token.actions.githubusercontent.com`은 Provider URL에 들어가는 값이며 Audience에 그대로 쓰면 AssumeRoleWithWebIdentity 403 에러가 발생합니다. 두 값의 역할이 다르기 때문에 혼동하지 않도록 주의해야 합니다."
  - question: "IAM 신뢰 정책 sub 조건에서 StringEquals와 StringLike 차이"
    answer: "`StringEquals`는 정확한 문자열 일치만 허용하며 와일드카드(`*`)가 작동하지 않습니다. 반면 `StringLike`는 와일드카드 패턴 매칭을 지원하므로 여러 브랜치나 경로를 유연하게 허용할 때 사용합니다. 와일드카드를 포함한 값을 `StringEquals`에 넣으면 조건이 절대 매칭되지 않아 403 에러가 발생합니다."
  - question: "GitHub Actions OIDC environment 사용할 때 신뢰 정책 sub 형식이 다른가요"
    answer: "네, 워크플로에서 `environment`를 지정하면 GitHub OIDC 토큰의 `sub` 클레임이 `repo:org/repo:environment:production` 형태로 생성됩니다. 브랜치 기반 조건인 `ref:refs/heads/main` 형식과는 완전히 다르기 때문에 신뢰 정책의 Condition도 실제 사용 방식에 맞게 별도로 작성해야 합니다. 환경 기반과 브랜치 기반을 혼용할 경우 `StringLike`와 와일드카드를 활용하되 보안 범위를 최소화하는 것이 좋습니다."
---

`AssumeRoleWithWebIdentity` 에러 앞에서 두 시간째 멈춰있다면, 이 글이 그 삽질을 끝내 줄 거예요.

AWS IAM 자격증명을 GitHub Secrets에 하드코딩하는 건 2026년 기준 보안 감사에서 즉시 지적받는 패턴이에요. GitHub Advisory Database에 따르면, 노출된 AWS 액세스 키 관련 사고 중 40% 이상이 CI/CD 파이프라인의 환경 변수 유출에서 시작됐어요. OIDC 방식으로 전환하면 정적 키 자체가 사라지니까 그 위험이 원천 차단되죠. 문제는 설정이 생각보다 까다롭다는 것. 특히 `AssumeRoleWithWebIdentity 403` 에러는 원인이 서너 가지가 겹쳐서 나타나기 때문에 어디서 막혔는지 바로 보이질 않아요.

> **핵심 요약**
> - GitHub Actions OIDC는 정적 AWS 액세스 키 없이 임시 자격증명을 발급받는 방식으로, 키 유출 위험을 구조적으로 없애준다.
> - `AssumeRoleWithWebIdentity 403` 에러의 원인은 크게 세 가지: OIDC Provider Thumbprint 불일치, IAM 신뢰 정책의 Condition 오류, GitHub Actions 워크플로 권한(`id-token: write`) 누락.
> - AWS IAM OIDC Provider를 등록할 때 Audience 값을 `sts.amazonaws.com`으로 설정해야 하며, `token.actions.githubusercontent.com`을 그대로 쓰면 안 된다.
> - 신뢰 정책의 `sub` Condition은 브랜치명, 태그, 환경(environment) 범위에 따라 정확히 다르게 써야 하며, 와일드카드 남발은 보안 구멍이다.

---

## OIDC가 지금 표준이 된 이유

원래 GitHub Actions에서 AWS 리소스에 접근하려면 `AWS_ACCESS_KEY_ID`와 `AWS_SECRET_ACCESS_KEY`를 Secrets에 저장해서 쓰는 게 일반적이었어요. 단순하고 빠르죠. 하지만 이 방식에는 구조적인 문제가 있어요. 키가 장기간 유효하고, 한 번 유출되면 교체 전까지 계속 악용 가능하거든요.

GitHub는 2021년 10월에 OIDC(OpenID Connect) 지원을 공식 추가했어요. AWS는 이를 받아서 `sts.amazonaws.com`을 통해 임시 토큰을 발급하는 플로우를 제공하고 있죠. 2026년 현재 AWS Well-Architected Framework의 보안 기둥(Security Pillar)에서도 "장기 자격증명 대신 임시 자격증명을 써라"는 항목이 명시적으로 들어가 있어요.

플로우를 간단히 설명하면 이래요.

1. GitHub Actions 워크플로가 실행되면 GitHub가 OIDC 토큰(JWT)을 발급해요
2. 워크플로가 그 토큰을 AWS STS에 전달하면서 특정 역할을 맡겠다(`AssumeRoleWithWebIdentity`)고 요청해요
3. AWS가 토큰을 검증하고 신뢰 정책과 대조한 뒤 15분~1시간짜리 임시 자격증명을 내려줘요

여기서 403이 뜬다는 건 1번과 2번 사이 어딘가에서 검증 실패가 났다는 신호예요.

---

## 403이 뜨는 세 가지 원인

### 원인 #1: `id-token: write` 권한 누락

가장 자주 빠뜨리는 설정이에요. GitHub Actions 워크플로 파일에 아래처럼 permissions 블록이 없으면 OIDC 토큰 자체가 생성되질 않아요.

```yaml
permissions:
  id-token: write
  contents: read
```

`contents: read`는 repo 코드를 체크아웃하기 위한 거고, `id-token: write`가 OIDC 토큰 발급에 필요한 핵심 권한이에요. 이걸 빠뜨리면 `configure-aws-credentials` 액션 단계에서 `Error: Credentials could not be loaded` 메시지가 나와요. 에러 메시지만 봐서는 권한 문제인지 바로 알기 어렵죠. 삽질의 절반이 여기서 나와요.

### 원인 #2: IAM 신뢰 정책의 `sub` Condition 오류

IAM 역할의 신뢰 정책(Trust Policy)에서 `sub` 조건이 틀리면 403이 나와요. GitHub OIDC 토큰의 `sub` 클레임은 이런 형식이에요.

```
repo:{GitHubOrg}/{RepoName}:ref:refs/heads/{브랜치명}
repo:{GitHubOrg}/{RepoName}:environment:{환경명}
```

신뢰 정책 예시는 이래요.

```json
{
  "Condition": {
    "StringLike": {
      "token.actions.githubusercontent.com:sub": 
        "repo:myorg/myrepo:ref:refs/heads/main"
    }
  }
}
```

흔한 실수 두 가지예요.

- `StringEquals`를 써놓고 와일드카드(`*`)를 값에 넣는 경우. `StringEquals`는 와일드카드 매칭을 안 해요. `StringLike`를 써야 `*`가 작동해요.
- `environment`를 쓰는 워크플로인데 신뢰 정책에는 `ref` 형식으로만 걸어놓은 경우. 환경 이름을 쓰면 `sub`가 `repo:org/repo:environment:production` 형태로 나와서 브랜치 기반 조건에 안 맞아요.

### 원인 #3: OIDC Provider 설정의 Audience 값 혼동

AWS 콘솔에서 IAM OIDC Provider를 등록할 때 Audience 값을 뭘로 써야 하는지 헷갈리는 경우가 많아요.

| 설정 항목 | 올바른 값 | 잘못된 값 |
|---|---|---|
| Provider URL | `https://token.actions.githubusercontent.com` | `https://github.com` |
| Audience | `sts.amazonaws.com` | `token.actions.githubusercontent.com` |
| Thumbprint | AWS 자동 갱신 (2023년 이후) | 수동 입력한 구 thumbprint |

`configure-aws-credentials` GitHub Action v2 이후 버전에서는 Audience가 기본적으로 `sts.amazonaws.com`으로 설정돼요. 하지만 구 버전 문서를 참고해서 `token.actions.githubusercontent.com`을 Audience로 쓴 경우, 토큰의 `aud` 클레임과 불일치해서 403이 나와요.

---

## 정적 키 vs OIDC: 뭘 써야 하나

| 비교 항목 | 정적 액세스 키 | OIDC 임시 자격증명 |
|---|---|---|
| 키 유효 기간 | 무기한 (수동 교체 전까지) | 최대 1시간 |
| 유출 시 위험 | 즉시 악용 가능 | 만료 후 무용 |
| 설정 복잡도 | 낮음 (Secrets 등록만) | 중간 (IAM + Provider 설정) |
| 보안 감사 통과 | AWS Security Hub에서 경고 발생 | 권고 사항 충족 |
| 멀티 AWS 계정 | 계정별 키 따로 관리 | 역할 체인으로 처리 가능 |
| 권장 여부 | AWS Well-Architected에서 비권장 | 현재 Best Practice |

초기 설정이 조금 복잡한 건 사실이에요. 그런데 한 번 맞춰 놓으면 키 교체 스케줄도 없고, 키 노출 사고도 구조적으로 막혀요. 운영 편의성과 보안을 같이 잡는 셈이죠.

---

## 설정 전 체크리스트: 이 순서로 확인하세요

403을 만났을 때 가장 빠른 해결 경로예요.

**시나리오 1 — 워크플로 자체에서 토큰을 못 받는 경우**

에러 메시지: `Error: Credentials could not be loaded` 또는 `Unable to locate credentials`

확인할 것: 워크플로 파일의 `permissions` 블록에 `id-token: write`가 있는지 바로 보세요. 재사용 가능한 워크플로(`workflow_call`)를 쓴다면 호출하는 쪽과 호출받는 쪽 모두에 permissions 블록이 필요해요.

**시나리오 2 — STS에서 403이 떨어지는 경우**

에러 메시지: `An error occurred (AccessDenied) when calling the AssumeRoleWithWebIdentity operation`

확인할 것: IAM 역할 신뢰 정책의 `sub` Condition 값을 직접 복사해서 GitHub Actions 로그의 토큰 `sub` 클레임과 대조해요. CloudTrail에서 해당 시점 이벤트를 찾으면 `errorMessage` 필드에 어떤 조건에서 걸렸는지 나와요.

**시나리오 3 — Provider 등록은 됐는데 검증에서 깨지는 경우**

에러 메시지: `TokenVerificationError` 또는 `Invalid identity token`

확인할 것: IAM OIDC Provider의 Audience 값을 콘솔에서 직접 확인해요. `sts.amazonaws.com`이어야 해요. 2023년 이전에 등록한 Provider라면 Thumbprint도 AWS 콘솔에서 갱신 버튼 눌러서 최신 값으로 업데이트하세요.

---

## 지금 어떻게 움직여야 할까

**지금 당장:**
- 현재 운영 중인 GitHub Actions 워크플로 중 `AWS_ACCESS_KEY_ID`를 직접 쓰는 워크플로 목록 뽑기
- AWS Security Hub에서 `IAM.21: IAM customer managed policies that you create should not allow wildcard actions for services` 항목 확인

**4-8주 안에:**
- OIDC로 전환하면서 신뢰 정책을 환경(environment)별로 분리 — `production` 브랜치와 `develop` 브랜치에 서로 다른 역할을 맡기는 구조로 세팅
- GitHub Environments의 보호 규칙(Protection Rules)과 IAM 조건을 연결해서 승인 없는 배포를 IAM 수준에서도 막는 레이어 추가

**6개월 후 주목할 것:**
AWS가 2025년 말부터 IAM Identity Center와 GitHub Actions OIDC를 직접 연결하는 통합 방식을 강화하고 있어요. 멀티 계정 환경에서 역할 체인 없이 조직 단위 접근 제어를 OIDC로 처리하는 방향이죠. 지금 OIDC 기반 신뢰 정책 구조를 제대로 잡아두면 이 전환이 훨씬 수월해져요.

---

## 삽질 없이 넘어가려면

핵심을 다시 짚을게요.

- `id-token: write` 권한은 워크플로에 반드시 명시해야 해요
- IAM 신뢰 정책 `sub` Condition은 `environment` 사용 여부에 따라 형식이 달라요
- OIDC Provider Audience는 `sts.amazonaws.com`이에요
- `StringEquals`와 `StringLike`의 차이를 신뢰 정책에서 반드시 구분하세요

GitHub Actions OIDC + AWS 임시 자격증명 방식은 설정이 한 번 맞으면 이후에 건드릴 일이 거의 없어요. 403 에러 하나가 며칠짜리 삽질로 번지는 건 대부분 위에 나온 세 가지 포인트 중 하나 때문이에요.

지금 돌아가는 파이프라인에 정적 키가 있다면, 이번 달 안에 교체 일정을 잡는 게 맞아요. 어디서 막혔는지 CloudTrail 로그를 같이 보고 싶다면 댓글로 남겨 주세요.

## 참고자료

1. [Securely Connect GitHub Actions to AWS Using IAM Roles and OIDC - DEV Community](https://dev.to/aws-builders/securely-connect-github-actions-to-aws-using-iam-roles-and-oidc-4ek2)
2. [Automated deployments with GitHub Actions for Amazon ECS Express Mode | Amazon Web Services](https://aws.amazon.com/blogs/containers/automated-deployments-with-github-actions-for-amazon-ecs-express-mode/)
3. [Securely Connect GitHub Actions to AWS Using IAM Roles and OIDC | by Ravindra singh | Medium](https://medium.com/@rvisingh1221/securely-connect-github-actions-to-aws-using-iam-roles-and-oidc-df8536a6e288)


---

*Photo by [Shantanu Kumar](https://unsplash.com/@theshantanukr) on [Unsplash](https://unsplash.com/photos/a-cell-phone-sitting-on-top-of-an-open-book-xvdkNBaja90)*
