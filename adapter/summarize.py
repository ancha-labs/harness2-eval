"""Assemble reviewable tables from raw scores, without changing any results."""
import json
import statistics
import re
from pathlib import Path

from settings import RECEIPTS as R
data={}
demo=json.loads((R/'demo/demo.json').read_text())
tests=(R/'upstream-tests.log').read_text()
test_match=re.search(r'(\d+) passed, (\d+) subtests passed in ([\d.]+)s',tests)
data['upstream']={'demo_tasks_done':demo['done'],'demo_tasks_failed':demo['failed'],'python_executions':demo['execution_count'],'scripted_editor_calls':demo['editor_calls'],
    'focused_tests_passed':int(test_match[1]),'subtests_passed':int(test_match[2]),'test_wall_s':float(test_match[3])}
for group in ['oncall-k1','validation','oncall-opus','validation-opus']:
    rows=[]
    for f in sorted((R/group/'executions').glob('*/score.json')):
        if group=='oncall-opus' and not (R/group/'method-result.json').exists():continue
        row=json.loads(f.read_text());row['receipt']=str(f.relative_to(R));rows.append(row)
    data[group]=rows
controls={}
for label in ['null','oracle']:
    for f in (R/label).glob('run_*/summary.json'):
        s=json.loads(f.read_text());scene=s['scenes'][0]
        checks={k:v for k,v in scene['checks'].items() if v.get('required')}
        controls[label]={'passed':sum(c['passed'] for c in checks.values()),'required_total':len(checks),
            'valid':scene['invalidTrials']==0,'all_required_pass':scene['passed']==1,'startedAt':s['startedAt'],'finishedAt':s['finishedAt'],
            'receipt':str(f.relative_to(R))}
data['controls']=controls
cost=[json.loads(line) for line in (R/'cost.jsonl').read_text().splitlines()]
data['key_usage_initial']=cost[0]['usage'];data['key_usage_latest']=cost[-1]['usage']
data['metered_spend']=cost[-1]['usage']-cost[0]['usage'];data['metering_as_of']=cost[-1]['at']
groups={}
for phase in ['validation','validation-opus']:
    for row in data[phase]:
        version=row['run_id'].split('-',1)[0];key=(row['task'],version,phase)
        groups.setdefault(key,[]).append(row)
data['validation_summary']=[{'task':task,'version':version,'phase':phase,'valid_trials':sum(r['valid'] for r in rows),'trials':len(rows),
    'all_required_pass':sum(r['all_required_pass'] for r in rows),'required_passed':sum(r['required_passed'] for r in rows),
    'required_total':sum(r['required_total'] for r in rows),'wall_total_s':sum(r['wall_s'] for r in rows),
    'wall_mean_s':statistics.mean(r['wall_s'] for r in rows),'failed_checks':sorted({check for r in rows for check in r['failed']})}
    for (task,version,phase),rows in sorted(groups.items())]
(R/'results.json').write_text(json.dumps(data,indent=2))
lines=['# Measured results','','Raw inputs: per-rollout `score.json`, Ancha native state/trace/checks and model event streams. All required checks are deterministic; optional judges were skipped.','',
       '## Upstream reproduction','',f"Local deterministic demo: {demo['done']} tasks completed, {demo['failed']} failed, {demo['execution_count']} Python executions, {demo['editor_calls']} scripted editor calls, both parallel/sequential k=2 modes. See `demo/demo.json` and per-mode libraries.",
       '',f"Focused upstream suite: {test_match[1]} tests and {test_match[2]} subtests passed in {test_match[3]} seconds. See `upstream-tests.log`.",'',
       '## Controls','','| Agent | Required checks | Valid | All required passed |','|---|---:|---|---|']
for label,c in controls.items():lines.append(f"| {label} | {c['passed']}/{c['required_total']} | {c['valid']} | {c['all_required_pass']} |")
for phase,editor in [('oncall-k1','Sonnet 4.6'),('oncall-opus','Opus 4.8')]:
    if not data[phase]:continue
    lines+=['',f'## Harness² k=1 development task — {editor}','','| Run | Required checks | All required passed | Wall s | Failed checks |','|---|---:|---|---:|---|']
    for row in data[phase]:lines.append(f"| {row['run_id']} | {row['required_passed']}/{row['required_total']} | {row['all_required_pass']} | {row['wall_s']:.3f} | {', '.join(row['failed']) or 'none'} |")
    if phase=='oncall-opus':lines+=['','The baseline in this table is the exact reused original artifact; it is not a new execution. See `oncall-opus/shared-baseline.json`.']
lines+=['','## Frozen-harness validation','','| Task | Phase | Harness | Full passes / trials | Required checks | Mean wall s | Failed checks |','|---|---|---|---|---:|---:|---|']
for g in data['validation_summary']:lines.append(f"| {g['task']} | {g['phase']} | {g['version']} | {g['all_required_pass']}/{g['trials']} | {g['required_passed']}/{g['required_total']} | {g['wall_mean_s']:.3f} | {', '.join(g['failed_checks']) or 'none'} |")
lines+=['',f"OpenRouter initial usage: ${data['key_usage_initial']:.9f}; latest usage: ${data['key_usage_latest']:.9f}; difference: ${data['metered_spend']:.9f}. Metering as of {data['metering_as_of']}. Endpoint updates can lag.",
        '', 'OpenCode event cost sums are estimates and omit incidental title calls. The final settled key meter includes failed launchers, smoke calls, optimization and validation.']
(R/'results.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'sonnet_development_rows':len(data['oncall-k1']),'sonnet_validation_rows':len(data['validation']),'opus_development_rows':len(data['oncall-opus']),'opus_validation_rows':len(data['validation-opus']),'metered_spend':data['metered_spend']}))
