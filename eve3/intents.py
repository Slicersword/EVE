"""Offline command understanding for English, Hindi and Marathi (Devanagari or typed in English letters).
Only the person's own words are parsed here - never text produced by an AI model."""
from __future__ import annotations
import re
from dataclasses import dataclass, field

_DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
_PUNCT = re.compile(r"[^\w\sऀ-ॿ:]", re.UNICODE)


@dataclass(frozen=True)
class Intent:
    name: str
    args: dict = field(default_factory=dict)


def normalize(text: str) -> str:
    return " ".join(_PUNCT.sub(" ", str(text).lower().translate(_DEV_DIGITS)).split())


def strip_wake(text: str, wake_words) -> tuple[bool, str]:
    """Returns (wake word heard, remaining words). The wake word may come with 'hey/hi/ok/अरे/ए'."""
    words = normalize(text).split()
    wake = {normalize(w) for w in wake_words}
    for i, w in enumerate(words[:4]):
        if w in wake:
            return True, " ".join(words[i + 1:])
        if w not in {"hey", "hi", "ok", "okay", "अरे", "ए"}:
            break
    return False, " ".join(words)


# (intent, words/phrases). Checked in order; STOP is first so it always wins.
_RULES = [
    ("stop", ["stop", "halt", "freeze", "ruk", "ruko", "ruk ja", "bas", "thamb", "thamba", "रुक", "रुको", "रुक जा", "बस", "थांब", "थांबा"]),
    ("cancel_reminders", ["cancel reminder", "cancel reminders", "cancel timer", "रिमाइंडर रद्द", "आठवण रद्द"]),
    ("remind", ["remind", "reminder", "yaad dila", "yaad dilana", "aathvan", "athavan", "याद दिला", "याद दिलाना", "आठवण"]),
    ("timer", ["timer", "टाइमर", "टायमर"]),
    ("forget_hint", ["forget everything", "erase memory", "सब भूल जा", "सगळं विसर"]),
    ("recall", ["what do you remember", "what did i tell you", "kya yaad hai", "kay athavte", "क्या याद है", "काय आठवते", "काय लक्षात आहे"]),
    ("remember", ["remember that", "remember", "yaad rakh", "yaad rakhna", "lakshat thev", "याद रख", "याद रखना", "लक्षात ठेव"]),
    ("turn_left", ["turn left", "go left", "baye mud", "baen mud", "davikade val", "बाएं मुड़", "बाएँ मुड़", "डावीकडे वळ"]),
    ("turn_right", ["turn right", "go right", "daye mud", "daen mud", "ujvikade val", "दाएं मुड़", "दाएँ मुड़", "उजवीकडे वळ"]),
    ("forward", ["go forward", "move forward", "come forward", "forward", "come here", "aage", "aage chal", "aage aa", "pudhe", "pudhe ye",
                 "pudhe ja", "आगे", "आगे चल", "आगे आ", "पुढे", "पुढे ये", "पुढे जा", "इधर आ", "इकडे ये"]),
    ("look_left", ["look left", "baye dekh", "davikade bagh", "बाएं देख", "बाएँ देख", "डावीकडे बघ"]),
    ("look_right", ["look right", "daye dekh", "ujvikade bagh", "दाएं देख", "दाएँ देख", "उजवीकडे बघ"]),
    ("look_up", ["look up", "upar dekh", "var bagh", "ऊपर देख", "वर बघ"]),
    ("look_down", ["look down", "niche dekh", "khali bagh", "नीचे देख", "खाली बघ"]),
    ("look_center", ["look at me", "look straight", "look center", "look centre", "saamne dekh", "samor bagh", "सामने देख", "समोर बघ", "मेरी तरफ देख", "माझ्याकडे बघ"]),
    ("sleep", ["go to sleep", "sleep", "so ja", "zop", "zopa", "सो जा", "झोप", "झोपा"]),
    ("wake", ["wake up", "uth", "uth ja", "utha", "उठ", "उठ जा", "उठा", "जाग"]),
    ("time", ["what time", "time", "kitne baje", "samay", "kiti vajle", "vel kay", "कितने बजे", "समय", "किती वाजले", "वेळ"]),
    ("date", ["what date", "what day", "date", "today", "aaj kya", "tarikh", "aaj kay", "आज क्या", "तारीख", "आज काय", "आज कोणता"]),
    ("joke", ["joke", "chutkula", "vinod", "चुटकुला", "जोक", "विनोद"]),
    ("story", ["story", "kahani", "goshta", "gosht", "कहानी", "गोष्ट"]),
    ("who", ["who are you", "your name", "tum kaun", "tumhara naam", "tu kon", "tuza nav", "तुम कौन", "तुम्हारा नाम", "तू कोण", "तुझं नाव", "तुझे नाव"]),
    ("how", ["how are you", "kaise ho", "kaisi ho", "kasa ahes", "kashi ahes", "कैसे हो", "कैसी हो", "कसा आहेस", "कशी आहेस"]),
    ("status", ["are you ok", "status", "battery", "sab theek", "sagla thik", "सब ठीक", "बैटरी", "सगळं ठीक"]),
    ("thanks", ["thank you", "thanks", "dhanyavad", "shukriya", "धन्यवाद", "शुक्रिया", "आभारी"]),
    ("bye", ["bye", "good night", "alvida", "shubh ratri", "अलविदा", "शुभ रात्रि", "शुभ रात्री", "टाटा"]),
    ("greet", ["hello", "hi", "hey", "namaste", "namaskar", "good morning", "नमस्ते", "नमस्कार", "हेलो", "हाय"]),
]
_UNITS = [(3600, r"hours?|hrs?|ghante|ghanta|taas|tasa|घंटे|घंटा|तास"),
          (60, r"minutes?|mins?|minat|minit|मिनट|मिनिट|मिनिटे|मिनिटांनी|मिनिटं"),
          (1, r"seconds?|secs?|sekand|सेकंड|सेकंद")]
_FILLER = re.compile(r"^(?:me |mujhe |mala |मुझे |मला )?(?:in |after |to |that |ki |ke |baad |bad |nantar |kar |kara |de |dena |बाद |नंतर |की |कि |के |कर |करा |दे |देना )*")
_EXACT_RULES = {"forward", "turn_left", "turn_right", "look_left", "look_right", "look_up", "look_down",
                "look_center", "sleep", "wake", "cancel_reminders", "recall"}


def _has(text: str, phrase: str) -> bool:
    return re.search(rf"(?<![\wऀ-ॿ]){re.escape(phrase)}(?![\wऀ-ॿ])", text) is not None


def _duration(text: str):
    """First '<number> <unit>' in the text -> (seconds, text without it)."""
    for scale, unit in _UNITS:
        m = re.search(rf"(\d{{1,4}})\s*(?:{unit})(?![\wऀ-ॿ])", text)
        if m:
            return int(m[1]) * scale, " ".join((text[:m.start()] + " " + text[m.end():]).split())
    return None, text


def _after(text: str, phrases) -> str:
    for phrase in sorted(phrases, key=len, reverse=True):
        m = re.search(rf"(?<![\wऀ-ॿ]){re.escape(phrase)}(?![\wऀ-ॿ])", text)
        if m:
            before, after = text[:m.start()].strip(), text[m.end():].strip()
            rest = after or before                      # Hindi/Marathi put the verb last
            return _FILLER.sub("", rest + " ").strip()
    return text


def parse(text: str) -> Intent | None:
    t = normalize(text)
    if not t:
        return None
    command = t.removeprefix("please ").removesuffix(" please")
    for name, phrases in _RULES:
        if name in _EXACT_RULES:
            if command in phrases:
                return Intent(name)
            continue
        if name == "remember" and not any(command == p or command.startswith(p + " ") for p in phrases):
            continue
        if not any(_has(t, p) for p in phrases):
            continue
        if name in ("remind", "timer"):
            seconds, rest = _duration(t)
            if seconds is None:
                return Intent("remind_unclear")
            what = _after(rest, phrases) if name == "remind" else ""
            return Intent("remind", {"seconds": seconds, "text": what or "timer"})
        if name == "remember":
            what = _after(t, phrases)
            return Intent("remember", {"text": what}) if what else Intent("remember_unclear")
        return Intent(name)
    return None
