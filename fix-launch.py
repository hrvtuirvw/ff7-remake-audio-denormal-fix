#!/usr/bin/env python3
"""Run the normal UMU command beneath a bounded, audio-only FP initializer."""
import json
import os
from pathlib import Path
import sys

if len(sys.argv) < 3 or sys.argv[1] != '/usr/bin/umu-run':
    raise SystemExit('Expected the existing UMU launch command')
prefix = Path(os.environ['WINEPREFIX']).resolve()
logs = prefix.parent / 'logs'
logs.mkdir(exist_ok=True)
os.environ['FF7_AUDIO_COMMAND'] = json.dumps(sys.argv[1:])
os.environ['FF7_AUDIO_STATUS'] = str(logs / 'audio-fp-status.json')
log = os.open(logs / 'audio-fp-launch.log', os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
os.dup2(log, 1)
os.dup2(log, 2)
os.close(log)
script = Path(__file__).with_name('fix-startup.gdb')
os.execv('/usr/bin/gdb', ['gdb', '-nx', '-nh', '-q', '-batch', '-x', str(script)])
