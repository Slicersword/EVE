# Repository verification — 24 November 2026

| Check | Observed result |
|---|---|
| Supplied baseline host suite | 105 tests passed before modifications |
| Repository host suite | 111 tests passed, including real-sketch fake-core harness and new regressions |
| Generated-file / defaults / documentation checks | Passed |
| Python compilation and shell syntax | Passed |
| Live simulated runtime | HTTP status and token-authenticated CLI chat passed; physical features disabled; motion blocked |
| Fast-forward update fixture | Passed: owner calibration/data preserved, header regenerated, clean-default tests run, two backups retained |
| Real Pi, wiring and sensor diagnosis | Not performed |
| Real AVR toolchain compile/upload | Not performed locally; separate CI compilation configured |
| Physical commissioning | No stage or commissioning flag confirmed |
| GitHub Actions run | Not observed locally; requires successful push and a workflow run |

These checks are specific to source behavior. They do not close the historical I2C fault, establish
safe stopping distance, measure current, validate a bootloader or prove full-duplex voice capability.
