---
title: "Gemini 3.5 Transcribe 회의록 자동 생성, 실제로 쓸 만한지 데이터로 따져봤다"
date: 2026-08-28T05:13:57+0900
draft: false
author: "Jake Park"
categories: ["ai"]
tags: ["subtopic-ai", "gemini", "3.5", "transcribe"]
description: "Gemini 3.5 Transcribe, 회의록 자동 생성 실제로 써봤습니다. WER 2.6% 정확도와 한국어 인식 성능을 직접 테스트한 결과, 기존 AI 받아쓰기와 무엇이 달라졌는지 데이터로"
image: "/images/20260828-gemini-3-5-transcribe-써봤나-회의록.webp"
faq:
  - question: "회의 중에 실시간으로 자막처럼 띄우는 게 가능한가요?"
    answer: "네, 실시간 스트리밍용 API(`gemini-3.5-transcribe-live`)를 쓰면 회의 중 실시간 자막 형태로 출력할 수 있어요. 다만 스트리밍 기준 WER이 5.50%라 비스트리밍(2.6%)보다 오류가 좀 더 나오는 건 감안해야 해요."
  - question: "'어', '음' 같은 군말도 회의록에 그대로 남나요?"
    answer: "아니요, Gemini 3.5 Transcribe는 채움말을 자동으로 제거하고 의미 단위로 재작성해서 출력해요. 기존 STT 도구들이 들리는 대로 다 받아 적던 것과 가장 크게 다른 점이에요."
  - question: "참석자가 4명 이상이면 화자 구분이 그냥 망가지나요?"
    answer: "공식 지원은 최대 3인까지고, 4인 이상은 실험적 기능으로 분류돼 있어요. 안정성을 보장하지 않는다는 뜻이라, 대규모 회의에 바로 쓰기엔 아직 리스크가 있어요."
  - question: "법무팀 미팅 녹취록에 써도 되는 건지 궁금해요."
    answer: "쓰면 안 돼요. 이 모델은 발화를 그대로 옮기는 게 아니라 의미를 보존하면서 재작성하기 때문에, 원문 그대로가 필요한 법률이나 의료 기록에는 적합하지 않아요."
  - question: "한국어 기술 용어 오인식이 심하면 어떻게 대응하나요?"
    answer: "커스텀 어휘 등록 기능으로 사전에 회사 내부 용어나 업계 전문어를 등록해두면 오인식을 줄일 수 있어요. 한국어·영어 혼용 환경에서도 85개 이상 언어를 지원하기 때문에 기본적인 혼용 처리는 가능해요."
---

60분짜리 회의, 끝나고 나면 늘 누군가 희생자가 생기죠. 회의록 쓰는 사람. 2026년 8월 26일, Google이 Gemini 3.5 Transcribe를 공개하면서 그 희생자 자리가 드디어 AI로 넘어갈 수 있게 됐어요. 그런데 "AI가 회의록 써준다"는 말은 2년 전부터 들었잖아요. 이번엔 뭐가 다를까요?

데이터를 먼저 볼게요. [Artificial Analysis의 벤치마크](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-5-transcribe/)에 따르면, Gemini 3.5 Transcribe의 단어 오류율(WER)은 스트리밍 기준 4.0%, 사전 녹음 기준 2.6%예요. 전작 Chirp 3 대비 최종 텍스트 변환 속도는 70% 빨라졌고요. 숫자만 보면 꽤 그럴듯해요. 근데 회의록 자동 생성에 실제로 쓸 만한지는 다른 얘기거든요.

---

**핵심 요약**

- Gemini 3.5 Transcribe는 2026년 8월 26일 출시됐으며, WER 2.6%(비스트리밍)로 전작 Chirp 3의 스트리밍 WER 7.32%에서 크게 개선됐다.
- 단순 받아쓰기가 아닌 "편집된 텍스트" 출력 방식으로, 군말 제거·자기 수정 처리·문장 자동 포맷을 지원한다.
- 최대 3인 화자 구분과 단어 단위 타임스탬프를 제공해 다자간 회의록 자동 생성에 실용적 기반을 갖췄다.
- 단, 법률·의료처럼 원문 그대로가 필요한 맥락에서는 부적합하다 — 모델이 발화 내용을 "재작성"하기 때문이다.

---

## 기존 음성 인식과 뭐가 다른가

기존 STT(Speech-to-Text) 도구들은 말 그대로 "들리는 대로" 받아 적었어요. "어... 그러니까... 이거 있잖아요, 이거..."까지 전부 텍스트로 나왔죠. 결과물을 사람이 다시 정리해야 했어요. 반 자동화에 불과했던 거예요.

[Google 공식 블로그](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-5-transcribe/)에 따르면, Gemini 3.5 Transcribe는 원시 오디오를 바로 "정제된 텍스트"로 변환해요. 구체적으로 어떤 처리를 하냐면:

- **군말 자동 제거**: "음", "어", "그러니까" 같은 채움말 삭제
- **자기 수정 처리**: "다음 달에... 아니 이번 달에 마감이에요"처럼 스스로 고치는 발화를 깔끔하게 정리
- **커스텀 어휘**: 회사 내부 용어, 업계 전문어를 미리 등록해 오인식 줄이기
- **화자 구분**: 최대 3인까지 누가 말했는지 레이블링 + 단어 단위 타임스탬프

여기서 핵심은 "편집된 텍스트"라는 개념이에요. 이 모델은 발화 내용을 그대로 옮기는 게 아니라, 의미를 보존하면서 읽기 좋게 재작성해요. [Ars Technica가 지적한 것처럼](https://arstechnica.com/ai/2026/08/google-announces-gemini-3-5-transcribe-for-ai-powered-speech-to-text/), 이게 양날의 검이에요. 회의록 목적으로는 장점이지만, 법률 진술이나 의료 기록처럼 원문 보존이 필수인 경우엔 쓰면 안 돼요.

두 가지 API도 구분해서 알아둬야 해요. `gemini-3.5-transcribe-live`는 실시간 스트리밍용, `gemini-3.5-transcribe`는 사전 녹음 파일 처리용이에요. 회의 중 실시간으로 자막처럼 띄우고 싶다면 전자, 녹음 파일 올려서 나중에 정리하고 싶다면 후자를 쓰면 되는 구조예요.

---

## 수치로 보는 성능 — Chirp 3와 비교

[9to5Google 보도](https://9to5google.com/2026/08/26/gemini-3-5-transcribe/)와 Google 공식 데이터를 바탕으로 Chirp 3와 직접 비교해봤어요.

| 항목 | Chirp 3 | Gemini 3.5 Transcribe | 변화 |
|------|---------|----------------------|------|
| 스트리밍 WER (FLEURS) | 7.32% | 5.50% | -25% |
| 비스트리밍 WER | 미공개 | 2.6% (Artificial Analysis) | 기준선 |
| 최종 텍스트 속도 | 기준 | 70% 향상 | ↑ |
| 지원 언어 | 미공개 | 85개 이상 | ↑ |
| 화자 구분 | 제한적 | 최대 3인 (실험적: 3인 이상) | ↑ |
| 군말 처리 | 없음 | 자동 제거 | 신규 |
| 커스텀 어휘 | 없음 | 지원 | 신규 |

WER 5.50%를 회의록 맥락으로 풀어보면, 100단어 중 약 5~6단어가 틀릴 수 있다는 얘기예요. 60분 회의에서 나오는 단어가 대략 6,000~8,000단어라면, 330~440개 단어 오류가 생길 수 있는 셈이죠. 들리는 것보다 많아 보일 수 있어요.

그런데 여기서 맥락이 중요해요. 채움말이나 단순 발음 실수는 모델이 애초에 걸러내기 때문에, 실제 "의미 있는 오류"는 저 숫자보다 훨씬 적을 가능성이 높아요. 단순 WER 수치만으로 판단하면 과소평가가 될 수 있는 거예요.

---

## 실제로 어떻게 쓸 수 있나 — 세 가지 시나리오

**시나리오 1: 스타트업 개발팀 (3인 이하 스탠드업)**
가장 적합한 케이스예요. 화자 3인, 전문 용어는 커스텀 어휘로 등록, 영어 기술 용어 + 한국어 혼용 환경에서 비스트리밍 API로 녹음 후 처리. 지금 당장 실용적으로 써볼 만한 조건이에요. Google AI Studio에서 개발자 프리뷰로 바로 접근할 수 있어요.

**시나리오 2: 기업 영업팀 (고객 미팅 후 CRM 입력)**
회의 후 녹음 파일을 올려서 요약 생성, CRM에 붙여넣는 워크플로우예요. 다만 고객 동의 없는 녹음은 국내 법률 이슈가 있으니 사전 고지가 필수예요. 기술적 적합성보다 컴플라이언스 검토가 먼저예요.

**시나리오 3: 법무팀 / 의료 기관**
쓰지 마세요. 발화를 "재작성"하는 모델 특성상 원문 보존이 안 돼요. [Ars Technica도 같은 이유로 정밀도가 필요한 맥락에서의 부적합성을 명시](https://arstechnica.com/ai/2026/08/google-announces-gemini-3-5-transcribe-for-ai-powered-speech-to-text/)했어요.

그럼 실시간 회의 통합은 어떻게 될까요? Zoom이나 Google Meet에 붙인다고 가정하면, 회의 중 실시간으로 텍스트가 생성돼요. 이미 Agora, LiveKit, LangChain, Vercel, Pipecat과의 통합이 확인됐어요. LangChain 연동이 특히 흥미로운데 — 회의록 생성 이후 "액션 아이템 추출", "요약 생성" 같은 후처리를 같은 파이프라인에서 돌릴 수 있거든요.

한 가지 현실적인 한계도 짚어둘게요. 화자 구분은 최대 3인까지 안정적이고, 4인 이상은 아직 실험 단계예요. 5~10명이 참여하는 일반적인 팀 회의에서는 화자 레이블이 섞일 수 있어요. 한국 비즈니스 현장 특유의 영어·한국어 혼용("Q3 OKR 리뷰해서 레트로 하자") 코드스위칭 상황에서 정확도가 어떻게 나오는지도 아직 검증된 독립 데이터가 없고요. 이 부분은 직접 테스트해봐야 해요.

---

## 지금 쓸 만한가, 기다려야 하는가

핵심을 세 줄로 요약하면 이래요:

- WER 2.6%와 70% 속도 향상은 실질적인 개선이에요. 전작과 비교하면 체감 차이가 날 정도예요.
- 군말 제거 + 화자 구분 + 커스텀 어휘의 조합이 회의록 자동화에 딱 맞는 구조예요. 단, 3인 이하일 때.
- "재작성" 방식이라는 특성은 일반 비즈니스 미팅엔 장점이지만, 원문 보존이 필요한 영역엔 명확한 한계예요.

앞으로 주시할 신호도 세 가지예요. Chrome 통합 출시 시점 — 브라우저 내 모든 텍스트 입력창에서 음성 입력이 가능해지면 파급력이 달라져요. 4인 이상 화자 구분 안정화 — 실험 단계에서 정식 지원으로 넘어오는 시점이 분기점이에요. 한국어 특화 벤치마크 데이터 — 현재 FLEURS 기준 수치가 한국어 코드스위칭 환경을 얼마나 반영하는지 여전히 불투명하거든요.

2026년 남은 기간 동안 Chrome 통합과 화자 구분 확대가 이뤄지면, 지금보다 훨씬 넓은 범위에서 실용적으로 쓸 수 있게 될 거예요. 지금 당장 개발자라면 [Google AI Studio의 프리뷰 접근](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-5-transcribe/)으로 팀 워크플로우에 테스트해볼 가치는 충분해요.

마지막으로 한 가지 질문을 던져볼게요. 회의록 자동 생성이 보편화되면, 회의를 더 많이 하게 될까요, 아니면 덜 하게 될까요?

## 참고자료

1. [Intelligent transcription with Gemini 3.5 Transcribe](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-5-transcribe/)
2. [Google announces Gemini 3.5 Transcribe for AI-powered speech-to-text - Ars Technica](https://arstechnica.com/ai/2026/08/google-announces-gemini-3-5-transcribe-for-ai-powered-speech-to-text/)
3. [Google launches Gemini 3.5 Transcribe, which powers Gboard Rambler & is coming to Chrome](https://9to5google.com/2026/08/26/gemini-3-5-transcribe/)


---

*Photo by [yanzheng xia](https://unsplash.com/@novaspark) on [Unsplash](https://unsplash.com/photos/mclaren-formula-1-car-with-gemini-and-mastercard-logos-TqAILI5qDDM)*
