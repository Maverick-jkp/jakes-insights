---
title: "Vercel 무료 플랜 cron 실행 안 될 때 GitHub Actions로 대체한 실전 후기"
date: 2026-04-15T20:21:41+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "vercel", "\uc2a4\ucf00\uc904", "cron", "Next.js"]
description: "Vercel 무료 플랜 cron 함수가 조용히 실행 안 되는 이유와 해결법을 정리했습니다. Hobby 플랜의 일 1회 제한을 GitHub Actions schedule 트리거로 우회해 5분 단위 실행까지 무료로 구현하는 실전 방"
image: "/images/20260415-vercel-스케줄-cron-함수-무료-플랜-실행-안될.webp"
technologies: ["Next.js", "Vercel", "GitHub Actions"]
faq:
  - question: "Vercel 무료 플랜 cron 설정했는데 실행이 안 되는 이유"
    answer: "Vercel Hobby(무료) 플랜은 cron 함수 실행을 하루 1회, daily 주기로만 제한하고 있어서 1시간·30분 단위 스케줄은 구조적으로 실행되지 않습니다. 더 짜증스러운 점은 에러 메시지 없이 조용히 스킵되기 때문에 처음엔 코드 문제로 오해하기 쉽다는 것입니다. 분·시간 단위 cron을 사용하려면 Pro 플랜($20/월) 이상으로 업그레이드해야 합니다."
  - question: "Vercel 스케줄 cron 함수 무료 플랜 실행 안될 때 GitHub Actions 대체 구현 방법"
    answer: "'Vercel 스케줄 cron 함수 무료 플랜 실행 안될 때 GitHub Actions 대체 구현 실전 후기'에서 소개된 방법은 Vercel에 일반 API 엔드포인트를 열어두고 GitHub Actions의 schedule 트리거로 주기적으로 HTTP 요청을 보내는 방식입니다. .github/workflows/ 폴더에 YAML 파일 하나와 시크릿 토큰 설정만으로 구현 가능하며, 기존 Vercel 코드 변경을 최소화할 수 있습니다. GitHub Actions는 월 2,000분까지 무료로 제공되어 Pro 플랜 비용 없이 원하는 주기로 백그라운드 작업을 실행할 수 있습니다."
  - question: "GitHub Actions schedule cron 정확도 얼마나 되나요"
    answer: "GitHub Actions의 schedule 트리거는 트래픽이 많을 때 2~10분 정도 지연이 발생할 수 있으며, GitHub 공식 문서에서도 이를 명시하고 있습니다. 따라서 결제 처리나 정시 알림처럼 정밀한 타이밍이 필요한 작업에는 적합하지 않습니다. 데이터 수집, 캐시 갱신, 배치 처리 등 약간의 지연이 허용되는 작업에 사용하는 것이 적합합니다."
  - question: "Vercel cron GitHub Actions로 대체할 때 보안 설정 어떻게 하나요"
    answer: "API 엔드포인트가 외부에 노출되므로 요청 헤더에 Authorization: Bearer 형태로 시크릿 토큰을 붙여 검증하는 방식을 사용해야 합니다. Vercel 환경 변수와 GitHub 레포의 Settings → Secrets에 동일한 CRON_SECRET 값을 등록해두면 코드에 하드코딩 없이 안전하게 관리할 수 있습니다. API 라우트에서 토큰이 일치하지 않으면 401 응답을 반환하도록 구현하면 무단 호출을 차단할 수 있습니다."
  - question: "Vercel 스케줄 cron 함수 무료 플랜 실행 안될 때 GitHub Actions 말고 다른 대안은"
    answer: "'Vercel 스케줄 cron 함수 무료 플랜 실행 안될 때 GitHub Actions 대체 구현 실전 후기'에서 다룬 GitHub Actions 방식 외에도 Vercel Pro 플랜으로 업그레이드($20/월)하는 방법이 있습니다. Pro 플랜은 설정 복잡도가 낮고 실행 정확도가 높으며 Vercel 대시보드에서 로그를 바로 확인할 수 있다는 장점이 있습니다. 이미 Pro 플랜을 사용 중이거나 정밀한 타이밍이 필요한 경우라면 Vercel 자체 cron을 그대로 쓰는 것이 더 나은 선택입니다."
aliases:
  - "/tech/2026-04-15-vercel-스케줄-cron-함수-무료-플랜-실행-안될-때-github-actions-대체/"

---

Vercel 무료 플랜에서 cron 설정했는데 아무것도 안 돌아간 경험, 있으시죠? 로그도 없고, 에러도 없고, 그냥 조용히 아무 일도 일어나지 않는 그 상황. 알고 보면 플랜 제한 때문인데, 에러 메시지조차 없으니 처음엔 내 코드 문제인 줄 알고 한참 헤매게 돼요.

> **핵심 요약**
> - Vercel 무료 플랜(Hobby)은 cron 함수 실행을 일 1회로 제한하며, 최소 실행 간격도 1일(daily)로 고정되어 있어요.
> - GitHub Actions의 `schedule` 트리거는 완전 무료로 매 5분 단위까지 cron 실행이 가능해요.
> - Vercel API 엔드포인트를 열어두고 GitHub Actions에서 HTTP 요청을 보내는 방식으로 기존 코드 변경을 최소화할 수 있어요.
> - 이 패턴을 적용하면 Vercel Pro($20/월) 업그레이드 없이도 원하는 주기로 백그라운드 작업을 돌릴 수 있어요.
> - 단, GitHub Actions 무료 티어는 월 2,000분 제한이 있어서 실행 빈도와 잡 런타임을 미리 계산해야 해요.

---

## Vercel cron이 무료 플랜에서 막히는 이유

Vercel은 서버리스 함수와 cron 트리거를 같은 인프라 위에서 돌려요. Hobby 플랜 기준으로는 cron 함수 실행이 하루 한 번, 그것도 UTC 자정 기준 daily 주기만 허용돼요. 1시간마다 돌아야 하는 데이터 수집 스크립트나 15분 단위 알림 발송 같은 건 구조적으로 불가능한 거죠.

공식 Vercel 문서에 따르면, 분·시간 단위 cron을 돌리려면 Pro 플랜($20/월) 이상이 필요해요. Vercel 커뮤니티에서도 2024-2025년 사이 "cron이 실행 안 된다"는 글이 꾸준히 올라왔고, 대부분 플랜 제한이 원인이었어요.

가장 짜증스러운 부분은 에러 메시지가 없다는 거예요. 대시보드에서 cron을 설정하면 저장도 되고 다음 실행 예정 시간도 표시돼요. 근데 Hobby 플랜에서 허용되지 않는 주기면 그냥 조용히 스킵해버려요. 처음 마주치면 디버깅에 꽤 시간 날리게 되는 구조예요.

비용 측면도 있어요. 서버리스 함수 호출 횟수가 곧 비용이 되는 구조라 고빈도 cron은 비용 리스크가 있거든요. GitHub Actions로 넘기면 이 리스크도 같이 해결돼요.

---

## GitHub Actions로 cron 대체하는 법: 실제 구현 흐름

개념 자체는 단순해요. Vercel에 HTTP로 호출 가능한 API 엔드포인트를 만들고, GitHub Actions에서 정해진 시간에 그 엔드포인트를 `curl`로 호출하는 거예요.

### 1단계: Vercel에 API 엔드포인트 만들기

Vercel cron 함수를 그대로 일반 API 라우트로 바꾸면 돼요. Next.js 기준으로 `/api/cron-job` 경로에 핸들러를 두고, 외부에서 POST 요청이 오면 실행되게 하면 끝이에요.

보안을 위해 시크릿 토큰 검증은 필수예요. 요청 헤더에 `Authorization: Bearer YOUR_SECRET`을 붙이고, API 라우트에서 이걸 확인하는 방식이에요. Vercel 환경 변수에 `CRON_SECRET`을 등록해두면 코드에 하드코딩할 필요도 없어요.

```js
// pages/api/cron-job.js
export default async function handler(req, res) {
  const secret = req.headers['authorization']?.split('Bearer ')[1];
  if (secret !== process.env.CRON_SECRET) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  await doWork();
  return res.status(200).json({ ok: true });
}
```

### 2단계: GitHub Actions 워크플로우 설정

`.github/workflows/cron.yml` 파일 하나 만들면 돼요.

```yaml
name: Cron Job
on:
  schedule:
    - cron: '*/30 * * * *'  # 30분마다 실행
jobs:
  trigger:
    runs-on: ubuntu-latest
    steps:
      - name: Call Vercel endpoint
        run: |
          curl -X POST \
            -H "Authorization: Bearer ${{ secrets.CRON_SECRET }}" \
            https://your-project.vercel.app/api/cron-job
```

`CRON_SECRET`은 GitHub 레포의 Settings → Secrets에 동일한 값으로 등록해두면 돼요. 배포 없이 환경 변수만 맞춰주면 바로 동작해요.

### 주의할 점

GitHub Actions의 `schedule` 트리거는 정확도가 100%가 아니에요. GitHub 공식 문서에서도 "트래픽이 많을 때 지연이 발생할 수 있다"고 명시하고 있어요. 실제로 5분 단위 cron을 써보면 2-10분 지연이 종종 생겨요. 결제나 알림처럼 정밀한 타이밍이 필요한 작업엔 맞지 않아요.

---

## 두 방식 비교: 내 상황에 뭐가 맞나요?

| 항목 | Vercel Cron (Pro) | GitHub Actions |
|------|-------------------|----------------|
| 비용 | $20/월 (Pro 플랜) | 월 2,000분 무료 |
| 최소 주기 | 1분 | 1분 (schedule) |
| 무료 플랜 지원 | ❌ (daily만) | ✅ |
| 실행 정확도 | 높음 | 중간 (±10분 지연 가능) |
| 설정 복잡도 | 낮음 (`vercel.json`만) | 중간 (YAML + 시크릿) |
| 로그 접근 | Vercel 대시보드 | GitHub Actions 탭 |
| 장애 알림 | 제한적 | 이메일 자동 알림 |

Pro 플랜이 이미 있거나 Vercel 생태계 안에서 모든 걸 해결하고 싶다면 Vercel cron이 더 깔끔해요. 사이드 프로젝트나 초기 스타트업처럼 비용이 민감한 상황이라면 GitHub Actions 조합이 실용적인 선택이에요.

참고로 GitHub Actions 무료 티어는 월 2,000분이에요. 30분마다 실행되는 잡이 1회당 1분이면 한 달에 약 1,440분 써요. 잡이 여러 개거나 런타임이 길면 금방 차거든요. 미리 계산해두는 게 좋아요.

---

## 실제로 쓸 때 생기는 상황들

**매일 자정 한 번 도는 배치 작업**이라면 Vercel Hobby 플랜의 daily cron으로도 충분해요. 억지로 GitHub Actions 쓸 필요 없어요.

**1시간 이내 주기가 필요한 작업** — RSS 피드 수집, 가격 모니터링, 슬랙 리마인더 같은 것들이에요. GitHub Actions + Vercel API 엔드포인트 조합이 가장 현실적이고, 설정 시간도 30분이면 충분해요.

**트래픽 스파이크가 예상되는 서비스**에서 cron을 워밍 목적으로만 쓴다면, 그냥 Vercel Pro cron을 쓰는 게 더 깔끔해요. GitHub Actions 워크플로우를 워밍 전용으로 운영하는 건 오버킬이에요.

그리고 하나 더. Vercel이 Hobby 플랜의 cron 제한 완화를 검토 중이라는 커뮤니티 피드백이 있었어요. 공식 발표는 아직 없지만, 변화 가능성은 열려 있어요. 그 전까지는 GitHub Actions 조합이 현실적인 답이에요.

---

## 돌아가는 코드가 제일 좋은 코드예요

Vercel 스케줄 cron이 무료 플랜에서 실행 안 될 때, 이게 버그가 아니라 설계라는 걸 알면 오히려 마음이 편해져요. 플랫폼의 수익 모델이 반영된 제한이고, GitHub Actions는 그 빈틈을 메워주는 도구예요.

- Vercel Hobby 플랜 cron은 daily 단위만 무료예요
- 더 짧은 주기가 필요하면 GitHub Actions + API 엔드포인트 조합이 현실적이에요
- 시크릿 토큰으로 엔드포인트를 보호하는 건 필수예요
- 실행 정확도가 중요한 작업엔 이 방법이 맞지 않아요

당신 프로젝트에서 cron이 돌아야 하는 주기가 얼마인가요? 그 답에 따라 $20을 쓸지, 30분 들여 GitHub Actions를 설정할지가 결정돼요. 지금 `vercel.json`의 cron 설정이 daily로 묶여 있다면, 오늘 저녁에 워크플로우 파일 하나 만들어보는 게 어때요.

## 참고자료

1. [How can I use GitHub Actions with Vercel? | Vercel Knowledge Base](https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel)
2. [How to Run Cron Jobs in a Vercel Serverless Environment (Without Paying Extra) - DEV Community](https://dev.to/hexshift/how-to-run-cron-jobs-in-a-vercel-serverless-environment-without-paying-extra-502h)
3. [Kept seeing racked up Vercel bills every now and then, built a tool to fix this once and for all - O](https://community.vercel.com/t/kept-seeing-racked-up-vercel-bills-every-now-and-then-built-a-tool-to-fix-this-once-and-for-all/34159)


---

*Photo by [Gavin Phillips](https://unsplash.com/@gavinspavin) on [Unsplash](https://unsplash.com/photos/mechanical-keyboard-parts-and-tools-laid-out-mxmB5ar6F4M)*
