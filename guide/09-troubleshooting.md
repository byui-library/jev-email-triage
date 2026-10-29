# 9. Troubleshooting

These are the problems hit while building and testing this project, and how they were fixed.

## Jev and the API key

**`TYPESAFE_API_KEY is not set`**
: The key isn't visible to this window. On Windows, close **every** terminal and VS Code window,
  and reopen them; programs only see new settings when they start. On a Mac, open a new Terminal
  window, and check step 4 of [chapter 2](02-install.md#step-4-get-your-jev-api-key-and-store-it-safely).

**`HTTP 401` / `authentication_error`**
: TypeSafe rejected the key. Check that billing is set up, then **create a new key** at
  <https://console.typesafe.ai/keys> and store it again. A key made before billing was set up can
  keep failing. If a brand-new key still fails, contact TypeSafe support.

**I stored a new key, but the old one is still used**
: Reopen your terminals (see above). On Windows, you can check without showing the key. This prints
  `True` when the current window has the latest key:
  ```powershell
  $env:TYPESAFE_API_KEY -ceq [Environment]::GetEnvironmentVariable('TYPESAFE_API_KEY','User')
  ```

**`HTTP 429`**
: Too many requests at once. Wait a minute and run again.

## Google sign-in and Gmail

**"Access blocked … has not completed the Google verification process" (`Error 403: access_denied`)**
: Your address isn't a test user. In Google Cloud, go to **Google Auth Platform → Audience → Test
  users**, add your Gmail address, save, wait a few minutes, and try again.

**"Google hasn't verified this app"**
: That's expected for a private app in Testing mode. Click **Continue**.

**`Missing ~/.jev-gmail/client_secret.json`**
: The credentials file isn't where the tool looks. Google names the download
  `client_secret_<long id>.json`; rename it to exactly `client_secret.json` and put it in the
  `.jev-gmail` folder in your home folder, not in the project.

**No "Download JSON" button**
: It appears in the dialog right after you click **Create**. If you closed it, open **Clients**,
  click your client, and download it there; you may need to add a new secret first.

**The fetch finds 0 threads**
: Your inbox may not have the last 14 days, or every sender matched the automated-sender filter.
  Try `--newer 30`.

**I want to sign in as a different account**
: Delete `~/.jev-gmail/token.json` and run the fetch again.

## Python and the scripts

**`py` or `python3` isn't recognized**
: Python isn't installed, or isn't on your PATH. Reinstall it from <https://www.python.org>, and
  on Windows check **"Add python.exe to PATH"**. Open a new terminal afterwards.

**`No module named google` (or `googleapiclient`)**
: Install the Google libraries: `py -3 -m pip install --user -r requirements.txt`.

**`No module named email_triage`**
: The terminal isn't in the project folder. Open it there (see
  [chapter 2](02-install.md#opening-a-terminal-in-the-project-folder)) and run the command again.

**Mac: the `.command` file won't open**
: Right-click it and choose **Open** the first time. If macOS says it isn't allowed to run, run
  `chmod +x run-email-triage.command` once in Terminal, in the project folder.

## Results look wrong

**An email is in the wrong pile**
: Read the report's **Why** column, then open that thread's file in `private/runs/<time>/payloads/`
  to see exactly what Jev was given and what it answered. Usually the fix is better information
  or a clearer rule, not new wording. See [chapter 6](06-customize.md) for a prompt that asks
  Claude to investigate, and [chapter 7](07-test-honestly.md) for how to check the fix.

**The same task appears several times**
: Repeated reminders from one sender each get a row. Grouping them is a possible improvement.

**Something else?** Please [open an issue](https://github.com/byui-library/jev-email-triage/issues),
and leave out real email content, keys and credentials.

[← Back to the start](../README.md)
