from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserProfileResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime


class UpdateUserProfileRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)