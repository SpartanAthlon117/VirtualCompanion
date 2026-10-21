# MEMORY.md — Diario de Estudio
Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no
aporte.

## Estado actual
- Milestone **M1 — visión por computadora**. Único módulo implementado: `vision/`. Cadena funcional: webcam → MediaPipe `FaceLandmarker` (LIVE_STREAM) → EAR → calibración → clasificación `OPEN/CLOSED` → detección de parpadeos con métricas temporales.
- Detector de parpadeos completo: **13/13 pruebas pasan** (`vision/tests/test_blink_detector.py`, re-verificado 2026-10-21 desde la raíz). Corregidos el cálculo de frecuencia, el reinicio de `observation_start_time` en `reset()` y la codificación de los docstrings.
- **T1 completada**: `vision/src/blink_detector.py` reparado a UTF-8 sin BOM (24 secuencias mojibake), sin cambios de lógica; CRLF preservados.
- Frecuencia = **cálculo híbrido**: observación inicial por tiempo transcurrido; al completar la ventana (60 s por defecto, configurable) usa la ventana móvil. Estimaciones iniciales inestables; no leerse como fatiga.
- **Estado Git**: T1, métricas, pruebas, reglas y memoria versionadas en `master` el 2026-10-21 (commits `fix`, `test`, `chore`, `docs`).
- **P1-1/P1-3 implementadas y versionadas**: `.venv` (Python 3.13.15) con `opencv-contrib-python 4.14.0.94`, `mediapipe 1.1.1`, `numpy 2.2.6` y `pytest 9.1.1`; modelo en `vision/models/face_landmarker.task` (3.76 MB, ignorado por Git). Ruta del modelo resuelta con `pathlib` y error explícito si falta; carga del `FaceLandmarker` verificada sin cámara.
- Git: rama única `master`, remote `SpartanAthlon117/VirtualCompanion`.

## Decisiones (y por qué)
- **Gobernanza**: `AGENTS.md` (reescrito) contiene las reglas permanentes del proyecto; `MEMORY.md` es el diario entre sesiones (≤50 líneas). Leer ambos antes de trabajar.
- Ejecutar los scripts desde cualquier CWD: la ruta del modelo se resuelve desde `__file__` y Python añade `vision/src` a `sys.path`. Las pruebas importan `vision.src.*` y deben correr **desde la raíz**.
- **Dependencias exactas**: versiones fijadas en `vision/requirements*.txt`. Se usa `opencv-contrib-python` (no `opencv-python`) porque es la dependencia de MediaPipe y evita dos paquetes compitiendo por `cv2`.
- **Python 3.13 se mantiene**: MediaPipe 1.1.1 publica wheel `py3-none-win_amd64` y funciona; no fue necesario bajar a 3.12.
- Clasificación ocular: umbral = 0.70 × EAR de referencia calibrado. **Experimental**, no validado para fatiga.
- El detector solo cuenta parpadeos **completados** (`OPEN → CLOSED → OPEN`); un cierre sin reapertura no es parpadeo. Cierres prolongados/alertas requieren lógica temporal adicional.
- Idioma del proyecto: comentarios, docstrings, UI, README/docs y commits en **español** (Conventional Commits con scope).

## Aprendizajes y errores a evitar
- **Stack**: solo Python/OpenCV/MediaPipe están implementados. FastAPI, PostgreSQL, HTTP/WebSocket y la UI web del avatar figuran como contemplados en `AGENTS.md`/README, pero **no** existen en el repo (solo hay `vision/`, `data/`, `docs/`). No asumir que están instalados o integrados.
- **Bug resuelto**: `observation_start_time` se fija en la primera actualización **válida**, no en la rama que lanza `ValueError`. No reintroducir esa asignación en el bloque de error (dejaba la frecuencia siempre en `0.0`).
- **Codificación**: guardar siempre UTF-8 sin BOM. El mojibake (acentos españoles convertidos en secuencias de dos caracteres) aparece al decodificar UTF-8 como CP1252; verificarlo con una comprobación de bytes y no asumir que el editor conserva el BOM.
- No confiar en la documentación: `docs/PROJECT_STATUS.md` sigue en M0; los `SETUP.md` ya se actualizaron parcialmente, pero pueden quedar referencias obsoletas. El código y los scripts son la fuente de verdad.
- Revisar `git status` y `git diff` antes y después de cada tarea; **no sobrescribir** ni descartar cambios del usuario.
- Ejecutar pytest desde `vision/` falla con `ModuleNotFoundError: No module named 'vision'`.
- No guardar secretos, credenciales ni datos personales en `MEMORY.md`, `AGENTS.md`, Git ni documentación.

## Próximos pasos
- **P1-2**: manejar la pérdida de rostro en detector/calibrador (no interpretar ausencia de landmarks como ojos cerrados).
- **P1-4/P1-5**: integrar las métricas en el overlay y ampliar pruebas a `face_metrics`, `ear_calibrator` y `eye_state`.
- **P1-6/P1-7**: reconciliar documentación duplicada y evaluar CI/calidad estática.
