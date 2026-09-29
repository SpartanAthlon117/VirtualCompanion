# Changelog

## [Unreleased]

### Added

* `vision/src/eye_state.py` con la clase `EyeStateClassifier`.
* Clasificación básica del estado ocular mediante EAR.
* Utilización del EAR calibrado como referencia para la clasificación.
* Estados `OPEN` y `CLOSED`.
* Clasificación independiente de la detección facial.
* `vision/src/blink_detector.py` con la clase `BlinkDetector`.
* Detección de parpadeos mediante la transición `OPEN → CLOSED → OPEN`.
* Medición de la duración de cada cierre ocular.

### Changed

- `face_tracker.py`: integración del clasificador de estado ocular y visualización del estado `OPEN/CLOSED` en la interfaz.
- `README.md`: actualización del estado actual del proyecto y corrección de la estructura documentada.
- Documentación del carácter experimental del umbral utilizado para la clasificación ocular.
- `blink_detector.py`: corrección del registro del inicio del cierre ocular para evitar reiniciar el temporizador durante cada frame clasificado como `CLOSED`.
- `face_tracker.py`: integración de la detección de parpadeos y visualización de la duración del cierre ocular cuando se detecta un parpadeo.
- `README.md`: documentación de la detección de parpadeos y medición de duración de cierres oculares.

## [0.1.0] - 2026-09-18

### Added

* Entorno de desarrollo basado en Python 3.13.
* Repositorio Git del proyecto.
* Estructura inicial del proyecto.
* Captura de video mediante webcam.
* Detección facial mediante MediaPipe Face Landmarker.
* Obtención de landmarks faciales.
* Cálculo del Eye Aspect Ratio (EAR).
* Calibración automática del EAR de referencia.

### Notes

* La clasificación `OPEN/CLOSED` se encuentra actualmente en una etapa experimental.
* Los parámetros utilizados para determinar el estado ocular todavía no han sido validados para detección de fatiga.
* La detección de fatiga será implementada en etapas posteriores.
