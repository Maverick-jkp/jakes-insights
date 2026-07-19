---
title: "Cloudflare Pages Hugo 빌드 시간 초과 원인과 대용량 이미지 해결법"
date: 2026-05-27T22:15:39+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-cloud", "cloudflare", "pages", "hugo", "Next.js"]
description: "Cloudflare Pages 빌드 20분 제한 초과 문제, 원인은 Hugo 이미지 처리입니다. 5MB 이상 PNG 파일이 많으면 빌드 시간이 비선형 증가하며, Cloudflare Images로 분리해 해결하는 방법을 설명합니다."
image: "/images/20260527-cloudflare-pages-hugo-배포-빌드-시간.webp"
technologies: ["Next.js", "Vercel", "Go", "Cloudflare", "Hugo"]
faq:
  - question: "Cloudflare Pages Hugo 배포 빌드 시간 초과 오류 대용량 이미지 해결법 뭐가 제일 빠름?"
    answer: "Cloudflare Pages Hugo 배포 빌드 시간 초과 오류 대용량 이미지 해결법 중 가장 빠른 임시 방법은 Hugo가 생성한 resources/_gen 폴더를 .gitignore에서 제외하고 Git에 직접 커밋하는 것입니다. 이렇게 하면 Cloudflare Pages가 빌드 시 이미지를 재처리하지 않고 캐시를 그대로 사용해 빌드 시간을 60~70% 단축할 수 있습니다. 단, 이미지가 많아질수록 리포지토리 용량이 급격히 커지므로 장기적으로는 외부 CDN 분리를 권장합니다."
  - question: "Cloudflare Pages 무료 플랜 빌드 시간 제한 몇 분이에요?"
    answer: "Cloudflare Pages 무료 플랜의 빌드 제한 시간은 20분이며, 월 빌드 횟수는 500회, 동시 빌드는 1건으로 제한됩니다. Hugo 사이트에서 대용량 이미지가 많을 경우 이미지 리사이징과 WebP 변환 작업이 CPU를 집중적으로 사용해 이 20분 한도를 쉽게 초과할 수 있습니다."
  - question: "Hugo 빌드할 때마다 이미지 처음부터 다시 처리되는 이유"
    answer: "Hugo는 처리된 이미지를 resources/_gen 폴더에 캐싱하지만, Cloudflare Pages는 매 빌드마다 새로운 컨테이너를 생성하기 때문에 이전 빌드 캐시가 삭제됩니다. 결과적으로 글 하나를 수정하더라도 사이트 내 모든 이미지를 처음부터 다시 처리하게 되어 빌드 시간이 급증합니다."
  - question: "Cloudflare Images 쓰면 Hugo 빌드 시간 얼마나 줄어드나요?"
    answer: "Cloudflare Images를 사용해 이미지를 빌드 파이프라인 외부로 분리하면 빌드 시간을 최대 80% 단축할 수 있습니다. Hugo 템플릿에서는 이미지 URL만 참조하고 실제 변환은 Cloudflare 엣지에서 요청 시점에 처리되므로, 빌드 시 이미지 처리 부하가 거의 사라집니다. 다만 Cloudflare Images는 월 $5부터 비용이 발생하므로 중대형 사이트에 적합합니다."
  - question: "Cloudflare Pages Hugo 빌드 시간 초과 오류 해결 플랜 업그레이드로 되나요?"
    answer: "Cloudflare Pages Hugo 배포 빌드 시간 초과 오류 대용량 이미지 해결법으로 Pro 플랜 업그레이드(월 $20)를 고려할 수 있지만, 이는 빌드 시간 한도만 늘려줄 뿐 근본적인 해결책이 아닙니다. 이미지가 계속 늘어나면 동일한 문제가 반복되기 때문에, 이미지 사전 최적화나 외부 CDN 분리처럼 빌드 파이프라인 자체의 부하를 줄이는 방법이 장기적으로 더 효과적입니다."
aliases:
  - "/tech/2026-05-27-cloudflare-pages-hugo-배포-빌드-시간-초과-오류-대용량-이미지-해결법/"
  - "/ko/tech/2026-05-27-cloudflare-pages-hugo-배포-빌드-시간-초과-오류-대용량-이미지-해결법/"

---

Hugo로 정적 사이트를 만들다 보면 어느 순간 Cloudflare Pages 배포가 갑자기 멈춰버리는 상황을 맞닥뜨려요. 빌드 로그 마지막 줄에는 `Build exceeded maximum allowed duration`이라는 메시지만 남고요. 문제는 코드가 아니에요. 대부분 이미지 때문이에요.

> **핵심 요약**
> - Cloudflare Pages 무료 플랜의 빌드 제한 시간은 20분으로, 대용량 이미지가 많은 Hugo 사이트는 이 한도를 쉽게 초과해요.
> - Hugo의 내장 이미지 처리 파이프라인(`resources.Process`)은 PNG 기준 5MB 이상 파일에서 빌드 시간이 비선형적으로 증가해요.
> - Cloudflare Images 또는 외부 CDN으로 이미지를 분리하면 빌드 시간을 최대 80% 단축할 수 있어요.
> - 2026년 기준 Cloudflare 무료 플랜은 월 500회 빌드, 스토리지 25GB 제한이 있어 이미지 관리 전략이 배포 안정성과 직결돼요.

---

## 2026년에 이 문제가 더 자주 터지는 이유

Hugo는 지금 Next.js, Astro와 함께 정적 사이트 생성기(SSG) 시장의 3대 선택지예요. 2025 Jamstack Community Survey 기준으로 전체 SSG 사용자의 약 18%가 Hugo를 쓰고 있고, 특히 기술 블로그와 문서 사이트에서 선호도가 높죠.

문제는 콘텐츠 규모가 커지는 속도예요. 블로그 포스트 하나에 Retina 대응 이미지를 3~5장 넣는 게 이제 일반적인 패턴이 됐어요. 이미지 한 장이 3~8MB라면, 글이 50개만 넘어도 Hugo가 처리해야 할 이미지 총량은 수백 MB에 달해요.

Cloudflare Pages 무료 플랜의 빌드 제한 시간은 20분, 월 빌드 횟수는 500회, 동시 빌드는 1건이에요. 여기에 Hugo의 이미지 처리(리사이징, WebP 변환, 썸네일 생성)가 겹치면 빌드 시간이 기하급수적으로 늘어나요. 글 하나 고쳤을 뿐인데 코드 배포가 이미지 병목 때문에 막히는 거죠.

---

## 빌드 시간 초과의 실제 구조

### Hugo 이미지 처리가 빌드를 잡아먹는 이유

Hugo의 이미지 파이프라인은 강력하지만 무거워요. `resources.Fit`, `resources.Fill`, `resources.Process` 같은 함수를 템플릿에서 호출하면 Hugo는 빌드 시점에 원본 이미지를 읽고, 리사이징하고, 포맷을 변환해요. 이 작업은 CPU 바운드 연산이라 이미지가 많을수록 선형이 아니라 계단식으로 시간이 늘어요.

실제 패턴을 보면:

- 이미지 10장(각 2MB) → 빌드 시간 약 2~3분
- 이미지 50장(각 4MB) → 빌드 시간 약 12~15분
- 이미지 100장(각 5MB+) → 빌드 시간 20분 초과로 타임아웃 발생

Cloudflare Pages는 빌드 컨테이너 스펙이 공개되어 있지 않지만, 공유 환경에서 CPU 성능이 제한되기 때문에 로컬 빌드보다 3~5배 느린 경우도 흔해요.

### 캐시가 없으면 매번 처음부터

Hugo는 `resources/_gen` 폴더에 처리된 이미지를 캐싱해요. 로컬에서는 잘 작동하는데, Cloudflare Pages는 기본적으로 매 빌드마다 새로운 컨테이너를 띄워요. 이전 빌드 캐시가 사라지는 거죠.

결국 이미지 100장짜리 사이트는 배포 버튼을 누를 때마다 100장을 처음부터 처리해요. 글 하나 고쳤을 뿐인데도요. 이게 빌드 시간 초과 오류의 가장 큰 구조적 원인이에요.

### 접근법 비교

| 방식 | 빌드 시간 단축 | 비용 | 구현 난이도 | 적합한 규모 |
|------|--------------|------|------------|------------|
| Hugo 이미지 캐시 커밋 | 높음 (60~70%) | 무료 | 낮음 | 소~중형 사이트 |
| Cloudflare Images 분리 | 매우 높음 (80%+) | 월 $5~ | 중간 | 중~대형 사이트 |
| 외부 CDN (Cloudinary 등) | 높음 (70~80%) | 무료 플랜 있음 | 중간 | 이미지 중심 사이트 |
| 이미지 사전 최적화 후 업로드 | 중간 (40~50%) | 무료 | 낮음 | 모든 규모 |
| Cloudflare Pages Pro 업그레이드 | 낮음 (제한 시간만 증가) | 월 $20 | 매우 낮음 | 임시방편 |

비용과 효과를 같이 보면 방향이 명확해요. 단순히 플랜을 올리는 건 근본 해결이 아니에요. 빌드 시간 한도가 늘어날 뿐, 이미지가 늘수록 같은 문제가 반복돼요.

---

## 실전 해결법: 시나리오별로 뭘 해야 하나요?

### 시나리오 1: 빠르게 막아야 할 때 (캐시 커밋)

가장 빠른 임시 해결책은 Hugo가 생성한 `resources/_gen` 폴더를 `.gitignore`에서 빼고 Git에 커밋하는 거예요. Cloudflare Pages는 리포지토리를 클론해서 빌드를 돌리기 때문에, 캐시 파일이 리포지토리 안에 있으면 재처리를 건너뛰어요.

```bash
# .gitignore에서 이 줄을 제거하거나 주석 처리
# resources/_gen
```

단, 이미지가 많은 사이트라면 리포지토리가 수백 MB가 되는 건 시간문제예요. 단기 해결책으로만 쓰세요.

### 시나리오 2: 근본적으로 분리하고 싶을 때 (외부 CDN)

Cloudflare Images는 이미지 저장과 변환을 빌드 파이프라인 밖으로 꺼내는 서비스예요. Hugo 템플릿에서는 이미지 URL만 참조하고, 실제 변환은 Cloudflare 엣지에서 요청 시점에 처리해요.

```html
<!-- 기존 Hugo 이미지 처리 -->
{{ $img := .Resources.GetMatch "cover.jpg" }}
{{ $resized := $img.Resize "800x" }}
<img src="{{ $resized.RelPermalink }}">

<!-- Cloudflare Images 사용 시 -->
<img src="https://imagedelivery.net/{account_hash}/{image_id}/w=800">
```

빌드 시 이미지 처리가 아예 없어지니 Hugo 빌드는 텍스트 렌더링만 담당하게 돼요. 빌드 시간이 대부분 1~3분 이내로 줄어들어요.

### 시나리오 3: 무료로 해결하고 싶을 때 (사전 최적화)

업로드 전에 이미지를 WebP나 AVIF 포맷으로 미리 변환하고, 해상도도 최대 1,920px로 제한하는 거예요. `squoosh-cli`나 `sharp` CLI를 로컬 전처리 스크립트로 쓰면 Hugo에 들어오는 원본 파일 크기를 70~80% 줄일 수 있어요.

```bash
npx @squoosh/cli --webp '{}' --resize '{"width":1920}' ./static/images/*.jpg
```

Hugo가 처리할 원본이 작아지면 빌드 시간도 비례해서 줄어들어요. 추가 비용 없이 효과를 볼 수 있는 방법이에요.

---

## 지금 당장 확인해야 할 것들

빌드 시간 초과 오류를 진단하는 순서를 정리하면:

1. **빌드 로그 확인**: Pages 대시보드 → 해당 배포 → `View build log` → `Processing images` 항목이 전체 빌드 시간의 절반 이상이면 이미지가 원인이에요.
2. **이미지 총 용량 측정**: `find ./static -name "*.jpg" -o -name "*.png" | xargs du -sh` 로 원본 크기 확인.
3. **Hugo 캐시 여부 확인**: 로컬에서 `hugo --gc` 후 `resources/_gen` 폴더 크기가 크다면 Cloudflare에서 매번 재생성 중인 거예요.
4. **단계별 해결**: 이미지 사전 최적화 → 캐시 커밋 → 외부 CDN 분리 순으로 필요한 만큼만 적용하면 돼요.

참고로, Vercel과 Netlify는 이미 빌드 캐시 퍼시스턴스를 지원하고 있어요. 경쟁 압박 때문에 Cloudflare Pages도 향후 6~12개월 내에 이 기능을 정식 지원할 가능성이 있어요. 그전까지는 이미지를 빌드 파이프라인 밖으로 꺼내는 게 가장 확실한 방법이에요.

한 줄로 요약하면: **Hugo에게 이미지를 맡기지 마세요.** 이미지는 CDN에, Hugo는 텍스트에. 역할을 나누는 순간 20분짜리 타임아웃 문제는 사라져요. 지금 빌드 로그를 열어보면 어디서 시간이 가장 많이 쓰이는지 바로 보일 거예요.

## 참고자료

1. [[배포] Cloudflare Pages 배포에 인증 추가하기](https://meal-coding.tistory.com/54)
2. [Cloudflare 오류가 발생했을 때 해결하는 방법 | Octoparse](https://www.octoparse.kr/blog/cloudflare-error-codes)
3. [클라우드플레어 무료 플랜, 어디까지 가능할까? (요청, 빌드, 스토리지 제한 총정리) - Sentio](https://sentio5.com/entry/cloudflare-free-plan-limits/)


---

*Photo by [Growtika](https://unsplash.com/@growtika) on [Unsplash](https://unsplash.com/photos/a-computer-tower-with-a-purple-light-wlQUkvDhvQw)*
