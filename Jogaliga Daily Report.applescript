-- Jogaliga Daily Report Mailer
-- This script runs the daily report mailer in a new Terminal window

-- Get the path to the current script's directory
set scriptPath to (path to me as text)
set scriptDir to do shell script "dirname " & quoted form of POSIX path of scriptPath

-- Construct the full path to the shell script
set shellScriptPath to scriptDir & "/run_daily_report.sh"

-- Open Terminal and run the script
tell application "Terminal"
    activate
    set newTab to do script "cd " & quoted form of scriptDir & " && " & quoted form of shellScriptPath
    set custom title of newTab to "Jogaliga Daily Report"
end tell 