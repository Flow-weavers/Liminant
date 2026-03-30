import os
from pathlib import Path
from typing import Any, Optional
import aiofiles
import json


class JsonStorage:
    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            base_dir = os.environ.get(
                "LIMINANT_DATA_DIR",
                str(Path(__file__).parent.parent.parent / "data")
            )
        self.base_dir = Path(base_dir)
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        for subdir in ["sessions", "knowledge", "config", "cache"]:
            (self.base_dir / subdir).mkdir(parents=True, exist_ok=True)

    def _resolve(self, category: str, key: str) -> Path:
        return self.base_dir / category / f"{key}.json"

    async def read(self, category: str, key: str) -> Optional[dict[str, Any]]:
        path = self._resolve(category, key)
        if not path.exists():
            return None
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            content = await f.read()
            return json.loads(content) if content else None

    async def write(self, category: str, key: str, data: dict[str, Any]) -> None:
        path = self._resolve(category, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, indent=2, ensure_ascii=False))

    async def delete(self, category: str, key: str) -> bool:
        path = self._resolve(category, key)
        if path.exists():
            path.unlink()
            return True
        return False

    async def list_keys(self, category: str) -> list[str]:
        dir_path = self.base_dir / category
        if not dir_path.exists():
            return []
        return [p.stem for p in dir_path.iterdir() if p.suffix == ".json"]

    async def exists(self, category: str, key: str) -> bool:
        return self._resolve(category, key).exists()


_storage: Optional[JsonStorage] = None


def get_storage() -> JsonStorage:
    global _storage
    if _storage is None:
        _storage = JsonStorage()
    return _storage
