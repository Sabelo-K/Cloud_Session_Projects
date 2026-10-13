#!/usr/bin/env bash
# Pull the narration lines (blockquotes starting with "> ") out of a SCRIPT.md, stripping
# pause marks "/" and markdown emphasis. Stops at the fact-check log.
# Usage: extract_vo.sh SCRIPT.md > VOICEOVER.txt
sed -n '1,/^## Fact-check/p' "$1" | grep '^> ' | grep -v 'Status:' | sed 's/^> //;s# / # #g;s#/$##;s/\*//g'
