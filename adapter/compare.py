"""Predeclared, interleaved checks of a frozen selected harness; no further editing."""
import hashlib
import argparse
import json
import time
from pathlib import Path
from adapter import AnchaAdapter, RECEIPTS, tree

parser=argparse.ArgumentParser()
parser.add_argument('--source',default='oncall-k1')
parser.add_argument('--name',default='validation')
parser.add_argument('--selected-only',action='store_true')
args=parser.parse_args()
adapter=AnchaAdapter(args.name)
selected=RECEIPTS/args.source/'selected-harness'
if not selected.exists():raise SystemExit('Finish optimization before validation')
files={str(p.relative_to(selected)):hashlib.sha256(p.read_bytes()).hexdigest() for p in selected.rglob('*') if p.is_file()}
plan=[]
for repeat in [1,2,3]:
    for version in (['selected'] if args.selected_only else ['base','selected'] if repeat%2 else ['selected','base']):
        plan.append({'task':'status-request','repeat':repeat,'version':version,'seed':'l18-fixed','role':'fresh-repeat-on-development-task'})
for task in ['bad-deploy','false-alarm']:
    for version in (['selected'] if args.selected_only else ['base','selected']):
        plan.append({'task':task,'repeat':1,'version':version,'seed':'l18-heldout-'+task,'role':'held-out-task with new IDs; no edits or selection use this result'})
receipt=adapter.root/'plan.json'
if receipt.exists() and json.loads(receipt.read_text())['frozen_selected_files'] != files:
    raise SystemExit('The selected harness changed after validation was planned')
receipt.write_text(json.dumps({'source':args.source,'frozen_selected_files':files,'plan':plan,'baseline_controls':'validation/' if args.selected_only else 'interleaved in this batch','policy':'No edits or model optimization during validation. All runs use fresh worlds and serial execution.'},indent=2))
start=time.monotonic()
for row in plan:
    harness=selected if row['version']=='selected' else None
    adapter.execute(row['task'],harness,f"{row['version']}-{row['task']}-{row['repeat']}",seed=row['seed'])
(adapter.root/'timing.json').write_text(json.dumps({'wall_s':time.monotonic()-start},indent=2))
after={str(p.relative_to(selected)):hashlib.sha256(p.read_bytes()).hexdigest() for p in selected.rglob('*') if p.is_file()}
assert after == files, 'The selected harness changed during validation'
