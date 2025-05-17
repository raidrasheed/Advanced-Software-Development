from sqlalchemy import Column, Integer, String, Float, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import enum

class ServiceType(enum.Enum):
    PREVENTIVE_CARE = "PREVENTIVE_CARE"
    BASIC_RESTORATIVE = "BASIC_RESTORATIVE"
    MAJOR_RESTORATIVE = "MAJOR_RESTORATIVE"
    SPECIALTY_SERVICES = "SPECIALTY_SERVICES"

class TimeSlot(enum.Enum):
    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"
    EVENING = "EVENING"

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    booking_reference = Column(String(255), unique=True, nullable=False)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    room_id = Column(Integer, nullable=False)
    service_type = Column(Enum(ServiceType), nullable=False)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False)
    time_slot = Column(Enum(TimeSlot), nullable=False)
    appointment_date = Column(DateTime, nullable=False)
    price = Column(Float, nullable=False)
    status = Column(String(50), nullable=False, default="SCHEDULED")
    created_at = Column(DateTime, nullable=False)

    # Relationships
    doctor = relationship("Doctor", foreign_keys=[doctor_id], back_populates="appointments")
    clinic = relationship("Clinic", back_populates="appointments")
    patient = relationship("User", back_populates="appointments")
    # room = relationship("Room", back_populates="appointments")
