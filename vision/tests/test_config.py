"""Pruebas de carga y validación de la configuración externa."""

from pathlib import Path

import pytest

from config.settings import AppSettings, load_settings


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "default.toml"


def write_modified_config(
    tmp_path,
    replacements,
):
    """Copia la configuración por defecto y aplica reemplazos."""

    text = DEFAULT_CONFIG_PATH.read_text(encoding="utf-8")

    for old, new in replacements:
        if old not in text:
            raise AssertionError(
                f"No se encontró el fragmento esperado en la configuración: {old}"
            )
        text = text.replace(old, new)

    config_path = tmp_path / "custom.toml"
    config_path.write_text(text, encoding="utf-8")
    return config_path


def test_loads_default_config():
    settings = load_settings()

    assert isinstance(settings, AppSettings)
    assert settings.config_path == DEFAULT_CONFIG_PATH.resolve()
    assert settings.project_root == PROJECT_ROOT
    assert settings.camera.index == 0
    assert settings.camera.width == 640
    assert settings.camera.height == 480
    assert settings.calibration.duration_seconds == 5.0
    assert settings.eye_state.threshold_factor == 0.70
    assert settings.perclos.window_seconds == 60.0
    assert settings.perclos.minimum_observation_seconds == 20.0
    assert settings.face.loss_timeout_seconds == 0.5
    assert settings.web.host == "127.0.0.1"
    assert settings.web.port == 8000
    assert settings.logging.level == "INFO"


def test_resolves_paths_from_project_root():
    settings = load_settings()

    assert settings.vision.model_path == (
        PROJECT_ROOT / "vision" / "models" / "face_landmarker.task"
    ).resolve()
    assert settings.storage.database_path == (
        PROJECT_ROOT / "data" / "virtualcompanion.db"
    ).resolve()
    assert settings.logging.file == (
        PROJECT_ROOT / "logs" / "virtualcompanion.log"
    ).resolve()


def test_loads_custom_values_from_path(tmp_path):
    config_path = write_modified_config(
        tmp_path,
        [
            ("width = 640", "width = 800"),
            ("duration_seconds = 5.0", "duration_seconds = 8.0"),
        ],
    )

    settings = load_settings(config_path)

    assert settings.camera.width == 800
    assert settings.calibration.duration_seconds == 8.0
    assert settings.config_path == config_path.resolve()


def test_environment_variable_selects_config(tmp_path, monkeypatch):
    config_path = write_modified_config(
        tmp_path,
        [("height = 480", "height = 720")],
    )
    monkeypatch.setenv("VIRTUALCOMPANION_CONFIG", str(config_path))

    settings = load_settings()

    assert settings.camera.height == 720
    assert settings.config_path == config_path.resolve()


def test_rejects_missing_config_file(tmp_path):
    missing_path = tmp_path / "missing.toml"

    with pytest.raises(FileNotFoundError, match="No se encontró"):
        load_settings(missing_path)


def test_rejects_invalid_toml(tmp_path):
    config_path = tmp_path / "invalid.toml"
    config_path.write_text("[camera\nwidth = 640", encoding="utf-8")

    with pytest.raises(ValueError, match="TOML"):
        load_settings(config_path)


def test_rejects_missing_section(tmp_path):
    config_path = tmp_path / "incomplete.toml"
    config_path.write_text(
        "[vision]\nmodel_path = \"model.task\"\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=r"\[camera\]"):
        load_settings(config_path)


def test_rejects_invalid_eye_threshold(tmp_path):
    config_path = write_modified_config(
        tmp_path,
        [("threshold_factor = 0.70", "threshold_factor = 1.50")],
    )

    with pytest.raises(ValueError, match="eye_state.threshold_factor"):
        load_settings(config_path)


def test_rejects_non_local_web_host(tmp_path):
    config_path = write_modified_config(
        tmp_path,
        [('host = "127.0.0.1"', 'host = "0.0.0.0"')],
    )

    with pytest.raises(ValueError, match="127.0.0.1"):
        load_settings(config_path)


def test_rejects_invalid_logging_level(tmp_path):
    config_path = write_modified_config(
        tmp_path,
        [('level = "INFO"', 'level = "VERBOSE"')],
    )

    with pytest.raises(ValueError, match="logging.level"):
        load_settings(config_path)


def test_rejects_incoherent_state_thresholds(tmp_path):
    config_path = write_modified_config(
        tmp_path,
        [("warning_perclos = 0.20", "warning_perclos = 0.35")],
    )

    with pytest.raises(ValueError, match="warning_perclos"):
        load_settings(config_path)
