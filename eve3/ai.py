"""M12 - EVE's brain. Three layers, tried in this order:
 1. intents      - the person's own words mapped to a fixed list of actions (offline, always on)
 2. small talk   - built-in answers in English / Hindi / Marathi (offline)
 3. language model - optional. Local llama-server on this Pi, or (owner opt-in only) a cloud endpoint.

Model output is TEXT ONLY. It is cleaned, shortened and spoken; it is never parsed for commands.
The cloud path receives one redacted sentence - no memory, names list, audio or images.
"""
from __future__ import annotations
import json, os, random, re, time, urllib.request
from datetime import datetime, timedelta, timezone
from . import intents
from .config import data_path

_MR_WORDS = {"आहे", "आहेस", "आहात", "काय", "नाही", "मला", "माझं", "माझे", "तू", "तुझं", "तुझे", "तुम्ही", "कसा", "कशी",
             "किती", "झाला", "बघ", "थांब", "थांबा", "सांग", "ये", "पुढे", "आठवण", "लक्षात", "वाजले", "गोष्ट", "विनोद",
             "आज", "उद्या", "नंतर", "मिनिटांनी", "डावीकडे", "उजवीकडे", "समोर", "वर", "खाली", "झोप", "उठा", "नमस्कार",
             "ahe", "ahes", "kay", "nahi", "mala", "maza", "tu", "kasa", "kashi", "kiti", "bagh", "thamb", "zop",
             "pudhe", "sang", "goshta", "athavan", "vajle", "nantar", "davikade", "ujvikade", "samor"}
_HI_WORDS = {"है", "हूँ", "हूं", "हो", "क्या", "नहीं", "मुझे", "मेरा", "मेरी", "तुम", "आप", "कैसे", "कैसी", "कितने", "देख",
             "रुक", "रुको", "बजे", "सुना", "सुनाओ", "कहानी", "चुटकुला", "याद", "बाद", "मिनट", "घंटे", "आगे", "बाएं", "दाएं",
             "ऊपर", "नीचे", "सामने", "नमस्ते", "बता", "बताओ", "कौन", "तारीख",
             "hai", "ho", "kya", "nahi", "mujhe", "tum", "kaise", "kaisi", "kitne", "dekh", "ruk", "baje", "aage",
             "sunao", "kahani", "chutkula", "yaad", "baad", "ghante", "baye", "daye", "kaun"}

LINES = {
    "greet_morning": {"en": "Good morning!", "hi": "सुप्रभात!", "mr": "शुभ सकाळ!"},
    "greet_day": {"en": "Hello!", "hi": "नमस्ते!", "mr": "नमस्कार!"},
    "greet_evening": {"en": "Good evening!", "hi": "शुभ संध्या!", "mr": "शुभ संध्याकाळ!"},
    "who": {"en": "I am {name}, your home robot.", "hi": "मैं {name} हूँ, आपका घर का रोबोट।", "mr": "मी {name} आहे, तुमचा घरचा रोबोट."},
    "how": {"en": "I am fine, thank you. How are you?", "hi": "मैं ठीक हूँ, धन्यवाद। आप कैसे हैं?", "mr": "मी ठीक आहे, धन्यवाद. तुम्ही कसे आहात?"},
    "thanks": {"en": "You are welcome.", "hi": "आपका स्वागत है।", "mr": "तुमचं स्वागत आहे."},
    "bye": {"en": "Bye! See you soon.", "hi": "अलविदा! फिर मिलेंगे।", "mr": "टाटा! पुन्हा भेटू."},
    "time": {"en": "It is {time}.", "hi": "अभी {time} बजे हैं।", "mr": "आता {time} वाजले आहेत."},
    "date": {"en": "Today is {date}.", "hi": "आज {date} है।", "mr": "आज {date} आहे."},
    "ok": {"en": "Okay.", "hi": "ठीक है।", "mr": "ठीक आहे."},
    "stopped": {"en": "Stopped.", "hi": "रुक गई।", "mr": "थांबले."},
    "cannot": {"en": "I cannot do that now: {why}.", "hi": "मैं अभी यह नहीं कर सकती: {why}.", "mr": "मी आत्ता हे करू शकत नाही: {why}."},
    "remind_set": {"en": "Okay, I will remind you.", "hi": "ठीक है, मैं याद दिला दूँगी।", "mr": "ठीक आहे, मी आठवण करून देईन."},
    "remind_unclear": {"en": "After how many minutes?", "hi": "कितने मिनट बाद?", "mr": "किती मिनिटांनी?"},
    "remind_due": {"en": "Reminder: {text}", "hi": "याद दिला रही हूँ: {text}", "mr": "आठवण: {text}"},
    "remembered": {"en": "I will remember that.", "hi": "मैं याद रखूँगी।", "mr": "मी लक्षात ठेवीन."},
    "remember_unclear": {"en": "What should I remember?", "hi": "क्या याद रखूँ?", "mr": "काय लक्षात ठेवू?"},
    "recall_none": {"en": "I have no notes yet.", "hi": "अभी कुछ याद नहीं है।", "mr": "अजून काही लक्षात नाही."},
    "recall": {"en": "I remember: {text}", "hi": "मुझे याद है: {text}", "mr": "मला आठवतं: {text}"},
    "forget_hint": {"en": "To erase my memory, use the control page.", "hi": "याददाश्त मिटाने के लिए कंट्रोल पेज इस्तेमाल करें।",
                    "mr": "आठवणी पुसण्यासाठी कंट्रोल पेज वापरा."},
    "cancelled": {"en": "Reminders cancelled.", "hi": "रिमाइंडर रद्द किए।", "mr": "आठवणी रद्द केल्या."},
    "status_ok": {"en": "I am okay.", "hi": "मैं ठीक हूँ।", "mr": "मी ठीक आहे."},
    "status_bad": {"en": "Something needs attention: {why}.", "hi": "कुछ देखना पड़ेगा: {why}.", "mr": "काहीतरी बघावं लागेल: {why}."},
    "sleep": {"en": "Good night.", "hi": "शुभ रात्रि।", "mr": "शुभ रात्री."},
    "wake": {"en": "I am awake.", "hi": "मैं जाग गई।", "mr": "मी जागी आहे."},
    "unknown": {"en": "Sorry, I did not understand.", "hi": "माफ़ कीजिए, मैं समझी नहीं।", "mr": "माफ करा, मला समजलं नाही."},
    "joke": {"en": ["Why did the robot go on holiday? To recharge its batteries!",
                    "What is a robot's favourite snack? Computer chips!"],
             "hi": ["रोबोट छुट्टी पर क्यों गया? अपनी बैटरी चार्ज करने!", "रोबोट का पसंदीदा नाश्ता क्या है? कंप्यूटर चिप्स!"],
             "mr": ["रोबोट सुट्टीवर का गेला? बॅटरी चार्ज करायला!", "रोबोटचा आवडता खाऊ कोणता? कॉम्प्युटर चिप्स!"]},
    "story": {"en": ["A thirsty crow found a pot with a little water. It dropped pebbles in, one by one, until the water rose. Then it drank happily. Clever thinking solves problems."],
              "hi": ["एक प्यासे कौए को घड़े में थोड़ा पानी मिला। उसने एक-एक कंकड़ डाला और पानी ऊपर आ गया। फिर उसने खुशी से पानी पिया। समझदारी से हर मुश्किल हल होती है।"],
              "mr": ["एका तहानलेल्या कावळ्याला माठात थोडं पाणी दिसलं. त्याने एक एक खडा टाकला आणि पाणी वर आलं. मग तो आनंदाने पाणी प्यायला. युक्तीने प्रश्न सुटतात."]},
}
# intent -> (runtime command, args). Only these actions can ever come out of speech or chat.
ACTIONS = {
    "stop": ("stop", {}),
    "forward": ("drive", {"left": 100, "right": 100, "seconds": 1.5}),
    "turn_left": ("drive", {"left": 50, "right": 110, "seconds": 1.2}),
    "turn_right": ("drive", {"left": 110, "right": 50, "seconds": 1.2}),
    "look_left": ("head_look", {"direction": "left"}), "look_right": ("head_look", {"direction": "right"}),
    "look_up": ("head_look", {"direction": "up"}), "look_down": ("head_look", {"direction": "down"}),
    "look_center": ("head_look", {"direction": "center"}),
    "sleep": ("sleep", {}), "wake": ("wake", {}),
}
_SIMPLE = {"who", "how", "thanks", "bye", "forget_hint", "remind_unclear", "remember_unclear"}


def detect_lang(text: str, default="en") -> str:
    words = set(intents.normalize(text).split())
    mr, hi = len(words & _MR_WORDS), len(words & _HI_WORDS)
    if re.search(r"[ऀ-ॿ]", text):
        return "mr" if mr > hi else "hi" if hi > mr else (default if default in ("hi", "mr") else "hi")
    if mr or hi:
        return "mr" if mr > hi else "hi" if hi > mr else default
    return "en"


def line(key: str, lang: str, rng=random, **fmt) -> str:
    entry = LINES[key].get(lang) or LINES[key]["en"]
    if isinstance(entry, list):
        entry = rng.choice(entry)
    return entry.format(**fmt)


def clean_reply(text, limit=300) -> str:
    """Model output is untrusted: keep printable text only, one paragraph, bounded length."""
    text = re.sub(r"<think>.*?</think>", " ", str(text), flags=re.S)
    text = " ".join("".join(ch if ch.isprintable() else " " for ch in text).split())
    return text[:limit]


def redact(text: str) -> str:
    """Remove things that identify people before any text may leave the house."""
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[email]", text)
    text = re.sub(r"https?://\S+", "[link]", text)
    return re.sub(r"\d[\d\s-]{5,}\d", "[number]", text)


def _post_chat(url, payload, timeout, headers=None) -> str:
    request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                     headers={"Content-Type": "application/json", **(headers or {})}, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(65537)
    if len(raw) > 65536:
        raise ValueError("model response too large")
    return json.loads(raw)["choices"][0]["message"]["content"]


class Brain:
    def __init__(self, cfg, memory=None, scheduler=None, clock=time.time, post=_post_chat, rng=None):
        self.cfg, self.memory, self.scheduler = cfg, memory, scheduler
        self._clock, self._post, self.rng = clock, post, rng or random.Random()
        self.name = cfg["robot"]["name"]
        self.default_lang = cfg["robot"]["language"]
        self.tz = timezone(timedelta(minutes=cfg["behavior"]["utc_offset_minutes"]))
        self.last_error = ""

    def _now(self) -> datetime:
        return datetime.fromtimestamp(self._clock(), self.tz)

    def greeting(self, lang) -> str:
        hour = self._now().hour
        return line("greet_morning" if 5 <= hour < 12 else "greet_day" if hour < 17 else "greet_evening", lang)

    def respond(self, text, status_reason="") -> dict:
        """-> {"reply": str, "lang": str, "action": (command, args) | None}"""
        if not isinstance(text, str) or not text.strip():
            return {"reply": "", "lang": self.default_lang, "action": None}
        text = text.strip()[:400]
        lang = detect_lang(text, self.default_lang)
        intent = intents.parse(text)
        say = lambda key, **fmt: {"reply": line(key, lang, self.rng, **fmt), "lang": lang, "action": None}
        if intent is None:
            return {"reply": self._model(text, lang) or line("unknown", lang), "lang": lang, "action": None}
        name = intent.name
        if name in ACTIONS:
            return {"reply": "", "lang": lang, "action": ACTIONS[name]}
        if name in _SIMPLE:
            return say(name, name=self.name)
        if name == "greet":
            return {"reply": self.greeting(lang), "lang": lang, "action": None}
        if name == "time":
            return say("time", time=self._now().strftime("%H:%M"))
        if name == "date":
            return say("date", date=self._now().strftime("%d-%m-%Y"))
        if name in ("joke", "story"):
            return say(name)
        if name == "status":
            return say("status_bad", why=status_reason) if status_reason else say("status_ok")
        if name == "remind" and self.scheduler:
            ok, why = self.scheduler.add_in(intent.args["seconds"], intent.args["text"])
            return say("remind_set") if ok else say("cannot", why=why)
        if name == "cancel_reminders" and self.memory:
            self.memory.cancel_reminders()
            return say("cancelled")
        if name == "remember" and self.memory:
            try:
                self.memory.add_note(intent.args["text"], consent=True)     # the person said "remember ..."
                return say("remembered")
            except ValueError as exc:
                return say("cannot", why=str(exc))
        if name == "recall" and self.memory:
            notes = self.memory.notes(3)
            return say("recall", text="; ".join(n["text"] for n in notes)) if notes else say("recall_none")
        return say("unknown")

    # -- optional language models ---------------------------------------------------
    def _model(self, text, lang) -> str:
        ai = self.cfg["ai"]
        system = (f"You are {self.name}, a friendly home robot for a family. Reply in "
                  f"{ {'en': 'English', 'hi': 'Hindi', 'mr': 'Marathi'}[lang] }, in one or two short sentences. "
                  "You cannot move, see or control anything from this chat.")
        try:
            if ai["local_llm"]["enabled"]:
                llm = ai["local_llm"]
                return clean_reply(self._post(llm["endpoint"], {
                    "messages": [{"role": "system", "content": system},
                                 {"role": "user", "content": text[:llm["max_input_chars"]]}],
                    "max_tokens": llm["max_tokens"], "temperature": 0.6}, llm["timeout_s"]))
            if ai["cloud"]["enabled"] and ai["cloud"]["privacy_consent"] is True and ai["cloud"]["send_private_data"] is False:
                return self._cloud(system, text)
        except Exception as exc:
            self.last_error = f"{type(exc).__name__}"                        # never log the text itself
        return ""

    def _cloud(self, system, text) -> str:
        cloud = self.cfg["ai"]["cloud"]
        key_path = data_path(self.cfg, cloud["key_file"])
        if os.stat(key_path).st_mode & 0o077:
            raise PermissionError("cloud key file must be chmod 600")
        day = self._now().strftime("%Y-%m-%d")
        used = 0
        if self.memory:
            stamp, _, count = (self.memory.get("cloud_day", "") or "").partition("=")
            used = int(count) if stamp == day and count.isdigit() else 0
            if used >= cloud["max_requests_per_day"]:
                raise RuntimeError("cloud daily limit reached")
            self.memory.put("cloud_day", f"{day}={used + 1}")
        key = key_path.read_text(encoding="utf-8").strip()
        return clean_reply(self._post(cloud["endpoint"], {
            "model": cloud["model"], "max_tokens": cloud["max_tokens"],
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": redact(text)[:400]}]},
            cloud["timeout_s"], {"Authorization": f"Bearer {key}"}))
