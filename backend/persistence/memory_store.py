import json
import os
import time

MEMORY_DIR = os.path.join(os.path.dirname(__file__), "..", "memory_data")
os.makedirs(MEMORY_DIR, exist_ok=True)

DEFAULTS = {
    "pattern_memory": {
        "date_formats": {},
        "name_patterns": {},
        "typo_frequency": {},
        "total_runs": 0,
        "last_updated": None,
    },
    "proposals": {
        "pending": [],
        "approved": [],
        "rejected": [],
    },
    "healing_log": {
        "events": [],
        "known_errors": {},
    },
    "custom_rules": [],
}


def _path(key: str) -> str:
    return os.path.join(MEMORY_DIR, f"{key}.json")


def load(key: str) -> dict | list:
    p = _path(key)
    if not os.path.exists(p):
        return DEFAULTS.get(key, {} if key not in DEFAULTS else DEFAULTS[key])
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return DEFAULTS.get(key, {})


def save(key: str, data) -> None:
    p = _path(key)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, p)


def append(key: str, item: dict) -> None:
    data = load(key)
    if isinstance(data, list):
        data.append(item)
    elif isinstance(data, dict) and "events" in data:
        data["events"].append(item)
    else:
        data = [item]
    save(key, data)


def get_stats() -> dict:
    stats = {}
    for key in DEFAULTS:
        p = _path(key)
        if os.path.exists(p):
            size = os.path.getsize(p)
            mtime = os.path.getmtime(p)
            stats[key] = {
                "exists": True,
                "size_bytes": size,
                "last_modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime)),
            }
        else:
            stats[key] = {"exists": False, "size_bytes": 0, "last_modified": None}
    return stats


def reset(key: str) -> None:
    p = _path(key)
    if os.path.exists(p):
        os.remove(p)
