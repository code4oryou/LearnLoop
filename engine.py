"""
engine.py
LangGraph workflow orchestrating generation, evaluation, deterministic checks,
bounded revision (max 3 total attempts), and persistent storage.
"""

import json
import re
from pathlib import Path
from typing import TypedDict, List, Dict, Any, Tuple

from google import genai
from langgraph.graph import StateGraph, START, END
from pydantic import ValidationError

from config import GEMINI_API_KEY, GEMINI_MODEL
from evaluation.rubric import RUBRIC, EvaluatorOutputSchema
from memory.store import (
    init_db,
    save_evaluation,
    save_lesson,
    recent_failures
)

client = genai.Client(api_key=GEMINI_API_KEY)

ROOT = Path(__file__).resolve().parent
KNOWLEDGE_PATH = ROOT / "knowledge" / "rag_sources.md"

DEMO_ERROR = (
    "Whenever RAG retrieves a document, it permanently "
    "trains the language model on that document."
)


class LessonState(TypedDict, total=False):
    topic: str
    lesson: str
    attempts: int
    checks: list
    approved: bool
    rejection_log: list
    summary: str
    inject_failure: bool


# ---------------------------------------------------------
# Helper & Extraction Logic
# ---------------------------------------------------------

def ask_model(prompt: str) -> str:
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )
    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")
    return response.text.strip()


def extract_json(text: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("Evaluator response contains no JSON object.")

    return json.loads(cleaned[start:end + 1])


def check_misconception_assertion(text: str) -> Tuple[bool, str]:
    """
    Returns (has_unnegated_error, detected_evidence).
    Prevents false positives when a lesson correctly clarifies:
    'RAG does NOT permanently train the language model'.
    """
    pattern = r"permanently\s+train(?:s|ed|ing)?\s+(?:the\s+)?(?:language\s+model|llm|model)"
    match = re.search(pattern, text, re.IGNORECASE)
    
    if not match:
        return False, "No false claims detected."

    # Inspect the 60 characters preceding the match for negation words
    start_pos = match.start()
    lookback = text[max(0, start_pos - 60):start_pos].lower()
    negation_regex = r"\b(not|never|doesn't|does\s+not|without|isn't|no)\b"

    if re.search(negation_regex, lookback):
        return False, "Correctly clarified that RAG does NOT permanently train the model."

    return True, match.group(0)


# ---------------------------------------------------------
# Graph Nodes
# ---------------------------------------------------------

def generate_node(state: LessonState) -> dict:
    source = KNOWLEDGE_PATH.read_text(encoding="utf-8")

    prompt = f"""
You are an expert educational content writer.

Create a complete beginner lesson on: {state['topic']}

TARGET LEARNER:
An Indian student who has completed Class 12.
Assume limited English vocabulary and no prior technical knowledge.

RULES:
- Use simple, direct, natural English (short sentences).
- Explain difficult words immediately.
- Use short paragraphs.
- Teach concepts in a logical order.
- Include relatable real-world analogies (e.g. open-book vs closed-book exam).
- Avoid unnecessary technical complexity.
- Target 600-900 words.
- Do not invent facts.

REQUIRED SECTIONS:
1. Learning Objectives
2. What is the Concept?
3. Why is it Useful?
4. Important Components
5. How it Works, Step by Step
6. A Practical Real-World Example
7. Limitations
8. Key Terms and Their Meanings
9. Quick Knowledge Check with Answers

KNOWLEDGE PACK:
{source}

Return only the lesson in Markdown.
"""
    lesson = ask_model(prompt)

    if state.get("inject_failure"):
        lesson += "\n\n## Deliberate demo misconception\n" + DEMO_ERROR

    return {
        "lesson": lesson,
        "attempts": 1
    }


def evaluate_node(state: LessonState) -> dict:
    source = KNOWLEDGE_PATH.read_text(encoding="utf-8")

    prompt = f"""
You are a strict educational quality evaluator.
You did NOT write this lesson. Evaluate it critically.

TARGET LEARNER:
Indian Class 12 graduate with limited English vocabulary.

Evaluate every criterion below.
A criterion can only PASS if it is fully satisfied.
Do not reward effort or give partial credit.

RUBRIC:
{json.dumps(RUBRIC, indent=2)}

KNOWLEDGE PACK:
{source}

LESSON:
{state['lesson']}

Return ONLY valid JSON in this exact structure:
{{
  "checks": [
    {{
      "id": "Q1",
      "status": "PASS",
      "evidence": "A short quotation or specific evidence",
      "reason": "Why it passes or fails"
    }}
  ],
  "summary": "Short evaluation summary"
}}

Include every rubric ID from Q1 to Q8 exactly once.
Use only PASS or FAIL.
Be especially strict about factual accuracy and beginner readability.
"""

    model_checks: Dict[str, Dict[str, str]] = {}
    summary = "Evaluation completed."

    try:
        raw_json = extract_json(ask_model(prompt))
        validated = EvaluatorOutputSchema.model_validate(raw_json)
        model_checks = {c.id: c.model_dump() for c in validated.checks}
        summary = validated.summary
    except (json.JSONDecodeError, ValidationError, Exception) as exc:
        summary = f"Evaluator failed closed: {str(exc)}"

    checks = []

    # 1. Semantic Rubric Checks
    for criterion in RUBRIC:
        cid = criterion["id"]
        item = model_checks.get(cid)

        if not item or item.get("status") not in ("PASS", "FAIL"):
            checks.append({
                "id": cid,
                "name": criterion["name"],
                "status": "FAIL",
                "evidence": "",
                "reason": "Missing or invalid evaluator decision."
            })
        else:
            checks.append({
                "id": cid,
                "name": criterion["name"],
                "status": item["status"],
                "evidence": str(item.get("evidence", "")),
                "reason": str(item.get("reason", ""))
            })

    # 2. Deterministic Checks
    lesson_text = state["lesson"]
    word_count = len(lesson_text.split())

    # D1: Word count
    checks.append({
        "id": "D1",
        "name": "Minimum lesson length",
        "status": "PASS" if 400 <= word_count <= 1300 else "FAIL",
        "evidence": f"{word_count} words",
        "reason": "Lesson must contain 400-1300 words."
    })

    # D2: Misconception Check (Robust Negation-Aware)
    has_unnegated_error, det_evidence = check_misconception_assertion(lesson_text)
    checks.append({
        "id": "D2",
        "name": "RAG training misconception",
        "status": "FAIL" if has_unnegated_error else "PASS",
        "evidence": det_evidence if has_unnegated_error else "No unnegated misconception detected.",
        "reason": (
            "Detected unnegated assertion that RAG permanently trains the model."
            if has_unnegated_error
            else "Correct: No claim that retrieval permanently trains the model."
        )
    })

    # D3: Required Structural Anchors
    required_anchors = ["learning objective", "example", "limitation", "key term", "knowledge check"]
    lesson_lower = lesson_text.lower()
    missing_sections = [s for s in required_anchors if s not in lesson_lower]

    checks.append({
        "id": "D3",
        "name": "Required sections",
        "status": "PASS" if not missing_sections else "FAIL",
        "evidence": "All required sections detected." if not missing_sections else f"Missing: {', '.join(missing_sections)}",
        "reason": "Lesson must cover all foundational pedagogical sections."
    })

    # Deterministic approval verification
    approved = all(item["status"] == "PASS" for item in checks)

    # Collect failure items cleanly (fixing prior syntax issue)
    failed = [
        f"{item['id']} · {item['name']}: {item['reason']}"
        for item in checks
        if item["status"] == "FAIL"
    ]

    rejection_log = list(state.get("rejection_log", []))
    if not approved:
        rejection_log.append({
            "attempt": state["attempts"],
            "failures": failed
        })

    # Persist evaluation result
    save_evaluation(
        state["topic"],
        state["attempts"],
        approved,
        checks
    )

    if approved or state["attempts"] >= 3:
        save_lesson(
            state["topic"],
            state["lesson"],
            approved,
            state["attempts"]
        )

    return {
        "checks": checks,
        "approved": approved,
        "summary": summary,
        "rejection_log": rejection_log
    }


def revise_node(state: LessonState) -> dict:
    history = recent_failures(state["topic"])
    failed_checks = [c for c in state["checks"] if c["status"] == "FAIL"]

    prompt = f"""
You are an expert educational lesson editor.

Rewrite the entire lesson below to fix EVERY single failure identified by the quality evaluator.

CRITICAL INSTRUCTIONS:
- Address each failed checkpoint thoroughly.
- If a misconception about RAG permanently retraining the model was flagged, explicitly remove it.
- Do not append commentary or notes. Output the full revised lesson in Markdown.

TOPIC: {state['topic']}

TARGET:
Indian Class 12 graduate with limited English vocabulary.

FAILED CRITERIA IN LAST ATTEMPT:
{json.dumps(failed_checks, indent=2)}

HISTORICAL FAILURES ON THIS TOPIC:
{json.dumps(history, indent=2)}

CURRENT LESSON TO REVISE:
{state['lesson']}

Return only the complete revised lesson in Markdown.
"""
    revised = ask_model(prompt)

    return {
        "lesson": revised,
        "attempts": state["attempts"] + 1
    }


def route_after_evaluation(state: LessonState) -> str:
    if state["approved"] or state["attempts"] >= 3:
        return END
    return "revise"


def build_graph():
    workflow = StateGraph(LessonState)

    workflow.add_node("generate", generate_node)
    workflow.add_node("evaluate", evaluate_node)
    workflow.add_node("revise", revise_node)

    workflow.add_edge(START, "generate")
    workflow.add_edge("generate", "evaluate")

    workflow.add_conditional_edges(
        "evaluate",
        route_after_evaluation,
        {
            END: END,
            "revise": "revise"
        }
    )

    workflow.add_edge("revise", "evaluate")
    return workflow.compile()


def run_learnloop(topic: str, inject_failure: bool = False) -> dict:
    init_db()
    graph = build_graph()

    return graph.invoke({
        "topic": topic,
        "attempts": 0,
        "rejection_log": [],
        "inject_failure": inject_failure
    })