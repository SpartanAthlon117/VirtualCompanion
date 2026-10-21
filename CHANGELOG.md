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
* `vision/tests/test_blink_detector.py`: incorporación de 13 pruebas automatizadas para verificar el comportamiento del detector de parpadeos y sus métricas temporales.

### Changed

- `face_tracker.py`: integración del clasificador de estado ocular y visualización del estado `OPEN/CLOSED` en la interfaz.
- `README.md`: actualización del estado actual del proyecto y corrección de la estructura documentada.
- Documentación del carácter experimental del umbral utilizado para la clasificación ocular.
- `blink_detector.py`: corrección del registro del inicio del cierre ocular para evitar reiniciar el temporizador durante cada frame clasificado como `CLOSED`.
- `face_tracker.py`: integración de la detección de parpadeos y visualización de la duración del cierre ocular cuando se detecta un parpadeo.
- `README.md`: documentación de la detección de parpadeos y medición de duración de cierres oculares.
- `blink_detector.py`: ampliación del detector de parpadeos para incorporar métricas temporales.
- `blink_detector.py`: la frecuencia de parpadeo se calcula utilizando una ventana de análisis de 60 segundos.
- `blink_detector.py`: separación entre los eventos utilizados para la frecuencia de parpadeo y el registro del último parpadeo detectado.
- `README.md`: documentación de las nuevas métricas temporales del detector de parpadeos.
- `blink_detector.py`: modificación del cálculo de frecuencia para utilizar el tiempo transcurrido durante la observación inicial y la ventana temporal móvil una vez completada la duración configurada.
- `blink_detector.py`: reinicio del instante inicial de observación mediante `reset()` para iniciar correctamente un nuevo periodo de medición.
- `README.md`: documentación del cálculo híbrido de frecuencia, de las variaciones durante la observación inicial y de la necesidad de lógica adicional para detectar cierres oculares prolongados.
- `vision/requirements.txt`: versiones exactas (`opencv-contrib-python==4.14.0.94`, `mediapipe==1.1.1`, `numpy==2.2.6`); se usa `opencv-contrib-python` para evitar conflictos con el `cv2` de MediaPipe.
- `vision/requirements-dev.txt`: versión exacta de `pytest`.
- `vision/src/face_tracker.py`: ruta del modelo resuelta desde `__file__` y error explícito si no existe.
- `README.md` y `docs/VirtualCompanion_SETUP.md`: instalación reproducible, descarga del modelo y ejecución de pruebas.
- `docs/SETUP.md`: corrección de la ruta de dependencias y comandos de prueba.
- Verificada la compatibilidad de MediaPipe 1.1.1 con Python 3.13 y la carga del modelo sin cámara.

### Fixed

- `vision/src/blink_detector.py`: corrección de la codificación de los docstrings (mojibake) y eliminación del BOM, preservando la lógica y las pruebas existentes.

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
