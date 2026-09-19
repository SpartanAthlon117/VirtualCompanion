# Changelog

## [Unreleased]

### Added

* `vision/src/eye_state.py` con la clase `EyeStateClassifier`.
* Clasificación básica del estado ocular mediante EAR.
* Utilización del EAR calibrado como referencia para la clasificación.
* Estados `OPEN` y `CLOSED`.
* Clasificación independiente de la detección facial.

### Changed

- `face_tracker.py`: integración del clasificador de estado ocular y visualización del estado `OPEN/CLOSED` en la interfaz.
- `README.md`: actualización del estado actual del proyecto y corrección de la estructura documentada.
- Documentación del carácter experimental del umbral utilizado para la clasificación ocular.

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
