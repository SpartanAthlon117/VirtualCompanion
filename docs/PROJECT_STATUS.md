# Estado del proyecto

## Fecha

2026-10-23

## Hito actual

**M1 — Visión por computadora básica.**

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
- Overlay con parpadeos totales, último cierre, cierre promedio, frecuencia, tiempo desde el último parpadeo, cierre actual, cierres prolongados y umbral.
- Suite de **74 pruebas automatizadas** para métricas, calibración, presencia de rostro, parpadeos, cierres prolongados, overlay y clasificación ocular.
- Flujo de integración continua verificado en GitHub Actions con Windows y Python 3.13 (`pip check`, `compileall` y `pytest`); ejecución #1 concluida con éxito el 2026-10-23.
- Documentación de entorno consolidada en `docs/SETUP.md`.

## Validación de M1

- **Smoke test técnico (2026-10-23):** la cámara `0` abrió correctamente, se leyeron 20 frames, el modelo se cargó y 7 frames contuvieron un rostro. El EAR promedio observado fue `0.339`, con rango `0.283–0.396`. No se guardaron imágenes ni video.
- **Alcance:** este smoke test verifica cámara, modelo y obtención de landmarks. No sustituye la validación funcional de calibración, parpadeos, cierres prolongados ni recuperación ante pérdida de rostro.
- **Pendiente:** ejecutar una sesión guiada con una persona frente a la cámara y registrar resultados de calibración, parpadeos, cierres prolongados, pérdida de rostro, gafas, distancia e iluminación.
- **Protocolo mínimo propuesto:** verificar cámara y modelo; calibrar con ojos abiertos; registrar 10 parpadeos; provocar 3 cierres superiores a 2 s; simular pérdida de rostro; repetir con gafas, dos distancias y dos condiciones de luz; anotar aciertos, falsos positivos, falsos negativos y limitaciones. No guardar imágenes.
- **Registro recomendado:** mantener el estado y el protocolo en este documento. Cuando existan resultados completos, crear `docs/validation/M1.md` (o `docs/VALIDATION.md`) con fecha, entorno, escenarios, resultados y limitaciones. No crear el documento antes de tener evidencia para evitar documentación vacía o duplicada.

## Limitaciones

- Es un prototipo académico y experimental; no es un dispositivo médico ni un sistema certificado.
- Las métricas y los umbrales no han sido validados científicamente para detectar fatiga.
- El umbral ocular actual (`0.70 × EAR de referencia`) es experimental.
- El umbral de cierre prolongado (`1.5 s` por defecto) es experimental y configurable.
- Un cierre prolongado también se contabiliza como parpadeo completado; la separación de ambas métricas queda para una etapa posterior.
- Solo se procesa un rostro.
- La generación de alertas todavía no está implementada.
- La validación funcional con cámara está pendiente; la integración continua ejecuta pruebas sin hardware.
- La verificación estática actual se limita a la compilación de sintaxis (`compileall`) y a la consistencia de dependencias (`pip check`); no incluye linter ni tipado.
- No se ha adoptado todavía un linter o formatter porque el código existente no cuenta con una configuración acordada.
- FastAPI, PostgreSQL, WebSocket, el avatar, la voz y Unity aún no están implementados.

## Pendiente

- Validación funcional de M1 con cámara y registro de resultados.
- Cálculo de la proporción de tiempo con ojos cerrados (PERCLOS simplificado).
- Estabilización y validación de las métricas de frecuencia y duración.
- Integración de indicadores y máquina de estados de fatiga.
- Generación de alertas.
- Integración con el acompañante virtual y la interfaz 3D.
- Integración con backend, persistencia y servicios externos cuando corresponda.
- Evaluación experimental con datos y metodología definidos.

## Documentos relacionados

- `README.md`: punto de entrada y resumen del proyecto.
- `docs/SETUP.md`: guía canónica de entorno y ejecución.
- `AGENTS.md`: reglas permanentes del proyecto.
- `MEMORY.md`: memoria entre sesiones.
- `CHANGELOG.md`: registro de cambios.
