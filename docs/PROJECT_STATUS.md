# Estado del proyecto

## Fecha

2026-10-22

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
- Cálculo de la frecuencia de parpadeo con ventana temporal configurable.
- Registro del tiempo transcurrido desde el último parpadeo.
- Pausa y reanudación ante pérdida de rostro, sin interpretar la ausencia como ojos cerrados.
- Overlay con parpadeos totales, último cierre, cierre promedio, frecuencia y tiempo desde el último parpadeo.
- Suite de **57 pruebas automatizadas** para métricas, calibración, presencia de rostro, parpadeos, overlay y clasificación ocular.
- Flujo de integración continua configurado para Windows con Python 3.13 (`pip check`, `compileall` y `pytest`).
- Documentación de entorno consolidada en `docs/SETUP.md`.

## Limitaciones

- Es un prototipo académico y experimental; no es un dispositivo médico ni un sistema certificado.
- Las métricas y los umbrales no han sido validados científicamente para detectar fatiga.
- El umbral ocular actual (`0.70 × EAR de referencia`) es experimental.
- Solo se procesa un rostro.
- La detección de cierres prolongados y la generación de alertas todavía no están implementadas.
- La validación con cámara no está automatizada; la integración continua ejecuta pruebas sin hardware.
- La verificación estática actual se limita a la compilación de sintaxis (`compileall`) y a la consistencia de dependencias (`pip check`); no incluye linter ni tipado.
- No se ha adoptado todavía un linter o formatter porque el código existente no cuenta con una configuración acordada.
- FastAPI, PostgreSQL, WebSocket, el avatar, la voz y Unity aún no están implementados.

## Pendiente

- Estabilización y validación de las métricas de frecuencia y duración.
- Detección de indicadores de fatiga.
- Máquina de estados de fatiga.
- Integración con el acompañante virtual y la interfaz 3D.
- Integración con backend, persistencia y servicios externos cuando corresponda.
- Evaluación experimental con datos y metodología definidos.
- Primera ejecución remota del flujo de integración continua.

## Documentos relacionados

- `README.md`: punto de entrada y resumen del proyecto.
- `docs/SETUP.md`: guía canónica de entorno y ejecución.
- `AGENTS.md`: reglas permanentes del proyecto.
- `MEMORY.md`: memoria entre sesiones.
- `CHANGELOG.md`: registro de cambios.
