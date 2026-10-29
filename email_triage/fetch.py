"""Fetch Gmail threads into private/threads.json, read-only.

Usage (Windows: `py -3 -m ...`; Mac: `python3 -m ...`):
    py -3 -m email_triage.fetch [--newer 14] [--older 0] [--out private/threads.json]

The first run opens a browser to sign in. The OAuth client and token live in
~/.jev-gmail/, outside the repo. Only the gmail.readonly scope is requested.

What gets written (and later sent to Jev, after run.py's cleaning):
- recipients as names; the inbox owner is "You", unnamed people "another recipient"
- the inbox owner's address and username are removed from subjects, text and
  attachment names
- with --subject-only-repeats N, sender domains with N+ threads in the set get
  subject only (off by default: it hid a real payment reminder from a sender
  that sent several)
- thread IDs listed in private/structure_only.txt: senders, recipients and dates
  only, no subject text or bodies (for confidential or third-party material)
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import re
from collections import Counter
from datetime import datetime, timezone
from email.utils import getaddresses, parseaddr
from pathlib import Path

CONFIG_DIR = Path.home() / ".jev-gmail"
CLIENT_FILE = CONFIG_DIR / "client_secret.json"
TOKEN_FILE = CONFIG_DIR / "token.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Same filter used for the hand-fetched test sets.
EXCLUDE = (
    "-from:(noreply OR no-reply OR donotreply OR notifications OR notification OR newsletter "
    "OR news OR info OR marketing OR hello OR email OR mail OR support OR customersupport "
    "OR invoice OR billing OR system OR media OR team OR updates OR dailybriefing) -unsubscribe"
)
STRUCTURE_ONLY_FILE = Path("private/structure_only.txt")


def gmail_service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    if not CLIENT_FILE.exists():
        raise SystemExit(f"Missing {CLIENT_FILE}. See guide/04-connect-gmail.md.")
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES) if TOKEN_FILE.exists() else None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = InstalledAppFlow.from_client_secrets_file(str(CLIENT_FILE), SCOPES).run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def _headers(msg: dict) -> dict:
    return {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}


def _decode(data: str) -> str:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")


def _html_to_text(markup: str) -> str:
    markup = re.sub(r"(?is)<(script|style).*?</\1>", " ", markup)
    markup = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>", "\n", markup)
    return html.unescape(re.sub(r"<[^>]+>", " ", markup))


def _walk(part: dict):
    yield part
    for sub in part.get("parts", []) or []:
        yield from _walk(sub)


def body_and_attachments(msg: dict) -> tuple[str, list[str]]:
    plain, markup, files = [], [], []
    for part in _walk(msg["payload"]):
        if part.get("filename"):
            files.append(part["filename"])
            continue
        data = part.get("body", {}).get("data")
        if not data:
            continue
        if part.get("mimeType") == "text/plain":
            plain.append(_decode(data))
        elif part.get("mimeType") == "text/html":
            markup.append(_decode(data))
    text = "\n".join(plain) if plain else "\n".join(_html_to_text(m) for m in markup)
    return text, files


class Redactor:
    """Removes the inbox owner's address and username from text."""

    def __init__(self, address: str):
        self.address = address.lower()
        user = re.escape(self.address.split("@")[0])
        self._addr = re.compile(re.escape(self.address), re.I)
        # Letters and digits bound the username; "_" and "." don't (as in "user_123.pptx").
        self._user = re.compile(rf"(?<![A-Za-z0-9]){user}(?![A-Za-z0-9])", re.I) if len(user) >= 4 else None

    def __call__(self, text: str) -> str:
        text = self._addr.sub("[your address]", text or "")
        return self._user.sub("[your username]", text) if self._user else text


def _names(header: str, owner: str) -> list[str]:
    out = []
    for name, addr in getaddresses([header or ""]):
        if not addr:
            continue
        out.append("You" if addr.lower() == owner else (name.strip() or "another recipient"))
    return out


def _sender(header: str, owner: str) -> str:
    name, addr = parseaddr(header or "")
    if addr.lower() == owner:
        return "You"
    return f"{name} <{addr}>" if name else addr


def to_thread(raw: dict, owner: str, redact: Redactor, subject_only: bool, structure_only: bool) -> dict:
    messages = []
    subject = ""
    for msg in raw["messages"]:
        if "DRAFT" in msg.get("labelIds", []):
            continue
        h = _headers(msg)
        subject = subject or h.get("subject", "")
        sender = _sender(h.get("from", ""), owner)
        text, files = body_and_attachments(msg)
        entry = {
            "sender": sender,
            "from_me": sender == "You",
            "date": datetime.fromtimestamp(int(msg["internalDate"]) / 1000, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "body": "" if (subject_only or structure_only) else redact(text),
            "to": _names(h.get("to", ""), owner),
            "cc": _names(h.get("cc", ""), owner),
        }
        if files and not structure_only:
            entry["attachments"] = [redact(f) for f in files]
        messages.append(entry)
    view = f"https://mail.google.com/mail/#all/{raw['id']}"
    return {
        "id": raw["id"],
        "subject": "(subject withheld)" if structure_only else redact(subject),
        "view_url": view,
        "messages": messages,
    }


def _latest_other_domain(thread: dict) -> str:
    other = next((m for m in reversed(thread["messages"]) if not m["from_me"]), None)
    return parseaddr(other["sender"])[1].split("@")[-1].lower() if other else ""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--newer", type=int, default=14, help="newer than N days")
    ap.add_argument("--older", type=int, default=0, help="older than N days (0 = no limit)")
    ap.add_argument("--max", type=int, default=150, help="max threads to fetch")
    ap.add_argument("--out", default="private/threads.json")
    ap.add_argument("--subject-only-repeats", type=int, metavar="N",
                    help="send only the subject for sender domains with N+ threads (off by default)")
    args = ap.parse_args()

    svc = gmail_service()
    owner = svc.users().getProfile(userId="me").execute()["emailAddress"].lower()
    redact = Redactor(owner)
    query = f"in:inbox newer_than:{args.newer}d " + (f"older_than:{args.older}d " if args.older else "") + EXCLUDE

    ids, token = [], None
    while len(ids) < args.max:
        page = svc.users().threads().list(userId="me", q=query, pageToken=token, maxResults=100).execute()
        ids += [t["id"] for t in page.get("threads", [])]
        token = page.get("nextPageToken")
        if not token:
            break
    ids = ids[: args.max]

    structure_only = set()
    if STRUCTURE_ONLY_FILE.exists():
        structure_only = {line.split("#")[0].strip() for line in STRUCTURE_ONLY_FILE.read_text().splitlines()} - {""}

    raws = [svc.users().threads().get(userId="me", id=i, format="full").execute() for i in ids]
    drafts = [to_thread(r, owner, redact, False, r["id"] in structure_only) for r in raws]
    domains = Counter(_latest_other_domain(t) for t in drafts)
    limit = args.subject_only_repeats
    repeat = {d for d, n in domains.items() if d and limit and n >= limit}
    threads = [
        to_thread(r, owner, redact, _latest_other_domain(t) in repeat, r["id"] in structure_only)
        if _latest_other_domain(t) in repeat else t
        for r, t in zip(raws, drafts)
    ]
    threads = [t for t in threads if t["messages"]]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(threads, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(threads)} threads written to {out} "
          f"({sum(1 for t in threads if t['id'] in structure_only)} structure-only, "
          f"{len(repeat)} repeat sender domains set to subject only).")


if __name__ == "__main__":
    main()
