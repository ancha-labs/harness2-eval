"""Ancha command agent: materialize a candidate and run OpenCode against local tools."""
import json
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

from settings import ROOT, HOME, KEY_FILE, DOCKER_CONFIG
from harness2.core import tree
from harness2.substrate.opencode import OPENCODE_SURFACE

harness = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()
work.mkdir(parents=True, exist_ok=True)
content = tree.read_tree(OPENCODE_SURFACE, harness)
prompt = tree.always_on_text(OPENCODE_SURFACE, content)
for rel, text in content.items():
    if rel.startswith('skills/'):
        dest = work / '.opencode' / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text)
    elif rel.startswith('scripts/'):
        dest=work/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
model = os.environ.get('H2_EXECUTOR_MODEL', 'openrouter/anthropic/claude-haiku-5.5')
config = {
    '$schema': 'https://opencode.ai/config.json',
    'model': model,
    'agent': {'oncall': {'mode': 'primary', 'prompt': prompt, 'steps': 55}},
    'permission': {'*': 'deny', 'world_*': 'allow', 'skill': 'allow', 'read': {'*': 'deny', str(work) + '/**': 'allow'}},
    'mcp': {'world': {'type': 'local', 'command': ['node', str(ROOT/'bridge/tools-mcp.ts')], 'environment': {'OPENROUTER_API_KEY': ''}, 'timeout': 70000}},
    'share': 'disabled',
    'provider': {'openrouter': {'models': {'anthropic/claude-haiku-5.5': {'name': 'Claude Haiku 5.5', 'limit': {'context': 1000000, 'output': 16000}, 'cost': {'input': 0.1, 'output': 0.5}}}}},
}
(work/'opencode.json').write_text(json.dumps(config,indent=2))
env = dict(os.environ)
env['HOME'] = str(HOME)
for name, leaf in [('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache'),('XDG_DATA_HOME','data'),('XDG_STATE_HOME','state')]:
    env[name] = str(HOME/leaf)
env['ANCHA_CREDENTIALS_FILE'] = str(HOME/'no-login')
env['DOCKER_CONFIG'] = DOCKER_CONFIG
env['OPENROUTER_API_KEY'] = os.environ.get('OPENROUTER_API_KEY') or KEY_FILE.read_text().strip()
env['OPENCODE_DISABLE_AUTOUPDATE'] = 'true'
env['OPENCODE_DISABLE_CLAUDE_CODE'] = 'true'
env['OPENCODE_CONFIG_DIR'] = str(HOME/'config/opencode')
# Keep every XDG directory in the dedicated lab home, including individual sessions.
for name, leaf in [('XDG_DATA_HOME','data'),('XDG_STATE_HOME','state')]:
    identity=hashlib.sha256(str(work).encode()).hexdigest()[:16]
    env[name] = str(HOME/leaf/'probes'/identity)
command = ['opencode','run','--dir',str(work),'--agent','oncall','--model',model,'--format','json',os.environ.get('ANCHA_TASK','Handle the incident using the provided local tools.')]
result = subprocess.run(command,cwd=work,env=env,timeout=540)
raise SystemExit(result.returncode)
