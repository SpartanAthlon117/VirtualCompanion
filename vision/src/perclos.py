import time
from collections import deque


DEFAULT_WINDOW_SECONDS = 60.0
DEFAULT_MINIMUM_OBSERVATION_SECONDS = 20.0


class PerclosCalculator:
    """
    Calcula un PERCLOS simplificado a partir del estado ocular.

    PERCLOS se define como la proporción del tiempo de observación
    válido en el que los ojos estuvieron cerrados. El cálculo se
    realiza sobre una ventana temporal móvil y excluye los periodos
    en los que el detector está pausado, por ejemplo ante la pérdida
    del rostro.

    Asume que update() se invoca de forma periódica mientras el
    rostro está presente; un hueco no pausado se atribuye al último
    estado conocido.

    Es un indicador experimental. No es una medida clínica de fatiga
    ni sustituye una validación con evidencia independiente.
    """

    OPEN = "OPEN"
    CLOSED = "CLOSED"

    def __init__(
        self,
        window_seconds=DEFAULT_WINDOW_SECONDS,
        minimum_observation_seconds=(
            DEFAULT_MINIMUM_OBSERVATION_SECONDS
        ),
        clock=None,
    ):
        """
        Inicializa el cálculo de PERCLOS.

        window_seconds determina la ventana móvil de análisis.
        minimum_observation_seconds es el tiempo mínimo de
        observación efectiva antes de devolver un valor.
        clock permite inyectar un reloj controlable en las pruebas.
        """

        if window_seconds <= 0:
            raise ValueError(
                "window_seconds debe ser mayor que cero."
            )

        if minimum_observation_seconds < 0:
            raise ValueError(
                "minimum_observation_seconds no puede ser negativo."
            )

        if clock is not None and not callable(clock):
            raise TypeError(
                "clock debe ser una función invocable."
            )

        self.window_seconds = float(window_seconds)
        self.minimum_observation_seconds = float(
            minimum_observation_seconds
        )
        self._clock = (
            time.monotonic
            if clock is None
            else clock
        )

        self._intervals = deque()
        self._current_state = None
        self._current_start = None
        self._observation_start = None
        self._paused_at = None
        self._total_paused_duration = 0.0

    def _now(self):
        """
        Devuelve el tiempo efectivo de observación, excluyendo
        los periodos pausados.
        """

        if self._paused_at is not None:
            return (
                self._paused_at
                - self._total_paused_duration
            )

        return (
            self._clock()
            - self._total_paused_duration
        )

    def _append_interval(self, start, end, state):
        """Guarda un intervalo con duración positiva."""

        duration = end - start

        if duration <= 0:
            return

        self._intervals.append(
            (start, end, state)
        )

    def _close_current_interval(self, end):
        """Cierra el intervalo del estado actual, si existe."""

        if (
            self._current_state is not None
            and self._current_start is not None
        ):
            self._append_interval(
                self._current_start,
                end,
                self._current_state,
            )

        self._current_state = None
        self._current_start = None

    def _prune_intervals(self, current_time):
        """
        Elimina los intervalos que ya quedaron completos fuera
        de la ventana móvil.
        """

        window_start = (
            current_time
            - self.window_seconds
        )

        while (
            self._intervals
            and self._intervals[0][1] <= window_start
        ):
            self._intervals.popleft()

    def pause(self):
        """
        Pausa el cálculo y cierra el intervalo en curso.

        El tiempo pausado no se incluye en el denominador.
        """

        if self._paused_at is not None:
            return

        self._close_current_interval(self._now())
        self._paused_at = self._clock()

    def resume(self):
        """Reanuda el cálculo después de una pausa."""

        if self._paused_at is None:
            return

        self._total_paused_duration += (
            self._clock()
            - self._paused_at
        )
        self._paused_at = None

    def is_paused(self):
        """Indica si el cálculo está pausado."""

        return self._paused_at is not None

    def update(self, eye_state):
        """
        Actualiza el cálculo con el estado ocular actual.

        Devuelve el PERCLOS calculado o None si todavía no hay
        suficiente tiempo de observación. Si el cálculo está
        pausado, devuelve el último valor sin modificarlo.
        """

        if eye_state not in (
            self.OPEN,
            self.CLOSED,
        ):
            raise ValueError(
                "El estado ocular debe ser OPEN o CLOSED."
            )

        if self.is_paused():
            return self.get_perclos()

        current_time = self._now()

        if self._observation_start is None:
            self._observation_start = current_time

        if self._current_state is None:
            self._current_state = eye_state
            self._current_start = current_time
        elif eye_state != self._current_state:
            self._append_interval(
                self._current_start,
                current_time,
                self._current_state,
            )
            self._current_state = eye_state
            self._current_start = current_time

        self._prune_intervals(current_time)

        return self.get_perclos()

    def get_perclos(self):
        """
        Devuelve el PERCLOS actual como un valor entre 0.0 y 1.0.

        Devuelve None si no se alcanzó el tiempo mínimo de
        observación o si todavía no existe una ventana válida.
        """

        if self._observation_start is None:
            return None

        current_time = self._now()

        observation_duration = (
            current_time
            - self._observation_start
        )

        if observation_duration < self.minimum_observation_seconds:
            return None

        window_start = max(
            self._observation_start,
            current_time - self.window_seconds,
        )

        duration = current_time - window_start

        if duration <= 0:
            return None

        closed_duration = 0.0

        for start, end, state in self._intervals:
            if state != self.CLOSED:
                continue

            overlap_start = max(start, window_start)
            overlap_end = min(end, current_time)

            if overlap_end > overlap_start:
                closed_duration += (
                    overlap_end
                    - overlap_start
                )

        if (
            self._current_state == self.CLOSED
            and self._current_start is not None
        ):
            overlap_start = max(
                self._current_start,
                window_start,
            )

            if current_time > overlap_start:
                closed_duration += (
                    current_time
                    - overlap_start
                )

        perclos = closed_duration / duration

        return min(1.0, max(0.0, perclos))

    def get_observation_duration(self):
        """
        Devuelve el tiempo de observación efectiva en segundos,
        excluyendo las pausas.
        """

        if self._observation_start is None:
            return 0.0

        return max(
            0.0,
            self._now() - self._observation_start,
        )

    def get_window_seconds(self):
        """Devuelve la ventana móvil configurada."""

        return self.window_seconds

    def get_minimum_observation_seconds(self):
        """Devuelve el tiempo mínimo de observación configurado."""

        return self.minimum_observation_seconds

    def reset(self):
        """Reinicia completamente el cálculo y sus métricas."""

        self._intervals.clear()
        self._current_state = None
        self._current_start = None
        self._observation_start = None
        self._paused_at = None
        self._total_paused_duration = 0.0
