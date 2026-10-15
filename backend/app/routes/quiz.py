
import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..models import (
    # existing model imports — edhaiyum remove panna vendam
    LeaderboardSetting,
)
from ..database import get_db
from ..dependencies import require_participant
from ..models import (
    Participant,
    QuizRound,
    Question,
    QuizSession,
    QuizResult,
    RoundApproval,
    RoundControl,
)

router = APIRouter(prefix="/api/quiz", tags=["Quiz"])


def utc_now():
    return datetime.now(timezone.utc)


def get_approved_participant(db: Session, participant_id: int):
    participant = (
        db.query(Participant)
        .filter(
            Participant.id == participant_id,
            Participant.is_active.is_(True),
            Participant.is_approved.is_(True),
        )
        .first()
    )

    if not participant:
        raise HTTPException(
            status_code=403,
            detail="Participant account approval required",
        )

    return participant


def get_round_approval(
    db: Session,
    participant_id: int,
    level: int,
):
    approval = (
        db.query(RoundApproval)
        .filter(
            RoundApproval.participant_id == participant_id,
            RoundApproval.level == level,
            RoundApproval.is_approved.is_(True),
        )
        .first()
    )

    if not approval:
        raise HTTPException(
            status_code=403,
            detail=f"Admin approval required for Level {level}",
        )

    return approval


def get_round(db: Session, level: int):
    if level not in (1, 2, 3):
        raise HTTPException(
            status_code=400,
            detail="Invalid quiz level",
        )

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

    return round_


def is_round_active(db: Session, level: int) -> bool:
    control = (
        db.query(RoundControl)
        .filter(RoundControl.level == level)
        .first()
    )

    return bool(control and control.status == "active")

def is_previous_level_completed(
    db: Session,
    participant_id: int,
    level: int,
) -> bool:
    if level == 1:
        return True

    previous_level = level - 1

    result = (
        db.query(QuizResult)
        .filter(
            QuizResult.participant_id == participant_id,
            QuizResult.level == previous_level,
        )
        .first()
    )

    return result is not None

def get_level_questions(db: Session, level: int, count: int):
    questions = (
        db.query(Question)
        .filter(Question.level == level)
        .order_by(Question.id)
        .limit(count)
        .all()
    )

    if len(questions) != count:
        raise HTTPException(
            status_code=409,
            detail="Question bank is incomplete",
        )

    return questions


def session_deadline_is_past(session: QuizSession, now: datetime):
    deadline = session.deadline_at

    # PostgreSQL normally returns timezone-aware datetimes when the
    # column is configured with timezone=True. This also handles a
    # naive datetime returned by a different database configuration.
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)

    return deadline <= now


@router.get("/levels")
def get_quiz_levels(
    payload: dict = Depends(require_participant),
    db: Session = Depends(get_db),
):
    participant_id = int(payload.get("sub"))
    get_approved_participant(db, participant_id)

    rounds = db.query(QuizRound).order_by(QuizRound.level).all()
    response = []

    for round_ in rounds:
        approval = (
            db.query(RoundApproval)
            .filter(
                RoundApproval.participant_id == participant_id,
                RoundApproval.level == round_.level,
            )
            .first()
        )

        approved = bool(approval and approval.is_approved)
        active = is_round_active(db, round_.level)

        previous_completed = is_previous_level_completed(
            db, participant_id, round_.level
        )

        level_result = (
            db.query(QuizResult)
            .filter(
                QuizResult.participant_id == participant_id,
                QuizResult.level == round_.level,
            )
            .first()
        )

        level_completed = level_result is not None

        response.append({
            "level": round_.level,
            "question_count": round_.question_count,
            "seconds_per_question": round_.seconds_per_question,
            "is_approved": approved,
            "is_round_active": active,
            "is_unlocked": bool(round_.is_unlocked and active),
            "is_completed": level_completed,
          
                "can_start": bool(
                    approved
                    and active
                    and round_.is_unlocked
                    and previous_completed
                    and not level_completed
                    ),
            
                })

    return response




@router.get("/leaderboard-status")
def get_participant_leaderboard_status(
    payload: dict = Depends(require_participant),
    db: Session = Depends(get_db),
):
    participant_id = int(payload.get("sub"))
    get_approved_participant(db, participant_id)

    level_3_result = (
        db.query(QuizResult)
        .filter(
            QuizResult.participant_id == participant_id,
            QuizResult.level == 3,
        )
        .first()
    )

    has_completed_level_3 = level_3_result is not None

    setting = (
        db.query(LeaderboardSetting)
        .filter(LeaderboardSetting.id == 1)
        .first()
    )

    is_published = (
        setting is not None and setting.is_published is True
    )

    can_view_results = has_completed_level_3 and is_published

    if not has_completed_level_3:
        message = "Complete Level 3 to view your results."
    elif not is_published:
        message = "Final results are waiting for administrator publication."
    else:
        message = "Final results are available."

    return {
        "has_completed_level_3": has_completed_level_3,
        "is_published": is_published,
        "can_view_results": can_view_results,
        "message": message,
    }

@router.get("/leaderboard")
def get_participant_leaderboard(
    payload: dict = Depends(require_participant),
    db: Session = Depends(get_db),
):
    participant_id = int(payload.get("sub"))
    get_approved_participant(db, participant_id)

    setting = (
        db.query(LeaderboardSetting)
        .filter(LeaderboardSetting.id == 1)
        .first()
    )

    if setting is None or not setting.is_published:
        raise HTTPException(
            status_code=403,
            detail="Final results have not been published yet.",
        )

    level_3_result = (
        db.query(QuizResult)
        .filter(
            QuizResult.participant_id == participant_id,
            QuizResult.level == 3,
        )
        .first()
    )

    if level_3_result is None:
        raise HTTPException(
            status_code=403,
            detail="Complete Level 3 to view final results.",
        )

    results = (
        db.query(QuizResult, Participant)
        .join(
            Participant,
            QuizResult.participant_id == Participant.id,
        )
        .order_by(QuizResult.level, QuizResult.id)
        .all()
    )

    results.sort(
        key=lambda item: (
            item[0].level,
            -(item[0].score or 0),
            (
                item[0].duration_seconds
                if item[0].duration_seconds is not None
                else float("inf")
            ),
            (
                item[0].submitted_at.isoformat()
                if item[0].submitted_at is not None
                else ""
            ),
            item[0].id,
        )
    )

    ranks = {}
    leaderboard = []

    for result, participant in results:
        level = result.level
        ranks[level] = ranks.get(level, 0) + 1

        leaderboard.append({
            "rank": ranks[level],
            "participant_name": participant.name,
            "register_number": participant.register_number,
            "college_name": participant.college_name,
            "level": result.level,
            "score": result.score,
            "correct_answers": result.correct_answers,
            "wrong_answers": result.wrong_answers,
            "unanswered": result.unanswered,
            "duration_seconds": result.duration_seconds,
            "submitted_at": result.submitted_at,
        })

    return {
        "is_published": True,
        "leaderboard": leaderboard,
    }


@router.get("/questions/{level}")
def get_level_questions_endpoint(
    level: int,
    payload: dict = Depends(require_participant),
    db: Session = Depends(get_db),
):
    participant_id = int(payload.get("sub"))
    get_approved_participant(db, participant_id)
    get_round_approval(db, participant_id, level)
    if not is_previous_level_completed(db, participant_id, level):
        raise HTTPException(
        status_code=403,
        detail=f"Complete Level {level - 1} before starting Level {level}",
    )

    round_ = get_round(db, level)

    # Allow an already-started participant to reload their questions
    # after the admin ends the round. No new session can start then.
    active_session = (
        db.query(QuizSession)
        .filter(
            QuizSession.participant_id == participant_id,
            QuizSession.level == level,
            QuizSession.status == "in_progress",
        )
        .order_by(QuizSession.id.desc())
        .first()
    )

    if not is_round_active(db, level) and not active_session:
        raise HTTPException(
            status_code=403,
            detail="This round is not active",
        )

    if not round_.is_unlocked:
        raise HTTPException(
            status_code=403,
            detail="This level is locked",
        )

    questions = get_level_questions(
        db,
        level,
        round_.question_count,
    )

    # Never expose correct answers or explanations.
    return [
        {
            "id": question.id,
            "question_text": question.question_text,
            "options": {
                "A": question.option_a,
                "B": question.option_b,
                "C": question.option_c,
                "D": question.option_d,
            },
        }
        for question in questions
    ]


@router.post("/start/{level}")
def start_quiz_level(
    level: int,
    payload: dict = Depends(require_participant),
    db: Session = Depends(get_db),
):
    participant_id = int(payload.get("sub"))
    get_approved_participant(db, participant_id)
    get_round_approval(db, participant_id, level)
    if not is_previous_level_completed(db, participant_id, level):
        raise HTTPException(
        status_code=403,
        detail=f"Complete Level {level - 1} before accessing Level {level}",
    )

    round_ = get_round(db, level)

    
    get_level_questions(db, level, round_.question_count)

    now = utc_now()

    existing_session = (
        db.query(QuizSession)
        .filter(
            QuizSession.participant_id == participant_id,
            QuizSession.level == level,
            QuizSession.status == "in_progress",
        )
        .order_by(QuizSession.id.desc())
        .first()
    )

    if existing_session:
        if session_deadline_is_past(existing_session, now):
            existing_session.status = "expired"
            existing_session.completed_at = now
            db.commit()

            raise HTTPException(
                status_code=403,
                detail="Quiz time has expired",
            )
        
        # Initialize the question deadline for older sessions
        # that were created before this feature was added.
        if existing_session.question_deadline_at is None:
            existing_session.question_deadline_at = now + timedelta(
                seconds=round_.seconds_per_question
            )
            db.commit()

 # Resume the same session without resetting its timer or progress.
        saved_answers = {}

        if existing_session.answers_json:
            try:
                saved_answers = json.loads(existing_session.answers_json)
            except (json.JSONDecodeError, TypeError):
                saved_answers = {}

       
        return {
            "session_id": existing_session.id,
            "level": existing_session.level,
            "started_at": existing_session.started_at,
            "deadline_at": existing_session.deadline_at,
             "question_deadline_at": existing_session.question_deadline_at,
            "status": existing_session.status,
            "current_question_index": existing_session.current_question_index,
            "answers": saved_answers,
        }


    previous_sessions = (
        db.query(QuizSession)
        .filter(
            QuizSession.participant_id == participant_id,
            QuizSession.level == level,
        )
        .order_by(QuizSession.id.desc())
        .all()
    )

    if not round_.is_unlocked or not is_round_active(db, level):
        raise HTTPException(
            status_code=403,
            detail="This round is not active",
        )

    if previous_sessions:
        last_session = previous_sessions[0]

       

        attempt_number = last_session.attempt_number + 1
        last_session.retry_authorized = False
    else:
        attempt_number = 1

    duration_seconds = (
        round_.question_count * round_.seconds_per_question
    )

    # The participant's individual timer begins here, not when the
    # administrator activates the round.
    session = QuizSession(
        participant_id=participant_id,
        level=level,
        attempt_number=attempt_number,
        started_at=now,
        deadline_at=now + timedelta(seconds=duration_seconds),
         question_deadline_at=now + timedelta(
           seconds=round_.seconds_per_question
        ),
        status="in_progress",
        retry_authorized=False,
    )

    db.add(session)
    db.commit()
    db.refresh(session)

  
    return {
        "session_id": session.id,
        "level": session.level,
        "started_at": session.started_at,
        "deadline_at": session.deadline_at,
         "question_deadline_at": session.question_deadline_at,
        "status": session.status,
        "duration_seconds": duration_seconds,
        "current_question_index": session.current_question_index,
        "answers": {},
    }


class QuizSubmission(BaseModel):
    session_id: int
    answers: dict[int, str] = Field(default_factory=dict)

class QuizProgressUpdate(BaseModel):
    session_id: int
    current_question_index: int = Field(ge=0)
    answers: dict[int, str] = Field(default_factory=dict)



@router.patch("/progress")
def save_quiz_progress(
    progress: QuizProgressUpdate,
    payload: dict = Depends(require_participant),
    db: Session = Depends(get_db),
):
    participant_id = int(payload.get("sub"))
    get_approved_participant(db, participant_id)

    session = (
        db.query(QuizSession)
        .filter(
            QuizSession.id == progress.session_id,
            QuizSession.participant_id == participant_id,
        )
        .with_for_update()
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Quiz session not found",
        )

    if session.status != "in_progress":
        raise HTTPException(
            status_code=409,
            detail="Quiz session is already closed",
        )

    now = utc_now()

    if session_deadline_is_past(session, now):
        session.status = "expired"
        session.completed_at = now
        db.commit()
        raise HTTPException(
            status_code=403,
            detail="Quiz time has expired",
        )

    get_round_approval(db, participant_id, session.level)

    round_ = get_round(db, session.level)
    questions = get_level_questions(
        db,
        session.level,
        round_.question_count,
    )
    valid_question_ids = {question.id for question in questions}

    if not questions:
        raise HTTPException(
            status_code=404,
            detail="No questions available for this round",
        )

    current_index = session.current_question_index or 0
    requested_index = progress.current_question_index

    if requested_index < 0 or requested_index >= len(questions):
        raise HTTPException(
            status_code=422,
            detail="Invalid question index",
        )

    # Allow saving the current question or moving forward by one.
    if requested_index not in {
        current_index,
        current_index + 1,
    }:
        raise HTTPException(
            status_code=422,
            detail="Invalid question navigation",
        )

    for question_id, option in progress.answers.items():
        if question_id not in valid_question_ids:
            raise HTTPException(
                status_code=422,
                detail="Invalid question ID",
            )

        if option not in {"A", "B", "C", "D"}:
            raise HTTPException(
                status_code=422,
                detail="Invalid answer option",
            )

    # Initialize the timer for sessions created before this feature.
    if session.question_deadline_at is None:
        session.question_deadline_at = min(
            now + timedelta(seconds=round_.seconds_per_question),
            session.deadline_at,
        )

    # A new question gets a new timer; saving the same question
    # does not reset its timer.
    if requested_index == current_index + 1:
        session.current_question_index = requested_index
        session.question_deadline_at = min(
            now + timedelta(seconds=round_.seconds_per_question),
            session.deadline_at,
        )

    session.answers_json = json.dumps(progress.answers)

    db.commit()
    db.refresh(session)

    return {
        "saved": True,
        "current_question_index": session.current_question_index,
        "deadline_at": session.deadline_at,
        "question_deadline_at": session.question_deadline_at,
    }

@router.post("/submit")
def submit_quiz(
    submission: QuizSubmission,
    payload: dict = Depends(require_participant),
    db: Session = Depends(get_db),
):
    participant_id = int(payload.get("sub"))
    get_approved_participant(db, participant_id)

    session = (
        db.query(QuizSession)
        .filter(
            QuizSession.id == submission.session_id,
            QuizSession.participant_id == participant_id,
        )
        .with_for_update()
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Quiz session not found",
        )

    if session.status != "in_progress":
        raise HTTPException(
            status_code=409,
            detail="Quiz session is already closed",
        )

    get_round_approval(db, participant_id, session.level)

    now = utc_now()

    if session_deadline_is_past(session, now):
        session.status = "expired"
        session.completed_at = now
        db.commit()

        raise HTTPException(
            status_code=403,
            detail="Quiz time has expired",
        )

    round_ = get_round(db, session.level)

    questions = get_level_questions(
        db,
        session.level,
        round_.question_count,
    )

    question_ids = {question.id for question in questions}

    for question_id, option in submission.answers.items():
        if question_id not in question_ids:
            raise HTTPException(
                status_code=422,
                detail="An answer contains an invalid question ID",
            )

        if option not in {"A", "B", "C", "D"}:
            raise HTTPException(
                status_code=422,
                detail="Answers must be A, B, C, or D",
            )

    correct = 0
    wrong = 0
    unanswered = 0

    for question in questions:
        selected = submission.answers.get(question.id)

        if selected is None:
            unanswered += 1
        elif selected == question.correct_option:
            correct += 1
        else:
            wrong += 1

    duration_seconds = max(
        0,
        int((now - session.started_at).total_seconds()),
    )

    result = QuizResult(
        participant_id=participant_id,
        level=session.level,
        correct_answers=correct,
        wrong_answers=wrong,
        unanswered=unanswered,
        score=correct,
        duration_seconds=duration_seconds,
        answers_json=json.dumps(submission.answers),
    )

    session.answers_json = json.dumps(submission.answers)
    session.status = "completed"
    session.completed_at = now

    db.add(result)
    db.commit()

    return {
        "message": "Quiz submitted successfully",
        "level": session.level,
        "total_questions": len(questions),
        "submitted": True,
    }
