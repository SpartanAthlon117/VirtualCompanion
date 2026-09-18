# Manual de preparación del entorno — VirtualCompanion

Este documento explica cómo preparar un entorno de desarrollo desde cero después de clonar el repositorio de **VirtualCompanion** en un equipo nuevo.

Está pensado especialmente para sistemas basados en Linux, como **Pop!_OS**, pero los conceptos generales también aplican a otros sistemas operativos.

## 1. Requisitos previos

Antes de comenzar, asegúrate de tener instalado:

- Git
- Python 3.13
- Una cámara web compatible con el sistema operativo
- Acceso a Internet durante la instalación de dependencias y del modelo de MediaPipe
- Un editor de código, por ejemplo Visual Studio Code

Comprobar Git:

```bash
git --version
```

Comprobar Python:

```bash
python3.13 --version
```

El proyecto utiliza **Python 3.13.x**. Para reproducibilidad, se recomienda utilizar la versión indicada por el equipo durante el desarrollo.

## 2. Clonar el repositorio

```bash
git clone https://github.com/SpartanAthlon117/VirtualCompanion.git
cd VirtualCompanion
```

Comprobar la ubicación y el estado:

```bash
pwd
git status
```

## 3. Crear el entorno virtual de Python

Desde la raíz del proyecto:

```bash
python3.13 -m venv .venv
```

Activarlo en Linux:

```bash
source .venv/bin/activate
```

Comprobar la versión:

```bash
python --version
```

Debe mostrar Python 3.13.x.

> **Importante:** `.venv` es específico del sistema operativo. Si se cambia de Windows a Linux o se utiliza otro equipo, debe crearse un entorno virtual nuevo.

## 4. Actualizar pip

Con `.venv` activo:

```bash
python -m pip install --upgrade pip
```

## 5. Instalar dependencias

Las dependencias de visión están definidas en `vision/requirements.txt`.

```bash
pip install -r vision/requirements.txt
```

Actualmente incluye:

```text
opencv-python
mediapipe
numpy
```

## 6. Comprobar dependencias

```bash
python -c "import cv2, mediapipe, numpy; print('OpenCV:', cv2.__version__); print('MediaPipe:', mediapipe.__version__); print('NumPy:', numpy.__version__)"
```

Si no aparece ningún error, las bibliotecas principales pueden importarse correctamente.

## 7. Preparar el modelo de MediaPipe

VirtualCompanion utiliza:

```text
vision/models/face_landmarker.task
```

El modelo está excluido del control de versiones mediante `.gitignore`, por lo que puede no estar presente después de clonar el repositorio.

Comprobar:

```bash
ls -lh vision/models/
```

Si `face_landmarker.task` no está presente, debe descargarse nuevamente desde la fuente oficial de MediaPipe utilizada por el proyecto.

> No se debe eliminar la regla de `.gitignore` únicamente para subir el modelo al repositorio.

## 8. Comprobar la cámara web

En Linux:

```bash
ls /dev/video*
```

Normalmente aparecerá un dispositivo como `/dev/video0`.

Si `v4l2-ctl` está disponible:

```bash
v4l2-ctl --list-devices
```

## 9. Probar la captura de cámara

Con `.venv` activo y desde la raíz del proyecto:

```bash
python vision/src/camera.py
```

Debe abrirse una ventana con la imagen de la cámara. Para salir, pulsa `q`.

## 10. Probar el seguimiento facial

```bash
python vision/src/face_tracker.py
```

Esta prueba verifica la cadena actual:

```text
Cámara
   ↓
Captura de frames
   ↓
MediaPipe Face Landmarker
   ↓
Detección facial
   ↓
Landmarks faciales
   ↓
EAR
   ↓
Calibración EAR
```

Comprueba que:

- La cámara funciona de forma fluida.
- El rostro es detectado.
- Los landmarks aparecen correctamente.
- El EAR se actualiza.
- La calibración se inicia y muestra su progreso.
- Se obtiene un EAR de referencia al finalizar.

Para salir puede utilizarse `q` o cerrar la ventana.

## 11. Comprobar Git

Preparar un entorno nuevo no debería generar cambios de código accidentales.

```bash
git status
git remote -v
git branch
```

La creación de `.venv` no debería aparecer como una gran cantidad de archivos pendientes si `.venv` está correctamente incluido en `.gitignore`.

## 12. Flujo recomendado para nuevos desarrolladores

```text
Clonar repositorio
       ↓
Crear .venv
       ↓
Activar .venv
       ↓
Instalar requirements.txt
       ↓
Preparar modelo de MediaPipe
       ↓
Comprobar cámara
       ↓
Ejecutar pruebas existentes
       ↓
Comenzar desarrollo
```

Para cada modificación:

```text
Modificar
   ↓
Probar
   ↓
Actualizar documentación
   ↓
Revisar git status / git diff
   ↓
git add
   ↓
Revisar staging
   ↓
git commit
   ↓
Verificar git status
   ↓
git push
```

No se recomienda hacer `commit` o `push` antes de comprobar que los cambios corresponden únicamente a la funcionalidad desarrollada.

## 13. Estructura relevante

```text
VirtualCompanion/
├── .git/
├── .venv/
├── vision/
│   ├── src/
│   │   ├── camera.py
│   │   ├── face_tracker.py
│   │   ├── face_metrics.py
│   │   └── ear_calibrator.py
│   ├── models/
│   │   └── face_landmarker.task
│   ├── tests/
│   └── requirements.txt
├── unity/
├── config/
├── data/
├── docs/
├── scripts/
├── tests/
├── .gitignore
├── CHANGELOG.md
└── README.md
```

Los archivos `.venv/` y determinados modelos pueden estar excluidos del repositorio.

## 14. Solución de problemas básicos

### Python no se encuentra

```bash
python3.13 --version
```

Si falla, Python 3.13 no está disponible mediante ese comando y debe instalarse o configurarse.

### No se puede crear `.venv`

Comprueba que `python3.13` sea una instalación funcional y que el soporte para entornos virtuales esté disponible.

### No se pueden instalar dependencias

Comprueba que el entorno virtual esté activo:

```bash
which python
```

La ruta debería apuntar a `VirtualCompanion/.venv/bin/python`.

Después:

```bash
python -m pip install -r vision/requirements.txt
```

### La cámara no aparece

```bash
ls /dev/video*
```

Si no aparece ningún dispositivo, el problema probablemente está relacionado con el reconocimiento de la cámara por parte del sistema operativo.

### El seguimiento facial no inicia

Comprueba que exista `vision/models/face_landmarker.task` y que las dependencias estén instaladas correctamente.

## 15. Notas de compatibilidad

El proyecto se encuentra en desarrollo y sus dependencias pueden cambiar entre etapas.

Por esta razón:

- No se deben asumir versiones futuras de las bibliotecas.
- `vision/requirements.txt` es la referencia para las dependencias Python.
- La documentación debe actualizarse cuando cambie el entorno de ejecución.
- Los cambios importantes de arquitectura o instalación deben registrarse también en el README principal y/o `CHANGELOG.md`.

## 16. Estado del manual

Este documento representa el procedimiento base para preparar un entorno de desarrollo desde cero.

A medida que VirtualCompanion incorpore nuevos componentes —por ejemplo, clasificación del estado ocular, detección de parpadeos, detección de fatiga, voz, Unity o integración con el simulador— se deberán añadir los requisitos necesarios para ejecutar esas nuevas etapas.

**Objetivo:** que una persona pueda clonar el repositorio, preparar su entorno y ejecutar la versión disponible del proyecto sin depender de configuraciones específicas de la computadora original.
