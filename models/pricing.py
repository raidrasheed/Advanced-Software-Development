from sqlalchemy import Column, Integer, String, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Pricing(Base):
    __tablename__ = 'service_pricing'

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_id = Column(Integer, nullable=True)
    price = Column(Float, nullable=True)
    shift = Column(Enum('morning', 'afternoon', 'evening'), nullable=True)