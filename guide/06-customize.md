# 6. Customize it with Claude

The tool works out of the box, but your inbox isn't anyone else's. You might want a pile for
student questions, a VIP list, or a different sense of what's urgent. You don't need to edit code
yourself: **describe the change to Claude**, and it will update `email_triage/questions.py` using
the TypeSafe skill.

## How to ask

1. Open a terminal in the project folder and run `claude`.
2. Start every request with **"Use the TypeSafe skill"**, or **`/ts`**.
3. Ask Claude to **show you the plan before changing anything**, and to run the tests and the
   sample afterwards.

Claude reads this project's [`CLAUDE.md`](../CLAUDE.md), which tells it how the tool is built and
which privacy rules to follow.

## Prompts you can paste

**Understand what's there first**

```text
/ts Explain in plain language how email_triage/questions.py decides which pile an email goes
in. List each question Jev is asked, and walk me through the routing rules as a table.
```

**Add a pile**

```text
/ts I'd like a new pile called "Students" for emails from students asking about assignments,
grades or deadlines. Show me the plan first: any new question, its criteria, the routing rule
and threshold, and where it sits among the other piles. After I approve, make the change, run
the tests and --sample, and tell me what changed.
```

**Boost important people**

```text
/ts Emails from my supervisor and the people in a VIP list should rank higher. Keep the VIP list
in a private file that git ignores, not in the code. Show me the plan first.
```

**Change what counts as urgent**

```text
/ts Deadlines matter more to me than how long something has waited. Show me the current
priority weights and suggest new ones, explaining what would move up or down. Don't change
anything until I agree.
```

**Find out why an email landed in the wrong pile**

```text
/ts The thread with ID <paste the ID from the report's Gmail link> landed in Check, but I think
it should be Reply needed. Look at its saved payload in private/runs, explain which answer drove
the decision, and suggest a fix that isn't specific to this one email. Don't quote the email's
content in code or docs.
```

## The design rules Claude should follow

These come from the TypeSafe skill and the tutorial. If Claude's plan breaks one, ask it why.

1. **Start from the action, not the data.** Every question must change what happens to an email.
   List the piles first, then ask "what would a person need to know to choose between them?" A
   question no rule uses still costs money on every email, and does nothing.
2. **Jev judges, code decides.** Questions ask for judgments, such as *"is the sender asking you
   to act?"*. Rules and thresholds live in code. Never ask Jev *"which pile should this go in?"*.
3. **One judgment per question.** If a question contains "and" or "or", it's probably two
   questions.
4. **Describe each option concretely,** including what it is *not*. For example: *"Billing:
   charges, invoices, refunds; not login problems on a paid plan."*
5. **Give Jev a way to say "none of these."** A Choice always picks an option, so pair it with a
   yes/no question: *"does this fit any of these at all?"*.
6. **Give Jev what a person would look at,** and nothing more: who sent it, who it was addressed
   to, the recent messages, and facts code already knows.
7. **Ask everything at once.** All questions go in one request. Extra questions are nearly free.
8. **Set each threshold by what a wrong answer costs.** Missing a real request is worse than
   showing a newsletter in Check, so uncertain cases go to Check.
9. **Treat 0.3–0.7 as "not sure".** It needs its own rule, usually Check.

## After any change

Ask Claude to run the tests and the sample, or run them yourself:

```sh
py -3 -m unittest discover -s tests -t .
py -3 -m email_triage.run --sample
```

Then check the change on **real email it wasn't designed around**. [Chapter 7](07-test-honestly.md)
explains how.

**Next:** [7. Test it honestly →](07-test-honestly.md)
