from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="employee", nullable=False)  # employee | manager
    created_at = Column(DateTime, default=datetime.utcnow)

    expenses = relationship("Expense", back_populates="owner")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(String(255), nullable=False)
    status = Column(String(20), default="PENDING", nullable=False)  # PENDING | APPROVED | REJECTED
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="expenses")