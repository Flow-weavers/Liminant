import platform
import subprocess
import shutil
from pathlib import Path
from typing import Any


class ToolExecutor:
    def __init__(self, allowed_paths: list[str] | None = None):
        self._system = platform.system()
        self._allowed_paths = allowed_paths or self._default_allowed_paths()
        self._allowed_resolved = [Path(p).resolve() for p in self._allowed_paths]
        self._powershell_path = self._find_powershell()

    def _default_allowed_paths(self) -> list[str]:
        if self._system == "Windows":
            user_dir = Path.home()
            return [
                str(user_dir / "workspace"),
                str(user_dir / "Liminant"),
                "d:\\Liminant",
                "c:\\workspace",
            ]
        return ["/workspace"]

    def _find_powershell(self) -> str:
        pwsh = shutil.which("pwsh")
        if pwsh:
            return pwsh
        powershell = shutil.which("powershell")
        if powershell:
            return powershell
        return "powershell.exe"

    def _is_path_safe(self, path: str) -> bool:
        try:
            resolved = Path(path).resolve()
            for allowed in self._allowed_resolved:
                try:
                    resolved.relative_to(allowed)
                    return True
                except ValueError:
                    continue
            if self._system == "Windows":
                if resolved.drive == Path.cwd().drive:
                    return True
            return False
        except Exception:
            return False

    async def execute_file_read(self, path: str) -> dict[str, Any]:
        if not self._is_path_safe(path):
            return {"success": False, "error": f"Path not allowed: {path}"}
        try:
            p = Path(path)
            if not p.exists():
                return {"success": False, "error": f"File not found: {path}"}
            content = p.read_text(encoding="utf-8", errors="replace")
            return {"success": True, "content": content, "path": str(p)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def execute_file_write(self, path: str, content: str) -> dict[str, Any]:
        if not self._is_path_safe(path):
            return {"success": False, "error": f"Path not allowed: {path}"}
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return {"success": True, "path": str(p), "size": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def execute_bash(self, command: str, cwd: str | None = None) -> dict[str, Any]:
        if not command.strip():
            return {"success": False, "error": "Empty command"}

        effective_cwd = cwd or str(Path.cwd())

        try:
            if self._system == "Windows":
                ps_command = self._to_powershell(command)
                result = subprocess.run(
                    [self._powershell_path, "-NoProfile", "-NonInteractive", "-Command", ps_command],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=effective_cwd,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
                )
            else:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=effective_cwd,
                )

            stdout = result.stdout
            stderr = result.stderr
            if not stdout and not stderr:
                stdout = "(no output)"

            return {
                "success": result.returncode == 0,
                "stdout": stdout,
                "stderr": stderr,
                "returncode": result.returncode,
                "shell": "powershell" if self._system == "Windows" else "bash",
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out after 60s"}
        except FileNotFoundError:
            return {"success": False, "error": f"Shell not found: {self._powershell_path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _to_powershell(self, bash_cmd: str) -> str:
        cmd = bash_cmd.strip()

        if cmd.startswith("cat > ") or cmd.startswith("echo "):
            if cmd.startswith("cat > "):
                parts = cmd[7:].split(" <<", 1)
                if len(parts) == 2:
                    file_target = parts[0].strip().strip("'\"")
                    delimiter = parts[1].strip().strip("'\"")
                    return f'{delimiter}\n{cmd}\n{delimiter}'

        if cmd.startswith("cat ") and " <<" in cmd:
            return cmd

        if cmd.startswith("echo ") and " > " in cmd:
            parts = cmd[5:].split(" > ", 1)
            content = parts[0].strip().strip("'\"")
            target = parts[1].strip().strip("'\"")
            content_escaped = content.replace("'", "''")
            return f"@'\n{content}\n'@ | Out-File -FilePath '{target}' -Encoding UTF8"

        if cmd.startswith("cat ") and " > " in cmd:
            return cmd.replace("cat ", "Get-Content ").replace(" > ", " | Out-File -FilePath ")

        return cmd

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
        if self._system == "Windows":
            return [
                {"name": "file_read", "description": "Read the complete contents of a file from the filesystem."},
                {"name": "file_write", "description": "Write or overwrite content to a file. Creates parent directories if needed."},
                {"name": "bash", "description": "Execute a PowerShell command and return its stdout/stderr."},
            ]
        return [
            {"name": "file_read", "description": "Read the complete contents of a file from the filesystem."},
            {"name": "file_write", "description": "Write or overwrite content to a file. Creates parent directories if needed."},
            {"name": "bash", "description": "Execute a bash/shell command and return its stdout/stderr."},
        ]
