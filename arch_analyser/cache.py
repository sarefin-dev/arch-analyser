import hashlib
import json
import os
from pathlib import Path

CACHE_DIR = Path(".cache/responses")


def _key(prompt_id: str, *inputs: str) -> str:
    content = prompt_id + "|".join(inputs)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def get(prompt_id: str, *inputs: str) -> dict | None:
    path = CACHE_DIR / f"{prompt_id}_{_key(prompt_id, *inputs)}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


def set(prompt_id: str, result: dict, *inputs: str) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{prompt_id}_{_key(prompt_id, *inputs)}.json"
    path.write_text(json.dumps(result, indent=2))
