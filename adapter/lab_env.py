#!/usr/bin/env python3
"""Run lab commands with an isolated home and no inherited account credentials."""
import os
import sys
import json
import datetime
from pathlib import Path

from settings import ROOT, WORK, HOME, RECEIPTS, KEY_FILE, DOCKER_CONFIG
env = {
    'PATH': f"{ROOT}/.venv/bin:{WORK}/npm/bin:" + os.environ.get("PATH", os.defpath),
    'HOME': str(HOME),
    'DOCKER_CONFIG': DOCKER_CONFIG,
    'ANCHA_CREDENTIALS_FILE': str(HOME / 'no-login'),
    'npm_config_cache': str(WORK / 'npm-cache'),
    'npm_config_prefix': str(WORK / 'npm'),
    'UV_CACHE_DIR': str(HOME / 'uv-cache'),
    'TMPDIR': '/tmp',
    'LANG': 'en_US.UTF-8',
    'TZ': 'UTC',
    'PYTHONUNBUFFERED': '1',
}
for name, rel in [('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache'),('XDG_DATA_HOME','data'),('XDG_STATE_HOME','state')]:
    env[name] = str(HOME / rel)
for p in [HOME] + [Path(env[k]) for k in env if k.startswith('XDG_')]:
    p.mkdir(parents=True, exist_ok=True)
for name, value in os.environ.items():
    if name.startswith('H2_'):
        env[name] = value
args = sys.argv[1:]
if args and args[0] == '--paid':
    args.pop(0)
    key = os.environ.get('OPENROUTER_API_KEY')
    if not key:
        raise SystemExit('--paid requires OPENROUTER_API_KEY in the environment')
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(KEY_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, 'w') as out:
        out.write(key)
    env['OPENROUTER_API_KEY'] = key
    env['H2_KEY_FILE'] = str(KEY_FILE)
while args and '=' in args[0] and not args[0].startswith('-'):
    name, value = args.pop(0).split('=', 1)
    env[name] = value
if not args:
    raise SystemExit('Usage: lab_env.py [--paid] [NAME=value ...] command [args ...]')
receipt_dir = RECEIPTS
receipt_dir.mkdir(parents=True, exist_ok=True)
with (receipt_dir / 'commands.jsonl').open('a') as log:
    log.write(json.dumps({'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'cwd': os.getcwd(), 'argv': args, 'home': str(HOME), 'paid_key_loaded': 'OPENROUTER_API_KEY' in env}) + '\n')
os.execvpe(args[0], args, env)
