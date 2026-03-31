from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/vibesense", tags=["vibesense"])


@router.post("/analyze")
async def analyze_input(data: dict[str, str]):
    from app.services.vibe_sense import VibeSense
    vibe = VibeSense()
    text = data.get("text", "")
    result = vibe.analyze(text)
    result["formatted"] = vibe.format_suggestion(result)
    return result
