# FF7 Remake Audio Denormal Fix v0.1.0

[日本語](README.ja.md) | [Changelog](CHANGELOG.md)

A mod that addresses audio dropouts in **FINAL FANTASY VII REMAKE**.

In the environment investigated, subnormal floating-point values (denormals)
occurred during audio mixing and caused SSE operations to slow down dramatically.
This mod avoids that delay by enabling the audio-processing thread's FTZ/DAZ
flags when the game starts.

This is an experimental release tested only on Linux/Proton with a specific
game build. I made it because I needed it, and I am sharing it in case others
are experiencing the same problem.

Aerith-taso is so cute. Aerith-taso.

## How it works

At startup, GDB enables FTZ (Flush to Zero) and DAZ (Denormals Are Zero) on the
target audio-processing thread.

The debugger detaches afterward. The GDB process remains alive to wait for UMU
to exit, but it does not keep measuring or monitoring the game during gameplay.

## Tested environment

The following configuration was tested:

| Item | Environment |
|---|---|
| OS | Linux x86-64 |
| Proton | CachyOS 11.0-20261005-slr |
| Game | FF7 Remake EXE build 1.0.0.6 |

Target executable:

```text
End/Binaries/Win64/ff7remake_.exe
```

The same approach may work on Windows, but it has not been tested there. Other
executables have not been tested either.

FTZ/DAZ is set only once at startup. If the game recreates the audio thread,
the flags are not reapplied; restart the game in that case.

## Installation

Manual installation only. There is no automatic integration for launching
directly through Steam.

### Requirements

- Python 3 (`/usr/bin/python3`)
- GDB with Python support (`/usr/bin/gdb`)
- `/usr/bin/umu-run`

### Setup

1. Quit the game and back up your current launch script.
2. Extract the distribution ZIP to a permanent directory. Keep `fix-launch.py`
   and `fix-startup.gdb` in the same directory.
3. Change the UMU invocation in the launch script.

Before:

```sh
/usr/bin/umu-run "$game/ff7remake.exe" -dx11 "$@"
```

After:

```sh
/usr/bin/python3 "$fixdir/fix-launch.py" /usr/bin/umu-run "$game/ff7remake.exe" -dx11 "$@"
```

Set `$fixdir` to the absolute path of the directory where you extracted the mod.

Preserve existing environment variables, launch arguments and performance
settings. If you use an outer wrapper such as `game-performance`, keep it in
place. Use the `WINEPREFIX` already configured by your normal launcher.

Running with sudo or changing system-wide ptrace settings is not required.

### Confirming application

Launch the game using your usual shortcut. In the **parent of the resolved
`WINEPREFIX` directory**, check:

```text
logs/audio-fp-status.json
```

These values indicate successful application:

```json
{
  "applied": true,
  "phase": "applied"
}
```

The same directory contains `logs/audio-fp-launch.log`. Both log files are
overwritten on each launch.

After confirming application, test BGM and dialogue in a gameplay scene that
previously had dropouts.

If GDB itself fails to start, the game may stop before launching. Check the
dependencies or restore the original launcher. Failure notifications require
`notify-send`.

## Uninstallation

Quit the game and restore the original launch script or its backup.

FTZ/DAZ is changed only in the running process, so the next launch without the
helper returns to the original state. Leaving the mod files on disk does not
activate it unless the launcher calls them. No game-file or save-data restoration
is needed.

## Results

In an environment with audio dropouts, the workaround was compared ON → OFF → ON
in the same game process and scene.

Host audio was recorded at 48 kHz stereo. The metric counts spans where both
channels are simultaneously exactly zero for at least 10 ms, excluding initial
recording-start silence.

| Condition | Recording | Zero spans ≥10 ms |
|---|---:|---:|
| ON | 30 seconds | 0 |
| OFF | 30 seconds | 126 |
| ON again | 30 seconds | 0 |

Disabling the workaround reproduced the dropouts; enabling it again removed
them from this measurement.

The original Pulse path also produced zero such gaps in a 30-second recording.
A separate 15-second Wine Pulse trace recorded zero underflows across 1,500
`ReleaseBuffer` calls.

## Reference

For FTZ/DAZ behavior, see Intel's official documentation:

[Intel: Set the FTZ and DAZ Flags](https://www.intel.com/content/www/us/en/docs/dpcpp-cpp-compiler/developer-guide-reference/2025-0/set-the-ftz-and-daz-flags.html)

## License

Released under the [MIT License](LICENSE). No game files are included.

This is an unofficial, independently developed tool, not affiliated with Square
Enix. It comes without a warranty; use it at your own discretion.
