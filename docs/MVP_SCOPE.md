# Alcance del MVP — VirtualCompanion

## Estado del documento

- Fecha: 2026-11-13
- Estado: alcance acordado para el MVP. La máquina de estados y el gestor de alertas ya están implementados en el CLI; la web, el backend, la persistencia y el avatar siguen pendientes.
- Este documento describe lo que se va a construir. No afirma que todas las
  funcionalidades del MVP ya estén implementadas.

## Objetivo del MVP

Construir un prototipo local, funcional y demostrable que:

1. Capture video de una webcam y detecte un rostro.
2. Calcule indicadores oculares y PERCLOS.
3. Estime un estado experimental de fatiga con reglas explicables.
4. Genere alertas visuales y sonoras.
5. Presente la información en una página web local con un avatar 2D.
6. Registre sesiones y eventos en SQLite, sin almacenar video ni imágenes.

El sistema es académico y experimental. No es un dispositivo médico, no
diagnostica fatiga y no garantiza la prevención de accidentes. Los umbrales
son configurables y no están validados científicamente.

## Decisiones cerradas

| Decisión | Elección |
|---|---|
| Avatar | 2D simple, pseudo-holográfico, SVG/Canvas |
| Persistencia | SQLite local |
| Plataforma | Windows y Linux; se valida en ambas |
| Indicadores | Oculares: EAR, parpadeos, cierres prolongados y PERCLOS |
| Validación | Autopruebas guionizadas, sin participantes |
| Autenticación | Fase posterior; un único administrador |
| Página web | Obligatoria para usar el sistema |
| Exposición de red | Solo `127.0.0.1` en el MVP |
| Frontend | HTML/CSS/JS y SVG/Canvas, sin build ni npm |

## Alcance incluido

- Captura de webcam y detección de un solo rostro.
- Cálculo de EAR, calibración y clasificación `OPEN`/`CLOSED`.
- Detección de parpadeos y cierres prolongados.
- Cálculo de PERCLOS con ventana móvil.
- Estado experimental `NORMAL`, `WARNING` o `FATIGUE` con histéresis.
- Razones explicables de cada evaluación.
- Alertas visuales, textuales y sonoras.
- Página web local para iniciar/detener el monitoreo, calibrar y consultar.
- Vista en vivo de la cámara, sin grabación.
- Avatar 2D que reacciona al estado.
- Historial de sesiones y eventos en SQLite.
- Exportación CSV de eventos.
- Configuración externa de umbrales y ventanas.
- Pruebas automatizadas y validación técnica documentada.
- Funcionamiento en Windows y Linux.

## Fuera del alcance del MVP

- Registro público de usuarios y multiusuario.
- Login de administrador, roles y recuperación de contraseña.
- PostgreSQL y despliegue en red o internet.
- Avatar 3D, Unity y voz.
- Bostezos y orientación de cabeza.
- Múltiples rostros.
- Validación con participantes o validez clínica.
- Entrenamiento de modelos de aprendizaje automático.
- Aplicación móvil.

Estos elementos quedan como fases posteriores y no deben presentarse como
parte del MVP.

## Arquitectura mínima

```text
[Webcam]
   |
   v
[VisionEngine] --> [Metricas / PERCLOS] --> [FatigueStateMachine] --> [AlertManager]
   |                     |                        |
   v                     v                        v
[SQLite] <------ [MonitoringService] ------> [FastAPI REST + WebSocket + MJPEG]
                                                     |
                                                     v
                                       [Dashboard web + avatar 2D]
```

Responsabilidades:

| Componente | Responsabilidad |
|---|---|
| `VisionEngine` / `MonitoringSession` | Captura, landmarks, EAR y coordinación del flujo; `VisionEngine` implementado, `MonitoringSession` pendiente |
| `PerclosCalculator` | Proporción de tiempo con ojos cerrados en una ventana; implementado |
| `FatigueStateMachine` | Transiciones de estado con histéresis y razones; implementado |
| `AlertManager` | Niveles, deduplicación y cooldown de alertas; implementado |
| `MonitoringService` | Une visión, métricas, estado, alertas y persistencia; pendiente |
| `FastAPI` | REST, WebSocket y transmisión MJPEG; pendiente |
| `SQLite` | Sesiones, evaluaciones y eventos; pendiente |
| `web/` | Dashboard, historial y avatar 2D; pendiente |

Directrices:

- No reescribir `face_tracker.py`: se extrae la lógica reutilizable y el CLI
  queda como adaptador de desarrollo.
- La visión se ejecuta en un hilo o worker para no bloquear el event loop.
- El motor de visión no depende de FastAPI ni del avatar.
- La UI debe poder probarse con datos simulados, sin cámara.
- Los umbrales viven en configuración, no en el código.

## Contratos de datos

Los contratos son documentación de diseño. Su implementación en código se
distribuye entre el motor de visión y la futura capa de persistencia.

### `MetricsSnapshot`

- `captured_at`: fecha y hora UTC en ISO 8601.
- `elapsed_seconds`: tiempo de observación efectiva.
- `face_present`: booleano.
- `left_ear`, `right_ear`, `average_ear`: número o `None`.
- `eye_state`: `OPEN`, `CLOSED` o `UNKNOWN`.
- `blink_count`: entero.
- `last_closed_duration`: segundos o `None`.
- `mean_closed_duration`: segundos o `None`.
- `blink_rate_per_minute`: número o `None`.
- `time_since_last_blink`: segundos o `None`.
- `current_closed_duration`: segundos o `None`.
- `prolonged_closure_count`: entero.
- `perclos`: número entre 0 y 1, o `None` si no hay datos suficientes.
- `perclos_window_seconds`: número.
- `paused`: booleano.

### `Assessment`

- `state`: `NORMAL`, `WARNING` o `FATIGUE`.
- `reasons`: tupla de cadenas explicables.
- `changed`: indica si el estado cambió en esa evaluación.
- `paused`: indica si la evaluación está en pausa por pérdida de rostro.
- `alert_level`: `NONE`, `INFO`, `WARNING` o `CRITICAL`.

### `PipelineUpdate`

- `snapshot`: `MetricsSnapshot`.
- `calibration`: estado de la calibración.
- `events`: eventos de visión de la actualización.
- `assessment`: `Assessment` de la actualización.
- `alerts`: alertas emitidas en la actualización.

### `AlertEvent`

- `type`: `FATIGUE_WARNING` o `FATIGUE_CRITICAL`.
- `level`: `WARNING` o `CRITICAL`.
- `message`: texto para el usuario.
- `occurred_at`: fecha y hora UTC.

Los campos de persistencia (`id`, `session_id`, métricas asociadas) se añadirán
cuando se integre SQLite.

### `SessionSummary`

- `id`, `started_at`, `ended_at`, `status`.
- `duration_seconds`.
- `blink_count`, `prolonged_closure_count`.
- `max_state`.
- `event_count`.

## Esquema SQLite propuesto

```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    status TEXT NOT NULL CHECK (status IN ('RUNNING', 'COMPLETED', 'ABORTED')),
    notes TEXT
);

CREATE TABLE assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    captured_at TEXT NOT NULL,
    state TEXT NOT NULL,
    alert_level TEXT NOT NULL,
    ear REAL,
    perclos REAL,
    blink_rate REAL,
    reasons_json TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    occurred_at TEXT NOT NULL,
    type TEXT NOT NULL,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    metrics_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_assessments_session_time
    ON assessments(session_id, captured_at);

CREATE INDEX idx_events_session_time
    ON events(session_id, occurred_at);
```

No se crea tabla de usuarios en el MVP. La fase de autenticación añadirá
`users` y `sessions.user_id` mediante una migración pequeña.

## Configuración inicial

Los umbrales de estado y alertas ya están definidos en `config/default.toml` como valores experimentales y configurables. Su justificación definitiva requiere validación adicional. El cargador de configuración está implementado.

| Sección | Claves previstas |
|---|---|
| `camera` | `index`, `width`, `height` |
| `calibration` | `duration_seconds`, `stabilization_seconds`, `minimum_ear` |
| `eye_state` | `threshold_factor` |
| `blink` | `analysis_window_seconds` |
| `prolonged_closure` | `threshold_seconds` |
| `perclos` | `window_seconds`, `minimum_observation_seconds` |
| `state_machine` | `warning_perclos`, `fatigue_perclos`, `warning_sustain_seconds`, `fatigue_sustain_seconds`, `warning_closure_seconds`, `fatigue_closure_seconds`, `warning_exit_perclos`, `recovery_sustain_seconds` |
| `alerts` | `warning_cooldown_seconds`, `critical_cooldown_seconds`, `sound_enabled` |
| `storage` | `database_path` |
| `web` | `host`, `port`, `preview_enabled` |

Las claves `warning_to_fatigue_seconds`, `fatigue_exit_perclos`, `no_blink_*` y
`low_blink_rate_*` están reservadas y no intervienen en las transiciones
actuales. La frecuencia y la ausencia de parpadeo se conservan como
información.

## Backlog priorizado

### P0 — imprescindible para el MVP

1. Separar el motor de visión de la UI. **Completado.**
2. Validar el PERCLOS integrado en el flujo y el overlay mediante la prueba manual controlada. **Parcialmente completado: verificado en vivo; falta la recuperación sostenida y la repetición controlada.**
3. Añadir configuración externa y logging. **Completado.**
4. Implementar la máquina de estados. **Completado.**
5. Implementar el gestor de alertas. **Completado.**
6. Crear FastAPI con REST, WebSocket y MJPEG.
7. Crear el repositorio SQLite.
8. Crear el dashboard web.
9. Crear el avatar 2D.
10. Integrar el flujo de extremo a extremo.
11. Completar pruebas unitarias y de integración.
12. Ejecutar la autovalidación técnica y documentarla.
13. Actualizar README, SETUP, PROJECT_STATUS, CHANGELOG y MEMORY. **Completado.**

### P1 — deseable si el tiempo alcanza

- Exportación CSV.
- Filtros básicos del historial.
- Resumen de sesión.
- Botón para activar o desactivar la vista en vivo.
- Edición básica de configuración desde la web.
- Recuperación ante desconexión de cámara o WebSocket.

### P2 — fase posterior

- Login de administrador único.
- PostgreSQL.
- Avatar 3D, Unity y voz.
- Bostezos y orientación de cabeza.
- Validación con participantes.
- Multiusuario y roles.

## Criterios de aceptación del MVP

1. El sistema inicia y abre la web local.
2. Cámara, modelo y calibración funcionan en Windows y Linux.
3. Se muestran métricas, PERCLOS, estado y alertas en vivo.
4. El avatar 2D reacciona a los estados.
5. Los eventos se guardan en SQLite y se pueden exportar a CSV.
6. No se almacena video ni imágenes.
7. La suite de pruebas pasa en ambas plataformas.
8. La documentación está actualizada.
9. Existe un guion de demo y un informe de autovalidación con resultados reales.
10. Las limitaciones se declaran sin afirmar detección clínica de fatiga.

## Seguridad y privacidad

- La web escucha solo en `127.0.0.1`.
- No se expone a la red en el MVP.
- Se restringe CORS al mismo origen y se valida `Origin`/`Host`.
- Las acciones que cambian estado usan POST con JSON.
- No se almacenan imágenes ni video.
- No se recogen datos personales.
- La base SQLite, los logs y los exports están excluidos de Git.
- No se guardan secretos en el repositorio.
- Exponer el sistema en red requerirá HTTPS y autenticación.

La fase posterior de autenticación usará un único administrador creado por
script, con Argon2id, cookie de sesión `HttpOnly`, protección CSRF, límite de
intentos y HTTPS si se expone. No habrá auto-registro público.

## Validación prevista

- Autopruebas guionizadas, sin participantes.
- Calibración con ojos abiertos.
- Registro de 10 parpadeos.
- Tres cierres superiores a 2 s.
- Pérdida y recuperación de rostro.
- Recuperación sostenida a `NORMAL` tras reducir el PERCLOS y cesar los cierres `>= 1.5 s`.
- Repetición con gafas, dos distancias y dos condiciones de luz cuando sea posible.
- Registro de aciertos, falsos positivos, falsos negativos, FPS y latencia.
- Sin imágenes ni video; solo métricas, eventos y logs.

Los resultados se documentarán en `docs/validation/` únicamente cuando existan
datos reales. No se atribuirá validez clínica a los resultados.

## Riesgos principales

| Riesgo | Mitigación |
|---|---|
| Alcance no priorizado | Prioridad P0 y revisión de alcance |
| Diferencias de cámara entre Windows y Linux | Pruebas en ambas plataformas |
| Bloqueo de FastAPI por MediaPipe | Visión en hilo y estado compartido |
| Concurrencia en SQLite | WAL y un único escritor |
| Web expuesta por error | Bind a `127.0.0.1` y checklist |
| Scope creep | Auth y extras quedan en P2 |
| Falsos positivos o negativos | Umbrales configurables y limitaciones documentadas |

## Documentos relacionados

- `README.md`: descripción y estado del proyecto.
- `docs/SETUP.md`: guía de entorno y ejecución.
- `docs/PROJECT_STATUS.md`: estado detallado y pendientes.
- `docs/validation/`: resultados de validación cuando existan.
- `AGENTS.md`: reglas permanentes.
- `MEMORY.md`: memoria entre sesiones.
- `CHANGELOG.md`: registro de cambios.
