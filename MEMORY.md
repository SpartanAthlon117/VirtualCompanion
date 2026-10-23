# MEMORY.md — Diario de Estudio
Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no
aporte.

## Estado actual
- Milestone **M1 — visión por computadora**. Único módulo implementado: `vision/`. Cadena funcional: webcam → MediaPipe `FaceLandmarker` (LIVE_STREAM) → EAR → calibración → clasificación `OPEN/CLOSED` → parpadeos y cierres prolongados con métricas temporales → overlay.
- Suite de visión: **74/74 pruebas pasan** (`test_blink_detector`, `test_ear_calibrator`, `test_face_presence`, `test_overlay_metrics`, `test_face_metrics`, `test_eye_state`, `test_eye_closure`; re-verificado 2026-10-23 desde la raíz). Corregidos el cálculo de frecuencia, el reinicio de `observation_start_time` en `reset()` y la codificación de los docstrings.
- **T1 completada**: `vision/src/blink_detector.py` reparado a UTF-8 sin BOM (24 secuencias mojibake), sin cambios de lógica; CRLF preservados.
- Frecuencia = **cálculo híbrido**: observación inicial por tiempo transcurrido; al completar la ventana (60 s por defecto, configurable) usa la ventana móvil. Estimaciones iniciales inestables; no leerse como fatiga.
- **Git**: rama `master`; los commits se crean localmente y el push requiere aprobación explícita.
- **P1-1/P1-3 implementadas y versionadas**: `.venv` (Python 3.13.15) con `opencv-contrib-python 4.14.0.94`, `mediapipe 1.1.1`, `numpy 2.2.6` y `pytest 9.1.1`; modelo en `vision/models/face_landmarker.task` (3.76 MB, ignorado por Git). Ruta del modelo resuelta con `pathlib` y error explícito si falta; carga del `FaceLandmarker` verificada sin cámara.
- **P1-2 implementada y versionada**: pérdida de rostro con timeout de 0.5 s; calibración, parpadeos y cierres prolongados se pausan/reanudan, se descartan cierres interrumpidos y los landmarks obsoletos o incompletos se tratan como ausencia de rostro.
- **P1-4 implementada y versionada**: overlay con parpadeos totales, último cierre, cierre promedio, frecuencia y tiempo desde el último parpadeo; formato aislado en `overlay_metrics.py` y estado de pausa visible.
- **P1-5 implementada y versionada**: pruebas de `face_metrics` (distancias, EAR, escala y entradas inválidas) y `eye_state` (factores, referencia, frontera y errores).
- **P1-6/P1-7 implementadas y versionadas**: documentación consolidada en `docs/SETUP.md`, estado M1 y contexto; CI de Windows/Python 3.13 con `pip check`, `compileall` y `pytest`; linter diferido.
- **P2-1 implementada**: `vision/src/eye_closure.py` detecta cierres prolongados (umbral experimental 1.5 s, un evento por cierre, pausa/reanudación) y overlay ampliado; `BlinkDetector` no cambió.
- Git: rama única `master`, remote `SpartanAthlon117/VirtualCompanion`.

## Decisiones (y por qué)
- **Gobernanza**: `AGENTS.md` (reescrito) contiene las reglas permanentes del proyecto; `MEMORY.md` es el diario entre sesiones (≤50 líneas). Leer ambos antes de trabajar.
- Ejecutar los scripts desde cualquier CWD: la ruta del modelo se resuelve desde `__file__` y Python añade `vision/src` a `sys.path`. Las pruebas importan `vision.src.*` y deben correr **desde la raíz**.
- **Dependencias exactas**: versiones fijadas en `vision/requirements*.txt`. Se usa `opencv-contrib-python` (no `opencv-python`) porque es la dependencia de MediaPipe y evita dos paquetes compitiendo por `cv2`.
- **Python 3.13 se mantiene**: MediaPipe 1.1.1 publica wheel `py3-none-win_amd64` y funciona; no fue necesario bajar a 3.12.
- **Pérdida de rostro**: solo se considera presente si el último resultado de MediaPipe es reciente (`FACE_LOSS_TIMEOUT_SECONDS = 0.5`). Calibrador y detector pausan su tiempo y descartan el cierre en curso; la ausencia no se interpreta como `CLOSED`.
- **Overlay de métricas**: se muestra tras una calibración con referencia válida; `--` significa "sin datos" y los valores se congelan y se etiquetan cuando el rostro no está presente.
- **Documentación canónica**: `docs/SETUP.md` es la guía de entorno; `docs/VirtualCompanion_SETUP.md` queda como referencia histórica. `docs/PROJECT_STATUS.md` refleja M1.
- **CI**: Windows + Python 3.13 por ser el entorno validado; ejecuta `pip check`, `compileall` y `pytest`. Linter y formatter diferidos.
- Clasificación ocular: umbral = 0.70 × EAR de referencia calibrado. **Experimental**, no validado para fatiga.
- **Frontera de clasificación**: `ear < threshold` produce `CLOSED`; `ear == threshold` produce `OPEN`.
- El detector de parpadeos solo cuenta **cierres completados** (`OPEN → CLOSED → OPEN`); un cierre sin reapertura no es parpadeo. El detector de cierres prolongados emite una vez al cruzar el umbral; al reabrir, ese cierre también cuenta como parpadeo.
- Idioma del proyecto: comentarios, docstrings, UI, README/docs y commits en **español** (Conventional Commits con scope).

## Aprendizajes y errores a evitar
- **Stack**: solo Python/OpenCV/MediaPipe están implementados. FastAPI, PostgreSQL, HTTP/WebSocket y la UI web del avatar figuran como contemplados en `AGENTS.md`/README, pero **no** existen en el repo (solo hay `vision/`, `data/`, `docs/` y `.github/`). No asumir que están instalados o integrados.
- **Bug resuelto**: `observation_start_time` se fija en la primera actualización **válida**, no en la rama que lanza `ValueError`. No reintroducir esa asignación en el bloque de error (dejaba la frecuencia siempre en `0.0`).
- **Ausencia de landmarks ≠ ojos cerrados**: `LIVE_STREAM` puede dejar de entregar resultados; usar un timeout de frescura y pausar evita parpadeos y muestras de calibración falsos.
- **Overlay**: usar ASCII en `cv2.putText`; las fuentes Hershey no garantizan acentos.
- **Codificación**: guardar siempre UTF-8 sin BOM. El mojibake (acentos españoles convertidos en secuencias de dos caracteres) aparece al decodificar UTF-8 como CP1252; verificarlo con una comprobación de bytes y no asumir que el editor conserva el BOM.
- **Documentación**: `docs/SETUP.md` es la guía canónica y `docs/PROJECT_STATUS.md` se actualiza por hito. No asumir que las etapas futuras están implementadas; el código es la fuente de verdad.
- **CI**: ejecución #1 verificada con éxito el 2026-10-23; no afirmar nuevas ejecuciones sin consultar GitHub Actions.
- **Validación M1**: smoke test técnico OK (cámara, modelo, 7/20 frames con rostro, EAR 0.283–0.396); falta validación funcional guiada. No guardar imágenes.
- Revisar `git status` y `git diff` antes y después de cada tarea; **no sobrescribir** ni descartar cambios del usuario.
- Ejecutar pytest desde `vision/` falla con `ModuleNotFoundError: No module named 'vision'`.
- No guardar secretos, credenciales ni datos personales en `MEMORY.md`, `AGENTS.md`, Git ni documentación.

## Próximos pasos
- **Validación funcional**: sesión guiada con cámara; registrar en `PROJECT_STATUS.md` y crear un documento aparte solo cuando haya evidencia.
- **Siguiente etapa funcional**: PERCLOS simplificado y después máquina de estados.
