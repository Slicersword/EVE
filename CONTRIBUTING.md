# Contributing to EVE

Use a feature branch and reviewable commits. Keep the documented hardware/pin contract and EN/HI/MR
handling intact. Keep commissioning flags false, actuator firmware disabled, calibration unset and cloud
off in tracked defaults. Do not commit another robot's verified state, data, token or credentials.

The [software guide](docs/SETUP_GUIDE.md#developer-verification) contains the host verification commands.
Run the full test suite after runtime/firmware changes. Hardware tests require the owner and are not CI tests.
Changes affecting compiled settings must regenerate the firmware header. Setup recipes live in
tools/setup_steps.py; stage checks and guide generation live in tools/stage.py. Regenerate and review the
guide after changing either. Avoid hand-editing the generated guide.

Meaningful regression tests should cover refusal behavior and externally observed functionality.
The firmware harness compiles the actual sketch against a fake core; the separate AVR job checks target
compilation. Neither proves electrical safety. Preserve both distinctions in issues and pull requests.

No code downloaded or produced by an LLM may bypass the allow-list or directly actuate motors. Do not
introduce cloud uploads of private data, raw frames/audio or local notes. Keep updates reversible and
preserve owner settings. Do not introduce a software-controlled fan module or INA219 dependency.

The owner has not chosen a project license; do not add one without an explicit decision. Check licenses
for any new dependencies and models. Never include copyrighted third-party weights as project-owned assets.
