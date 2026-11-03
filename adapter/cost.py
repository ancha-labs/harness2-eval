"""Record only allowlisted OpenRouter key metering fields; never save the key."""
import datetime
import json
import sys
import os
import urllib.request
from pathlib import Path

from settings import WORK, RECEIPTS, KEY_FILE
receipts = RECEIPTS
receipts.mkdir(parents=True,exist_ok=True)
if sys.argv[1].startswith('before-') and (WORK / 'STOP_PAID').exists():
    raise SystemExit('Paid batches paused by lab STOP_PAID marker')
key = os.environ.get('OPENROUTER_API_KEY') or KEY_FILE.read_text().strip()
request = urllib.request.Request('https://openrouter.ai/api/v1/key', headers={'Authorization': 'Bearer ' + key})
try:
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)['data']
except Exception as exc:
    raise SystemExit('Key metering failed: ' + type(exc).__name__)
record = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'label': sys.argv[1]}
for field in ['usage', 'limit', 'limit_remaining', 'usage_daily', 'usage_weekly', 'usage_monthly', 'is_free_tier']:
    record[field] = data.get(field)
with (receipts / 'cost.jsonl').open('a') as out:
    out.write(json.dumps(record) + '\n')
md = receipts / 'cost.md'
if not md.exists():
    md.write_text('# OpenRouter spend receipts\n\nGET `https://openrouter.ai/api/v1/key`; monetary fields are USD. Key material and label are excluded. Stop at $24 cumulative key usage.\n\n| UTC | Batch boundary | Cumulative usage | Limit | Remaining |\n|---|---|---:|---:|---:|\n')
with md.open('a') as out:
    out.write(f"| {record['at']} | {record['label']} | {record['usage']} | {record['limit']} | {record['limit_remaining']} |\n")
print(json.dumps(record))
if float(record['usage'] or 0) >= 24:
    raise SystemExit('STOP: paid-work threshold reached')
