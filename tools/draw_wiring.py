#!/usr/bin/env python3
"""Render the build diagrams using the shipped GPIO and Mega pin assignments."""
from html import escape
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config/eve.json").read_text(encoding="utf-8"))
PINS = CFG["pins"]["mega"]
PI_HEADER = {2: 3, 3: 5, 5: 29, 6: 31, 13: 33, 18: 12, 19: 35, 20: 38, 22: 15, 25: 22, 27: 13}


def gpio(bcm):
    return f"Pi BCM{bcm} · pin {PI_HEADER[bcm]}"


def node(x, y, label, style=""):
    return f'<text x="{x}" y="{y}" class="{style}">{escape(label)}</text>'


def diagram(title, subtitle, groups):
    """Each row is one labelled wire or one group of related wires."""
    content = [node(26, 40, title, "title"), node(26, 66, subtitle, "note")]
    y = 88
    for heading, rows, note in groups:
        height = 53 + 33 * len(rows) + (27 if note else 0)
        content.append(f'<rect x="20" y="{y}" width="820" height="{height}" rx="10"/>')
        content.append(node(38, y + 30, heading, "heading"))
        for left, right, arrow, kind in rows:
            y += 33
            baseline = y + 29
            content.append(node(38, baseline, left, "terminal"))
            end = ' marker-end="url(#arrow)"' if arrow in ("to", "both") else ""
            start = ' marker-start="url(#arrow)"' if arrow in ("from", "both") else ""
            content.append(f'<path d="M303 {baseline - 5} H382" class="{kind}"{start}{end}/>')
            content.append(node(402, baseline, right))
        if note:
            y += 27
            content.append(node(38, y + 29, note, "note"))
        y += 68
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 860 {y + 5}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{escape(title)}</title><desc id="desc">{escape(subtitle)}</desc>',
        '<defs><marker id="arrow" markerWidth="7" markerHeight="6" refX="6" refY="3" orient="auto-start-reverse" '
        'viewBox="0 0 7 6"><path d="M0 0 L7 3 L0 6z" fill="#b6d0e7"/></marker></defs>',
        '<style>.canvas{fill:#0c1827;stroke:none} rect{fill:#15273a;stroke:#365470} text{fill:#e9f3fb;'
        'font:16px system-ui, sans-serif} .title{font-size:30px;font-weight:700}.heading{fill:#7fe6d7;'
        'font-weight:700;font-size:19px}.terminal{font-weight:600}.note{font-size:14px;fill:#c0d5e9}'
        'path[class]{stroke-width:2;fill:none}.power{stroke:#ffd07e}.signal{stroke:#85d8f9}'
        '.ground{stroke:#c6d0dd;stroke-dasharray:5 4}</style>',
        '<rect class="canvas" width="100%" height="100%"/>', *content, "</svg>", "",
    ])


def power_diagram():
    return diagram("Power and speaker wiring", "Gold = supply · dashed = return · blue = audio or a speaker pair", [
        ("Bank A · Pi and logic", [
            ("Bank A 5 V USB", "Pi 4 USB-C power input", "to", "power"),
            ("Pi USB-A", "Mega USB-B and display touch USB", "to", "power"),
            ("Pi 5 V · measured budget", "Always-on Pi fan (+), fan (−) to Pi GND", "to", "power"),
            ("Mega 5 V logic", "Both TB6612 VCC and compatible digital sensors", "to", "power"),
        ], "Check how your panel receives 5 V. Use one documented supply path."),
        ("Bank B · switched motor branch", [
            ("Bank B 5 V (+)", "Branch protection, then actuator cutoff", "to", "power"),
            ("Actuator cutoff output · 5 V", "Both TB6612 VM and both ULN2003 motor (+)", "to", "power"),
            ("Bank B common return (−)", "Each motor driver GND and the Mega GND reference", "both", "ground"),
        ], "Keep Bank A and Bank B positive rails separate. The cutoff opens every motor (+) feed."),
        ("Bank B · switched audio branch", [
            ("Bank B 5 V (+)", "Branch protection, audio switch, boost IN+", "to", "power"),
            ("Bank B return (−)", "Boost IN−, audio ground per module instructions", "both", "ground"),
            ("Boost OUT+ / OUT−", "Regulated 9 V to PAM8610 DC+ / DC−", "to", "power"),
            ("Pi 3.5 mm stereo line", "Amplifier L / R / GND input", "to", "signal"),
            ("PAM8610 left + / −", "Left 4 Ω / 3 W speaker, its own pair", "to", "signal"),
            ("PAM8610 right + / −", "Right 4 Ω / 3 W speaker, its own pair", "to", "signal"),
        ], "Set and load-test 9 V before attaching the amplifier. Keep both speaker pairs isolated from ground."),
    ])


def mega_diagram():
    groups = []
    signals = "STBY AIN1 AIN2 PWMA BIN1 BIN2 PWMB".split()
    for side in ("left", "right"):
        rows = [(f"Mega D{pin}", signal, "to", "signal") for signal, pin in zip(signals, PINS[side], strict=True)]
        rows += [("Driver AO1 / AO2", f"{side.title()}-front N20 wheel motor pair", "to", "signal"),
                 ("Driver BO1 / BO2", f"{side.title()}-rear N20 wheel motor pair", "to", "signal")]
        groups.append((f"{side.title()}-side TB6612FNG", rows, "VCC at Mega logic 5 V · VM at switched Bank B 5 V · common GND"))
    rows = [(f"Mega D{PINS['pan'][i]} (pan) / D{PINS['tilt'][i]} (tilt)", f"IN{i + 1} on the matching ULN2003", "to", "signal")
            for i in range(4)]
    groups.append(("Pan and tilt · one ULN2003 per motor", rows + [
        ("Each ULN2003 five-pin socket", "Matching keyed 28BYJ-48 5 V motor plug", "to", "signal"),
    ], "Each ULN2003 motor supply uses switched Bank B 5 V and common GND."))
    cliff = ("Front-left", "Rear-centre", "Front-right")
    rows = [(f"Mega D{pin}", f"{name} TCRT5000 digital OUT", "from", "signal")
            for name, pin in zip(cliff, PINS["cliff"], strict=True)]
    groups.append(("Cliff and presence inputs", rows + [(f"Mega D{PINS['pir']}", "HC-SR501 PIR OUT", "from", "signal")],
                   "Mega-side supply only if the module accepts it. All module GNDs go to Mega GND."))
    return diagram("Mega signal wiring", "Numbers are Arduino digital sockets. See the power diagram for the positive feeds and returns.", groups)


def pi_diagram():
    s = CFG["sensors"]
    return diagram("Pi signal and data wiring", "BCM = software number · pin = position on the Pi 40-pin header", [
        ("Shared I²C bus · 3.3 V-compatible logic", [
            (gpio(2), "SDA on all three VL53L0X and the MPU6050", "both", "signal"),
            (gpio(3), "SCL on all three VL53L0X and the MPU6050", "to", "signal"),
            *[(gpio(pin), f"{name} VL53L0X XSHUT → {address:#04x}", "to", "signal")
              for pin, name, address in zip(s["tof_xshut"], ("Front-left", "Front-right", "Rear"), s["tof_addresses"], strict=True)],
        ], f"Verify breakout VIN, pull-ups and GND. MPU6050 defaults to {s['imu_address']:#04x}."),
        ("Shared I²S bus · two INMP441 microphones", [
            (gpio(18), "SCK / BCLK on both mics", "to", "signal"),
            (gpio(19), "WS / LRCLK on both mics", "to", "signal"),
            (gpio(20), "SD / DOUT on both mics", "from", "signal"),
            ("Pi 3.3 V · pin 1 or 17", "Both VDD pins, right microphone L/R", "to", "power"),
            ("Pi GND · e.g. pin 6", "Both GND pins, left microphone L/R", "both", "ground"),
        ], "Same SD line with opposite slots. Check decoupling and the SD pull-down in the wiring guide."),
        ("Touch, camera and display", [
            (gpio(CFG["touch"]["head_gpio"]), "Head TTP233 OUT", "from", "signal"),
            (gpio(CFG["touch"]["back_gpio"]), "Back TTP233 OUT", "from", "signal"),
            (gpio(CFG["camera"]["led_gpio"]), "Camera indicator via resistor / driver to GND", "to", "signal"),
            ("Pi CSI connector", "Camera Module 3 via correct Pi 4 ribbon", "both", "signal"),
            ("Pi micro-HDMI 0", "7-inch display HDMI input · picture", "to", "signal"),
            ("Pi USB-A", "Display touch USB · data; Mega USB-B · serial", "both", "signal"),
        ], "TTP233 modules use 3.3 V and Pi GND. Set direct active-high mode. Keep the physical camera shutter."),
    ])


def main():
    for name, draw in (("power", power_diagram), ("mega", mega_diagram), ("pi", pi_diagram)):
        path = ROOT / "docs" / "assets" / f"wiring-{name}.svg"
        svg = draw()
        if "--check" in sys.argv:
            if not path.is_file() or path.read_text(encoding="utf-8") != svg:
                sys.exit(f"{path.name} is stale; run python3 tools/draw_wiring.py")
        else:
            path.write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
