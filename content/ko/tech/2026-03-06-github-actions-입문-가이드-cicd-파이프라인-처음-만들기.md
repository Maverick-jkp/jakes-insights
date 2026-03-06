---
title: "GitHub Actions 입문 가이드: YAML 설정으로 CI/CD 파이프라인 처음 만들기"
date: 2026-03-06T14:04:08+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "github", "actions", "\uac00\uc774\ub4dc", "Node.js"]
description: "GitHub Actions로 CI/CD 파이프라인 구축하기. 퍼블릭 레포 무제한 무료, 프라이빗 월 2,000분 무료. YAML 파일 하나로 테스트·빌드·배포 자동화, needs 키워드로 실행 순서까지 제어하는 법"
image: "/images/20260306-github-actions-입문-가이드-cicd-파이프.webp"
technologies: ["Node.js", "GitHub Actions", "Linux", "Go", "VS Code"]
faq:
  - question: "GitHub Actions 입문 가이드 CICD 파이프라인 처음 만들기 어디서 시작해야 하나요"
    answer: "GitHub Actions 입문 가이드 CICD 파이프라인 처음 만들기는 프로젝트 루트에 `.github/workflows/` 폴더를 만들고 YAML 파일 하나를 추가하는 것에서 시작해요. `on` 블록으로 트리거(push, pull_request 등)를 설정하고, `jobs` 안에 실행할 step들을 정의하면 기본 CI 파이프라인이 완성돼요."
  - question: "GitHub Actions 무료 플랜 제한 어떻게 되나요"
    answer: "GitHub Actions는 퍼블릭 레포에서는 무제한 무료로 사용할 수 있어요. 프라이빗 레포는 월 2,000분까지 무료이며, 이를 초과하면 추가 요금이 발생해요."
  - question: "GitHub Actions Jenkins CircleCI 뭐가 다른가요"
    answer: "Jenkins는 자유도가 높지만 서버를 직접 관리해야 하고 GitHub 연동에 플러그인이 필요해요. CircleCI는 월 6,000분 무료로 플랜이 후하지만 레포 외부에서 설정을 관리해야 하는 불편함이 있어요. GitHub Actions는 레포 안에서 모든 설정이 완결되기 때문에 처음 CI/CD 파이프라인을 만드는 팀에게 진입 장벽이 가장 낮아요."
  - question: "GitHub Actions 워크플로우에서 job 순서 지정하는 방법"
    answer: "GitHub Actions에서 job은 기본적으로 병렬로 실행되는데, `needs` 키워드를 사용하면 `test → build → deploy`처럼 순서를 강제할 수 있어요. 예를 들어 `deploy` job에 `needs: [build]`를 추가하면 build가 성공한 후에만 deploy가 실행돼요."
  - question: "GitHub Actions 입문 가이드 CICD 파이프라인 처음 만들기에서 의존성 캐시 설정하는 법"
    answer: "GitHub Actions 입문 가이드 CICD 파이프라인 처음 만들기에서 캐시는 `actions/setup-node@v4`에 `cache: 'npm'`을 추가하는 것만으로 자동 설정돼요. 더 세밀하게 제어하고 싶다면 `actions/cache@v4`와 `hashFiles('package-lock.json')`를 함께 사용하면 락파일 변경 여부를 기준으로 캐시가 자동 무효화되어 의존성 설치 시간을 크게 줄일 수 있어요."
---

코드 짜고 나서 배포까지 손으로 하고 있다면, 이 글이 딱 맞아요.

GitHub Actions는 퍼블릭 레포 무제한 무료, 프라이빗 레포도 월 2,000분 무료예요. 설정 파일 하나면 테스트부터 배포까지 전부 자동화돼요. YAML 파일 어떻게 쓰는지, 실제 CI/CD 파이프라인은 어떻게 만드는지 단계별로 짚어드릴게요.

---

> **핵심 요약**
> - GitHub Actions는 `.github/workflows/` 폴더에 YAML 파일을 저장하는 것만으로 CI/CD 파이프라인이 작동해요.
> - 워크플로우는 **workflow → event → job → step → runner** 다섯 개 컴포넌트로 구성돼요.
> - `needs` 키워드로 `test → build → deploy` 순서를 강제할 수 있고, 기본은 병렬 실행이에요.
> - `actions/cache@v4`와 `hashFiles('package-lock.json')`를 함께 쓰면 의존성 설치 시간을 크게 줄일 수 있어요.
> - GitHub Secrets에 저장한 민감 정보는 포크된 레포의 PR에서는 접근이 차단돼요. (보안 기본값)

---

## GitHub Actions가 뭔지, 왜 지금인지

CI/CD는 오래된 개념이에요. 그런데 2018년 GitHub Actions가 나오기 전까지는 Jenkins, CircleCI, Travis CI처럼 별도 서버나 외부 서비스를 붙여야 했어요. 설정도 복잡하고, 레포랑 파이프라인이 따로 놀다 보니 관리 포인트가 두 배였죠.

GitHub Actions는 그걸 레포 안으로 끌어들였어요. `.github/workflows/` 폴더에 YAML 파일 하나 올리면 끝이에요. GitHub 레포, PR, 이슈와 자연스럽게 연동되고, Ubuntu / Windows / macOS 러너를 선택할 수 있어요.

Actions의 핵심 구조는 다섯 가지예요:

- **Workflow**: 자동화 프로세스 전체
- **Event**: 워크플로우를 실행시키는 트리거 (push, PR 등)
- **Job**: 같은 러너 위에서 실행되는 Step 묶음
- **Step**: 개별 작업 단위
- **Runner**: 실제 코드가 실행되는 서버

진입 장벽이 낮은 만큼, CI/CD 파이프라인 처음 만들기엔 GitHub Actions가 제격이에요.

**사전 준비:**
- GitHub 계정
- Node.js 프로젝트 (파이썬, Go도 무방)
- 기본적인 YAML 문법 감각 (들여쓰기가 핵심)

---

## CI/CD 도구 비교: GitHub Actions vs 대안들

| 항목 | GitHub Actions | Jenkins | CircleCI |
|------|---------------|---------|----------|
| 비용 | 퍼블릭 무제한 / 프라이빗 월 2,000분 무료 | 오픈소스 (서버 비용 별도) | 월 6,000분 무료 |
| 설정 난이도 | 낮음 (YAML, 레포 내 관리) | 높음 (플러그인, 서버 관리) | 중간 |
| GitHub 연동 | 네이티브 | 플러그인 필요 | 웹훅 설정 필요 |
| 러너 선택 | Ubuntu / Windows / macOS | 직접 구성 | Linux / macOS |
| Marketplace | 25,000+ 액션 | 1,800+ 플러그인 | Orbs |
| 자체 호스팅 | 지원 (Self-hosted Runner) | 기본 | 지원 |

Jenkins는 자유도가 높지만 서버를 직접 관리해야 해요. GitHub 레포랑 연동도 플러그인을 따로 설치해야 하고요. CircleCI는 무료 플랜이 후하지만, 레포 밖에서 설정을 관리해야 한다는 점이 불편해요. GitHub Actions는 레포와 완전히 붙어있어서, 처음 CI/CD 파이프라인 만들기를 시작하는 팀한테 진입 장벽이 가장 낮아요.

---

## 단계별 구축 가이드

### Step 1: 워크플로우 파일 만들기

프로젝트 루트에 `.github/workflows/` 폴더를 만들고, `ci.yml` 파일을 생성해요.

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

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

      - name: Node.js 설정
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: 의존성 설치
        run: npm ci

      - name: 린트 검사
        run: npm run lint

      - name: 단위 테스트
        run: npm test
```

`on` 블록이 트리거예요. `push`와 `pull_request` 두 가지를 걸었으니, main 브랜치에 코드가 올라오거나 PR이 열릴 때 자동 실행돼요.

---

### Step 2: 캐시로 속도 높이기

`setup-node@v4`에 `cache: 'npm'`을 넣으면 `package-lock.json` 해시 기반으로 캐시가 자동 관리돼요. 락파일이 바뀌면 캐시가 무효화되고, 안 바뀌면 저장된 `node_modules`를 그대로 써요.

직접 캐시를 제어하고 싶다면 이렇게 써요:

```yaml
      - name: 캐시 설정 (수동)
        uses: actions/cache@v4
        with:
          path: ~/.npm
          key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
          restore-keys: |
            ${{ runner.os }}-node-
```

캐시 방식은 크게 두 가지예요. `setup-*` 내장 캐시가 설정이 제일 간단하고, `actions/cache@v4`는 경로를 직접 지정할 때 써요.

---

### Step 3: test → build → deploy 파이프라인 연결

실제 배포까지 이어지는 파이프라인은 세 Job이 순서대로 실행돼야 해요. `needs` 키워드가 그걸 강제해요.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm test

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run build
      - name: 아티팩트 업로드
        uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/
          retention-days: 3

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: 아티팩트 다운로드
        uses: actions/download-artifact@v4
        with:
          name: build-output
      - name: 서버 배포
        run: echo "배포 스크립트 실행"
```

`test → build → deploy` 체인에서 앞 단계가 실패하면 다음 단계는 실행되지 않아요.

---

### Step 4: Secrets 설정하기

배포에 쓰는 SSH 키, API 토큰 같은 민감 정보는 절대 YAML에 직접 쓰면 안 돼요.

GitHub 레포 → **Settings → Secrets and variables → Actions**에서 추가하면 돼요.

```yaml
      - name: SSH로 EC2 배포
        uses: appleboy/ssh-action@v0.1.5
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ${{ secrets.EC2_USER }}
          key: ${{ secrets.EC2_PRIVATE_KEY }}
          script: |
            cd /app
            git pull origin main
            npm ci --production
            pm2 restart app
```

참고로, 포크된 레포에서 온 PR은 Secrets에 접근할 수 없어요. 보안 기본값이에요.

---

## 실전 예시: Node.js + EC2 전체 파이프라인

```yaml
name: Production Deploy

on:
  push:
    branches: [main]

concurrency:
  group: production
  cancel-in-progress: true

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm audit --audit-level high
      - run: npm test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: appleboy/ssh-action@v0.1.5
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ubuntu
          key: ${{ secrets.EC2_PRIVATE_KEY }}
          script: |
            cd /var/www/myapp
            git pull origin main
            npm ci --production
            pm2 reload ecosystem.config.js --env production
```

`concurrency` 블록이 핵심이에요. 배포가 두 번 겹쳐서 실행되면 서버 상태가 꼬일 수 있는데, 이걸로 이전 실행을 자동 취소해요.

---

## 흔한 실수와 해결법

**함정 1: YAML 들여쓰기 오류**
YAML은 탭이 아닌 스페이스예요. VS Code에서 `.yml` 파일 열면 오른쪽 하단에서 들여쓰기 타입을 확인할 수 있어요. GitHub Actions 워크플로우 파일 편집 시 내장 린터가 오류를 바로 표시해줘요.

**함정 2: `npm install` 대신 `npm ci` 안 쓰기**
`npm install`은 `package-lock.json`을 수정할 수 있어서 CI 환경에서 재현성이 떨어져요. CI 환경에선 항상 `npm ci` 써요.

**함정 3: Secrets를 코드에 직접 하드코딩**
로그에 그대로 노출돼요. GitHub이 알려진 시크릿 패턴을 자동 마스킹하지만, 100% 믿으면 안 돼요. 모든 민감값은 Secrets에만 저장하고 `${{ secrets.KEY_NAME }}`으로만 참조해요.

### 프로덕션 체크리스트
- [ ] `npm audit --audit-level high` 파이프라인에 포함
- [ ] Secrets로 민감 정보 관리
- [ ] `concurrency` 블록으로 중복 배포 방지
- [ ] `environment: production`으로 승인 게이트 설정
- [ ] 아티팩트 보관 기간 설정 (`retention-days`)

---

## 마무리 및 다음 단계

정리하면 이래요:

- YAML 파일 하나로 테스트부터 배포까지 자동화
- `needs`로 순서 보장, `concurrency`로 중복 방지
- `setup-node` 내장 캐시로 속도 확보
- Secrets로 민감 정보 안전하게 관리

오늘 당장 여러분 레포에 `.github/workflows/ci.yml`을 만들어 보세요. Step 1의 기본 코드를 그대로 복사해서 붙여넣으면 5분 안에 첫 CI 파이프라인이 돌아가요. 생각보다 빠르죠.

다음 단계로는 Matrix 빌드로 여러 Node 버전을 동시에 테스트하거나, Self-hosted Runner로 EC2를 직접 연결하는 것도 도전해 보세요. 막히는 부분 있으면 댓글 남겨요!

## 참고자료

1. [P4_기존 프로젝트에 배포 자동화 구축하기(github actions)_1 :: Fadet's coding box](https://fadet-coding.tistory.com/92)
2. [[GitHub 입문 #11] GitHub Actions 입문: CI/CD 파이프라인 구축하기 | Park Labs](https://blog.park-labs.com/posts/github-series-11-github-actions-intro/)
3. [EC2와 GitHub Actions를 활용한 배포 파이프라인 구축: 효율적인 CI/CD 구현 가이드 — 기피말고깊이](https://notavoid.tistory.com/157)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-white-dice-with-a-black-github-logo-on-it-HLQDfaJUTVI)*
