import os
import json
from app.system_prompt import default_system_prompt, retired_default_system_prompt
from app.rag import get_default_rag_source_dir


def get_base_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_data_dir():
    base = get_base_dir()
    data_dir = os.path.join(base, "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_settings_path():
    return os.path.join(get_data_dir(), "settings.json")


def get_db_path():
    return os.path.join(get_data_dir(), "conversations.db")


MODEL_CHOICES = [
    {
        "id": "vortex/helpingai-9b",
        "label": "HelpingAI 9B \u2014 Recommended",
        "description": "Your regular Tobias model. Best overall quality for everyday conversations.",
    },
    {
        "id": "qwen3:8b",
        "label": "Qwen3 8B",
        "description": "High-quality alternative for general use. Requires more system resources.",
    },
    {
        "id": "qwen2.5:3b",
        "label": "Qwen2.5 3B \u2014 Lightweight",
        "description": "Lightweight option for lower-end computers. Uses fewer system resources.",
    },
]
MODEL_IDS = [c["id"] for c in MODEL_CHOICES]
DEFAULT_MODEL = "vortex/helpingai-9b"


def model_label(model_id):
    for c in MODEL_CHOICES:
        if c["id"] == model_id:
            return c["label"]
    return model_id


def model_description(model_id):
    for c in MODEL_CHOICES:
        if c["id"] == model_id:
            return c["description"]
    return ""


default_settings = {
    "ollama_url": "http://localhost:11434",
    "model": DEFAULT_MODEL,
    "temperature": 0.7,
    "context_length": 4096,
    "max_tokens": 1024,
    "system_prompt": default_system_prompt,
    "streaming": True,
    "rag_enabled": True,
    "rag_source_dir": get_default_rag_source_dir(),
    "rag_top_k": 5,
    "rag_embed_model": "nomic-embed-text"
}

def load_settings():
    path = get_settings_path()
    if not os.path.exists(path):
        save_settings(default_settings)
        return dict(default_settings)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return dict(default_settings)
    merged = dict(default_settings)
    merged.update(data)
    if merged.get("model") not in MODEL_IDS:
        merged["model"] = DEFAULT_MODEL
    if str(merged.get("system_prompt", "")).strip() == retired_default_system_prompt.strip():
        merged["system_prompt"] = default_system_prompt
    return merged


def save_settings(settings):
    path = get_settings_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
