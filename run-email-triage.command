#!/bin/zsh
# Mac: double-click to fetch the last 14 days of Gmail (read-only) and rank what needs follow-up.
# The report opens when it's done. Email data and reports stay in the private/ folder (never shared).
# UNTESTED on Mac so far; please report problems.

cd "$(dirname "$0")" || exit 1

fail() {
  echo
  echo "Something went wrong; see the messages above. Nothing in Gmail was changed."
  echo "guide/09-troubleshooting.md lists the common fixes."
  read -k 1 "?Press any key to close..."
  exit 1
}

# A double-clicked script doesn't always load your shell settings, so read the key
# from the Keychain if it isn't already set (see guide/02-install.md, step 4).
if [[ -z "$TYPESAFE_API_KEY" ]]; then
  TYPESAFE_API_KEY="$(security find-generic-password -a "$USER" -s TYPESAFE_API_KEY -w 2>/dev/null)"
  export TYPESAFE_API_KEY
fi
[[ -n "$TYPESAFE_API_KEY" ]] || { echo "TYPESAFE_API_KEY is not set. See guide/02-install.md, step 4."; fail; }

echo "Step 1 of 2: fetching Gmail (read-only)..."
python3 -m email_triage.fetch --newer 14 --out private/threads.json || fail

echo
echo "Step 2 of 2: asking Jev and ranking threads..."
python3 -m email_triage.run --input private/threads.json --cap 0.10 || fail

REPORT="$(ls -t private/runs/*/followup-*.md 2>/dev/null | head -n 1)"
if [[ -n "$REPORT" ]]; then
  echo
  echo "Opening $REPORT"
  open "$REPORT"
fi
echo
echo "Done."
read -k 1 "?Press any key to close..."
