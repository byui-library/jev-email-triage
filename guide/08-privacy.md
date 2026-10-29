# 8. Privacy and safety

Using this tool means real email, including other people's names and messages, is sent to
TypeSafe's API to be judged. Here's exactly what is and isn't shared, and how to control it.

## What leaves your computer

**To Google:** nothing new. The tool *reads* from Gmail with the read-only `gmail.readonly`
permission. It can't send, delete, archive or label anything.

**To TypeSafe (Jev),** for each thread:

| Sent | Not sent |
| --- | --- |
| The subject (with your address and username removed) | Your email address or username |
| The last 3 messages' text, with quoted history and signatures removed, up to 500 words each | Links of any kind, including private payment or login links |
| Each sender's name and address | Phone numbers and email addresses inside the text |
| Recipients, as names, with you as "You" | Attachment contents (only file names are sent) |
| Dates, and facts like "the latest message is from You" | Drafts, older messages, and anything outside the date range |

**To Anthropic (Claude):** only what you show Claude in a conversation. The tool itself doesn't
use Claude. When you ask Claude to investigate a result, it may read the saved files in
`private/`. This project's `CLAUDE.md` tells it never to copy email content into code, docs or
commits.

## What stays on your computer

- `private/`: fetched threads, every request and response, and the reports. Git ignores this
  folder, so it's never uploaded if you share or fork the project. Delete it whenever you like.
- `~/.jev-gmail/client_secret.json` and `token.json`: your Google credentials, kept outside the
  project.
- `TYPESAFE_API_KEY`: stored as a user setting on Windows, or in the Keychain on a Mac. It's never
  written to a file in the project.

## Confidential or third-party email

Some threads shouldn't be sent at all, such as forwarded confidential business documents or
someone else's financial records. List their Gmail thread IDs, one per line, in
`private/structure_only.txt`:

```text
18c2f0a9b1e4d7c3   # confidential board thread
```

The thread ID is the long code at the end of the thread's Gmail link in the report. Those threads
are fetched with **who sent what, and when, only**: the subject is withheld and no text is
included. Jev can still tell whether you wrote last, but it judges less accurately.

## Good habits

- **Dry-run first** when you change anything, and look at a payload or two.
- **Never paste your API key or Google files into Claude**, email or chat.
- **Don't commit `private/`.** It's ignored by default; keep it that way.
- **When sharing results,** describe them generically ("a payment reminder"), not with real
  names or subjects.
- **Check your organization's policy** before using this on a work account. Some employers don't
  allow sending work email to outside services.

## Turning it off

- **Stop Google access:** go to <https://myaccount.google.com/permissions>, remove the app, and
  delete `~/.jev-gmail/token.json`.
- **Stop Jev access:** delete or revoke the key at <https://console.typesafe.ai/keys>.
- **Remove local data:** delete the `private/` folder.

**Next:** [9. Troubleshooting →](09-troubleshooting.md)
