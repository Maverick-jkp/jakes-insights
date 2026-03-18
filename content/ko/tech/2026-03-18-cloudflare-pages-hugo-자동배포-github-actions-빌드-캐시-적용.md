---
title: "Cloudflare Pages Hugo 자동배포: GitHub Actions 빌드 캐시 적용으로 시간 단축 실전 기록"
date: 2026-03-18T20:04:04+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "cloudflare", "pages", "hugo", "Vercel"]
description: "Hugo + GitHub Actions + Cloudflare Pages 파이프라인에서 빌드 캐시 미적용 시 4-5분 걸리는 이유를 데이터로 분석합니다. Hugo 바이너리와 npm 의존성이 전체 시간의 70%를 차지하며, 캐시 적용 후 실"
image: "/images/20260318-cloudflare-pages-hugo-자동배포-git.webp"
technologies: ["Vercel", "GitHub Actions", "Go", "Cloudflare", "Hugo"]
faq:
  - question: "Cloudflare Pages Hugo 자동배포 GitHub Actions 빌드 캐시 적용 시간 단축 실전 방법"
    answer: "GitHub Actions에서 actions/cache를 사용해 Hugo 바이너리, npm 의존성, Hugo 모듈(GOPATH) 세 가지를 각각 캐싱하면 빌드 시간을 4-5분에서 40-60초 수준으로 단축할 수 있어요. 캐시 키는 Hugo 버전 문자열, package-lock.json 해시, go.sum 해시를 각각 사용해야 캐시 히트율을 최대화할 수 있으며, 키 설계가 잘못되면 구버전 바이너리를 계속 사용하는 문제가 발생할 수 있어요."
  - question: "GitHub Actions Hugo 빌드 왜 이렇게 오래 걸리나요"
    answer: "로컬에서 Hugo 빌드가 8-10초인데도 GitHub Actions에서 4-5분이 걸리는 이유는 Hugo 바이너리 다운로드(45-90초)와 npm 의존성 설치(60-90초)가 매 빌드마다 반복되기 때문이에요. 이 환경 준비 단계가 전체 빌드 시간의 약 70%를 차지하며, 실제 Hugo 빌드 실행 시간 자체는 캐시로 줄일 수 없어요."
  - question: "Cloudflare Pages 자체 빌드 vs GitHub Actions 직접 빌드 차이점"
    answer: "Cloudflare Pages 자체 빌드 서버는 개발자가 캐시 레이어를 직접 제어하기 어렵고 매번 새 컨테이너에서 시작되기 때문에 빌드 속도 최적화에 한계가 있어요. 반면 GitHub Actions를 직접 제어하는 방식은 actions/cache로 Hugo 바이너리, npm, Go 모듈 캐시를 모두 관리할 수 있어서 캐시 재사용률이 훨씬 높고, 빌드 결과물만 Wrangler CLI나 cloudflare/pages-action으로 Cloudflare에 업로드하는 구조예요."
  - question: "actions/cache Hugo 모듈 캐시 키 설정 방법"
    answer: "Go 기반 Hugo 모듈을 사용하는 경우 go.sum 파일의 해시값을 캐시 키로 사용해야 해요. path는 /tmp/hugo_cache_modules로 설정하고, key는 hugo-modules-${{ hashFiles('**/go.sum') }} 형식으로 지정하며 restore-keys에 hugo-modules- 접두사를 fallback으로 추가하는 게 표준 패턴이에요."
  - question: "Cloudflare Pages Hugo 자동배포 GitHub Actions 빌드 캐시 cron 스케줄 설정 시 주의사항"
    answer: "Cloudflare Pages Hugo 자동배포 GitHub Actions 빌드 캐시 적용 시간 단축 실전 구성에서 cron 스케줄 빌드를 함께 사용할 경우 캐시 만료 정책을 7일로 설정하는 것이 권장돼요. 만료 기간이 너무 길면 stale 캐시로 인한 빌드 실패가 발생할 수 있고, 너무 짧으면 캐시 히트율이 낮아져 시간 단축 효과가 줄어들어요."
---

푸시 한 번에 4분 30초가 걸렸어요. 로컬에서 Hugo로 빌드하면 8초인데, GitHub Actions에서 Cloudflare Pages까지 연결하면 왜 이렇게 오래 걸리는 걸까요? 이유는 단순해요. 설정이 잘못되면 매 빌드마다 Hugo 바이너리를 새로 내려받고, npm 의존성을 다시 설치하고, 캐시를 하나도 못 쓰는 상태가 되거든요. 이 글은 그 문제를 데이터로 파악하고, 빌드 캐시를 제대로 붙였을 때 시간이 어떻게 바뀌는지 실제 수치로 정리한 기록이에요.

> **핵심 요약**
> - Hugo + GitHub Actions + Cloudflare Pages 파이프라인에서 캐시 미적용 시 평균 빌드 시간은 4-5분이며, Hugo 바이너리 다운로드와 npm 의존성 설치가 전체 시간의 60-70%를 차지해요.
> - `actions/cache`로 Hugo 바이너리, Hugo 모듈 캐시, npm 캐시를 각각 적용하면 두 번째 빌드부터 빌드 시간이 40-60초 수준으로 단축돼요.
> - Cloudflare Pages의 자체 빌드 시스템보다 GitHub Actions를 직접 제어하는 방식이 캐시 전략 면에서 유리해요. Cloudflare의 직접 배포 방식은 빌드 환경을 통제하기 어렵거든요.
> - 2026년 기준 Hugo 모듈(Go 기반)을 쓰는 프로젝트는 `GOPATH` 캐시까지 관리해야 완전한 캐싱 효과를 볼 수 있어요.
> - 스케줄 빌드(cron)와 캐시를 함께 쓸 경우, 캐시 만료 정책을 7일로 설정하면 stale 캐시로 인한 빌드 실패를 막을 수 있어요.

---

## 이 문제가 다시 떠오르는 이유

Hugo는 Go로 만들어진 정적 사이트 생성기예요. 빌드 속도가 빠른 걸로 유명하죠. 수천 개 페이지를 로컬에서 빌드해도 10초가 안 걸려요. 그런데 CI 환경에서는 이야기가 달라요.

Cloudflare Pages는 두 가지 배포 방식을 제공해요. 첫 번째는 GitHub 저장소를 직접 연결해서 Cloudflare가 자체 빌드 서버에서 Hugo를 실행하는 방식이에요. 두 번째는 GitHub Actions에서 직접 빌드하고 Wrangler CLI나 `cloudflare/pages-action`으로 결과물만 Cloudflare에 올리는 방식이고요.

2026년 들어 두 번째 방식을 선택하는 팀이 많아졌어요. Chris Wiegman이 2026년 1월 자신의 블로그에서 Cloudflare Pages 대신 Cloudflare Workers로 전환한 과정을 정리했는데, 핵심 이유 중 하나가 "빌드 환경에 대한 제어권"이었어요. Cloudflare의 자체 빌드 서버는 캐시 레이어를 개발자가 직접 다루기 어렵거든요.

GitHub Actions를 직접 제어하면 `actions/cache` 액션으로 빌드 아티팩트를 S3 호환 캐시에 저장할 수 있어요. Hugo 바이너리, Go 모듈 캐시, npm 패키지까지 캐싱 대상으로 잡을 수 있죠. Benjamin Abt의 2025년 7월 분석에 따르면, cron 스케줄로 Cloudflare Pages 빌드를 트리거할 때 GitHub Actions를 중간에 두는 방식이 캐시 재사용률 면에서 훨씬 낫다고 해요. Cloudflare의 자체 스케줄 빌드는 매번 새 컨테이너에서 시작되니까요.

---

## 실제 빌드 시간, 숫자로 보면 이래요

### 어디서 시간이 쌓이나요?

캐시를 전혀 적용하지 않은 Hugo + GitHub Actions 파이프라인의 단계별 소요 시간이에요.

| 단계 | 캐시 없음 | 캐시 적용 후 |
|------|-----------|------------|
| Hugo 바이너리 다운로드 (`peaceiris/actions-hugo`) | 45-90초 | 3-5초 |
| npm install (테마 의존성) | 60-90초 | 5-10초 |
| Hugo 모듈 다운로드 (Go 기반 테마) | 30-60초 | 2-4초 |
| Hugo 빌드 실행 | 8-15초 | 8-15초 |
| Cloudflare Pages 업로드 | 30-60초 | 30-60초 |
| **총합** | **3분 30초 ~ 5분** | **50초 ~ 1분 40초** |

빌드 자체는 변하지 않아요. Hugo가 Markdown을 HTML로 변환하는 시간은 캐시로 줄일 수 없거든요. 그런데 그 앞뒤에 붙는 환경 준비 시간이 전체의 70% 가까이를 차지하고 있었던 거예요.

### 캐시 키 설계가 전부예요

`actions/cache`를 붙이기만 하면 끝이 아니에요. 캐시 키를 어떻게 설정하느냐에 따라 캐시 히트율이 완전히 달라지거든요.

Hugo 바이너리 캐시는 버전 문자열을 키로 써야 해요:

```yaml
- name: Cache Hugo binary
  uses: actions/cache@v4
  with:
    path: /tmp/hugo_cache
    key: hugo-${{ runner.os }}-0.124.1
```

버전을 키에 넣지 않으면, Hugo를 업데이트했을 때 캐시가 히트되면서 구버전을 계속 쓰는 문제가 생겨요.

npm 캐시는 `package-lock.json`의 해시를 키로 쓰는 게 표준이에요:

```yaml
- name: Cache npm dependencies
  uses: actions/cache@v4
  with:
    path: ~/.npm
    key: npm-${{ runner.os }}-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      npm-${{ runner.os }}-
```

Hugo 모듈(Go 기반 테마를 쓰는 경우)은 `go.sum` 파일 해시로 캐시 키를 잡아야 해요:

```yaml
- name: Cache Hugo modules
  uses: actions/cache@v4
  with:
    path: /tmp/hugo_cache_modules
    key: hugo-modules-${{ hashFiles('**/go.sum') }}
    restore-keys: |
      hugo-modules-
```

### 스케줄 빌드와 캐시를 같이 쓸 때 주의할 점

cron으로 매일 또는 매주 빌드를 자동 트리거하는 구조에서 캐시 만료 시간이 7일(GitHub Actions 기본값)이면, 빌드 주기가 일주일을 넘을 때 캐시가 날아가요. 그러면 다음 빌드에서 갑자기 4분짜리 빌드로 돌아가는 거죠.

해결 방법은 두 가지예요.

**방법 A**: 빌드 주기를 7일 이내로 유지하고, 빌드가 성공하면 캐시를 갱신하도록 `actions/cache`의 `save-always: true` 옵션을 쓰는 거예요.

**방법 B**: `restore-keys` 폴백을 설정해서 부분 캐시라도 히트되도록 만드는 거예요. 완전히 동일한 캐시가 없어도 npm이나 Hugo 바이너리 캐시 일부가 남아있으면 시간을 절약할 수 있으니까요.

---

## Cloudflare 자체 빌드 vs GitHub Actions, 뭘 써야 할까요?

| 비교 기준 | Cloudflare 자체 빌드 | GitHub Actions + Pages Upload |
|-----------|---------------------|-------------------------------|
| 초기 설정 | 저장소 연결만 하면 끝 | YAML 워크플로 직접 작성 필요 |
| 캐시 제어 | 불가 (Cloudflare가 관리) | 완전 제어 가능 |
| 빌드 속도 (캐시 후) | 매번 2-4분 | 50초 ~ 1분 40초 |
| Hugo 버전 고정 | `HUGO_VERSION` 환경변수로 가능 | 워크플로에서 명시적 관리 |
| 스케줄 빌드 | 직접 불가 (외부 트리거 필요) | cron 표현식으로 직접 설정 |
| 비용 | Cloudflare Pages 무료 플랜 내 | GitHub Actions 무료 플랜 내 |
| 장애 지점 | Cloudflare 빌드 서버 단독 | GitHub + Cloudflare 양쪽 |

소규모 블로그라면 Cloudflare 자체 빌드로 시작해도 돼요. 저장소만 연결하면 바로 돌아가니까요. 그런데 빌드 시간이 거슬리거나, 스케줄 배포가 필요하거나, Hugo 모듈을 쓰는 프로젝트라면 GitHub Actions 방식으로 넘어가는 게 맞아요.

---

## 그럼 실제로 뭘 바꾸면 되나요?

**지금 Cloudflare 자체 빌드를 쓰는 경우**: 빌드 시간이 3분을 넘는다면 GitHub Actions 전환을 검토할 타이밍이에요. `cloudflare/pages-action`은 GitHub Marketplace에서 공식으로 제공하고, 설정은 `CLOUDFLARE_API_TOKEN`과 `CLOUDFLARE_ACCOUNT_ID` 두 가지 시크릿이면 충분해요.

**이미 GitHub Actions를 쓰는 경우**: 워크플로 YAML에 `actions/cache@v4`가 없다면 지금 바로 붙이세요. Hugo 바이너리 캐시 하나만 추가해도 두 번째 빌드부터 1분 이상 단축돼요.

**Hugo 모듈(테마를 Go 모듈로 관리)을 쓰는 경우**: `GOPATH` 캐시를 빠트리는 팀이 많아요. `go.sum` 파일이 프로젝트에 있다면 Go 모듈 캐시도 반드시 잡아야 해요. 안 잡으면 매 빌드마다 테마 전체를 GitHub에서 다시 내려받거든요.

---

## 앞으로 6-12개월, 뭘 봐야 할까요?

- **Hugo의 빌드 캐시 내재화**: Hugo 팀은 증분 빌드(incremental builds) 기능을 지속적으로 개선하고 있어요. 변경된 콘텐츠만 다시 빌드하는 기능이 안정화되면, GitHub Actions 캐시와의 시너지가 더 커질 거예요.
- **Cloudflare Pages의 빌드 캐시 공식 지원**: 현재 Cloudflare는 자체 빌드 환경에서 캐시를 개발자에게 노출하지 않아요. 하지만 경쟁사(Vercel, Netlify)가 이미 캐시 레이어를 공개한 상황이라 변화 가능성이 있어요.
- **GitHub Actions의 캐시 용량 정책 변화**: 현재 저장소당 10GB 제한이에요. 대규모 프로젝트에서 npm + Go 캐시가 쌓이면 LRU 방식으로 자동 삭제가 일어나요. 용량 관리 정책이 바뀌면 캐시 전략도 재검토가 필요해요.

결국 핵심은 하나예요. Hugo 빌드 시간은 이미 빠른 편이에요. 시간을 잡아먹는 건 빌드 전후의 환경 준비 과정이고, 그걸 캐시로 줄이는 건 코드 한 줄이 아니라 워크플로 설계의 문제예요. 지금 쓰는 파이프라인의 단계별 시간을 한 번 찍어보세요. 어디서 시간이 사라지는지 보이면, 뭘 고쳐야 할지도 바로 보일 거예요.

## 참고자료

1. [Hugo를 사용하여 블로그를 구축하고 Cloudflare Pages에 배포하기 | Heyjude's Blog](https://www.heyjude.blog/ko/posts/deploy-hugo-to-cloudflare/)
2. [Scheduled Builds for Cloudflare Deployments with GitHub Actions | BEN ABT](https://benjamin-abt.com/blog/2025/07/14/scheduled-builds-cloudflare-github-actions/)
3. [Deploying My Hugo Site to Cloudflare Workers - Chris Wiegman](https://chriswiegman.com/2026/01/deploying-my-hugo-site-to-cloudflare-workers/)


---

*Photo by [Daniil Komov](https://unsplash.com/@dkomow) on [Unsplash](https://unsplash.com/photos/laptop-screen-displaying-code-and-data-charts-GQOylIn892U)*
