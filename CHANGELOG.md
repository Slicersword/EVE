# Change log

## Standalone reference build — 24 November 2026

- Added a complete newcomer path: prerequisites, fresh OS, parts, assembly, wiring,
  installation, ordered M00–M17 tests, acceptance, maintenance and troubleshooting.
- Removed migration scripts, personal handover material and inherited progress claims.
- Added a hardware/build-choice worksheet and safe local configuration example.
- Corrected executable permissions and added Git ignore protection for local data,
  settings, credentials, downloaded models and generated output.
- Made runtime and flasher honor the same explicitly configured Mega serial device.
- Validated configuration structure, numeric types, pins, PWM assignments, addresses,
  private-data locations and timing; local settings are written with private permissions.
- Made runtime-lock and I2C diagnostic behavior respect configured paths/pins.
- Used UTC as the neutral timezone default; local offset remains adjustable.
- Added Pi/platform checks and pinned the AVR toolchain inputs.
- Added regression coverage for configuration, serial selection, locks and upload failure.
- Added dependency-free repository-to-website generation, offline search, full source
  listings, copy buttons, accessible navigation and responsive/print styles.
- Added CI for Python host tests, real-sketch harness, locked/enabled Mega target
  compilation, generated files and website validation; optional GitHub Pages deployment.
