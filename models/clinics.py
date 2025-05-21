from sqlalchemy import Column, Integer, String,Boolean
from sqlalchemy.orm import relationship
from database import Base

class Clinic(Base):
    __tablename__ = "clinics"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    location = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=False)

    rooms = relationship("Room", back_populates="clinic")
    doctors = relationship("Doctor", back_populates="clinic")
    schedules = relationship("Schedule", back_populates="clinic")
    appointments = relationship("Appointment", back_populates="clinic")
    
    bookings = relationship("Booking", back_populates="clinic")
