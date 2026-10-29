# 7. Test it honestly

It's easy to make a tool look perfect on the emails you're staring at, and still have it fail on
next week's. This chapter covers how this project was tested, and the real mistakes that testing
caught.

## The routine

1. **Dry run first.** `--dry-run` builds every request and sends nothing. Open a few files in
   `private/runs/<time>/payloads/` and check what *would* be sent.
2. **Privacy scan.** Check that no links, phone numbers, or your own address are in the requests.
   You can ask Claude: *"Scan the latest dry-run payloads for links, phone numbers and my
   address, without printing any email content."*
3. **Send one thread** (`--thread <id>` or `--limit 1`), and read Jev's raw answers in its payload
   file.
4. **Run the full set,** and read the report row by row. Don't just look at the totals.
5. **When something's wrong, fix the cause, then test on a *different* date range,** for example
   `fetch --newer 28 --older 14`. This is the most important step.

## Why a different date range?

If you change the questions until this week's report looks right, you've tuned the tool to this
week's emails. The test that counts is mail it has never seen. This project used four separate
two-week windows: a fix suggested by one window was always checked on another.

On the last window, which was untouched before the run, **42 of 43 threads** landed where a
person would put them.

## Real mistakes testing caught

Each of these was found by reading the report, then fixed in a way that **wasn't specific to one
email**:

| What went wrong | Why | The fix |
| --- | --- | --- |
| Marketing written to look personal ("Hi [name]", signed by a named "Program Director") landed in **Reply needed** | The "written personally" question didn't describe that trick | The question's "no" description now mentions marketing made to look personal |
| A lost package went to **No action** | No question asked about unresolved problems | Added an "open issue" question and pile |
| A deadline that had already passed wasn't flagged | Jev saw a deadline, but nothing compared it with today | Code finds the written dates, Jev picks the deadline, and **code** compares it with today. Date math belongs in code. |
| Surveys and "review your statement" emails filled **Check** | Automated mail that asks you to do something isn't always a real task | Automated mail goes to Check only if it also has a deadline, and isn't a promotion |
| In a group thread, a message addressed to someone else landed in **Reply needed** | Jev couldn't see who each message was addressed to | To/Cc recipients were added to the state. That fixes the *information*, not the wording. |
| An automated password-reset email landed in **Reply needed** | "Written personally" scored 0.31, just above the 0.30 "no" line | When "written personally" is unsure and the email asks you to act, it goes to Check |
| A real payment reminder dropped to **No action** | A "senders with 3+ emails get subject only" rule removed its text | That rule is now off by default |

## Warning signs of "prompt gymnastics"

Be wary when a change looks like any of these. They make one email come out right, and tend to
break others:

- question wording that mentions a specific email, sender or subject
- a new exception for every email that fails
- thresholds nudged until one email moves
- tests that check for an exact number from Jev
- code that quietly overrides Jev's answers

The better fix is usually to **give Jev better information** (the state), **split a question in
two**, or **change a rule in code**.

## Cost of testing

Each run of 30–50 threads costs about $0.002. All the testing behind this project, more than 200
thread judgments across many reruns, cost well under 5 cents.

**Next:** [8. Privacy and safety →](08-privacy.md)
