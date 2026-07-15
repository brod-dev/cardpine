"""Persisting per-card review state next to a deck file.

State lives in a sibling ``<deck>.cardpine.json`` file so a deck stays a
single portable text file and its progress is easy to inspect, back up, or
delete. Cards are keyed by content hash, not position.
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime
from typing import Dict

from .scheduler import ReviewState

_ISO = "%Y-%m-%d"


def state_path(deck_path: str) -> str:
    base, _ = os.path.splitext(deck_path)
    return base + ".cardpine.json"


class Store:
    """A tiny JSON-backed record of when each card is next due."""

    def __init__(self) -> None:
        self.records: Dict[str, dict] = {}

    @classmethod
    def load(cls, deck_path: str) -> "Store":
        store = cls()
        path = state_path(deck_path)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as handle:
                store.records = json.load(handle).get("cards", {})
        return store

    def save(self, deck_path: str) -> None:
        path = state_path(deck_path)
        payload = {"version": 1, "cards": self.records}
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")

    def get_state(self, uid: str) -> ReviewState:
        rec = self.records.get(uid)
        if not rec:
            return ReviewState()
        return ReviewState.from_dict(rec)

    def due_date(self, uid: str) -> date:
        rec = self.records.get(uid)
        if not rec or not rec.get("due"):
            return date.min  # brand-new cards are due immediately
        return datetime.strptime(rec["due"], _ISO).date()

    def is_due(self, uid: str, on: date) -> bool:
        return self.due_date(uid) <= on

    def record(self, uid: str, state: ReviewState, due: date) -> None:
        data = state.as_dict()
        data["due"] = due.strftime(_ISO)
        self.records[uid] = data
