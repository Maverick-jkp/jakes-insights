---
title: "GitHub Actions 입문 가이드: CI/CD 자동화 처음 설정하는 법"
date: 2026-03-03T09:00:54+0900
draft: true
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "github", "actions", "cicd"]
description: "GitHub Actions로 CI/CD 자동화를 처음 설정하는 완벽 입문 가이드. 워크플로우 파일 작성부터 자동 빌드, 테스트, 배포까지 단계별로 따라하며 개발 생산성을 높여보세요."
image: "/images/20260303-github-actions-입문-가이드-cicd-자동화.webp"
technologies: ["Node.js", "Docker", "AWS", "GitHub Actions", "Linux"]
faq:
  - question: "GitHub Actions 처음 설정하는 법 모르겠어요 어디서 시작해야 하나요"
    answer: "GitHub Actions 입문 가이드 CICD 자동화 처음 설정하는 법에 따르면, 저장소 루트에 `.github/workflows/` 폴더를 만들고 그 안에 YAML 파일을 생성하는 것부터 시작하면 됩니다. `on`, `jobs`, `steps` 세 가지 핵심 키워드만 이해하면 push 이벤트 기준으로 테스트부터 배포까지 자동화하는 기본 파이프라인을 빠르게 만들 수 있어요."
  - question: "GitHub Actions 비용 얼마나 드나요 무료로 쓸 수 있나요"
    answer: "공개(Public) 저장소는 GitHub Actions를 무제한 무료로 사용할 수 있고, 비공개(Private) 저장소는 월 2,000분이 무료로 제공됩니다. 소규모~중규모 프로젝트라면 무료 한도 안에서 추가 비용 없이 운영하는 것이 가능합니다."
  - question: "GitHub Actions에서 SSH 키 비밀번호 같은 민감 정보 어떻게 관리해요"
    answer: "서버 SSH 키, IP 주소, 비밀번호 같은 민감 정보는 코드에 직접 넣지 말고, 저장소의 Settings → Secrets and variables → Actions 메뉴에서 GitHub Secrets으로 등록해야 합니다. 워크플로우 YAML 파일에서는 `${{ secrets.변수명 }}` 형식으로 안전하게 참조할 수 있어요."
  - question: "GitHub Actions 워크플로우 커밋 없이 로컬에서 테스트하는 방법"
    answer: "`act`라는 도구를 사용하면 커밋 없이 로컬 환경에서 워크플로우를 미리 실행해볼 수 있습니다. 매번 커밋을 올려가며 디버깅할 필요가 없어지기 때문에 개발 초기 단계에서 파이프라인을 빠르게 검증하는 데 특히 유용합니다."
  - question: "CI/CD 자동화 처음 설정할 때 GitHub Actions vs Jenkins 뭐가 더 나은가요"
    answer: "GitHub Actions 입문 가이드 CICD 자동화 처음 설정하는 법 관점에서 보면, GitHub 기반 프로젝트라면 Actions가 훨씬 빠르게 시작할 수 있는 선택입니다. Jenkins는 별도 서버 설치와 플러그인 설정이 필요한 반면, GitHub Actions는 YAML 파일 하나로 설정이 끝나고 GitHub 저장소와 네이티브로 통합되어 관리가 훨씬 단순합니다."
---

매번 서버에 직접 접속해서 `git pull`하고 `npm install`하고... 이 반복, 질리죠? GitHub Actions를 쓰면 코드를 push하는 순간 테스트, 빌드, 배포까지 자동으로 돌아가요. 지금 GitHub 저장소의 절반 이상이 이미 Actions를 쓰고 있어요. 처음 설정이 낯설게 느껴질 뿐, 막상 해보면 생각보다 빨리 됩니다.

이 글은 GitHub Actions를 처음 써보는 개발자를 위한 실전 가이드예요. 읽고 나면 push 한 번으로 배포까지 되는 파이프라인을 직접 만들 수 있어요.

**이 글에서 배우는 것:**
- `.github/workflows/` 파일 구조와 YAML 작성법
- push 이벤트 트리거 → 테스트 → 빌드 → 배포 흐름
- GitHub Secrets으로 민감 정보 안전하게 처리하는 법
- 로컬에서 워크플로우를 미리 돌려보는 `act` 도구

---

> **Key Takeaways**
> - GitHub Actions 워크플로우는 `.github/workflows/` 폴더에 YAML 파일로 정의하며, `push` 이벤트 기준으로 평균 배포 완료 시간은 약 4분이다.
> - Private 저장소는 월 2,000분 무료 제공되며, 소규모~중규모 프로젝트에서 추가 비용 없이 운영 가능하다.
> - 서버 접속 정보(SSH 키, IP, 비밀번호)는 코드에 절대 넣지 말고, Repository Settings → Secrets and variables → Actions에 등록해야 한다.
> - `test → build → deploy` 순서로 job을 구성하면, 테스트가 실패할 경우 배포 단계 자체가 실행되지 않아 안전하다.
> - `act` 도구를 쓰면 커밋 없이 로컬에서 워크플로우를 먼저 돌려볼 수 있어 디버깅 시간을 크게 줄여준다.

---

## GitHub Actions가 뭔지부터

GitHub Actions는 2019년 정식 출시됐어요. 그 전까지 CI/CD를 하려면 Jenkins 서버를 따로 띄우거나, CircleCI 같은 외부 서비스와 연결하는 과정이 필요했죠. 설정 파일도 길고, GitHub 저장소와 연동하는 것도 한 단계 더 필요했어요.

GitHub Actions는 이 모든 걸 저장소 안으로 가져왔어요. 코드와 파이프라인이 같은 곳에 있으니 관리가 훨씬 편해졌고, 공개 저장소는 무제한 무료, 비공개 저장소는 월 2,000분 무료로 작은 팀도 부담 없이 쓸 수 있게 됐어요.

**사전 지식으로 필요한 것:**
- Git/GitHub 기본 사용법 (commit, push, branch)
- YAML 파일 기본 문법 (들여쓰기 규칙)
- 터미널 명령어 기초

Jenkins나 다른 CI 도구를 써본 적 없어도 괜찮아요. 오히려 처음 배우기엔 GitHub Actions가 더 접근하기 쉬운 편이에요.

---

## 도구 비교: GitHub Actions vs Jenkins vs CircleCI

| 항목 | GitHub Actions | Jenkins | CircleCI |
|------|---------------|---------|----------|
| **비용** | Public 무제한 무료 / Private 월 2,000분 무료 | 오픈소스(무료), 서버 비용 별도 | 무료 플랜 월 6,000분 |
| **설정 난이도** | 낮음 (YAML 파일 하나) | 높음 (서버 설치, 플러그인 설정) | 중간 |
| **GitHub 연동** | 네이티브 통합 | 웹훅 별도 설정 필요 | OAuth 연동 필요 |
| **실행 환경** | GitHub 호스팅 러너 제공 | 직접 서버 관리 | 호스팅 러너 제공 |
| **커뮤니티/마켓플레이스** | 20,000+ Action 마켓플레이스 | 2,000+ 플러그인 | 오브(Orb) 생태계 |
| **병렬 실행** | 지원 | 지원 | 지원 |

Jenkins는 대규모 엔터프라이즈 환경에서 여전히 강점이 있어요. 그런데 GitHub 기반 프로젝트라면 Actions가 훨씬 빠르게 시작할 수 있어요. 설정 복잡도가 낮고, GitHub 플랫폼 안에서 통합 관리가 가능하다는 게 실용적인 차이예요.

---

## 단계별 설정: 처음부터 배포까지

### 사전 준비물

- GitHub 저장소 (Node.js 프로젝트 기준으로 설명할게요)
- 배포 대상 서버 (AWS EC2 또는 다른 Linux 서버)
- 서버 SSH 접속 키

---

### Step 1: 워크플로우 파일 만들기

저장소 루트에 `.github/workflows/` 폴더를 만들고, 그 안에 `deploy.yml` 파일을 생성해요.

```yaml
# .github/workflows/deploy.yml
name: CI/CD 파이프라인  # 워크플로우 이름 (GitHub UI에서 표시됨)

on:
  push:
    branches:
      - main  # main 브랜치에 push될 때만 실행

jobs:
  test:
    runs-on: ubuntu-latest  # GitHub 호스팅 러너 사용
    steps:
      - name: 코드 가져오기
        uses: actions/checkout@v4

      - name: Node.js 18 설정
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'  # package-lock.json 기준으로 의존성 캐시

      - name: 패키지 설치
        run: npm ci  # npm install보다 재현성이 높은 ci 명령어 사용

      - name: 테스트 실행
        run: npm test
```

`on` 키가 트리거 조건이에요. `main` 브랜치에 push가 들어올 때만 실행돼요. `pull_request`도 트리거로 추가할 수 있어요.

---

### Step 2: GitHub Secrets 등록하기

서버 접속 정보를 코드에 직접 넣으면 안 돼요. 저장소 **Settings → Secrets and variables → Actions**로 가서 아래 항목들을 등록해요.

| Secret 이름 | 내용 |
|------------|------|
| `EC2_HOST` | 서버 IP 주소 |
| `EC2_USERNAME` | 접속 유저명 (예: `ubuntu`) |
| `EC2_SSH_KEY` | SSH 비밀 키 전체 내용 |

등록 후 워크플로우에서 이렇게 참조해요:

```yaml
# ${{ secrets.변수명 }} 형식으로 참조
- name: 서버 접속 테스트
  run: echo "배포 대상: ${{ secrets.EC2_HOST }}"
  # 실제 값은 로그에 절대 노출되지 않음
```

---

### Step 3: 빌드 및 배포 job 추가하기

`test` job이 성공해야 `deploy`가 실행되도록 `needs` 키로 연결해요.

```yaml
  build:
    runs-on: ubuntu-latest
    needs: test  # test job이 성공해야 실행됨
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'

      - run: npm ci
      - run: npm run build  # dist/ 폴더 생성

      # 빌드 결과물을 다음 job으로 전달
      - uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/

  deploy:
    runs-on: ubuntu-latest
    needs: build  # build job이 성공해야 실행됨
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: build-output
          path: dist/

      # SCP로 서버에 파일 전송
      - name: 서버에 배포
        uses: appleboy/scp-action@v0.1.7
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ${{ secrets.EC2_USERNAME }}
          key: ${{ secrets.EC2_SSH_KEY }}
          source: "dist/"
          target: "/var/www/app/"
```

`test → build → deploy` 순서가 핵심이에요. 테스트나 빌드가 실패하면 배포 단계 자체가 건너뛰어져요.

---

### Step 4: 서버에서 프로세스 재시작

배포 후 서버에서 앱을 재시작해야 해요. SSH로 접속해서 PM2를 통해 처리해요.

```yaml
      - name: PM2로 앱 재시작
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ${{ secrets.EC2_USERNAME }}
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            cd /var/www/app
            npm ci --production
            pm2 reload ecosystem.config.js --update-env
            # 재시작 실패 시 이전 프로세스 유지됨
```

---

### Step 5: 로컬에서 먼저 테스트하기 (`act`)

push하기 전에 워크플로우를 로컬에서 돌려볼 수 있어요. `act` 도구가 Docker 컨테이너로 GitHub Actions 환경을 흉내 내줘요.

```bash
# 설치 (macOS/Linux)
brew install act

# 전체 워크플로우 실행
act

# 특정 job만 실행
act -j test

# Secrets 파일과 함께 실행
act --secret-file .secrets
```

`.secrets` 파일에 로컬 테스트용 값을 넣어두면 돼요. `.gitignore`에 반드시 추가하세요.

---

## 실전 예시: 완성된 워크플로우 파일

```yaml
# .github/workflows/deploy.yml - 복사해서 바로 쓸 수 있는 예시
name: 프로덕션 배포

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]  # PR에서는 test까지만 실행됨

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
      - run: npm ci
      - run: npm audit --audit-level high  # 보안 취약점 검사
      - run: npm test

  deploy:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'  # main 브랜치 push일 때만 배포
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
      - run: npm ci && npm run build

      - uses: appleboy/scp-action@v0.1.7
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ${{ secrets.EC2_USERNAME }}
          key: ${{ secrets.EC2_SSH_KEY }}
          source: "dist/"
          target: "/var/www/app/"

      - uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ${{ secrets.EC2_USERNAME }}
          key: ${{ secrets.EC2_SSH_KEY }}
          script: pm2 reload app --update-env
```

`if: github.ref == 'refs/heads/main'` 조건이 중요해요. PR에서 테스트는 돌리되, 실제 배포는 main에 머지됐을 때만 실행되도록 막아줘요.

---

## 자주 하는 실수와 체크리스트

### 흔한 실수들

- **들여쓰기 오류**: YAML은 탭 대신 스페이스를 써야 해요. 2칸 들여쓰기를 일관되게 유지하세요.
  - 해결: VS Code의 YAML 익스텐션을 설치하면 실시간으로 오류를 잡아줘요.

- **Secrets 이름 오타**: `${{ secrets.EC2_HOST }}`에서 대소문자가 틀리면 빈 값이 들어가요.
  - 해결: Settings에서 등록한 이름을 그대로 복사해서 쓰세요.

- **`npm install` vs `npm ci`**: CI 환경에서는 `npm ci`를 써야 해요. `package-lock.json`을 엄격하게 따라서 재현 가능한 빌드를 만들어줘요.

### 보안 체크리스트

- [ ] SSH 키는 GitHub Secrets에만 저장, 코드에 절대 없음
- [ ] 서버에서 root 로그인 비활성화, 비밀번호 인증 비활성화
- [ ] `npm audit --audit-level high` 파이프라인에 포함
- [ ] `.secrets` 파일 `.gitignore`에 추가

### 성능 팁

- `actions/cache@v3`로 `node_modules` 캐싱 → 의존성 설치 시간이 크게 줄어요
- 빌드 artifact는 `actions/upload-artifact` / `download-artifact`로 job 간 전달

---

## 마무리: 다음 단계

자, 정리할게요. YAML 파일 하나로 테스트 → 빌드 → 배포 파이프라인이 완성돼요. Secrets으로 민감 정보를 안전하게 관리하고, `act`로 로컬 테스트해서 불필요한 push를 줄이고, `if` 조건으로 브랜치별 실행을 제어하면 돼요.

지금 바로 본인 저장소에 `.github/workflows/` 폴더를 만들고, Step 1부터 따라해보세요. 처음엔 YAML 들여쓰기 오류로 한두 번 실패할 수 있어요. 그래도 괜찮아요. 다음 단계로는 Blue-Green 배포나 Slack 알림 연동을 도전해보세요.

---

*Photo by [Enchanted Tools](https://unsplash.com/@enchantedtools) on [Unsplash](https://unsplash.com/photos/close-up-of-an-orange-robot-with-a-sensor-array-1lHqfaLjnRA)*


## 관련 글


- [취업 코딩 테스트 위장 악성코드, 백도어로 개발자 피해 확산](/ko/tech/취업-코딩-테스트-악성코드-백도어-개발자-피해/)
- [코딩 부트캠프 추천: SSAFY·우테코·내배캠 등 5개 비교 분석](/ko/tech/코딩-부트캠프-추천/)
- [틱톡이 E2EE를 거부하는 이유: 아동 안전인가 데이터 수집인가](/ko/tech/틱톡-e2ee-거부-아동-안전-핑계-개인정보-논란/)
- [AI가 코드 짜면 누가 검증하나: 실무 개발자 딜레마와 ADR 활용법](/ko/tech/ai가-코드-짜면-누가-검증하나-실무-개발자-딜레마/)
- [GPT-5.3 출시, API 어떻게 달라졌나: 개발자 실전 정리](/ko/tech/gpt53-출시-api-어떻게-달라졌나-개발자-실전-정리/)

