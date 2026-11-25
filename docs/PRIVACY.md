# Privacy and data handling

Defaults are local: network binds to 127.0.0.1; cloud AI, local LLM, microphone capture, camera,
tracking and web tools are disabled. Speaking, consent-based memory and basic offline dialogue are enabled.

| Data | Handling |
|---|---|
| Camera frames | Local picamera2/OpenCV processing; no frame saving or upload path in the runtime |
| Microphone audio | ALSA stream; short transcription clip in /dev/shm, deleted in finally; no disk fallback |
| Conversation text | Used for the current answer; not written to a conversation log |
| Explicit notes/reminders | Local SQLite under ignored data/; not sent to model adapters |
| Owner token / API key | Ignored runtime files, never source configuration or commits |
| Optional local-model request | Current text to configured loopback model endpoint |
| Optional cloud-model request | Current text after limited regex redaction, only with both opt-in switches |

RAM-backed files/memory are not a forensic zero-retention guarantee: system swap, OS crash tooling,
backups and external audio/model programs are outside this runtime's control. Inspect the actual Pi
configuration when strict volatile-only processing is required.

## Cloud limitation

Cloud is OFF. The existing optional redactor handles email addresses, URLs and long numbers; it does
not reliably recognize names, addresses or every identifying detail. Enabling its switches does not make
arbitrary private speech safe for cloud transmission. To preserve the owner's strict no-private-data
rule, leave cloud disabled. No private notes, audio or images are intentionally attached by the adapter.

Model responses are text-only; they are never parsed as actuator commands. Fixed intent actions from the
person's own words still pass the runtime motion gates.

## Local access

Every command needs the runtime token. Loopback status can be read locally; remote status needs a token.
The home-network mode uses HTTP, not TLS: keep it on a trusted LAN, do not port-forward it, and avoid
sharing a URL that includes a token. Tokens change with runtime restart.

The runtime avoids HTTP access logs, but terminal history, manually copied output and service logs can
still disclose information. Inspect logs before sharing. Git ignores all runtime data and local overlays.


Home activity records are held locally in `home_companion.sqlite3`. The robot's
control token is required to read or change them. Household messages are a shared
board for holders of that token. Music is selected and played in the browser
without uploading a file. The expression WAVs are original generated cues, and
the bundled activity catalog contains prepared examples. Git does not contain
the Pi's saved household records.
