from pydantic import BaseModel
from typing import Optional


class AvatarProfile(BaseModel):
    session_id: str
    mode: str                        # "manual" | "ai"
    colour: Optional[str] = None     # warm | cool | neutral | bold
    bodyType: Optional[str] = None
    fit: Optional[str] = None        # Fitted | Relaxed | Oversized | Mixed
    styles: list[str] = []
    selectedColour: Optional[str] = None  # hex from AI mode colour picker


class AvatarProfileResponse(AvatarProfile):
    id: str
    createdAt: str
