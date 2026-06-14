import json
from pathlib import Path

STATE_FILE = Path("state.json")


class StateManager:
    def __init__(self):
        if not STATE_FILE.exists():
            self.save({})

    def load(self):
        with open(STATE_FILE, "r") as f:
            return json.load(f)

    def save(self, data):
        with open(STATE_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def get(self, key, default=None):
        return self.load().get(key, default)

    def set(self, key, value):
        data = self.load()
        data[key] = value
        self.save(data)