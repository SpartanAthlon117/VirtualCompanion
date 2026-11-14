# MEMORY.md — Diario de Estudio
Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no
aporte.

## Estado actual
- **M1 de visión + evaluación experimental**: webcam → MediaPipe FaceLandmarker → EAR → calibración → `OPEN`/`CLOSED` → parpadeos, cierres prolongados y PERCLOS → `FatigueStateMachine` → `AlertManager` → panel/consola/log. `MetricsPipeline` puro, `VisionEngine` síncrono y CLI separados.
- Reglas: `WARNING` con PERCLOS `>= 0.20` sostenido 10 s o cierre `>= 1.5 s`; `FATIGUE` con PERCLOS `>= 0.30` sostenido 10 s o cierre `>= 3.0 s`; `NORMAL` con PERCLOS `< 0.12` sostenido 20 s y sin cierre `>= 1.5 s`. Umbrales experimentales.
- Alertas: solo al entrar en `WARNING`/`FATIGUE`; cooldowns 30 s/60 s; pausa sin alertas. Salida en consola, log y panel; audio/web pendientes.
- La frecuencia y la ausencia de parpadeo no escalan el estado; se conservan como información.
- **Prueba manual con cámara**: aparecieron `WARNING` (cierre 1.519 s) y `FATIGUE` (cierre 3.0 s) con alertas. No se observó `NORMAL`: PERCLOS mínimo 13.8 % (41.98 s), luego 20.7–31.8 %, y los cierres largos reiniciaron la espera.
- **Recuperación**: la ventana de PERCLOS es de 60 s; tras el último cierre largo pueden pasar ~80 s (ventana + 20 s de sostenimiento) antes de volver a `NORMAL`. El panel muestra PERCLOS actual y objetivo.
- Suite **195 pruebas**. `compileall` correcto.
- **MVP pendiente**: FastAPI, SQLite, web, avatar 2D, audio y validación controlada. El alcance sigue en `docs/MVP_SCOPE.md`.
- **Git**: `master` sincronizada con `origin/master` hasta `be376b5`; los cambios de evaluación, alertas, panel y documentación están sin commit. Push solo con autorización.

## Decisiones (y por qué)
- **Gobernanza**: `AGENTS.md` reglas permanentes; `MEMORY.md` diario ≤50 líneas. Leer ambos antes de trabajar.
- **Alcance MVP**: SQLite local (sin PostgreSQL), avatar 2D SVG/Canvas (sin Unity/3D), sin auth en el MVP, web solo en `127.0.0.1`, validación sin participantes.
- **Plataforma**: Windows referencia y CI; Linux para compatibilidad. Pruebas desde la raíz.
- **Dependencias exactas** en `vision/requirements*.txt`; `opencv-contrib-python` evita el conflicto con `cv2` de MediaPipe.
- **Pérdida de rostro**: solo presente si el último resultado es reciente (0.5 s); calibración, detectores, PERCLOS y evaluación pausan; no se interpreta como ojos cerrados.
- **Clasificación ocular**: umbral `0.70 × EAR` de referencia; experimental.
- **Parpadeo**: solo `OPEN → CLOSED → OPEN` con duración menor al umbral de cierre prolongado; los cierres largos no suman parpadeos.
- **Estado**: solo PERCLOS sostenido y cierre actual; sin frecuencia ni ausencia de parpadeo. Recuperación estricta; no ajustar umbrales por una sola persona.
- **Alertas**: deduplicadas por cambio de estado; cooldowns independientes; una pausa no actualiza el estado recordado.
- **Privacidad**: no guardar imágenes, video ni datos personales; logs solo con métricas y mensajes.

## Aprendizajes y errores a evitar
- Solo Python/OpenCV/MediaPipe están implementados; FastAPI, SQLite, web y avatar no existen aún.
- **Ausencia de landmarks ≠ ojos cerrados**: usar timeout de frescura y pausar.
- **Overlay**: ASCII en `cv2.putText`; las fuentes Hershey no garantizan acentos.
- **PERCLOS**: mínimo 20 s de observación efectiva; la ventana de 60 s hace que la recuperación sea lenta. No prometer recuperación en 20 s.
- **Codificación**: UTF-8 sin BOM; evitar mojibake.
- **Documentación**: `docs/SETUP.md` guía canónica; `PROJECT_STATUS.md` estado; `MVP_SCOPE.md` alcance; `validation/M1.md` evidencia.
- Revisar `git status` y `git diff` antes y después de cada tarea; no sobrescribir cambios del usuario.

## Próximos pasos
- Verificar con cámara la recuperación sostenida a `NORMAL`, el panel y la salida de alertas.
- Después: FastAPI/SQLite, página web, avatar 2D y alertas sonoras.
- Validación controlada cuando el usuario pueda interactuar con la cámara; repetir en Windows y Linux.
