import os
import tempfile
import unittest
from datetime import date, timedelta

from cardpine.scheduler import ReviewState
from cardpine.store import Store, state_path


class TestStore(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.deck = os.path.join(self.dir, "greek.txt")

    def test_new_card_is_due_immediately(self):
        store = Store()
        self.assertTrue(store.is_due("abc", date.today()))

    def test_record_and_reload_round_trip(self):
        store = Store()
        due = date.today() + timedelta(days=6)
        store.record("abc", ReviewState(repetitions=2, interval=6), due)
        store.save(self.deck)

        reloaded = Store.load(self.deck)
        self.assertEqual(reloaded.get_state("abc").interval, 6)
        self.assertEqual(reloaded.due_date("abc"), due)

    def test_card_not_due_before_its_due_date(self):
        store = Store()
        future = date.today() + timedelta(days=3)
        store.record("abc", ReviewState(interval=3), future)
        self.assertFalse(store.is_due("abc", date.today()))
        self.assertTrue(store.is_due("abc", future))

    def test_state_path_is_sibling_json(self):
        self.assertTrue(state_path("/tmp/deck.txt").endswith("deck.cardpine.json"))


if __name__ == "__main__":
    unittest.main()
