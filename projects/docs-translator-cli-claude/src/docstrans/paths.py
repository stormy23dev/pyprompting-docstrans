"""Resolve platform-appropriate paths for config, data, and logs."""

from pathlib import Path

from platformdirs import user_config_dir, user_data_dir, user_state_dir

from docstrans.constants import APP_DIR_NAME, CONFIG_FILENAME, DB_FILENAME, LOG_FILENAME


def default_config_path() -> Path:
    return Path(user_config_dir(APP_DIR_NAME)) / CONFIG_FILENAME


def default_db_path() -> Path:
    return Path(user_data_dir(APP_DIR_NAME)) / DB_FILENAME


def default_log_path() -> Path:
    return Path(user_state_dir(APP_DIR_NAME)) / LOG_FILENAME
