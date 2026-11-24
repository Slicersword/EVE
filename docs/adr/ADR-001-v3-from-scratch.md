# ADR-001: V3 rebuilt from scratch, stdlib-first
Date: 2026-11-23   Status: accepted
Context: Owner asked for a brand new V3 covering the full robot (M00-M17) and to restart the setup process from M00. The old tree is ~10k lines with aiohttp and many build tools; V2 covered only the safe core.
Decision: New folder EVE_SOURCE_V3, package `eve3`, Python standard library for everything except hardware drivers (pyserial, smbus2, adafruit VL53L0X, gpiozero, picamera2/opencv). One process, one composition root (`eve3/runtime.py`). Same wiring, same pin map, same E1+CRC16 framing idea; firmware rewritten.
Alternatives: upgrade V2 (owner declined); keep the old modular plugin tree (too large to verify).
Consequences: easy to read and test on a PC; fewer installs on the Pi. Old calibration/config is not carried over - every stage is repeated. Reverse: old project stays in the backup folder and in the Pi archive.
