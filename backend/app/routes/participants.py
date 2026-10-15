from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import require_participant
from ..models import Participant

router = APIRouter(prefix="/api/participant", tags=["Participant"])


@router.get("/me")
def get_my_profile(
    payload: dict = Depends(require_participant),
    db: Session = Depends(get_db),
):
    participant_id = payload.get("sub")

    try:
        participant_id = int(participant_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid participant identity",
        )

    participant = (
        db.query(Participant)
        .filter(Participant.id == participant_id)
        .first()
    )

    if not participant or not participant.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Participant account is unavailable",
        )

    if not participant.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Participant approval required",
        )

    return {
        "id": participant.id,
        "name": participant.name,
        "register_number": participant.register_number,
        "college_name": participant.college_name,
        "college_location": participant.college_location,
        "department": participant.department,
        "course": participant.course,
        "email": participant.email,
        "is_approved": participant.is_approved,
    }


