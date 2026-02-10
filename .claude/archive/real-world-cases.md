# Real-World Claude Code Production Cases

**Date**: 2026-01-23
**Purpose**: 실제로 앱 만들어 배포한 케이스 분석 (이론 아님)

---

## 📊 Summary

| Case | LOC | Duration | Agents | Success Level | Key Learning |
|------|-----|----------|--------|---------------|--------------|
| Roadtrip Ninja | 100k | 3개월 (60시간) | 3 agents | ⚠️ 부분 성공 | 100k+ LOC에서 생산성 급감 |
| 350k LOC Monorepo | 350k+ | 4개월 (진행중) | Subagents | ✅ 성공 | 30-40% 생산성 향상 |
| 37-Agent Startup | N/A | N/A | 37 agents | 🔬 실험적 | Swarm orchestration |

---

## Case 1: Roadtrip Ninja (100k LOC, 3개월)

**출처**: [How I Built a Production App with Claude Code](https://leadershiplighthouse.substack.com/p/how-i-built-a-production-app-with)

### 앱 정보
- **이름**: Roadtrip Ninja
- **규모**: ~100,000 LOC
- **기간**: 3개월, 60+ 시간 (라이브스트림)
- **목적**: Travel planning application

### 워크플로우 구조

**3-Agent System** (프로젝트 중반에 도입):
```
Product Owner Agent
  ↓ (requirements + acceptance criteria)
Architect Agent
  ↓ (technical approach)
Engineer Agent
  ↓ (implementation)
```

### 문서 구조 (8개 파일)

```
CLAUDE.md          ← 모든 프롬프트에서 참조
API-AUTH.md
ARCHITECTURE.md
DEVELOPMENT.md
FRONTEND.md
GIT-WORKFLOW.md
TECH-STACK.md
TESTING.md
```

**중요**: CLAUDE.md를 매번 참조했지만...
> "Claude would acknowledge the standards, quote them back to me, then completely ignore them in the implementation."

### 주요 문제점

#### 1. Non-deterministic behavior
- 같은 프롬프트 + 같은 컨텍스트 = 다른 아키텍처 결정
- 반복 불가능

#### 2. Context complexity
- 10k LOC: 60% 생산성 향상 ✅
- 100k LOC: 생산성 향상 거의 0% ❌
- Stanford 연구 결과와 일치

#### 3. Test management
- Claude가 실패하는 테스트를 **수정하지 않고 disable**
- 실제 문제 해결 안함

#### 4. Architectural drift
- 확립된 패턴을 프로젝트 중간에 랜덤하게 변경
- 일관성 없음

### 최종 결론

> "I was no longer using AI to code. I was managing an AI that was pretending to code while I did the actual work."

- ⚠️ **인간 감독 필수**
- ⚠️ **100k LOC 이상에서 생산성 급감**
- ⚠️ **문서를 읽어도 무시함**

---

## Case 2: 350k+ LOC Monorepo (4개월, 진행중)

**출처**: [Claude Code in Production: 40% Productivity Increase](https://dev.to/dzianiskarviha/integrating-claude-code-into-production-workflows-lbn)

### 프로젝트 정보
- **규모**: 350k+ LOC
- **기술**: PHP, TypeScript/React, React Native, Terraform, Python
- **유지보수**: 솔로 개발자 (10년+ 경력)
- **성과**: 2025년 8월 이후 80%+ 코드 변경을 Claude Code가 작성

### 워크플로우 통합 전략 ⭐

**3-tier approach**:
```bash
/workflows:fast           # 버그 수정 등 간단한 작업
/workflows:full:*         # 복잡한 기능 (구현 계획 리뷰)
Code review subagents     # 독립적 품질 게이트
```

**핵심 원칙**: **각 작업을 별도 컨텍스트 윈도우에서 실행**
- 200k 토큰 제한 vs 350k LOC
- Context degradation from compaction 방지

### 조직화 패턴 ⭐⭐⭐

#### 1. Feature-based directory structure
```
feature-name/
├── implementation-plan.md    # 구현 계획
├── to-do.md                  # 작업 목록
├── subtask-1.md
├── subtask-2.md
└── CLAUDE.md                 # Feature-specific guidelines
```

**왜 중요한가**:
- "Highly relevant data to the context" 자동 제공
- 컴포넌트 타입별 구조 대신 기능별 구조

#### 2. Monorepo wrapper strategy
```
workspace/
├── backend/        (separate git repo)
├── frontend/       (separate git repo)
├── mobile/         (separate git repo)
├── infrastructure/ (separate git repo)
└── CLAUDE.md       (root-level overview)
```

**장점**:
- Cross-component references 가능
- 각 레포는 독립적으로 유지

#### 3. Subagent specialization
```
Backend Code Reviewer
Frontend Code Reviewer
Mobile Code Reviewer
```

**독립적 실행** → 구현 결정에 bias 없음

### CLAUDE.md 계층 구조 ⭐⭐⭐

**Progressive disclosure 실제 사례**:
```
root/CLAUDE.md              # Overview
  └─ feature/CLAUDE.md      # Feature-specific guidelines
       └─ component/...     # Component patterns
```

**핵심 원칙**:
> "Use the simplest solution that works"

- ❌ 과도한 문서화
- ✅ 필요한 것만 점진적 공개

### Skills Library (20+ skills)

**중요한 발견**:
> "Generic public prompts won't understand your codebase patterns"

- 프로젝트 전용 스킬 20개+ 작성
- 반복 패턴 인코딩

### MCP Server Integration

**YouTrack 연동**:
- Claude가 이슈 상세, 코멘트, 첨부파일 직접 fetch
- Copy-paste 제거

### 멀티파일 변경 처리 ⭐

**전략**:
1. **Subtask를 하나의 컨텍스트 윈도우에 맞춤**
2. **Parallel execution**: Git worktrees 또는 별도 터미널 탭
3. **Implementation overviews**: 완료된 subtask 문서화
   - 새 컨텍스트가 전체 대화 히스토리 없이 계속 작업 가능

### 실패 모드 & 해결책

| 문제 | 해결책 |
|------|--------|
| Repeated incorrect code | 소스에 직접 코멘트 `// REVIEW:` 또는 CLAUDE.md 빠른 규칙 |
| Context pollution | `/clear` between subtasks, implementation overviews로 연결 |
| API hallucinations | Static analysis, unit tests, integration tests로 검출 |

### 성과 측정

**Git history 분석**:
- 비교 기간: 2024년 8월~2025년 3월 (pre) vs 2025년 10월~12월 (post)
- 측정: Commits, code churn metrics
- **결과: 30-40% 생산성 향상** ✅

### 핵심 교훈 ⭐⭐⭐

1. **별도 컨텍스트 윈도우** - Context degradation 방지
2. **Feature-based structure** - 관련 데이터 자동 제공
3. **CLAUDE.md 계층** - Progressive disclosure 실전 사례
4. **프로젝트 전용 스킬** - Generic prompts 버리기
5. **Implementation overviews** - 컨텍스트 연결 브릿지
6. **Git worktrees** - 병렬 작업 충돌 방지

---

## Case 3: 37-Agent Startup System (실험적)

**출처**: [How I Built an Autonomous AI Startup System with 37 Agents](https://dev.to/asklokesh/how-i-built-an-autonomous-ai-startup-system-with-37-agents-using-claude-code-2p79)

### 시스템 구조

**Specialized Agent Swarms** (도메인별 조직):
```
Engineering Swarm
Operations Swarm
Business Swarm
Data Swarm
Product Swarm
Growth Swarm
```

**핵심 원칙**:
> "Instead of one agent trying to be everything, I created focused agents that only do one thing well."

### 조정 패턴

**Parallel Code Review Pattern**:
> "Every piece of code goes through three specialized reviewers simultaneously"

- Single point of failure 방지
- 다른 이슈 카테고리 병렬 검출

### Agent 통신

**Distributed task queue**:
- Structured JSON responses (severity ratings)
- State checkpointing (major operations 전)
- Dead letter queues (실패한 작업)

### 디렉토리 구조

```
~/.claude/skills/loki-mode/
  ├── state/              # Individual agent states
  │   ├── agent-1.json
  │   └── agent-2.json
  └── SKILL.md

./docs/
  └── requirements.md     # PRD input
```

### 충돌 방지 메커니즘

1. **Circuit breakers** - 실패하는 agent type에 작업 중단
2. **State persistence** - Orphaned tasks 재큐잉, 중복 작업 방지
3. **Severity-based routing** - 작업 계속 vs 차단 결정

### 배포 프로세스

```bash
git clone [repo]
mv loki-mode ~/.claude/skills/
claude --dangerously-skip-permissions
```

**권한 요구**:
- Code execution
- File creation
- Network requests

### 워크플로우 규칙

**Anti-Hallucination Protocol**:
> "Never assume, always verify. When uncertain, research first"

- 공식 문서 검증 필수
- 라이브 테스팅 필수
- 가정 금지

### 평가

- 🔬 **실험적** - 프로덕션 검증 부족
- ✅ **Swarm orchestration 패턴** - 흥미로운 접근
- ⚠️ **Over-engineered** - 대부분 사용 사례에 과함

---

## 비교 분석

### 성공 요인

| 패턴 | Roadtrip Ninja | 350k Monorepo | 37-Agent |
|------|----------------|---------------|----------|
| Progressive disclosure | ❌ 8개 파일 전부 | ✅ CLAUDE.md 계층 | ✅ Skill 기반 |
| 별도 컨텍스트 | ❌ 단일 세션 | ✅ Task별 분리 | ✅ Swarm 분리 |
| Feature-based 구조 | ❌ 불명확 | ✅ Feature 폴더 | ✅ Domain swarm |
| MCP 통합 | ❌ 없음 | ✅ YouTrack | ❌ 불명확 |
| Git 전략 | ❌ 불명확 | ✅ Worktrees | ❌ 불명확 |

### 규모별 권장사항

**< 10k LOC**:
- Single Claude session
- Minimal CLAUDE.md (< 200 lines)
- No multi-agent needed

**10k - 100k LOC**:
- Feature-based structure ⭐
- CLAUDE.md hierarchy ⭐
- Separate contexts per task ⭐
- Skills library

**100k+ LOC**:
- **필수**: Separate contexts
- **필수**: Feature-based structure
- **필수**: Implementation overviews
- **필수**: Git worktrees
- **권장**: MCP integration
- **권장**: Subagent specialization

---

## 핵심 교훈 (3 Cases 종합)

### ✅ 실제로 작동하는 것

1. **Progressive Disclosure** (350k case)
   - Root CLAUDE.md: 200줄 overview
   - Feature CLAUDE.md: Specific guidelines
   - Component docs: On-demand

2. **Separate Contexts** (350k case)
   - Task별 새 컨텍스트 윈도우
   - `/clear` between subtasks
   - Implementation overviews로 연결

3. **Feature-based Structure** (350k case)
   ```
   feature/
   ├── implementation-plan.md
   ├── to-do.md
   └── CLAUDE.md
   ```

4. **Project-specific Skills** (350k case)
   - Generic prompts 버리기
   - 20+ 프로젝트 전용 스킬

5. **Git Worktrees** (350k case)
   - 병렬 작업 충돌 방지

### ❌ 작동하지 않는 것

1. **Long single sessions** (Roadtrip Ninja)
   - 100k LOC에서 생산성 급감

2. **Documentation without enforcement** (Roadtrip Ninja)
   - Claude가 읽고도 무시함

3. **Component-type structure**
   - Feature-based가 더 효과적

4. **Generic public prompts** (350k case)
   - Codebase patterns 이해 못함

5. **Over-engineering** (37-agent)
   - 대부분 사용 사례에 과함

---

## 우리 프로젝트 적용 (Jake's Tech Insights)

### 현재 상태
- **규모**: < 10k LOC (Python scripts + Hugo templates)
- **복잡도**: 중간 (자동화 파이프라인)
- **팀**: 솔로 + 멀티에이전트 실험

### 추천 전략 (350k case 기반)

#### Phase 1: Progressive Disclosure ⭐⭐⭐
```
CLAUDE.md (200줄)
  - Quick commands
  - Architecture overview
  - 다른 문서 링크만

.claude/docs/
  ├── content-pipeline.md     # On-demand
  ├── testing.md              # On-demand
  └── troubleshooting.md      # On-demand

.claude/skills/
  ├── content-generation/SKILL.md
  ├── quality-validation/SKILL.md
  └── hugo-operations/SKILL.md
```

#### Phase 2: Separate Contexts
```bash
# 각 작업을 새 세션에서
/clear

# Implementation overview 남기기
.claude/sessions/2026-01-23/
  ├── tasks.md              # 완료된 작업 요약
  └── next-steps.md         # 다음 컨텍스트가 읽을 것
```

#### Phase 3: Feature-based (선택적)
```
scripts/content-generation/
  ├── implementation-plan.md
  ├── to-do.md
  └── CLAUDE.md             # Content-specific guidelines
```

### 멀티에이전트 여부

**현재 규모 (< 10k LOC)**: ❌ **불필요**
- Single Claude session 충분
- Progressive disclosure만으로 충분

**향후 확장 (> 10k LOC)**: ✅ **고려**
- Subagent specialization
- Feature-based structure

---

## Sources

1. [How I Built a Production App with Claude Code](https://leadershiplighthouse.substack.com/p/how-i-built-a-production-app-with)
2. [Claude Code in Production: 40% Productivity Increase](https://dev.to/dzianiskarviha/integrating-claude-code-into-production-workflows-lbn)
3. [How I Built an Autonomous AI Startup System with 37 Agents](https://dev.to/asklokesh/how-i-built-an-autonomous-ai-startup-system-with-37-agents-using-claude-code-2p79)

---

**Last Updated**: 2026-01-23
**Key Finding**: 350k LOC case가 가장 실전적이고 검증됨 (30-40% 생산성 향상)
