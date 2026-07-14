"""Small ANSI helpers for a tidy terminal interface."""

from __future__ import annotations

import os
import sys

_ENABLED = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None

_CODES = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "cyan": "\033[36m",
    "magenta": "\033[35m",
    "red": "\033[31m",
    "grey": "\033[90m",
}


def style(text: str, *names: str) -> str:
    if not _ENABLED:
        return text
    prefix = "".join(_CODES[n] for n in names if n in _CODES)
    return f"{prefix}{text}{_CODES['reset']}"


def rule(width: int = 52) -> str:
    return style("─" * width, "grey")


def box(text: str, width: int = 52) -> str:
    """Render a single-line-or-multi-line string inside a rounded box."""
    lines = text.split("\n")
    inner = width - 2
    top = style("╭" + "─" * inner + "╮", "cyan")
    bottom = style("╰" + "─" * inner + "╯", "cyan")
    body = []
    for line in lines:
        for chunk in _wrap(line, inner - 2):
            pad = chunk.ljust(inner - 2)
            edge = style("│", "cyan")
            body.append(f"{edge} {pad} {edge}")
    return "\n".join([top, *body, bottom])


def _wrap(text: str, width: int):
    if text == "":
        return [""]
    words = text.split(" ")
    lines, current = [], ""
    for word in words:
        candidate = word if not current else current + " " + word
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def clear() -> None:
    if _ENABLED:
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()
