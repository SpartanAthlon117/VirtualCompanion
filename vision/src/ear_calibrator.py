import math
import statistics
import time

class EARCalibrator:
    """
    Realiza una calibración automática del EAR
    utilizando muestras obtenidas durante un periodo determinado.
    """

    def __init__(
            self,
            duration_seconds=5.0,
            stabilization_seconds=1.0,
            minimum_ear=0.15,
    ):
        self.duration_seconds = duration_seconds
        self.stabilization_seconds = stabilization_seconds
        self.minimum_ear = minimum_ear

        self.samples = []
        self.start_time = None
        self.reference_ear = None
        self.current_ear = None
        self.completed = False
        self.paused_at = None

    def start(self):
        """Inicia una nueva sesión de calibración."""

        self.samples = []
        self.start_time = time.monotonic()
        self.reference_ear = None
        self.current_ear = None
        self.completed = False
        self.paused_at = None

    def pause(self):
        """
        Pausa la calibración sin perder las muestras recogidas.

        El tiempo transcurrido durante la pausa no se cuenta para
        la duración total de la calibración.
        """

        if self.completed or self.paused_at is not None:
            return

        self.paused_at = time.monotonic()
        self.current_ear = None

    def resume(self):
        """
        Reanuda la calibración tras una pausa.

        El tiempo pausado se excluye del tiempo total transcurrido.
        """

        if self.completed or self.paused_at is None:
            return

        if self.start_time is not None:
            self.start_time += (
                time.monotonic() - self.paused_at
            )

        self.paused_at = None

    def is_paused(self):
        """Indica si la calibración está pausada."""

        return self.paused_at is not None

    def _get_elapsed_time(self):
        """Devuelve el tiempo transcurrido sin contar las pausas."""

        if self.start_time is None:
            return 0.0

        end_time = (
            self.paused_at
            if self.paused_at is not None
            else time.monotonic()
        )

        return max(0.0, end_time - self.start_time)

    def update(self, ear):
        """
        Recibe un nuevo valor de EAR y actualiza
        el estado de la calibración.

        Si la calibración está pausada o el EAR no es un valor
        finito, la actualización se ignora.
        """

        if self.completed or self.paused_at is not None:
            return

        if ear is None or not math.isfinite(ear):
            return

        if self.start_time is None:
            self.start()

        self.current_ear = ear

        elapsed_time = self._get_elapsed_time()

        #Durante el periodo de estabilización
        #todavía no se guardan muestras.

        if (
            elapsed_time >= self.stabilization_seconds
            and ear >= self.minimum_ear
        ):
            self.samples.append(ear)

        #Finaliza la calibración cuando se alcanza
        #el tiempo total establecido.

        if elapsed_time >= self.duration_seconds:
            self._finish()

    def _finish(self):
        """Finaliza la calibración y calcula el EAR referencia."""

        self.completed = True

        if not self.samples:
            self.reference_ear = None
            return

        self.reference_ear = statistics.mean(
            self.samples
        )

    def is_completed(self):
        """Indica si la calibración ha termiando."""

        return self.completed

    def get_progress(self):
        """
        Devuelve el progreso de calibración
        como un valor entre 0.0 y 1.0.

        El progreso no avanza mientras la calibración está pausada.
        """

        if self.start_time is None:
            return 0.0

        if self.completed:
            return 1.0

        elapsed_time = self._get_elapsed_time()

        progress = (
            elapsed_time / self.duration_seconds
        )

        return min(progress, 1.0)

    def get_reference_ear(self):
        """Devuelve el EAR de referencia calculado."""

        return self.reference_ear

    def get_current_ear(self):
        """Devuelve el último EAR recibido."""

        return self.current_ear

    def get_sample_count(self):
        """Devuelve la cantidad de muestras válidas."""

        return len(self.samples)