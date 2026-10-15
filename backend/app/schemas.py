
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ParticipantLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
class ParticipantRegister(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    register_number: str = Field(min_length=1, max_length=50)
    college_name: str = Field(min_length=2, max_length=200)
    college_location: str | None = None
    gender: str = Field(min_length=1, max_length=20)
    phone: str = Field(min_length=7, max_length=20)
    email: EmailStr
    department: str = Field(min_length=2, max_length=100)
    course: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class ParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    register_number: str
    email: EmailStr
    is_approved: bool