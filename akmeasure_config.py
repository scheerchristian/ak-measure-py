"""Load and save the YAML config files in config/."""

from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).parent / "config"


def load(name):
    with open(CONFIG_DIR / f"{name}.yaml") as f:
        return yaml.safe_load(f)


def save(name, data):
    with open(CONFIG_DIR / f"{name}.yaml", "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)
