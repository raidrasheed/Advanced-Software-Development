from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from models.clinics import Clinic
from models.schedule import Schedule

class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False)
    full_name = Column(String(100), nullable=False)
    experience = Column(Integer, nullable=False)  # Years of experience
    speciality = Column(String(100), nullable=False)
    description = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    user = relationship("User", back_populates="doctor")
    clinic = relationship("Clinic", back_populates="doctors")
    schedules = relationship("Schedule", back_populates="doctor")
    appointments = relationship("Appointment", foreign_keys="[Appointment.doctor_id]", back_populates="doctor")