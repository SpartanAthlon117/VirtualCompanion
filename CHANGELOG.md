# Changelog

## [Unreleased]

### Added

* `vision/src/state_machine.py`: `FatigueStateMachine` con estados `NORMAL`, `WARNING` y `FATIGUE`, histéresis, sostenimiento temporal, motivos explicables y recuperación sostenida.
* `vision/src/alert_manager.py`: `AlertManager` con deduplicación, cooldowns independientes por nivel y pausa sin alertas.
* `vision/src/models.py`: `Assessment` con `changed`, `paused` y `alert_level`; `AlertEvent`; `PipelineUpdate.assessment` y `PipelineUpdate.alerts`.
* `vision/src/metrics_pipeline.py`: integración de la evaluación y las alertas en cada actualización.
* `vision/src/overlay_metrics.py`: etiquetas de estado y nivel, conversión ASCII, ajuste de líneas y panel de evaluación.
* `vision/src/face_tracker.py`: panel de estado, motivo y nivel; líneas `ESTADO` y `ALERTA` en consola; registro en el log; línea `DEBUG` con estado y nivel.
* `vision/tests/test_state_machine.py`, `test_alert_manager.py`, `test_pipeline_fatigue.py` y `test_face_tracker_reporting.py`: pruebas de transiciones, alertas, integración y reporte; la suite total pasa a 195 pruebas.
* Panel que explica el PERCLOS actual y el objetivo de recuperación cuando el estado está elevado.
* `config/logging_setup.py`: logger de la aplicación con rotación por tamaño, salida UTF-8, nivel configurable y manejador de consola opcional.
* `vision/tests/test_logging_setup.py`: 6 pruebas de creación del archivo y su directorio, nivel, consola opcional, reconfiguración idempotente, rotación y UTF-8.
* Registro en archivo del inicio y fin de sesión, eventos de calibración, parpadeo, cierre prolongado y pérdida o recuperación de rostro, y errores.
* `vision/src/eye_state.py` con la clase `EyeStateClassifier`.
* Clasificación básica del estado ocular mediante EAR.
* Utilización del EAR calibrado como referencia para la clasificación.
* Estados `OPEN` y `CLOSED`.
* Clasificación independiente de la detección facial.
* `vision/src/blink_detector.py` con la clase `BlinkDetector`.
* Detección de parpadeos mediante la transición `OPEN → CLOSED → OPEN`.
* Medición de la duración de cada cierre ocular.
* `vision/tests/test_blink_detector.py`: incorporación de 13 pruebas automatizadas para verificar el comportamiento del detector de parpadeos y sus métricas temporales.
* `vision/src/face_presence.py` con `is_face_present()` y el tiempo máximo `FACE_LOSS_TIMEOUT_SECONDS`.
* Pruebas automatizadas para el calibrador EAR, la presencia de rostro y la pausa del detector de parpadeos.
* `vision/src/overlay_metrics.py` con el formato de las métricas de parpadeo para el overlay.
* `vision/tests/test_overlay_metrics.py`: pruebas del formato de las métricas del overlay.
* `vision/tests/test_face_metrics.py` y `vision/tests/test_eye_state.py`: pruebas del cálculo del EAR, validación de entradas y clasificación ocular.
* `.github/workflows/ci.yml`: integración continua en Windows/Python 3.13 con `pip check`, `compileall` y `pytest`.
* `vision/src/eye_closure.py`: detección de cierres prolongados con umbral configurable y un evento por cierre.
* `vision/tests/test_eye_closure.py`: pruebas de umbral, evento único, reapertura, pausa, reanudación, reinicio y entradas inválidas.
* Overlay de cierre actual, cierres prolongados y umbral, con etiqueta `[PROLONGADO]` cuando corresponde.
* `vision/src/perclos.py` con `PerclosCalculator`: PERCLOS simplificado con ventana móvil, pausa, mínimo de observación y reloj inyectable.
* `vision/tests/test_perclos.py`: 18 pruebas de ventanas, pausas, datos insuficientes y estados inválidos.
* `vision/src/overlay_metrics.py`: `format_perclos()` y línea `PERCLOS (ventana): porcentaje` en el overlay.
* `vision/tests/test_overlay_metrics.py`: 4 pruebas del formato y de la presencia condicional de la línea de PERCLOS.
* `docs/MVP_SCOPE.md`: alcance del MVP, decisiones cerradas, contratos de datos, esquema SQLite, backlog y criterios de aceptación.
* `docs/validation/M1.md`: resultados del smoke test técnico en Linux del 2026-11-02 y sus limitaciones.

### Changed

- Recuperación a `NORMAL` documentada como estricta: PERCLOS `< 0.12` sostenido 20 s y sin cierre `>= 1.5 s`; después de un cierre largo puede tardar aproximadamente 80 s en completarse.
- `README.md`, `docs/PROJECT_STATUS.md`, `docs/MVP_SCOPE.md`, `docs/SETUP.md`, `docs/validation/M1.md`, `PROJECT_CONTEXT.md` y `MEMORY.md`: estado, contratos, reglas, alertas, panel y validación actualizados.
- `docs/MVP_SCOPE.md` y `MEMORY.md`: alcance, decisiones y próximos pasos actualizados.
- `docs/MVP_SCOPE.md`: contratos `Assessment`, `PipelineUpdate` y `AlertEvent` alineados con el código.
- `README.md` y `docs/PROJECT_STATUS.md`: prueba manual con cámara documentada; la recuperación sostenida queda pendiente de verificación.
- `vision/src/state_machine.py`: los estados elevados explican el PERCLOS actual y el objetivo de recuperación en lugar de un mensaje genérico de histéresis.
- `face_tracker.py`: integración del clasificador de estado ocular y visualización del estado `OPEN/CLOSED` en la interfaz.
- `face_tracker.py`: integración de `PerclosCalculator` en el flujo en vivo, pausa y reanudación con la presencia del rostro, valor en el overlay y en la salida de depuración.
- `face_tracker.py`: ajuste del inicio y la separación vertical del overlay para incluir la línea de PERCLOS sin salir del frame de 480 px.
- `docs/validation/M1.md`: registro de las dos pruebas manuales de PERCLOS (2026-11-03 y 2026-11-04) en Linux, incluida la confirmación visual y de pausa.
- `docs/PROJECT_STATUS.md`, `README.md` y `MEMORY.md`: resultados de las pruebas manuales de PERCLOS y pendientes de verificación en vivo y Windows.
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
- `vision/src/face_tracker.py`: detección de pérdida de rostro por ausencia de landmarks o por resultados obsoletos (0.5 s); pausa y reanudación de la calibración y de la detección de parpadeos.
- `vision/src/ear_calibrator.py`: `pause()`/`resume()` para excluir del tiempo de calibración los periodos sin rostro.
- `vision/src/blink_detector.py`: `pause()`/`resume()` para excluir los periodos sin rostro de las métricas temporales.
- `README.md`: documentación del comportamiento ante pérdida de rostro.
- `vision/src/face_tracker.py`: visualización en el overlay de parpadeos totales, último cierre, cierre promedio, frecuencia y tiempo desde el último parpadeo, con indicador de métricas activas o en pausa.
- `README.md`: documentación de las métricas del overlay y actualización de las próximas etapas.
- `vision/src/face_tracker.py`: mensaje explícito cuando la calibración termina sin muestras válidas.
- `README.md`: estructura real del repositorio, separación entre tecnologías implementadas y contempladas, sección de calidad/CI y enlaces de documentación.
- `docs/SETUP.md`: guía canónica consolidada para Windows y referencia para Linux.
- `docs/VirtualCompanion_SETUP.md`: reducido a referencia histórica; el contenido anterior permanece en Git.
- `docs/PROJECT_STATUS.md`: estado actualizado a M1, con limitaciones y pendientes.
- `PROJECT_CONTEXT.md`: contexto breve y enlaces a documentos canónicos.
- CI inicial limitada a dependencias, compilación y pruebas; linter y formatter diferidos.
- `vision/src/face_tracker.py`: integración del detector de cierres prolongados, pausa/reanudación ante pérdida de rostro y ajuste del espacio del overlay.
- `vision/src/overlay_metrics.py`: líneas opcionales para cierre actual, cierres prolongados y umbral, manteniendo compatibilidad con las llamadas anteriores.
- `README.md`: documentación de cierres prolongados, semántica del evento, carácter experimental del umbral y enfoque de validación.
- `PROJECT_CONTEXT.md`: alcance de M1 actualizado con la detección de cierres prolongados.
- `docs/PROJECT_STATUS.md`: estado actualizado, smoke test técnico de cámara y criterio para documentar la validación funcional.
- `MEMORY.md`: estado, decisiones y siguientes pasos de la iteración.
- `docs/PROJECT_STATUS.md`: validación de M1 actualizada con el smoke test Linux del 2026-11-02.
- `README.md`, `docs/SETUP.md` y `PROJECT_CONTEXT.md`: estado, compatibilidad y próximas etapas alineados con el alcance del MVP.
- `MEMORY.md`: alcance del MVP cerrado y decisiones registradas.
- `.gitignore`: exclusión de bases SQLite, exports y logs.
- `vision/src/blink_detector.py`: un cierre que alcanza el umbral de cierre prolongado ya no se contabiliza como parpadeo ni afecta la frecuencia; su duración se sigue registrando.
- `vision/src/metrics_pipeline.py`: el límite de duración de parpadeo se toma de `prolonged_closure.threshold_seconds`, sin duplicar umbrales en la configuración.
- `vision/src/face_tracker.py`: la línea `DEBUG` se emite como máximo una vez por segundo para reducir el volumen de la consola.
- `config/default.toml`: comentario sobre el límite compartido entre parpadeos y cierres prolongados.
- `README.md` y `docs/PROJECT_STATUS.md`: semántica del conteo de parpadeos, salida del CLI y número de pruebas actualizados.
- `vision/src/face_tracker.py`: registro en archivo del inicio y fin de sesión, eventos relevantes y errores, manteniendo intacta la salida por consola.
- `README.md` y `docs/SETUP.md`: documentación del registro de eventos, su ubicación y su rotación.
- `docs/validation/M1.md`: prueba manual en Windows del 2026-11-10, con la nota sobre el conteo de parpadeos anterior al cambio de semántica.
- `docs/PROJECT_STATUS.md` y `MEMORY.md`: cierre de la etapa de motor y logging, y siguiente etapa del MVP.

### Fixed

- `vision/src/blink_detector.py`: corrección de la codificación de los docstrings (mojibake) y eliminación del BOM, preservando la lógica y las pruebas existentes.
- `vision/src/face_tracker.py`: los landmarks incompletos o los resultados obsoletos se tratan como ausencia de rostro, no como ojos cerrados.
- `vision/src/blink_detector.py`: un cierre ocular interrumpido por la pérdida de rostro ya no se contabiliza como parpadeo.

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
