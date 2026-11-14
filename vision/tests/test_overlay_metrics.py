from vision.src.overlay_metrics import (
    build_assessment_lines,
    build_metrics_lines,
    format_alert_level,
    format_blink_rate,
    format_duration,
    format_perclos,
    format_state_label,
    format_time_since_last_blink,
    to_ascii_text,
    wrap_text,
)


def test_formats_durations():
    assert format_duration(0.2) == "0.200 s"
    assert format_duration(None) == "--"


def test_formats_time_since_last_blink():
    assert format_time_since_last_blink(12.34) == "12.3 s"
    assert format_time_since_last_blink(None) == "--"


def test_formats_blink_rate():
    assert format_blink_rate(12.34, 3) == "12.3 parp./min"
    assert format_blink_rate(0.0, 0) == "--"
    assert format_blink_rate(None, 3) == "--"


def test_formats_perclos():
    assert format_perclos(0.0) == "0.0 %"
    assert format_perclos(0.423) == "42.3 %"
    assert format_perclos(1.0) == "100.0 %"
    assert format_perclos(None) == "--"


def test_builds_lines_without_data():
    lines = build_metrics_lines(
        blink_count=0,
        last_closed_duration=None,
        average_closed_duration=None,
        blink_rate_per_minute=0.0,
        time_since_last_blink=None,
        paused=False,
    )

    assert lines == [
        "Parpadeos: 0",
        "Ultimo cierre: --",
        "Cierre promedio: --",
        "Frecuencia: --",
        "Desde ultimo parpadeo: --",
        "Metricas activas",
    ]


def test_builds_lines_with_data_and_pause():
    lines = build_metrics_lines(
        blink_count=2,
        last_closed_duration=0.25,
        average_closed_duration=0.3,
        blink_rate_per_minute=6.0,
        time_since_last_blink=4.2,
        paused=True,
    )

    assert lines == [
        "Parpadeos: 2",
        "Ultimo cierre: 0.250 s",
        "Cierre promedio: 0.300 s",
        "Frecuencia: 6.0 parp./min",
        "Desde ultimo parpadeo: 4.2 s",
        "Metricas en pausa (sin rostro)",
    ]


def test_builds_lines_with_prolonged_closure_metrics():
    lines = build_metrics_lines(
        blink_count=2,
        last_closed_duration=0.25,
        average_closed_duration=0.3,
        blink_rate_per_minute=6.0,
        time_since_last_blink=4.2,
        paused=False,
        current_closed_duration=0.8,
        prolonged_closure_count=1,
        prolonged_threshold_seconds=1.5,
        prolonged_active=False,
    )

    assert lines == [
        "Parpadeos: 2",
        "Ultimo cierre: 0.250 s",
        "Cierre promedio: 0.300 s",
        "Frecuencia: 6.0 parp./min",
        "Desde ultimo parpadeo: 4.2 s",
        "Cierre actual: 0.800 s",
        "Cierres prolongados: 1",
        "Umbral cierre: 1.500 s",
        "Metricas activas",
    ]


def test_marks_active_prolonged_closure():
    lines = build_metrics_lines(
        blink_count=1,
        last_closed_duration=1.6,
        average_closed_duration=1.6,
        blink_rate_per_minute=2.0,
        time_since_last_blink=1.0,
        paused=False,
        current_closed_duration=1.6,
        prolonged_closure_count=1,
        prolonged_threshold_seconds=1.5,
        prolonged_active=True,
    )

    assert "Cierre actual: 1.600 s [PROLONGADO]" in lines
    assert lines[-1] == "Metricas activas"


def test_builds_prolonged_closure_lines_without_data():
    lines = build_metrics_lines(
        blink_count=0,
        last_closed_duration=None,
        average_closed_duration=None,
        blink_rate_per_minute=0.0,
        time_since_last_blink=None,
        paused=True,
        current_closed_duration=None,
        prolonged_closure_count=2,
        prolonged_threshold_seconds=1.5,
        prolonged_active=False,
    )

    assert "Cierre actual: --" in lines
    assert "Cierres prolongados: 2" in lines
    assert "Umbral cierre: 1.500 s" in lines
    assert lines[-1] == "Metricas en pausa (sin rostro)"


def test_builds_perclos_line():
    lines = build_metrics_lines(
        blink_count=2,
        last_closed_duration=0.25,
        average_closed_duration=0.3,
        blink_rate_per_minute=6.0,
        time_since_last_blink=4.2,
        paused=False,
        perclos=0.423,
        perclos_window_seconds=60.0,
    )

    assert "PERCLOS (60 s): 42.3 %" in lines
    assert lines[-1] == "Metricas activas"


def test_builds_perclos_line_without_data():
    lines = build_metrics_lines(
        blink_count=0,
        last_closed_duration=None,
        average_closed_duration=None,
        blink_rate_per_minute=0.0,
        time_since_last_blink=None,
        paused=False,
        perclos=None,
        perclos_window_seconds=60,
    )

    assert "PERCLOS (60 s): --" in lines


def test_omits_perclos_line_without_window():
    lines = build_metrics_lines(
        blink_count=0,
        last_closed_duration=None,
        average_closed_duration=None,
        blink_rate_per_minute=0.0,
        time_since_last_blink=None,
        paused=False,
        perclos=0.5,
    )

    assert not any(
        line.startswith("PERCLOS") for line in lines
    )


def test_formats_state_and_alert_labels():
    assert format_state_label("NORMAL") == "NORMAL"
    assert format_state_label("WARNING") == "ADVERTENCIA"
    assert format_state_label("FATIGUE") == "FATIGA"
    assert format_state_label("DROWSY") == "DROWSY"

    assert format_alert_level("NONE") == "SIN ALERTA"
    assert format_alert_level("INFO") == "INFO"
    assert format_alert_level("WARNING") == "ADVERTENCIA"
    assert format_alert_level("CRITICAL") == "CRITICA"


def test_converts_text_to_ascii():
    assert (
        to_ascii_text("Evaluación ≥ fatiga — crítica")
        == "Evaluacion >= fatiga - critica"
    )


def test_wraps_text_at_word_boundaries():
    assert wrap_text("uno dos tres cuatro", 7) == [
        "uno dos",
        "tres",
        "cuatro",
    ]


def test_wraps_text_with_long_words():
    assert wrap_text("abcdefghij", 4) == [
        "abcd",
        "efgh",
        "ij",
    ]


def test_wrap_text_rejects_invalid_width():
    try:
        wrap_text("texto", 0)
    except ValueError as error:
        assert "width" in str(error)
    else:
        raise AssertionError("Se esperaba ValueError.")


def test_builds_assessment_lines_without_reasons():
    lines = build_assessment_lines(
        state="NORMAL",
        reasons=(),
        alert_level="NONE",
    )

    assert lines == [
        "Estado: NORMAL",
        "Nivel: SIN ALERTA",
        "Motivo: Sin motivos registrados.",
    ]


def test_builds_assessment_lines_with_wrapped_reason():
    lines = build_assessment_lines(
        state="WARNING",
        reasons=(
            "PERCLOS 0.25 >= 0.20 durante 10.0 s "
            "(sostenimiento: 10.0 s).",
        ),
        alert_level="WARNING",
    )

    assert lines[0] == "Estado: ADVERTENCIA"
    assert lines[1] == "Nivel: ADVERTENCIA"
    assert lines[2].startswith("Motivo: PERCLOS")
    assert any("sostenimiento" in line for line in lines)
    assert len(lines) <= 6


def test_builds_paused_assessment_lines_and_sanitizes_reason():
    lines = build_assessment_lines(
        state="FATIGUE",
        reasons=("Sin rostro: evaluación en pausa.",),
        alert_level="CRITICAL",
        paused=True,
    )

    assert lines[0] == "Estado: FATIGA (PAUSA)"
    assert lines[1] == "Nivel: CRITICA"
    assert all("ó" not in line for line in lines)
    assert any("evaluacion" in line for line in lines)


def test_assessment_lines_respect_maximum_length():
    lines = build_assessment_lines(
        state="FATIGUE",
        reasons=(
            "Primer motivo muy largo para ocupar varias lineas.",
            "Segundo motivo que tampoco deberia aparecer completo.",
        ),
        alert_level="CRITICAL",
        max_lines=4,
    )

    assert len(lines) == 4


def test_assessment_lines_show_trigger_and_recovery_hint():
    lines = build_assessment_lines(
        state="FATIGUE",
        reasons=(
            "PERCLOS 0.31 >= 0.30 durante 10.0 s "
            "(sostenimiento: 10.0 s).",
            "Recuperación: PERCLOS < 0.12 durante 20.0 s "
            "(actual: 0.31).",
        ),
        alert_level="CRITICAL",
    )

    text = " ".join(lines)

    assert "Motivo: PERCLOS" in text
    assert "Recuperacion: PERCLOS < 0.12" in text
    assert "actual: 0.31" in text
    assert len(lines) <= 8
