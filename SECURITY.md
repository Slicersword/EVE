# Security and sensitive reports

Do not file public issues containing API keys, runtime tokens, private memories, full owner overlays,
family photographs or raw microphone recordings. Report a vulnerability using GitHub's private
vulnerability reporting only if enabled, or contact the repository owner through an established private
channel. No dedicated security contact or response SLA has been configured in this repository.

Keep network.host at 127.0.0.1 unless trusted-LAN control is required. Commands need the rotating runtime
token, but the built-in HTTP server is not an Internet-facing hardened service. Do not port-forward it.
Cloud is disabled and optional regex redaction does not guarantee removal of identifying text.

Ignore rules exclude config/local.json, data, recordings, credentials and local model downloads.
Before a commit, inspect staged files. If a real secret is committed, rotate it; deleting a later copy
does not remove it from Git history. Issue attachments and terminal screenshots need the same review.
