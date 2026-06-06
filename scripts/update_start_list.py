import json
from pathlib import Path
import random

"""
Скрипт для заполнения race_setup.json ID'ми всех спортсменов из athletes.json.
Запускать из корня проекта:
    python scripts/update_race_setup.py
или из папки scripts:
    python update_race_setup.py
"""

DB_DIR = Path(__file__).resolve().parent.parent / "db"
ATHLETES_FILE = DB_DIR / "athletes.json"
RACE_SETUP_FILE = DB_DIR / "race_setup.json"


def main():
    with open(ATHLETES_FILE, "r", encoding="utf-8") as f:
        athletes_data = json.load(f)

    ids = [a["id"] for a in athletes_data["athletes"]]
    random.shuffle(ids)

    if RACE_SETUP_FILE.exists():
        with open(RACE_SETUP_FILE, "r", encoding="utf-8") as f:
            race_setup = json.load(f)
    else:
        race_setup = {}

    race_setup["athletes"] = ids
    if "race_name" not in race_setup:
        race_setup["race_name"] = "Sprint"

    with open(RACE_SETUP_FILE, "w", encoding="utf-8") as f:
        json.dump(race_setup, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
