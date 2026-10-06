import time
from collections import deque


class BlinkDetector:
    """
    Detecta eventos de parpadeo a partir de la secuencia
    temporal de estados OPEN y CLOSED de los ojos.

    También registra la duración de cada cierre ocular
    y calcula métricas temporales de parpadeo.
    """

    OPEN = "OPEN"
    CLOSED = "CLOSED"

    def __init__(self, analysis_window_seconds=60.0):
        """
        Inicializa el detector de parpadeos.

        analysis_window_seconds determina el intervalo temporal
        utilizado para calcular la frecuencia de parpadeo.
        """

        if analysis_window_seconds <= 0:
            raise ValueError(
                "analysis_window_seconds debe ser mayor que cero."
            )

        self.analysis_window_seconds = analysis_window_seconds

        self.previous_state = None
        self.blink_detected = False
        self.blink_count = 0

        self.closed_start_time = None
        self.last_closed_duration = None

        self.blink_timestamps = deque()
        self.last_blink_time = None

        self.total_closed_duration = 0.0
        self.completed_blinks = 0

    def update(self, eye_state):
        """
        Actualiza el detector con el estado actual de los ojos.

        Un parpadeo se detecta cuando existe la transición:

        OPEN -> CLOSED -> OPEN

        También se mide cuánto tiempo permanecieron cerrados
        los ojos entre CLOSED y OPEN.
        """

        self.blink_detected = False

        if eye_state not in (
            self.OPEN,
            self.CLOSED,
        ):
            raise ValueError(
                "El estado ocular debe ser OPEN o CLOSED."
            )

        current_time = time.monotonic()

        if (
            eye_state == self.CLOSED
            and self.previous_state != self.CLOSED
        ):
            self.closed_start_time = current_time

        if (
            self.previous_state == self.CLOSED
            and eye_state == self.OPEN
        ):
            if self.closed_start_time is not None:
                self.last_closed_duration = (
                    current_time - self.closed_start_time
                )

                self.total_closed_duration += (
                    self.last_closed_duration
                )

                self.completed_blinks += 1

            self.blink_detected = True
            self.blink_count += 1

            self.blink_timestamps.append(current_time)
            self.last_blink_time = current_time
            self._remove_expired_timestamps(current_time)

            self.closed_start_time = None

        self.previous_state = eye_state

    def _remove_expired_timestamps(self, current_time):
        """
        Elimina los parpadeos que quedaron fuera de la
        ventana de análisis.
        """

        minimum_time = (
            current_time - self.analysis_window_seconds
        )

        while (
            self.blink_timestamps
            and self.blink_timestamps[0] < minimum_time
        ):
            self.blink_timestamps.popleft()

    def is_blink(self):
        """Indica si se detectó un parpadeo en la última actualización."""

        return self.blink_detected

    def get_blink_count(self):
        """Devuelve la cantidad total de parpadeos detectados."""

        return self.blink_count

    def get_last_closed_duration(self):
        """
        Devuelve la duración del último cierre ocular completado
        en segundos.

        Devuelve None si todavía no se ha completado ningún
        cierre ocular.
        """

        return self.last_closed_duration

    def get_average_closed_duration(self):
        """
        Devuelve la duración promedio de los cierres oculares
        completados.

        Devuelve None si todavía no se ha completado ningún cierre.
        """

        if self.completed_blinks == 0:
            return None

        return (
            self.total_closed_duration
            / self.completed_blinks
        )

    def get_blink_rate_per_minute(self):
        """
        Devuelve la frecuencia estimada de parpadeos por minuto
        dentro de la ventana de análisis.
        """

        current_time = time.monotonic()

        self._remove_expired_timestamps(current_time)

        if not self.blink_timestamps:
            return 0.0

        return (
            len(self.blink_timestamps)
            * 60.0
            / self.analysis_window_seconds
        )

    def get_time_since_last_blink(self):
        """
        Devuelve el tiempo desde el último parpadeo completado.
        
        Devuelve None si todavía no se ha detectado ningún
        parpadeo.
        """

        if self.last_blink_time is None:
            return None

        current_time = time.monotonic()

        return current_time - self.last_blink_time

    def reset(self):
        """Reinicia completamente el detector y sus métricas."""

        self.previous_state = None
        self.blink_detected = False
        self.blink_count = 0

        self.closed_start_time = None
        self.last_closed_duration = None

        self.blink_timestamps.clear()
        self.last_blink_time = None

        self.total_closed_duration = 0.0
        self.completed_blinks = 0