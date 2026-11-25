"""Recovered local expression artwork and WAV catalog."""
import json
from pathlib import Path

WEB = Path(__file__).resolve().parent / "web"
CATALOG = json.loads((WEB / "expressions.json").read_text(encoding="utf-8"))
EXPRESSIONS = tuple(CATALOG["expressions"])
CLIPS = frozenset(CATALOG["clips"])
