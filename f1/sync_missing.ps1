# Saves every finished race weekend that is not in f1/store yet and pushes it, so the hosted app updates itself.
# Meant to be run by Windows Task Scheduler (see the README), but you can run it by hand too.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)   # the repo folder (this file lives in f1/)
git pull --rebase --quiet
python -m f1.sync --missing --push
