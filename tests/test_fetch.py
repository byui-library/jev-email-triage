"""Offline tests for the Gmail fetcher's parsing and redaction. No network calls."""

import base64
import unittest

from email_triage import fetch

OWNER = "jo.smith@example.com"


def b64(text):
    return base64.urlsafe_b64encode(text.encode()).decode().rstrip("=")


def raw_message(frm, to, cc="", subject="Hi", body="hello", files=(), ms="1790000000000", labels=()):
    parts = [{"mimeType": "text/plain", "body": {"data": b64(body)}}]
    parts += [{"filename": f, "mimeType": "application/pdf", "body": {}} for f in files]
    headers = [{"name": "From", "value": frm}, {"name": "To", "value": to},
               {"name": "Cc", "value": cc}, {"name": "Subject", "value": subject}]
    return {"internalDate": ms, "labelIds": list(labels), "payload": {"mimeType": "multipart/mixed", "headers": headers, "parts": parts}}


class Parsing(unittest.TestCase):
    def setUp(self):
        self.redact = fetch.Redactor(OWNER)

    def test_redactor(self):
        self.assertEqual(self.redact("Write to Jo.Smith@example.com"), "Write to [your address]")
        self.assertEqual(self.redact("jo.smith_report.pptx"), "[your username]_report.pptx")
        self.assertEqual(self.redact("pinjo.smithy"), "pinjo.smithy")  # not a whole token

    def test_names(self):
        self.assertEqual(fetch._names('"Sam Lee" <sam@x.org>, jo.smith@example.com, z@y.org', OWNER),
                         ["Sam Lee", "You", "another recipient"])

    def test_html_fallback(self):
        msg = {"payload": {"mimeType": "text/html", "body": {"data": b64("<p>Hi&amp;bye</p><script>x</script>")}}}
        text, files = fetch.body_and_attachments(msg)
        self.assertEqual(text.strip(), "Hi&bye")
        self.assertEqual(files, [])

    def test_to_thread(self):
        raw = {"id": "t1", "messages": [
            raw_message('"Sam Lee" <sam@x.org>', OWNER, cc="Pat <pat@x.org>",
                        subject="For jo.smith", body="Hi, ask jo.smith@example.com", files=["a.pdf"]),
            raw_message(f"Jo <{OWNER}>", "sam@x.org", body="Sure", ms="1790000100000"),
            raw_message(f"Jo <{OWNER}>", "sam@x.org", body="draft", labels=["DRAFT"]),
        ]}
        t = fetch.to_thread(raw, OWNER, self.redact, subject_only=False, structure_only=False)
        self.assertEqual(t["subject"], "For [your username]")
        self.assertEqual(len(t["messages"]), 2)  # draft dropped
        first, second = t["messages"]
        self.assertEqual(first["sender"], "Sam Lee <sam@x.org>")
        self.assertEqual((first["to"], first["cc"]), (["You"], ["Pat"]))
        self.assertEqual(first["body"], "Hi, ask [your address]")
        self.assertEqual(first["attachments"], ["a.pdf"])
        self.assertTrue(second["from_me"])
        self.assertEqual(second["sender"], "You")

    def test_subject_only_and_structure_only(self):
        raw = {"id": "t2", "messages": [raw_message("Shop <deals@shop.com>", OWNER, subject="Sale", files=["x.pdf"])]}
        t = fetch.to_thread(raw, OWNER, self.redact, subject_only=True, structure_only=False)
        self.assertEqual((t["subject"], t["messages"][0]["body"]), ("Sale", ""))
        t = fetch.to_thread(raw, OWNER, self.redact, subject_only=False, structure_only=True)
        self.assertEqual(t["subject"], "(subject withheld)")
        self.assertEqual(t["messages"][0]["body"], "")
        self.assertNotIn("attachments", t["messages"][0])


if __name__ == "__main__":
    unittest.main()
