from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any

from app.services.tool_executor import ToolExecutor
from app.config import settings

router = APIRouter(prefix="/api/v1/tools", tags=["tools"])

executor = ToolExecutor(allowed_paths=settings.tool_allowed_paths)


class ToolExecuteRequest(BaseModel):
    params: dict[str, Any] = {}


@router.get("")
async def list_tools():
    return {"tools": executor.list_tools()}


@router.post("/{tool_name}/execute")
async def execute_tool(tool_name: str, req: ToolExecuteRequest):
    result = await executor.execute(tool_name, req.params)
    if not result.get("success", False) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
