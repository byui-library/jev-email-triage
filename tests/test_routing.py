"""Offline tests for the follow-up truth table and state building. No API calls."""

import unittest
from datetime import date

from email_triage import questions as q
from email_triage.run import is_automated

TODAY = date(2026, 10, 29)


def thread(*msgs):
    return {
        "id": "t1",
        "subject": "Test",
        "messages": [
            {"sender": s, "from_me": s == "me", "date": d, "body": b} for s, d, b in msgs
        ],
    }


def answers(asks=0.5, await_=0.5, deadline=0.5, personal=0.9, issue=0.1, roles=None, due=None, sus=0.05):
    a = {
        "asks_you": {"type": "noul", "noul": asks},
        "open_issue": {"type": "noul", "noul": issue},
        "looks_suspicious": {"type": "noul", "noul": sus},
        "you_await_reply": {"type": "noul", "noul": await_},
        "has_deadline": {"type": "noul", "noul": deadline},
        "written_personally": {"type": "noul", "noul": personal},
        "sender_role": {
            "type": "choice",
            "choice": "colleague",
            "confidence": 0.9,
            "probabilities": roles or {"colleague": 1.0},
        },
    }
    if due:
        a["deadline_date"] = {"type": "choice", "choice": due, "confidence": 0.9, "probabilities": {due: 1.0}}
    return a


THEM_LAST = thread(("Jane <jane@x.edu>", "2026-10-25T10:00:00Z", "Can you send the report?"))
ME_LAST = thread(
    ("Jane <jane@x.edu>", "2026-10-20T10:00:00Z", "Hi"),
    ("me", "2026-10-26T10:00:00Z", "Could you confirm the date?"),
)


class TruthTable(unittest.TestCase):
    def pile(self, t, **kw):
        return q.route(q.build_state(t, TODAY), answers(**kw))[0]

    def test_them_last_personal(self):
        self.assertEqual(self.pile(THEM_LAST, asks=0.9), "reply_needed")
        self.assertEqual(self.pile(THEM_LAST, asks=0.5), "check")
        self.assertEqual(self.pile(THEM_LAST, asks=0.1), "no_action")

    def test_unsettled_personal_with_ask_goes_to_check(self):
        self.assertEqual(self.pile(THEM_LAST, asks=0.9, personal=0.5), "check")
        self.assertEqual(self.pile(THEM_LAST, asks=0.9, personal=0.31), "check")
        self.assertEqual(self.pile(THEM_LAST, asks=0.9, personal=0.7), "reply_needed")
        # without an ask, an unsettled sender still follows the normal rows
        self.assertEqual(self.pile(THEM_LAST, asks=0.1, personal=0.5), "no_action")

    def test_them_last_bulk(self):
        self.assertEqual(self.pile(THEM_LAST, asks=0.9, personal=0.1, deadline=0.9), "check")
        self.assertEqual(self.pile(THEM_LAST, asks=0.9, personal=0.1, deadline=0.5), "no_action")
        self.assertEqual(self.pile(THEM_LAST, asks=0.9, personal=0.1, deadline=0.1), "no_action")
        self.assertEqual(self.pile(THEM_LAST, asks=0.5, personal=0.1, deadline=0.9), "no_action")

    def test_promotion_with_deadline_not_checked(self):
        promo = {"vendor_or_sales": 0.8, "service_provider": 0.2}
        self.assertEqual(self.pile(THEM_LAST, asks=0.9, personal=0.1, deadline=0.9, roles=promo), "no_action")
        notice = {"vendor_or_sales": 0.1, "service_provider": 0.9}
        self.assertEqual(self.pile(THEM_LAST, asks=0.9, personal=0.1, deadline=0.9, roles=notice), "check")

    def test_stale_ask_moves_to_check(self):
        s = q.build_state(THEM_LAST, TODAY)
        pile, why = q.route(s, answers(asks=0.9, deadline=0.5, due="2026-09-29"))
        self.assertEqual(pile, "check")
        self.assertIn("may be stale", why)
        # a future date leaves it alone; Jev saying "no deadline" ignores the date
        self.assertEqual(q.route(s, answers(asks=0.9, deadline=0.5, due="2026-11-05"))[0], "reply_needed")
        self.assertEqual(q.route(s, answers(asks=0.9, deadline=0.1, due="2026-09-29"))[0], "reply_needed")

    def test_suspicious_checked_first(self):
        self.assertEqual(self.pile(THEM_LAST, asks=0.9, sus=0.9), "suspicious")
        self.assertEqual(self.pile(THEM_LAST, asks=0.9, sus=0.5), "reply_needed")
        # your own last message is never flagged
        self.assertEqual(self.pile(ME_LAST, await_=0.9, sus=0.9), "waiting_on_them")

    def test_me_last(self):
        self.assertEqual(self.pile(ME_LAST, await_=0.9), "waiting_on_them")
        self.assertEqual(self.pile(ME_LAST, await_=0.5), "check")
        self.assertEqual(self.pile(ME_LAST, await_=0.1), "no_action")

    def test_me_last_ignores_asks_you(self):
        self.assertEqual(self.pile(ME_LAST, asks=0.99, await_=0.1), "no_action")

    def test_open_issue(self):
        self.assertEqual(self.pile(ME_LAST, await_=0.1, issue=0.9), "open_issue")
        self.assertEqual(self.pile(THEM_LAST, asks=0.1, issue=0.9), "open_issue")
        # a reply or a pending answer takes precedence over tracking the issue
        self.assertEqual(self.pile(THEM_LAST, asks=0.9, issue=0.9), "reply_needed")
        self.assertEqual(self.pile(ME_LAST, await_=0.9, issue=0.9), "waiting_on_them")

    def test_bulk_ignores_open_issue(self):
        self.assertEqual(self.pile(THEM_LAST, asks=0.1, personal=0.1, issue=0.9), "no_action")

    def test_overdue_deadline_noted(self):
        s = q.build_state(ME_LAST, TODAY)
        pile, reason = q.route(s, answers(await_=0.9, deadline=0.9, due="2026-10-28"))
        self.assertEqual(pile, "waiting_on_them")
        self.assertIn("its date passed 1 day(s) ago", reason)


class Priority(unittest.TestCase):
    def test_bounds(self):
        s = q.build_state(THEM_LAST, TODAY)
        hi = q.priority(s, answers(asks=1, deadline=1, roles={"supervisor_or_leader": 1.0}, due="2026-10-30"), "reply_needed")
        lo = q.priority(s, answers(asks=0, deadline=0, roles={"vendor_or_sales": 1.0}), "no_action")
        self.assertGreater(hi, lo)
        self.assertLessEqual(hi, 100)
        self.assertGreaterEqual(lo, 0)

    def test_older_ranks_higher(self):
        old = thread(("Jane", "2026-10-15T10:00:00Z", "x"))
        a = answers()
        self.assertGreater(q.priority(q.build_state(old, TODAY), a, "check"), q.priority(q.build_state(THEM_LAST, TODAY), a, "check"))

    def test_near_deadline_ranks_higher_than_distant(self):
        s = q.build_state(THEM_LAST, TODAY)
        near = q.priority(s, answers(deadline=0.9, due="2026-10-30"), "check")
        far = q.priority(s, answers(deadline=0.9, due="2026-12-20"), "check")
        self.assertGreater(near, far)


class DeadlineDates(unittest.TestCase):
    def cands(self, subject, body, sent="2026-10-28T10:00:00Z"):
        t = {"id": "t", "subject": subject, "messages": [{"sender": "A", "from_me": False, "date": sent, "body": body}]}
        return q.date_candidates(q.build_state(t, TODAY))

    def test_finds_written_dates(self):
        c = self.cands("Renew your account by October 28, 2026", "Offer ends Friday 30th October 2026 at noon. Event Fri 5 Mar 2027.")
        self.assertEqual(sorted(c), ["2026-10-28", "2026-10-30", "2027-03-05"])
        self.assertIn("subject", c["2026-10-28"])

    def test_year_inferred_from_message_date(self):
        self.assertEqual(list(self.cands("x", "the meeting is on December 3")), ["2026-12-03"])
        self.assertEqual(list(self.cands("x", "due Jan 5", sent="2026-12-20T10:00:00Z")), ["2027-01-05"])

    def test_no_dates_means_no_question(self):
        s = q.build_state(THEM_LAST, TODAY)
        self.assertNotIn("deadline_date", q.build_request(s)["questions"])
        t = thread(("Jane", "2026-10-25T10:00:00Z", "Please reply by November 2"))
        self.assertEqual(list(q.build_request(q.build_state(t, TODAY))["questions"]["deadline_date"]["criteria"]), ["2026-11-02"])


class State(unittest.TestCase):
    def test_recipients_and_how_addressed(self):
        t = thread(("Jo", "2026-10-25T10:00:00Z", "can you ask the keyboard player?"))
        self.assertNotIn("you_are_on_latest_message_from_others_as", q.build_state(t, TODAY)["facts"])
        t["messages"][0].update(to=["Sam"], cc=["You", "Alex"])
        s = q.build_state(t, TODAY)
        self.assertEqual(s["thread"]["messages"][0]["to"], ["Sam"])
        self.assertEqual(s["facts"]["you_are_on_latest_message_from_others_as"], "cc")
        t["messages"][0].update(to=["Team list"], cc=[])
        self.assertEqual(q.build_state(t, TODAY)["facts"]["you_are_on_latest_message_from_others_as"], "not listed")
        t["messages"][0].update(to=["You"])
        self.assertEqual(q.build_state(t, TODAY)["facts"]["you_are_on_latest_message_from_others_as"], "to")

    def test_attachments_only_when_present(self):
        t = thread(("Jo", "2026-10-25T10:00:00Z", "see attached"))
        self.assertNotIn("attachments", q.build_state(t, TODAY)["thread"]["messages"][0])
        t["messages"][0]["attachments"] = ["notes.pptx"]
        self.assertEqual(q.build_state(t, TODAY)["thread"]["messages"][0]["attachments"], ["notes.pptx"])

    def test_labels_and_facts(self):
        s = q.build_state(ME_LAST, TODAY)
        self.assertEqual(s["thread"]["messages"][-1]["sender"], "You")
        self.assertTrue(s["facts"]["latest_message_is_from_you"])
        self.assertEqual(s["facts"]["days_since_latest_message"], 3)

    def test_keeps_last_three(self):
        t = thread(*[("Jane", f"2026-10-2{i}T10:00:00Z", str(i)) for i in range(5)])
        s = q.build_state(t, TODAY)
        self.assertEqual([m["text"] for m in s["thread"]["messages"]], ["2", "3", "4"])
        self.assertEqual(s["thread"]["earlier_messages_not_shown"], 2)

    def test_clean_body_strips_quotes_and_signature(self):
        body = "Sounds good.\n\n--\nJane Doe\nLibrarian\n\nOn Mon, Oct 26 Bob wrote:\n> old text"
        self.assertEqual(q.clean_body(body), "Sounds good.")
        self.assertEqual(q.clean_body("Yes\n> quoted\nThanks"), "Yes Thanks")
        self.assertEqual(q.clean_body("New\n\nOn Tue, Oct 27, 2026 at 9:00 AM Al <a@x> wrote:\nold"), "New")

    def test_clean_body_removes_links(self):
        out = q.clean_body("Pay here: https://pay.example.com/checkout?ref=SECRET123 by Friday")
        self.assertNotIn("SECRET123", out)
        self.assertEqual(out, "Pay here: [link] by Friday")
        self.assertEqual(q.clean_body("[Check availability](https://x.com/a?t=1)"), "Check availability")
        self.assertEqual(q.clean_body("View → [](https://x.com/t?id=9)"), "View → [link]")

    def test_clean_body_removes_contact_details(self):
        out = q.clean_body("Call 208-555-0142 or (307) 555.0199, or write jo.smith@example.org")
        self.assertEqual(out, "Call [phone] or [phone], or write [email]")
        self.assertEqual(q.clean_body("Order 9100892977 due 2026-10-28"), "Order 9100892977 due 2026-10-28")

    def test_clean_body_removes_padding_and_tables(self):
        self.assertEqual(q.clean_body("͏ ͏ ­\nHi there"), "Hi there")
        self.assertEqual(q.clean_body("| ## Your report is ready |"), "Your report is ready")

    def test_clean_body_caps_length(self):
        out = q.clean_body("word " * 900)
        self.assertEqual(len(out.split()), q.MAX_WORDS_PER_MESSAGE + 2)

    def test_automated_filter(self):
        self.assertTrue(is_automated(thread(("Canvas <no-reply@instructure.com>", "2026-10-28T10:00:00Z", "x"))))
        self.assertFalse(is_automated(THEM_LAST))


if __name__ == "__main__":
    unittest.main()
