import unittest

from cardpine.scheduler import (
    MIN_EASINESS,
    ReviewState,
    schedule,
    GRADE_AGAIN,
    GRADE_GOOD,
    GRADE_EASY,
)


class TestScheduler(unittest.TestCase):
    def test_first_correct_review_sets_one_day(self):
        state = schedule(ReviewState(), GRADE_GOOD)
        self.assertEqual(state.repetitions, 1)
        self.assertEqual(state.interval, 1)

    def test_second_correct_review_sets_six_days(self):
        state = ReviewState(repetitions=1, interval=1, easiness=2.5)
        state = schedule(state, GRADE_GOOD)
        self.assertEqual(state.repetitions, 2)
        self.assertEqual(state.interval, 6)

    def test_third_review_multiplies_by_easiness(self):
        state = ReviewState(repetitions=2, interval=6, easiness=2.5)
        state = schedule(state, GRADE_GOOD)
        self.assertEqual(state.repetitions, 3)
        self.assertEqual(state.interval, round(6 * 2.5))

    def test_failure_resets_streak_and_interval(self):
        state = ReviewState(repetitions=5, interval=40, easiness=2.6)
        state = schedule(state, GRADE_AGAIN)
        self.assertEqual(state.repetitions, 0)
        self.assertEqual(state.interval, 1)

    def test_easiness_never_drops_below_floor(self):
        state = ReviewState(easiness=1.3)
        for _ in range(10):
            state = schedule(state, GRADE_AGAIN)
        self.assertGreaterEqual(state.easiness, MIN_EASINESS)

    def test_easy_grade_raises_easiness(self):
        state = schedule(ReviewState(easiness=2.5), GRADE_EASY)
        self.assertGreater(state.easiness, 2.5)

    def test_invalid_quality_raises(self):
        with self.assertRaises(ValueError):
            schedule(ReviewState(), 9)

    def test_state_round_trips_through_dict(self):
        state = ReviewState(repetitions=3, interval=15, easiness=2.36)
        restored = ReviewState.from_dict(state.as_dict())
        self.assertEqual(restored.repetitions, 3)
        self.assertEqual(restored.interval, 15)
        self.assertAlmostEqual(restored.easiness, 2.36, places=3)


if __name__ == "__main__":
    unittest.main()
