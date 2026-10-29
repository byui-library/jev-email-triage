# 4. Connect Gmail (read-only)

*About 15 minutes, once.* You'll create a private "app" in Google Cloud that only you can use,
and give this tool **read-only** access to your Gmail. It can't send, delete, label or change
anything.

Everything here is free. The screens are from Google's console as of October 2026, and Google
renames things occasionally. If a label doesn't match, look for the closest one.

## Step 1: Create a Google Cloud project and turn on the Gmail API

1. Go to <https://console.cloud.google.com/> and sign in with the Google account whose Gmail you
   want to sort.
2. Use the project picker at the top to **create a new project**, for example
   `jev-email-triage`. Make sure it's selected.
3. Open **APIs & Services → Library**, search for **Gmail API**, and click **Enable**.

## Step 2: Set up the sign-in screen, and add yourself as a tester

1. Open **Google Auth Platform** (also called *OAuth consent screen*). Search for it in the top
   bar if you can't find it.
2. If you're asked to configure it, give the app a name (for example `Jev email triage`), choose
   your email as the support contact, and choose **External** as the audience.
3. Go to **Audience**. Leave the publishing status as **Testing**; don't publish.
4. Under **Test users**, click **+ Add users**, enter **your Gmail address**, and **Save**.

> **Don't skip step 4.** Without it, sign-in fails with *"Access blocked … Error 403:
> access_denied"*. Testing mode means only the accounts you list can use the app, which is what
> you want.

## Step 3: Create the credentials file

1. Go to **Google Auth Platform → Clients** and click **Create client**.
2. **Application type: Desktop app.** Give it any name.
3. Leave **"Use this client for an AI-powered agent"** **unchecked**. This tool is ordinary
   Python on your computer.
4. Click **Create**. In the dialog that appears, click **Download JSON**.
5. Create a folder called `.jev-gmail` in your **home folder**, outside the project:
   - **Windows:** `C:\Users\<you>\.jev-gmail\`
   - **Mac:** `/Users/<you>/.jev-gmail/`. Folders starting with a dot are hidden in Finder, so
     create it in Terminal: `mkdir ~/.jev-gmail`
6. Move the downloaded file there and **rename it to `client_secret.json`**. Google names it
   something like `client_secret_1234…apps.googleusercontent.com.json`.

> This file is a credential. Keep it out of the project folder, and never email it, upload it or
> paste it into Claude.

## Step 4: Install the Google libraries

In a terminal in the project folder:

```sh
py -3 -m pip install --user -r requirements.txt
```

*(Mac: `python3 -m pip install --user -r requirements.txt`)*

## Step 5: Sign in once and fetch your email

```sh
py -3 -m email_triage.fetch --newer 14
```

1. A browser tab opens. Choose your Gmail account.
2. You'll see **"Google hasn't verified this app"**. That's expected for a private testing app.
   Click **Continue**.
3. Approve the one permission requested, which is to **view your email messages and settings**.
4. The tab says *"The authentication flow has completed."* Close it.

Back in the terminal, you'll see something like
`31 threads written to private\threads.json`. Your sign-in is saved as
`~/.jev-gmail/token.json`, so you won't need to sign in again.

### What the fetch does

- It reads inbox threads from the **last 14 days**, skipping senders that look automated
  (`noreply`, `newsletter`, `info`…) and anything containing "unsubscribe".
- It writes recipients as names, with **you as "You"**, and removes **your email address and
  username** from subjects, text and attachment names.
- It skips drafts, and never opens attachments.
- It saves everything to `private/threads.json`, which git ignores and nothing uploads.

To look further back, change the numbers. For example, `--newer 28 --older 14` gets the two
weeks before last.

## Step 6: Run Jev on your email

First, do a dry run. It builds the requests and **sends nothing**:

```sh
py -3 -m email_triage.run --dry-run
```

Open a file or two in the `private/runs/<time>/payloads/` folder it names, and check you're
comfortable with what would be sent. Then run it for real:

```sh
py -3 -m email_triage.run
```

The report is saved in `private/runs/<time>/`. See [chapter 5](05-run-daily.md) for how to read
it, and [chapter 8](08-privacy.md) for exactly what's shared with TypeSafe.

**Next:** [5. Run it and read the report →](05-run-daily.md)
