from pydantic import BaseModel,EmailStr
from typing import Optional,List
from datetime import datetime


class UserCreate(BaseModel):
    email : EmailStr
    password : str
    full_name : str
    phone_number: Optional[str] = None
    
class UserOut(BaseModel):
    id : int
    email: EmailStr
    full_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email : EmailStr
    password : str

class Token(BaseModel):
    access_token : str
    token_type : str


class TokenData(BaseModel):
    user_id: Optional[int] = None

class JobCreate(BaseModel):
    title: str
    description: Optional[str] = None
    required_skills: List[str]  

class JobOut(JobCreate):
    id: int
    company_id: int

    class Config:
        from_attributes = True