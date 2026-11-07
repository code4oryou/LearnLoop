"""
evaluation/rubric.py
Defines the quality rubric and Pydantic validation schema for LearnLoop.
"""

from typing import List, Literal, Dict
from pydantic import BaseModel, Field, field_validator

RUBRIC = [
    {
        "id": "Q1",
        "name": "Factual accuracy",
        "requirement": "All technical explanations must be factually correct."
    },
    {
        "id": "Q2",
        "name": "Source grounding",
        "requirement": "Core claims must agree with the supplied knowledge pack."
    },
    {
        "id": "Q3",
        "name": "Beginner readability",
        "requirement": "A 12th-grade graduate with limited English vocabulary must understand it."
    },
    {
        "id": "Q4",
        "name": "Jargon explanation",
        "requirement": "Technical terms must be explained in simple language."
    },
    {
        "id": "Q5",
        "name": "Practical example",
        "requirement": "Include a realistic example that explains how RAG is used."
    },
    {
        "id": "Q6",
        "name": "Core coverage",
        "requirement": "Explain what RAG is, why it is used, its components and workflow."
    },
    {
        "id": "Q7",
        "name": "Limitations",
        "requirement": "Explain meaningful limitations and avoid claiming RAG is always correct."
    },
    {
        "id": "Q8",
        "name": "Standalone lesson",
        "requirement": "The lesson must have a logical teaching sequence and work without external explanations."
    }
]

EXPECTED_IDS = {item["id"] for item in RUBRIC}


class EvaluatorCheckItem(BaseModel):
    id: Literal["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8"]
    status: Literal["PASS", "FAIL"]
    evidence: str = Field(default="")
    reason: str = Field(default="")


class EvaluatorOutputSchema(BaseModel):
    checks: List[EvaluatorCheckItem]
    summary: str = Field(default="Evaluation completed.")

    @field_validator("checks")
    @classmethod
    def validate_complete_rubric(cls, v: List[EvaluatorCheckItem]) -> List[EvaluatorCheckItem]:
        found_ids = [c.id for c in v]
        if len(found_ids) != len(set(found_ids)):
            raise ValueError("Duplicate check IDs in evaluation response.")
        if set(found_ids) != EXPECTED_IDS:
            missing = EXPECTED_IDS - set(found_ids)
            raise ValueError(f"Missing required rubric IDs: {missing}")
        return v