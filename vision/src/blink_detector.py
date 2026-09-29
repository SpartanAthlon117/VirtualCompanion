import time


class BlinkDetector:
    """
    Detecta eventos de parpadeo a partir de la secuencia
    temporal de estados OPEN y CLOSED de los ojos.
    
    También registren la duración de cada cierre ocular.
    """

    OPEN = "OPEN"
    CLOSED = "CLOSED"

    def __init__(self):
        self.previous_state = None
        self.blink_detected = False
        self.blink_count = 0
        self.closed_start_time = None
        self.last_closed_duration = None

        self.last_closed_time = None

    def update(self, eye_state):
        """
        Actualiza el detector con el estado actual de los ojos.
        
        un parpadeo se detecta cuando existe una transición:
        
        OPEN -> CLOSED -> OPEN
        
        Tamibién se mide cuánto tiempo permaneciron cerrados los ojos entre CLOSED t OPEN
        """

        self.blink_detected = False

        if eye_state not in (
            self.OPEN,
            self.CLOSED,
        ):
            raise ValueError(
                "El estado ocular debe ser OPEN o CLOSED."
            )

        current_time =time.monotonic()

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

            self.blink_detected = True
            self.blink_count += 1

            self.closed_start_time = None

        self.previous_state = eye_state

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
        
        Devuelve NOne si todavía no se ha completado ningún cierre ocular.
        """

        return  self.last_closed_duration

    def reset(self):
        """Reinicia el estado y el contador de parpadeos."""

        self.previous_state = None
        self.blink_detected = False
        self.blink_count = 0

        self.closed_start_time = None
        self.last_closed_duration = None