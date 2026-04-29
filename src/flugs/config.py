"""FLUGS path configuration.

Resolves the runtime paths used throughout FLUGS, with the order:

1. Environment variables ``FLUGS_DATA_DIR``, ``FLUGS_CACHE_DIR``,
   ``FLUGS_CONFIG_DIR``, ``FLUGS_OUTPUT_DIR``, ``FLUGS_LOG_DIR``.
2. Defaults relative to the project root (i.e. the working tree of this
   package): ``data/``, ``cache/``, ``yaml_configs/``, ``outputs/``,
   ``logs/``.

The resolved paths are exported as module-level constants
(``DATA_DIR`` / ``CACHE_DIR`` / ``CONFIG_DIR`` / ``OUTPUT_DIR`` / ``LOG_DIR``).
"""

import os
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent.parent

_DEFAULTS = {
    "data_dir": str(_PROJECT_ROOT / "data"),
    "cache_dir": str(_PROJECT_ROOT / "cache"),
    "config_dir": str(_PROJECT_ROOT / "yaml_configs"),
    "output_dir": str(_PROJECT_ROOT / "outputs"),
    "log_dir": str(_PROJECT_ROOT / "logs"),
}

_FLUGS_ENV_MAP = {
    "data_dir": "FLUGS_DATA_DIR",
    "cache_dir": "FLUGS_CACHE_DIR",
    "config_dir": "FLUGS_CONFIG_DIR",
    "output_dir": "FLUGS_OUTPUT_DIR",
    "log_dir": "FLUGS_LOG_DIR",
}


def _resolve(key: str) -> str:
    return os.environ.get(_FLUGS_ENV_MAP[key]) or _DEFAULTS[key]


DATA_DIR = _resolve("data_dir")
CACHE_DIR = _resolve("cache_dir")
CONFIG_DIR = _resolve("config_dir")
OUTPUT_DIR = _resolve("output_dir")
LOG_DIR = _resolve("log_dir")
