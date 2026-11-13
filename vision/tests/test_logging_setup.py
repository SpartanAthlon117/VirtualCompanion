"""Pruebas de la configuración del registro de eventos."""

from dataclasses import replace
import logging

import pytest

from config.logging_setup import LOGGER_NAME, configure_logging
from config.settings import load_settings


@pytest.fixture(autouse=True)
def cleanup_logger():
    """Cierra los manejadores del logger al terminar cada prueba."""

    yield

    logger = logging.getLogger(LOGGER_NAME)

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


def make_logging_settings(tmp_path, **overrides):
    """Construye una configuración de logging aislada en tmp_path."""

    settings = load_settings().logging
    settings = replace(
        settings,
        file=tmp_path / "logs" / "app.log",
    )

    for name, value in overrides.items():
        settings = replace(settings, **{name: value})

    return settings


def test_creates_log_file_and_parent_directory(tmp_path):
    settings = make_logging_settings(tmp_path)

    logger = configure_logging(settings)
    logger.info("Hola %s", "mundo")

    assert settings.file.is_file()
    assert "INFO | Hola mundo" in settings.file.read_text(encoding="utf-8")
    assert logger.level == logging.INFO
    assert logger.propagate is False
    assert len(logger.handlers) == 1


def test_respects_configured_level(tmp_path):
    settings = make_logging_settings(tmp_path, level="WARNING")

    logger = configure_logging(settings)
    logger.info("No debe registrarse")
    logger.warning("Sí debe registrarse")

    text = settings.file.read_text(encoding="utf-8")

    assert "No debe registrarse" not in text
    assert "WARNING | Sí debe registrarse" in text


def test_adds_console_handler_when_requested(tmp_path):
    settings = make_logging_settings(tmp_path)

    logger = configure_logging(settings, console=True)

    assert len(logger.handlers) == 2
    assert any(
        isinstance(handler, logging.StreamHandler)
        and not isinstance(handler, logging.FileHandler)
        for handler in logger.handlers
    )


def test_reconfiguration_does_not_duplicate_handlers(tmp_path):
    settings = make_logging_settings(tmp_path)

    configure_logging(settings)
    logger = configure_logging(settings)
    logger.info("Una sola línea")

    text = settings.file.read_text(encoding="utf-8")

    assert len(logger.handlers) == 1
    assert text.count("Una sola línea") == 1


def test_rotates_file_when_size_is_exceeded(tmp_path):
    settings = make_logging_settings(
        tmp_path,
        max_bytes=120,
        backup_count=1,
    )

    logger = configure_logging(settings)

    for index in range(5):
        logger.info("Mensaje de prueba %d %s", index, "x" * 50)

    assert settings.file.is_file()
    assert settings.file.with_name("app.log.1").is_file()


def test_writes_utf8_without_losing_accents(tmp_path):
    settings = make_logging_settings(tmp_path)

    logger = configure_logging(settings)
    logger.info("Calibración completada: sesión válida")

    text = settings.file.read_text(encoding="utf-8")

    assert "Calibración completada: sesión válida" in text
