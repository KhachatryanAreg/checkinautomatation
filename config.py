"""
Application configuration.
Loads from config.yaml; keeps defaults for missing values.
Change config.example.yaml to config.yaml and set your Luma API key and printer.
"""

import os
from pathlib import Path

# Defaults used when config.yaml is missing or values are absent.
DEFAULTS = {
    "listen_port": 8765,
    "luma": {
        "base_url": "https://public-api.luma.com/v1/event",
        "api_key": "",
        "event_id": "",
    },
    "printer": {
        "name": "",
        "use_raw": True,
    },
    "logging": {
        "checkin_log_path": "checkins.csv",
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Merge override into base recursively; override wins."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(config_path: str | None = None) -> dict:
    """
    Load config from YAML file. Falls back to DEFAULTS if file missing.
    Returns a single dict with listen_port, luma, printer, logging.
    """
    if config_path is None:
        base = Path(__file__).resolve().parent
        config_path = base / "config.yaml"

    config = dict(DEFAULTS)
    path = Path(config_path)
    if path.exists():
        try:
            import yaml
            with open(path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
            if loaded:
                config = _deep_merge(config, loaded)
        except Exception:
            pass
    return config


def get_listen_port(config: dict) -> int:
    return int(config.get("listen_port", DEFAULTS["listen_port"]))


def get_luma_settings(config: dict) -> dict:
    return config.get("luma", DEFAULTS["luma"])


def get_printer_settings(config: dict) -> dict:
    return config.get("printer", DEFAULTS["printer"])


def get_log_settings(config: dict) -> dict:
    return config.get("logging", DEFAULTS["logging"])
