import json
from pathlib import Path
from typing import Any

STATE_FILE = Path("state.json")


class StateManager:
    def __init__(self) -> None:
        if not STATE_FILE.exists():
            self.save({})

    def load(self) -> dict[str, Any]:
        with open(STATE_FILE, "r") as f:
            return json.load(f)

    def save(self, data: dict[str, Any]) -> None:
        with open(STATE_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        return self.load().get(key, default)

    def set(self, key: str, value: Any) -> None:
        data = self.load()
        data[key] = value
        self.save(data)