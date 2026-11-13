"""Configuración del registro de eventos de la aplicación."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from config.settings import LoggingSettings

LOGGER_NAME = "virtualcompanion"

_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"


def configure_logging(
    settings: LoggingSettings,
    *,
    console: bool = False,
) -> logging.Logger:
    """
    Configura y devuelve el logger de la aplicación.

    El registro se escribe en el archivo configurado con rotación por
    tamaño y codificación UTF-8. El directorio se crea si no existe.
    console permite añadir además una salida a la consola; el CLI
    mantiene su propia salida y lo deja desactivado.

    La función es idempotente: al invocarla de nuevo se cierran los
    manejadores anteriores para no duplicar líneas.
    """

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(settings.level)
    logger.propagate = False

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    settings.file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        settings.file,
        maxBytes=settings.max_bytes,
        backupCount=settings.backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    logger.addHandler(file_handler)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
        logger.addHandler(console_handler)

    return logger
