from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.preflight_service import PreflightService

router = APIRouter(prefix="/api/v1/preflight", tags=["preflight"])

preflight_service = PreflightService()


class PreflightAnalyzeRequest(BaseModel):
    user_input: str
    session_id: str


@router.post("/analyze")
async def analyze_preflight(req: PreflightAnalyzeRequest):
    from app.services.session_manager import SessionManager

    sm = SessionManager()
    session = await sm.get(req.session_id)

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await preflight_service.analyze(
        user_input=req.user_input,
        session=session.to_dict(),
    )

    return result
