from datetime import datetime
from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=8, max_length=72)
    role: str = Field(default="employee", pattern="^(employee|manager)$")


class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1, max_length=72)


class UserOut(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ExpenseCreate(BaseModel):
    amount: float = Field(..., gt=0, le=100000, description="Must be a positive amount")
    category: str = Field(..., min_length=2, max_length=50, pattern="^[a-zA-Z0-9 _-]+$")
    description: str = Field(..., min_length=3, max_length=255)


class ExpenseStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(APPROVED|REJECTED)$")


class ExpenseOut(BaseModel):
    id: int
    owner_id: int
    amount: float
    category: str
    description: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True