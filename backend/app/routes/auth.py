
import os
import jwt
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..database import get_db
from ..models import Participant
from ..schemas import ParticipantRegister, ParticipantLogin
from ..security import hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_participant(
    participant_data: ParticipantRegister,
    db: Session = Depends(get_db),
):
    existing_email = (
        db.query(Participant)
        .filter(
            Participant.email == str(participant_data.email).lower()
        )
        .first()
    )

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    existing_register_number = (
        db.query(Participant)
        .filter(
            Participant.register_number
            == participant_data.register_number.strip()
        )
        .first()
    )

    if existing_register_number:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Register number is already registered",
        )

    participant = Participant(
        name=participant_data.name.strip(),
        register_number=participant_data.register_number.strip(),
        college_name=participant_data.college_name.strip(),
        college_location=participant_data.college_location,
        gender=participant_data.gender,
        phone=participant_data.phone.strip(),
        email=str(participant_data.email).lower(),
        department=participant_data.department.strip(),
        course=participant_data.course.strip(),
        hashed_password=hash_password(participant_data.password),
        is_approved=False,
        is_active=True,
    )

    try:
        db.add(participant)
        db.commit()
        db.refresh(participant)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or register number is already registered",
        )

    return {
        "message": "Registration successful. Waiting for admin approval.",
        "participant": {
            "id": participant.id,
            "name": participant.name,
            "register_number": participant.register_number,
            "email": participant.email,
            "is_approved": participant.is_approved,
        },
    }


@router.post("/login")
def login_participant(
    login_data: ParticipantLogin,
    db: Session = Depends(get_db),
):
    email = str(login_data.email).lower()

    participant = (
        db.query(Participant)
        .filter(Participant.email == email)
        .first()
    )

    if not participant or not verify_password(
        login_data.password,
        participant.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not participant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    if not participant.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is waiting for admin approval",
        )

    secret_key = os.getenv("SECRET_KEY")
    algorithm = os.getenv("ALGORITHM", "HS256")
    expires_minutes = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )

    if (
        not secret_key
        or secret_key == "replace_with_a_long_random_secret_key"
    ):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT secret key is not configured",
        )

    if algorithm != "HS256":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unsupported JWT algorithm configuration",
        )

    now = datetime.now(timezone.utc)

    access_token = jwt.encode(
        {
            "sub": str(participant.id),
            "role": "participant",
            "iat": now,
            "exp": now + timedelta(minutes=expires_minutes),
        },
        secret_key,
        algorithm=algorithm,
    )

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "participant": {
            "id": participant.id,
            "name": participant.name,
            "register_number": participant.register_number,
            "email": participant.email,
            "is_approved": participant.is_approved,
        },
    }
