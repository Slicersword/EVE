from __future__ import annotations

from datetime import date
import copy
import json
import math
from pathlib import Path
import secrets
import threading
import time
import unicodedata

from .store import HomeStore


LANGUAGES = ("en", "hi", "mr", "hi-en", "mr-en", "hi-mixed", "mr-mixed")


def text(value, limit, label="text", empty=False):
    if not isinstance(value, str) or (not value.strip() and not empty) or len(value) > limit:
        raise ValueError(f"{label} must be text within {limit} characters")
    if any(ord(c) < 32 and c not in "\n\t" for c in value):
        raise ValueError(f"invalid {label}")
    return value.strip()


def number(value, low, high, label, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"invalid {label}")
    if not low <= value <= high or (integer and type(value) is not int):
        raise ValueError(f"invalid {label}")
    return value


class HomeModule:
    def __init__(self, runtime, path):
        self.runtime = runtime
        self.lock = threading.RLock()
        self.game = self.story = self.kitchen = None
        self._stopped = False
        self.music_stop_generation = 0
        self.catalog = json.loads((Path(__file__).parent / "catalog.json").read_text(encoding="utf-8"))
        self.store = HomeStore(path)

    def _allowed(self):
        return not self._stopped and not self.runtime.behavior.sleeping

    def commands(self):
        methods = {
            "view": self.view, "game": self.game_command, "story": self.story_command,
            "kitchen": self.kitchen_command, "messages": self.messages, "capsule": self.capsule,
            "delete": self.delete, "music_stop": self.music_stop, "erase": self.erase,
            "timer": self.timer, "timers": self.timers, "timer_cancel": self.timer_cancel,
        }
        return {"home." + name: self._guard(method) for name, method in methods.items()}

    def _guard(self, method):
        def call(payload):
            with self.lock:
                if not self._allowed():
                    return False, "Wake EVE before opening home activities."
                result = copy.deepcopy(method(payload))
                self.runtime._interaction()
                return True, result
        return call

    @staticmethod
    def language(payload, default="en"):
        lang = payload.get("lang", default)
        if lang not in LANGUAGES:
            raise ValueError("choose en, hi, mr or a supported mixed language")
        return lang

    @staticmethod
    def words(values, lang):
        return values.get(lang, values.get(lang.split("-")[0], values["en"]))

    @staticmethod
    def consent(payload):
        if payload.get("confirm") is not True:
            raise ValueError("review the text and explicitly confirm saving")

    def view(self, p):
        return {"game": self.game_view(), "story": self.story_view(),
                "kitchen": self.kitchen, "stories": self.store.list("story"),
                "recipes": self.store.list("recipe"), "messages": self.messages({})["items"],
                "memories": self.store.list("capsule"), "languages": list(LANGUAGES)}

    def game_view(self):
        if not self.game:
            return None
        result = {k: v for k, v in self.game.items() if k not in ("secret", "answer")}
        if result["kind"] == "riddles":
            item = self.catalog["riddles"][result["round"] % len(self.catalog["riddles"])]
            result["question"] = self.words(item["question"], result["lang"])
            result["options"] = [self.words(x, result["lang"]) for x in item["options"]]
            base = result["lang"].split("-")[0]
            result["speech_text"] = self.words(item["question"], base) + " " + " ".join(str(i + 1) + ". " + self.words(x, base) for i, x in enumerate(item["options"]))
        return result

    def game_command(self, p):
        action = p.get("action", "status")
        if action == "start":
            kind = p.get("kind", "riddles")
            if kind not in ("riddles", "twenty", "antakshari"):
                raise ValueError("unknown game")
            players = p.get("players", ["Team 1", "Team 2"])
            if not isinstance(players, list) or not 1 <= len(players) <= 6:
                raise ValueError("choose one to six players/teams")
            self.game = {"kind": kind, "lang": self.language(p), "players": [text(x, 40, "player") for x in players],
                         "scores": [0] * len(players), "turn": 0, "round": 0, "paused": False,
                         "feedback": "", "secret": secrets.randbelow(len(self.catalog["objects"])), "questions": 0,
                         "last_title": "", "next_letter": ""}
        elif action == "end":
            self.game = None
        elif self.game is None:
            raise ValueError("start a game first")
        elif action in ("pause", "resume"):
            self.game["paused"] = action == "pause"
        elif action == "status":
            pass
        elif self.game["paused"]:
            raise ValueError("resume the game first")
        elif action == "score":
            team = number(p.get("team"), 0, len(self.game["scores"]) - 1, "team", True)
            delta = number(p.get("delta"), -1, 1, "score correction", True)
            self.game["scores"][team] = max(-1000, min(1000, self.game["scores"][team] + delta))
        elif action in ("answer", "skip"):
            g = self.game
            if g["kind"] == "riddles":
                item = self.catalog["riddles"][g["round"] % len(self.catalog["riddles"])]
                choice = p.get("choice")
                if action == "answer":
                    number(choice, 0, len(item["options"]) - 1, "answer", True)
                correct = action == "answer" and choice == item["answer"]
                if correct:
                    g["scores"][g["turn"]] += 1
                g["feedback"] = self.words(self.catalog["correct" if correct else "try_again"], g["lang"])
                if not correct:
                    g["feedback"] += " " + self.words(item["options"][item["answer"]], g["lang"])
            elif g["kind"] == "antakshari":
                title = text(p.get("title", ""), 100, "song title", empty=action == "skip")
                if action != "skip":
                    g["last_title"] = title
                    # Last orthographic cluster, not a claim of phonetic song judging.
                    clusters = []
                    for char in title:
                        if char.isalnum() or unicodedata.category(char).startswith("M"):
                            if clusters and unicodedata.category(char).startswith("M"):
                                clusters[-1] += char
                            else:
                                clusters.append(char)
                    g["next_letter"] = clusters[-1] if clusters else ""
                    g["feedback"] = self.words(self.catalog["host_judges"], g["lang"])
                else:
                    g["feedback"] = "Skipped"
            else:
                raise ValueError("use question or guess in twenty questions")
            g["round"] += 1
            g["turn"] = (g["turn"] + 1) % len(g["players"])
        elif action in ("question", "guess") and self.game["kind"] == "twenty":
            g = self.game
            if g["questions"] >= 20:
                raise ValueError("twenty questions finished; start another round")
            obj = self.catalog["objects"][g["secret"]]
            if action == "question":
                key = p.get("question")
                if key not in obj["traits"]:
                    raise ValueError("choose living, home, writing or flying")
                g["feedback"] = self.words(self.catalog["yes" if obj["traits"][key] else "no"], g["lang"])
                g["questions"] += 1
            else:
                guess = text(p.get("guess"), 60, "guess").casefold()
                correct = guess in [x.casefold() for x in obj["names"]]
                g["questions"] += 1
                g["feedback"] = self.words(self.catalog["correct" if correct else "try_again"], g["lang"])
                if correct:
                    g["scores"][g["turn"]] += 1
                    g["questions"] = 20
            if g["questions"] >= 20:
                g["feedback"] += " " + self.words(obj["label"], g["lang"])
        else:
            raise ValueError("unknown game action")
        view = self.game_view()
        self.runtime._c_expression({"name": "playful" if view else "idle"})
        reply = "Game ended"
        if view:
            reply = " ".join(x for x in (view.get("feedback"), view.get("question")) if x) or "Game ready"
            if view.get("options"):
                reply += " " + " ".join(str(i + 1) + ". " + option for i, option in enumerate(view["options"]))
        return {"game": view, "reply": reply, "speech_text": view.get("speech_text", reply) if view else reply}

    def story_view(self):
        if not self.story:
            return None
        s = self.story
        node = self.catalog["story"][s["path"][-1]]
        render = lambda value: self.words(value, s["lang"]).replace("{hero}", s["hero"])
        return {**s, "text": render(node["text"]),
                "speech_text": self.words(node["text"], s["lang"].split("-")[0]).replace("{hero}", s["hero"]),
                "choices": [render(c["label"]) for c in node.get("choices", [])],
                "recap": " ".join(render(self.catalog["story"][n]["text"]) for n in s["path"][:-1])}

    def story_command(self, p):
        action = p.get("action", "status")
        if action == "continue":
            if self.story:
                action = "resume"
            else:
                saved = self.store.list("story")
                if not saved:
                    raise ValueError("save or start a story first")
                p = {**p, "id": saved[0]["id"]}
                action = "resume_saved"
        if action == "start":
            self.story = {"hero": text(p.get("hero", "Tara"), 40, "character"),
                          "lang": self.language(p), "path": ["start"], "paused": False}
        elif action == "resume_saved":
            row = self.store.get("story", p.get("id"))
            if not row:
                raise ValueError("saved story not found")
            value = row["value"]
            if any(n not in self.catalog["story"] for n in value["path"]) or not 1 <= len(value["path"]) <= 20:
                raise ValueError("saved story is incompatible")
            self.story = {"hero": text(value["hero"], 40), "lang": self.language(value),
                          "path": list(value["path"]), "paused": False, "saved_id": row["id"]}
        elif action == "end":
            self.story = None
        elif self.story is None:
            raise ValueError("start or resume a story first")
        elif action in ("pause", "resume"):
            self.story["paused"] = action == "pause"
        elif action == "save":
            self.consent(p)
            value = {k: self.story[k] for k in ("hero", "lang", "path")}
            value["title"] = text(p.get("title", self.story["hero"] + " - lantern adventure"), 100, "title")
            self.story["saved_id"] = self.store.save("story", value, self.story.get("saved_id"))
        elif action == "choose":
            if self.story["paused"]:
                raise ValueError("resume the story first")
            choices = self.catalog["story"][self.story["path"][-1]].get("choices", [])
            index = number(p.get("choice"), 0, len(choices) - 1, "choice", True)
            self.story["path"].append(choices[index]["next"])
            # Updating deliberately retained progress is consented by Save; no
            # unsaved story or new character is persisted automatically.
            if "saved_id" in self.story:
                old = self.store.get("story", self.story["saved_id"])["value"]
                self.store.save("story", {**old, "path": self.story["path"]}, self.story["saved_id"])
        elif action != "status":
            raise ValueError("unknown story action")
        view = self.story_view()
        self.runtime._c_expression({"name": "wonder" if view else "idle"})
        return {"story": view, "reply": view["text"] if view else "Story closed",
                "speech_text": view["speech_text"] if view else "Story closed"}

    def kitchen_command(self, p):
        action = p.get("action", "status")
        if action == "start":
            steps = p.get("steps")
            if not isinstance(steps, list) or not 1 <= len(steps) <= 20:
                raise ValueError("enter one to twenty recipe steps")
            self.kitchen = {"title": text(p.get("title"), 100, "recipe title"),
                            "steps": [text(s, 500, "step") for s in steps], "index": 0,
                            "lang": self.language(p), "paused": False}
        elif action == "resume_saved":
            row = self.store.get("recipe", p.get("id"))
            if not row:
                raise ValueError("saved recipe not found")
            self.kitchen = {**row["value"], "saved_id": row["id"], "paused": False}
        elif action == "end":
            self.kitchen = None
        elif self.kitchen is None:
            raise ValueError("choose a recipe first")
        elif action in ("pause", "resume"):
            self.kitchen["paused"] = action == "pause"
        elif action == "save":
            self.consent(p)
            value = {k: self.kitchen[k] for k in ("title", "steps", "index", "lang")}
            self.kitchen["saved_id"] = self.store.save("recipe", value, self.kitchen.get("saved_id"))
        elif action in ("next", "back"):
            if self.kitchen["paused"]:
                raise ValueError("resume the recipe first")
            self.kitchen["index"] = max(0, min(len(self.kitchen["steps"]) - 1, self.kitchen["index"] + (1 if action == "next" else -1)))
            if "saved_id" in self.kitchen:
                value = {k: self.kitchen[k] for k in ("title", "steps", "index", "lang")}
                self.store.save("recipe", value, self.kitchen["saved_id"])
        elif action not in ("status", "repeat"):
            raise ValueError("unknown kitchen action")
        return {"kitchen": self.kitchen, "reply": self.kitchen["steps"][self.kitchen["index"]] if self.kitchen else "Recipe closed"}

    def timer(self, p):
        name = text(p.get("name"), 80, "timer name")
        seconds = number(p.get("seconds"), 1, 86400, "timer seconds", True)
        reminder = self.runtime.memory.add_reminder(time.time() + seconds, name)
        return {"id": reminder, "reply": "Timer saved"}

    def timers(self, p):
        return {"items": self.runtime.memory.pending_reminders()}

    def timer_cancel(self, p):
        ident = number(p.get("id"), 1, 2**63 - 1, "timer ID", True)
        return {"deleted": self.runtime.memory.cancel_reminder(ident)}

    def messages(self, p):
        if p.get("action") == "save":
            self.consent(p)
            expires = p.get("expires", 0)
            number(expires, 0, time.time() + 366 * 86400, "expiry")
            if expires and expires <= time.time():
                raise ValueError("expiry must be in the future")
            value = {"recipient": text(p.get("recipient", "Household"), 40, "recipient"),
                     "text": text(p.get("text"), 1000), "read": False, "expires": expires}
            self.store.save("message", value, p.get("id"))
        elif p.get("action") == "read":
            row = self.store.get("message", p.get("id"))
            if not row:
                raise ValueError("message not found")
            self.store.save("message", {**row["value"], "read": True}, row["id"])
        elif p.get("action", "list") != "list":
            raise ValueError("unknown message action")
        items = self.store.list("message")
        live = []
        for row in items:
            if row["value"]["expires"] and row["value"]["expires"] <= time.time():
                self.store.delete("message", row["id"])
            else:
                live.append(row)
        return {"items": live}

    def capsule(self, p):
        action = p.get("action", "list")
        if action == "save":
            self.consent(p)
            stamp = p.get("date", "")
            if stamp:
                date.fromisoformat(text(stamp, 10, "date"))
            category = p.get("category", "other")
            if category not in ("birthday", "celebration", "funny", "story", "other"):
                raise ValueError("unknown category")
            value = {"title": text(p.get("title"), 100, "title"), "text": text(p.get("text"), 1000), "date": stamp, "category": category}
            self.store.save("capsule", value, p.get("id"))
        elif action == "recap":
            ids = p.get("ids")
            if not isinstance(ids, list) or not 1 <= len(ids) <= 5:
                raise ValueError("select one to five saved memories")
            rows = [self.store.get("capsule", i) for i in ids]
            if any(r is None for r in rows):
                raise ValueError("memory not found")
            return {"reply": "\n".join(r["value"]["title"] + ": " + r["value"]["text"] for r in rows),
                    "source": "approved_local_entries", "ids": ids}
        elif action != "list":
            raise ValueError("unknown capsule action")
        return {"items": self.store.list("capsule")}

    def delete(self, p):
        kind, ident = p.get("kind"), p.get("id")
        deleted = self.store.delete(kind, ident)
        if kind == "story" and self.story and self.story.get("saved_id") == ident:
            self.story = None
        if kind == "recipe" and self.kitchen and self.kitchen.get("saved_id") == ident:
            self.kitchen = None
        return {"deleted": deleted}

    def music_stop(self, p):
        self.music_stop_generation += 1
        return {"generation": self.music_stop_generation, "reply": "Music stop requested"}

    def clear_private_data(self):
        with self.lock:
            self.game = self.story = self.kitchen = None
            self.music_stop_generation += 1
            self.store.clear()

    def erase(self, p):
        if p.get("confirm") != "ERASE HOME DATA":
            raise ValueError("confirm ERASE HOME DATA")
        self.clear_private_data()
        return {"erased": True}

    def status(self):
        return {"available": self._allowed(), "music_stop_generation": self.music_stop_generation,
                "counts": self.store.counts() if self._allowed() else {},
                "no_hardware": True}

    def stop(self):
        with self.lock:
            self._stopped = True
            self.store.close()
