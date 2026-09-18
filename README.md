# Virtual Companion

Sistema holográfico de acompañante virtual para la prevención de fatiga y monitoreo del conductor en tractocamiones.

## Estado

En desarrollo.

## Objetivo

Desarrollar un prototipo modular capaz de detectar indicadores de fatiga mediante visión por computadora y proporcionar asistencia mediante un acompañante virtual.

## Tecnologías principales

- Python
- OpenCV
- MediaPipe
- Unity
- C#
- Git

### Clasificación del estado ocular

El sistema utiliza el EAR promedio y el EAR de referencia obtenido
durante la calibración para clasificar el estado actual de los ojos
como OPEN o CLOSED.

La clasificación utiliza un umbral relativo basado en el EAR de
referencia. Este parámetro es experimental y todavía no representa
un umbral validado para detección de fatiga.

## Estructura

- vision/ — visión por computadora y detección de fatiga.
- unity/ — aplicación visual y avatar virtual.
- config/ — configuración del sistema.
- data/ — datos y resultados experimentales.
- docs/ — documentación técnica y experimental.
- scripts/ — herramientas auxiliares.
- 	ests/ — pruebas generales.

## Estado actual

Milestone M0 — Preparación del entorno.
