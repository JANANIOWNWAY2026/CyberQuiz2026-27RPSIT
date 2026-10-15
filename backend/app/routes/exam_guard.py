
import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import require_admin, require_participant

# Reuse the existing quiz submission logic.
from .quiz import QuizSubmission, submit_quiz


router = APIRouter(tags=["Exam Guard"])

logger = logging.getLogger("cyberquiz.exam_guard")

# Local development log file.
# For multi-worker/production deployments, use a database table instead.
LOG_FILE = Path(__file__).resolve().parents[2] / "exam_violations.jsonl"
LOG_LOCK = threading.Lock()


class ViolationSubmission(BaseModel):
    session_id: int
    answers: dict[int, str] = Field(default_factory=dict)
    reason: str = Field(default="page_hidden", max_length=100)


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def write_violation(record: dict):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    with LOG_LOCK:
        with LOG_FILE.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, default=str) + "\n")


@router.post("/api/quiz/violation-submit")
def violation_submit(
    data: ViolationSubmission,
    payload: dict = Depends(require_participant),
    db: Session = Depends(get_db),
):
    participant_id = int(payload.get("sub"))

    # Reuse the normal endpoint's ownership, session, answer,
    # scoring and result-saving checks.
    submission = QuizSubmission(
        session_id=data.session_id,
        answers=data.answers,
    )

    result = submit_quiz(
        submission=submission,
        payload=payload,
        db=db,
    )

    record = {
        "event": "exam_violation",
        "participant_id": participant_id,
        "session_id": data.session_id,
        "reason": data.reason,
        "detected_at": utc_now_iso(),
        "submission_message": result.get("message"),
        "level": result.get("level"),
    }

    try:
        write_violation(record)
    except OSError:
        # The quiz has already been submitted. Do not undo the result.
        logger.exception("Could not write exam violation log")

    return {
        **result,
        "violation_detected": True,
        "violation_reason": data.reason,
    }


@router.get("/api/admin/exam-violations")
def get_exam_violations(
    admin: dict = Depends(require_admin),
):
    if not LOG_FILE.exists():
        return []

    records = []

    with LOG_LOCK:
        with LOG_FILE.open("r", encoding="utf-8") as file:
            for line in file:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning("Skipping invalid violation log line")

    return records[-500:]
