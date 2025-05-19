from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Room(Base):
    __tablename__ = 'rooms'

    id = Column(Integer, primary_key=True, autoincrement=True)
    clinic_id = Column(Integer, ForeignKey('clinics.id'))
    room_type = Column(Enum('surgery', 'regular', name='room_type'))
    room_number = Column(String(20))

    clinic = relationship("Clinic", back_populates="rooms")
    bookings = relationship("Booking", back_populates="room")
