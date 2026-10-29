# 2. Install the tools

*About 30 minutes, once.* You'll install Python, Claude Code and the TypeSafe skill, and store
your Jev API key safely.

> **Mac users:** the Mac steps below are written from the official instructions but haven't been
> tested yet. If something doesn't match what you see, please
> [open an issue](https://github.com/byui-library/jev-email-triage/issues).

## Step 1: Get this project onto your computer

The easiest way, with no git needed:

1. On this repository's GitHub page, click the green **Code** button, then **Download ZIP**.
2. Unzip it into your **Documents** folder, and rename the folder to `jev-email-triage` if it has
   a suffix such as `-main`.

If you already use git: `git clone https://github.com/byui-library/jev-email-triage.git`

### Opening a terminal in the project folder

Several steps ask you to "open a terminal in the project folder":

- **Windows:** open the `jev-email-triage` folder in File Explorer, right-click an empty area, and
  choose **Open in Terminal**.
- **Mac:** in Finder, right-click the `jev-email-triage` folder and choose **Services → New
  Terminal at Folder**. If you don't see it, open Terminal and type `cd ` (with a space), drag the
  folder into the window, and press Return.

## Step 2: Install Python (3.10 or newer)

**Windows**

1. Download the latest Python installer from <https://www.python.org/downloads/>.
2. Run it. On the first screen, check **"Add python.exe to PATH"**, then click **Install Now**.
3. Open a new terminal and run `py -3 --version`. You should see `Python 3.1x.x`.

**Mac**

1. Download the macOS installer from <https://www.python.org/downloads/> and run it.
2. Open a new Terminal window and run `python3 --version`. You should see `Python 3.1x.x`.

> In the rest of this guide, commands start with `py -3` (Windows). **On a Mac, type `python3`
> instead.** Everything after that is the same.

## Step 3: Install Claude Code and the TypeSafe skill

Claude Code needs a paid Claude plan (Pro, Max, Team or Enterprise) or a Console account. The
official instructions are at <https://code.claude.com/docs/en/setup>.

1. Install Claude Code. In a terminal, run:

   - **Windows (PowerShell):** `irm https://claude.ai/install.ps1 | iex`
   - **Mac:** `curl -fsSL https://claude.ai/install.sh | bash`

2. Open a **new** terminal and run `claude --version` to check it worked. Then run `claude`, and
   follow the browser prompts to sign in. Type `/exit` to leave.

   *Prefer a window to a terminal?* Claude Code also comes as a
   [desktop app](https://code.claude.com/docs/en/desktop-quickstart.md) and a
   [VS Code extension](https://code.claude.com/docs/en/vs-code.md).

3. Install the TypeSafe skill, the rulebook Claude uses for Jev. In a terminal, run these two
   commands:

   ```sh
   claude plugin marketplace add typesafe-ai/skills
   claude plugin install typesafe@typesafe-ai
   ```

4. Start `claude` again and type `/plugins`. **typesafe** should be listed under *Installed*.

**Tip: name the skill in your requests.** TypeSafe recommends starting requests with *"Use the
TypeSafe skill…"*. In this project you can also say **"ts skill"**, or start with **`/ts`**.

## Step 4: Get your Jev API key and store it safely

1. Create a TypeSafe account at <https://typesafe.ai> and **set up billing first**.
2. Go to <https://console.typesafe.ai/keys> and create an API key. If you made a key before
   setting up billing, create a new one; old keys can keep returning `401` errors.
3. **Don't paste the key into Claude or save it in a file.** Store it as a private setting on your
   computer instead:

### Windows

Open **PowerShell**, not Claude, and run these four lines. The key isn't shown while you paste
it, and it isn't saved in your command history:

```powershell
$s = Read-Host "TypeSafe API key" -AsSecureString
$k = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
[Environment]::SetEnvironmentVariable('TYPESAFE_API_KEY', $k.Trim(), 'User')
Remove-Variable s, k
```

Then **close every terminal and VS Code window, and reopen them**. Programs only see a new
setting when they start.

### Mac (untested)

Store the key in your Keychain. This command asks you to paste it, and doesn't show it:

```sh
security add-generic-password -a "$USER" -s TYPESAFE_API_KEY -w
```

Then make new terminals load it. Run this once:

```sh
echo 'export TYPESAFE_API_KEY="$(security find-generic-password -a "$USER" -s TYPESAFE_API_KEY -w 2>/dev/null)"' >> ~/.zshrc
```

Open a new Terminal window. The double-click script reads the Keychain directly, too.

## Step 5: Check that everything works

1. Open a terminal **in the project folder** and run `claude`.
2. Paste this request:

   ```text
   Use the TypeSafe skill. Check my key works: ask Jev one yes/no question about
   "Charged twice, please fix asap." Question: "The customer is reporting a billing problem."
   Show the raw answer from Jev.
   ```

3. Claude will ask before sending a test request. Allow it.

You should see an answer close to `"noul": 0.99`, which means Jev is 99% sure it's a billing
problem. The check costs about $0.00001.

If you get an error, see [Troubleshooting](09-troubleshooting.md): `401` means a key problem,
and "not set" means you need to reopen your terminal.

**Next:** [3. Try it on sample emails →](03-try-sample.md)
