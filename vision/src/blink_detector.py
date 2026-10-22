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
        self.observation_start_time = None
        self.paused_at = None
        self.total_paused_duration = 0.0

        self.previous_state = None
        self.blink_detected = False
        self.blink_count = 0

        self.closed_start_time = None
        self.last_closed_duration = None

        self.blink_timestamps = deque()
        self.last_blink_time = None

        self.total_closed_duration = 0.0
        self.completed_blinks = 0

    def _now(self):
        """
        Devuelve el tiempo efectivo de observación, excluyendo
        los periodos en los que el rostro no estuvo presente.
        """

        if self.paused_at is not None:
            return (
                self.paused_at
                - self.total_paused_duration
            )

        return (
            time.monotonic()
            - self.total_paused_duration
        )

    def pause(self):
        """
        Pausa la detección y descarta el cierre ocular en curso.

        Los parpadeos ya contabilizados se conservan. El tiempo
        pausado no se incluye en las métricas temporales.
        """

        if self.paused_at is not None:
            return

        self.paused_at = time.monotonic()
        self.previous_state = None
        self.closed_start_time = None
        self.blink_detected = False

    def resume(self):
        """Reanuda la detección tras una pausa."""

        if self.paused_at is None:
            return

        self.total_paused_duration += (
            time.monotonic() - self.paused_at
        )
        self.paused_at = None

    def is_paused(self):
        """Indica si la detección está pausada."""

        return self.paused_at is not None

    def update(self, eye_state):
        """
        Actualiza el detector con el estado actual de los ojos.

        Un parpadeo se detecta cuando existe la transición:

        OPEN -> CLOSED -> OPEN

        También se mide cuánto tiempo permanecieron cerrados
        los ojos entre CLOSED y OPEN.

        Si el detector está pausado, la actualización se ignora.
        """

        self.blink_detected = False

        if eye_state not in (
            self.OPEN,
            self.CLOSED,
        ):
            raise ValueError(
                "El estado ocular debe ser OPEN o CLOSED."
            )

        if self.paused_at is not None:
            return

        current_time = self._now()

        if self.observation_start_time is None:
            self.observation_start_time = current_time

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
        Devuelve la frecuencia estimada de parpadeos por minuto.

        Utiliza el tiempo observado mientras la ventana configurada
        aún no se ha completado. Después, utiliza la ventana móvil.
        Los periodos sin rostro (pausas) se excluyen del tiempo de
        observación.
        """

        current_time = self._now()

        self._remove_expired_timestamps(current_time)

        if not self.blink_timestamps:
            return 0.0

        if self.observation_start_time is None:
            return 0.0

        elapsed_time = current_time -self.observation_start_time

        observation_window = min(
            elapsed_time,
            self.analysis_window_seconds,
        )

        if observation_window <= 0:
            return 0.0

        return (
            len(self.blink_timestamps)
            * 60.0
            / observation_window
        )

    def get_time_since_last_blink(self):
        """
        Devuelve el tiempo desde el último parpadeo completado.

        Los periodos sin rostro (pausas) no se incluyen.

        Devuelve None si todavía no se ha detectado ningún
        parpadeo.
        """

        if self.last_blink_time is None:
            return None

        current_time = self._now()

        return current_time - self.last_blink_time

    def reset(self):
        """Reinicia completamente el detector y sus métricas."""

        self.observation_start_time = None
        self.paused_at = None
        self.total_paused_duration = 0.0

        self.previous_state = None
        self.blink_detected = False
        self.blink_count = 0

        self.closed_start_time = None
        self.last_closed_duration = None

        self.blink_timestamps.clear()
        self.last_blink_time = None

        self.total_closed_duration = 0.0
        self.completed_blinks = 0

