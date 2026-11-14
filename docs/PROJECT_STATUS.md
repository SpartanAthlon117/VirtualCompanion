# Estado del proyecto

## Fecha

2026-11-13

## Hito actual

**M1 — Visión por computadora básica, con evaluación experimental de fatiga y alertas en el CLI.**

## Implementado

- Captura de video mediante webcam.
- Detección facial con MediaPipe Face Landmarker.
- Obtención de landmarks faciales.
- Cálculo del Eye Aspect Ratio (EAR).
- Calibración automática del EAR de referencia.
- Clasificación experimental `OPEN`/`CLOSED` basada en el EAR calibrado.
- Detección de parpadeos mediante la transición `OPEN → CLOSED → OPEN`.
- Medición de la duración de cada cierre ocular.
- Cálculo de la duración promedio de los cierres.
- Detección de cierres prolongados con umbral configurable y un evento por cierre.
- Cálculo de la frecuencia de parpadeo con ventana temporal configurable.
- Registro del tiempo transcurrido desde el último parpadeo.
- Pausa y reanudación ante pérdida de rostro, sin interpretar la ausencia como ojos cerrados.
- Overlay con parpadeos totales, último cierre, cierre promedio, frecuencia, tiempo desde el último parpadeo, PERCLOS, cierre actual, cierres prolongados y umbral.
- Cálculo de PERCLOS simplificado (`vision/src/perclos.py`) con ventana móvil de 60 s, mínimo de 20 s de observación efectiva y pausa ante la pérdida de rostro, integrado en el flujo en vivo y el overlay.
- Máquina de estados experimental (`vision/src/state_machine.py`) con `NORMAL`, `WARNING` y `FATIGUE`, histéresis, sostenimiento temporal y motivos explicables.
- Evaluación basada en PERCLOS sostenido y cierres prolongados; la frecuencia y la ausencia de parpadeo quedan como información y no escalan el estado.
- Recuperación a `NORMAL` con PERCLOS `< 0.12` sostenido durante 20 s y sin cierre `>= 1.5 s` en curso.
- Gestor de alertas (`vision/src/alert_manager.py`) con deduplicación y cooldowns independientes de 30 s para advertencias y 60 s para alertas críticas.
- Integración de la evaluación y las alertas en `MetricsPipeline`, con `Assessment` y `AlertEvent` en cada actualización.
- Panel de estado, nivel y motivo en el overlay, con indicador `(PAUSA)` y explicación del PERCLOS actual y el objetivo de recuperación.
- Salida de cambios de estado (`ESTADO`) y alertas (`ALERTA`) en consola y en el archivo de log.
- Suite de **195 pruebas automatizadas** para métricas, calibración, presencia de rostro, parpadeos, cierres prolongados, PERCLOS, configuración, logging, pipeline, motor, máquina de estados, alertas, integración, overlay y clasificación ocular.
- Registro de eventos en archivo con rotación por tamaño, nivel configurable y salida UTF-8 (`config/logging_setup.py`).
- Flujo de integración continua verificado en GitHub Actions con Windows y Python 3.13 (`pip check`, `compileall` y `pytest`); ejecución #1 concluida con éxito el 2026-10-23.
- Documentación de entorno consolidada en `docs/SETUP.md`.

## Validación de M1

- **Smoke test técnico en Linux (2026-11-02):** la cámara `0` abrió correctamente y se procesaron 164 frames en 12 s; los 164 contuvieron un rostro (100 %). La calibración completó con 61 muestras y un EAR de referencia de `0.417989`. Se observaron 85 estados `OPEN`, 4 `CLOSED`, 1 parpadeo incidental, 0 cierres prolongados y 0 pérdidas de rostro, con ~13.67 FPS. No se guardaron imágenes ni video.
- **Prueba manual de PERCLOS en Linux (2026-11-03):** calibración completada con 59 muestras. PERCLOS apareció tras 20 s de observación efectiva, descendió con ojos abiertos (14.2 % a 12.5 %), aumentó durante un cierre de 0.936 s (12.5 % a 15.7 %) y respetó las pausas por pérdida de rostro. Se registraron 13 parpadeos y ningún cierre prolongado. El operador confirmó que la línea se ve sin problemas y que cubrir la cámara detiene los cálculos.
- **Segunda prueba manual de PERCLOS (2026-11-04):** calibración completada con 54 muestras; la sesión terminó a los 30.18 s con PERCLOS en `--` porque las pausas impidieron acumular 20 s efectivos. La calibración (`Completada: True`, 54 muestras) y el contador de parpadeos (de 4 a 8) se conservaron tras las pérdidas de rostro; solo se reinició el cierre en curso, por diseño. No se produjeron errores.
- **Prueba manual en Windows (2026-11-10):** aplicación completa con cámara, 79 muestras de calibración y PERCLOS visible a los 20.02 s (33.8 %, con descenso a 24.9 % y ascenso a 37.3 % durante los cierres). Se registraron dos cierres prolongados (1.514 s y 1.520 s), pérdida y recuperación de rostro a los 21.07 s y salida limpia. El conteo de 13 parpadeos incluía dos cierres largos; con la regla vigente habría sido 11. No se guardaron imágenes ni video.
- **Prueba manual de evaluación y alertas con cámara:** se observaron `WARNING` con un cierre de 1.519 s y `FATIGUE` con un cierre de 3.0 s, junto con las alertas de advertencia y crítica. El PERCLOS mínimo fue 13.8 % a los 41.98 s y después se mantuvo entre 20.7 % y 31.8 %, por lo que la recuperación a `NORMAL` no llegó a activarse; los cierres largos también reiniciaron la espera. El panel muestra desde entonces el PERCLOS actual y el objetivo de recuperación. No se guardaron imágenes ni video.
- **Smoke test técnico en Windows (2026-10-23):** 20 frames leídos, 7 con rostro, EAR promedio `0.339` y rango `0.283–0.396`. No se guardaron imágenes ni video.
- **Alcance:** los smoke tests verifican cámara, modelo, landmarks, EAR, calibración y clasificación básica. No sustituyen la validación funcional controlada de parpadeos, cierres prolongados, recuperación ante pérdida de rostro, gafas, distancias e iluminación.
- **Pendiente:** ejecutar el protocolo controlado con una persona frente a la cámara y repetirlo en Linux; registrar aciertos, falsos positivos, falsos negativos, FPS y latencia.
- **Registro:** `docs/validation/M1.md` contiene el entorno, el procedimiento, los resultados reales y las limitaciones. No se deben añadir resultados no observados.

## Limitaciones

- Es un prototipo académico y experimental; no es un dispositivo médico ni un sistema certificado.
- Las métricas y los umbrales no han sido validados científicamente para detectar fatiga.
- El umbral ocular actual (`0.70 × EAR de referencia`) es experimental.
- El umbral de cierre prolongado (`1.5 s` por defecto) es experimental y configurable.
- Un cierre que alcanza el umbral de cierre prolongado no se contabiliza como parpadeo; se registra solo como cierre prolongado.
- El PERCLOS implementado es una versión simplificada basada en la proporción de tiempo con ojos cerrados; no aplica el criterio P80 ni ha sido validado para estimar fatiga.
- La pérdida de rostro pausa el cálculo. En sesiones con pausas frecuentes, el mínimo de 20 s efectivos puede tardar más de lo esperado; conviene revisar el timeout de frescura y mostrar el tiempo de observación efectiva.
- Solo se procesa un rostro.
- Las alertas actuales son textuales y visuales en el CLI y el overlay; el audio y la presentación web aún no están implementados.
- La recuperación a `NORMAL` es deliberadamente estricta: requiere PERCLOS `< 0.12` sostenido 20 s. Como la ventana de PERCLOS es de 60 s, después de un cierre largo pueden pasar aproximadamente 80 s antes de que el indicador salga de la ventana y se complete la recuperación. Los cierres `>= 1.5 s` reinician la espera.
- En la prueba manual con cámara no se observó la recuperación porque el PERCLOS no bajó de 0.12 y continuaron los cierres largos. El comportamiento es coherente con la regla, pero la recuperación sostenida todavía debe verificarse.
- La validación funcional controlada con cámara está pendiente; ya existe un smoke test técnico en Linux y un antecedente en Windows. La integración continua ejecuta pruebas sin hardware.
- La verificación estática actual se limita a la compilación de sintaxis (`compileall`) y a la consistencia de dependencias (`pip check`); no incluye linter ni tipado.
- No se ha adoptado todavía un linter o formatter porque el código existente no cuenta con una configuración acordada.
- FastAPI, PostgreSQL, WebSocket, el avatar, la voz y Unity aún no están implementados.

## Pendiente

- Validación funcional controlada de M1 (parpadeos, cierres prolongados, pérdida de rostro, gafas, distancias e iluminación) en Windows y Linux.
- Verificación con cámara de la recuperación sostenida a `NORMAL`, del panel de estado y de la salida de alertas.
- Estabilización y validación de las métricas de frecuencia y duración.
- Integración con el acompañante virtual y la interfaz 3D.
- Integración con backend, persistencia y servicios externos cuando corresponda.
- Evaluación experimental con datos y metodología definidos.

## Documentos relacionados

- `README.md`: punto de entrada y resumen del proyecto.
- `docs/MVP_SCOPE.md`: alcance del MVP, decisiones, contratos y backlog.
- `docs/SETUP.md`: guía canónica de entorno y ejecución.
- `docs/validation/M1.md`: resultados del smoke test técnico y limitaciones.
- `AGENTS.md`: reglas permanentes del proyecto.
- `MEMORY.md`: memoria entre sesiones.
- `CHANGELOG.md`: registro de cambios.
