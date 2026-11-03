"""Harness² -> OpenCode -> Ancha local native twins; deterministic verdict selection.

Core Harness² sees only trajectories/deliverables. Scores are stored outside that
context and used by the experiment's external selection step, not the core composer.
"""
import argparse
import datetime
import json
import os
import re
import shutil
import shlex
import subprocess
import sys
import threading
import time
from pathlib import Path

from settings import ROOT, WORK, RECEIPTS, SCENARIO, HOME
from harness2.core import recursion, tree
from harness2.core.proposer import Proposer, _opencode_cost, _opencode_stdout
from harness2.core.spec import BenchPrompts, BenchSpec, ChannelSpec, RunView
from harness2.substrate.opencode import OpencodeSubstrate

EXECUTOR='openrouter/anthropic/claude-haiku-5.5'
EDITOR=os.environ.get('H2_EDITOR_MODEL','openrouter/anthropic/claude-sonnet-4.6')

def cost(label):
    subprocess.run([sys.executable,str(ROOT/'adapter/cost.py'),label],check=True)

def no_model_key():
    return {k:v for k,v in os.environ.items() if k != 'OPENROUTER_API_KEY'}

class BinaryProposer(Proposer):
    """Same core proposer contract, with npm's OpenCode binary instead of Bun source."""
    def _opencode(self,cwd,mission,system,wall):
        cwd=cwd.resolve()
        cost('before-editor-'+cwd.name)
        (cwd/'MISSION.md').write_text((system+'\n\n' if system else '')+mission)
        (cwd/'output').mkdir(exist_ok=True)
        # OpenCode's no-git project has Instance.worktree='/' and edit/write
        # permissions match path.relative(worktree, filepath), unlike read.
        # Preserve exact workspace scope in that namespace, including canonical paths.
        relative_root=str(cwd).lstrip('/')
        config={'agent':{'build':{'steps':self.spec.steps}},'share':'disabled','permission':{
            '*':'deny','read':{str(cwd):'allow',str(cwd)+'/**':'allow'},'glob':'allow','grep':'allow',
            'edit':{relative_root+'/context/harness/**':'allow',relative_root+'/output/**':'allow'},
            'external_directory':'deny',
        }}
        (cwd/'opencode.json').write_text(json.dumps(config,indent=2))
        env=self.env()
        env['OPENCODE_DISABLE_AUTOUPDATE']='true'
        env['OPENCODE_DISABLE_CLAUDE_CODE']='true'
        env['XDG_DATA_HOME']=str(HOME/'data/editors'/cwd.name)
        env['XDG_STATE_HOME']=str(HOME/'state/editors'/cwd.name)
        prompt='Read MISSION.md and the supplied context. Edit context/harness/ as requested. Reply with the required notes, and save the same reply in output/answer.md. Do not attempt shell commands or network access.'
        start=time.monotonic()
        raw=RECEIPTS/'editor-raw';raw.mkdir(exist_ok=True)
        (raw/(cwd.name+'.config.json')).write_text(json.dumps(config,indent=2))
        stdout=raw/(cwd.name+'.jsonl');stderr=raw/(cwd.name+'.stderr')
        try:
            with stdout.open('w') as out,stderr.open('w') as err:
                p=subprocess.run(['opencode','run','--dir',str(cwd),'--model',self.spec.model,'--format','json',prompt],cwd=cwd,env=env,text=True,stdout=out,stderr=err,timeout=wall)
        finally:
            cost('after-editor-'+cwd.name)
        (raw/(cwd.name+'.timing.json')).write_text(json.dumps({'wall_s':time.monotonic()-start,'exit_code':p.returncode}))
        output=stdout.read_text()
        text,error=_opencode_stdout(output)
        answer=cwd/'output/answer.md'
        if not error and answer.is_file():text=answer.read_text()
        return text,_opencode_cost(output),error

class AnchaAdapter:
    def __init__(self,name='oncall-k1'):
        self.root=RECEIPTS/name
        self.root.mkdir(parents=True,exist_ok=True)
        self.substrate=OpencodeSubstrate()
        channel=ChannelSpec('opencode',EDITOR,effort='',steps=35,timeout=300)
        self.spec=BenchSpec(name='ancha-oncall',runs_root=self.root,install_mode='workspace_config',
            prompts=BenchPrompts(work='handle service incidents using PagerDuty, Datadog, GitHub, and Slack',
                inv_levers='Planning, tool use, communication, and checking current evidence.',
                dom_levers='Incident investigation, repair, deployment observation, and team communication.',
                yardstick='Follow the task request and corroborate conclusions with current tool observations.'),
            channels={'proposer':channel,'selector':channel})
        self._lock=threading.Lock()
        base={p:'' for p in self.substrate.surface().always_on}
        original=(SCENARIO/'agent-v1.ts').read_text()
        base['systemprompt.md']=re.search(r'const SYSTEM = `(.+?)`;',original,re.S).group(1)+'\n'
        base['tool_descriptions/tool_guidance.md']='The world MCP server exposes the on-call tools. Use those tools to do the work. The finish tool records your summary; after calling it, stop. All services are local simulation twins.\n'
        tree.write_tree(self.substrate.surface(),base,self.base_harness())
        self.rows=[]

    def tasks(self,split='all'):return ['status-request','bad-deploy','false-alarm']
    def domain_of(self,task_id):return 'oncall'
    def task_prompt(self,task_id):
        # Task text only; no scene, seed, check definitions or oracle scripts enter context.
        text=(SCENARIO/'scenes/incidents'/task_id/'scene.yaml').read_text()
        part=text.split("task: '",1)[1].split("'\nseed:",1)[0]
        return ' '.join(part.split())
    def task_files(self,task_id):return None
    def base_harness(self):return self.root/'base-harness'
    def validate_tree(self,value):
        # This adapter activates always-on prompts and skills only. Reject unsupported
        # components rather than silently evaluating an edit which never runs.
        for rel in value:
            if rel not in self.substrate.surface().always_on and not rel.startswith('skills/') and not rel.endswith('/README.md'):
                raise ValueError('This experiment activates prompts and skills only: '+rel)

    def execute(self,task_id,harness_dir,run_id,*,timeout=None,seed='l18-fixed'):
        with self._lock:
            directory=self.root/'executions'/run_id
            if (directory/'score.json').exists():return directory
            directory.mkdir(parents=True,exist_ok=True)
            harness=harness_dir or self.base_harness()
            work=WORK/'probe-work'/self.root.name/run_id
            if work.exists():shutil.rmtree(work)
            command=shlex.join([sys.executable,str(ROOT/'adapter/probe-agent.py'),str(harness),str(work)])
            scene=SCENARIO/'scenes/incidents'/task_id/'scene.yaml'
            args=['ancha','--local','run',str(scene),'--agent',command,'-n','1','--parallel','1','--seed',seed,'--out',str(directory/'ancha'),'--json']
            for name in ['H2_WORKDIR','H2_RECEIPTS','H2_SCENARIO','H2_KEY_FILE','H2_EXECUTOR_MODEL']:
                if name in os.environ:
                    args.extend(['--pass-env',name])
            (directory/'command.json').write_text(json.dumps(args,indent=2))
            cost('before-probe-'+run_id)
            start=time.monotonic()
            p=subprocess.run(args,cwd=SCENARIO,env=no_model_key(),text=True,capture_output=True,timeout=timeout or 650)
            wall=time.monotonic()-start
            (directory/'ancha.jsonl').write_text(p.stdout)
            (directory/'ancha.stderr').write_text(p.stderr)
            cost('after-probe-'+run_id)
            summary_files=list((directory/'ancha').glob('run_*/summary.json'))
            if not summary_files:raise RuntimeError('Ancha produced no summary: '+p.stderr[-300:])
            summary=json.loads(summary_files[0].read_text())
            result_dir=summary_files[0].parent/f'trial-{task_id}-1'
            checks=json.loads((result_dir/'checks.json').read_text())
            required=summary['scenes'][0]['checks']
            ids=[key for key,c in required.items() if c.get('required')]
            passed=sum(required[key]['passed'] for key in ids)
            valid=summary['scenes'][0].get('invalidTrials',0)==0
            raw=(result_dir/'agent.log').read_text(errors='replace')
            rendered=[];answers=[]
            for line in raw.splitlines():
                try:event=json.loads(line)
                except ValueError:continue
                part=event.get('part',{})
                if event.get('type')=='tool_use':
                    state=part.get('state',{})
                    rendered.append('[ACTION] '+part.get('tool','')+' '+json.dumps(state.get('input',{})))
                    rendered.append('[OBSERVATION] '+str(state.get('output','')))
                elif event.get('type')=='text':
                    answers.append(part.get('text',''));rendered.append('[ASSISTANT] '+part.get('text',''))
                elif event.get('type')=='error':rendered.append('[ERROR] '+json.dumps(event))
            (directory/'trajectory.md').write_text('\n'.join(rendered))
            (directory/'answer.txt').write_text('\n'.join(answers))
            token_cost=_opencode_cost(raw)
            score={'task':task_id,'run_id':run_id,'scene_seed':seed,'valid':valid,'required_passed':passed,'required_total':len(ids),
                'score':passed/len(ids) if valid and ids else None,'all_required_pass':valid and bool(ids) and passed==len(ids),
                'failed':[key for key in ids if required[key]['passed']==0],
                'checks':{key:required[key] for key in ids},'wall_s':wall,'opencode_reported_usd':token_cost,
                'executor':EXECUTOR,'ancha_exit':p.returncode,'optional_judge':'skipped; no key in Ancha parent'}
            (directory/'score.json').write_text(json.dumps(score,indent=2))
            self.rows.append(score)
            print(json.dumps(score),flush=True)
            return directory

    def delivered(self,directory):return bool((directory/'answer.txt').read_text().strip())
    def trajectory(self,directory,*,obs_trunc):return (directory/'trajectory.md').read_text()
    def deliverable_text(self,directory):return (directory/'answer.txt').read_text()
    def deliverable_files(self,directory):return {'answer.txt':self.deliverable_text(directory)}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['baseline','optimize','validate']);parser.add_argument('--name',default='oncall-k1');parser.add_argument('--harness');parser.add_argument('--task',default='status-request');parser.add_argument('--repeats',type=int,default=1)
    args=parser.parse_args();adapter=AnchaAdapter(args.name)
    started=time.monotonic()
    if args.action=='baseline':
        adapter.execute(args.task,None,'baseline-'+args.task)
    elif args.action=='optimize':
        base_dir=adapter.execute(args.task,None,'baseline-'+args.task)
        base=[RunView(label='base1',run_id='baseline-'+args.task,run_dir=base_dir,ok=True,delivered=adapter.delivered(base_dir))]
        proposer=BinaryProposer(adapter.spec.channels['proposer'],audit_dir=adapter.root/'editor-audit',attempts=1)
        result=recursion.run_parallel(args.task,1,base,adapter=adapter,prop=proposer,work_dir=adapter.root/'method',
            run_id_of=lambda label:'probe-'+args.task+'-'+label,
            base_tree=tree.read_tree(adapter.substrate.surface(),adapter.base_harness()),propose_workers=1,rollout_workers=1)
        (adapter.root/'method-result.json').write_text(json.dumps(result.to_dict(),indent=2))
        # Explicit extension: deterministic Ancha score chooses among *executed* trees.
        candidates=[]
        for label,view in result.rollouts.items():
            score=json.loads((view.run_dir/'score.json').read_text())
            if score['valid'] and score['score'] is not None:
                candidates.append((score['score'],label,score,view))
        candidates.sort(key=lambda c:(c[0],c[1]=='agg1',c[1]=='base1'),reverse=True)
        if not candidates:raise RuntimeError('No valid Ancha scores for selection')
        _,label,score,view=candidates[0]
        selected=result.trees.get(label,tree.read_tree(adapter.substrate.surface(),adapter.base_harness()))
        tree.write_tree(adapter.substrate.surface(),selected,adapter.root/'selected-harness')
        (adapter.root/'selection.json').write_text(json.dumps({'policy':'maximum fraction of required Ancha checks; ties prefer composition, then baseline','chosen_label':label,'score':score,'core_composer_receives_verdicts':False,'core_ok':result.ok},indent=2))
    else:
        for task in adapter.tasks():
            for n in range(1,args.repeats+1):
                adapter.execute(task,Path(args.harness).resolve() if args.harness else None,f'validation-{task}-{n}')
    (adapter.root/(args.action+'-timing.json')).write_text(json.dumps({'wall_s':time.monotonic()-started,'at':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))

if __name__=='__main__':main()
