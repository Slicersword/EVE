# Verification record

This record describes software evidence for the standalone reference build.
It does not record anyone's robot as assembled or commissioned.

| Check | Observed result |
|---|---|
| Linux host suite (Python 3.12) | 122 tests passed, including real-sketch fake-core harness |
| Configuration/upload regressions | Explicit port precedence, rejected unsafe settings, private local file mode, configured lock path, fake upload success/failure passed |
| Public defaults | All readiness flags false; drive/head disabled; cliff calibration unset; external AI off |
| Generated files | Firmware header and M00–M17 software guide match generators |
| Source / syntax | Python compilation, Bash syntax, JavaScript syntax and diff whitespace checks passed |
| Documentation site | 25 Markdown pages, 64 source listings; local links/fragments/assets/raw source consistency passed |
| Browser QA | Desktop page layout and offline search checked in the local preview |
| Live simulation | Mega handshake, authenticated CLI chat, shipped motion refusal and safe shutdown passed |
| GitHub CI | Python 3.11/3.12 host jobs, Mega target compilation and site validation passed in the linked run |
| AVR target | Locked and enabled Mega 2560 variants compiled in CI using CLI 1.3.1 and AVR core 1.8.6 |
| Raspberry Pi installation | Requires a real Pi 4 / Bookworm / arm64 system; not run on the development host |
| Mega upload and bootloader | Requires the physical Mega; not performed |
| Wiring, load, sensors and stop distance | Builder must measure and run the corresponding physical stages |

Host tests use fakes/temp state and do not set public commissioning flags.
The upload regression uses a fake CLI and pseudoterminal, not a connected board.
The real sketch harness exercises logic; target compilation checks the AVR build;
a successful upload still does not provide physical acceptance.

For reproducible commands see [Testing](TESTING.md). Read the repository Actions
results for the commit you intend to build. Optional Pages hosting must be enabled
once as described in [Website](WEBSITE.md).

CI evidence: [Verify EVE, commit 21b6c3b](https://github.com/Slicersword/EVE/actions/runs/45338206886).
All four jobs completed successfully. This report's later text/link-only updates
do not change the tested runtime or firmware.
