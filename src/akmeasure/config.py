"""Load and save the YAML config files in ./config.

If a project has no ./config yet, defaults are copied from the package so
`import akmeasure` works out of the box regardless of where it's installed.
"""

from importlib import resources
from pathlib import Path

import yaml

CONFIG_DIR = Path("config")


def load(name):
    path = CONFIG_DIR / f"{name}.yaml"
    if not path.exists():
        CONFIG_DIR.mkdir(exist_ok=True)
        default = resources.files("akmeasure.config_defaults").joinpath(f"{name}.yaml")
        path.write_text(default.read_text())
    return yaml.safe_load(path.read_text())


def save(name, data):
    CONFIG_DIR.mkdir(exist_ok=True)
    with open(CONFIG_DIR / f"{name}.yaml", "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)
