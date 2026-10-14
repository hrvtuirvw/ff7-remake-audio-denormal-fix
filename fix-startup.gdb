set pagination off
set confirm off
set print thread-events off
set debuginfod enabled off
handle SIGUSR1 nostop noprint pass
handle SIGUSR2 nostop noprint pass
handle SIGSEGV nostop noprint pass
python
import gdb
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import threading
import time

RVA = 0x3fe8259
argv = json.loads(os.environ['FF7_AUDIO_COMMAND'])
prefix = Path(os.environ['WINEPREFIX']).resolve()
exe = Path(argv[1]).parent / 'End/Binaries/Win64/ff7remake_.exe'
status_path = Path(os.environ['FF7_AUDIO_STATUS'])
status = {'applied': False, 'prefix': str(prefix), 'method': 'audio-thread FTZ/DAZ once; no code patch', 'started_at': time.time(), 'phase': 'initializing'}
status_path.write_text(json.dumps(status, indent=2))
attached = False
bp = None
timer = None
child = subprocess.Popen(argv, close_fds=False)

def owns(pid):
    """Yama-compatible: the debugger itself must be an ancestor."""
    seen = set()
    while pid > 1 and pid not in seen:
        if pid == os.getpid():
            return True
        seen.add(pid)
        text = Path('/proc/%d/status' % pid).read_text()
        pid = int(next(s for s in text.splitlines() if s.startswith('PPid:')).split()[1])
    return False

try:
    actual = hashlib.sha256(exe.read_bytes()).hexdigest()
    # The hash is diagnostic metadata, not an executable/build allowlist.
    deadline = time.monotonic() + 60
    target = None
    while time.monotonic() < deadline and child.poll() is None:
        for proc in Path('/proc').iterdir():
            if not proc.name.isdigit():
                continue
            try:
                if (proc / 'comm').read_text().strip() != 'ff7remake_.exe':
                    continue
                env = dict(s.split(b'=', 1) for s in (proc / 'environ').read_bytes().split(b'\0') if b'=' in s)
                if Path(os.fsdecode(env[b'WINEPREFIX'])).resolve() != prefix or not owns(int(proc.name)):
                    continue
                target = int(proc.name)
                break
            except (OSError, KeyError, StopIteration, ValueError):
                continue
        if target:
            break
        time.sleep(.1)
    if not target:
        raise RuntimeError('Owned game process not found within startup deadline')
    gdb.execute('attach %d' % target, to_string=True)
    attached = True
    base = None
    for line in Path('/proc/%d/maps' % target).read_text().splitlines():
        parts = line.split(None, 5)
        if len(parts) == 6 and parts[2] == '00000000' and parts[5] == str(exe):
            base = int(parts[0].split('-')[0], 16)
            break
    if base is None:
        raise RuntimeError('Expected executable image not found')
    address = base + RVA
    bp = gdb.Breakpoint('*0x%x' % address, temporary=True, internal=True)
    expired = threading.Event()
    def interrupt_wait():
        expired.set()
        os.kill(os.getpid(), signal.SIGINT)
    timer = threading.Timer(20, interrupt_wait)
    timer.daemon = True
    timer.start()
    gdb.execute('continue', to_string=True)
    timer.cancel()
    if expired.is_set() or int(gdb.parse_and_eval('$pc')) != address:
        raise RuntimeError('Mixer breakpoint not reached normally')
    tid = gdb.selected_thread().ptid[1]
    if tid == target:
        raise RuntimeError('Unexpected main-thread mixer; refusing initialization')
    before = int(gdb.parse_and_eval('$mxcsr'))
    gdb.execute('set $mxcsr = $mxcsr | 0x8040', to_string=True)
    after = int(gdb.parse_and_eval('$mxcsr'))
    if after != before | 0x8040:
        raise RuntimeError('Floating-point control readback failed')
    status.update(applied=True, phase='applied', pid=target, tid=tid, before=hex(before), after=hex(after), executable_sha256=actual)
except BaseException as exc:
    status['error'] = str(exc)
    status['phase'] = 'failed'
finally:
    if timer is not None:
        timer.cancel()
    if bp is not None and bp.is_valid():
        bp.delete()
    if attached:
        try:
            gdb.execute('detach', to_string=True)
        except gdb.error as exc:
            status['detach_error'] = str(exc)
    status_path.write_text(json.dumps(status, indent=2))
    print(json.dumps(status))
    if not status['applied']:
        subprocess.run(['/usr/bin/notify-send', 'FF7 REMAKE', '音声最適化を適用できませんでした。audio-fp-status.jsonを確認してください。'], check=False)
    result = child.wait()
    print('UMU exit:', result)
    gdb.execute('quit %d' % (result if result >= 0 else 128 - result))
end
