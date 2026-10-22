# Guía de entorno y ejecución

Esta es la guía canónica para preparar y ejecutar VirtualCompanion. El entorno validado es **Windows con Python 3.13 (probado con 3.13.15)**. Los comandos de Linux se incluyen como referencia, pero no se han verificado en este repositorio.

## 1. Requisitos

- Windows (entorno validado) o Linux (referencia)
- Python 3.13.x
- Git
- Webcam para la ejecución en tiempo real
- Conexión a Internet para instalar dependencias y descargar el modelo

Editor de código opcional: Visual Studio Code.

## 2. Clonar el repositorio

```bash
git clone https://github.com/SpartanAthlon117/VirtualCompanion.git
cd VirtualCompanion
```

## 3. Crear el entorno virtual

En Windows:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

En Linux:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

`.venv` es específico del sistema operativo y está excluido de Git.

## 4. Instalar dependencias

Las versiones exactas están fijadas en `vision/requirements.txt` y `vision/requirements-dev.txt`.

En Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r vision/requirements.txt -r vision/requirements-dev.txt
```

En Linux, con el entorno activo:

```bash
python -m pip install -r vision/requirements.txt -r vision/requirements-dev.txt
```

Comprobar las bibliotecas principales:

```powershell
.\.venv\Scripts\python.exe -c "import cv2, mediapipe, numpy; print('OpenCV:', cv2.__version__); print('MediaPipe:', mediapipe.__version__); print('NumPy:', numpy.__version__)"
```

Se utiliza `opencv-contrib-python` para evitar conflictos con el `cv2` que requiere MediaPipe.

## 5. Descargar el modelo de MediaPipe

El modelo se guarda en `vision/models/face_landmarker.task` y está excluido de Git.

En Windows (PowerShell):

```powershell
New-Item -ItemType Directory -Force -Path vision/models | Out-Null
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task" -OutFile "vision/models/face_landmarker.task"
```

En Linux:

```bash
mkdir -p vision/models
wget -O vision/models/face_landmarker.task \
https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task
```

## 6. Ejecutar el prototipo

En Windows:

```powershell
.\.venv\Scripts\python.exe vision/src/camera.py
.\.venv\Scripts\python.exe vision/src/face_tracker.py
```

En Linux, con el entorno activo:

```bash
python vision/src/camera.py
python vision/src/face_tracker.py
```

`face_tracker.py` inicia la cámara, la calibración del EAR, la clasificación ocular, la detección de parpadeos y el overlay de métricas. Para salir, pulsa `q`, `ESC` o cierra la ventana. `camera.py` solo utiliza `q`.

## 7. Ejecutar las pruebas

Desde la raíz del repositorio:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Las pruebas no requieren cámara. Ejecutar `pytest` desde `vision/` produce `ModuleNotFoundError: No module named 'vision'`; el directorio de trabajo debe ser la raíz.

## 8. Integración continua

El flujo `.github/workflows/ci.yml` está configurado para Windows con Python 3.13. Instala las dependencias fijadas, verifica su consistencia con `pip check`, compila `vision/` con `compileall` y ejecuta `pytest`.

La primera ejecución remota ocurrirá en el siguiente push a `master` o en un pull request. La integración continua no sustituye la validación con cámara.

## 9. Problemas comunes

### No se encuentra el módulo `vision`

Ejecuta las pruebas desde la raíz del repositorio, no desde `vision/`.

### No se encuentra el modelo

Comprueba que exista `vision/models/face_landmarker.task`. Si falta, descárgalo con los comandos de la sección 5.

### La cámara no se abre

Comprueba que no esté siendo utilizada por otra aplicación y que el sistema tenga permisos de acceso a la webcam. El prototipo abre el dispositivo `0` por defecto.

### Falla la instalación de dependencias

Confirma que estás usando Python 3.13 y el intérprete de `.venv`. No instales las dependencias globalmente.

## 10. Documentos relacionados

- `README.md`: descripción, estado, instalación resumida y estructura.
- `docs/PROJECT_STATUS.md`: estado detallado, limitaciones y pendientes.
- `AGENTS.md`: reglas permanentes del proyecto.
- `MEMORY.md`: memoria entre sesiones.
- `CHANGELOG.md`: registro de cambios.
