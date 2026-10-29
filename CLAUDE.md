# CLAUDE.md

This folder is an email triage tool built on **Jev**, TypeSafe's judgment model. Jev answers typed
questions (Noul = yes/no, Choice, Score) about each email thread with calibrated probabilities.
Python code in `email_triage/` turns those answers into piles and a ranked report. The user is
probably not a developer, so explain what you change in plain language.

## Before any TypeSafe work

- Load the `typesafe:typesafe-ai` skill before designing, changing, reviewing or debugging anything
  that calls Jev. "ts", "ts skill", "TypeSafe skill" and "Jev skill" all mean this skill, and
  `/ts <request>` invokes it.
- The live docs are the source of truth: <https://docs.typesafe.ai/llms.txt>.

## How this tool is built (keep it this way)

- **Jev judges, code decides.** Questions in `email_triage/questions.py` ask for single,
  observable judgments. The `route()` truth table and `priority()` decide the pile and the order.
  Every combination of answers must have a defined pile, including a Noul between 0.3 and 0.7.
- **All question wording, criteria, thresholds and weights live in `questions.py`.**
- **State is named JSON fields** with only what a person would need. The inbox owner is "You".
- **Ask every question of every thread in one request** (speculative fan-out).
- **A failed API call is an error, never a "no".** Every request and response is logged under
  `private/runs/`.
- **No prompt gymnastics:** never add criteria that name a specific email, fit thresholds to a
  few cases, or assert exact probabilities in tests. Improve the state, split the question, or
  change the rules instead.
- After any change, run `py -3 -m unittest discover -s tests -t .` (Mac: `python3 ...`), then
  `--sample`, then a fresh date range of real mail. See `guide/07-test-honestly.md`.

## Privacy rules (always)

- The API key is in the `TYPESAFE_API_KEY` environment variable. Never print it, log it, write it
  to a file, or ask the user to paste it.
- Google credentials live in `~/.jev-gmail/` (`client_secret.json`, `token.json`). Never read
  them into the conversation, print them, or copy them into this folder.
- Real email lives only in `private/`, which is git-ignored. Never commit it. Never quote real
  email content, senders or subjects in code, tests, docs or commit messages. Describe results
  generically ("a payment reminder", "a personal thread").
- Ask the user before sending real email to the live API for the first time in a session, and
  say what will be sent. Gmail access is read-only; change nothing in the mailbox.
