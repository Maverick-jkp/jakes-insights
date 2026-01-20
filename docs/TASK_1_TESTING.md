# Task 1: 테스트 추가 (Testing Implementation)

**작업 기간**: 3-5일
**우선순위**: High
**담당**: Claude Code

---

## 목표

1. pytest 기반 테스트 프레임워크 구축
2. 핵심 로직 50% 커버리지 달성
3. CI/CD에 자동 테스트 통합
4. 회귀 버그 자동 탐지 체계 마련

**예상 효과:**
- 코드 수정 시 기존 기능 보호
- 리팩토링 안전성 확보
- 버그 조기 발견
- 코드 문서화 효과

---

## 배경: 왜 테스트가 중요한가?

### 테스트가 잡아주는 실수들

1. **회귀 버그** (Regression bugs)
   - 코드 수정 시 기존 기능이 망가지는 경우
   - 예: topic_queue.py 수정 → reserve 로직이 망가짐

2. **엣지 케이스**
   - 빈 큐에서 reserve 시도
   - 중복된 topic_id 추가
   - 잘못된 JSON 파싱

3. **리팩토링 검증**
   - 코드 구조 개선 후 동작 확인
   - "이 함수 건드려도 안전한가?"

### 테스트가 못 잡는 실수들

1. **새로운 기능의 논리적 오류**
   - 테스트를 작성하지 않은 신규 코드
   - 잘못된 요구사항 이해

2. **Production 환경 차이**
   - API rate limits
   - 네트워크 타임아웃
   - 파일 권한 문제

---

## Task 1.1: pytest 설정 및 기본 구조 (Day 1)

### 작업 내용

#### 1. pytest 설치

**파일**: `requirements.txt` (수정)

```
anthropic>=0.18.0
requests>=2.31.0
jsonschema>=4.20.0
feedparser>=6.0.10

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0
```

**설치:**
```bash
pip install -r requirements.txt
```

#### 2. 테스트 디렉토리 구조 생성

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_topic_queue.py      # Topic queue tests
├── test_quality_gate.py     # Quality gate tests
├── test_keyword_curator.py  # Keyword curator tests
├── fixtures/                # Test data
│   ├── sample_queue.json
│   ├── sample_post.md
│   └── sample_keywords.json
└── utils/
    └── test_validation.py   # Validation utils tests (if Task 3 done)
```

#### 3. pytest 설정 파일

**파일**: `pytest.ini` (신규 생성)

```ini
[pytest]
# Test discovery
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Test output
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=scripts
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=50

# Test paths
testpaths = tests

# Markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

#### 4. Conftest (공통 fixtures)

**파일**: `tests/conftest.py` (신규 생성)

```python
"""
Shared pytest fixtures for all tests.
"""
import json
import pytest
from pathlib import Path
from typing import Dict, List

@pytest.fixture
def sample_queue() -> Dict:
    """Load sample topic queue for testing."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_queue.json"

    if fixture_path.exists():
        with open(fixture_path, 'r') as f:
            return json.load(f)

    # Default sample queue
    return {
        "topics": [
            {
                "id": "001-en-tech-test-keyword",
                "keyword": "Test Keyword",
                "category": "tech",
                "language": "en",
                "priority": 8,
                "status": "pending",
                "expiry_days": 3,
                "trend_type": "evergreen",
                "retry_count": 0,
                "created_at": "2026-01-20T12:00:00+09:00",
                "reserved_at": None,
                "completed_at": None
            }
        ]
    }

@pytest.fixture
def temp_queue_file(tmp_path, sample_queue):
    """Create a temporary queue file for testing."""
    queue_file = tmp_path / "test_queue.json"

    with open(queue_file, 'w') as f:
        json.dump(sample_queue, f)

    return str(queue_file)

@pytest.fixture
def sample_post_content() -> str:
    """Sample blog post content for testing."""
    return """---
title: "Test Post"
date: 2026-01-20T12:00:00+09:00
description: "This is a test post for unit testing."
categories: ["tech"]
tags: ["testing", "python"]
image: cover.jpg
---

This is a test post with some content.

## Section 1

Some content here.

## Section 2

More content here.

## Conclusion

Final thoughts.
"""

@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response."""
    return {
        "content": [
            {
                "text": "Generated content here..."
            }
        ],
        "usage": {
            "input_tokens": 1000,
            "output_tokens": 2000
        }
    }
```

#### 5. Fixture 데이터 파일

**파일**: `tests/fixtures/sample_queue.json`

```json
{
  "topics": [
    {
      "id": "001-en-tech-test-pending",
      "keyword": "Test Pending",
      "category": "tech",
      "language": "en",
      "priority": 8,
      "status": "pending",
      "expiry_days": 3,
      "trend_type": "evergreen",
      "retry_count": 0,
      "created_at": "2026-01-20T12:00:00+09:00",
      "reserved_at": null,
      "completed_at": null
    },
    {
      "id": "002-ko-business-test-inprogress",
      "keyword": "테스트 진행중",
      "category": "business",
      "language": "ko",
      "priority": 7,
      "status": "in_progress",
      "expiry_days": 3,
      "trend_type": "trend",
      "retry_count": 0,
      "created_at": "2026-01-19T12:00:00+09:00",
      "reserved_at": "2026-01-20T08:00:00+09:00",
      "completed_at": null
    },
    {
      "id": "003-ja-lifestyle-test-completed",
      "keyword": "テスト完了",
      "category": "lifestyle",
      "language": "ja",
      "priority": 6,
      "status": "completed",
      "expiry_days": 3,
      "trend_type": "evergreen",
      "retry_count": 0,
      "created_at": "2026-01-18T12:00:00+09:00",
      "reserved_at": "2026-01-19T08:00:00+09:00",
      "completed_at": "2026-01-19T10:00:00+09:00"
    }
  ]
}
```

---

## Task 1.2: Topic Queue 테스트 (Day 2)

### 작업 내용

**파일**: `tests/test_topic_queue.py`

```python
"""
Tests for scripts/topic_queue.py
"""
import pytest
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Import functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from topic_queue import (
    load_queue,
    save_queue,
    add_topic,
    reserve_topics,
    mark_completed,
    mark_failed,
    cleanup_expired,
    get_stats
)

class TestLoadSaveQueue:
    """Test queue loading and saving."""

    def test_load_queue_valid_file(self, temp_queue_file):
        """Test loading a valid queue file."""
        queue = load_queue(temp_queue_file)

        assert isinstance(queue, dict)
        assert "topics" in queue
        assert len(queue["topics"]) > 0

    def test_load_queue_missing_file(self, tmp_path):
        """Test loading non-existent file creates empty queue."""
        missing_file = tmp_path / "missing.json"

        queue = load_queue(str(missing_file))

        assert queue == {"topics": []}

    def test_save_queue(self, tmp_path, sample_queue):
        """Test saving queue to file."""
        queue_file = tmp_path / "test_save.json"

        save_queue(sample_queue, str(queue_file))

        assert queue_file.exists()

        # Verify content
        with open(queue_file, 'r') as f:
            loaded = json.load(f)

        assert loaded == sample_queue

class TestAddTopic:
    """Test adding topics to queue."""

    def test_add_topic_basic(self, temp_queue_file):
        """Test adding a basic topic."""
        topic_id = add_topic(
            "New Keyword",
            "tech",
            "en",
            priority=8,
            queue_file=temp_queue_file
        )

        assert topic_id is not None
        assert "new-keyword" in topic_id
        assert topic_id.startswith("004-")  # Next ID

        # Verify added to queue
        queue = load_queue(temp_queue_file)
        added = next(t for t in queue["topics"] if t["id"] == topic_id)

        assert added["keyword"] == "New Keyword"
        assert added["status"] == "pending"
        assert added["priority"] == 8

    def test_add_topic_invalid_category(self, temp_queue_file):
        """Test adding topic with invalid category."""
        with pytest.raises(ValueError, match="Invalid category"):
            add_topic("Test", "invalid_category", "en", queue_file=temp_queue_file)

    def test_add_topic_invalid_language(self, temp_queue_file):
        """Test adding topic with invalid language."""
        with pytest.raises(ValueError, match="Invalid language"):
            add_topic("Test", "tech", "invalid_lang", queue_file=temp_queue_file)

    def test_add_topic_invalid_priority(self, temp_queue_file):
        """Test adding topic with invalid priority."""
        with pytest.raises(ValueError, match="Priority"):
            add_topic("Test", "tech", "en", priority=15, queue_file=temp_queue_file)

class TestReserveTopics:
    """Test topic reservation logic."""

    def test_reserve_topics_basic(self, temp_queue_file):
        """Test reserving topics by priority."""
        reserved = reserve_topics(count=2, queue_file=temp_queue_file)

        assert len(reserved) == 2
        assert all(t["status"] == "in_progress" for t in reserved)
        assert reserved[0]["priority"] >= reserved[1]["priority"]  # Sorted

    def test_reserve_topics_empty_queue(self, tmp_path):
        """Test reserving from empty queue."""
        empty_file = tmp_path / "empty.json"
        save_queue({"topics": []}, str(empty_file))

        reserved = reserve_topics(count=5, queue_file=str(empty_file))

        assert len(reserved) == 0

    def test_reserve_topics_fewer_than_requested(self, temp_queue_file):
        """Test reserving more topics than available."""
        reserved = reserve_topics(count=100, queue_file=temp_queue_file)

        # Should only get pending topics (1 in fixture)
        assert len(reserved) <= 1

    def test_reserve_topics_skips_in_progress(self, temp_queue_file):
        """Test that in_progress topics are not reserved again."""
        reserved = reserve_topics(count=10, queue_file=temp_queue_file)

        # Should not include already in_progress topics
        for topic in reserved:
            assert "inprogress" not in topic["id"]

class TestMarkCompleted:
    """Test marking topics as completed."""

    def test_mark_completed_basic(self, temp_queue_file):
        """Test marking a topic as completed."""
        topic_id = "002-ko-business-test-inprogress"

        success = mark_completed(topic_id, queue_file=temp_queue_file)

        assert success is True

        # Verify status changed
        queue = load_queue(temp_queue_file)
        topic = next(t for t in queue["topics"] if t["id"] == topic_id)

        assert topic["status"] == "completed"
        assert topic["completed_at"] is not None

    def test_mark_completed_nonexistent(self, temp_queue_file):
        """Test marking non-existent topic."""
        success = mark_completed("999-nonexistent", queue_file=temp_queue_file)

        assert success is False

class TestMarkFailed:
    """Test marking topics as failed."""

    def test_mark_failed_basic(self, temp_queue_file):
        """Test marking a topic as failed."""
        topic_id = "002-ko-business-test-inprogress"

        success = mark_failed(topic_id, queue_file=temp_queue_file)

        assert success is True

        # Verify status changed
        queue = load_queue(temp_queue_file)
        topic = next(t for t in queue["topics"] if t["id"] == topic_id)

        assert topic["status"] == "failed"
        assert topic["retry_count"] == 1

    def test_mark_failed_increments_retry(self, temp_queue_file):
        """Test that retry_count increments on failure."""
        topic_id = "002-ko-business-test-inprogress"

        # Fail twice
        mark_failed(topic_id, queue_file=temp_queue_file)
        mark_failed(topic_id, queue_file=temp_queue_file)

        queue = load_queue(temp_queue_file)
        topic = next(t for t in queue["topics"] if t["id"] == topic_id)

        assert topic["retry_count"] == 2

class TestCleanupExpired:
    """Test cleanup of expired/stuck topics."""

    def test_cleanup_expired_basic(self, temp_queue_file):
        """Test cleanup of topics stuck for >24 hours."""
        # Create old stuck topic
        queue = load_queue(temp_queue_file)

        old_time = datetime.now(timezone.utc) - timedelta(hours=25)

        queue["topics"].append({
            "id": "999-en-tech-stuck-topic",
            "keyword": "Stuck Topic",
            "category": "tech",
            "language": "en",
            "priority": 5,
            "status": "in_progress",
            "reserved_at": old_time.isoformat(),
            "retry_count": 0
        })

        save_queue(queue, temp_queue_file)

        # Cleanup
        cleaned = cleanup_expired(hours=24, queue_file=temp_queue_file)

        assert cleaned == 1

        # Verify status changed
        queue = load_queue(temp_queue_file)
        stuck = next(t for t in queue["topics"] if t["id"] == "999-en-tech-stuck-topic")

        assert stuck["status"] == "failed"

class TestGetStats:
    """Test statistics calculation."""

    def test_get_stats(self, temp_queue_file):
        """Test getting queue statistics."""
        stats = get_stats(queue_file=temp_queue_file)

        assert "total" in stats
        assert "pending" in stats
        assert "in_progress" in stats
        assert "completed" in stats

        assert stats["total"] == 3
        assert stats["pending"] == 1
        assert stats["in_progress"] == 1
        assert stats["completed"] == 1
```

---

## Task 1.3: Quality Gate 테스트 (Day 3)

**파일**: `tests/test_quality_gate.py`

```python
"""
Tests for scripts/quality_gate.py
"""
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from quality_gate import (
    check_word_count,
    check_ai_phrases,
    check_frontmatter,
    check_seo_quality,
    validate_post
)

class TestWordCount:
    """Test word count validation."""

    def test_word_count_english_valid(self):
        """Test valid English word count."""
        content = " ".join(["word"] * 1000)  # 1000 words

        result = check_word_count(content, "en")

        assert result["status"] == "PASS"
        assert result["count"] == 1000

    def test_word_count_english_too_short(self):
        """Test English post that's too short."""
        content = " ".join(["word"] * 500)  # 500 words

        result = check_word_count(content, "en")

        assert result["status"] == "FAIL"

    def test_word_count_korean_valid(self):
        """Test valid Korean word count."""
        content = "테스트 " * 1000  # 1000 words

        result = check_word_count(content, "ko")

        assert result["status"] == "PASS"

    def test_word_count_japanese_valid(self):
        """Test valid Japanese character count."""
        content = "テスト" * 2000  # 4000 chars

        result = check_word_count(content, "ja")

        assert result["status"] == "PASS"

class TestAIPhrases:
    """Test AI phrase detection."""

    def test_ai_phrases_none_detected(self):
        """Test content with no AI phrases."""
        content = "This is normal content without any AI clichés."

        result = check_ai_phrases(content, "en")

        assert result["status"] == "PASS"
        assert len(result["found"]) == 0

    def test_ai_phrases_detected(self):
        """Test content with AI phrases."""
        content = "This is a game-changer and revolutionary solution."

        result = check_ai_phrases(content, "en")

        assert result["status"] == "WARN"
        assert len(result["found"]) == 2

class TestFrontmatter:
    """Test frontmatter validation."""

    def test_frontmatter_complete(self, sample_post_content):
        """Test post with complete frontmatter."""
        result = check_frontmatter(sample_post_content)

        assert result["status"] == "PASS"
        assert all(result["has_" + field] for field in ["title", "date", "description"])

    def test_frontmatter_missing_fields(self):
        """Test post with missing frontmatter fields."""
        content = """---
title: "Test"
---

Content here.
"""

        result = check_frontmatter(content)

        assert result["status"] == "FAIL"
        assert not result["has_date"]
        assert not result["has_description"]

class TestSEOQuality:
    """Test SEO quality checks."""

    def test_seo_good_description(self):
        """Test post with good description length."""
        frontmatter = {
            "description": "This is a description that's between 120 and 160 characters long for good SEO."
        }

        result = check_seo_quality(frontmatter, "Content with some links http://example.com")

        assert result["description_length"] >= 120
        assert result["has_links"] is True

    def test_seo_short_description(self):
        """Test post with too-short description."""
        frontmatter = {
            "description": "Too short"
        }

        result = check_seo_quality(frontmatter, "Content")

        assert result["status"] == "WARN"

class TestValidatePost:
    """Test full post validation."""

    def test_validate_post_all_pass(self, sample_post_content, tmp_path):
        """Test post that passes all checks."""
        post_file = tmp_path / "test.md"
        post_file.write_text(sample_post_content)

        result = validate_post(str(post_file), "en")

        assert result["overall_status"] == "PASS"

    def test_validate_post_with_failures(self, tmp_path):
        """Test post that fails some checks."""
        bad_content = """---
title: "Test"
---

Too short.
"""

        post_file = tmp_path / "bad.md"
        post_file.write_text(bad_content)

        result = validate_post(str(post_file), "en")

        assert result["overall_status"] in ["FAIL", "WARN"]
```

---

## Task 1.4: CI/CD 통합 (Day 4)

### 작업 내용

#### 1. GitHub Actions Workflow 수정

**파일**: `.github/workflows/daily-content.yml` (수정)

```yaml
# 기존 내용에 test step 추가

name: Daily Content Generation

on:
  schedule:
    - cron: '0 9,21,3 * * *'
  workflow_dispatch:
    inputs:
      count:
        description: 'Number of posts to generate'
        required: false
        default: '3'

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run pytest
        run: |
          pytest --cov=scripts --cov-report=term --cov-report=xml

      - name: Upload coverage to Codecov (optional)
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: false

  generate:
    name: Generate Content
    runs-on: ubuntu-latest
    needs: test  # Only run if tests pass

    steps:
      # ... 기존 generate steps
```

#### 2. 별도 Test Workflow (optional)

**파일**: `.github/workflows/test.yml` (신규 생성)

```yaml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11']

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run tests
        run: |
          pytest -v --cov=scripts --cov-report=term-missing

      - name: Test report
        if: always()
        run: |
          echo "## Test Results" >> $GITHUB_STEP_SUMMARY
          pytest --tb=line >> $GITHUB_STEP_SUMMARY
```

---

## Task 1.5: 추가 테스트 작성 (Day 5)

### 작업 내용

**파일**: `tests/test_keyword_curator.py` (일부만)

```python
"""
Tests for scripts/keyword_curator.py
"""
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from keyword_curator import (
    assess_risk_level,
    extract_intent_signals,
    is_decision_stage_keyword
)

class TestRiskAssessment:
    """Test keyword risk assessment."""

    def test_risk_high(self):
        """Test high-risk keyword detection."""
        assert assess_risk_level("Trump election") == "high_risk"
        assert assess_risk_level("Bitcoin crash") == "high_risk"

    def test_risk_caution(self):
        """Test caution-level keywords."""
        assert assess_risk_level("AI regulation") == "caution"
        assert assess_risk_level("Crypto news") == "caution"

    def test_risk_safe(self):
        """Test safe keywords."""
        assert assess_risk_level("Python tutorial") == "safe"
        assert assess_risk_level("React hooks") == "safe"

class TestIntentSignals:
    """Test intent signal detection."""

    def test_decision_stage_signals(self):
        """Test decision-stage keyword detection."""
        signals = extract_intent_signals("Best React framework 2026")

        assert "DECISION_STAGE" in signals
        assert is_decision_stage_keyword("Best React framework 2026") is True

    def test_problem_signals(self):
        """Test problem-based signals."""
        signals = extract_intent_signals("Why is my code slow")

        assert "PROBLEM_BASED" in signals
```

---

## 검증 방법

### 로컬에서 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 특정 파일만 실행
pytest tests/test_topic_queue.py

# 특정 테스트만 실행
pytest tests/test_topic_queue.py::TestAddTopic::test_add_topic_basic

# 커버리지 리포트
pytest --cov=scripts --cov-report=html
open htmlcov/index.html  # macOS
```

### CI/CD 테스트 확인

```bash
# GitHub Actions workflow 수동 실행
# → Actions 탭 → Test Suite → Run workflow

# 로그 확인
# → Test job 클릭 → Run pytest 단계 확인
```

---

## 예상 결과

### Before (현재)
```bash
$ pytest
ERROR: file or package not found

$ # 코드 수정
$ python scripts/generate_posts.py
# 뭔가 망가졌는지 모름
```

### After (개선)
```bash
$ pytest
===== 47 passed in 2.34s =====

Coverage: 52% (target: 50%)

$ # 코드 수정
$ pytest
===== 2 failed, 45 passed in 2.18s =====
# 어떤 함수가 망가졌는지 즉시 확인
```

---

## 회귀 방지

이 작업 후 다음 규칙 준수:

1. **새로운 함수 작성 시**: 최소 1개 이상의 테스트 작성
2. **버그 수정 시**: 버그를 재현하는 테스트 먼저 작성
3. **PR 전**: `pytest` 실행하여 모든 테스트 통과 확인

---

## 비용

- **개발 시간**: 3-5일 (초기 설정)
- **유지보수**: 새 기능마다 테스트 추가 (+20% 개발 시간)
- **CI/CD 시간**: +30초/workflow
- **금전 비용**: $0 (GitHub Actions 무료 tier 충분)

---

## 참고 문서

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
