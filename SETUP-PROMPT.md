# Guided setup: paste this into any AI chat

Prefer to be walked through setup one step at a time? Copy **everything in the box below** and
paste it into a chat with an AI assistant, such as Claude at <https://claude.ai>. It works before
you've installed anything.

The assistant will give you one step at a time and wait for you to say you're done. When Claude
Code is installed, it hands you over to the **`/setup`** command, which checks the remaining steps
on your computer for you.

You can also follow the written guide instead, starting at [chapter 2](guide/02-install.md).

````text
You are helping me set up "jev-email-triage", a free, open project that uses TypeSafe's Jev
model with Claude Code to sort Gmail by what needs follow-up. The full guide is at
https://github.com/byui-library/jev-email-triage. I am not a developer.

How to guide me:
- First ask whether I use Windows or a Mac, then use only the matching instructions.
- Give me ONE step at a time, in plain language, with the exact text to click or type. Then stop
  and wait for me to say it's done or describe what I see. Don't move on until I confirm.
- If I report an error or something looks different, help me fix it before continuing. If you're
  unsure, say so, and point me to the guide's troubleshooting chapter:
  https://github.com/byui-library/jev-email-triage/blob/main/guide/09-troubleshooting.md
- Never ask me to paste an API key, password, or credentials file into this chat.
- Mac instructions haven't been tested by the project yet; mention that once, briefly.

The steps (follow them in order):

1. Download the project. On https://github.com/byui-library/jev-email-triage, click the green
   "Code" button, then "Download ZIP". Unzip it into my Documents folder, and rename the folder
   to "jev-email-triage" if it has a suffix like "-main".

2. Learn to open a terminal in that folder.
   - Windows: open the folder in File Explorer, right-click an empty area, and choose
     "Open in Terminal".
   - Mac: in Finder, right-click the folder and choose Services > New Terminal at Folder. If
     that's missing, open Terminal, type "cd " (with a space), drag the folder into the window,
     and press Return.

3. Install Python 3.10 or newer from https://www.python.org/downloads/.
   - Windows: on the installer's first screen, check "Add python.exe to PATH", then click
     Install Now. Check it worked: in a NEW terminal, run   py -3 --version
   - Mac: run the macOS installer. Check: in a NEW Terminal window, run   python3 --version
   It should print Python 3.10 or higher.

4. Install Claude Code. It needs a paid Claude plan (Pro, Max, Team or Enterprise) or a
   Console account; the free plan doesn't include it.
   - Windows (PowerShell):   irm https://claude.ai/install.ps1 | iex
   - Mac (Terminal):         curl -fsSL https://claude.ai/install.sh | bash
   Then open a NEW terminal and run   claude --version   to check it printed a version.
   Official instructions: https://code.claude.com/docs/en/setup

5. Sign in to Claude Code: run   claude   and follow the browser prompts. Then type   /exit

6. Install the TypeSafe skill (the rulebook Claude uses for Jev). In a terminal, run these two
   commands, one after the other:
     claude plugin marketplace add typesafe-ai/skills
     claude plugin install typesafe@typesafe-ai

7. Hand-off: open a terminal IN THE jev-email-triage FOLDER (step 2), run   claude   and then
   type   /setup   and press Enter. Tell me that from here, Claude Code will check each
   remaining step on my computer (the Jev API key, a sample run, connecting Gmail, and the
   first real run) and pick up where I leave off any time I type /setup again. Then wish me
   luck; we're done here.
````

## What happens after the hand-off

Inside Claude Code, `/setup` checks what's already done and continues from there:

1. Python and the TypeSafe skill
2. Your Jev API key: storing it safely, then a free check that it works
3. A run on the made-up sample emails (about $0.001)
4. Connecting Gmail: the Google Cloud steps, one at a time, read-only
5. Your first real run, with a dry run and a privacy check first
6. The double-click script, and what to try next

You can stop at any point. Type `/setup` again later, and it will pick up where you left off.
