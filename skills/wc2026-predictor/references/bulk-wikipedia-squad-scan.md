# Bulk Wikipedia Squad Status Scan

## Why

When Exa is exhausted (HTTP 402) and you need to check the squad status of all 48 teams, searching each team individually via SerpAPI consumes 10+ calls and yields messy results. Instead, extract ALL teams' status from a single Wikipedia `action=raw` download.

## One-shot scan (proven, 2026-05-30)

```bash
# Step 1 — download wiki markup (~300KB, 0.5s)
curl -sL -o /tmp/wiki_raw.wiki \
  "https://en.wikipedia.org/w/index.php?title=2026_FIFA_World_Cup_squads&action=raw"

# Step 2 — bulk extract all 48 teams' announcement status
python3 -c "
import re
with open('/tmp/wiki_raw.wiki') as f:
    text = f.read()

# Find team headings
team_pattern = re.compile(r'^===([^=]+)===\s*$', re.MULTILINE)
splits = team_pattern.split(text)

statuses = []
for i in range(1, len(splits), 2):
    team_name = splits[i].strip()
    team_content = splits[i+1] if i+1 < len(splits) else ''

    if team_name in ['Age', 'Coach representation by country']:
        continue

    has_players = '{{nat fs g start}}' in team_content
    will_announce = re.search(r'final squad will be announced on ([^<.]+)', team_content)
    final_announced = re.search(r'(announced|named) their final squad on ([^<.]+)', team_content)

    status = ''
    if will_announce:
        status = f'⏳ Final: {will_announce.group(1).strip()}'
    elif final_announced:
        status = f'✅ Final on {final_announced.group(2).strip()}'
    elif has_players:
        status = '✅ Final (listed)'
    else:
        status = '❓ Unknown'

    player_count = len(re.findall(r'{{nat fs g player\\|', team_content)) if has_players else 0
    if player_count > 0:
        status += f' ({player_count} players)'

    statuses.append(f'{team_name}: {status}')

print('\\n'.join(statuses))
"
```

## Extract a single team's full roster

```bash
python3 -c "
with open('/tmp/wiki_raw.wiki') as f:
    text = f.read()

start = text.find('===Canada===')
end = text.find('\\n===', start + 12)
section = text[start:end]
print(section)
"
```

Replace `Canada` with any team name as it appears in the Wikipedia section heading.

## Key regex patterns for markup parsing

| What | Regex |
|------|-------|
| Team heading | `^===[^=]+===$` (multi-line) |
| Player entry | `{{nat fs g player\|no=\|pos=GK\|name=[[...]]\|...}}` |
| Squad start marker | `{{nat fs g start}}` |
| Squad end marker | `{{nat fs end}}` |
| Future tense (not yet) | `will be announced on ([^<.]+)` |
| Past tense (confirmed) | `(announced\|named) their final squad on ([^<.]+)` |

## Trigger rules

Use this technique when:
1. Exa is exhausted (HTTP 402) AND
2. You need a comprehensive overview of which teams have announced squads AND
3. You want to avoid exhausting SerpAPI credits on individual team searches

Do NOT use for deep analysis (injury context, coach quotes, tactical analysis) — those still require SerpAPI + targeted article extraction.
