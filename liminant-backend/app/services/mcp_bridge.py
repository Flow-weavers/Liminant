import re
import subprocess
from pathlib import Path
from typing import Any
from app.config import settings


class MCPToolBridge:
    TOOL_DESCRIPTORS = {
        "file_read": {
            "name": "file_read",
            "description": "Read contents of a file from the filesystem",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute path to the file"},
                },
                "required": ["path"],
            },
        },
        "file_write": {
            "name": "file_write",
            "description": "Write content to a file, creating or overwriting",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute path to the file"},
                    "content": {"type": "string", "description": "Content to write"},
                },
                "required": ["path", "content"],
            },
        },
        "bash": {
            "name": "bash",
            "description": "Execute a bash command and return its output",
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The bash command to execute"},
                    "cwd": {"type": "string", "description": "Working directory for the command"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30},
                },
                "required": ["command"],
            },
        },
        "directory_tree": {
            "name": "directory_tree",
            "description": "List directory structure as a tree",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Root path to list"},
                    "depth": {"type": "integer", "description": "Max depth", "default": 3},
                },
                "required": ["path"],
            },
        },
    }

    def __init__(self, allowed_paths: list[str] | None = None):
        self.allowed_paths = allowed_paths or ["/workspace"]

    def _is_allowed(self, path: str) -> bool:
        if not self.allowed_paths:
            return True
        abs_path = str(Path(path).resolve())
        return any(abs_path.startswith(allowed) for allowed in self.allowed_paths)

    def _resolve_path(self, path: str, cwd: str | None = None) -> Path:
        p = Path(path)
        if not p.is_absolute():
            base = Path(cwd) if cwd else Path.cwd()
            p = base / p
        return p.resolve()

    async def execute(self, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        if tool_name == "file_read":
            return await self._file_read(params["path"])
        elif tool_name == "file_write":
            return await self._file_write(params["path"], params["content"])
        elif tool_name == "bash":
            return await self._bash(params["command"], params.get("cwd"), params.get("timeout", 30))
        elif tool_name == "directory_tree":
            return await self._directory_tree(params["path"], params.get("depth", 3))
        return {"success": False, "error": f"Unknown tool: {tool_name}"}

    async def _file_read(self, path: str) -> dict[str, Any]:
        if not self._is_allowed(path):
            return {"success": False, "error": f"Access denied: {path}"}
        try:
            resolved = self._resolve_path(path)
            content = resolved.read_text(encoding="utf-8")
            return {"success": True, "content": content, "path": str(resolved)}
        except FileNotFoundError:
            return {"success": False, "error": f"File not found: {path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _file_write(self, path: str, content: str) -> dict[str, Any]:
        if not self._is_allowed(path):
            return {"success": False, "error": f"Access denied: {path}"}
        try:
            resolved = self._resolve_path(path)
            resolved.parent.mkdir(parents=True, exist_ok=True)
            resolved.write_text(content, encoding="utf-8")
            return {
                "success": True,
                "path": str(resolved),
                "bytes_written": len(content.encode()),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _bash(self, command: str, cwd: str | None = None, timeout: int = 30) -> dict[str, Any]:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Command timed out after {timeout}s", "stderr": "", "stdout": ""}
        except Exception as e:
            return {"success": False, "error": str(e), "stdout": "", "stderr": ""}

    async def _directory_tree(self, path: str, depth: int = 3) -> dict[str, Any]:
        if not self._is_allowed(path):
            return {"success": False, "error": f"Access denied: {path}"}
        try:
            root = Path(path)
            if not root.exists():
                return {"success": False, "error": f"Path not found: {path}"}

            def build_tree(p: Path, current_depth: int) -> dict:
                if current_depth >= depth:
                    return {"type": "dir", "name": p.name, "truncated": True}
                if p.is_file():
                    return {"type": "file", "name": p.name, "size": p.stat().st_size}
                children = [
                    build_tree(child, current_depth + 1)
                    for child in sorted(p.iterdir())
                ]
                return {"type": "dir", "name": p.name, "children": children}

            tree = build_tree(root, 0)
            return {"success": True, "tree": tree, "path": str(root)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_tools(self) -> list[dict]:
        return list(self.TOOL_DESCRIPTORS.values())

    def get_tool_schema(self, tool_name: str) -> dict | None:
        return self.TOOL_DESCRIPTORS.get(tool_name)
