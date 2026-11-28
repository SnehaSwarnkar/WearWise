from pydantic import BaseModel, ConfigDict
from typing import Optional


class SignupRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class SellerApplyRequest(BaseModel):
    name: Optional[str] = None
    email: str
    password: str
    store_name: str
    owner_name: Optional[str] = None
    phone: Optional[str] = None
    business_type: Optional[str] = "Apparel Brand"
    business_address: Optional[str] = None
    store_description: Optional[str] = ""


class AdminCreateSellerRequest(BaseModel):
    name: str
    email: str
    password: str
    store_name: str
    business_email: Optional[str] = None
    store_description: Optional[str] = ""
    brand_tagline: Optional[str] = ""
    brand_id: Optional[str] = None
    approved: bool = True


class SellerStatusUpdateRequest(BaseModel):
    status: str  # active | pending | rejected | suspended
    seller_approved: Optional[bool] = None
    rejection_reason: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str = "shopper"
    status: str = "active"
    is_active: bool = True
    seller_approved: bool = False
    brand_id: Optional[str] = None
    store_name: Optional[str] = None
    store_slug: Optional[str] = None
    owner_name: Optional[str] = None
    phone: Optional[str] = None
    business_email: Optional[str] = None
    business_type: Optional[str] = None
    business_address: Optional[str] = None
    store_description: Optional[str] = None
    brand_tagline: Optional[str] = None
    rejection_reason: Optional[str] = None
    verified_at: Optional[str] = None
    gender: Optional[str] = None          # men | women | kids
    bodyType: Optional[str] = None
    kidsGender: Optional[str] = None      # boys | girls  (kids only)
    ageGroup: Optional[str] = None        # 2-5 | 6-10 | 11-14  (kids only)
    onboardingDone: bool = False
    createdAt: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    csrf_token: Optional[str] = None
    user: UserResponse


class ProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    gender: Optional[str] = None
    bodyType: Optional[str] = None
    kidsGender: Optional[str] = None
    ageGroup: Optional[str] = None
    onboardingDone: Optional[bool] = None
