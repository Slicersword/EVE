"""Copyable owner setup recipes. Explanations use the non-shell `you` label."""

SETUP_STEPS = {'M00': [('you',
          'Choose ONE installation route in the installation section above. Use a fresh ~/eve3 folder; '
          'keep Bank B off. After the chosen route finishes, reconnect PuTTY once to apply the new '
          'groups.'),
         ('PuTTY 1', 'cd "$HOME/eve3" || exit 1\n./eve doctor\n./eve stage M00')],
 'M01': [('PuTTY 1', 'cd "$HOME/eve3" || exit 1\n./eve run'),
         ('PuTTY 2',
          'cd "$HOME/eve3" || exit 1\n'
          './eve face\n'
          './eve ctl expression name=happy\n'
          'sleep 6\n'
          './eve ctl say "Hello"')],
 'M02': [('you',
          'Stop EVE with Ctrl+C in PuTTY 1. Keep Bank B off. Flashing is performed FROM THE PI over its '
          'USB cable to the Mega; no separate Windows Arduino upload is needed.'),
         ('PuTTY 1', 'cd "$HOME/eve3" || exit 1\n./eve flash && ./eve run'),
         ('PuTTY 2', 'cd "$HOME/eve3" || exit 1\n./eve status')],
 'M03': [('PuTTY 2', 'vcgencmd get_throttled\nvcgencmd measure_temp'),
         ('you',
          'Carry out the power and current measurements described in Your test BEFORE confirming any '
          'flag. Switch Bank B on only for these attended electrical measurements, then off again. The '
          'firmware still has both actuators disabled.'),
         ('PuTTY 2',
          './eve cfg confirm power_a_verified\n'
          './eve cfg confirm power_b_verified\n'
          './eve cfg confirm motor_current_verified'),
         ('you', 'Stop EVE with Ctrl+C in PuTTY 1, then restart to load your confirmations.'),
         ('PuTTY 1', './eve run'),
         ('PuTTY 2', './eve ctl session_start minutes=1\n./eve status')],
 'M04': [('you',
          'Stop EVE with Ctrl+C in PuTTY 1. Keep Bank B off. Fix wiring until diagnostics report all '
          'four I2C devices. Releasing XSHUT changes bus addresses; only one process may own the '
          'sensors.'),
         ('PuTTY 1', './eve i2c'),
         ('you', 'After all four devices answer, start EVE.'),
         ('PuTTY 1', './eve run'),
         ('PuTTY 2', './eve status'),
         ('you',
          'Keep actuator power disconnected. Securely support the robot; never put it at an '
          'uncontrolled edge. Capture floor readings with all three cliff sensors over the normal '
          'floor.'),
         ('PuTTY 2', './eve cliff floor'),
         ('you',
          'While securely holding/supporting the robot, expose all three cliff sensors to a drop/no '
          'floor and capture edge readings. Each sensor must give steady values and flip between floor '
          'and edge.'),
         ('PuTTY 2', './eve cliff edge\n./eve cliff apply'),
         ('you',
          'Stop EVE with Ctrl+C in PuTTY 1. Keep Bank B off; reflash the changed cliff calibration.'),
         ('PuTTY 1', './eve flash && ./eve run')],
 'M05': [('PuTTY 2',
          './eve ctl session_start minutes=5\n./eve ctl clear\n./eve status\nwatch -n 0.5 ./eve status'),
         ('you',
          'Ctrl+C stops watch. Perform each refusal test described below, then clear only after fixing '
          'its cause.')],
 'M06': [('PuTTY 2', 'vcgencmd measure_temp')],
 'M07': [('PuTTY 2',
          './eve cfg set firmware.drive_enabled true\n./eve cfg confirm contained_ground_area'),
         ('you', 'Stop EVE with Ctrl+C in PuTTY 1. Bank B must be off while flashing.'),
         ('PuTTY 1', './eve flash && ./eve run'),
         ('you',
          'Use a stable support with all four wheels free AND all cliff sensors viewing a safe floor '
          'target within their calibrated range. If that arrangement is not possible, stop and improve '
          'the support. Do not bypass a cliff check. Switch Bank B on; keep your hand at its physical '
          'switch.'),
         ('PuTTY 2',
          './eve ctl session_start minutes=10\n'
          './eve ctl clear\n'
          './eve ctl drive_test left=60 right=60 wheels_lifted=true\n'
          './eve ctl drive_test left=40 right=70 wheels_lifted=true'),
         ('you',
          'Do all stopping/direction tests below BEFORE confirming drive. Default max duration is one '
          'second in drive_test.'),
         ('PuTTY 2', './eve cfg confirm drive_verified'),
         ('you',
          'Stop EVE with Ctrl+C and restart to load the flag. For the floor test, place the robot in '
          'the contained area, start a new attended session, then clear.'),
         ('PuTTY 1', './eve run'),
         ('PuTTY 2',
          './eve ctl session_start minutes=5\n'
          './eve ctl clear\n'
          './eve ctl drive left=100 right=100 seconds=1')],
 'M08': [('PuTTY 2', './eve cfg set firmware.head_enabled true'),
         ('you',
          'Stop EVE with Ctrl+C in PuTTY 1. Bank B off during upload. With motor power off, carefully '
          'align the head centre marks without forcing the gearbox.'),
         ('PuTTY 1', './eve flash && ./eve run'),
         ('you', 'Switch Bank B on with all sensors safe and the wheels stationary.'),
         ('PuTTY 2',
          './eve ctl session_start minutes=10\n'
          './eve ctl clear\n'
          './eve ctl head_home confirm=true\n'
          './eve ctl head_jog pan=8 confirm=true'),
         ('you',
          'Wait for each jog to finish, inspect cable clearance, then repeat as required. Use pan=-8, '
          'tilt=8 or tilt=-8 for the other directions. Note safe position values. If limits need '
          'reducing, use the optional settings section; stop, reflash and restart before continuing. '
          'Never increase the shipped limits without physical validation.'),
         ('PuTTY 2', './eve cfg set head.soft_limits_verified true\n./eve cfg confirm head_verified'),
         ('you',
          'Stop EVE with Ctrl+C and restart to load the confirmations. Reflash first if you changed '
          'pan/tilt limits. Start a new session, clear, and set manual home again after every '
          'restart/reflash that resets the Mega.'),
         ('PuTTY 1', './eve run'),
         ('PuTTY 2',
          './eve ctl session_start minutes=10\n'
          './eve ctl clear\n'
          './eve ctl head_home confirm=true\n'
          './eve ctl head_look direction=left\n'
          './eve ctl head_look direction=center')],
 'M09': [('PuTTY 2', 'watch -n 0.5 ./eve status')],
 'M10': [('PuTTY 2', './eve cfg set camera.enabled true'),
         ('you', 'Stop EVE with Ctrl+C and restart.'),
         ('PuTTY 1', './eve run'),
         ('PuTTY 2', './eve status'),
         ('you',
          'Head tracking is optional; see the optional settings section after completing the camera '
          'test.')],
 'M11': [('PuTTY 2', './eve ctl chat "remember that the keys are in the drawer"'),
         ('you',
          'Restart EVE once, then check persistence before the erase test. This erases ALL notes and '
          'reminders; use only disposable test data.'),
         ('PuTTY 2',
          './eve ctl chat "what do you remember"\n'
          './eve ctl notes\n'
          './eve ctl erase_memory confirm=true\n'
          './eve ctl notes')],
 'M12': [('PuTTY 2',
          './eve ctl chat "who are you"\n'
          './eve ctl chat "किती वाजले"\n'
          './eve ctl chat "एक चुटकुला सुनाओ"\n'
          './eve ctl chat "tell me a story"'),
         ('you',
          'Optional local models need a separately installed on-Pi llama-server and model. They are not '
          'bundled or required; keep cloud AI off.')],
 'M13': [('PuTTY 2',
          './eve ctl say "Hello, I am EVE"\n'
          './eve ctl say "नमस्ते" lang=hi\n'
          './eve ctl say "नमस्कार" lang=mr'),
         ('you',
          'Stop EVE with Ctrl+C in PuTTY 1. The first voice install requires internet and downloads '
          'whisper.cpp and its model.'),
         ('PuTTY 1', 'bash scripts/install_voice.sh && ./eve mic'),
         ('you',
          'Apply the threshold command printed by the microphone tool. Change the capture device if the '
          'default is wrong; see optional settings.'),
         ('PuTTY 2', './eve cfg set voice.capture_enabled true'),
         ('PuTTY 1', './eve run')],
 'M14': [('PuTTY 2', 'watch -n 0.5 ./eve status')],
 'M15': [('PuTTY 2', './eve ctl chat "remind me in 1 minute to drink water"\n./eve ctl reminders')],
 'M16': [('PuTTY 2', './eve ctl chat "go to sleep"\nsleep 5\n./eve ctl chat "wake up"'),
         ('you',
          'Phone control on the trusted home network is optional; see optional settings. Keep the '
          'default loopback address if you only need the Pi screen and PuTTY.')],
 'M17': [('PuTTY 2', './eve ctl session_start minutes=30\n./eve ctl clear'),
         ('you',
          'Run the 30-minute attended acceptance test below. Only after it passes, stop EVE with Ctrl+C '
          'in PuTTY 1 and install autostart. Bank B off for the reboot.'),
         ('PuTTY 1', 'bash scripts/install_service.sh'),
         ('PuTTY 2', 'sudo reboot'),
         ('you',
          'Reconnect PuTTY, verify the face and runtime start, then run ./eve stage M17. No motion is '
          'permitted until a fresh attended session and clear.')]}
