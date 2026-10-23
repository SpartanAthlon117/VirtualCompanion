import time


DEFAULT_PROLONGED_CLOSURE_SECONDS = 1.5


class ProlongedClosureDetector:
    """
    Detecta cierres oculares que superan un umbral configurable.

    Un cierre prolongado se emite una sola vez por cierre. El
    evento es un indicador temporal y no una detección de fatiga.

    El umbral predeterminado es experimental y debe ajustarse
    con evidencia adicional antes de interpretarse clínicamente.
    """

    OPEN = "OPEN"
    CLOSED = "CLOSED"

    def __init__(
        self,
        threshold_seconds=DEFAULT_PROLONGED_CLOSURE_SECONDS,
        clock=None,
    ):
        """
        Inicializa el detector.

        threshold_seconds debe ser mayor que cero. clock permite
        inyectar un reloj controlable en las pruebas; por defecto
        se utiliza time.monotonic.
        """

        if threshold_seconds <= 0:
            raise ValueError(
                "threshold_seconds debe ser mayor que cero."
            )

        if clock is not None and not callable(clock):
            raise TypeError(
                "clock debe ser una función invocable."
            )

        self.threshold_seconds = threshold_seconds
        self._clock = (
            time.monotonic
            if clock is None
            else clock
        )

        self.previous_state = None
        self.closed_start_time = None
        self.active_prolonged = False
        self.last_event = False
        self.prolonged_count = 0
        self.last_prolonged_duration = None
        self.paused = False

    def pause(self):
        """
        Pausa el detector y descarta el cierre en curso.

        Los cierres prolongados ya contabilizados se conservan.
        """

        if self.paused:
            return

        self.paused = True
        self.previous_state = None
        self.closed_start_time = None
        self.active_prolonged = False
        self.last_event = False

    def resume(self):
        """Reanuda el detector después de una pausa."""

        if not self.paused:
            return

        self.paused = False
        self.previous_state = None
        self.closed_start_time = None
        self.active_prolonged = False
        self.last_event = False

    def is_paused(self):
        """Indica si el detector está pausado."""

        return self.paused

    def update(self, eye_state):
        """
        Actualiza el detector con el estado ocular actual.

        Devuelve True únicamente en la actualización en la que
        un cierre cruza el umbral. Un cierre que permanece
        cerrado no vuelve a emitir el evento.
        """

        self.last_event = False

        if eye_state not in (
            self.OPEN,
            self.CLOSED,
        ):
            raise ValueError(
                "El estado ocular debe ser OPEN o CLOSED."
            )

        if self.paused:
            return False

        current_time = self._clock()

        if eye_state == self.CLOSED:
            if self.previous_state != self.CLOSED:
                self.closed_start_time = current_time
                self.active_prolonged = False

            if self.closed_start_time is not None:
                duration = max(
                    0.0,
                    current_time - self.closed_start_time,
                )

                if (
                    not self.active_prolonged
                    and duration >= self.threshold_seconds
                ):
                    self.active_prolonged = True
                    self.last_event = True
                    self.prolonged_count += 1
                    self.last_prolonged_duration = duration

        elif self.previous_state == self.CLOSED:
            self._finish_closure(current_time)

        self.previous_state = eye_state

        return self.last_event

    def _finish_closure(self, current_time):
        """Cierra el conteo activo y conserva su duración final."""

        if self.closed_start_time is None:
            self.active_prolonged = False
            return

        duration = max(
            0.0,
            current_time - self.closed_start_time,
        )

        # Si el umbral se cruzó entre dos actualizaciones, el
        # evento se registra al reabrir para no perderlo.
        if (
            not self.active_prolonged
            and duration >= self.threshold_seconds
        ):
            self.active_prolonged = True
            self.last_event = True
            self.prolonged_count += 1

        if self.active_prolonged:
            self.last_prolonged_duration = duration

        self.closed_start_time = None
        self.active_prolonged = False

    def get_current_closed_duration(self):
        """
        Devuelve la duración del cierre actual en segundos.

        Devuelve None si los ojos están abiertos o si el detector
        está pausado.
        """

        if self.paused or self.closed_start_time is None:
            return None

        return max(
            0.0,
            self._clock() - self.closed_start_time,
        )

    def get_last_prolonged_duration(self):
        """
        Devuelve la duración del último cierre prolongado detectado.

        Si el cierre sigue activo, corresponde al instante en que
        se cruzó el umbral. Si la pérdida de rostro interrumpe el
        cierre, conserva la duración registrada en ese instante.
        Devuelve None si todavía no se ha detectado un cierre
        prolongado.
        """

        return self.last_prolonged_duration

    def get_prolonged_count(self):
        """Devuelve la cantidad de cierres prolongados detectados."""

        return self.prolonged_count

    def is_prolonged(self):
        """Indica si el cierre actual ya superó el umbral."""

        return self.active_prolonged

    def get_threshold_seconds(self):
        """Devuelve el umbral configurado en segundos."""

        return self.threshold_seconds

    def reset(self):
        """Reinicia completamente el detector y sus métricas."""

        self.previous_state = None
        self.closed_start_time = None
        self.active_prolonged = False
        self.last_event = False
        self.prolonged_count = 0
        self.last_prolonged_duration = None
        self.paused = False
