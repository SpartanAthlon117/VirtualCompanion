# Virtual Companion

Prototipo académico de acompañante virtual para el monitoreo de indicadores visuales asociados con la fatiga y la somnolencia en conductores de tractocamiones.

## Estado

En desarrollo. M1 de visión implementado; el MVP con página web y avatar 2D está en planificación.

## Objetivo

Desarrollar un prototipo modular que integre visión por computadora para monitorear indicadores visuales asociados con la fatiga y proporcione asistencia mediante un acompañante virtual.

## Tecnologías principales

Implementadas actualmente:

* Python
* OpenCV
* MediaPipe
* Git

Planificadas para el MVP, aún no implementadas:

* FastAPI
* SQLite
* HTML, CSS y JavaScript

Contempladas para etapas posteriores:

* Unity
* C#

## Estado actual

**Milestone M1 — Visión por computadora básica.**

Actualmente se encuentran implementadas las siguientes capacidades:

* Captura de video mediante webcam.
* Detección facial mediante MediaPipe Face Landmarker.
* Obtención de landmarks faciales.
* Cálculo del Eye Aspect Ratio (EAR).
* Calibración automática del EAR de referencia.
* Clasificación experimental del estado ocular.
* Clasificación y visualización del estado de los ojos como `OPEN` o `CLOSED`.
* Detección de eventos de parpadeo mediante la transición `OPEN → CLOSED → OPEN`.
* Medición de la duración de cada cierre ocular.
* Cálculo de la duración promedio de los cierres oculares.
* Detección de cierres oculares prolongados con umbral configurable y un evento por cierre.
* Cálculo de la frecuencia de parpadeo dentro de una ventana temporal de análisis.
* Registro del tiempo transcurrido desde el último parpadeo detectado.
* Módulo de cálculo de PERCLOS simplificado (`vision/src/perclos.py`), integrado en el flujo en vivo y en el overlay.
* Pausa y reanudación de la calibración, los parpadeos, los cierres prolongados y PERCLOS ante la pérdida del rostro.
* Visualización en el overlay de parpadeos totales, último cierre, cierre promedio, frecuencia, tiempo desde el último parpadeo, PERCLOS, cierre actual, cierres prolongados y umbral.

La clasificación del estado ocular utiliza el EAR promedio y un EAR de referencia obtenido durante la calibración.

El detector de parpadeos utiliza la secuencia temporal del estado ocular para identificar eventos de parpadeo y registra la duración del cierre ocular en segundos.

La duración del cierre se obtiene desde el momento en que los ojos pasan de `OPEN` a `CLOSED` hasta que regresan a `OPEN`. Esa duración alimenta tanto el conteo de parpadeos como la detección de cierres prolongados.

La duración del cierre ocular todavía no representa por sí sola una detección de fatiga. Será utilizada como uno de los indicadores dentro de las etapas posteriores del sistema.

El umbral utilizado actualmente es relativo al EAR de referencia. Este parámetro es experimental y todavía no representa un umbral validado científicamente para la detección de fatiga.

El detector utiliza una ventana temporal de análisis configurable, cuyo valor predeterminado es de 60 segundos, para calcular la frecuencia de parpadeo en parpadeos por minuto. Durante la fase inicial de observación, antes de completar la ventana configurada, el cálculo utiliza el tiempo transcurrido desde la primera actualización del detector. Una vez alcanzada la duración de la ventana, el cálculo utiliza los eventos registrados dentro de la ventana temporal móvil, excluyendo aquellos que quedan fuera de ella.

Este enfoque híbrido permite estimar la frecuencia sin esperar a que transcurra un minuto completo desde el inicio de la observación. Sin embargo, las estimaciones iniciales pueden variar considerablemente debido al reducido tiempo de observación y no deben interpretarse de manera aislada como evidencia de fatiga.

La lógica del detector cuenta los parpadeos completados mediante la transición `OPEN → CLOSED → OPEN`. Por ello, un cierre ocular que continúa sin una reapertura todavía no se registra como un parpadeo completado.

También se conserva de manera independiente el instante del último parpadeo para poder calcular el tiempo transcurrido desde ese evento, incluso cuando el parpadeo ya se encuentra fuera de la ventana de análisis.

Estas métricas constituyen indicadores temporales que posteriormente podrán utilizarse en el análisis de patrones asociados a la fatiga. En esta etapa no se utilizan todavía para determinar por sí solas un estado de fatiga.

### Cierres prolongados

La detección de cierres prolongados utiliza un componente independiente. El umbral predeterminado es de `1.5 s`; es un valor **experimental y configurable**, no un umbral clínico validado.

El evento se emite una sola vez cuando un cierre cruza el umbral. Mientras los ojos permanezcan cerrados no se repite, y al reabrir se registra la duración final. Si se pierde el rostro, el cierre en curso se descarta; si los ojos siguen cerrados al reanudar, comienza un nuevo conteo.

Un cierre prolongado también se contabiliza como parpadeo completado por el detector actual. Esta iteración no modifica esa semántica; el nuevo componente solo añade el indicador de duración prolongada.

La generación de alertas por fatiga requiere lógica adicional y no forma parte de esta etapa.

### PERCLOS simplificado

El módulo `vision/src/perclos.py` calcula un PERCLOS simplificado: la proporción del tiempo de observación válido en el que los ojos estuvieron cerrados. Utiliza una ventana móvil de `60 s` y no devuelve un valor hasta acumular `20 s` de observación efectiva; mientras tanto, el overlay muestra `--`.

El tiempo en el que el rostro no está presente se excluye del cálculo. Al recuperar el rostro, el cálculo continúa desde el estado ocular observado y no interpreta la ausencia como un cierre.

El resultado se presenta como porcentaje en el overlay y también se incluye en la salida de depuración. Es un indicador **experimental**: no distingue por sí mismo fatiga, somnolencia ni otros estados, y no sustituye una validación con evidencia independiente.

### Pérdida de rostro

Si MediaPipe deja de detectar el rostro o no entrega resultados nuevos durante 0.5 segundos, la calibración, la detección de parpadeos, la detección de cierres prolongados y el cálculo de PERCLOS se pausan. La ausencia de landmarks no se interpreta como ojos cerrados. Al recuperar el rostro, los componentes se reanudan y se descarta cualquier cierre ocular que haya quedado interrumpido.

El tiempo máximo sin resultados nuevos se define en `vision/src/face_presence.py` mediante `FACE_LOSS_TIMEOUT_SECONDS`.

### Métricas en el overlay

Después de completar la calibración, el overlay muestra el número total de parpadeos, la duración del último cierre, la duración promedio de los cierres, la frecuencia estimada, el tiempo transcurrido desde el último parpadeo, el PERCLOS de la ventana móvil, la duración del cierre actual, el número de cierres prolongados y el umbral configurado. Los valores `--` indican que todavía no existe información suficiente.

Cuando un cierre supera el umbral, la línea del cierre actual muestra `[PROLONGADO]` y cambia de color; el texto se conserva para no depender únicamente del color. Cuando el rostro no está presente, las métricas se congelan y el overlay indica `Metricas en pausa (sin rostro)`. El texto gráfico utiliza caracteres ASCII para evitar problemas de representación con las fuentes de OpenCV.

## Instalación y ejecución

Windows es el entorno de referencia y de integración continua. Linux se verificó parcialmente el 2026-11-02 con un smoke test técnico (cámara, modelo, landmarks, EAR y calibración); la ejecución completa con ventana y la futura web aún no se han validado en Linux. La guía detallada está en [`docs/SETUP.md`](docs/SETUP.md).

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r vision/requirements.txt -r vision/requirements-dev.txt
```

Descarga el modelo de MediaPipe (no se versiona):

```powershell
New-Item -ItemType Directory -Force -Path vision/models | Out-Null
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task" -OutFile "vision/models/face_landmarker.task"
```

Ejecuta el seguimiento facial:

```powershell
.\.venv\Scripts\python.exe vision/src/face_tracker.py
```

Las versiones exactas de las dependencias están fijadas en `vision/requirements.txt` y `vision/requirements-dev.txt`.

## Pruebas

Desde la raíz del repositorio:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

La suite incluye 96 pruebas de métricas geométricas, calibración, presencia de rostro, detección de parpadeos, cierres prolongados, PERCLOS, formato del overlay y clasificación ocular.

El 2026-11-02 se ejecutó un smoke test técnico en Linux: 164 frames, 100 % con rostro, calibración completada con EAR de referencia `0.417989` y un parpadeo incidental. Los resultados y las limitaciones están en [`docs/validation/M1.md`](docs/validation/M1.md).

El 2026-11-03 se verificó manualmente la integración de PERCLOS en Linux: el valor apareció tras 20 s de observación efectiva, varió con los cierres oculares y respetó las pausas por pérdida de rostro. El 2026-11-04 se confirmó que la línea se ve sin problemas y que la pausa detiene los cálculos. En una segunda sesión, las pausas impidieron acumular 20 s efectivos y PERCLOS permaneció en `--`; la calibración y el contador de parpadeos se conservaron. Falta verificar en vivo la conservación de un valor numérico y repetir la prueba en Windows.

La integración continua no cubre la cámara. La validación funcional controlada de M1 sigue pendiente: 10 parpadeos, 3 cierres superiores a 2 s, pérdida de rostro, gafas, distancias, iluminación y prueba en Windows. No se guardan imágenes ni video.

## Calidad y CI

El flujo `.github/workflows/ci.yml` está configurado para ejecutarse en Windows con Python 3.13. Instala las dependencias fijadas, verifica su consistencia con `pip check`, compila `vision/` y ejecuta `pytest`. Linux todavía no forma parte de la matriz.

La verificación actual es funcional y sintáctica. No se ha adoptado todavía un linter o formatter porque el código existente no cuenta con una configuración acordada y su incorporación requiere una limpieza separada.

## Documentación

* [`docs/MVP_SCOPE.md`](docs/MVP_SCOPE.md) — alcance del MVP, decisiones, contratos y backlog.
* [`docs/SETUP.md`](docs/SETUP.md) — guía canónica de entorno y ejecución.
* [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) — estado actual, limitaciones y pendientes.
* [`docs/validation/M1.md`](docs/validation/M1.md) — smoke test técnico y limitaciones.
* [`docs/VirtualCompanion_SETUP.md`](docs/VirtualCompanion_SETUP.md) — referencia histórica; redirige a la guía canónica.
* [`AGENTS.md`](AGENTS.md) — reglas permanentes del proyecto.
* [`MEMORY.md`](MEMORY.md) — memoria entre sesiones.
* [`CHANGELOG.md`](CHANGELOG.md) — registro de cambios.

## Estructura

* `vision/` — módulo de visión por computadora.
  * `vision/src/` — captura, métricas, calibración, clasificación, parpadeos, cierres prolongados, PERCLOS y overlay.
  * `vision/tests/` — pruebas automatizadas.
* `data/` — estructura para datos experimentales; actualmente solo contiene archivos `.gitkeep`.
* `docs/` — documentación técnica, alcance, estado y guía de entorno.
  * `docs/validation/` — resultados de validación con evidencia real.
* `.github/workflows/` — integración continua.
* `backend/`, `web/` y `config/` — planificados para el MVP; todavía no existen.
* `AGENTS.md`, `PROJECT_CONTEXT.md`, `MEMORY.md` y `CHANGELOG.md` — reglas, contexto, memoria y registro de cambios.

## Próximas etapas

El alcance detallado está en [`docs/MVP_SCOPE.md`](docs/MVP_SCOPE.md). La secuencia prevista es:

1. Cerrar la validación funcional controlada de M1 en Windows y Linux.
2. Separación del motor de visión de la interfaz y configuración externa de umbrales y ventanas.
3. Integración de indicadores y máquina de estados de fatiga.
4. Generación de alertas.
5. Backend local con FastAPI, SQLite y página web.
6. Avatar 2D pseudo-holográfico e integración del MVP.
7. Fase posterior: login de administrador único, avatar 3D/Unity, voz y validación con participantes.
