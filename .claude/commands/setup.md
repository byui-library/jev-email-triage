---
description: Guided setup. Checks each step on this computer, then walks through the next one.
argument-hint: "[optional: step to jump to, e.g. gmail]"
---

You are guiding a non-developer through setting up this project, one step at a time. The full
written guide is in `guide/` (chapters 02 to 05); use it as the source for exact wording, and
`guide/09-troubleshooting.md` when something goes wrong. Follow `CLAUDE.md`, especially its
privacy rules.

## How to run this

1. **Check before telling.** Detect the operating system first (Windows or Mac). Then, for the
   steps below in order, run the check quietly. Skip steps that pass, with a one-line "✓ done"
   for each, so the user sees their progress. Start guiding at the first step that fails.
   If the user named a step ($ARGUMENTS), start there, but still run the checks for earlier
   steps and mention any that fail.
2. **One step at a time.** Explain the step in plain language, with the exact text to click or
   type. Then **stop and wait** for the user to say it's done. Then re-run that step's check to
   confirm before moving on. If the check fails, help fix it, using the troubleshooting chapter.
3. **Do what you can, ask what you must.** You may run read-only checks yourself. **Ask before**
   anything that installs software, sends data to Jev, reads Gmail, or renames files, and say
   in one sentence what it does and what it costs.
4. **Never** ask for, print or echo the API key; never read the contents of
   `~/.jev-gmail/client_secret.json` or `token.json`; never quote real email content, senders
   or subjects. Report Gmail results only as counts and generic descriptions.
5. If a step needs a **restart** (a new API key, or a newly installed plugin), say so clearly,
   and tell the user to type `/setup` again afterwards. You'll pick up where they left off.
6. Mac steps haven't been tested by the project yet. If something differs, help, and suggest
   they report it at https://github.com/byui-library/jev-email-triage/issues.

In commands below, `PY` means `py -3` on Windows and `python3` on a Mac.

## Steps and their checks

**1. Python 3.10+**
Check: `PY --version` prints 3.10 or higher.
If missing: guide/02-install.md, step 2.

**2. TypeSafe skill**
Check: the `typesafe:typesafe-ai` skill is available to you in this session.
If missing: have the user run, in a separate terminal,
`claude plugin marketplace add typesafe-ai/skills` and then
`claude plugin install typesafe@typesafe-ai`, then restart Claude Code and type `/setup`.

**3. Jev API key stored**
Check, without printing the value: `TYPESAFE_API_KEY` is set in this session. On Windows, also
compare it with the stored user value
(`[Environment]::GetEnvironmentVariable('TYPESAFE_API_KEY','User')`) and report only whether they
match. A mismatch means the user needs to restart.
If missing: walk through guide/02-install.md, step 4, one sub-step at a time. Billing first, then
the key at https://console.typesafe.ai/keys, then storing it (PowerShell on Windows, Keychain on a
Mac). The user does this **in their own terminal, not in this chat.** Then they restart and type
`/setup` again.

**4. Jev key works**
Check: a `GET https://api.typesafe.ai/v1/models` request with the key as a Bearer token returns
200. It's free, and sends no email data. Do this with a short Python one-liner (urllib) that
reads the key from the environment and prints only the HTTP status.
If 401: see "HTTP 401" in guide/09-troubleshooting.md (usually: set up billing, create a new key).

**5. Sample run**
Check: a file matching `private/runs/*/followup-sample-*.md` exists.
To do (ask first; fictional emails, about $0.001): run `PY -m email_triage.run --sample`. Then
explain the result in plain language: how many threads, how long, the cost, the "Sample check"
line, and why the usual misses land in Check (guide/03-try-sample.md).

**6. Google Cloud set up**
Check: `~/.jev-gmail/client_secret.json` exists. Check existence only; don't open it.
If a file named `client_secret_*.json` is there instead, offer to rename it.
If missing: walk through guide/04-connect-gmail.md, steps 1 to 3, **one sub-step per message**:
create a project; enable the Gmail API; configure the sign-in screen; **add yourself as a test
user** (stress this, since skipping it causes Error 403); create a **Desktop app** client, leaving
"AI-powered agent" unchecked; download the JSON; make the `.jev-gmail` folder; move and rename
the file.

**7. Google libraries**
Check: `PY -c "import googleapiclient, google_auth_oauthlib"` succeeds.
To do (ask first): `PY -m pip install --user -r requirements.txt`.

**8. Gmail connected**
Check: `~/.jev-gmail/token.json` exists, and `private/threads.json` exists.
To do (ask first; read-only, the last 14 days): run `PY -m email_triage.fetch --newer 14`. Tell
the user a browser will open: choose their account, click **Continue** past "Google hasn't
verified this app", and allow read-only access. Report only the thread count.

**9. First real run**
Check: a report matching `private/runs/*/followup-20*.md` exists. Sample reports are named
`followup-sample-*` instead.
To do:
- Run `PY -m email_triage.run --dry-run`.
- Scan the new payload files for `http`, `www.`, the user's own address, and phone-number
  patterns. Report only whether any were found, and never show matches that contain email text.
- Tell the user what will be sent to TypeSafe (guide/08-privacy.md, in two sentences), and the
  estimated cost.
- **Ask**, then run `PY -m email_triage.run`. Summarize the pile counts only.
- Tell them to open the report themselves (the path is printed), and how to read it
  (guide/05-run-daily.md).

**10. Daily use**
Explain the double-click script: `run-email-triage.cmd` on Windows, `run-email-triage.command` on a
Mac (right-click → Open the first time). Also mention the desktop shortcut tip, and suggest
guide/06-customize.md as the next thing to try. Congratulate them; setup is complete.
