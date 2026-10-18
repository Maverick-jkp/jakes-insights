---
title: "ChatGPT로 NASA 데이터에서 행성 발견한 아마추어 천문학자, 일반인이 알아야 할 진짜 의미"
date: 2026-10-18T22:53:46+0900
draft: false
author: "Jake Park"
categories: ["ai"]
tags: ["subtopic-ai", "chatgpt/ub85c", "nasa", "/ub370/uc774/ud130/uc5d0/uc11c"]
description: "ChatGPT로 12만 6천 개 별을 분석해 NASA 행성 후보를 발견한 아마추어 천문학자. 학위 없이 2주·1,000개 스크립트로 공식 후속 관측까지 이끈 AI 협업의 실제 가능성을 분석합니다."
image: "/images/20261018-chatgpt로-nasa-데이터에서-행성-발견-일반인이.webp"
faq:
  - question: "아마추어가 NASA 데이터로 행성 찾는 게 실제로 가능한 건가요?"
    answer: "가능해요. NASA TESS 관측 데이터는 공개되어 있고, Rabtsevich는 상용 AI 도구만으로 2주 만에 전문 팀 수준의 분석을 해냈어요. NASA가 그의 발견을 받아들여 공식 후속 관측까지 예약했다는 게 그 증거예요."
  - question: "왜 자동화 시스템이 2020년에 이미 놓친 신호를 지금 찾아낸 거죠?"
    answer: "TESS 자동 탐지 필터가 2020년에 동일한 신호를 감지했지만 '증거 부족'으로 기각했어요. 이번엔 AI가 74가지 분석과 1,000개 이상의 스크립트로 대안 설명을 하나씩 제거하는 방식을 썼고, 세 개의 독립 시스템이 교차 검증해서 통과됐어요."
  - question: "Claude Code가 행성을 발견한 거라고 봐도 되나요?"
    answer: "정확히는 아니에요. AI는 코드 실행, 데이터 처리, 오류 필터링을 맡았고, 어떤 신호를 볼지·결과를 믿을지는 끝까지 사람이 판단했어요. 예일대 천문학자도 이걸 'AI 자동화'가 아닌 '인간-AI 협업'으로 정리했어요."
  - question: "이 행성 후보, 진짜 행성이라고 확정된 건 아니죠?"
    answer: "맞아요, 아직 미확인 상태예요. 기기 오류나 배경 쌍성계일 가능성이 남아 있고, 2018년 데이터 일부가 TESS 추진기 점화 시점과 겹쳐서 아티팩트 의혹도 있어요. NASA의 후속 관측이 끝나야 더 확실한 판단이 가능해요."
  - question: "나도 이런 분석 해보려면 어디서 데이터 받고 뭐부터 시작해야 하나요?"
    answer: "TESS 데이터는 MAST 포털(mast.stsci.edu)에서 무료로 받을 수 있어요. Rabtsevich가 쓴 도구는 Claude Code와 OpenAI Codex 같은 상용 AI였고, 천문학 전용 라이브러리인 lightkurve를 파이썬으로 돌리는 게 일반적인 시작점이에요."
---

12만 6,000개 별을 혼자 분석했어요. 학위도, 연구실도, 팀도 없이.

스페인 타라고나에 사는 아마추어 천문학자 Pavel Rabtsevich가 2026년 10월, NASA TESS 망원경 데이터에서 지구 반지름의 1.4배짜리 행성 후보를 찾아냈어요. 더 놀라운 건 NASA가 그의 제출을 받아들여 10월 31일부터 11월 26일까지 공식 후속 관측을 예약했다는 거예요. "일반인의 발견"이 제도권 과학의 공식 프로세스에 들어간 거죠.

이게 기술 업계에서 주목해야 할 사건인 이유, 지금부터 정확히 뜯어볼게요.

> **핵심 요약**
> - Pavel Rabtsevich는 2주 동안 74가지 분석과 1,000개 이상의 스크립트를 작성해 별 TIC 4206066에서 행성 신호를 찾아냈으며, Claude Code와 OpenAI Codex가 핵심 도구였어요.
> - TESS 자동 탐지 필터는 2020년에 동일한 신호를 감지했지만 "증거 부족"으로 기각했고, 2026년 AI 보조 분석에서야 재발굴됐어요.
> - MIT TESS팀의 딥러닝 모델과 천문학자 Michelle Kunimoto의 LEO-Vetter 소프트웨어가 동일한 신호를 독립적으로 탐지해 교차 검증이 이뤄졌어요.
> - 행성 후보는 아직 미확인 상태로, 기기 오류나 배경 쌍성계 가능성이 남아 있어요.
> - 이 사례는 "AI가 과학을 자동화"한 게 아니라 "인간 감독 아래 AI가 분석 장벽을 낮췄다"는 새로운 협업 모델을 보여줘요.

---

## 어떻게 된 건지, 정확하게 짚어볼게요

별 TIC 4206066은 지구에서 116광년 떨어진 K형 왜성이에요. 태양보다 조금 작고 차가운 별이죠. [Cybernews 보도](https://cybernews.com/tech/claude-code-possible-exoplanet-found-in-nasa-data/)에 따르면 이 별의 밝기가 매 3.18일마다 약 0.05%씩, 2시간 동안 떨어져요. 행성이 별 앞을 지나갈 때 생기는 "통과(transit)" 현상과 정확히 일치하는 패턴이에요.

Rabtsevich는 이 신호를 2025년 TESS 관측 데이터에서 처음 발견하고, 2020년과 2018년 데이터와 교차 검증했어요. 그가 쓴 방법이 특히 인상적인데요. "블라인드 예측"이에요. 세 개의 TESS 관측 기간 중 두 개의 데이터만 가지고 궤도 파라미터를 계산한 다음, 세 번째 데이터에서 정확히 언제 별이 어두워질지 예측했어요. 세 번 모두 맞았어요.

[Journal du Geek](https://www.journaldugeek.com/2026/10/11/claude-code-internaute-affirme-avoir-trouve-planete-dont-personne-soupconnait-lexistence-lenquete-archives-nasa-secoue-reddit/)이 전한 내용을 보면, 그는 예측 타임스탬프를 10월 6일 Zenodo에 사전 공개했어요. "나중에 슬쩍 수정했다"는 의심을 원천 차단하려고요. 과학적 방법론 측면에서 꽤 성숙한 접근이에요.

단, 이 신호는 아직 확정이 아니에요. 2018년 관측에서 일부 밝기 변화가 TESS 추진기 점화 시점과 겹쳤거든요. 기기 아티팩트일 가능성이 남아 있어요.

---

## AI가 실제로 무슨 일을 했나

"ChatGPT로 NASA 데이터에서 행성 발견"이라는 말을 들으면 AI가 혼자 다 한 것처럼 들릴 수 있어요. 실제는 달라요.

[Tech Times](https://www.techtimes.com/articles/329085/20261015/could-ai-discover-new-planet-amateur-astronomer-finds-promising-signal-nasa-data.htm)가 인용한 예일대 천문학자 Greg Laughlin의 말이 이걸 정확하게 정리해줘요. 이번 사례는 "인간-AI 협업 모델"이라고요. AI가 코드를 작성하고, 분석을 돌리고, 결과를 교차 검증했지만, 과학적 판단은 인간이 계속 유지했어요.

구체적으로 역할을 나눠보면 이래요.

### AI의 역할: 분석 엔진

Claude Code가 맡은 건 TESS 데이터 처리, 통과 모델링, 대안 설명(Alternative Explanation) 테스트였어요. 별 근처에 다른 별이 있는지, 기기 오류는 아닌지, 쌍성계가 신호를 흉내 내는 건 아닌지를 수십 가지 테스트로 걸러냈죠. OpenAI Codex는 독립 검토자 역할을 했어요. 같은 신호를 다른 AI 세션이 다시 봤을 때도 동일한 결론이 나오는지 확인한 거예요.

2주 동안 74개 분석, 1,000개 이상 스크립트. 사람이 혼자 했다면 몇 년이 걸렸을 거예요.

### 인간의 역할: 방향과 판단

Rabtsevich는 어떤 신호를 볼지, 어떤 기준으로 신뢰할지를 결정했어요. AI 합의가 아닌 측정 가능한 신호와 재현 가능한 계산을 기준으로 삼는다는 원칙도 그가 세웠어요. AI가 엄청난 속도로 계산을 돌렸지만, "이게 진짜인지"를 판단하는 건 끝까지 사람이었어요.

### 독립 검증: 시스템이 뒷받침했다

이 사례를 단순한 개인 프로젝트와 다르게 만드는 건 외부 검증이에요. MIT TESS팀 딥러닝 모델과 천문학자 Michelle Kunimoto의 LEO-Vetter 소프트웨어가 각각 독립적으로 동일한 신호를 탐지했거든요. 세 개의 다른 시스템이 같은 별에서 같은 패턴을 찾은 셈이에요.

---

## 일반인 vs. 전문 연구팀: 접근 방식 비교

| 기준 | Rabtsevich (아마추어) | 전문 연구팀 |
|------|----------------------|-------------|
| 분석 도구 | Claude Code + Codex (상용) | 전용 파이프라인 + 독점 소프트웨어 |
| 데이터 접근 | TESS 공개 데이터 | 동일 공개 데이터 + 우선 접근권 |
| 소요 시간 | 약 2주 | 수개월~수년 (팀 규모에 따라) |
| 검증 방식 | 블라인드 예측 + AI 교차 검증 | 동료 심사 + 다중 망원경 후속 관측 |
| 제도 승인 | NASA 후속 관측 수락 | 표준 절차 |
| 한계 | 전문 장비 없음, 기기 오류 판단 어려움 | 예산·시간 제약, 방대한 데이터 수동 검토 비효율 |
| 강점 | 빠른 반복, 낮은 진입 장벽 | 깊은 도메인 지식, 추가 관측 수단 |

여기서 중요한 점이 있어요. 전문 팀과 아마추어가 "경쟁"한 게 아니에요. TESS 자동 필터가 2020년에 이 신호를 걸러냈다는 사실을 기억하세요. 전문 시스템이 놓친 걸 외부인이 다른 각도로 잡아낸 거예요. 그게 열린 데이터와 범용 AI 도구의 조합이 만들어낸 진짜 가치예요.

---

## 이 사례가 실제로 의미하는 것들

### 데이터는 이미 공개되어 있어요

TESS가 관측한 12만 6,000개 이상의 별 데이터는 지금 이 순간도 NASA 공개 아카이브에 있어요. [ScienceDaily 보도](https://www.sciencedaily.com/releases/2026/05/260502233926.htm)에 따르면 2026년 5월 기준 AI 기반 분석으로 100개 이상의 숨겨진 행성 후보가 추가로 발굴됐는데, 이 중 상당수가 기존 자동화 필터가 기각했던 데이터에서 나왔어요. 놓친 신호가 아직도 아카이브 안에 잠들어 있다는 뜻이에요.

### 진입 장벽이 낮아졌지만, 책임은 그대로예요

Claude Code, Codex 같은 도구를 쓰면 복잡한 데이터 파이프라인을 처음부터 짤 필요가 없어요. 그런데 Rabtsevich가 보여준 것처럼, 블라인드 예측이나 사전 공개 타임스탬프 같은 방법론적 엄격함은 AI가 대신해주지 않아요. 도구는 쉬워졌지만, 신뢰를 만드는 과정은 여전히 사람 몫이에요.

### 기업 R&D에도 적용할 수 있는 패턴이에요

천문학 얘기라서 멀게 느껴질 수 있지만, 구조는 같아요. 방대한 공개 데이터, 반복적 분석, AI 보조 코드 생성, 인간 판단 유지. 이 패턴은 의약품 분자 탐색, 금융 이상 탐지, 제조 결함 분석 어디에나 적용돼요. 일반인이 행성을 찾은 게 아니라, 복잡한 데이터 분석의 접근 비용이 극적으로 낮아진 거예요.

---

## 앞으로 뭘 봐야 할까요

**11월 26일 이후가 첫 번째 분기점이에요.** NASA의 TESS 관측이 끝나면 TIC 4206066이 진짜 행성을 거느리는지 훨씬 명확해져요. Rabtsevich가 Zenodo에 올린 예측 타임스탬프와 실제 데이터가 일치한다면, "아마추어 AI 발견"이 학술 검증으로 넘어가는 첫 사례가 돼요.

**다음 6개월 안에 유사 사례가 늘어날 거예요.** 공개 데이터 + 범용 AI 도구 조합의 검증이 끝났으니까요. 이미 340,505개의 자동화 TESS 경보 중 AI 필터가 기각한 데이터들이 재검토 대상이 됐어요. 다음 발견자가 전문가일지 아마추어일지는 점점 덜 중요한 질문이 되고 있어요.

결국 이 사건의 진짜 의미는 AI가 과학을 대체한다는 게 아니에요. 지식 접근의 비대칭이 무너지고 있다는 거예요. 제도와 도구가 이 변화에 어떻게 적응할지, 11월 말 첫 번째 데이터가 나왔을 때 다시 얘기해봐요.

## 참고자료

1. [Amateur astronomer harnesses AI to find a possible hidden exoplanet | Scientific American](https://www.scientificamerican.com/article/amateur-astronomer-harnesses-ai-to-find-a-possible-hidden-exoplanet/)
2. [Powerful AI finds 100+ hidden planets in NASA data including rare and extreme worlds | ScienceDaily](https://www.sciencedaily.com/releases/2026/05/260502233926.htm)
3. [Claude Code may have uncovered a planet in NASA data | Cybernews](https://cybernews.com/tech/claude-code-possible-exoplanet-found-in-nasa-data/)


---

*Photo by [Smithsonian](https://unsplash.com/@smithsonian) on [Unsplash](https://unsplash.com/photos/a-complex-scientific-instrument-with-a-camera-lens-l7H8Ukd8nK8)*
