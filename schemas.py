from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime


class AppointmentCreate(BaseModel):
    owner_name: str
    mobile: str
    email: EmailStr
    pet_name: str
    pet_type: str
    breed: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[str] = None
    service_required: str
    preferred_date: str
    preferred_time: str
    notes: Optional[str] = None

    @field_validator("owner_name", "pet_name", "mobile", "service_required")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("This field cannot be blank")
        return v.strip()


class AppointmentResponse(BaseModel):
    id: int
    owner_name: str
    mobile: str
    email: str
    pet_name: str
    pet_type: str
    breed: Optional[str]
    age: Optional[str]
    gender: Optional[str]
    service_required: str
    preferred_date: str
    preferred_time: str
    notes: Optional[str]
    status: str
    submitted_at: datetime

    model_config = {"from_attributes": True}


class AppointmentStatusUpdate(BaseModel):
    status: str
