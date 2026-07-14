"""Command-line entry point for cardpine."""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta

from . import __version__, ui
from .deck import load as load_deck
from .scheduler import (
    GRADE_AGAIN,
    GRADE_EASY,
    GRADE_GOOD,
    GRADE_HARD,
    schedule,
)
from .store import Store

LOGO = r"""
    card   _
   .-----.| |
   | ?   || |  cardpine
   | ___ |'-'
   '-----'
"""

_GRADE_KEYS = {
    "1": ("Again", GRADE_AGAIN, "red"),
    "2": ("Hard", GRADE_HARD, "yellow"),
    "3": ("Good", GRADE_GOOD, "green"),
    "4": ("Easy", GRADE_EASY, "cyan"),
}


def _due_cards(deck, store, today):
    return [c for c in deck.cards if store.is_due(c.uid, today)]


def cmd_review(args) -> int:
    deck = load_deck(args.deck)
    if len(deck) == 0:
        print(ui.style("This deck has no cards yet.", "yellow"))
        return 0

    store = Store.load(args.deck)
    today = date.today()
    due = _due_cards(deck, store, today)
    if args.limit:
        due = due[: args.limit]

    if not due:
        ui.clear()
        print(ui.style("✓ All caught up!", "green", "bold"))
        print(ui.style(f"Nothing due in “{deck.title}” today.", "grey"))
        upcoming = min((store.due_date(c.uid) for c in deck.cards), default=None)
        if upcoming and upcoming > today:
            print(ui.style(f"Next review: {upcoming.isoformat()}", "grey"))
        return 0

    reviewed = 0
    for index, card in enumerate(due, start=1):
        ui.clear()
        print(ui.style(f"  {deck.title}", "bold"))
        print(ui.style(f"  Card {index} of {len(due)} due", "grey"))
        print()
        print(ui.box(card.front))
        try:
            input(ui.style("\n  press enter to reveal answer…", "dim"))
        except (EOFError, KeyboardInterrupt):
            print()
            break

        print(ui.box(card.back))
        print()
        print(
            "  "
            + "   ".join(
                ui.style(f"[{k}] {label}", colour)
                for k, (label, _, colour) in _GRADE_KEYS.items()
            )
        )
        choice = None
        while choice is None:
            try:
                raw = input(ui.style("  grade › ", "bold")).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                store.save(args.deck)
                return 0
            if raw in _GRADE_KEYS:
                choice = _GRADE_KEYS[raw]
            elif raw == "":
                choice = _GRADE_KEYS["3"]  # enter = Good
            else:
                print(ui.style("  please press 1, 2, 3 or 4", "yellow"))

        _label, quality, _colour = choice
        new_state = schedule(store.get_state(card.uid), quality)
        next_due = today + timedelta(days=max(1, new_state.interval))
        store.record(card.uid, new_state, next_due)
        reviewed += 1

    store.save(args.deck)
    ui.clear()
    print(ui.style("✓ Session complete", "green", "bold"))
    print(ui.style(f"  Reviewed {reviewed} card(s) in “{deck.title}”.", "grey"))
    remaining = len(_due_cards(deck, Store.load(args.deck), today))
    print(ui.style(f"  {remaining} still due today.", "grey"))
    return 0


def cmd_stats(args) -> int:
    deck = load_deck(args.deck)
    store = Store.load(args.deck)
    today = date.today()

    total = len(deck)
    new = sum(1 for c in deck.cards if c.uid not in store.records)
    due = len(_due_cards(deck, store, today))
    learned = sum(1 for c in deck.cards if store.get_state(c.uid).repetitions >= 3)

    print(ui.style(f"  {deck.title}", "bold"))
    print(ui.rule())
    rows = [
        ("Total cards", total, "cyan"),
        ("Due today", due, "yellow"),
        ("New (never seen)", new, "magenta"),
        ("Learned (3+ streak)", learned, "green"),
    ]
    for label, value, colour in rows:
        print(f"  {label.ljust(22)} {ui.style(str(value), colour, 'bold')}")

    upcoming = sorted(
        (
            (store.due_date(c.uid), c)
            for c in deck.cards
            if c.uid in store.records and store.due_date(c.uid) > today
        ),
        key=lambda pair: pair[0],
    )
    if upcoming:
        print(ui.rule())
        print(ui.style("  Next up", "grey"))
        for due_on, card in upcoming[:5]:
            when = (due_on - today).days
            label = "tomorrow" if when == 1 else f"in {when} days"
            preview = card.front.split("\n")[0][:34]
            print(f"    {ui.style(label.ljust(12), 'grey')} {preview}")
    return 0


def cmd_list(args) -> int:
    deck = load_deck(args.deck)
    print(ui.style(f"  {deck.title}  ({len(deck)} cards)", "bold"))
    print(ui.rule())
    for i, card in enumerate(deck.cards, start=1):
        front = card.front.split("\n")[0][:44]
        print(f"  {ui.style(str(i).rjust(3), 'grey')}  {front}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cardpine",
        description="Spaced-repetition flashcards for your terminal.",
    )
    parser.add_argument(
        "--version", action="version", version=f"cardpine {__version__}"
    )
    sub = parser.add_subparsers(dest="command")

    p_review = sub.add_parser("review", help="review cards that are due")
    p_review.add_argument("deck", help="path to a deck text file")
    p_review.add_argument("--limit", type=int, default=0, help="max cards this session")
    p_review.set_defaults(func=cmd_review)

    p_stats = sub.add_parser("stats", help="show progress for a deck")
    p_stats.add_argument("deck", help="path to a deck text file")
    p_stats.set_defaults(func=cmd_stats)

    p_list = sub.add_parser("list", help="list the cards in a deck")
    p_list.add_argument("deck", help="path to a deck text file")
    p_list.set_defaults(func=cmd_list)

    return parser


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        print(ui.style(LOGO, "cyan"))
        parser.print_help()
        return 0
    try:
        return args.func(args)
    except FileNotFoundError:
        print(ui.style(f"Deck not found: {args.deck}", "red"))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
