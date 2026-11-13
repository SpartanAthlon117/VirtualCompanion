"""Carga y validación de la configuración externa del proyecto."""

from __future__ import annotations

import math
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONFIG_ENV_VAR = "VIRTUALCOMPANION_CONFIG"

_VALID_LOG_LEVELS = frozenset(
    {
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    }
)


@dataclass(frozen=True)
class VisionSettings:
    """Configuración del modelo y del motor de visión."""

    model_path: Path


@dataclass(frozen=True)
class CameraSettings:
    """Configuración de captura de video."""

    index: int
    width: int
    height: int


@dataclass(frozen=True)
class CalibrationSettings:
    """Parámetros de la calibración del EAR."""

    duration_seconds: float
    stabilization_seconds: float
    minimum_ear: float


@dataclass(frozen=True)
class EyeStateSettings:
    """Parámetros del clasificador experimental del estado ocular."""

    threshold_factor: float


@dataclass(frozen=True)
class BlinkSettings:
    """Configuración de la ventana de análisis de parpadeos."""

    analysis_window_seconds: float


@dataclass(frozen=True)
class ProlongedClosureSettings:
    """Configuración de la detección de cierres prolongados."""

    threshold_seconds: float


@dataclass(frozen=True)
class PerclosSettings:
    """Configuración de la ventana y el mínimo de observación de PERCLOS."""

    window_seconds: float
    minimum_observation_seconds: float


@dataclass(frozen=True)
class FaceSettings:
    """Configuración de la presencia del rostro."""

    loss_timeout_seconds: float


@dataclass(frozen=True)
class StateMachineSettings:
    """Heurísticas experimentales de la máquina de estados."""

    warning_perclos: float
    fatigue_perclos: float
    warning_sustain_seconds: float
    fatigue_sustain_seconds: float
    warning_closure_seconds: float
    fatigue_closure_seconds: float
    warning_to_fatigue_seconds: float
    warning_exit_perclos: float
    fatigue_exit_perclos: float
    recovery_sustain_seconds: float
    no_blink_warning_seconds: float
    no_blink_min_observation_seconds: float
    low_blink_rate_per_minute: float
    low_blink_rate_min_observation_seconds: float


@dataclass(frozen=True)
class AlertSettings:
    """Configuración del gestor de alertas."""

    warning_cooldown_seconds: float
    critical_cooldown_seconds: float
    sound_enabled: bool


@dataclass(frozen=True)
class StorageSettings:
    """Configuración de persistencia local."""

    database_path: Path


@dataclass(frozen=True)
class WebSettings:
    """Configuración del servidor web local."""

    host: str
    port: int
    preview_enabled: bool


@dataclass(frozen=True)
class LoggingSettings:
    """Configuración del registro de eventos."""

    level: str
    file: Path
    max_bytes: int
    backup_count: int


@dataclass(frozen=True)
class AppSettings:
    """Configuración completa y validada de la aplicación."""

    project_root: Path
    config_path: Path
    vision: VisionSettings
    camera: CameraSettings
    calibration: CalibrationSettings
    eye_state: EyeStateSettings
    blink: BlinkSettings
    prolonged_closure: ProlongedClosureSettings
    perclos: PerclosSettings
    face: FaceSettings
    state_machine: StateMachineSettings
    alerts: AlertSettings
    storage: StorageSettings
    web: WebSettings
    logging: LoggingSettings


def load_settings(config_path: str | Path | None = None) -> AppSettings:
    """
    Carga y valida la configuración del proyecto.

    Si config_path es None, se utiliza la variable de entorno
    VIRTUALCOMPANION_CONFIG o, en su defecto, config/default.toml.
    Las rutas relativas se resuelven desde la raíz del repositorio.
    """

    project_root = Path(__file__).resolve().parents[1]
    path = _resolve_config_path(config_path, project_root)

    if not path.is_file():
        raise FileNotFoundError(
            "No se encontró el archivo de configuración: "
            f"{path}. Crea config/default.toml o define "
            f"{CONFIG_ENV_VAR}."
        )

    try:
        with path.open("rb") as handle:
            raw = tomllib.load(handle)
    except tomllib.TOMLDecodeError as error:
        raise ValueError(
            f"La configuración TOML no es válida en {path}: {error}"
        ) from error

    vision_section = _section(raw, "vision")
    camera_section = _section(raw, "camera")
    calibration_section = _section(raw, "calibration")
    eye_state_section = _section(raw, "eye_state")
    blink_section = _section(raw, "blink")
    closure_section = _section(raw, "prolonged_closure")
    perclos_section = _section(raw, "perclos")
    face_section = _section(raw, "face")
    state_section = _section(raw, "state_machine")
    alerts_section = _section(raw, "alerts")
    storage_section = _section(raw, "storage")
    web_section = _section(raw, "web")
    logging_section = _section(raw, "logging")

    calibration = CalibrationSettings(
        duration_seconds=_number(
            calibration_section,
            "calibration",
            "duration_seconds",
            minimum=0.0,
            exclusive_minimum=True,
        ),
        stabilization_seconds=_number(
            calibration_section,
            "calibration",
            "stabilization_seconds",
            minimum=0.0,
        ),
        minimum_ear=_number(
            calibration_section,
            "calibration",
            "minimum_ear",
            minimum=0.0,
            exclusive_minimum=True,
        ),
    )

    if calibration.stabilization_seconds >= calibration.duration_seconds:
        raise ValueError(
            "calibration.stabilization_seconds debe ser menor que "
            "calibration.duration_seconds."
        )

    eye_state = EyeStateSettings(
        threshold_factor=_number(
            eye_state_section,
            "eye_state",
            "threshold_factor",
            minimum=0.0,
            maximum=1.0,
            exclusive_minimum=True,
            exclusive_maximum=True,
        )
    )

    state_machine = StateMachineSettings(
        warning_perclos=_probability(
            state_section,
            "state_machine",
            "warning_perclos",
        ),
        fatigue_perclos=_probability(
            state_section,
            "state_machine",
            "fatigue_perclos",
        ),
        warning_sustain_seconds=_number(
            state_section,
            "state_machine",
            "warning_sustain_seconds",
            minimum=0.0,
        ),
        fatigue_sustain_seconds=_number(
            state_section,
            "state_machine",
            "fatigue_sustain_seconds",
            minimum=0.0,
        ),
        warning_closure_seconds=_number(
            state_section,
            "state_machine",
            "warning_closure_seconds",
            minimum=0.0,
            exclusive_minimum=True,
        ),
        fatigue_closure_seconds=_number(
            state_section,
            "state_machine",
            "fatigue_closure_seconds",
            minimum=0.0,
            exclusive_minimum=True,
        ),
        warning_to_fatigue_seconds=_number(
            state_section,
            "state_machine",
            "warning_to_fatigue_seconds",
            minimum=0.0,
        ),
        warning_exit_perclos=_probability(
            state_section,
            "state_machine",
            "warning_exit_perclos",
        ),
        fatigue_exit_perclos=_probability(
            state_section,
            "state_machine",
            "fatigue_exit_perclos",
        ),
        recovery_sustain_seconds=_number(
            state_section,
            "state_machine",
            "recovery_sustain_seconds",
            minimum=0.0,
        ),
        no_blink_warning_seconds=_number(
            state_section,
            "state_machine",
            "no_blink_warning_seconds",
            minimum=0.0,
            exclusive_minimum=True,
        ),
        no_blink_min_observation_seconds=_number(
            state_section,
            "state_machine",
            "no_blink_min_observation_seconds",
            minimum=0.0,
        ),
        low_blink_rate_per_minute=_number(
            state_section,
            "state_machine",
            "low_blink_rate_per_minute",
            minimum=0.0,
            exclusive_minimum=True,
        ),
        low_blink_rate_min_observation_seconds=_number(
            state_section,
            "state_machine",
            "low_blink_rate_min_observation_seconds",
            minimum=0.0,
        ),
    )
    _validate_state_machine(state_machine)

    alerts = AlertSettings(
        warning_cooldown_seconds=_number(
            alerts_section,
            "alerts",
            "warning_cooldown_seconds",
            minimum=0.0,
        ),
        critical_cooldown_seconds=_number(
            alerts_section,
            "alerts",
            "critical_cooldown_seconds",
            minimum=0.0,
        ),
        sound_enabled=_boolean(
            alerts_section,
            "alerts",
            "sound_enabled",
        ),
    )

    web_host = _string(web_section, "web", "host")
    if web_host != "127.0.0.1":
        raise ValueError(
            "web.host debe ser 127.0.0.1 en el MVP. "
            "No se permite exponer el servicio en red."
        )

    logging_level = _string(
        logging_section,
        "logging",
        "level",
    ).upper()
    if logging_level not in _VALID_LOG_LEVELS:
        raise ValueError(
            "logging.level debe ser uno de: "
            f"{', '.join(sorted(_VALID_LOG_LEVELS))}."
        )

    settings = AppSettings(
        project_root=project_root,
        config_path=path,
        vision=VisionSettings(
            model_path=_path(
                vision_section,
                "vision",
                "model_path",
                project_root,
            )
        ),
        camera=CameraSettings(
            index=_integer(
                camera_section,
                "camera",
                "index",
                minimum=0,
            ),
            width=_integer(
                camera_section,
                "camera",
                "width",
                minimum=1,
            ),
            height=_integer(
                camera_section,
                "camera",
                "height",
                minimum=1,
            ),
        ),
        calibration=calibration,
        eye_state=eye_state,
        blink=BlinkSettings(
            analysis_window_seconds=_number(
                blink_section,
                "blink",
                "analysis_window_seconds",
                minimum=0.0,
                exclusive_minimum=True,
            )
        ),
        prolonged_closure=ProlongedClosureSettings(
            threshold_seconds=_number(
                closure_section,
                "prolonged_closure",
                "threshold_seconds",
                minimum=0.0,
                exclusive_minimum=True,
            )
        ),
        perclos=PerclosSettings(
            window_seconds=_number(
                perclos_section,
                "perclos",
                "window_seconds",
                minimum=0.0,
                exclusive_minimum=True,
            ),
            minimum_observation_seconds=_number(
                perclos_section,
                "perclos",
                "minimum_observation_seconds",
                minimum=0.0,
            ),
        ),
        face=FaceSettings(
            loss_timeout_seconds=_number(
                face_section,
                "face",
                "loss_timeout_seconds",
                minimum=0.0,
                exclusive_minimum=True,
            )
        ),
        state_machine=state_machine,
        alerts=alerts,
        storage=StorageSettings(
            database_path=_path(
                storage_section,
                "storage",
                "database_path",
                project_root,
            )
        ),
        web=WebSettings(
            host=web_host,
            port=_integer(
                web_section,
                "web",
                "port",
                minimum=1,
                maximum=65535,
            ),
            preview_enabled=_boolean(
                web_section,
                "web",
                "preview_enabled",
            ),
        ),
        logging=LoggingSettings(
            level=logging_level,
            file=_path(
                logging_section,
                "logging",
                "file",
                project_root,
            ),
            max_bytes=_integer(
                logging_section,
                "logging",
                "max_bytes",
                minimum=1,
            ),
            backup_count=_integer(
                logging_section,
                "logging",
                "backup_count",
                minimum=0,
            ),
        ),
    )

    return settings


def _resolve_config_path(
    config_path: str | Path | None,
    project_root: Path,
) -> Path:
    """Resuelve la ruta del archivo de configuración."""

    if config_path is None:
        env_path = os.environ.get(CONFIG_ENV_VAR)
        candidate = (
            Path(env_path).expanduser()
            if env_path
            else project_root / "config" / "default.toml"
        )
    else:
        candidate = Path(config_path).expanduser()

    if not candidate.is_absolute():
        candidate = project_root / candidate

    return candidate.resolve()


def _section(data: dict[str, Any], name: str) -> dict[str, Any]:
    """Obtiene una sección obligatoria del documento TOML."""

    value = data.get(name)

    if not isinstance(value, dict):
        raise ValueError(
            f"Falta la sección [{name}] en la configuración."
        )

    return value


def _raw(
    section: dict[str, Any],
    section_name: str,
    key: str,
) -> Any:
    """Obtiene una clave obligatoria de una sección."""

    if key not in section:
        raise ValueError(
            f"Falta la clave '{section_name}.{key}' en la configuración."
        )

    return section[key]


def _integer(
    section: dict[str, Any],
    section_name: str,
    key: str,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    """Valida y devuelve un entero."""

    value = _raw(section, section_name, key)

    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"'{section_name}.{key}' debe ser un entero."
        )

    if minimum is not None and value < minimum:
        raise ValueError(
            f"'{section_name}.{key}' debe ser mayor o igual que {minimum}."
        )

    if maximum is not None and value > maximum:
        raise ValueError(
            f"'{section_name}.{key}' debe ser menor o igual que {maximum}."
        )

    return value


def _number(
    section: dict[str, Any],
    section_name: str,
    key: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
    exclusive_minimum: bool = False,
    exclusive_maximum: bool = False,
) -> float:
    """Valida y devuelve un número finito."""

    value = _raw(section, section_name, key)

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(
            f"'{section_name}.{key}' debe ser un número."
        )

    number = float(value)

    if not math.isfinite(number):
        raise ValueError(
            f"'{section_name}.{key}' debe ser un número finito."
        )

    if minimum is not None:
        invalid = (
            number <= minimum
            if exclusive_minimum
            else number < minimum
        )
        if invalid:
            operator = "mayor que" if exclusive_minimum else "mayor o igual que"
            raise ValueError(
                f"'{section_name}.{key}' debe ser {operator} {minimum}."
            )

    if maximum is not None:
        invalid = (
            number >= maximum
            if exclusive_maximum
            else number > maximum
        )
        if invalid:
            operator = "menor que" if exclusive_maximum else "menor o igual que"
            raise ValueError(
                f"'{section_name}.{key}' debe ser {operator} {maximum}."
            )

    return number


def _probability(
    section: dict[str, Any],
    section_name: str,
    key: str,
) -> float:
    """Valida una proporción entre 0 y 1, ambos incluidos."""

    return _number(
        section,
        section_name,
        key,
        minimum=0.0,
        maximum=1.0,
    )


def _boolean(
    section: dict[str, Any],
    section_name: str,
    key: str,
) -> bool:
    """Valida y devuelve un booleano."""

    value = _raw(section, section_name, key)

    if not isinstance(value, bool):
        raise ValueError(
            f"'{section_name}.{key}' debe ser un booleano."
        )

    return value


def _string(
    section: dict[str, Any],
    section_name: str,
    key: str,
) -> str:
    """Valida y devuelve una cadena no vacía."""

    value = _raw(section, section_name, key)

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"'{section_name}.{key}' debe ser una cadena no vacía."
        )

    return value.strip()


def _path(
    section: dict[str, Any],
    section_name: str,
    key: str,
    project_root: Path,
) -> Path:
    """Valida una ruta y la resuelve desde la raíz del repositorio."""

    value = _string(section, section_name, key)
    path = Path(value).expanduser()

    if not path.is_absolute():
        path = project_root / path

    return path.resolve()


def _validate_state_machine(settings: StateMachineSettings) -> None:
    """Comprueba la coherencia de los umbrales de estado."""

    if settings.warning_perclos >= settings.fatigue_perclos:
        raise ValueError(
            "state_machine.warning_perclos debe ser menor que "
            "state_machine.fatigue_perclos."
        )

    if settings.warning_exit_perclos >= settings.warning_perclos:
        raise ValueError(
            "state_machine.warning_exit_perclos debe ser menor que "
            "state_machine.warning_perclos."
        )

    if settings.fatigue_exit_perclos >= settings.fatigue_perclos:
        raise ValueError(
            "state_machine.fatigue_exit_perclos debe ser menor que "
            "state_machine.fatigue_perclos."
        )

    if settings.fatigue_exit_perclos <= settings.warning_exit_perclos:
        raise ValueError(
            "state_machine.fatigue_exit_perclos debe ser mayor que "
            "state_machine.warning_exit_perclos."
        )

    if settings.warning_closure_seconds >= settings.fatigue_closure_seconds:
        raise ValueError(
            "state_machine.warning_closure_seconds debe ser menor que "
            "state_machine.fatigue_closure_seconds."
        )
