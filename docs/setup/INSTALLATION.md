## Before M00: choose an installation route

Target: 64-bit Raspberry Pi Bookworm with a working desktop login, SSH/PuTTY access and internet.
The desktop must be running on the Pi for the face kiosk; PuTTY alone does not create a desktop session.
Keep Bank B off. Substitute your real Pi login/IP and local ZIP path. Do not paste window labels or prose.
If an existing ~/eve3 folder is present, preserve it and choose a new installation folder; these routes
refuse to overwrite it. Do not mix this V3 tree into an old EVE_SOURCE directory.

### Route A — clone this repository on the Pi

**PuTTY 1**

```bash
sudo apt-get update && sudo apt-get install -y git
```

```bash
git clone https://github.com/Slicersword/EVE.git "$HOME/eve3" && cd "$HOME/eve3" && bash scripts/retire_old.sh
```

If the repository is private, use GitHub's supported authenticated clone flow. Do not paste credentials
into a clone URL or this chat. Preview the old folders/services listed above before parking them.
Only after confirming this is the intended old installation:

```bash
cd "$HOME/eve3" && bash scripts/retire_old.sh --yes && bash scripts/setup_pi.sh
```

Reconnect PuTTY, then continue with M00 below.

### Route B — transfer the complete ZIP from Windows

Download EVE_complete_build.zip from the provided deliverable, or GitHub's Code → Download ZIP.
The extraction below accepts EVE/, EVE-main/ or the original EVE_SOURCE_V3/ archive root.
This is an alternative to Route A, not an extra installation step.

**Windows PowerShell**

```powershell
pscp "C:\path\to\EVE_complete_build.zip" PI_USER@PI_IP:EVE_complete_build.zip
```

**PuTTY 1**

```bash
sudo apt-get update && sudo apt-get install -y unzip
```

```bash
bash <<'EVE_INSTALL'
set -euo pipefail
if [ -e "$HOME/eve3" ]; then
  echo "STOP: ~/eve3 exists. Preserve it and choose a fresh installation folder."
  exit 1
fi
stage_dir=$(mktemp -d)
trap 'rm -rf "$stage_dir"' EXIT
unzip -q "$HOME/EVE_complete_build.zip" -d "$stage_dir"
source_dir=""
for candidate in EVE EVE-main EVE_SOURCE_V3; do
  if [ -f "$stage_dir/$candidate/eve3/runtime.py" ]; then
    source_dir="$stage_dir/$candidate"
    break
  fi
done
[ -n "$source_dir" ] || { echo "STOP: expected EVE source folder not found in ZIP"; exit 1; }
mv "$source_dir" "$HOME/eve3"
cd "$HOME/eve3"
chmod +x eve scripts/*.sh tools/*.py
bash scripts/retire_old.sh
EVE_INSTALL
```

Review the parking preview, then:

```bash
cd "$HOME/eve3" && bash scripts/retire_old.sh --yes && bash scripts/setup_pi.sh
```

Reconnect PuTTY, then continue with M00. The original V3 ZIP does not contain the new repository docs/fixes;
use the complete repository ZIP for this version. ZIP installs do not have Git history or support git pull;
use the Git route for ongoing source updates.

### How the virtual environment works

The package installer creates .venv with system-site-packages, so apt-installed Pi drivers remain available.
The EVE launcher selects .venv/bin/python automatically. You do not need to activate it in each PuTTY window.
System package/firmware tooling uses the system shell; do not run the robot as root. A group change requires
logging out and back in; that is why M00 includes reconnecting PuTTY.
