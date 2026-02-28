from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from database import Base
from sqlalchemy.orm import relationship
from datetime import datetime
class Habit(Base):
    __tablename__="habits"
    id = Column(Integer,primary_key=True,index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    completed = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="habits")
    streak = Column(Integer, default=0)
    last_log_date = Column(DateTime, nullable=True)
    established = Column(Boolean, default=False)

    user = relationship("User", back_populates="habits")
    logs = relationship("HabitLog", back_populates="habit", cascade="all, delete-orphan")
class HabitLog(Base):
    __tablename__ = "habit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False)
    date = Column(DateTime, default=datetime.now)

    habit = relationship("Habit", back_populates="logs")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    habits = relationship("Habit", back_populates="user")