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

    def start(self):
        """Inicia una nueva sesión de calibración."""

        self.samples = []
        self.start_time = time.monotonic()
        self.reference_ear = None
        self.current_ear = None
        self.completed = False

    def update(self, ear):
        """
        Recibe un nuevo valor de EAR y actualiza
        el estado de la calibración.
        """

        if self.completed:
            return

        if self.start_time is None:
            self.start()

        self.current_ear = ear

        elapsed_time = (
            time.monotonic() - self.start_time
        )

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
        """

        if self.start_time is None:
            return 0.0

        if self.completed:
            return 1.0

        elapsed_time = (
            time.monotonic() - self.start_time
        )

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