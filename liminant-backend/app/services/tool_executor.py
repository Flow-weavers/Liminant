import asyncio
import os
import subprocess
from pathlib import Path
from typing import Any


class ToolExecutor:
    def __init__(self, allowed_paths: list[str] | None = None):
        self.allowed_paths = [Path(p) for p in (allowed_paths or ["/workspace"])]

    def _is_path_safe(self, path: str) -> bool:
        try:
            resolved = Path(path).resolve()
            for allowed in self.allowed_paths:
                if resolved.is_relative_to(allowed):
                    return True
            return False
        except Exception:
            return False

    async def execute_file_read(self, path: str) -> dict[str, Any]:
        if not self._is_path_safe(path):
            return {"success": False, "error": "Path not allowed"}
        try:
            p = Path(path)
            if not p.exists():
                return {"success": False, "error": "File not found"}
            content = p.read_text(encoding="utf-8")
            return {"success": True, "content": content, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def execute_file_write(self, path: str, content: str) -> dict[str, Any]:
        if not self._is_path_safe(path):
            return {"success": False, "error": "Path not allowed"}
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def execute_bash(self, command: str, cwd: str | None = None) -> dict[str, Any]:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=cwd,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def execute(self, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        if tool_name == "file_read":
            return await self.execute_file_read(params.get("path", ""))
        elif tool_name == "file_write":
            return await self.execute_file_write(
                params.get("path", ""), params.get("content", "")
            )
        elif tool_name == "bash":
            return await self.execute_bash(
                params.get("command", ""), params.get("cwd")
            )
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

    def list_tools(self) -> list[dict[str, str]]:
        return [
            {"name": "file_read", "description": "Read a file from the filesystem"},
            {"name": "file_write", "description": "Write content to a file"},
            {"name": "bash", "description": "Execute a bash/shell command"},
        ]
