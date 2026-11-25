# Change log

## Lumen expressions

- Widen the mouth, deepen smiles, and give the Speaking face a more visible jaw movement.
- Use the reference preview’s glass eyes and soft lighting for all 90 expressions.
  The build guide, Pi touchscreen, Expression Studio, and Home music display share
  the same renderer. Alert turns red immediately.

## Original artwork across all expressions

- Use the original artwork across the full set of 90 expressions on the Pi,
  in the build guide, and in the Expression Studio and Home. Keep red for Alert.

## Consistent expression styling

- Use the same eyes-and-mouth display for all 90 expressions on the Pi, in the
  Expression Studio and Home, and in the build guide preview. Keep the red Alert
  signal and pair each expression with its original sound cue.

## Eyes and controls preview

- Preview EVE’s touchscreen face, all 90 expressions and selected original sounds
  from the build guide. See the Pi’s control panel with read-only sample status.

## Software audit and wiring diagrams — 25 November 2026

- Require whole motion phrases and keep Stop ahead of movement. Cancel head
  movement and tracking on Stop, and make stale Mega links reconnect without
  carrying over the attended session.
- Invalidate failed I2C data immediately and refuse clear on a firmware mismatch.
- End the motion session and pause local camera capture during sleep.
- Restore multilingual spoken Home shortcuts and keep due timers until Done.
  Retry failed playback and preserve timer state on databases from earlier builds.
- Keep captured audio local, discard capture backlog before recognition and add
  an optional paired WebRTC echo-cancel route for on-Pi acceptance.
- Restrict optional cloud requests to fixed public questions and pin local-model
  requests to numeric loopback with no redirect or proxy.
- Preserve expression cues through the brief quiet interval. Add three wiring
  diagrams generated from the current pin assignments and correct the setup's
  motor, head and note tests.

## Restore original expression and home features

- Bundle all 90 recovered WAV cues with checksums, original artwork and a local
  expression studio. The kiosk retains its simple default face and opt-in cues.
- Restore the multilingual home activity catalog, home controls and local
  persistence for games, stories, recipes, timers, messages, music and capsules.
- Check the complete media pack and simulated HTTP build before setup installs
  packages. Keep the existing firmware and commissioning defaults.

## Detailed hardware guide and optional progress — 24 November 2026

- Matched the inventory and wiring to N20/TB6612 wheels, 28BYJ-48 head motors,
  TCRT5000 digital cliff modules, two TTP233 touch pads, two INMP441 microphones,
  Camera Module 3 and PAM8610 with 4 Ω / 3 W speakers.
- Kept two 5 V banks as the main path and INA219 disabled. Added the selected
  5 V-to-9 V audio boost branch and supply/output-limit acceptance requirements;
  the optional BMS/battery/charger system remains outside the power-bank build.
- Added per-terminal wiring, feature/limits tables, beginner terminal guidance,
  daily operating/backup instructions and expanded troubleshooting.
- Added a Pi 4 capture-only I2S overlay, a stereo-to-mono ALSA profile, backed-up
  setup helpers and both-microphone testing instructions without changing playback.
- Report speech-process failures accurately instead of clearing their error state.
- Added opt-in browser-local build progress: 44 tasks, notes, completion dates,
  next task, filters, pause/reset and validated export/import backups.
- Added a self-contained source viewer and shared navigation for the live/offline guides.
- Added notebook and I2S configuration regression checks plus overlay compilation in CI.

## GitHub Pages hosting

- Made https://slicersword.github.io/EVE/ the primary build website.
- Added a Jekyll layout and search generated directly from the repository documents.
- Used the existing main/root Pages publishing setup, without ChatGPT hosting or keys.
- Preserved the offline export and added validation of the actual Pages rendering.

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
