"""Gmail follow-up triage: state, questions, and routing in one place.

Jev makes the judgments; the code below makes the decisions. Edit wording,
thresholds, and weights here only.

Sections:
  1. STATE      - what each thread looks like when it reaches Jev
  2. QUESTIONS  - one request per thread, all questions asked up front
  3. ROUTING    - thresholds, the pile truth table, and the priority score
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta

# =============================================================================
# 1. STATE
# =============================================================================
# One JSON object per thread with named fields. Messages you sent are labelled
# "You" so no question has to work out who the inbox owner is, and your own
# address is never sent. Facts code already knows (who wrote last, how long
# ago) are stated, not left for Jev to infer.

LAST_N_MESSAGES = 3
MAX_WORDS_PER_MESSAGE = 500

_QUOTE_HEADER = re.compile(r"^\s*On .+ wrote:\s*$", re.IGNORECASE)
_FORWARD_HEADER = re.compile(r"^-{2,}\s*(Original|Forwarded) Message\s*-{2,}", re.IGNORECASE)
_OUTLOOK_HEADER = re.compile(r"^\s*From:\s.+$")
# Links can carry private tokens (payment or login links), and no question needs
# them, so they never leave this machine. Markdown links keep their label.
_MD_LINK = re.compile(r"\[([^\]]*)\]\((?:https?://|www\.)[^)]*\)")
_URL = re.compile(r"(?:https?://|www\.)\S+")
# Invisible padding that marketing email uses to hide preview text.
_INVISIBLE = re.compile("[­͏​-‏⁠﻿]")
# Contact details in message text (signatures, your own messages) aren't needed
# by any question. Sender names and addresses stay in `sender`.
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_PHONE = re.compile(r"(?<![\w.])(?:\+\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}(?![\w])")


def clean_body(text: str) -> str:
    """Drop quoted replies, signatures, links and padding, then cap the length."""
    text = _INVISIBLE.sub("", text or "")
    text = _MD_LINK.sub(lambda m: m.group(1) or "[link]", text)
    text = _URL.sub("[link]", text)
    text = _EMAIL.sub("[email]", text)
    text = _PHONE.sub("[phone]", text)
    text = re.sub(r"[|#]{1,}\s*", " ", text)  # flatten markdown tables and headings
    kept = []
    for line in text.splitlines():
        if line.strip() == "--" or _QUOTE_HEADER.match(line) or _FORWARD_HEADER.match(line):
            break
        if kept and _OUTLOOK_HEADER.match(line) and not kept[-1].strip():
            break
        if line.lstrip().startswith(">"):
            continue
        kept.append(line.rstrip())
    words = " ".join(kept).split()
    if len(words) > MAX_WORDS_PER_MESSAGE:
        words = words[:MAX_WORDS_PER_MESSAGE] + ["[…message shortened]"]
    return " ".join(words)


def _sent_date(msg: dict) -> date:
    return datetime.fromisoformat(msg["date"].replace("Z", "+00:00")).date()


def _message_state(m: dict) -> dict:
    out = {
        "sender": "You" if m["from_me"] else m["sender"],
        "sent": _sent_date(m).isoformat(),
        "text": clean_body(m.get("body", "")),
    }
    for field in ("to", "cc"):  # recipient names; the fetch writes the inbox owner as "You"
        if m.get(field):
            out[field] = list(m[field])
    if m.get("attachments"):  # only when present; an empty list can read as a signal
        out["attachments"] = list(m["attachments"])
    return out


def _how_addressed(m: dict) -> str | None:
    """Where You appear on a message: "to", "cc", or "not listed" (bcc or a list)."""
    if "to" not in m and "cc" not in m:
        return None  # recipients weren't fetched; say nothing rather than guess
    if "You" in m.get("to", []):
        return "to"
    return "cc" if "You" in m.get("cc", []) else "not listed"


def build_state(thread: dict, today: date) -> dict:
    """Turn one fetched thread into the state for a follow-up request."""
    messages = thread["messages"]
    recent = messages[-LAST_N_MESSAGES:]
    latest = messages[-1]
    return {
        "today": today.isoformat(),
        "thread": {
            "subject": thread.get("subject") or "(no subject)",
            "earlier_messages_not_shown": len(messages) - len(recent),
            "messages": [_message_state(m) for m in recent],
        },
        "facts": _facts(messages, today),
    }


def _facts(messages: list[dict], today: date) -> dict:
    latest = messages[-1]
    facts = {
        "latest_message_is_from_you": latest["from_me"],
        "days_since_latest_message": (today - _sent_date(latest)).days,
    }
    latest_other = next((m for m in reversed(messages) if not m["from_me"]), None)
    how = _how_addressed(latest_other) if latest_other else None
    if how:
        facts["you_are_on_latest_message_from_others_as"] = how
    return facts


# --- Deadline date candidates (select instead of generate) -------------------
# Code finds every written date in the thread; Jev only picks which one is the
# deadline. Code then compares that date with today.

MAX_DATE_CANDIDATES = 8
_MONTHS = {m: i for i, m in enumerate(
    "jan feb mar apr may jun jul aug sep oct nov dec".split(), start=1)}
_MON = r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?"
_DATE_PATTERNS = [
    # October 28, 2026 / Oct 30 / December 3rd
    (re.compile(rf"\b{_MON}\s+(\d{{1,2}})(?:st|nd|rd|th)?\b(?:,?\s+(\d{{4}}))?", re.I), ("mon", "day", "year")),
    # 30th October 2026 / 5 Mar 2027
    (re.compile(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+{_MON}\b(?:,?\s+(\d{{4}}))?", re.I), ("day", "mon", "year")),
    # 2026-10-28
    (re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b"), ("year", "month", "day")),
    # 10/28/2026
    (re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b"), ("month", "day", "year")),
]


def _to_date(parts: dict, ref: date) -> date | None:
    month = parts.get("month") or _MONTHS.get(parts.get("mon", "")[:3].lower())
    try:
        year = int(parts["year"]) if parts.get("year") else ref.year
        found = date(year, int(month), int(parts["day"]))
    except (TypeError, ValueError):
        return None
    if not parts.get("year") and found < ref - timedelta(days=60):
        found = found.replace(year=found.year + 1)  # "Jan 5" written in December
    return found


def date_candidates(state: dict) -> dict[str, str]:
    """Map ISO date -> where it appears, for every date written in the thread."""
    sources = [("subject", state["thread"]["subject"], date.fromisoformat(state["today"]))]
    sources += [
        (f"message from {m['sender']} on {m['sent']}", m["text"], date.fromisoformat(m["sent"]))
        for m in state["thread"]["messages"]
    ]
    found: dict[str, str] = {}
    for where, text, ref in sources:
        for pattern, names in _DATE_PATTERNS:
            for match in pattern.finditer(text):
                d = _to_date(dict(zip(names, match.groups())), ref)
                if d and d.isoformat() not in found:
                    snippet = text[max(0, match.start() - 50): match.end() + 30].strip()
                    found[d.isoformat()] = f'Written as "{match.group(0)}" in the {where}: "…{snippet}…"'
    return dict(list(found.items())[:MAX_DATE_CANDIDATES])


# =============================================================================
# 2. QUESTIONS
# =============================================================================
# Every question is asked of every thread (speculative fan-out); code reads
# only the answers that matter for that thread's row in the truth table.

QUESTIONS = {
    "asks_you": {
        "type": "noul",
        "instructions": (
            "In `thread.messages`, does the most recent message from someone other "
            "than You ask You to reply, decide, or do something?"
        ),
        "criteria": {
            "true": (
                "The sender asks You a question, asks You for a decision, or asks You "
                "to take an action, and is waiting on You."
            ),
            "false": (
                "The message only shares information, thanks You, confirms something, "
                "or makes a general announcement with nothing asked of You."
            ),
        },
    },
    "you_await_reply": {
        "type": "noul",
        "instructions": (
            "In `thread.messages`, does the most recent message from You ask someone "
            "for something that nobody has answered yet?"
        ),
        "criteria": {
            "true": "You asked a question or requested something, and no one has answered since.",
            "false": "Your message answers, thanks, or confirms, and leaves nothing outstanding.",
        },
    },
    "open_issue": {
        "type": "noul",
        "instructions": (
            "Does `thread` describe a problem of Yours that is still unresolved at the "
            "end of the thread?"
        ),
        "criteria": {
            "true": (
                "Something of Yours is lost, broken, delayed, missing, or disputed, and "
                "the last message does not say it has been fixed or settled."
            ),
            "false": (
                "There is no problem, or the thread ends with the problem fixed, "
                "delivered, refunded, or otherwise settled."
            ),
        },
    },
    "has_deadline": {
        "type": "noul",
        "instructions": (
            "Does `thread` mention a date or time by which You are expected to respond or act?"
        ),
        "criteria": {
            "true": "A due date, meeting time, or 'by Friday'-style deadline applies to You.",
            "false": "No date or time is attached to anything You need to do.",
        },
    },
    "written_personally": {
        "type": "noul",
        "instructions": (
            "Was the most recent message from someone other than You written by a "
            "person directly to You?"
        ),
        "criteria": {
            "true": "A person wrote it to You or to a small group that includes You.",
            "false": (
                "It is a newsletter, mass mailing, automated notification, or system "
                "message sent to many recipients. This includes marketing written to "
                "look personal, with a first-name greeting and a staff member's name "
                "and title, that promotes an offer or a deadline to enroll or buy."
            ),
        },
    },
    "looks_suspicious": {
        "type": "noul",
        "instructions": (
            "Does the most recent message from someone other than You look like "
            "phishing or a scam?"
        ),
        "criteria": {
            "true": (
                "It comes from an unknown or random-looking address and pushes an "
                "unexpected attachment or link, asks for money, passwords, or personal "
                "details, or has content with no connection to You."
            ),
            "false": (
                "It is from a person You know or an organization You actually deal with, "
                "about something that concerns You, even if it is marketing."
            ),
        },
    },
    "sender_role": {
        "type": "choice",
        "instructions": (
            "Who is the sender of the most recent message from someone other than You, "
            "in relation to You?"
        ),
        "criteria": {
            "supervisor_or_leader": "Your manager, a director, or someone You report to.",
            "colleague": "A coworker or collaborator on shared work.",
            "student": "A student You teach, advise, or support.",
            "client_or_patron": "Someone You provide a service to, such as a library patron or client.",
            "service_provider": (
                "A business or professional You are a customer of, writing to You "
                "personally about Your order, repair, appointment, or account."
            ),
            "family_or_friend": "A personal contact outside work.",
            "vendor_or_sales": "A company sending You promotions, sales offers, or marketing.",
            "stranger": "Someone with no prior relationship writing to You for the first time.",
        },
    },
}

DEADLINE_DATE_QUESTION = (
    "Which date in `thread` is the deadline by which You are expected to respond or act?"
)


def build_request(state: dict, model: str = "jev-latest") -> dict:
    questions = dict(QUESTIONS)
    candidates = date_candidates(state)
    if candidates:  # asked only when code found dates; has_deadline covers "none fit"
        questions["deadline_date"] = {
            "type": "choice",
            "instructions": DEADLINE_DATE_QUESTION,
            "criteria": candidates,
        }
    return {"model": model, "state": state, "questions": questions}


# =============================================================================
# 3. ROUTING
# =============================================================================

YES = 0.70  # Noul at or above this reads as yes
NO = 0.30   # Noul below this reads as no; between YES and NO is unsettled

# Bulk mail with an ask and a deadline goes to Check only when it is probably
# not a promotion (P(vendor_or_sales) below this).
MAX_PROMOTION_P_FOR_CHECK = 0.5

# How much each sender role raises priority, 0-1. Combined using Jev's
# probabilities over the roles, so an uncertain role gives a middling value.
SENDER_IMPORTANCE = {
    "supervisor_or_leader": 1.0,
    "student": 0.8,
    "client_or_patron": 0.8,
    "colleague": 0.7,
    "service_provider": 0.6,
    "family_or_friend": 0.6,
    "stranger": 0.3,
    "vendor_or_sales": 0.2,
}

# Priority weights (sum to 1). The "ask" input depends on the pile: asks_you
# for Reply needed, you_await_reply for Waiting on them, open_issue for Open issue.
W_ASK = 0.35
W_DEADLINE = 0.25
W_DAYS_WAITING = 0.20
W_SENDER = 0.20
DAYS_FOR_FULL_WEIGHT = 7  # waiting this long or longer counts fully

# How pressing a deadline is, by days until it (negative = overdue).
DEADLINE_URGENCY_UNKNOWN_DATE = 0.5
DEADLINE_URGENCY = [(2, 1.0), (7, 0.7), (None, 0.4)]  # (max days until, weight); overdue = 1.0

PILES = ("reply_needed", "waiting_on_them", "open_issue", "check", "suspicious", "no_action")


def _band(p: float) -> str:
    return "yes" if p >= YES else "no" if p < NO else "unsettled"


def deadline(state: dict, answers: dict) -> tuple[date | None, int | None]:
    """(deadline date, days until it) unless Jev says there is no deadline, or no date was picked."""
    if _band(answers["has_deadline"]["noul"]) == "no" or "deadline_date" not in answers:
        return None, None
    due = date.fromisoformat(answers["deadline_date"]["choice"])
    return due, (due - date.fromisoformat(state["today"])).days


def route(state: dict, answers: dict) -> tuple[str, str]:
    """Return (pile, reason) for one thread. The full truth table:

    latest from You | you_await_reply | open_issue -> pile
    ----------------+-----------------+------------------------
    yes             | yes             | any        -> waiting_on_them
    yes             | unsettled       | any        -> check
    yes             | no              | yes        -> open_issue
    yes             | no              | other      -> no_action

    latest from them | written_personally | asks_you  | open_issue -> pile
    -----------------+--------------------+-----------+------------------------
    yes              | looks_suspicious = yes                         -> suspicious (checked first)
    yes              | no                 | yes + deadline yes, not a promotion -> check
    yes              | no                 | yes + deadline yes, promotion       -> no_action
    yes              | no                 | yes, no deadline       -> no_action (generic call to action)
    yes              | no                 | other     | any        -> no_action
    yes              | yes                | yes       | any        -> reply_needed
    yes              | unsettled          | yes       | any        -> check  (maybe automated)
    yes              | yes / unsettled    | unsettled | any        -> check
    yes              | yes / unsettled    | no        | yes        -> open_issue
    yes              | yes / unsettled    | no        | other      -> no_action

    A date that has passed is noted in the reason. If it is what a Reply needed
    thread hinges on, the ask may be stale, so the thread moves to Check.
    """
    pile, why = _route(state, answers)
    _, days = deadline(state, answers)
    if days is not None and days < 0:
        why = f"{why}; its date passed {-days} day(s) ago"
        if pile == "reply_needed":
            pile, why = "check", f"{why}, so the ask may be stale"
    return pile, why


def _route(state: dict, answers: dict) -> tuple[str, str]:
    issue = answers["open_issue"]["noul"]
    if state["facts"]["latest_message_is_from_you"]:
        p = answers["you_await_reply"]["noul"]
        band = _band(p)
        if band == "yes":
            return "waiting_on_them", f"your last message is waiting on a reply ({p:.2f})"
        if band == "unsettled":
            return "check", f"unclear if you're waiting on a reply ({p:.2f})"
        if _band(issue) == "yes":
            return "open_issue", f"unresolved problem of yours ({issue:.2f})"
        return "no_action", f"your last message closed the loop ({p:.2f})"

    suspicious = answers["looks_suspicious"]["noul"]
    if _band(suspicious) == "yes":
        return "suspicious", f"looks like phishing or a scam ({suspicious:.2f}); don't open attachments or links"
    ask = answers["asks_you"]["noul"]
    personal = answers["written_personally"]["noul"]
    if _band(personal) == "no":
        deadline_p = answers["has_deadline"]["noul"]
        promo = answers["sender_role"]["probabilities"].get("vendor_or_sales", 0.0)
        if _band(ask) == "yes" and _band(deadline_p) == "yes":
            if promo >= MAX_PROMOTION_P_FOR_CHECK:
                return "no_action", f"promotion with a deadline ({promo:.2f} vendor or sales)"
            return "check", f"bulk or automated, asks something of you by a deadline ({ask:.2f})"
        if _band(ask) == "yes":
            return "no_action", f"bulk call to action with no deadline ({ask:.2f})"
        return "no_action", f"bulk or automated ({personal:.2f} personal)"
    band = _band(ask)
    if band == "yes" and _band(personal) == "unsettled":
        return "check", f"asks you to act, but may be automated ({personal:.2f} personal)"
    if band == "yes":
        return "reply_needed", f"asks you to reply or act ({ask:.2f})"
    if band == "unsettled":
        return "check", f"unclear if anything is asked of you ({ask:.2f})"
    if _band(issue) == "yes":
        return "open_issue", f"unresolved problem of yours ({issue:.2f})"
    return "no_action", f"nothing asked of you ({ask:.2f})"


def _deadline_urgency(days: int | None) -> float:
    if days is None:
        return DEADLINE_URGENCY_UNKNOWN_DATE
    if days < 0:
        return 1.0
    return next(w for limit, w in DEADLINE_URGENCY if limit is None or days <= limit)


def priority(state: dict, answers: dict, pile: str) -> float:
    """Weighted 0-100 priority score; higher means follow up sooner."""
    ask_key = {"waiting_on_them": "you_await_reply", "open_issue": "open_issue"}.get(pile)
    if ask_key is None:
        ask_key = "you_await_reply" if state["facts"]["latest_message_is_from_you"] else "asks_you"
    ask = answers[ask_key]["noul"]
    _, days = deadline(state, answers)
    deadline_term = answers["has_deadline"]["noul"] * _deadline_urgency(days)
    waited = min(state["facts"]["days_since_latest_message"] / DAYS_FOR_FULL_WEIGHT, 1.0)
    probs = answers["sender_role"]["probabilities"]
    sender = sum(SENDER_IMPORTANCE.get(role, 0.0) * p for role, p in probs.items())
    score = W_ASK * ask + W_DEADLINE * deadline_term + W_DAYS_WAITING * waited + W_SENDER * sender
    return round(100 * score, 1)
