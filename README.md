# FF7 Remake Audio Denormal Fix v0.1.0

[English](#english) | [日本語](#日本語) | [Changelog](CHANGELOG.md)

A mod that addresses audio dropouts in **FINAL FANTASY VII REMAKE**.

『FINAL FANTASY VII REMAKE』の音声が途切れる問題に対処するMODです。

---

## English

In the environment investigated, subnormal floating-point values (denormals)
occurred during audio mixing and caused SSE operations to slow down dramatically.
This mod avoids that delay by enabling the audio-processing thread's FTZ/DAZ
flags when the game starts.

This is an experimental release tested only on Linux/Proton with a specific
game build. I made it because I needed it, and I am sharing it in case others
are experiencing the same problem.

Aerith-taso is so cute. Aerith-taso.

### How it works

At startup, GDB enables FTZ (Flush to Zero) and DAZ (Denormals Are Zero) on the
target audio-processing thread.

The debugger detaches afterward. The GDB process remains alive to wait for UMU
to exit, but it does not keep measuring or monitoring the game during gameplay.

### Tested environment

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

### Installation

Manual installation only. There is no automatic integration for launching
directly through Steam.

#### Requirements

- Python 3 (`/usr/bin/python3`)
- GDB with Python support (`/usr/bin/gdb`)
- `/usr/bin/umu-run`

#### Setup

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

#### Confirming application

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

### Uninstallation

Quit the game and restore the original launch script or its backup.

FTZ/DAZ is changed only in the running process, so the next launch without the
helper returns to the original state. Leaving the mod files on disk does not
activate it unless the launcher calls them. No game-file or save-data restoration
is needed.

### Results

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

### Reference

For FTZ/DAZ behavior, see Intel's official documentation:

[Intel: Set the FTZ and DAZ Flags](https://www.intel.com/content/www/us/en/docs/dpcpp-cpp-compiler/developer-guide-reference/2025-0/set-the-ftz-and-daz-flags.html)

### License

Released under the [MIT License](LICENSE). No game files are included.

This is an unofficial, independently developed tool, not affiliated with Square
Enix. It comes without a warranty; use it at your own discretion.

---

## 日本語

調査した環境では、音声ミキサーの処理中に非正規化浮動小数点数（denormal）が発生し、SSE演算が極端に遅くなる現象を確認しました。

このMODは、ゲーム起動時に音声処理スレッドのFTZ/DAZフラグを有効にすることで、その遅延を回避します。

現在はLinux/Proton環境かつ特定のゲームビルドでのみ検証した実験版です。

自分が必要だったので作成しましたが、同じ現象で困っている人がいるかもしれないので公開しておきます。

エアリスたそかわいいよ。エアリスたそ。


### 仕組み

ゲーム起動時にGDBを使い、対象の音声処理スレッドに対してFTZ（Flush to Zero）とDAZ（Denormals Are Zero）を設定します。

設定後はデバッガを切り離します。GDBプロセス自体はUMUの終了を待つために残りますが、ゲーム中に継続的な計測や監視を行うわけではありません。

### 動作確認環境

以下の構成で検証しています。

| 項目 | 環境 |
|---|---|
| OS | Linux x86-64 |
| Proton | CachyOS 11.0-20261005-slr |
| ゲーム | FF7 Remake EXE build 1.0.0.6 |

対象EXE：

```text
End/Binaries/Win64/ff7remake_.exe
```

Windowsでも同じ方法で対処できる可能性はありますが、未検証です。異なるEXEでの動作も未確認です。

なお、FTZ/DAZの設定は起動時の1回だけです。途中で音声スレッドが作り直された場合は再適用されないため、ゲームを再起動する必要があります。

### インストール

現時点では手動導入のみ対応しています。Steamからの直接起動に自動で組み込む機能はありません。

#### 必要なもの

- Python 3（`/usr/bin/python3`）
- Python対応のGDB（`/usr/bin/gdb`）
- `/usr/bin/umu-run`

#### 導入手順

1. ゲームを終了し、現在使っている起動スクリプトをバックアップします。
2. 配布ZIPを任意の固定ディレクトリに展開します。`fix-launch.py`と`fix-startup.gdb`は同じディレクトリに置いてください。
3. 起動スクリプトのUMU実行部分を変更します。

変更前：

```sh
/usr/bin/umu-run "$game/ff7remake.exe" -dx11 "$@"
```

変更後：

```sh
/usr/bin/python3 "$fixdir/fix-launch.py" /usr/bin/umu-run "$game/ff7remake.exe" -dx11 "$@"
```

`$fixdir`にはMODを展開したディレクトリの絶対パスを指定してください。

既存の環境変数や起動引数、性能制御の設定はそのまま残します。`game-performance`などを使っている場合も、外側の構成を変える必要はありません。

`WINEPREFIX`も普段のランチャーで設定しているものを使用してください。

sudoでの実行や、システム全体のptrace設定変更は不要です。

#### 適用の確認

いつものショートカットからゲームを起動します。

`WINEPREFIX`の実体ディレクトリの親にある、以下のファイルを確認してください。

```text
logs/audio-fp-status.json
```

次の値が記録されていれば適用成功です。

```json
{
  "applied": true,
  "phase": "applied"
}
```

起動ログは同じ場所の`logs/audio-fp-launch.log`に出力されます。これらのログは起動のたびに上書きされます。

適用を確認できたら、実際に音が途切れていた場面でBGMやボイスを確認してください。

GDBの起動自体に失敗した場合は、ゲームが起動する前に停止することがあります。その場合は依存関係を確認するか、元のランチャーに戻してください。

適用失敗時のデスクトップ通知には`notify-send`が必要です。

### アンインストール

ゲームを終了し、変更した起動スクリプトを元に戻すだけです。バックアップしたランチャーを復元しても構いません。

FTZ/DAZの変更は実行中のプロセスに対して行うため、次回起動時には元の状態に戻ります。

MODのファイルが残っていても、ランチャーから呼び出さなければ適用されません。ゲームファイルやセーブデータを復元する必要もありません。

### 検証結果

音切れが発生していた環境で、同じゲームプロセス・同じ場面のまま、修正ON → OFF → ONの順に比較しました。

48 kHzステレオでホスト側の音声を録音し、左右両チャンネルが同時に10 ms以上連続してゼロになった区間を数えています。録音開始時の無音区間は含めていません。

| 条件 | 録音時間 | 10 ms以上のゼロ区間 |
|---|---:|---:|
| 修正ON | 30秒 | 0 |
| 修正OFF | 30秒 | 126 |
| 再びON | 30秒 | 0 |

修正を無効にすると音声の途切れが再発し、再度有効にすると検出されなくなりました。

元のPulse経路でも30秒間の録音でゼロ区間は0件でした。また、15秒間のWine Pulseトレースでは、1,500回の`ReleaseBuffer`呼び出しに対してunderflowは0件でした。

### 参考資料

FTZ/DAZの動作については、Intelの公式ドキュメントを参照してください。

[Intel: Set the FTZ and DAZ Flags](https://www.intel.com/content/www/us/en/docs/dpcpp-cpp-compiler/developer-guide-reference/2025-0/set-the-ftz-and-daz-flags.html)

### ライセンス

[MIT License](LICENSE)で公開しています。配布物にゲーム本体のファイルは含まれません。

本MODは個人開発の非公式ツールであり、Square Enixとは関係ありません。動作保証はなく自己責任でご使用ください。
