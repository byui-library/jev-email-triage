# Jev + Claude: sort your email by what needs follow-up

A step-by-step guide to setting up **Jev**, TypeSafe's *judgment model*, with **Claude Code**, and to
using them together to build a real tool: a read-only email assistant that ranks the last two weeks
of your Gmail into piles such as **Reply needed**, **Waiting on them** and **Possible phishing**.

It's written for people who are comfortable following instructions but don't write code. Claude
does the coding. You make the decisions.

> **Status:** tested on Windows with Gmail and Claude Code. The Mac steps are written but not yet
> tested. Outlook/Microsoft 365 and Codex versions are planned.

## What you'll end up with

- A double-click script that reads your Gmail (read-only) and opens a ranked report like this:

  | Pile | What it means |
  | --- | --- |
  | **Reply needed** | Someone wrote to you personally and is waiting on you |
  | **Waiting on them** | You asked for something and nobody has answered |
  | **Open issue to track** | No one owes a reply, but a problem of yours isn't settled (for example, a lost package) |
  | **Check** | Jev wasn't sure, or an automated email has a real deadline |
  | **Possible phishing or spam** | Looks like a scam; don't open its links or attachments |
  | **No action** | Newsletters, receipts, marketing and finished conversations |

- A clear understanding of what Jev does that chat models like Claude don't, and how to combine them.
- A starting point you can customize, by asking Claude, for any "sort and prioritize" task.

A typical run judges 30–50 emails in about a second, for **a fraction of a cent**.

## Prefer to be guided?

Let an AI walk you through setup one step at a time, waiting for you to finish each step:

1. **Before installing anything:** copy the prompt in [SETUP-PROMPT.md](SETUP-PROMPT.md) into a
   chat with an AI assistant, such as Claude at [claude.ai](https://claude.ai). It walks you
   through installing Python and Claude Code.
2. **Once Claude Code is installed:** open a terminal in this folder, run `claude`, and type
   **`/setup`**. It checks each remaining step on your computer, skips what's done, and picks up
   where you left off whenever you run it again.

## The guide

Prefer to read? Work through these in order:

1. [What Jev is, and why it's different](guide/01-what-is-jev.md) (10-minute read, no setup)
2. [Install the tools](guide/02-install.md): Python, Claude Code, the TypeSafe skill and your API key
3. [Try it on sample emails](guide/03-try-sample.md): see Jev work before connecting any account
4. [Connect Gmail](guide/04-connect-gmail.md): the one-time Google setup (read-only)
5. [Run it and read the report](guide/05-run-daily.md)
6. [Customize it with Claude](guide/06-customize.md)
7. [Test it honestly](guide/07-test-honestly.md)
8. [Privacy and safety](guide/08-privacy.md)
9. [Troubleshooting](guide/09-troubleshooting.md)

## What's in this repository

| Path | What it is |
| --- | --- |
| `guide/` | The step-by-step guide |
| `email_triage/questions.py` | **The part you customize:** what Jev is asked, and the rules that turn its answers into piles |
| `email_triage/run.py` | Sends the questions to Jev and writes the report |
| `email_triage/fetch.py` | Reads Gmail with read-only access |
| `sample_data/` | 20 made-up email threads for trying it safely |
| `run-email-triage.cmd` / `.command` | Double-click scripts for Windows and Mac |
| `tests/` | Offline checks (no API calls) |
| `CLAUDE.md` | Instructions Claude Code reads when you work in this folder |

Your email, the requests sent to Jev, and the reports are saved only in a `private/` folder that git
ignores, so they're never uploaded.

## Costs and accounts you'll need

- **TypeSafe** account with billing set up, for Jev. A run of 50 emails costs about $0.003.
- **Claude** Pro, Max, Team or Enterprise plan, or a Console account, for Claude Code. The free plan
  doesn't include Claude Code.
- **Google** account with Gmail. The Google Cloud setup is free.

## Credits

Created by **Mat Miles, BYU-Idaho David O. McKay Library**.

- [TypeSafe](https://typesafe.ai) built Jev, the [documentation](https://docs.typesafe.ai) and the
  Claude Code skill this guide relies on.
- The tutorial video [**"Jev + Claude = INSANE Results (Every Concept Explained)"**](https://youtu.be/D-Z5HnLW_ho)
  by Simon Scrapes inspired this project and explains the concepts well. It's recommended viewing
  alongside chapter 1.

Licensed under the [MIT License](LICENSE).
