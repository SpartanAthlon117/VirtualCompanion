# Contexto del proyecto

VirtualCompanion es un prototipo académico y experimental para el monitoreo de indicadores visuales asociados con fatiga y somnolencia en conductores de tractocamiones. No es un dispositivo médico, un sistema certificado ni una solución validada para prevenir accidentes.

## Alcance implementado

El módulo funcional es `vision/`: captura de webcam, MediaPipe Face Landmarker, cálculo del EAR, calibración, clasificación `OPEN`/`CLOSED`, detección de parpadeos, detección de cierres prolongados, métricas temporales, PERCLOS simplificado, máquina de estados experimental, gestor de alertas, manejo de pérdida de rostro y overlay de métricas y estado.

El 2026-11-02 se ejecutó un smoke test técnico en Linux: cámara, modelo, landmarks, EAR y calibración funcionaron sin guardar imágenes ni video. La validación funcional controlada de M1 sigue pendiente.

## Alcance planificado del MVP

El MVP acordado añade una página web local, avatar 2D, FastAPI y SQLite. La máquina de estados y el gestor de alertas ya están implementados en el CLI; la web, el backend, la persistencia, el avatar y el audio de las alertas todavía no existen. El alcance detallado, las decisiones, los contratos y el backlog están en [`docs/MVP_SCOPE.md`](docs/MVP_SCOPE.md).

## Documentos canónicos

- `README.md`: descripción, estado, instalación resumida, ejecución y estructura.
- `docs/MVP_SCOPE.md`: alcance del MVP, decisiones, contratos, esquema SQLite y backlog.
- `docs/SETUP.md`: guía de entorno y ejecución.
- `docs/PROJECT_STATUS.md`: estado detallado, limitaciones y pendientes.
- `docs/validation/M1.md`: resultados reales del smoke test técnico y limitaciones.
- `AGENTS.md`: reglas permanentes del proyecto.
- `MEMORY.md`: memoria entre sesiones.
- `CHANGELOG.md`: registro de cambios.

El avatar, la voz, FastAPI, SQLite, PostgreSQL, el login de administrador y Unity todavía no forman parte del código implementado. La presentación web y el audio de las alertas tampoco están implementados.
