"""Rank email threads that may need follow-up, using Jev.

Usage (Windows: `py -3 -m ...`; Mac: `python3 -m ...`):
    py -3 -m email_triage.run --sample            # try it on made-up emails
    py -3 -m email_triage.run                     # your fetched Gmail threads
    py -3 -m email_triage.run --dry-run           # build requests, send nothing

Input is a JSON list of threads (see guide/03 and guide/04). Every request and
response is saved under private/runs/<timestamp>/ so any result can be rerun.
A failed call is reported as an error, never as a "no".
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from pathlib import Path

from . import questions as q

API_URL = "https://api.typesafe.ai/v1/systemone"
# From https://docs.typesafe.ai/go/models.md (checked 2026-10-29); output tokens are free.
USD_PER_INPUT_TOKEN = 0.042 / 1_000_000
WORKERS = 8

# The made-up sample emails are written as if "today" were this date, so their
# deadlines and waiting times stay meaningful no matter when you run them.
SAMPLE_FILE = Path(__file__).resolve().parent.parent / "sample_data" / "sample_threads.json"
SAMPLE_TODAY = date(2026, 10, 29)

PILE_TITLES = {
    "reply_needed": "Reply needed",
    "waiting_on_them": "Waiting on them",
    "open_issue": "Open issue to track",
    "check": "Check",
    "suspicious": "Possible phishing or spam",
    "no_action": "No action",
}


class JevError(RuntimeError):
    pass


class SpendCapReached(RuntimeError):
    pass


def api_key() -> str:
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        sys.exit("TYPESAFE_API_KEY is not set. See guide/02-install.md (step 4), then open a new terminal.")
    return key


def ask_jev(payload: dict, key: str) -> dict:
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        raise JevError(f"HTTP {e.code}: {e.read().decode(errors='replace')[:300]}") from e
    except urllib.error.URLError as e:
        raise JevError(f"network error: {e.reason}") from e


class Budget:
    """Stops new requests once estimated spend would pass the cap."""

    def __init__(self, cap_usd: float):
        self.cap = cap_usd
        self.spent = 0.0
        self._lock = threading.Lock()

    def reserve(self, payload: dict) -> float:
        est = len(json.dumps(payload)) / 3 * USD_PER_INPUT_TOKEN  # generous chars-per-token guess
        with self._lock:
            if self.spent + est > self.cap:
                raise SpendCapReached(f"cap ${self.cap:.2f} reached (spent ~${self.spent:.5f})")
            self.spent += est
        return est

    def settle(self, est: float, input_tokens: int) -> None:
        with self._lock:
            self.spent += input_tokens * USD_PER_INPUT_TOKEN - est


def is_automated(thread: dict) -> bool:
    """Code-level filter for obvious automated senders, before anything is sent."""
    latest_other = next((m for m in reversed(thread["messages"]) if not m["from_me"]), None)
    if latest_other is None:
        return False
    sender = latest_other["sender"].lower()
    return any(t in sender for t in ("no-reply", "noreply", "donotreply", "do-not-reply", "mailer-daemon"))


def process(thread: dict, today: date, key: str, budget: Budget, run_dir: Path) -> dict:
    state = q.build_state(thread, today)
    payload = q.build_request(state)
    row = {"thread": thread, "state": state}
    log = {"request": payload}
    try:
        est = budget.reserve(payload)
        started = time.perf_counter()
        resp = ask_jev(payload, key)
        row["seconds"] = time.perf_counter() - started
        budget.settle(est, resp["usage"]["input_tokens"])
        log["response"] = resp
        answers = resp["answers"]
        row["answers"] = answers
        row["pile"], row["reason"] = q.route(state, answers)
        row["priority"] = q.priority(state, answers, row["pile"])
        row["tokens"] = resp["usage"]["input_tokens"]
    except (JevError, SpendCapReached, KeyError) as e:
        row["error"] = f"{type(e).__name__}: {e}"
        log["error"] = row["error"]
    (run_dir / "payloads" / f"{thread['id']}.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    return row


def _md(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def _deadline_cell(row: dict) -> str:
    due, days = q.deadline(row["state"], row["answers"])
    if due is None:
        p = row["answers"]["has_deadline"]["noul"]
        return "date unclear" if p >= q.YES else "—"
    if days < 0:
        return f"**overdue** ({due:%b %d})"
    return f"{due:%b %d} ({days}d)"


def write_report(rows: list[dict], skipped: list[dict], today: date, path: Path, elapsed: float, spent: float) -> None:
    ok = [r for r in rows if "error" not in r]
    errors = [r for r in rows if "error" in r]
    lines = [
        f"# Gmail follow-up — {today.isoformat()}",
        "",
        f"{len(rows)} threads sent to Jev in {elapsed:.1f}s, ~${spent:.5f}. "
        f"{len(skipped)} skipped as automated. {len(errors)} errors.",
        "",
    ]
    for pile in q.PILES:
        pile_rows = sorted((r for r in ok if r["pile"] == pile), key=lambda r: -r["priority"])
        lines += [f"## {PILE_TITLES[pile]} ({len(pile_rows)})", ""]
        if not pile_rows:
            lines += ["_None._", ""]
            continue
        lines += ["| Pri | Subject | From | Days | Deadline | Why |", "| --- | --- | --- | --- | --- | --- |"]
        for r in pile_rows:
            t = r["thread"]
            other = next((m for m in reversed(t["messages"]) if not m["from_me"]), t["messages"][-1])
            subject = f"[{_md(t.get('subject') or '(no subject)')}]({t['view_url']})" if t.get("view_url") else _md(t.get("subject"))
            lines.append(
                f"| {r['priority']} | {subject} | {_md(other['sender'])} "
                f"| {r['state']['facts']['days_since_latest_message']} "
                f"| {_deadline_cell(r)} | {_md(r['reason'])} |"
            )
        lines.append("")
    if errors:
        lines += ["## Errors (not routed)", ""]
        lines += [f"- {_md(r['thread'].get('subject'))}: {_md(r['error'])}" for r in errors]
        lines.append("")
    if skipped:
        lines += ["## Skipped as automated", ""]
        lines += [f"- {_md(t.get('subject'))}" for t in skipped]
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", default="private/threads.json")
    ap.add_argument("--cap", type=float, default=0.10, help="max estimated spend in USD")
    ap.add_argument("--limit", type=int, help="only send the first N threads")
    ap.add_argument("--thread", help="only send the thread with this Gmail ID")
    ap.add_argument("--dry-run", action="store_true", help="build and save requests; send nothing")
    ap.add_argument("--sample", action="store_true", help="use the made-up emails in sample_data/")
    ap.add_argument("--today", type=date.fromisoformat, help="treat this date (YYYY-MM-DD) as today")
    args = ap.parse_args()

    source = SAMPLE_FILE if args.sample else Path(args.input)
    if not source.exists():
        sys.exit(f"{source} not found. Fetch your Gmail first (guide/04-connect-gmail.md) or try --sample.")
    threads = json.loads(source.read_text(encoding="utf-8"))
    today = args.today or (SAMPLE_TODAY if args.sample else date.today())
    skipped = [t for t in threads if is_automated(t)]
    todo = [t for t in threads if not is_automated(t) and args.thread in (None, t["id"])][: args.limit]

    run_dir = Path("private/runs") / datetime.now().strftime("%Y%m%d-%H%M%S")
    (run_dir / "payloads").mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        for t in todo:
            payload = q.build_request(q.build_state(t, today))
            (run_dir / "payloads" / f"{t['id']}.json").write_text(json.dumps({"request": payload}, indent=2), encoding="utf-8")
        print(f"Dry run: {len(todo)} requests saved to {run_dir / 'payloads'}; {len(skipped)} skipped as automated.")
        return

    key = api_key()
    budget = Budget(args.cap)
    started = time.perf_counter()
    with ThreadPoolExecutor(WORKERS) as pool:
        rows = list(pool.map(lambda t: process(t, today, key, budget, run_dir), todo))
    elapsed = time.perf_counter() - started

    report = run_dir / f"followup-{'sample-' if args.sample else ''}{today.isoformat()}.md"
    write_report(rows, skipped, today, report, elapsed, budget.spent)
    errors = sum("error" in r for r in rows)
    print(f"{len(rows)} threads in {elapsed:.1f}s, ~${budget.spent:.5f}, {errors} errors. Report: {report}")

    # The sample emails carry the pile a person would expect; show how Jev + the rules did.
    graded = [r for r in rows if "pile" in r and r["thread"].get("expected")]
    if graded:
        misses = [r for r in graded if r["pile"] != r["thread"]["expected"]]
        print(f"Sample check: {len(graded) - len(misses)} of {len(graded)} landed in the expected pile.")
        for r in misses:
            print(f"  - {r['thread']['subject']}: expected {r['thread']['expected']}, got {r['pile']} ({r['reason']})")


if __name__ == "__main__":
    main()
