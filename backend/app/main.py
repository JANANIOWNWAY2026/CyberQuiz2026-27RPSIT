
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.participants import router as participant_router
from .database import Base, engine
from . import models
from .routes.auth import router as auth_router
from .routes.admin import router as admin_router
from .routes.quiz import router as quiz_router
from .routes.leaderboard import router as leaderboard_router
from .routes.exam_guard import router as exam_guard_router
app = FastAPI(
    title="CyberQuiz API",
    description="Cybersecurity Quiz Backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)




app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(participant_router)
app.include_router(quiz_router)
app.include_router(leaderboard_router)
app.include_router(exam_guard_router)
@app.on_event("startup")
def create_database_tables():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return {"message": "CyberQuiz Backend is running!"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}