"""Parsing plain-text deck files into cards.

Deck format is deliberately human-friendly so a deck is just a text file you
can edit in any editor:

    # Optional deck title on the first heading line

    What is the capital of France?
    ===
    Paris

    2 + 2
    ===
    4

Cards are separated by one or more blank lines. Inside a card the front and
back are split by a line containing only ``===``. Lines starting with ``#``
before the first card are treated as the deck title. ``//`` line comments are
ignored anywhere.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import List

SEPARATOR = "==="


@dataclass
class Card:
    front: str
    back: str

    @property
    def uid(self) -> str:
        """A stable id derived from the card's content.

        Using content rather than position means reordering the deck or
        adding cards in the middle does not scramble saved review history.
        """
        digest = hashlib.sha1(f"{self.front}\x00{self.back}".encode("utf-8"))
        return digest.hexdigest()[:12]


@dataclass
class Deck:
    title: str = "Untitled deck"
    cards: List[Card] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.cards)


def parse(text: str) -> Deck:
    """Parse deck ``text`` into a :class:`Deck`."""

    lines = text.splitlines()
    title = "Untitled deck"
    seen_card = False

    # Split into blocks on blank-line boundaries.
    blocks: List[List[str]] = []
    current: List[str] = []
    for raw in lines:
        line = raw.rstrip()
        if line.strip().startswith("//"):
            continue  # comment
        if line.strip() == "":
            if current:
                blocks.append(current)
                current = []
            continue
        current.append(line)
    if current:
        blocks.append(current)

    cards: List[Card] = []
    for block in blocks:
        # A leading heading block before any card becomes the title.
        if (
            not seen_card
            and block[0].lstrip().startswith("#")
            and SEPARATOR not in block
        ):
            title = block[0].lstrip("#").strip() or title
            continue

        if SEPARATOR not in [ln.strip() for ln in block]:
            # No separator: skip malformed block rather than guessing.
            continue

        split_at = [ln.strip() for ln in block].index(SEPARATOR)
        front = "\n".join(block[:split_at]).strip()
        back = "\n".join(block[split_at + 1 :]).strip()
        if not front or not back:
            continue
        seen_card = True
        cards.append(Card(front=front, back=back))

    return Deck(title=title, cards=cards)


def load(path: str) -> Deck:
    with open(path, "r", encoding="utf-8") as handle:
        return parse(handle.read())
