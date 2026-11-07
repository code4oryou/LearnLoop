"""
tests/test_pipeline.py
Unit tests for LearnLoop verification
"""

import sys
from pathlib import Path

# Add project root to sys.path so modules like evaluation, engine, memory are found
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from unittest.mock import patch, MagicMock
from evaluation.rubric import RUBRIC, EvaluatorOutputSchema
from engine import check_misconception_assertion, LessonState, evaluate_node, route_after_evaluation
from memory.store import init_db, save_evaluation, recent_failures, save_lesson, recent_lessons
from langgraph.graph import END


@pytest.fixture(autouse=True)
def temporary_test_db(tmp_path):
    test_db = tmp_path / "test_learnloop.db"
    with patch("memory.store.DB_PATH", test_db):
        init_db()
        yield


# Test 1 & 2: Misconception assertion logic
def test_misconception_unnegated_fails():
    text = "RAG is great. Whenever RAG retrieves a document, it permanently trains the language model."
    has_error, evidence = check_misconception_assertion(text)
    assert has_error is True


def test_misconception_correct_negation_passes():
    text = "Key concept: RAG does not permanently train the language model or alter its weights."
    has_error, evidence = check_misconception_assertion(text)
    assert has_error is False


# Test 3: Pydantic Validation on complete valid checks
def test_rubric_schema_valid():
    valid_data = {
        "checks": [
            {"id": item["id"], "status": "PASS", "evidence": "Verified", "reason": "Accurate"}
            for item in RUBRIC
        ],
        "summary": "All standards met."
    }
    schema = EvaluatorOutputSchema.model_validate(valid_data)
    assert len(schema.checks) == 8


# Test 4: Missing rubric check raises validation error
def test_rubric_schema_missing_check_fails():
    incomplete_data = {
        "checks": [
            {"id": "Q1", "status": "PASS", "evidence": "Good", "reason": "Valid"}
        ],
        "summary": "Incomplete rubric"
    }
    with pytest.raises(Exception):
        EvaluatorOutputSchema.model_validate(incomplete_data)


# Test 5: Duplicate rubric check raises validation error
def test_rubric_schema_duplicate_check_fails():
    dup_data = {
        "checks": [
            {"id": "Q1", "status": "PASS", "evidence": "Good", "reason": "Valid"},
            {"id": "Q1", "status": "PASS", "evidence": "Good", "reason": "Duplicate"}
        ],
        "summary": "Duplicate check"
    }
    with pytest.raises(Exception):
        EvaluatorOutputSchema.model_validate(dup_data)


# Test 6: Bounded Retry Limit Routing
def test_route_after_evaluation():
    # Pass scenario
    assert route_after_evaluation({"approved": True, "attempts": 1}) == END
    # Fail scenario within retry budget
    assert route_after_evaluation({"approved": False, "attempts": 1}) == "revise"
    assert route_after_evaluation({"approved": False, "attempts": 2}) == "revise"
    # Max attempts reached -> Must terminate at END
    assert route_after_evaluation({"approved": False, "attempts": 3}) == END


# Test 7: SQLite Persistence works across failures
def test_database_persistence():
    topic = "Introduction to RAG"
    checks = [{"id": "Q1", "status": "FAIL", "reason": "Fact error", "name": "Factual accuracy"}]
    
    save_evaluation(topic, 1, False, checks)
    failures = recent_failures(topic)
    
    assert len(failures) == 1
    assert failures[0]["attempt"] == 1
    assert failures[0]["checks"][0]["id"] == "Q1"


# Test 8: Lessons Table Persistence
def test_lesson_persistence():
    topic = "Introduction to RAG"
    save_lesson(topic, "# Lesson Content", True, 2)
    history = recent_lessons()
    
    assert len(history) == 1
    assert history[0][0] == topic
    assert history[0][1] == 1  # Approved
    assert history[0][2] == 2  # 2 attempts