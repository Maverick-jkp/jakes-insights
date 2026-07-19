---
title: "맥북 M5 로컬 AI 속도 llama.cpp보다 6배 빠르다는데 일반인이 느낄 차이 있나: 모델 크기별 비교"
date: 2026-07-19T20:21:49+0900
draft: false
author: "Jake Park"
categories: ["ai"]
tags: ["subtopic-ai", "/ub9e5/ubd81 M5 /ub85c/uceec AI /uc18d/ub3c4 llama.cpp/ubcf4/ub2e4 6/ubc30 /ube60/ub974/ub2e4/ub294/ub370, /uc77c/ubc18/uc778/uc774 /ub290/ub084 /ucc28/uc774 /uc788/ub098"]
description: "M5 Max + MLX가 llama.cpp 대비 최대 6배 빠르지만, 7B~13B 소형 모델은 RTX 4090이 더 빠르고 가격도 절반 이하. 예산과 모델 크기별 실측 비교로 내 상황에 맞는 로컬"
image: "/images/20260719-맥북-m5-로컬-ai-속도-llama-cpp보다-6배.webp"
faq:
  - question: "70B 모델 로컬에서 돌릴 때 맥북이랑 RTX 4090 체감 차이 있나요?"
    answer: "70B 모델 기준으로는 실제로 체감 차이가 납니다. M5 Max는 12~18 토큰/초, RTX 4090은 6~10 토큰/초로 RTX 4090이 VRAM 한계 때문에 CPU로 오프로딩하면서 느려지거든요. 짧은 답변은 그냥 넘어갈 수 있지만, 긴 응답을 자주 뽑는다면 두 배 속도 차이는 확실히 느껴집니다."
  - question: "Ollama가 M5에서 6배 빠르다는 게 진짜 숫자 맞나요?"
    answer: "그 숫자는 CPU만 쓰는 llama.cpp와 MLX를 비교한 특정 조건에서 나온 거라 일반적인 상황과는 달라요. 실제로 llama.cpp Metal 백엔드 대비 MLX는 5~10% 정도 빠른 수준이고, 70B 모델에서 오프로딩 페널티까지 포함하면 2~3배 차이가 현실적인 숫자입니다."
  - question: "전기료까지 따지면 맥북 프로 M5 본전 뽑을 수 있을까요?"
    answer: "RTX 4090 빌드는 하루 8시간 추론 기준 월 40~60달러, M5 Max는 8~12달러 수준이에요. 1년이면 전기료 차이만 약 40만 원인데, 초기 구입비 차이가 2,500달러 이상이라 전기료만으로 본전 뽑기는 어렵습니다. 70B 모델을 주로 쓰거나 조용한 환경이 필요한 경우에 추가 가치를 찾는 편이 현실적이에요."
  - question: "맥북에서 AI 오래 돌리면 진짜 느려지나요?"
    answer: "3시간 이상 연속 추론을 돌리면 발열 쓰로틀링이 시작되고, 토큰 속도가 30% 이상 떨어진다는 보고가 MLX 공식 레포 이슈에도 올라와 있어요. 짧은 세션으로 쓰는 개인 용도라면 괜찮지만, 24시간 API 서버처럼 연속 운용이 필요하다면 맥북 프로는 적합하지 않습니다."
  - question: "7B 소형 모델만 쓸 거면 굳이 M5 살 이유가 있나요?"
    answer: "7B 모델만 쓴다면 RTX 4090이 90~120 토큰/초로 M5 Max의 50~75 토큰/초보다 오히려 빠르고, 가격도 절반 이하입니다. 소형 모델 위주에 파인튜닝이나 Stable Diffusion까지 같이 쓸 계획이라면 RTX 4090 빌드가 더 합리적인 선택이에요."
---

로컬 AI 쓰려고 세팅하다가 멈춘 적 있죠? "근데 이게 진짜 빠른 건가?" 싶어서요.

M5 Max + MLX가 이겨요. 70B 대형 모델 기준으로는 확실하게. 하지만 7B~13B 소형 모델만 쓴다면 RTX 4090 빌드가 더 빠르고, 예산도 절반 이하예요.

> **TL;DR**
> - **MLX (M5 Max) 쓰세요** if: 70B 이상 대형 모델을 로컬에서 돌리고 싶거나, 전력 요금이 걱정되거나, 파인튜닝 없이 추론만 할 때
> - **llama.cpp + RTX 4090 쓰세요** if: 7B~13B 모델 속도가 최우선이거나, Stable Diffusion·LoRA 파인튜닝까지 같이 쓸 때
> - **둘 다 건너뛰세요** if: 예산이 800달러 이하라면 — RTX 4070 Ti 빌드가 소형 모델에선 M5 Pro를 이기거든요

이 글에서 비교할 항목:
- **추론 속도**: 토큰/초, 모델 크기별 차이
- **실제 체감**: 일반인 기준 "느껴지는" 차이가 있는지
- **비용**: 초기 구입비 + 월 전기료
- **한계**: 각각 어디서 무너지는지

---

## 두 플레이어 소개

**MLX (Apple Silicon M5 Max)**는 Apple이 2024년 공개한 머신러닝 프레임워크예요. M5 Max 탑재 맥북 프로 16인치는 2026년 5월 기준 3,499달러(64GB)부터 시작하고, 128GB 구성은 4,499달러예요. 핵심 강점은 유니파이드 메모리예요. GPU VRAM과 RAM이 분리된 게 아니라 하나의 풀을 공유하는 구조라서, RTX 4090의 24GB 한계와 달리 128GB 전체를 모델에 쏟아부을 수 있어요. [Apple Silicon M5 로컬 LLM 벤치마크](https://www.promptquorum.com/local-llms/apple-silicon-m5-local-llm)에 따르면 M5 Max 128GB에서 Llama 3.3 70B Q4 모델이 12~18 토큰/초를 기록했어요.

**llama.cpp**는 Georgi Gerganov가 만든 C++ 추론 엔진이에요. 원래 CPU에서 LLM 돌리려고 시작했지만, 지금은 CUDA(NVIDIA GPU)와 Metal(Apple GPU) 모두 지원하는 사실상의 표준 로컬 AI 백엔드로 자리 잡았어요. RTX 4090 기준 7B 모델은 90~120 토큰/초, 70B 모델은 6~10 토큰/초예요. 2026년 초 기준 GitHub 커밋 수가 월 500건을 넘을 만큼 활발하고, 하드웨어 비용은 RTX 4090 단독 빌드 기준 1,600~2,000달러 수준이에요.

---

## 항목별 정면 비교

| 항목 | MLX (M5 Max 128GB) | llama.cpp + RTX 4090 | 승자 |
|---|---|---|---|
| 진입 비용 | 4,499달러 | 1,600~2,000달러 | RTX 4090 |
| 70B 모델 추론 속도 | 12~18 토큰/초 | 6~10 토큰/초 | MLX |
| 7B 모델 추론 속도 | 50~75 토큰/초 | 90~120 토큰/초 | RTX 4090 |
| 최대 모델 크기 (단일 GPU) | 128GB (Q8까지 가능) | 24GB (70B Q5+ 불가) | MLX |
| 월 전기료 | 8~12달러 | 40~60달러 | MLX |
| 파인튜닝 지원 | 제한적 (LoRA 일부) | CUDA 완전 지원 | RTX 4090 |
| 장시간 연속 추론 | 3시간 후 쓰로틀링 | 24시간+ 안정 | RTX 4090 |

[Apple Silicon M5 벤치마크 데이터 출처](https://www.promptquorum.com/local-llms/apple-silicon-m5-local-llm)

**가장 눈에 띄는 행은 70B 모델 속도예요.** RTX 4090은 24GB VRAM으로 70B 모델을 절반 이상 RAM으로 오프로딩해야 해요. 그 병목이 추론 속도를 6~10 토큰/초로 끌어내리죠. 반면 M5 Max는 460~614 GB/s 메모리 대역폭으로 모델 전체를 통합 메모리에 올려놓기 때문에 두 배 가까이 빨라요.

**전기료 차이는 진짜 돈 얘기예요.** RTX 4090은 추론 시 350W를 먹어요. M5 Max는 65~100W. 하루 8시간씩 돌리면 RTX 4090은 월 40~60달러, M5 Max는 8~12달러예요. 1년이면 거의 40만 원 차이가 나요.

**그럼 "6배 빠르다"는 주장은 어디서 나온 걸까요?** Ollama가 M5에서 MLX 백엔드를 자동으로 켜면서 나온 비교예요. 정확히는 llama.cpp Metal 백엔드 대비 순수 MLX가 5~10% 더 빠른 정도예요. 70B 모델에서 llama.cpp의 CPU 오프로딩 페널티까지 포함하면 2~3배 차이가 나고, 6배는 CPU만 쓰는 llama.cpp vs. MLX라는 특정 조건에서 나오는 숫자예요. 일반 사용자 기준으로 "6배"를 그대로 믿으면 과장이에요.

---

## 각각 어디서 무너지나

**MLX (M5 Max)가 무너지는 시점**: 맥북 프로에서 3시간 이상 연속 추론을 돌리면 발열 쓰로틀링이 시작돼요. GitHub 이슈([MLX 레포 #847](https://github.com/ml-explore/mlx))에서 장시간 배치 처리 시 토큰 속도가 30% 이상 떨어진다는 보고가 여러 건 올라와 있어요. 서버처럼 24시간 API를 돌려야 한다면 맥북 프로는 답이 아니에요. Mac Studio M5가 2026년 10월 출시 예정이지만, 아직은 검증된 데이터가 없어요.

**llama.cpp + RTX 4090이 무너지는 시점**: 70B Q5 이상 모델을 단일 GPU로 돌리는 게 물리적으로 불가능해요. VRAM 24GB 한계를 넘으면 CPU RAM으로 오프로딩해야 하는데, 이때 속도가 6~10 토큰/초로 떨어지고 시스템 RAM도 64GB 이상 필요해요. 멀티 GPU 세팅은 비용이 두 배 이상 올라가고, 70B 이상 모델을 쓰고 싶다면 사실상 막힌 길이에요.

---

## 결론: 일반인이 실제로 느끼는 차이

**70B 모델 쓰는 사람이라면 차이가 느껴져요.** 12~18 토큰/초 vs. 6~10 토큰/초는 긴 답변 생성 시 대략 30~40초 차이예요. 채팅보다 문서 요약이나 코드 리뷰처럼 긴 출력을 기다릴 때 체감이 확실하게 나와요.

**7B~13B 모델만 쓴다면 RTX 4090이 더 빠르고, M5 Max는 비교 자체가 안 돼요.** 90~120 토큰/초는 텍스트가 거의 실시간으로 나오는 속도거든요.

지금 당장 해볼 수 있는 것: [PromptQuorum 벤치마크 페이지](https://www.promptquorum.com/local-llms/apple-silicon-m5-local-llm)에서 본인이 쓰려는 모델 크기를 확인하고, 해당 모델 기준 토큰/초를 비교해보세요. 10분이면 자신에게 맞는 쪽을 정할 수 있어요.

앞으로 지켜봐야 할 질문은 하나예요. **2026년 10월 Mac Studio M5 출시 후 장시간 쓰로틀링 문제가 해결되면, 서버용 로컬 AI 인프라도 Apple Silicon으로 옮겨갈까요?** 그 시점이 llama.cpp + NVIDIA 조합의 진짜 변곡점이 될 거예요.

## 참고자료

1. [2026년 초보자 로컬 LLM: Llama, Phi, Gemma, Qwen | PromptQuorum](https://www.promptquorum.com/ko/local-llms/best-beginner-local-llm-models)
2. [Best Apple M5 Pro and Max for Local AI (2026) | InsiderLLM](https://insiderllm.com/guides/apple-m5-pro-max-local-ai/)
3. [llama.cpp Tutorial: Run a Local LLM in 12 Steps [2026]](https://tech-insider.org/llama-cpp-tutorial-2026/)


---

*Photo by [Igor Omilaev](https://unsplash.com/@omilaev) on [Unsplash](https://unsplash.com/photos/two-hands-touching-each-other-in-front-of-a-pink-background-gVQLAbGVB6Q)*
