"""Offline checks that the made-up sample emails are well formed. No API calls."""

import json
import unittest

from email_triage import questions as q
from email_triage.run import SAMPLE_FILE, SAMPLE_TODAY

PRIVATE_HINTS = ("@gmail.com", "@yahoo.com", "@hotmail.com", "@outlook.com")


class SampleData(unittest.TestCase):
    def setUp(self):
        self.threads = json.loads(SAMPLE_FILE.read_text(encoding="utf-8"))

    def test_every_thread_builds_a_request(self):
        for t in self.threads:
            payload = q.build_request(q.build_state(t, SAMPLE_TODAY))
            self.assertIn("asks_you", payload["questions"], t["id"])

    def test_expected_piles_are_real_piles(self):
        for t in self.threads:
            self.assertIn(t["expected"], q.PILES, t["id"])

    def test_every_pile_is_represented(self):
        self.assertEqual({t["expected"] for t in self.threads}, set(q.PILES))

    def test_only_fictional_addresses(self):
        text = json.dumps(self.threads).lower()
        for hint in PRIVATE_HINTS:
            self.assertNotIn(hint, text)


if __name__ == "__main__":
    unittest.main()
