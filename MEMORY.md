# MEMORY.md — Diario de Estudio
Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no
aporte.

## Estado actual
- Milestone **M1 — visión por computadora**. Único módulo implementado: `vision/`. Cadena funcional: webcam → MediaPipe `FaceLandmarker` (LIVE_STREAM) → EAR → calibración → clasificación `OPEN/CLOSED` → detección de parpadeos con métricas temporales.
- Detector de parpadeos completo: **13/13 pruebas pasan** (`vision/tests/test_blink_detector.py`, re-verificado 2026-10-21 desde la raíz). Corregidos el cálculo de frecuencia, el reinicio de `observation_start_time` en `reset()` y la codificación de los docstrings.
- **T1 completada**: `vision/src/blink_detector.py` reparado a UTF-8 sin BOM (24 secuencias mojibake), sin cambios de lógica; CRLF preservados.
- Frecuencia = **cálculo híbrido**: observación inicial por tiempo transcurrido; al completar la ventana (60 s por defecto, configurable) usa la ventana móvil. Estimaciones iniciales inestables; no leerse como fatiga.
- **Estado Git**: T1, métricas, pruebas, reglas y memoria versionadas en `master` el 2026-10-21 (commits locales `fix`, `test`, `chore`, `docs`; sin push).
- `.venv` (Python 3.13.15) solo tiene `pytest`; faltan `cv2`/`mediapipe`/`numpy` y no existe `vision/models/face_landmarker.task`.
- Git: rama única `master`, remote `SpartanAthlon117/VirtualCompanion`.

## Decisiones (y por qué)
- **Gobernanza**: `AGENTS.md` (reescrito) contiene las reglas permanentes del proyecto; `MEMORY.md` es el diario entre sesiones (≤50 líneas). Leer ambos antes de trabajar.
- Ejecutar los scripts **desde la raíz** del repo: `MODEL_PATH` es relativo al CWD y los imports de `vision/src/` son planos (dependen de que Python añada el directorio del script a `sys.path`; por eso no hay `__init__.py`).
- Las pruebas importan `vision.src.*`, así que pytest corre **desde la raíz**, no desde `vision/`.
- Clasificación ocular: umbral = 0.70 × EAR de referencia calibrado. **Experimental**, no validado para fatiga.
- El detector solo cuenta parpadeos **completados** (`OPEN → CLOSED → OPEN`); un cierre sin reapertura no es parpadeo. Cierres prolongados/alertas requieren lógica temporal adicional.
- Idioma del proyecto: comentarios, docstrings, UI, README/docs y commits en **español** (Conventional Commits con scope).

## Aprendizajes y errores a evitar
- **Stack**: solo Python/OpenCV/MediaPipe están implementados. FastAPI, PostgreSQL, HTTP/WebSocket y la UI web del avatar figuran como contemplados en `AGENTS.md`/README, pero **no** existen en el repo (solo hay `vision/`, `data/`, `docs/`). No asumir que están instalados o integrados.
- **Bug resuelto**: `observation_start_time` se fija en la primera actualización **válida**, no en la rama que lanza `ValueError`. No reintroducir esa asignación en el bloque de error (dejaba la frecuencia siempre en `0.0`).
- **Codificación**: guardar siempre UTF-8 sin BOM. El mojibake (acentos españoles convertidos en secuencias de dos caracteres) aparece al decodificar UTF-8 como CP1252; verificarlo con una comprobación de bytes y no asumir que el editor conserva el BOM.
- No confiar en la documentación: `docs/PROJECT_STATUS.md` dice M0 vs `README.md` M1; los `SETUP.md` listan archivos desactualizados. El código y los scripts son la fuente de verdad.
- Revisar `git status` y `git diff` antes y después de cada tarea; **no sobrescribir** ni descartar cambios del usuario.
- Ejecutar pytest desde `vision/` falla con `ModuleNotFoundError: No module named 'vision'`.
- No guardar secretos, credenciales ni datos personales en `MEMORY.md`, `AGENTS.md`, Git ni documentación.

## Próximos pasos
- **P1-1**: fijar versiones, instalar `vision/requirements.txt`, descargar el modelo MediaPipe y verificar compatibilidad con Python 3.13.
- **P1-3/P1-2**: ruta del modelo robusta (`pathlib`) y manejo de pérdida de rostro en detector/calibrador.
- **P1-4/P1-5**: integrar las métricas en el overlay y ampliar pruebas a `face_metrics`, `ear_calibrator` y `eye_state`.
