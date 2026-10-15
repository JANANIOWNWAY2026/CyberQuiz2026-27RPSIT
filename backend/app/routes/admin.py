import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import require_admin, require_participant
from ..models import (
    Participant,
    QuizRound,
    QuizResult,
    QuizSession,
    LeaderboardSetting,
    RoundApproval,
    RoundControl,
)

router = APIRouter(prefix="/api/admin", tags=["Admin"])


class AdminLoginRequest(BaseModel):
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


class RoundApprovalRequest(BaseModel):
    is_approved: bool


def utc_now():
    return datetime.now(timezone.utc)


def validate_level(level: int):
    if level not in (1, 2, 3):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid quiz level. Allowed levels are 1, 2 and 3.",
        )


def get_round_control(db: Session, level: int):
    control = (
        db.query(RoundControl)
        .filter(RoundControl.level == level)
        .first()
    )

    if control is None:
        control = RoundControl(
            level=level,
            status="locked",
        )
        db.add(control)
        db.flush()

    return control


@router.post("/login")
def admin_login(data: AdminLoginRequest):
    expected_username = os.getenv("ADMIN_USERNAME")
    expected_password = os.getenv("ADMIN_PASSWORD")
    secret_key = os.getenv("SECRET_KEY")
    algorithm = os.getenv("ALGORITHM", "HS256")

    if not expected_username or not expected_password:
        raise HTTPException(
            status_code=500,
            detail="Admin credentials are not configured",
        )

    if (
        not secret_key
        or secret_key == "replace_with_a_long_random_secret_key"
    ):
        raise HTTPException(
            status_code=500,
            detail="Configure a secure SECRET_KEY in .env",
        )

    if algorithm != "HS256":
        raise HTTPException(
            status_code=500,
            detail="Unsupported JWT algorithm configuration",
        )

    if (
        data.email != expected_username
        or data.password != expected_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid admin username or password",
        )

    try:
        expires_minutes = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
        )
        if expires_minutes <= 0:
            raise ValueError
    except ValueError:
        raise HTTPException(
            status_code=500,
            detail="Invalid token expiry configuration",
        )

    now = utc_now()

    token = jwt.encode(
        {
            "sub": expected_username,
            "role": "admin",
            "iat": now,
            "exp": now + timedelta(minutes=expires_minutes),
        },
        secret_key,
        algorithm=algorithm,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": expires_minutes,
    }


@router.get("/participants")
def get_participants(
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    participants = (
        db.query(Participant)
        .order_by(Participant.created_at.desc())
        .all()
    )

    participant_ids = [p.id for p in participants]
    approvals_by_participant = {}

    if participant_ids:
        approvals = (
            db.query(RoundApproval)
            .filter(
                RoundApproval.participant_id.in_(participant_ids)
            )
            .all()
        )

        for approval in approvals:
            approvals_by_participant.setdefault(
                approval.participant_id, {}
            )[str(approval.level)] = approval.is_approved

    return [
        {
            "id": p.id,
            "name": p.name,
            "register_number": p.register_number,
            "college_name": p.college_name,
            "college_location": p.college_location,
            "gender": p.gender,
            "phone": p.phone,
            "email": p.email,
            "department": p.department,
            "course": p.course,
            "is_approved": p.is_approved,
            "is_active": p.is_active,
            "created_at": p.created_at,
            "round_approvals": {
                "1": approvals_by_participant.get(p.id, {}).get(
                    "1", False
                ),
                "2": approvals_by_participant.get(p.id, {}).get(
                    "2", False
                ),
                "3": approvals_by_participant.get(p.id, {}).get(
                    "3", False
                ),
            },
        }
        for p in participants
    ]


@router.patch("/participants/{participant_id}/approve")
def approve_participant(
    participant_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    participant = (
        db.query(Participant)
        .filter(Participant.id == participant_id)
        .first()
    )

    if not participant:
        raise HTTPException(
            status_code=404,
            detail="Participant not found",
        )

    participant.is_approved = True

    db.commit()
    db.refresh(participant)

    return {
        "message": "Participant account approved successfully",
        "participant_id": participant.id,
        "name": participant.name,
        "is_approved": participant.is_approved,
    }


@router.patch("/participants/{participant_id}/round-approval/{level}")
def set_round_approval(
    participant_id: int,
    level: int,
    data: RoundApprovalRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    validate_level(level)

    participant = (
        db.query(Participant)
        .filter(Participant.id == participant_id)
        .first()
    )

    if not participant:
        raise HTTPException(
            status_code=404,
            detail="Participant not found",
        )

    approval = (
        db.query(RoundApproval)
        .filter(
            RoundApproval.participant_id == participant_id,
            RoundApproval.level == level,
        )
        .first()
    )

    if approval is None:
        approval = RoundApproval(
            participant_id=participant_id,
            level=level,
            is_approved=data.is_approved,
            approved_at=utc_now() if data.is_approved else None,
        )
        db.add(approval)
    else:
        approval.is_approved = data.is_approved
        approval.approved_at = (
            utc_now() if data.is_approved else None
        )

    db.commit()
    db.refresh(approval)

    return {
        "message": (
            f"Participant approved for Level {level}"
            if approval.is_approved
            else f"Level {level} approval removed"
        ),
        "participant_id": participant_id,
        "level": level,
        "is_approved": approval.is_approved,
    }


@router.get("/rounds/status")
def get_round_statuses(
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    rounds = (
        db.query(QuizRound)
        .order_by(QuizRound.level)
        .all()
    )

    controls = {
        control.level: control
        for control in db.query(RoundControl).all()
    }

    return [
        {
            "level": round_.level,
            "question_count": round_.question_count,
            "seconds_per_question": round_.seconds_per_question,
            "status": (
                controls[round_.level].status
                if round_.level in controls
                else "locked"
            ),
            "is_unlocked": round_.is_unlocked,
            "started_at": (
                controls[round_.level].started_at
                if round_.level in controls
                else None
            ),
            "ended_at": (
                controls[round_.level].ended_at
                if round_.level in controls
                else None
            ),
        }
        for round_ in rounds
    ]


@router.patch("/rounds/{level}/start")
def start_quiz_round(
    level: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    validate_level(level)

    round_ = (
        db.query(QuizRound)
        .filter(QuizRound.level == level)
        .first()
    )

    if not round_:
        raise HTTPException(
            status_code=404,
            detail=f"Level {level} is not configured",
        )

    control = get_round_control(db, level)

    if control.status == "active":
        return {
            "message": f"Level {level} is already active",
            "level": level,
            "status": control.status,
        }

    control.status = "active"
    control.started_at = utc_now()
    control.ended_at = None
    round_.is_unlocked = True

    db.commit()

    return {
        "message": f"Level {level} started successfully",
        "level": level,
        "status": "active",
    }


@router.patch("/rounds/{level}/end")
def end_quiz_round(
    level: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    validate_level(level)

    round_ = (
        db.query(QuizRound)
        .filter(QuizRound.level == level)
        .first()
    )

    if not round_:
        raise HTTPException(
            status_code=404,
            detail=f"Level {level} is not configured",
        )

    control = get_round_control(db, level)

    control.status = "ended"
    control.ended_at = utc_now()

    db.commit()

    return {
        "message": f"Level {level} ended. New quiz sessions are blocked.",
        "level": level,
        "status": "ended",
    }


# Compatibility endpoint for the existing dashboard.
# Unlocking now starts the round.
@router.patch("/rounds/{level}/unlock")
def unlock_quiz_level(
    level: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    return start_quiz_round(level, db, admin)


@router.patch("/sessions/{session_id}/retry")
def authorize_quiz_retry(
    session_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    session = (
        db.query(QuizSession)
        .filter(QuizSession.id == session_id)
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Quiz session not found",
        )

    if session.status == "in_progress":
        raise HTTPException(
            status_code=409,
            detail="Cannot authorize retry for an active session",
        )

    session.retry_authorized = True

    db.commit()
    db.refresh(session)

    return {
        "message": "Retry authorized successfully",
        "session_id": session.id,
        "level": session.level,
        "retry_authorized": session.retry_authorized,
    }



@router.get("/results")
def get_quiz_results(
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    participants = (
        db.query(Participant)
        .order_by(Participant.created_at.desc())
        .all()
    )

    rounds = {
        round_.level: round_.question_count
        for round_ in db.query(QuizRound)
        .filter(QuizRound.level.in_([1, 2, 3]))
        .all()
    }

    results = (
        db.query(QuizResult)
        .filter(QuizResult.level.in_([1, 2, 3]))
        .order_by(
            QuizResult.submitted_at.desc(),
            QuizResult.id.desc(),
        )
        .all()
    )

    # Keep the latest submitted result for each participant and level.
    latest_results = {}

    for result in results:
        key = (result.participant_id, result.level)

        if key not in latest_results:
            latest_results[key] = result

    response = []

    for participant in participants:
        participant_results = [
            latest_results.get((participant.id, level))
            for level in (1, 2, 3)
        ]

        submitted_results = [
            result
            for result in participant_results
            if result is not None
        ]

        correct = sum(
            result.correct_answers or 0
            for result in submitted_results
        )
        incorrect = sum(
            result.wrong_answers or 0
            for result in submitted_results
        )
        unanswered = sum(
            result.unanswered or 0
            for result in submitted_results
        )
        total_score = sum(
            result.score or 0
            for result in submitted_results
        )

        total_questions = sum(
            rounds.get(level, 0)
            for level in (1, 2, 3)
        )

        all_levels_completed = (
            all(participant_results[level - 1] is not None for level in (1, 2, 3))
            and all(rounds.get(level, 0) > 0 for level in (1, 2, 3))
        )

        response.append({
            "participant_id": participant.id,
            "participant_name": participant.name,
            "register_number": participant.register_number,
            "total_questions": total_questions,
            "correct_answers": correct,
            "wrong_answers": incorrect,
            "unanswered": unanswered,
            "score": total_score,
            "completed_levels": len(submitted_results),
            "status": (
                "Completed"
                if all_levels_completed
                else "In Progress"
            ),
        })

    return response



def get_or_create_leaderboard_setting(db: Session):
    setting = (
        db.query(LeaderboardSetting)
        .filter(LeaderboardSetting.id == 1)
        .first()
    )

    if setting is None:
        setting = LeaderboardSetting(
            id=1,
            is_published=False,
        )
        db.add(setting)

        try:
            db.commit()
            db.refresh(setting)
        except Exception:
            db.rollback()
            setting = (
                db.query(LeaderboardSetting)
                .filter(LeaderboardSetting.id == 1)
                .first()
            )
            if setting is None:
                raise

    return setting


@router.get("/leaderboard-status")
def get_leaderboard_status(
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    setting = get_or_create_leaderboard_setting(db)
    return {"is_published": setting.is_published}


@router.patch("/leaderboard/publish")
def publish_leaderboard(
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    setting = get_or_create_leaderboard_setting(db)
    setting.is_published = True

    db.commit()
    db.refresh(setting)

    return {
        "message": "Final leaderboard published successfully.",
        "is_published": setting.is_published,
    }


@router.patch("/leaderboard/unpublish")
def unpublish_leaderboard(
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    setting = get_or_create_leaderboard_setting(db)
    setting.is_published = False

    db.commit()
    db.refresh(setting)

    return {
        "message": "Final leaderboard hidden successfully.",
        "is_published": setting.is_published,
    }
