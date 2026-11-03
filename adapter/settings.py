"""Paths for the experiment; all runtime state defaults to .work/."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get('H2_WORKDIR', ROOT / '.work')).expanduser().resolve()
RECEIPTS = Path(os.environ.get('H2_RECEIPTS', WORK / 'receipts')).expanduser().resolve()
SCENARIO = Path(os.environ.get('H2_SCENARIO', ROOT / 'scenario')).expanduser().resolve()
HOME = WORK / 'home'
KEY_FILE = Path(os.environ.get('H2_KEY_FILE', HOME / 'openrouter-key')).expanduser().resolve()
DOCKER_CONFIG = os.environ.get('DOCKER_CONFIG', str(Path.home() / '.docker'))
