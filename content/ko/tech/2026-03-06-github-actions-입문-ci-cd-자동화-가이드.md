---
title: "GitHub Actions 입문: YAML 파일 하나로 CI CD 자동화 파이프라인 구축 가이드"
date: 2026-03-06T14:27:31+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "github", "actions", "\uc790\ub3d9\ud654", "Node.js"]
description: "GitHub Actions로 CI/CD 자동화하는 법을 처음부터 설명합니다. 공개 저장소 무제한 무료, 비공개는 월 2,000분 무료. git push 한 번으로 테스트부터 EC2 배포까지 자동화하세요."
image: "/images/20260306-github-actions-입문-ci-cd-자동화-가이.webp"
technologies: ["Node.js", "Docker", "AWS", "GitHub Actions", "Slack"]
faq:
  - question: "GitHub Actions 입문 CI CD 자동화 가이드 처음 시작하려면 뭐부터 해야 하나요"
    answer: "GitHub Actions 입문 CI CD 자동화 가이드에 따르면, 저장소 루트에 `.github/workflows/` 폴더를 만들고 YAML 파일 하나를 추가하는 것만으로 CI/CD 파이프라인을 시작할 수 있어요. 사전에 Git 기본 사용법과 YAML 파일 읽는 법 정도만 알면 충분하고, 별도 설치나 외부 서비스 연동 없이 GitHub 안에서 바로 시작할 수 있어요."
  - question: "GitHub Actions 비공개 저장소 무료로 쓸 수 있나요"
    answer: "GitHub Actions는 비공개 저장소 기준으로 월 2,000분을 무료로 제공하고, 공개 저장소는 무제한 무료로 사용할 수 있어요. 개인 프로젝트나 소규모 팀이라면 무료 플랜으로도 충분히 CI/CD 파이프라인을 운영할 수 있어요."
  - question: "GitHub Actions Jenkins Travis CI 중에 뭐가 더 좋나요"
    answer: "처음 시작하는 개발자라면 GitHub Actions가 가장 빠른 선택이에요. Jenkins는 서버를 직접 구성하고 유지보수해야 하는 부담이 있고, Travis CI는 GitHub 연동 시 외부 서비스 연동이 필요한 반면, GitHub Actions는 GitHub에 내장되어 있어 별도 설치 없이 바로 사용할 수 있어요."
  - question: "GitHub Actions 빌드 시간 줄이는 방법 있나요"
    answer: "`actions/cache@v4`를 사용해 의존성 캐싱을 설정하면 빌드 시간을 절반 이하로 줄일 수 있어요. `hashFiles('**/package-lock.json')`을 캐시 키로 지정하면 `package-lock.json`이 변경될 때만 캐시를 새로 생성하므로 불필요한 패키지 재다운로드를 방지할 수 있어요."
  - question: "GitHub Actions에서 AWS 시크릿 키 안전하게 관리하는 방법"
    answer: "OIDC 인증을 사용하면 AWS 시크릿 키를 저장소에 직접 저장하지 않아도 AWS 리소스에 접근할 수 있어 보안상 훨씬 안전해요. GitHub Actions 입문 CI CD 자동화 가이드에서도 OIDC 인증 방식을 권장하고 있으며, 시크릿 키 노출 위험을 근본적으로 차단할 수 있는 방법이에요."
---

배포하는 데 2시간 걸렸는데, 나중에 보니 그냥 YAML 파일 하나면 됐던 얘기예요. 이 가이드를 읽고 나면 그런 일 없을 거예요.

GitHub Actions는 2026년 현재 개발팀이 가장 많이 쓰는 CI/CD 도구예요. 공개 저장소는 무제한 무료, 비공개 저장소는 월 2,000분이 무료로 제공돼요. 코드 변경하고 `git push`만 하면 테스트, 빌드, 배포가 자동으로 돌아가는 세상이 됐어요.

이 가이드는 GitHub Actions를 처음 접하는 개발자를 위해 썼어요. 기본 개념부터 EC2 자동 배포까지 한 번에 정리해 드릴게요.

> **Key Takeaways**
> - GitHub Actions는 공개 저장소 무제한 무료, 비공개 저장소 월 2,000분 무료로 진입 장벽이 낮아요.
> - `.github/workflows/` 폴더에 YAML 파일 하나만 추가하면 CI/CD 파이프라인이 만들어져요.
> - `test → build → deploy` 세 단계 구조가 가장 기본적이고 안정적인 패턴이에요.
> - `actions/cache@v4`로 의존성 캐싱을 걸면 빌드 시간을 절반 이하로 줄일 수 있어요.
> - OIDC 인증을 쓰면 AWS 시크릿 키를 저장소에 저장하지 않아도 돼요 — 보안상 훨씬 안전해요.

---

## CI/CD, 지금 왜 GitHub Actions인가요?

CI/CD(Continuous Integration / Continuous Deployment)는 새로운 개념이 아니에요. Jenkins가 2004년에 나왔고, Travis CI는 2011년부터 GitHub 프로젝트에 널리 쓰였어요. 그런데 2026년에 다시 GitHub Actions 얘기를 하는 이유가 뭘까요?

단순해요. **GitHub 안에 전부 있어서요.**

Travis CI를 쓰려면 외부 서비스에 연결하고, IAM 권한 설정하고, SSH 키 관리하고... 설정만 하루가 갔어요. [Fadet's coding box 블로그](https://fadet-coding.tistory.com/92)에서도 Travis CI + S3 + CodeDeploy + EC2 조합이 얼마나 번거로운지 직접 경험을 공유하면서, 결국 GitHub Actions + Docker 두 개만으로 같은 파이프라인을 다시 만들었다고 해요.

**선행 지식으로 필요한 것들:**
- Git 기본 사용법 (push, pull, branch)
- YAML 파일 읽는 법 (들여쓰기가 중요해요)
- 서버 기초 — SSH 연결, 포트 개념

---

## CI/CD 도구 비교

| 항목 | GitHub Actions | Travis CI | Jenkins |
|---|---|---|---|
| **비용** | 공개 무제한 / 비공개 2,000분 무료 | 공개 무제한 / 비공개 유료 | 무료 (서버 직접 운영) |
| **설치 복잡도** | 없음 (GitHub 내장) | 외부 연동 필요 | 서버 직접 구성 필요 |
| **GitHub 연동** | 네이티브 | API 연동 | 플러그인 필요 |
| **마켓플레이스** | 수천 개의 사전 제작 액션 | 제한적 | 플러그인 중심 |
| **자체 호스팅** | 지원 (Self-hosted Runner) | 제한적 | 완전 지원 |
| **학습 난이도** | 낮음 | 낮음 | 높음 |

GitHub Actions의 가장 큰 강점은 "GitHub에서 바로 된다"는 거예요. Jenkins는 서버를 직접 관리해야 해서 유지보수 부담이 있고, Travis CI는 GitHub 연동이 가능하지만 GitHub Actions처럼 네이티브하지는 않아요. 처음 시작한다면 GitHub Actions가 가장 빠른 경로예요.

---

## 실전 구성 단계별 가이드

### 사전 준비

- GitHub 계정과 저장소
- Node.js 18.x 이상 (또는 본인 프로젝트 언어)
- AWS EC2 인스턴스 (배포 단계에서 필요)
- EC2 보안 그룹: 22(SSH), 80(HTTP), 443(HTTPS), 3000(앱) 포트 열기

### Step 1: 첫 번째 워크플로 파일 만들기

저장소 루트에 `.github/workflows/` 폴더를 만들고 `ci.yml` 파일을 생성해요.

```yaml
# .github/workflows/ci.yml
# main 브랜치에 push할 때마다 자동으로 실행됩니다

name: CI 파이프라인

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: 코드 체크아웃
        uses: actions/checkout@v4

      - name: Node.js 18 세팅
        uses: actions/setup-node@v4
        with:
          node-version: '18'

      # 두 번째 실행부터 빨라져요
      - name: 의존성 캐시 설정
        uses: actions/cache@v4
        with:
          path: ~/.npm
          key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}

      - name: 패키지 설치
        run: npm ci

      - name: 테스트 실행
        run: npm test
```

`hashFiles('**/package-lock.json')`이 핵심이에요. `package-lock.json`이 바뀔 때만 캐시를 새로 만들어서 불필요한 재다운로드를 막아요.

### Step 2: 빌드 단계 추가

테스트가 통과하면 빌드로 넘어가요.

```yaml
  build:
    runs-on: ubuntu-latest
    needs: test  # test 잡이 성공해야 실행됩니다

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'

      - run: npm ci
      - run: npm run build

      # node_modules, .git, tests 폴더는 제외 (용량 절약)
      - name: 배포 아카이브 생성
        run: |
          tar --exclude=./node_modules \
              --exclude=./.git \
              --exclude=./tests \
              -czf deployment.tar.gz .

      - name: 아티팩트 업로드
        uses: actions/upload-artifact@v4
        with:
          name: deployment-package
          path: deployment.tar.gz
```

### Step 3: EC2 자동 배포 설정

[notavoid.tistory.com의 EC2 배포 가이드](https://notavoid.tistory.com/157)에 따르면, GitHub Secrets에 세 가지 값을 먼저 등록해야 해요.

저장소 Settings → Secrets and variables → Actions에서:
- `SSH_PRIVATE_KEY`: RSA 4096비트 개인키
- `HOST`: EC2 공인 IP
- `USERNAME`: ubuntu 또는 ec2-user

```yaml
  deploy:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'  # main 브랜치만 배포

    steps:
      - name: 아티팩트 다운로드
        uses: actions/download-artifact@v4
        with:
          name: deployment-package

      - name: EC2로 파일 전송
        uses: appleboy/scp-action@v0.1.4
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          source: deployment.tar.gz
          target: /home/ubuntu/app

      - name: 서버 배포 실행
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /home/ubuntu/app
            tar -xzf deployment.tar.gz
            npm ci --production
            pm2 restart app || pm2 start npm --name "app" -- start
```

### Step 4: 여러 Node.js 버전에서 동시 테스트 (Matrix 전략)

[youngju.dev의 고급 CI/CD 가이드](https://www.youngju.dev/blog/devops/2026-03-02-github-actions-advanced-cicd)에 따르면, Matrix 전략으로 3개 버전 × 2개 OS = 6개 잡을 동시에 돌릴 수 있어요.

```yaml
  test-matrix:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false  # 하나 실패해도 나머지 계속 실행
      matrix:
        node-version: [16, 18, 20]
        os: [ubuntu-latest, windows-latest]

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm ci
      - run: npm test
```

`fail-fast: false`가 없으면 하나가 실패했을 때 나머지 잡도 전부 취소돼요. 어떤 버전에서 문제인지 알려면 꼭 넣어야 해요.

---

## 실제로 쓸 수 있는 전체 예시

### Slack 알림 연동

배포 결과를 Slack으로 받으면 팀 전체가 상황을 바로 알 수 있어요.

```yaml
      - name: Slack 알림
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: |
            배포 상태: ${{ job.status }}
            브랜치: ${{ github.ref_name }}
            커밋: ${{ github.sha }}
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
        if: always()  # 성공이든 실패든 항상 알림 전송
```

### 블루-그린 배포 스크립트

무중단 배포가 필요하다면 현재 포트를 감지해서 반대 포트에 새 버전을 올려요.

```bash
#!/bin/bash
CURRENT_PORT=$(pm2 list | grep "app" | grep -o "3[0-9][0-9][0-9]" | head -1)
NEW_PORT=$([[ "$CURRENT_PORT" == "3000" ]] && echo "3001" || echo "3000")

PORT=$NEW_PORT pm2 start npm --name "app-$NEW_PORT" -- start

sleep 10
curl -f http://localhost:$NEW_PORT/health || exit 1

sed -i "s/proxy_pass http:\/\/localhost:$CURRENT_PORT/proxy_pass http:\/\/localhost:$NEW_PORT/" /etc/nginx/sites-available/default
nginx -s reload

pm2 delete "app-$CURRENT_PORT"
```

---

## 흔히 하는 실수와 해결법

### 피해야 할 패턴

- **`npm install` 쓰지 말기**: CI 환경에서는 `npm ci`를 써야 해요. `package-lock.json`을 기준으로 정확히 설치하기 때문에 "내 컴퓨터에서는 되는데 서버에서 안 돼요" 문제가 없어져요.

- **시크릿을 코드에 직접 쓰지 말기**: AWS 키, SSH 키는 반드시 GitHub Secrets에. OIDC 인증을 쓰면 아예 장기 키를 저장할 필요가 없어요.

- **`if: always()`와 `if: success()` 구분하기**: Slack 알림은 `always()`로, 배포는 `success()`로만 실행해야 해요.

### 이런 경우엔 안 통해요

GitHub Actions가 항상 정답은 아니에요. 월 2,000분을 훌쩍 넘는 대규모 팀이라면 비용이 빠르게 올라가요. 빌드 시간이 길거나 잡이 많은 팀은 Self-hosted Runner를 직접 운영하는 게 나을 수 있어요. Jenkins가 복잡해 보여도 이미 인프라가 갖춰진 조직에선 더 유연하게 쓸 수 있고요. 상황에 맞게 선택하는 게 맞아요.

### 프로덕션 배포 전 체크리스트

- [ ] 모든 시크릿이 GitHub Secrets에 등록됐는지 확인
- [ ] EC2 보안 그룹에서 필요한 포트만 열려 있는지 확인
- [ ] PM2 로그 로테이션 설정 (10MB 캡, 30일 보존 권장)
- [ ] 헬스 체크 엔드포인트(`/health`) 구현됐는지 확인
- [ ] `fail-fast: false` 설정으로 Matrix 전략 안정화

---

## 지금 바로 시작하려면

GitHub Actions로 CI/CD를 처음 만들어 보면, 처음엔 YAML 들여쓰기로 10분은 날릴 거예요. 그래도 한 번 돌아가는 걸 보면 다시는 수동 배포로 못 돌아가요.

**시작 순서:**
1. 이 가이드의 Step 1 YAML을 복사해서 저장소에 추가하세요.
2. `git push`로 첫 워크플로를 실행해 보세요.
3. Actions 탭에서 실시간으로 로그 확인하세요.

공식 문서는 [docs.github.com/actions](https://docs.github.com/en/actions)에 있어요. 다음 단계로는 Docker 컨테이너 빌드, OIDC 인증, Self-hosted Runner 설정을 추천해요. 어떤 부분이 막히셨나요? 댓글로 남겨주시면 같이 풀어볼게요.

---

*Photo by [Enchanted Tools](https://unsplash.com/@enchantedtools) on [Unsplash](https://unsplash.com/photos/a-person-interacting-with-a-friendly-orange-robot-CdBJDBdkazs)*
