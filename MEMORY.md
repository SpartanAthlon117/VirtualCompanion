# MEMORY.md — Diario de Estudio
Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no
aporte.

## Estado actual
- Milestone **M1 — visión por computadora**: `vision/` con webcam → MediaPipe FaceLandmarker (LIVE_STREAM) → EAR → calibración → `OPEN`/`CLOSED` → parpadeos, cierres prolongados y PERCLOS → overlay. Suite **96/96**.
- **Semana 0 del MVP cerrada en alcance y smoke test**: `docs/MVP_SCOPE.md` define alcance, contratos, esquema SQLite y backlog; `docs/validation/M1.md` registra el smoke test Linux del 2026-11-02 (164 frames, 100 % con rostro, EAR de referencia 0.417989, 1 parpadeo incidental, 0 cierres prolongados, ~13.67 FPS). La validación funcional controlada sigue pendiente. Sin imágenes ni video.
- **Semana 1 en curso**: `vision/src/perclos.py` implementa `PerclosCalculator` y ya está integrado en `face_tracker.py` y el overlay; 18 pruebas del cálculo y 4 del formato. Ventana 60 s, mínimo 20 s y pausa ante pérdida de rostro.
- **MVP acordado**: página web local + avatar 2D + FastAPI + SQLite, máquina de estados y alertas. La web, el backend, la persistencia, el avatar, la máquina de estados y las alertas aún **no están implementados**.
- **Git**: rama `master`, sincronizada con `origin/master`; commits locales y push con aprobación explícita.
- Entorno: `.venv` Python 3.13.16 en Linux Fedora 44; Windows/Python 3.13 es referencia y CI. Modelo en `vision/models/face_landmarker.task` (ignorado por Git).
- **CI**: Windows/Python 3.13 con `pip check`, `compileall` y `pytest`; ejecución #1 verificada el 2026-10-23. Linux aún no está en la matriz.
- **Validación**: PERCLOS verificado manualmente en Linux el 2026-11-03 (20 s efectivos, 12.5–15.9 %, pausas, 13 parpadeos) y el 2026-11-04 (overlay, pausa y persistencia de calibración/parpadeos). Pendiente el protocolo controlado y Windows.

## Decisiones (y por qué)
- **Gobernanza**: `AGENTS.md` contiene reglas permanentes; `MEMORY.md` es el diario ≤50 líneas. Leer ambos antes de trabajar.
- **Alcance MVP**: SQLite local (sin PostgreSQL), avatar 2D SVG/Canvas (sin Unity/3D), sin auth en el MVP (login de administrador único en fase posterior), web solo en `127.0.0.1`, validación sin participantes y ~20 h/semana.
- **Plataforma**: Windows como referencia y CI; Linux para desarrollo y compatibilidad. Código portable y audio en el navegador.
- **Pruebas desde la raíz**: `pytest`; ejecutarlo desde `vision/` falla con `ModuleNotFoundError`.
- **Dependencias exactas** en `vision/requirements*.txt`; `opencv-contrib-python` evita el conflicto con el `cv2` de MediaPipe.
- **Pérdida de rostro**: solo se considera presente si el último resultado es reciente (0.5 s); calibración y detectores pausan y descartan el cierre en curso.
- **Clasificación ocular**: umbral `0.70 × EAR` de referencia; `ear < threshold` = `CLOSED`; experimental, no validado para fatiga.
- **Parpadeo**: solo cierres completados `OPEN → CLOSED → OPEN`; el cierre prolongado emite una vez y también cuenta como parpadeo.
- **Idioma**: comentarios, docstrings, UI, documentación y commits en español; Conventional Commits con scope.

## Aprendizajes y errores a evitar
- Solo Python/OpenCV/MediaPipe están implementados; FastAPI, SQLite, web, avatar, PostgreSQL y Unity no existen aún. No asumir lo planificado como hecho.
- **Bug resuelto**: `observation_start_time` se fija en la primera actualización válida; no reintroducir la asignación en la rama de error.
- **Ausencia de landmarks ≠ ojos cerrados**: usar timeout de frescura y pausar.
- **Overlay**: usar ASCII en `cv2.putText`; las fuentes Hershey no garantizan acentos.
- **Codificación**: UTF-8 sin BOM; el mojibake aparece al decodificar UTF-8 como CP1252.
- **Documentación**: `docs/SETUP.md` es la guía canónica; `docs/PROJECT_STATUS.md` el estado; `docs/MVP_SCOPE.md` el alcance; `docs/validation/M1.md` la evidencia.
- Revisar `git status` y `git diff` antes y después de cada tarea; no sobrescribir cambios del usuario.
- No guardar secretos, credenciales ni datos personales en `MEMORY.md`, `AGENTS.md`, Git ni documentación.

## Próximos pasos
- **Semana 1**: separar el motor de visión de la UI, externalizar umbrales y ventanas y revisar el timeout de frescura; después máquina de estados y alertas.
- **Prueba manual**: overlay y pausa confirmados; calibración y parpadeos persisten tras perder el rostro. PERCLOS numérico no reapareció en la segunda sesión por falta de 20 s efectivos; falta verificarlo en vivo y repetir en Windows.
- Después: máquina de estados, alertas, FastAPI/SQLite, web y avatar 2D.
- Validación controlada cuando el usuario pueda interactuar con la cámara; repetir en Windows.
