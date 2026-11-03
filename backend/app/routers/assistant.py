"""
POST /api/assistant/chat   — send a message to the WearWise AI stylist

The assistant uses a rule-based engine to generate contextual replies.
Each response is tailored to the user's saved avatar profile and wardrobe.
Swap the _generate_reply() function body for an LLM call when ready.
"""

from fastapi import APIRouter
from app.schemas.assistant import ChatRequest, ChatResponse
from app import database as db

router = APIRouter(prefix="/api/assistant", tags=["Fashion Assistant"])


# ── INTENT PATTERNS ──────────────────────────────────────────────────────────

_INTENTS = {
    "date": [
        "date", "romantic", "evening", "dinner", "night out", "restaurant"
    ],
    "casual": [
        "casual", "everyday", "daily", "relaxed", "weekend", "chill"
    ],
    "formal": [
        "formal", "office", "work", "interview", "meeting", "corporate"
    ],
    "party": [
        "party", "club", "dance", "festival", "birthday", "celebration"
    ],
    "wardrobe": [
        "wardrobe", "my clothes", "i have", "i own", "my pieces"
    ],
    "outfit": [
        "outfit", "what to wear", "wear tonight", "wear today", "look"
    ],
    "color": [
        "color", "colour", "palette", "shade", "tone", "hue"
    ],
    "avatar": [
        "profile", "avatar", "my style", "style profile", "body type"
    ],
}

_REPLIES: dict[str, str] = {
    "date": (
        "For a romantic evening, I'd suggest soft textures and a warm palette. "
        "Think a silk-effect top in blush or champagne paired with tailored trousers. "
        "A fitted midi dress also works beautifully if you want one-and-done dressing."
    ),
    "casual": (
        "For casual days I'd lean into your most comfortable silhouettes. "
        "An oversized tee with wide-leg jeans and clean trainers is always a win. "
        "Neutral tones keep it effortless — add one coloured piece to lift the look."
    ),
    "formal": (
        "For office or formal settings, focus on clean lines and solid colours. "
        "A well-fitted blazer instantly elevates any base outfit. "
        "Trousers or a structured midi skirt with minimal accessories hit the right note."
    ),
    "party": (
        "Party looks are all about confidence. Go for something with movement — "
        "a bold mini dress, sequin-accented pieces, or a statement jacket over basics. "
        "Don't overthink it: wear what makes you feel like the main character."
    ),
    "wardrobe": (
        "I can see your wardrobe items. Try combining a statement top from your collection "
        "with neutral bottoms for an easy everyday look. "
        "Visit your Wardrobe page to see all your pieces and get pairing ideas."
    ),
    "outfit": (
        "To build a full outfit, start with one hero piece — a dress, a jacket, or a standout top. "
        "Then build around it with neutrals. Shoes and a bag in the same tone family "
        "tie everything together without overthinking."
    ),
    "color": (
        "Your colour profile matters more than trends. "
        "If you suit warm tones, reach for peach, caramel and earthy reds. "
        "Cool undertones? Dusty rose, lavender and icy blues are your best friends. "
        "Head to My Style to discover your full colour profile."
    ),
    "avatar": (
        "Your WearWise style profile captures your body type, colour direction and vibe. "
        "It powers all your recommendations here. "
        "You can update it anytime from the Build Avatar page."
    ),
    "default": (
        "I'm checking your style profile, wardrobe and available fashion options "
        "to build the best recommendation for you. "
        "Tell me more about the occasion, your mood or the look you're going for "
        "and I'll get more specific."
    ),
}

_SUGGESTIONS_MAP: dict[str, list[str]] = {
    "date": ["Show me shoes for a date", "What jewellery works?", "Best colour for evening?"],
    "casual": ["Easy outfit ideas", "What to wear on weekends?", "Style my wardrobe"],
    "formal": ["Smart casual ideas", "Best work blazers", "What shoes for the office?"],
    "party": ["What to wear to a festival?", "Bold outfit ideas", "Statement accessories?"],
    "wardrobe": ["What can I build from my wardrobe?", "Missing basics checklist", "Outfit from my pieces"],
    "outfit": ["Full outfit ideas", "Build me a look", "What goes with my jeans?"],
    "color": ["My colour palette", "Best colours for warm tones", "What colours suit me?"],
    "avatar": ["Update my style profile", "Rebuild my avatar", "What styles suit me?"],
    "default": [
        "What should I wear tonight?",
        "Style my wardrobe",
        "Find something for a date",
        "Compare these two looks",
    ],
}


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _detect_intent(text: str) -> str:
    lower = text.lower()
    for intent, keywords in _INTENTS.items():
        if any(kw in lower for kw in keywords):
            return intent
    return "default"


def _generate_reply(message: str, session_id: str) -> tuple[str, list[str]]:
    """
    Rule-based reply engine.
    If a style profile exists for the session, personalise the response.
    """
    intent = _detect_intent(message)

    # Optionally enrich with profile data
    all_profiles = db.find_all("avatar_profiles")
    profile = next(
        (p for p in reversed(all_profiles) if p.get("session_id") == session_id),
        None,
    )

    reply = _REPLIES[intent]

    if profile and intent in ("casual", "color", "outfit"):
        body_type = profile.get("bodyType", "")
        colour = profile.get("colour", "")
        styles = profile.get("styles", [])

        additions = []
        if body_type:
            additions.append(f"Since your body profile is {body_type}, look for cuts that emphasise balance.")
        if colour:
            additions.append(f"Your {colour} colour direction means you'll shine in {colour}-tone palettes.")
        if styles:
            additions.append(f"Your saved vibes ({', '.join(styles)}) are a great starting point for this look.")

        if additions:
            reply = reply + " " + " ".join(additions)

    return reply, _SUGGESTIONS_MAP.get(intent, _SUGGESTIONS_MAP["default"])


# ── ROUTE ─────────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    """Receive a user message and return an AI stylist reply."""
    reply, suggestions = _generate_reply(payload.message, payload.session_id)
    return ChatResponse(reply=reply, suggestions=suggestions)
