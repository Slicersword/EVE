# ADR-003: Local processing and consent

Camera frames are processed locally. Short audio clips use /dev/shm and are deleted
after transcription; there is no disk fallback. OS swap/crash tools and external
processes are outside that runtime boundary.

Conversation text is not logged. Notes need explicit consent and are stored locally.
Optional local-model requests carry current text to a loopback endpoint. Model
output is text-only and cannot directly issue actuator commands.

Cloud and web integrations are off by default. Cloud opt-in sends current text
through limited regex redaction, which cannot guarantee removal of private names
or addresses. Keep it disabled for private use. See [Privacy](../PRIVACY.md).
