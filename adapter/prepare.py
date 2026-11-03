import json
import os
import shutil
import urllib.request
from pathlib import Path
from html.parser import HTMLParser

from settings import ROOT, WORK, SCENARIO, RECEIPTS
# The checked-in scenario is already prepared. An optional source uses the same
# copy layout, with .demo-log supported for the original example export.
demo = SCENARIO
demo.mkdir(parents=True, exist_ok=True)
source = Path(os.environ.get('H2_SCENARIO_SOURCE', SCENARIO)).expanduser().resolve()
if source != demo:
    for name in ['ancha.yaml', 'package.json', 'package-lock.json']:
        shutil.copy2(source / name, demo / name)
    for version in [1, 2, 3]:
        for name in [f'agent-v{version}.ts'] + ([f'tools-v{version}.ts'] if version <= 2 else []):
            candidate = source / name
            shutil.copy2(candidate if candidate.exists() else source / '.demo-log' / name, demo / name)
    tools = source / 'tools-v1.ts'
    shutil.copy2(tools if tools.exists() else source / '.demo-log/tools-v1.ts', demo / 'tools.ts')
    shutil.copytree(source / 'scenes', demo / 'scenes', dirs_exist_ok=True)
    if (source / 'node_modules').exists():
        shutil.copytree(source / 'node_modules', demo / 'node_modules', dirs_exist_ok=True)
receipts = RECEIPTS
receipts.mkdir(parents=True, exist_ok=True)
class Text(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]
    def handle_data(self, text): self.parts.append(text)
for name,url in [('paper','https://arxiv.org/html/2610.14224v1'),('models','https://openrouter.ai/api/v1/models')]:
    with urllib.request.urlopen(url, timeout=45) as response: raw=response.read()
    (receipts / (name + ('.html' if name=='paper' else '.json'))).write_bytes(raw)
    if name=='paper':
        p=Text();p.feed(raw.decode());(receipts/'paper.txt').write_text('\n'.join(p.parts))
    else:
        models=json.loads(raw)['data']
        selected=[{k:m.get(k) for k in ['id','name','context_length','pricing','supported_parameters']} for m in models if m['id'] in ['google/gemini-2.5-flash','google/gemini-2.5-flash-lite','anthropic/claude-sonnet-4.6','anthropic/claude-sonnet-4.5','openai/gpt-4.1-mini','qwen/qwen3-coder','anthropic/claude-haiku-5.5','google/gemini-3.5-flash']]
        (receipts/'selected-models.json').write_text(json.dumps(selected,indent=2))
        print(json.dumps(selected,indent=2))
