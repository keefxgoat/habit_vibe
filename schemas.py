from pydantic import BaseModel
from typing import Optional
class HabitCreate(BaseModel):
    title: str
    description: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str

class HabitResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    completed: bool
    streak: int
    established: bool

    model_config = {
        "from_attributes": True
    }
class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True