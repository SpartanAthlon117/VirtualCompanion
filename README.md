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

La clasificación del estado ocular utiliza el EAR promedio y un EAR de referencia obtenido durante la calibración.

El umbral utilizado actualmente es relativo al EAR de referencia. Este parámetro es experimental y todavía no representa un umbral validado científicamente para la detección de fatiga.

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

1. Estabilización temporal del estado ocular.
2. Detección de parpadeos.
3. Análisis de duración de cierres oculares.
4. Detección de indicadores de fatiga.
5. Máquina de estados de fatiga.
6. Integración con el acompañante virtual.
7. Integración de la interfaz 3D mediante Unity.
