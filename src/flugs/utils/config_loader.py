"""YAML config loading + deep-merge into FLUGS dataclasses."""

from pathlib import Path
import logging

import yaml

from . import data_classes as dc
from ..config import CONFIG_DIR

_logger = logging.getLogger("flugs.config_loader")


def _load_yaml(path) -> dict:
    """Load a YAML file and return its contents as a dict."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def _get_section(config: dict, section: str) -> dict:
    """Extract a required section from a config dict."""
    if section not in config:
        raise KeyError(f"Missing configuration section: {section}")
    return config[section]


def _deep_merge_impl(base: dict, override: dict) -> dict:
    """Recursively merge *override* into *base*; *override* values win."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge_impl(result[key], value)
        else:
            if key not in result:
                _logger.warning(
                    "Config key '%s' not found in base, adding it anyway.", key
                )
            result[key] = value
    return result


def _resolve_config_path(yml_fn: str) -> Path:
    """Resolve a config filename to a full path in CONFIG_DIR."""
    if not yml_fn.endswith((".yml", ".yaml")):
        yml_fn += ".yml"
    return Path(CONFIG_DIR) / yml_fn


def load_config(run_name: str, filename: str) -> dc.RunConfig:
    """Load and initialize all configuration objects from YAML file."""
    # Load defaults
    defaults = _load_yaml(_resolve_config_path("defaults"))

    # Load user config and deep merge
    if filename != "defaults":
        user_config = _load_yaml(_resolve_config_path(filename))
        config = _deep_merge_impl(defaults, user_config)  # User values overwrite
    else:
        config = defaults

    # Get config sections
    run_params = _get_section(config, "run_params")
    dataset_params = _get_section(config, "dataset_params")
    land_cover_params = _get_section(config, "land_cover_params")
    footprint_model_params = _get_section(config, "footprint_model_params")
    inversion_params = _get_section(config, "inversion_params")
    diagnostic_params = _get_section(config, "diagnostic_params")

    # Initialize project config (shared by dataset and landcover)
    project_config = dc.ProjectConfig()

    dataset = dc.DatasetParams(_project_config=project_config, **dataset_params)
    landcover = dc.LandCoverParams(_project_config=project_config, **land_cover_params)
    footprint_model = dc.FootprintParams(**footprint_model_params)
    inversion = dc.InversionParams(**inversion_params)
    diagnostics = dc.DiagnosticConfig(**diagnostic_params)

    # Initialize run config as orchestrator with nested data classes
    run_config = dc.RunConfig(
        run_name=run_name,
        **run_params,
        dataset=dataset,
        landcover=landcover,
        footprint_model=footprint_model,
        inversion=inversion,
        diagnostics=diagnostics,
    )

    dataset.check_measurements_to_keep(run_config=run_config)

    return run_config


def load_synth_config(synth_path: str = "") -> dc.GenerateSynthParams:
    """Load and initialize all configuration objects from YAML file."""
    # Try getting config from YAML file
    if len(synth_path) == 0:
        synth_config = dc.GenerateSynthParams()
    else:
        try:
            config = _load_yaml(_resolve_config_path(synth_path))
            synth_params = _get_section(config, "synth_params")
            synth_config = dc.GenerateSynthParams(**synth_params)
        except:
            print(f"Could not load synth config from {synth_path}, using defaults.")
            synth_config = dc.GenerateSynthParams()

    return synth_config
