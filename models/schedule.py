from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship
from database import Base
from models.clinics import Clinic
from sqlalchemy import Enum

class Schedule(Base):
    __tablename__ = "doctor_schedules"
    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    date = Column(Date, nullable=False)
    time_slot = Column(Enum("MORNING", "AFTERNOON", "EVENING", name="time_slot_enum"), nullable=False)
    is_available = Column(Boolean, default=True)
    
    clinic = relationship("Clinic", back_populates="schedules")
    doctor = relationship("Doctor", back_populates="schedules") 