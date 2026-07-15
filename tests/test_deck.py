import unittest

from cardpine.deck import parse, Card

SAMPLE = """# Capitals of Europe

// a comment line that should be ignored

What is the capital of France?
===
Paris

What is the capital of Spain?
===
Madrid
"""


class TestDeck(unittest.TestCase):
    def test_parses_title(self):
        deck = parse(SAMPLE)
        self.assertEqual(deck.title, "Capitals of Europe")

    def test_parses_all_cards(self):
        deck = parse(SAMPLE)
        self.assertEqual(len(deck), 2)
        self.assertEqual(deck.cards[0].front, "What is the capital of France?")
        self.assertEqual(deck.cards[0].back, "Paris")

    def test_ignores_comments(self):
        deck = parse(SAMPLE)
        self.assertTrue(all("comment" not in c.front for c in deck.cards))

    def test_skips_malformed_block(self):
        deck = parse("front with no separator\n\na\n===\nb")
        self.assertEqual(len(deck), 1)
        self.assertEqual(deck.cards[0].front, "a")

    def test_card_uid_is_stable_and_content_based(self):
        a = Card("q", "a")
        b = Card("q", "a")
        c = Card("q", "different")
        self.assertEqual(a.uid, b.uid)
        self.assertNotEqual(a.uid, c.uid)

    def test_multiline_back_is_preserved(self):
        deck = parse("term\n===\nline one\nline two")
        self.assertEqual(deck.cards[0].back, "line one\nline two")


if __name__ == "__main__":
    unittest.main()
