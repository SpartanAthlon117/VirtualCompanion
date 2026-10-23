# Contexto del proyecto

VirtualCompanion es un prototipo académico y experimental para el monitoreo de indicadores visuales asociados con fatiga y somnolencia en conductores de tractocamiones. No es un dispositivo médico, un sistema certificado ni una solución validada para prevenir accidentes.

## Alcance implementado

Actualmente el único módulo funcional es `vision/`: captura de webcam, MediaPipe Face Landmarker, cálculo del EAR, calibración, clasificación `OPEN`/`CLOSED`, detección de parpadeos, detección de cierres prolongados, métricas temporales, manejo de pérdida de rostro y overlay.

## Documentos canónicos

- `README.md`: descripción, estado, instalación resumida, ejecución y estructura.
- `docs/SETUP.md`: guía de entorno y ejecución.
- `docs/PROJECT_STATUS.md`: estado detallado, limitaciones y pendientes.
- `AGENTS.md`: reglas permanentes del proyecto.
- `MEMORY.md`: memoria entre sesiones.
- `CHANGELOG.md`: registro de cambios.

La detección de fatiga, la máquina de estados, el avatar, la voz, FastAPI, PostgreSQL y Unity todavía no forman parte del código implementado.
