from vision.src.overlay_metrics import (
    build_metrics_lines,
    format_blink_rate,
    format_duration,
    format_time_since_last_blink,
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
