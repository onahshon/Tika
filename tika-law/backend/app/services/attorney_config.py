import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent.parent / "core" / "attorneys.json"
_cache: dict | None = None


def get_attorney_config(attorney_id: str) -> dict | None:
    global _cache
    if _cache is None:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            _cache = json.load(f)
    return _cache.get(attorney_id)
