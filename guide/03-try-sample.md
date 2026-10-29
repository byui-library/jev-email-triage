# 3. Try it on sample emails

*About 5 minutes.* Before connecting your own inbox, run the tool on **20 made-up email threads**
in [`sample_data/sample_threads.json`](../sample_data/sample_threads.json). They include a
colleague's request, a student asking for an extension, a lost package, a payment reminder, two
phishing attempts, marketing, and a group thread where the latest message is addressed to someone
else.

All names and addresses are fictional, and this step needs no Google setup.

## Run it

Open a terminal in the project folder (see [chapter 2](02-install.md#opening-a-terminal-in-the-project-folder))
and run:

```sh
py -3 -m email_triage.run --sample
```

*(Mac: `python3 -m email_triage.run --sample`)*

You'll see something like:

```text
20 threads in 0.6s, ~$0.00108, 0 errors. Report: private\runs\20261029-111915\followup-2026-10-29.md
Sample check: 18 of 20 landed in the expected pile.
  - How did we do? Tell us about your recent visit: expected no_action, got check (...)
  - Your order has shipped: expected no_action, got check (...)
```

Twenty emails, each with seven questions, judged in well under a second for about a tenth of a
cent.

## What just happened

For each thread, the tool:

1. **Built the state:** the subject, the last three messages, who sent each one and when, who it
   was addressed to, and a few facts code already knows, such as "the latest message is from
   You" and "it's been 3 days". Links, phone numbers and email addresses in the text are removed
   first.
2. **Asked Jev seven questions in one request.** Jev returned a probability for each.
3. **Applied the rules** in `email_triage/questions.py` to choose a pile, then scored a priority
   from 0 to 100.

The sample emails are written as if today were **October 29, 2026**, so their deadlines stay
meaningful whenever you run them.

## Read the report

Open the report file named in the output. It's in the `private/runs/` folder, and it opens nicely
in VS Code or any Markdown viewer. Each pile lists its threads, highest priority first:

| Pri | Subject | From | Days | Deadline | Why |
| --- | --- | --- | --- | --- | --- |
| 79.3 | Q4 budget numbers | Dana Whitfield | 2 | Oct 30 (1d) | asks you to reply or act (0.99) |

- **Pri:** priority, 0 to 100. Higher means follow up sooner.
- **Days:** days since the latest message.
- **Deadline:** the date Jev picked as the deadline, with days left, or **overdue**.
- **Why:** the rule that chose the pile, with Jev's number. This is how you can always tell *why*
  something landed where it did.

## About the "misses"

You'll probably see **18 or 19 of 20**. Jev's numbers can shift slightly between runs. The usual
misses are automated notices, such as a survey or a shipping update, landing in **Check** instead
of No action. That's the safe direction: when Jev isn't sure, the rules ask you to look rather
than hide the email.

Don't "fix" the sample by rewording questions until it scores 20 of 20. That's called **prompt
gymnastics**, and it tends to break on real email. [Chapter 7](07-test-honestly.md) explains how
to improve the tool honestly.

## Look at exactly what was sent

Every request and response is saved in `private/runs/<time>/payloads/`, one file per thread. Open
one to see the exact state and the seven questions, with Jev's answers. Nothing is hidden.

To build the requests **without sending anything**, add `--dry-run`:

```sh
py -3 -m email_triage.run --sample --dry-run
```

**Next:** [4. Connect Gmail →](04-connect-gmail.md)
