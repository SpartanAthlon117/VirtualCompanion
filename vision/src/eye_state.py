class EyeStateClassifier:
    """
    Clasifica el estado de los ojos utilizando el EAR
    y un valor de referencia obtenido mediante calibración.
    """

    OPEN = "OPEN"
    CLOSED = "CLOSED"

    def __init__(self, threshold_factor=0.70):
        """
        Inicializa el clasificador.

        threshold_factor determina qué proporción del
        EAR de referencia se utilizará como umbral.
        """

        if not 0.0 < threshold_factor < 1.0:
            raise ValueError(
                "threshold_factor debe estar entre 0.0 y 1.0."
            )

        self.threshold_factor = threshold_factor
        self.reference_ear = None
        self.threshold = None

    def set_reference_ear(self, reference_ear):
        """
        Establece el EAR de referencia obtenido durante
        la calibración.
        """

        if reference_ear is None:
            raise ValueError(
                "El EAR de referencia no puede ser None."
            )

        if reference_ear <= 0:
            raise ValueError(
                "El EAR de referencia debe ser mayor que cero."
            )

        self.reference_ear = reference_ear

        self.threshold = (
            reference_ear * self.threshold_factor
        )

    def classify(self, ear):
        """
        Clasifica el estado de los ojos utilizando
        el EAR actual.
        """

        if self.threshold is None:
            raise RuntimeError(
                "Primero se debe establecer el EAR de referencia."
            )

        if ear is None:
            raise ValueError(
                "El EAR actual no puede ser None."
            )

        if ear < self.threshold:
            return self.CLOSED

        return self.OPEN

    def get_threshold(self):
        """Devuelve el umbral actual de clasificación."""

        return self.threshold

    def get_reference_ear(self):
        """Devuelve el EAR de referencia actual."""

        return self.reference_ear