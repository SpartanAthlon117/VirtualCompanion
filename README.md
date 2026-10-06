# Virtual Companion

Sistema holográfico de acompañante virtual para la prevención de fatiga y monitoreo del conductor en tractocamiones.

## Estado

En desarrollo.

## Objetivo

Desarrollar un prototipo modular capaz de detectar indicadores de fatiga mediante visión por computadora y proporcionar asistencia mediante un acompañante virtual.

## Tecnologías principales

* Python
* OpenCV
* MediaPipe
* Unity
* C#
* Git

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
* Cálculo de la frecuencia de parpadeo dentro de una ventana temporal de análisis.
* Registro del tiempo transcurrido desde el último parpadeo detectado.

La clasificación del estado ocular utiliza el EAR promedio y un EAR de referencia obtenido durante la calibración.

El detector de parpadeos utiliza la secuencia temporal del estado ocular para identificar eventos de parpadeo y registra la duración del cierre ocular en segundos.

La duración del cierre se obtiene desde el momento en que los ojos pasan de `OPEN` a `CLOSED` hasta que regresan a `OPEN`. Esta medición permitirá posteriormente diferenciar parpadeos normales de cierres oculares prolongados.

La duración del cierre ocular todavía no representa por sí sola una detección de fatiga. Será utilizada como uno de los indicadores dentro de las etapas posteriores del sistema.

El umbral utilizado actualmente es relativo al EAR de referencia. Este parámetro es experimental y todavía no representa un umbral validado científicamente para la detección de fatiga.

El detector mantiene una ventana temporal de análisis de 60 segundos para calcular la frecuencia de parpadeo. Esta frecuencia representa la cantidad de parpadeos detectados dentro de dicha ventana.

También se conserva de manera independiente el instante del último parpadeo para poder calcular el tiempo transcurrido desde ese evento, incluso cuando el parpadeo ya se encuentra fuera de la ventana de análisis.

Estas métricas constituyen indicadores temporales que posteriormente podrán utilizarse en el análisis de patrones asociados a la fatiga. En esta etapa no se utilizan todavía para determinar por sí solas un estado de fatiga.

## Estructura

* `vision/` — visión por computadora y detección de indicadores de fatiga.
* `unity/` — aplicación visual y avatar virtual.
* `config/` — configuración del sistema.
* `data/` — datos y resultados experimentales.
* `docs/` — documentación técnica y experimental.
* `scripts/` — herramientas auxiliares.
* `tests/` — pruebas generales.

## Próximas etapas

Las siguientes etapas contemplan:

1. Integración de las métricas de parpadeo en el seguimiento facial en tiempo real.
2. Estabilización y validación de las métricas de frecuencia y duración de los parpadeos.
3. Detección de indicadores de fatiga.
4. Máquina de estados de fatiga.
5. Integración con el acompañante virtual.
6. Integración de la interfaz 3D mediante Unity.
