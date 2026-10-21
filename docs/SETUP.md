# Setup

## Requisitos actuales

- Windows
- Python 3.13.x
- Git
- Visual Studio Code

## Entorno Python

El proyecto utiliza un entorno virtual ubicado en:

.venv

El intérprete objetivo es Python 3.13.x.

## Activación

En PowerShell puede utilizarse directamente el intérprete del entorno:

.\.venv\Scripts\python.exe

La configuración de VS Code debe apuntar a:

.\.venv\Scripts\python.exe

## Dependencias

Las dependencias del módulo de visión se encuentran definidas en:

`vision/requirements.txt`

Las dependencias de prueba están en:

`vision/requirements-dev.txt`

## Pruebas

Desde la raíz del proyecto:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Nota

No instalar dependencias globalmente. Las dependencias del proyecto deben instalarse dentro del entorno virtual.
