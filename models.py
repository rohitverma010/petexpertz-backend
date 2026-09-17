from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from database import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    owner_name = Column(String(100), nullable=False)
    mobile = Column(String(20), nullable=False)
    email = Column(String(150), nullable=False)
    pet_name = Column(String(100), nullable=False)
    pet_type = Column(String(50), nullable=False)
    breed = Column(String(100), nullable=True)
    age = Column(String(20), nullable=True)
    gender = Column(String(20), nullable=True)
    service_required = Column(String(100), nullable=False)
    preferred_date = Column(String(20), nullable=False)
    preferred_time = Column(String(20), nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String(20), default="Pending")
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
