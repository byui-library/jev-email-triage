@echo off
rem Windows: double-click to fetch the last 14 days of Gmail (read-only) and rank what needs follow-up.
rem The report opens when it's done. Email data and reports stay in the private\ folder (never shared).

setlocal
cd /d "%~dp0"
title Email triage with Jev

if "%TYPESAFE_API_KEY%"=="" (
    echo TYPESAFE_API_KEY is not set. See guide\02-install.md, step 4, then sign out and back in.
    goto :fail
)

echo Step 1 of 2: fetching Gmail (read-only)...
py -3 -m email_triage.fetch --newer 14 --out private\threads.json
if errorlevel 1 goto :fail

echo.
echo Step 2 of 2: asking Jev and ranking threads...
py -3 -m email_triage.run --input private\threads.json --cap 0.10
if errorlevel 1 goto :fail

rem Open the newest report.
for /f "delims=" %%R in ('dir /b /s /o:d "private\runs\followup-*.md" 2^>nul') do set "REPORT=%%R"
if defined REPORT (
    echo.
    echo Opening %REPORT%
    start "" "%REPORT%"
)
echo.
echo Done.
pause
exit /b 0

:fail
echo.
echo Something went wrong; see the messages above. Nothing in Gmail was changed.
echo guide\09-troubleshooting.md lists the common fixes.
pause
exit /b 1
