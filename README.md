# Virtual Companion

Prototipo académico de acompañante virtual para el monitoreo de indicadores visuales asociados con la fatiga y la somnolencia en conductores de tractocamiones.

## Estado

En desarrollo.

## Objetivo

Desarrollar un prototipo modular que integre visión por computadora para monitorear indicadores visuales asociados con la fatiga y proporcione asistencia mediante un acompañante virtual.

## Tecnologías principales

Implementadas actualmente:

* Python
* OpenCV
* MediaPipe
* Git

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
* Pausa y reanudación de la calibración, los parpadeos y los cierres prolongados ante la pérdida del rostro.
* Visualización en el overlay de parpadeos totales, último cierre, cierre promedio, frecuencia, tiempo desde el último parpadeo, cierre actual, cierres prolongados y umbral.

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

### Pérdida de rostro

Si MediaPipe deja de detectar el rostro o no entrega resultados nuevos durante 0.5 segundos, la calibración, la detección de parpadeos y la detección de cierres prolongados se pausan. La ausencia de landmarks no se interpreta como ojos cerrados. Al recuperar el rostro, los componentes se reanudan y se descarta cualquier cierre ocular que haya quedado interrumpido.

El tiempo máximo sin resultados nuevos se define en `vision/src/face_presence.py` mediante `FACE_LOSS_TIMEOUT_SECONDS`.

### Métricas en el overlay

Después de completar la calibración, el overlay muestra el número total de parpadeos, la duración del último cierre, la duración promedio de los cierres, la frecuencia estimada, el tiempo transcurrido desde el último parpadeo, la duración del cierre actual, el número de cierres prolongados y el umbral configurado. Los valores `--` indican que todavía no existe información suficiente.

Cuando un cierre supera el umbral, la línea del cierre actual muestra `[PROLONGADO]` y cambia de color; el texto se conserva para no depender únicamente del color. Cuando el rostro no está presente, las métricas se congelan y el overlay indica `Metricas en pausa (sin rostro)`. El texto gráfico utiliza caracteres ASCII para evitar problemas de representación con las fuentes de OpenCV.

## Instalación y ejecución

El entorno validado es Windows con Python 3.13 (probado con 3.13.15) y Git. La guía detallada, incluida una referencia para Linux, está en [`docs/SETUP.md`](docs/SETUP.md).

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

La suite incluye 74 pruebas de métricas geométricas, calibración, presencia de rostro, detección de parpadeos, cierres prolongados, formato del overlay y clasificación ocular.

La integración continua no cubre la cámara. La validación funcional de M1 es manual, no guarda imágenes y se registra en `docs/PROJECT_STATUS.md`; si se acumulan resultados, se valorará un documento específico de validación.

## Calidad y CI

El flujo `.github/workflows/ci.yml` está configurado para ejecutarse en Windows con Python 3.13. Instala las dependencias fijadas, verifica su consistencia con `pip check`, compila `vision/` y ejecuta `pytest`.

La verificación actual es funcional y sintáctica. No se ha adoptado todavía un linter o formatter porque el código existente no cuenta con una configuración acordada y su incorporación requiere una limpieza separada.

## Documentación

* [`docs/SETUP.md`](docs/SETUP.md) — guía canónica de entorno y ejecución.
* [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) — estado actual, limitaciones y pendientes.
* [`docs/VirtualCompanion_SETUP.md`](docs/VirtualCompanion_SETUP.md) — referencia histórica; redirige a la guía canónica.
* [`AGENTS.md`](AGENTS.md) — reglas permanentes del proyecto.
* [`MEMORY.md`](MEMORY.md) — memoria entre sesiones.
* [`CHANGELOG.md`](CHANGELOG.md) — registro de cambios.

## Estructura

* `vision/` — módulo de visión por computadora.
  * `vision/src/` — captura, métricas, calibración, clasificación, parpadeos, cierres prolongados y overlay.
  * `vision/tests/` — pruebas automatizadas.
* `data/` — estructura para datos experimentales; actualmente solo contiene archivos `.gitkeep`.
* `docs/` — documentación técnica, estado y guía de entorno.
* `.github/workflows/` — integración continua.
* `AGENTS.md`, `PROJECT_CONTEXT.md`, `MEMORY.md` y `CHANGELOG.md` — reglas, contexto, memoria y registro de cambios.

## Próximas etapas

Las siguientes etapas contemplan:

1. Validación funcional de M1 con cámara: calibración, parpadeos, cierres prolongados y pérdida de rostro.
2. Cálculo de la proporción de tiempo con ojos cerrados (PERCLOS simplificado).
3. Integración de indicadores y máquina de estados de fatiga.
4. Generación de alertas.
5. Integración con el acompañante virtual y la interfaz 3D mediante Unity.
