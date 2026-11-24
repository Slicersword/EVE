#!/usr/bin/env bash
# PuTTY 1: runs EVE in the foreground. Ctrl+C = safe stop (wheels and head are stopped first).
cd "$(dirname "$0")/.."
exec .venv/bin/python -m eve3 "$@"
