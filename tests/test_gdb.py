"""Real-GDB regression fixtures; no game files, Wine, sudo or ptrace changes.

Run: python3 -m unittest discover -s tests -v
Requires Linux x86-64, gcc and Python-enabled GDB.
These synthetic executables are deliberately not hash/signature matches.
"""
import json
import os
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROFILES = {'remake': ('ff7remake', '0x3fe8259'),
            'rebirth': ('ff7rebirth', '0x736ab0')}
SOURCE = r'''
#include <pthread.h>
#include <stdio.h>
#include <unistd.h>
#include <xmmintrin.h>
__attribute__((section(".mixer"), aligned(1), noinline))
void mixer(void) { __asm__ volatile("nop; nop; nop"); }
static unsigned before, after;
static void *worker(void *unused) {
    _mm_setcsr(_mm_getcsr() & ~0x8040u);
    before = _mm_getcsr();
    for (int i = 0; i < 500; ++i) {
        mixer();
        after = _mm_getcsr();
        if ((after & 0x8040u) == 0x8040u) break;
        usleep(10000);
    }
    return NULL;
}
int main(void) {
    _mm_setcsr(_mm_getcsr() & ~0x8040u);
    unsigned main_before = _mm_getcsr();
    usleep(300000);
#ifdef MAIN_ONLY
    mixer();
    unsigned main_after = _mm_getcsr();
    printf("MAIN_ONLY %x %x\n", main_before, main_after);
    return main_before == main_after ? 0 : 4;
#else
    pthread_t thread;
    if (pthread_create(&thread, NULL, worker, NULL)) return 5;
    pthread_join(thread, NULL);
    unsigned main_after = _mm_getcsr();
    printf("WORKER_ONLY %x %x %x %x\n", main_before, main_after, before, after);
    return main_before == main_after && (before & 0x8040u) == 0 &&
           (after & 0x8040u) == 0x8040u ? 0 : 3;
#endif
}
'''


@unittest.skipUnless(sys.platform == 'linux' and platform.machine() == 'x86_64' and shutil.which('gcc') and shutil.which('gdb'),
                     'Linux, gcc and GDB required')
class GDBTests(unittest.TestCase):
    def exercise(self, profile, *, main_only=False, wrong_prefix=False, direct=False):
        stem, rva = PROFILES[profile]
        with tempfile.TemporaryDirectory(prefix='ff7-fp-test-') as name:
            tmp = Path(name)
            exe = tmp / 'game/End/Binaries/Win64' / (stem + '_.exe')
            exe.parent.mkdir(parents=True)
            source = tmp / 'fixture.c'
            source.write_text(SOURCE)
            subprocess.run(['gcc', '-O0', '-g', '-fPIE', '-pie', '-pthread',
                            *(['-DMAIN_ONLY'] if main_only else []),
                            '-Wl,--section-start=.mixer='+rva, str(source), '-o', str(exe)],
                           check=True, capture_output=True)
            launcher = tmp / 'game' / (stem + '.exe')
            launcher.write_text('import os\n'+
                ('os.environ["WINEPREFIX"] += "/other"\n' if wrong_prefix else '')+
                'os.execv('+repr(str(exe))+', ['+repr(str(exe))+'])\n')
            prefix = tmp / 'prefix'
            prefix.mkdir()
            status_file = tmp / 'status.json'
            env = dict(os.environ, WINEPREFIX=str(prefix),
                       FF7_AUDIO_COMMAND=json.dumps(['/usr/bin/env', str(exe)] if direct else [sys.executable, str(launcher)]),
                       FF7_AUDIO_STATUS=str(status_file))
            env.pop('FF7_AUDIO_GAME', None)
            run = subprocess.run(['/usr/bin/gdb', '-nx', '-nh', '-q', '-batch',
                                  '-x', str(ROOT/'fix-startup.gdb')], env=env,
                                 capture_output=True, text=True, timeout=30)
            status = json.loads(status_file.read_text())
            self.assertNotIn('detach_error', status, run.stdout+run.stderr)
            self.assertEqual(status['game'], profile)
            self.assertEqual(status['breakpoint_rva'], rva)
            if main_only:
                self.assertFalse(status['applied'])
                self.assertIn('main-thread', status['error'])
                self.assertIn('MAIN_ONLY 1f80 1f80', run.stdout)
                self.assertEqual(run.returncode, 0, run.stdout+run.stderr)
            elif wrong_prefix:
                self.assertFalse(status['applied'])
                self.assertIn('Owned game process not found', status['error'])
                self.assertEqual(run.returncode, 3, run.stdout+run.stderr)
            else:
                self.assertTrue(status['applied'], run.stdout+run.stderr)
                self.assertNotEqual(status['pid'], status['tid'])
                self.assertEqual(int(status['after'],16), int(status['before'],16)|0x8040)
                self.assertIn('WORKER_ONLY 1f80 1f80 1f80 9fc0', run.stdout)
                self.assertEqual(run.returncode, 0, run.stdout+run.stderr)

    def test_remake_worker_only(self):
        self.exercise('remake')

    def test_rebirth_worker_only(self):
        self.exercise('rebirth')

    def test_rebirth_direct_executable(self):
        self.exercise('rebirth', direct=True)

    def test_refuses_main_thread(self):
        self.exercise('rebirth', main_only=True)

    def test_refuses_other_prefix(self):
        self.exercise('rebirth', wrong_prefix=True)


if __name__ == '__main__':
    unittest.main()
