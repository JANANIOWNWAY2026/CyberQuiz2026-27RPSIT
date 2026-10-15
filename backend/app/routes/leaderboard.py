
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    LeaderboardSetting,
    Participant,
    QuizResult,
)

router = APIRouter(
    prefix="/api/leaderboard",
    tags=["Leaderboard"],
)


@router.get("")
def get_public_leaderboard(db: Session = Depends(get_db)):
    # Check whether the final results have been published.
    setting = (
        db.query(LeaderboardSetting)
        .filter(LeaderboardSetting.id == 1)
        .first()
    )

    if setting is None or not setting.is_published:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Final results have not been published yet.",
        )

    # Fetch results for approved and active participants.
    results = (
        db.query(QuizResult, Participant)
        .join(
            Participant,
            QuizResult.participant_id == Participant.id,
        )
        .filter(
            Participant.is_approved.is_(True),
            Participant.is_active.is_(True),
            QuizResult.level.in_([1, 2, 3]),
        )
        .order_by(
            QuizResult.submitted_at.desc(),
            QuizResult.id.desc(),
        )
        .all()
    )

    # Keep only the latest result for each participant and level.
    latest = {}

    for result, participant in results:
        key = (participant.id, result.level)

        if key not in latest:
            latest[key] = (result, participant)

    # Group results by participant.
    participants = {}

    for (participant_id, level), (result, participant) in latest.items():
        entry = participants.setdefault(
            participant_id,
            {
                "name": participant.name,
                "register_no": participant.register_number,
                "levels": {},
            },
        )

        entry["levels"][level] = result

    # Build the leaderboard.
    ranking = []

    for entry in participants.values():
        levels = entry["levels"]

        # Include only participants who completed all three levels.
        if not all(level in levels for level in (1, 2, 3)):
            continue

        total_correct = sum(
            levels[level].correct_answers
            for level in (1, 2, 3)
        )

        total_time = sum(
            levels[level].duration_seconds
            for level in (1, 2, 3)
        )

        ranking.append(
            {
                "name": entry["name"],
                "register_no": entry["register_no"],
                "level_1_correct": levels[1].correct_answers,
                "level_2_correct": levels[2].correct_answers,
                "level_3_correct": levels[3].correct_answers,
                "total_correct": total_correct,
                "total_questions": 35,
                "total_time_seconds": total_time,
            }
        )

    # Sort by highest score, then shortest completion time.
    ranking.sort(
        key=lambda item: (
            -item["total_correct"],
            item["total_time_seconds"],
            item["name"].casefold(),
        )
    )

    # Assign ranks after sorting.
    for index, item in enumerate(ranking, start=1):
        item["rank"] = index

    return {
        "published": True,
        "participants_count": len(ranking),
        "leaderboard": ranking,
    }

