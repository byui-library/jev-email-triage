# 5. Run it and read the report

## One click

Once [chapter 4](04-connect-gmail.md) is done, a single double-click runs everything:

- **Windows:** double-click **`run-email-triage.cmd`** in the project folder.
- **Mac (untested):** double-click **`run-email-triage.command`**. The first time, you may need to
  right-click it and choose **Open**, because macOS asks before running downloaded scripts. If it
  says it isn't allowed to run, open Terminal in the folder and run
  `chmod +x run-email-triage.command` once.

The window shows two steps:

1. **Fetching Gmail (read-only)** for the last 14 days.
2. **Asking Jev and ranking threads.** The run stops if estimated spend would pass $0.10.

Then the newest report opens. Press any key to close the window.

*Tip:* make a desktop shortcut. On Windows, right-click the file → **Show more options → Create
shortcut**, and move the shortcut to your desktop. On a Mac, hold ⌘⌥ and drag the file to the
desktop to make an alias.

## Reading the report

The report has one section per pile, most important first. Within each pile, the highest
priority is at the top.

| Pile | What to do |
| --- | --- |
| **Reply needed** | Reply. Someone wrote to you personally and is waiting. |
| **Waiting on them** | Nudge them if it's been a while. You asked and haven't heard back. |
| **Open issue to track** | Follow up on the problem, such as a lost package or a pending refund. Nobody is waiting on you. |
| **Check** | Take a quick look. Jev was unsure, an automated email has a real deadline, or a request's date has already passed and may be stale. |
| **Possible phishing or spam** | Don't open links or attachments. Delete it or report it. |
| **No action** | Usually nothing. Skim it if you like. |

Each row has:

- **Pri:** the priority score, 0 to 100. It's 35% how clearly you're asked, 25% how close the
  deadline is, 20% how long it has waited, and 20% who sent it.
- **Days:** days since the latest message.
- **Deadline:** the date found, with days left, or **overdue**. "date unclear" means Jev saw a
  deadline but no written date, such as "by Friday".
- **Why:** the rule that chose the pile, with Jev's number. If a row looks wrong, the "Why" tells
  you which judgment to question.
- **Subject:** a link that opens the thread in Gmail.

## What the tool never does

- It never sends, deletes, archives or labels email. Access is read-only.
- It never writes replies. It tells you what needs attention, and you decide.
- It never uploads your data anywhere except the trimmed text sent to Jev for judging
  ([chapter 8](08-privacy.md)).

## Running it by hand

The script just runs these two commands, which you can type yourself:

```sh
py -3 -m email_triage.fetch --newer 14
py -3 -m email_triage.run
```

Useful options for `run`:

| Option | What it does |
| --- | --- |
| `--dry-run` | Builds and saves the requests, sends nothing |
| `--limit 5` | Only sends the first 5 threads |
| `--thread <id>` | Only sends one thread, by its Gmail ID |
| `--cap 0.05` | Stops if estimated spend would pass $0.05 |
| `--sample` | Uses the made-up sample emails instead |

**Next:** [6. Customize it with Claude →](06-customize.md)
