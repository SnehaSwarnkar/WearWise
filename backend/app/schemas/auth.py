from pydantic import BaseModel
from typing import Optional


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    gender: Optional[str] = None          # men | women | kids
    bodyType: Optional[str] = None
    kidsGender: Optional[str] = None      # boys | girls  (kids only)
    ageGroup: Optional[str] = None        # 2-5 | 6-10 | 11-14  (kids only)
    onboardingDone: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ProfileUpdateRequest(BaseModel):
    gender: Optional[str] = None
    bodyType: Optional[str] = None
    kidsGender: Optional[str] = None
    ageGroup: Optional[str] = None
    onboardingDone: Optional[bool] = None
