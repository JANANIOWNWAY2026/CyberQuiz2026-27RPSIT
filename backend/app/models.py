from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
    func,
)
from .database import Base


class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    register_number = Column(String(50), unique=True, nullable=False, index=True)
    college_name = Column(String(200), nullable=False)
    college_location = Column(String(200), nullable=True)
    gender = Column(String(20), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    department = Column(String(100), nullable=False)
    course = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)

    is_approved = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class QuizRound(Base):
    __tablename__ = "quiz_rounds"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(Integer, unique=True, nullable=False)
    question_count = Column(Integer, nullable=False)
    seconds_per_question = Column(Integer, nullable=False)
    is_unlocked = Column(Boolean, default=False, nullable=False)


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(Integer, nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    option_a = Column(String(500), nullable=False)
    option_b = Column(String(500), nullable=False)
    option_c = Column(String(500), nullable=False)
    option_d = Column(String(500), nullable=False)
    correct_option = Column(String(1), nullable=False)
    explanation = Column(Text, nullable=True)


class QuizResult(Base):
    __tablename__ = "quiz_results"

    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(
        Integer,
        ForeignKey("participants.id"),
        nullable=False,
        index=True,
    )
    level = Column(Integer, nullable=False)
    correct_answers = Column(Integer, default=0, nullable=False)
    wrong_answers = Column(Integer, default=0, nullable=False)
    unanswered = Column(Integer, default=0, nullable=False)
    score = Column(Integer, default=0, nullable=False)
    duration_seconds = Column(Integer, default=0, nullable=False)
    answers_json = Column(Text, nullable=True)
        
    submitted_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
   
class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id = Column(Integer, primary_key=True, index=True)

    participant_id = Column(
        Integer,
        ForeignKey("participants.id"),
        nullable=False,
        index=True,
    )

    level = Column(Integer, nullable=False, index=True)
    attempt_number = Column(Integer, nullable=False, default=1)

    started_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    deadline_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    question_deadline_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    status = Column(
        String(20),
        nullable=False,
        default="in_progress",
    )

    answers_json = Column(Text, nullable=True)
     
    current_question_index = Column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    retry_authorized = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
 
class LeaderboardSetting(Base):
    __tablename__ = "leaderboard_settings"

    id = Column(Integer, primary_key=True, default=1)
    is_published = Column(Boolean, default=False, nullable=False)

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

class RoundApproval(Base):
    __tablename__ = "round_approvals"

    __table_args__ = (
        UniqueConstraint(
            "participant_id",
            "level",
            name="uq_round_approval_participant_level",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(
        Integer,
        ForeignKey("participants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    level = Column(Integer, nullable=False, index=True)
    is_approved = Column(Boolean, default=False, nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class RoundControl(Base):
    __tablename__ = "round_controls"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(Integer, unique=True, nullable=False)
    status = Column(String(20), default="locked", nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)

