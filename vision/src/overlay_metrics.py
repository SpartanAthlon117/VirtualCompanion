"""
Formato de las métricas del overlay.

Este módulo no depende de OpenCV ni del detector. Su única
responsabilidad es convertir los valores numéricos y la evaluación
en texto para la interfaz.
"""

import unicodedata


_STATE_LABELS = {
    "NORMAL": "NORMAL",
    "WARNING": "ADVERTENCIA",
    "FATIGUE": "FATIGA",
}

_ALERT_LEVEL_LABELS = {
    "NONE": "SIN ALERTA",
    "INFO": "INFO",
    "WARNING": "ADVERTENCIA",
    "CRITICAL": "CRITICA",
}

_ASCII_REPLACEMENTS = (
    ("≥", ">="),
    ("≤", "<="),
    ("–", "-"),
    ("—", "-"),
    ("…", "..."),
)


def format_duration(seconds):
    """Formatea una duración en segundos con tres decimales."""

    if seconds is None:
        return "--"

    return f"{seconds:.3f} s"


def format_time_since_last_blink(seconds):
    """Formatea el tiempo transcurrido desde el último parpadeo."""

    if seconds is None:
        return "--"

    return f"{seconds:.1f} s"


def format_blink_rate(rate, blink_count):
    """
    Formatea la frecuencia de parpadeo.

    Sin parpadeos registrados no existe una estimación útil,
    por lo que se muestra "--".
    """

    if blink_count <= 0 or rate is None:
        return "--"

    return f"{rate:.1f} parp./min"


def format_perclos(value):
    """
    Formatea PERCLOS como porcentaje.

    El cálculo devuelve una proporción entre 0.0 y 1.0. Si
    todavía no hay datos suficientes, se muestra "--".
    """

    if value is None:
        return "--"

    return f"{value * 100:.1f} %"


def format_state_label(state):
    """Traduce un estado de fatiga a una etiqueta legible."""

    return _STATE_LABELS.get(state, str(state))


def format_alert_level(level):
    """Traduce un nivel de alerta a una etiqueta legible."""

    return _ALERT_LEVEL_LABELS.get(level, str(level))


def to_ascii_text(text):
    """
    Convierte un texto a ASCII para dibujarlo con OpenCV.

    OpenCV no garantiza la representación de acentos ni de símbolos
    tipográficos con las fuentes incluidas, por lo que se eliminan
    las marcas diacríticas y se sustituyen los símbolos habituales.
    """

    for original, replacement in _ASCII_REPLACEMENTS:
        text = text.replace(original, replacement)

    normalized = unicodedata.normalize("NFKD", text)

    return normalized.encode("ascii", "ignore").decode("ascii")


def wrap_text(text, width):
    """Divide un texto en líneas de como máximo ``width`` caracteres."""

    if width <= 0:
        raise ValueError("width debe ser mayor que cero.")

    words = text.split()

    if not words:
        return []

    lines = []
    current = ""

    for word in words:
        while len(word) > width:
            if current:
                lines.append(current)
                current = ""

            lines.append(word[:width])
            word = word[width:]

        if not current:
            current = word
        elif len(current) + 1 + len(word) <= width:
            current = f"{current} {word}"
        else:
            lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def build_assessment_lines(
    state,
    reasons=(),
    alert_level="NONE",
    paused=False,
    max_width=34,
    max_lines=8,
):
    """
    Construye las líneas del panel de estado y alertas.

    El panel muestra el estado, el nivel y el motivo principal. Los
    motivos se convierten a ASCII y se ajustan al ancho disponible
    para que puedan dibujarse con OpenCV.
    """

    state_label = format_state_label(state)

    if paused:
        state_label = f"{state_label} (PAUSA)"

    lines = [
        f"Estado: {state_label}",
        f"Nivel: {format_alert_level(alert_level)}",
    ]

    clean_reasons = [
        to_ascii_text(reason).strip()
        for reason in reasons
        if reason and reason.strip()
    ]

    if not clean_reasons:
        clean_reasons = ["Sin motivos registrados."]

    for index, reason in enumerate(clean_reasons):
        prefix = "Motivo: " if index == 0 else ""

        for piece in wrap_text(f"{prefix}{reason}", max_width):
            if len(lines) >= max_lines:
                return lines

            lines.append(piece)

        if len(lines) >= max_lines:
            break

    return lines


def build_metrics_lines(
    blink_count,
    last_closed_duration,
    average_closed_duration,
    blink_rate_per_minute,
    time_since_last_blink,
    paused,
    current_closed_duration=None,
    prolonged_closure_count=0,
    prolonged_threshold_seconds=None,
    prolonged_active=False,
    perclos=None,
    perclos_window_seconds=None,
):
    """
    Construye las líneas de texto del overlay de métricas.

    Devuelve cadenas sin formato gráfico para mantener separada
    la presentación del cálculo de las métricas. Las métricas de
    cierre prolongado y PERCLOS son opcionales para conservar la
    compatibilidad con llamadas anteriores.
    """

    status = (
        "Metricas en pausa (sin rostro)"
        if paused
        else "Metricas activas"
    )

    lines = [
        f"Parpadeos: {blink_count}",
        f"Ultimo cierre: {format_duration(last_closed_duration)}",
        (
            "Cierre promedio: "
            f"{format_duration(average_closed_duration)}"
        ),
        (
            "Frecuencia: "
            f"{format_blink_rate(blink_rate_per_minute, blink_count)}"
        ),
        (
            "Desde ultimo parpadeo: "
            f"{format_time_since_last_blink(time_since_last_blink)}"
        ),
    ]

    if perclos_window_seconds is not None:
        lines.append(
            f"PERCLOS ({perclos_window_seconds:g} s): "
            f"{format_perclos(perclos)}"
        )

    if prolonged_threshold_seconds is not None:
        current_text = format_duration(
            current_closed_duration
        )

        if (
            prolonged_active
            and current_closed_duration is not None
        ):
            current_text = f"{current_text} [PROLONGADO]"

        lines.extend(
            [
                f"Cierre actual: {current_text}",
                (
                    "Cierres prolongados: "
                    f"{prolonged_closure_count}"
                ),
                (
                    "Umbral cierre: "
                    f"{format_duration(prolonged_threshold_seconds)}"
                ),
            ]
        )

    lines.append(status)

    return lines
