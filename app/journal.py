import os
import re
from datetime import datetime

from app.config import get_data_dir

BUCKET_LABELS = ["Today", "Yesterday", "This week", "Older"]


def get_journal_dir():
    d = os.path.join(get_data_dir(), "journals")
    os.makedirs(d, exist_ok=True)
    return d


def _parse_fname(name):
    m = re.match(
        r"^(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})(?:_(\d+))?\.txt$",
        name,
    )
    if not m:
        return None
    try:
        return datetime(
            int(m.group(1)), int(m.group(2)), int(m.group(3)),
            int(m.group(4)), int(m.group(5)), int(m.group(6)),
        )
    except ValueError:
        return None


def new_entry_path():
    base = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    d = get_journal_dir()
    candidate = os.path.join(d, base + ".txt")
    n = 2
    while os.path.exists(candidate):
        candidate = os.path.join(d, "%s_%d.txt" % (base, n))
        n += 1
    return candidate


def header_for(path):
    dt = _parse_fname(os.path.basename(path))
    if dt is None:
        return "", ""
    date_line = dt.strftime("%A, %B %d, %Y")
    time_line = dt.strftime("%I:%M %p").lstrip("0")
    return date_line, time_line


def write_entry(path, body):
    date_line, time_line = header_for(path)
    content = date_line + "\n" + time_line + "\n\n" + body
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def read_entry(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.split("\n")
    if len(lines) <= 2:
        return ""
    return "\n".join(lines[2:]).lstrip("\n")


def delete_entry(path):
    try:
        os.remove(path)
    except OSError:
        pass


def preview(text, limit=90):
    plain = " ".join(text.strip().split())
    if not plain:
        return "Empty entry"
    if len(plain) > limit:
        return plain[:limit].rstrip() + "\u2026"
    return plain


def bucket_for(dt):
    diff = (datetime.now().date() - dt.date()).days
    if diff <= 0:
        return "Today"
    if diff == 1:
        return "Yesterday"
    if diff < 7:
        return "This week"
    return "Older"


def list_entries():
    entries = []
    for name in os.listdir(get_journal_dir()):
        if not name.lower().endswith(".txt"):
            continue
        path = os.path.join(get_journal_dir(), name)
        dt = _parse_fname(name)
        if dt is None:
            continue
        try:
            body = read_entry(path)
        except OSError:
            body = ""
        entries.append({
            "path": path,
            "name": name,
            "dt": dt,
            "body": body,
            "bucket": bucket_for(dt),
        })
    entries.sort(key=lambda e: e["dt"], reverse=True)
    return entries


def search(query):
    q = (query or "").strip().lower()
    entries = list_entries()
    if not q:
        return entries
    return [e for e in entries if q in e["body"].lower()]


def read_selected(paths):
    """Read only the explicitly selected journal files. Returns (entries, total_chars)."""
    entries = []
    total = 0
    seen = set()
    for path in paths:
        if not path or path in seen:
            continue
        seen.add(path)
        try:
            body = read_entry(path)
        except OSError:
            continue
        if not body.strip():
            continue
        date_line, time_line = header_for(path)
        label = (date_line + " " + time_line).strip() or os.path.basename(path)
        entries.append({"path": path, "label": label, "body": body})
        total += len(body)
    return entries, total


def format_selected_for_reflection(entries, max_chars=14000):
    """Build a readable, bounded context string for reflection, newest first."""
    ordered = sorted(entries, key=lambda e: e.get("label", ""), reverse=False)
    parts = []
    budget = max_chars
    for e in ordered:
        body = e["body"].strip()
        if len(body) > budget:
            body = body[:budget] + "\u2026 [truncated]"
        parts.append((e.get("label", ""), body))
        budget -= len(body)
        if budget <= 0:
            break
    blocks = []
    for i, (label, body) in enumerate(parts, start=1):
        blocks.append("Entry %d (%s):\n%s" % (i, label, body))
    return "\n\n---\n\n".join(blocks)
