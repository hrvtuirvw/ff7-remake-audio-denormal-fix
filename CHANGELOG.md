# Changelog

## 0.2.0

- Add FINAL FANTASY VII REBIRTH with its own audio-DSP breakpoint.
- Select Remake/Rebirth from the launch EXE name; retain Remake support.
- Support the root launcher or the corresponding shipping EXE.
- Preserve descendant/prefix checks and one-shot worker-only FTZ/DAZ setup.
- Add five real-GDB native-fixture regression tests, including main-thread and
  wrong-prefix rejection. These fixtures are not game/Wine compatibility tests.
- Update the English/Japanese installation instructions for both titles.


## 0.1.0

- Initial experimental Linux/Proton source release with manual UMU integration.
- One-shot FTZ/DAZ initialization on the observed audio-mixing thread.
- No executable-hash, version or instruction-signature restriction.
- Descendant-process and prefix checks remain in place.
- No game-file patching and no voice/channel cap.
- Local same-process ON/OFF/ON evidence: 0 / 126 / 0 interior zero spans ≥10 ms
  in three 30-second recordings.
- Windows, other executable builds and long-term gameplay remain unvalidated.

The GitHub source tree includes English and Japanese documentation. Tested
configurations are documented; other builds are untested.
