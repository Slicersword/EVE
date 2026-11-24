#!/usr/bin/env python3
"""Install the optional Pi 4 INMP441 profile, without starting capture or changing playback.

  sudo python3 tools/setup_i2s_mic.py --boot   compile/install overlay and back up boot config
  python3 tools/setup_i2s_mic.py --user-audio  add only the named eve_mic PCM to ~/.asoundrc
"""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
START, END = '# BEGIN EVE INMP441', '# END EVE INMP441'


def managed(text, body):
    """Preserve user configuration and keep exactly one explicitly delimited block."""
    if text.count(START) != text.count(END) or text.count(START) > 1:
        raise ValueError('Malformed EVE block; restore/review the configuration before retrying.')
    if START in text:
        first, last = text.index(START), text.index(END)
        if last < first:
            raise ValueError('Malformed EVE block order.')
        # Replace in place: moving [all] could change the meaning of later user settings.
        return text[:first] + START + '\n' + body.rstrip() + '\n' + END + text[last + len(END):]
    return text.rstrip() + ('\n\n' if text.strip() else '') + START + '\n' + body.rstrip() + '\n' + END + '\n'


def boot_config(text):
    # Do not silently replace a different owner's I2S device. Analogue audio and HDMI may stay.
    without_ours = re.sub(re.escape(START) + r'.*?' + re.escape(END), '', text, flags=re.S)
    for name in re.findall(r'^\s*dtoverlay\s*=\s*([^,\s#]+)', without_ours, flags=re.M):
        if re.search(r'i2s|i2smic|adau|voicehat|hifiberry|seeed|audioinjector|rpi-dac|iqaudio|justboom|wm8960', name, re.I):
            raise ValueError(f'Existing audio overlay {name}: review/disable the conflicting I2S device first.')
    return managed(text, '[all]\ndtparam=i2s=on\ndtoverlay=eve-inmp441')


def audio_config(text):
    without_ours = re.sub(re.escape(START) + r'.*?' + re.escape(END), '', text, flags=re.S)
    if re.search(r'\bpcm\.eve_mic\b', without_ours):
        raise ValueError('An unmanaged pcm.eve_mic already exists; review it before installing this profile.')
    return managed(text, (ROOT / 'config/alsa-inmp441.conf').read_text())


def backup_write(path, value):
    old = path.read_text() if path.exists() else ''
    if old == value:
        print(f'Already configured: {path}'); return
    if path.exists():
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        backup = path.with_name(path.name + '.eve-backup-' + stamp)
        shutil.copy2(path, backup)
        print(f'Backup: {backup}')
    path.write_text(value)
    print(f'Updated: {path}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--boot', action='store_true')
    choice.add_argument('--user-audio', action='store_true')
    args = parser.parse_args()
    if args.user_audio:
        if os.geteuid() == 0:
            parser.error('Run --user-audio as your normal Pi user, without sudo.')
        target = Path.home() / '.asoundrc'
        backup_write(target, audio_config(target.read_text() if target.exists() else ''))
        print('Named capture PCM: eve_mic. Playback defaults are unchanged. Test it before enabling voice.')
        return
    model = Path('/proc/device-tree/model')
    if not model.exists() or 'Raspberry Pi 4' not in model.read_text():
        parser.error('The boot profile targets Raspberry Pi 4 only.')
    if os.geteuid() != 0:
        parser.error('Use sudo for --boot only.')
    target = Path('/boot/firmware/config.txt')
    overlays = target.parent / 'overlays'
    if not target.is_file() or not overlays.is_dir():
        parser.error('Expected Bookworm /boot/firmware/config.txt and overlays directory.')
    value = boot_config(target.read_text())
    with tempfile.TemporaryDirectory(prefix='eve-i2s-') as tmp:
        output = Path(tmp) / 'eve-inmp441.dtbo'
        subprocess.run(['dtc', '-@', '-I', 'dts', '-O', 'dtb', '-o', str(output),
                        str(ROOT / 'config/eve-inmp441-overlay.dts')], check=True)
        destination = overlays / output.name
        if destination.exists() and destination.read_bytes() != output.read_bytes():
            backup_write(target, value)  # preserve boot settings before an updated overlay
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            shutil.copy2(destination, destination.with_name(destination.name + '.eve-backup-' + stamp))
        shutil.copyfile(output, destination)
        os.chmod(destination, 0o644)
    backup_write(target, value)
    print('Overlay installed. Motor power OFF; reboot the Pi, then run --user-audio without sudo.')


if __name__ == '__main__':
    main()
