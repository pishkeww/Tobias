import json
import os
import uuid
from datetime import datetime, timezone

from app.config import get_data_dir


def get_reflections_path():
    return os.path.join(get_data_dir(), "reflections.json")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_reflections():
    path = get_reflections_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return []
    if not isinstance(data, list):
        return []
    result = []
    for item in data:
        if not isinstance(item, dict):
            continue
        text = (item.get("text") or "").strip()
        if not text:
            continue
        result.append({
            "id": item.get("id") or str(uuid.uuid4()),
            "text": text,
            "created_at": item.get("created_at") or now_iso(),
            "source": item.get("source"),
        })
    result.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return result


def _save(reflections):
    path = get_reflections_path()
    temp = path + ".tmp"
    with open(temp, "w", encoding="utf-8") as f:
        json.dump(reflections, f, indent=2, ensure_ascii=False)
    os.replace(temp, path)


def add_reflection(text, source=None):
    text = (text or "").strip()
    if not text:
        return None
    existing = load_reflections()
    for r in existing:
        if (r.get("text") or "").strip() == text:
            return None
    item = {
        "id": str(uuid.uuid4()),
        "text": text,
        "created_at": now_iso(),
        "source": source,
    }
    existing.append(item)
    _save(existing)
    return item


def remove_reflection(ref_id):
    existing = load_reflections()
    kept = [r for r in existing if r.get("id") != ref_id]
    if len(kept) == len(existing):
        return False
    _save(kept)
    return True
