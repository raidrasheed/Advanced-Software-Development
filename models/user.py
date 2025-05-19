from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    contact = Column(String(15), nullable=False)
    identifier = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    role = Column(Enum('CUSTOMER','DOCTOR','ADMIN_OFFICER','MANAGER','ADMIN', name='user_role'), nullable=False)

    appointments = relationship("Appointment", back_populates="patient")
    bookings = relationship("Booking", back_populates="patient")