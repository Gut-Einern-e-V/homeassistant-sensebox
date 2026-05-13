"""Shared utility helpers for the openSenseMap integration."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def parse_timestamp(raw: Any) -> datetime | None:
    """Parse API timestamps like 2026-05-13T14:00:00.000Z."""
    if not isinstance(raw, str) or not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
