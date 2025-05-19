from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey, UniqueConstraint, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    booking_date = Column(Date, nullable=False)
    patient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    room = relationship("Room", back_populates="bookings")
    patient = relationship("User", back_populates="bookings")

    # Unique constraint to ensure room is only booked once per day
    __table_args__ = (
        UniqueConstraint('room_id', 'booking_date', name='unique_room_date'),
    )
