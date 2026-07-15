"""SM-2 spaced-repetition scheduling.

A clean, self-contained implementation of the SuperMemo-2 algorithm. The
core is a pure function so it is trivial to reason about and unit test.
"""

from __future__ import annotations

from dataclasses import dataclass

# The lowest an easiness factor is ever allowed to fall.
MIN_EASINESS = 1.3

# Quality grades a learner can give a card during review.
GRADE_AGAIN = 0  # complete blank / wrong
GRADE_HARD = 3  # correct, but with serious difficulty
GRADE_GOOD = 4  # correct after some hesitation
GRADE_EASY = 5  # perfect recall


@dataclass
class ReviewState:
    """Everything the scheduler needs to remember about a single card."""

    repetitions: int = 0  # consecutive correct answers
    interval: int = 0  # days until the card is due again
    easiness: float = 2.5  # SM-2 easiness factor

    def as_dict(self) -> dict:
        return {
            "repetitions": self.repetitions,
            "interval": self.interval,
            "easiness": round(self.easiness, 4),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ReviewState":
        return cls(
            repetitions=int(data.get("repetitions", 0)),
            interval=int(data.get("interval", 0)),
            easiness=float(data.get("easiness", 2.5)),
        )


def schedule(state: ReviewState, quality: int) -> ReviewState:
    """Return the next :class:`ReviewState` for a card given a review grade.

    ``quality`` is an integer from 0 (total blank) to 5 (perfect). Grades
    below 3 reset the learning streak; grades of 3 or more advance it.
    """

    if not 0 <= quality <= 5:
        raise ValueError("quality must be between 0 and 5")

    if quality < 3:
        # Lapsed: the learner failed to recall the card. Restart the streak
        # but keep (a slightly reduced) easiness so genuinely hard cards
        # settle at a shorter interval over time.
        repetitions = 0
        interval = 1
    else:
        repetitions = state.repetitions + 1
        if repetitions == 1:
            interval = 1
        elif repetitions == 2:
            interval = 6
        else:
            interval = round(state.interval * state.easiness)

    # Update the easiness factor using the standard SM-2 response curve.
    easiness = state.easiness + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    easiness = max(MIN_EASINESS, easiness)

    return ReviewState(repetitions=repetitions, interval=interval, easiness=easiness)
