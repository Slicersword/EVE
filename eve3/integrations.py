"""M16 - optional read-only internet look-ups. OFF by default (integrations.web_tools_enabled).
A fixed allow-list; only the short search word goes out - never audio, images, memory or names."""
from __future__ import annotations
import json, re, urllib.parse, urllib.request

UA = "EVE-home-robot/3"


def _json(url: str, timeout=5.0):
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(65537)
    if len(raw) > 65536:
        raise ValueError("response too large")
    return json.loads(raw)


def _term(value, limit=60) -> str:
    value = " ".join(str(value).split())
    if not value or len(value) > limit or not re.fullmatch(r"[\w .'ऀ-ॿ-]+", value):
        raise ValueError("search word not accepted")
    return value


def wikipedia(term, fetch=_json) -> str:
    data = fetch("https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(_term(term), safe=""))
    return " ".join(str(data.get("extract", "")).split())[:400]


def exchange_rate(base="USD", quote="INR", fetch=_json) -> float | None:
    base, quote = str(base).upper(), str(quote).upper()
    if not (re.fullmatch(r"[A-Z]{3}", base) and re.fullmatch(r"[A-Z]{3}", quote)):
        raise ValueError("currency codes are three letters")
    rate = fetch(f"https://open.er-api.com/v6/latest/{base}").get("rates", {}).get(quote)
    return float(rate) if type(rate) in (int, float) else None


TOOLS = {"wikipedia": wikipedia, "exchange_rate": exchange_rate}


def call(cfg: dict, name: str, *args):
    if cfg["integrations"]["web_tools_enabled"] is not True:
        raise PermissionError("web tools are switched off")
    if name not in TOOLS:
        raise KeyError(name)
    return TOOLS[name](*args)
