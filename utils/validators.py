from typing import Optional


def normalize_remote_option(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    v = value.strip().lower()
    if v in {"remote", "hybrid", "onsite", "on-site", "in-person"}:
        return v
    return None


def clamp_limit(value: Optional[int], default: int = 10, max_limit: int = 50) -> int:
    try:
        v = int(value) if value is not None else default
    except (TypeError, ValueError):
        v = default
    if v <= 0:
        return default
    return min(v, max_limit)
