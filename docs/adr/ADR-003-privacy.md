# ADR-003: Privacy defaults
Date: 2026-11-23   Status: accepted
Context: Family home robot with camera and microphones.
Decision: Camera frames and audio are processed in RAM on the Pi and never written to disk or sent anywhere. Conversation text is not logged (events and counts only). Memory notes need explicit consent per note. Cloud AI is OFF; it needs `ai.cloud.enabled` AND `ai.cloud.privacy_consent`, sends only the current typed/spoken sentence after redaction, never memory/names/audio/images, and `send_private_data=true` is rejected by config validation. LLM output is text only and is never parsed for commands. Web tools (Wikipedia/FX/holidays) are an allow-list and off by default.
Alternatives: no cloud code at all (kept as an explicit owner choice instead).
Consequences: answers are simpler offline. Reverse: flags in config/local.json.
