"""
Formato de las métricas de parpadeo para el overlay.

Este módulo no depende de OpenCV ni del detector. Su única
responsabilidad es convertir los valores numéricos en texto
para la interfaz.
"""


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
):
    """
    Construye las líneas de texto del overlay de métricas.

    Devuelve cadenas sin formato gráfico para mantener separada
    la presentación del cálculo de las métricas. Las métricas de
    cierre prolongado son opcionales para conservar la
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
