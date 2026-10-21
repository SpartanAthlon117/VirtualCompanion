# AGENTS.md — VirtualCompanion

## 1. Identidad y propósito del proyecto

**VirtualCompanion** es un prototipo modular de software orientado al monitoreo de indicadores visuales asociados con la fatiga y la somnolencia del conductor de vehículos de carga pesada, particularmente tractocamiones.

El sistema busca integrar visión artificial, procesamiento de imágenes, análisis de características faciales, estimación de estados, generación de alertas, persistencia de eventos e interacción mediante un avatar digital con una interfaz de tipo pseudo-holográfico.

El proyecto tiene fines académicos y experimentales. No debe presentarse como un sistema certificado, un dispositivo médico, una solución comercial validada ni un mecanismo que garantice la prevención de accidentes.

### Objetivos técnicos

- Capturar y procesar imágenes o secuencias de video del conductor.
- Detectar y seguir características faciales mediante visión artificial.
- Analizar indicadores como parpadeos, cierre ocular, EAR, PERCLOS, bostezos y orientación de la cabeza, según las funcionalidades implementadas.
- Combinar indicadores observables para estimar un estado relacionado con la fatiga, utilizando criterios configurables y documentados.
- Generar alertas y registrar eventos relevantes.
- Presentar información mediante una interfaz gráfica y un avatar digital.
- Mantener una arquitectura modular, verificable, mantenible y extensible.
- Documentar los cambios, las decisiones técnicas y los resultados de las pruebas.

La implementación real del repositorio es la fuente de verdad sobre las funcionalidades existentes. No asumir que todos los objetivos están implementados.

---

## 2. Memoria del proyecto y orden de lectura

### Regla obligatoria de inicio

Antes de realizar cualquier tarea:

1. Leer `MEMORY.md` en su totalidad.
2. Leer este `AGENTS.md` y las instrucciones adicionales aplicables a los directorios involucrados.
3. Revisar `README.md` para conocer la descripción, instalación y ejecución del proyecto.
4. Inspeccionar la estructura real del repositorio y los archivos relacionados con la tarea.
5. Consultar el historial de Git cuando sea necesario para entender decisiones o cambios anteriores.
6. Identificar las funcionalidades existentes, las limitaciones conocidas y los requisitos de la tarea.

No solicitar al usuario información que ya esté disponible en estos archivos.

Si `MEMORY.md` no existe, informar de ello cuando sea relevante y crearlo con un resumen inicial basado exclusivamente en información verificable.

### Regla obligatoria de cierre

Al terminar cada tarea, actualizar `MEMORY.md` cuando corresponda, incluyendo:

- Estado actual del trabajo.
- Cambios funcionales o técnicos importantes.
- Decisiones nuevas y sus motivos.
- Pruebas ejecutadas y resultados relevantes.
- Errores encontrados y cómo evitarlos.
- Pendientes necesarios para continuar.

Mantener `MEMORY.md` en un máximo aproximado de 50 líneas. Eliminar información obsoleta, resumir el contexto histórico y conservar únicamente aquello que facilite las próximas tareas.

Si una decisión se convierte en una regla permanente, proponer su incorporación a `AGENTS.md` y no mantenerla únicamente en la memoria.

Nunca almacenar claves, contraseñas, tokens, credenciales, datos personales identificables ni otros datos sensibles en `MEMORY.md`, `AGENTS.md`, registros de Git o documentación.

---

## 3. Stack tecnológico

El proyecto utiliza o contempla las siguientes tecnologías. Antes de modificar dependencias o integrar nuevas herramientas, comprobar su presencia y uso efectivo en el repositorio.

| Tecnología | Responsabilidad |
|---|---|
| Python | Lenguaje principal para el procesamiento visual y la lógica de backend. |
| OpenCV | Captura, manipulación y procesamiento de imágenes y video. |
| MediaPipe | Detección de referencias faciales y extracción de información geométrica del rostro. |
| FastAPI | Desarrollo de servicios y API del backend. |
| HTTP y WebSocket | Comunicación entre componentes, según el flujo de datos existente. |
| PostgreSQL | Persistencia de información y eventos cuando esté integrada en la configuración actual. |
| Tecnologías web del proyecto | Construcción de la interfaz gráfica y presentación del avatar. |
| Git | Control de versiones y trazabilidad de los cambios. |

### Reglas del stack

- Inspeccionar `pyproject.toml`, `requirements.txt`, archivos de bloqueo, configuraciones y manifiestos antes de instalar o actualizar dependencias.
- Respetar las versiones y restricciones existentes.
- No sustituir bibliotecas, frameworks o componentes principales sin una justificación técnica y, cuando afecte al diseño acordado, sin consultar al usuario.
- No asumir que una tecnología contemplada ya está instalada o completamente integrada.
- Mantener la lógica de procesamiento visual independiente de los detalles de presentación siempre que la arquitectura lo permita.
- Utilizar las API oficiales de las bibliotecas y verificar la compatibilidad de sus versiones.
- No introducir dependencias redundantes cuando las herramientas existentes resuelvan adecuadamente el problema.

---

## 4. Arquitectura y patrones de diseño

Priorizar una arquitectura modular con responsabilidades claramente delimitadas.

### Separación de responsabilidades

Cuando corresponda a la estructura existente, distinguir entre:

1. **Captura y adquisición:** acceso a cámara y obtención de fotogramas.
2. **Visión artificial:** detección facial, seguimiento de puntos de referencia y extracción de características.
3. **Análisis de indicadores:** cálculo de métricas oculares, detección de comportamientos y estimación del estado.
4. **Lógica de negocio:** aplicación de reglas, umbrales, estados y generación de eventos.
5. **Servicios y comunicación:** endpoints, validación de solicitudes y transmisión de información.
6. **Persistencia:** almacenamiento, consulta y mantenimiento de los registros.
7. **Interfaz y avatar:** representación visual, presentación de alertas e interacción con el usuario.
8. **Pruebas y configuración:** validación del comportamiento y administración de parámetros.

Esta clasificación es una guía arquitectónica, no una orden para crear directorios o módulos nuevos sin necesidad.

### Patrones recomendados

Aplicar los siguientes patrones únicamente cuando aporten una ventaja real:

- **Separación de responsabilidades:** cada módulo debe tener una finalidad definida.
- **Inyección de dependencias:** facilitar el reemplazo de componentes externos y las pruebas.
- **Adaptadores:** aislar cámaras, motores de visión artificial, bases de datos y servicios externos cuando sea conveniente.
- **Máquina de estados:** gestionar transiciones entre estados de monitoreo, alertas y recuperación cuando la lógica lo requiera.
- **Configuración externa:** mantener umbrales y parámetros ajustables fuera de la lógica central.
- **Persistencia desacoplada:** evitar que la lógica de detección dependa directamente de consultas SQL.
- **Interfaces y contratos explícitos:** definir estructuras de datos y responsabilidades en las fronteras entre módulos.

Evitar abstracciones innecesarias, jerarquías complejas, patrones introducidos únicamente por moda y refactorizaciones que no aporten un beneficio identificable.

### Comunicación entre componentes

- Respetar los contratos existentes de HTTP y WebSocket.
- Validar las estructuras de datos intercambiadas entre servicios.
- Mantener consistencia en los nombres de campos, tipos y estados.
- Gestionar desconexiones, errores de comunicación y pérdida de datos de forma explícita.
- Evitar dependencias circulares.
- No introducir operaciones bloqueantes prolongadas en rutas asíncronas sin evaluar sus consecuencias.
- No ejecutar migraciones destructivas ni alterar contratos existentes sin analizar el impacto.

---

## 5. Convenciones de código

### Python

- Seguir PEP 8 y utilizar nombres descriptivos.
- Utilizar `snake_case` para funciones y variables, `PascalCase` para clases y `UPPER_SNAKE_CASE` para constantes.
- Incorporar anotaciones de tipos cuando mejoren la comprensión y la verificación.
- Utilizar docstrings en módulos, clases y funciones públicas cuando aporten información útil.
- Mantener funciones pequeñas, con una responsabilidad claramente definida.
- Evitar duplicación de lógica y valores mágicos.
- Preferir `pathlib` para la manipulación de rutas.
- Utilizar el módulo `logging` para registrar acontecimientos relevantes.
- Capturar excepciones específicas y proporcionar mensajes de error útiles.
- Evitar bloques `except` genéricos que oculten errores.
- Utilizar gestores de contexto para recursos que deban liberarse.
- Evitar variables globales mutables y efectos secundarios inesperados.
- Mantener las operaciones de entrada/salida separadas de los cálculos puros siempre que sea viable.

### Visión artificial y métricas

- Documentar las fórmulas, unidades, intervalos y condiciones de validez de las métricas.
- Distinguir los valores observados de las inferencias realizadas por el sistema.
- Definir explícitamente el tratamiento de fotogramas inválidos, puntos faciales ausentes y detecciones fallidas.
- Evitar divisiones por cero, valores no finitos y cálculos sobre datos incompletos.
- No codificar umbrales arbitrarios sin documentar su procedencia y justificación.
- Separar los umbrales experimentales de los parámetros respaldados por evidencia científica.
- Mantener consistencia temporal al calcular métricas basadas en ventanas de observación.
- No interpretar una sola señal visual como prueba concluyente de fatiga.

### API y datos

- Mantener contratos de API explícitos y compatibles con los consumidores existentes.
- Validar entradas mediante los mecanismos adecuados de FastAPI y Pydantic, cuando estén disponibles.
- Utilizar respuestas de error coherentes y evitar exponer detalles internos innecesarios.
- Gestionar correctamente las conexiones y transacciones de base de datos.
- Evitar consultas SQL construidas mediante concatenación insegura de entradas.
- Aplicar migraciones versionadas cuando el proyecto disponga de un sistema de migraciones.
- No guardar información que no sea necesaria para los objetivos del prototipo.

### Interfaz

- Respetar el framework, los componentes y el sistema de estilos existentes.
- Mantener una presentación coherente entre estados normales, advertencias y errores.
- Diferenciar visualmente las estimaciones del sistema de los estados confirmados.
- Evitar animaciones, efectos o actualizaciones excesivas que perjudiquen el rendimiento.
- Mantener accesibles los mensajes importantes y no depender exclusivamente del color para transmitir alertas.

---

## 6. Reglas específicas de seguridad y responsabilidad

VirtualCompanion procesa información visual potencialmente sensible. Toda modificación debe considerar la privacidad, la seguridad y los límites de las inferencias realizadas.

- No almacenar video, imágenes faciales ni información identificable de forma persistente salvo que exista una necesidad justificada y autorizada.
- No enviar datos visuales a servicios externos sin una justificación técnica y autorización explícita.
- No incluir información personal en registros, mensajes de error o datos de prueba.
- No registrar credenciales ni secretos.
- Utilizar variables de entorno para los secretos que realmente sean necesarios.
- Mantener los archivos de entorno locales fuera del control de versiones; proporcionar únicamente plantillas sin secretos.
- No afirmar que el sistema detecta fatiga con certeza absoluta.
- No presentar los resultados experimentales como evidencia de reducción de accidentes.
- No modificar mecanismos de seguridad o privacidad para facilitar pruebas sin documentar el riesgo.
- Mantener los umbrales y las reglas de alerta configurables cuando corresponda.
- No desactivar las advertencias del sistema para ocultar errores de detección.

Las alertas generadas son indicadores de apoyo y no sustituyen el descanso, la supervisión operativa ni las medidas de seguridad aplicables al transporte.

---

## 7. Prohibiciones

Los agentes de programación deben cumplir las siguientes restricciones:

1. No reescribir archivos completos cuando un cambio localizado sea suficiente.
2. No eliminar funcionalidades existentes sin autorización o justificación explícita.
3. No modificar archivos ajenos a la tarea sin una razón técnica.
4. No cambiar dependencias principales, contratos de API o esquemas de datos de forma incompatible sin evaluar el impacto.
5. No inventar resultados de pruebas, métricas de precisión, validaciones ni referencias científicas.
6. No afirmar que una funcionalidad está terminada sin comprobar su implementación.
7. No introducir código de ejemplo, simulaciones o datos ficticios en el flujo de producción sin identificarlos claramente.
8. No utilizar datos reales sensibles en pruebas automatizadas.
9. No incluir secretos en el repositorio ni en la documentación.
10. No ejecutar comandos destructivos, restablecimientos de Git, borrados masivos o migraciones irreversibles sin autorización explícita.
11. No sobrescribir cambios del usuario ni descartar modificaciones preexistentes.
12. No crear una nueva arquitectura, framework o estructura de carpetas sin justificar su necesidad.
13. No ocultar errores mediante excepciones genéricas, silenciamiento de logs o resultados predeterminados engañosos.
14. No afirmar que se ejecutaron pruebas, análisis estáticos o procesos de CI/CD que no se hayan realizado.
15. No modificar `AGENTS.md` para introducir reglas permanentes nuevas sin explicar su propósito y mantenerlas coherentes con las existentes.

Si una tarea requiere incumplir alguna de estas restricciones, explicar el motivo y solicitar autorización cuando corresponda.

---

## 8. Estructura del proyecto

La estructura existente del repositorio es la referencia principal.

Antes de crear, mover o renombrar archivos:

1. Inspeccionar el árbol de directorios.
2. Identificar las convenciones de organización existentes.
3. Localizar los módulos relacionados con la funcionalidad.
4. Seguir la estructura vigente en lugar de imponer una nueva.
5. Actualizar las referencias afectadas después de cualquier reorganización autorizada.

Como orientación, las responsabilidades pueden organizarse en módulos equivalentes a los siguientes, siempre que sean compatibles con el diseño real:

- Captura de video y gestión de cámara.
- Procesamiento visual y seguimiento facial.
- Cálculo de indicadores y estimación del estado.
- Servicios HTTP y WebSocket.
- Modelos, esquemas y persistencia.
- Interfaz gráfica y avatar.
- Configuración y utilidades.
- Pruebas unitarias y de integración.
- Documentación técnica y académica.

No crear todos estos módulos de manera automática. Implementar únicamente los necesarios para resolver la tarea y mantener la arquitectura existente.

---

## 9. Flujo de trabajo obligatorio

Para cada tarea, seguir el proceso descrito a continuación.

### Fase 1. Comprensión

- Leer `MEMORY.md`, `AGENTS.md` y `README.md`.
- Revisar los archivos relacionados con la tarea.
- Comprender el comportamiento actual antes de modificarlo.
- Identificar restricciones, dependencias y posibles efectos secundarios.
- Formular una solución mínima que satisfaga los requisitos.

### Fase 2. Planificación

- Dividir las tareas complejas en cambios pequeños y verificables.
- Identificar los archivos que probablemente necesitarán cambios.
- Determinar qué pruebas permiten comprobar el resultado.
- Consultar al usuario si existen decisiones importantes ambiguas o cambios de arquitectura que requieran autorización.

### Fase 3. Implementación

- Realizar cambios incrementales.
- Mantener compatibilidad con los componentes existentes.
- Evitar refactorizaciones no relacionadas.
- Actualizar pruebas y documentación cuando corresponda.
- No sustituir cambios del usuario por versiones propias sin comprobar las diferencias.

### Fase 4. Verificación

- Ejecutar las pruebas pertinentes disponibles.
- Revisar los cambios mediante `git diff`.
- Comprobar errores de formato, tipos, importaciones y dependencias cuando existan herramientas para ello.
- Verificar que los cambios no introduzcan secretos, datos sensibles o archivos generados innecesarios.
- Documentar las pruebas que no pudieron ejecutarse y el motivo.

### Fase 5. Documentación y cierre

- Actualizar `README.md` cuando cambien la instalación, la configuración, la arquitectura, las funcionalidades, el uso o los procedimientos de desarrollo.
- Actualizar `CHANGELOG.md` cuando exista y corresponda registrar una modificación relevante.
- Actualizar `MEMORY.md` según las reglas establecidas.
- Revisar el estado de Git y resumir los archivos modificados.
- Comunicar los resultados, las pruebas realizadas, las limitaciones y los siguientes pasos.

No considerar una tarea terminada únicamente porque el código se haya escrito.

---

## 10. Testing y criterios de calidad

Las pruebas deben verificar el comportamiento esperado, no simplemente confirmar que el código se ejecuta.

### Pruebas unitarias

Priorizar pruebas de:

- Cálculos matemáticos de métricas visuales.
- Validación y normalización de entradas.
- Manejo de datos incompletos o inválidos.
- Transiciones entre estados.
- Evaluación de umbrales y reglas de alerta.
- Transformaciones de datos.
- Funciones de lógica de negocio independientes de la cámara y la base de datos.

### Pruebas de integración

Cuando los componentes estén disponibles, comprobar:

- Integración entre captura, procesamiento y estimación.
- Comunicación entre backend e interfaz.
- Funcionamiento de endpoints HTTP.
- Comunicación mediante WebSocket.
- Persistencia y recuperación de eventos.
- Gestión de errores y recuperación ante desconexiones.
- Compatibilidad entre los esquemas de datos de los componentes.

### Pruebas del sistema

Evaluar, según el alcance y los recursos disponibles:

- Funcionamiento con cámara conectada y desconectada.
- Comportamiento ante cambios de iluminación y posición facial.
- Tratamiento de fotogramas perdidos o detecciones fallidas.
- Rendimiento y latencia.
- Uso de memoria y recursos de procesamiento.
- Consistencia de las alertas y del historial de eventos.

### Validación de los indicadores

Si se evalúa la capacidad de detección, utilizar datos de prueba apropiados y criterios definidos previamente. Cuando existan etiquetas de referencia fiables, considerar métricas como precisión, exhaustividad (*recall*), F1 y tasas de falsos positivos y falsos negativos.

No atribuir validez científica a una métrica únicamente porque su cálculo sea correcto. La evaluación de su utilidad para estimar fatiga requiere evidencia independiente y una metodología apropiada.

### Reglas de ejecución

- Utilizar las herramientas de pruebas y los comandos definidos por el proyecto.
- No asumir nombres de comandos sin revisar la configuración.
- Preferir pruebas deterministas que no requieran hardware real.
- Separar las pruebas que dependen de cámara, GPU o servicios externos.
- No modificar el entorno del usuario innecesariamente para hacer pasar una prueba.
- No ocultar pruebas fallidas.
- Informar qué pruebas pasaron, cuáles fallaron y cuáles no se ejecutaron.

---

## 11. CI/CD y automatización

La integración y entrega continuas deben respetar las herramientas y configuraciones existentes.

Antes de introducir un flujo nuevo, revisar los archivos de configuración del repositorio, incluidos los workflows existentes y los manifiestos de dependencias.

Cuando el proyecto disponga de CI/CD, procurar que el proceso incluya:

1. Instalación reproducible de dependencias.
2. Verificación de formato y calidad estática.
3. Ejecución de pruebas automatizadas.
4. Comprobaciones de importación, configuración y compatibilidad.
5. Detección de errores que impidan integrar los cambios.

Si no existe un proceso de CI/CD configurado, no afirmar que está activo. Proponer su incorporación como una mejora independiente, justificando sus herramientas y requisitos.

No publicar versiones, desplegar servicios, modificar infraestructura ni ejecutar migraciones de producción sin autorización explícita.

---

## 12. Convenciones de Git, commits y pull requests

### Control de versiones

- Revisar `git status` antes de comenzar y antes de finalizar.
- Preservar los cambios preexistentes del usuario.
- No modificar el historial de Git de forma destructiva.
- No incluir archivos temporales, cachés, entornos virtuales, datos de prueba sensibles o secretos.
- Mantener los archivos de configuración de ejemplo libres de credenciales.
- Registrar cambios relacionados en unidades lógicas y fáciles de revisar.

### Mensajes de commit

Utilizar, cuando sea compatible con las convenciones existentes, el formato Conventional Commits:

`tipo(ámbito): descripción breve`

Tipos recomendados:

- `feat`: nueva funcionalidad.
- `fix`: corrección de errores.
- `refactor`: reorganización interna sin cambio funcional intencional.
- `test`: incorporación o modificación de pruebas.
- `docs`: documentación.
- `perf`: mejora de rendimiento.
- `build`: dependencias o proceso de construcción.
- `ci`: integración continua.
- `chore`: mantenimiento general.

Ejemplos:

- `feat(vision): add eye aspect ratio calculation`
- `fix(api): handle missing facial landmarks`
- `test(fatigue): cover alert threshold transitions`
- `docs(readme): update development instructions`

Escribir los mensajes de forma breve, descriptiva y coherente con el idioma predominante del historial existente.

No crear commits automáticamente salvo que el usuario lo solicite o el flujo de trabajo autorizado lo contemple.

### Pull requests

Cuando el proyecto utilice pull requests, incluir:

- Objetivo y contexto del cambio.
- Funcionalidades o archivos afectados.
- Decisiones técnicas relevantes.
- Pruebas ejecutadas y sus resultados.
- Limitaciones conocidas.
- Cambios de configuración, dependencias o base de datos.
- Actualizaciones de documentación.

Mantener cada cambio enfocado en una finalidad principal. No incluir modificaciones ajenas a la tarea.

No afirmar que una rama se fusionó, que un pull request se creó o que una publicación se realizó si no se ejecutó y verificó la operación.

---

## 13. Documentación y trazabilidad académica

VirtualCompanion debe mantener coherencia entre el software, la documentación técnica y la documentación académica.

### README.md

Mantener actualizado el `README.md` cuando cambien aspectos relevantes, incluyendo:

- Descripción y objetivos.
- Estado real del desarrollo.
- Arquitectura y componentes.
- Requisitos del sistema.
- Instalación y configuración.
- Instrucciones de ejecución.
- Pruebas y verificación.
- Limitaciones conocidas.
- Referencias técnicas pertinentes.

No convertir el README en un sustituto de la documentación detallada. Mantenerlo como punto de entrada para comprender y utilizar el proyecto.

### CHANGELOG.md

Cuando exista, registrar las modificaciones relevantes siguiendo la estructura y las convenciones ya adoptadas. Si el proyecto utiliza versiones, conservar su coherencia con los cambios documentados y los identificadores de Git cuando estén disponibles.

No inventar números de versión, etiquetas, hashes o referencias a commits.

### Documentación académica

- Fundamentar las afirmaciones científicas con fuentes confiables y verificables.
- Priorizar artículos revisados por pares, publicaciones académicas, normas oficiales y documentación primaria.
- Utilizar citas y referencias completas conforme al estilo bibliográfico solicitado.
- Distinguir los fundamentos teóricos de las decisiones particulares de implementación.
- Diferenciar las funcionalidades propuestas, implementadas y validadas.
- Documentar supuestos, limitaciones, metodología y resultados.
- No inventar fuentes, citas, experimentos ni resultados.
- Registrar la procedencia y justificación de las decisiones técnicas relevantes.

---

## 14. Reglas para el trabajo autónomo de la IA

El agente debe actuar de manera cuidadosa, verificable y orientada a resolver la tarea solicitada.

- Inspeccionar antes de modificar.
- Reutilizar antes de duplicar.
- Preferir cambios mínimos y reversibles.
- Justificar las decisiones que afecten a la arquitectura.
- Preguntar únicamente cuando falte información necesaria o exista una decisión importante que no pueda resolverse con seguridad.
- No solicitar confirmación para cada modificación rutinaria que esté claramente dentro del alcance autorizado.
- No interpretar una tarea como permiso para reestructurar todo el proyecto.
- Verificar los resultados mediante pruebas o inspecciones apropiadas.
- Informar honestamente de las limitaciones del entorno.
- No ocultar errores ni declarar éxito sin evidencia.
- Dejar el repositorio en un estado coherente con el alcance autorizado.
- Al terminar, resumir qué se hizo, por qué, qué se verificó y qué queda pendiente.

### Prioridad de las instrucciones

En caso de conflicto, respetar las instrucciones de mayor prioridad del sistema y del usuario. Entre las instrucciones propias del proyecto, aplicar las reglas específicas del directorio correspondiente y mantener coherencia con la arquitectura y las decisiones verificadas del repositorio.

Si una decisión histórica registrada en `MEMORY.md` contradice el código actual o una instrucción permanente, investigar la discrepancia antes de modificar el comportamiento.

---

## 15. Criterio final de calidad

Una tarea de VirtualCompanion se considera satisfactoria cuando:

- Resuelve el requisito solicitado.
- Respeta la arquitectura y las convenciones del proyecto.
- No introduce regresiones conocidas.
- Cuenta con pruebas o verificaciones apropiadas para el cambio.
- Mantiene actualizada la documentación afectada.
- Conserva la trazabilidad de las decisiones importantes.
- Respeta la privacidad y las limitaciones del prototipo.
- Deja constancia del estado actualizado en `MEMORY.md`.

**Principio rector:** realizar cambios técnicamente sólidos, académicamente justificables, verificables y proporcionales a la tarea, preservando siempre la integridad del proyecto y el control del usuario sobre su evolución.