# Introducción a Docker
=======================

Docker es una plataforma de contenedores que permite la creación y ejecución de aplicaciones en entornos aislados. En este documento, exploraremos los conceptos básicos de Docker y cómo utilizarlo para desarrollar y desplegar aplicaciones.

## ¿Qué son los contenedores?
---------------------------

Un contenedor es una unidad de ejecución que encapsula la aplicación, sus dependencias y configuración en un solo paquete. Los contenedores comparten el mismo kernel del host y se aíslan entre sí para evitar conflictos.

### Ventajas de los contenedores

*   Aislamiento: Los contenedores se aíslan entre sí para evitar conflictos.
*   Portabilidad: Los contenedores son portables y pueden ejecutarse en cualquier plataforma que admita Docker.
*   Reutilización: Los contenedores pueden reutilizarse en diferentes entornos.

## Instalación de Docker
-------------------------

Para empezar a utilizar Docker, debes instalarlo en tu máquina. Puedes descargar la versión más reciente desde el sitio web oficial de Docker.

### Instalación en Linux

Puedes instalar Docker en Linux utilizando el siguiente comando:

```bash
sudo apt-get update && sudo apt-get install docker.io
```

### Instalación en Windows y macOS

Puedes descargar e instalar la aplicación de Docker Desktop desde el sitio web oficial.

## Crear un contenedor con Docker
---------------------------------

Una vez instalado Docker, puedes crear un contenedor utilizando el comando `docker run`. Por ejemplo:

```bash
docker run -it ubuntu /bin/bash
```

Este comando crea un contenedor basado en la imagen de Ubuntu y lo ejecuta en modo interactivo.

## Crear una imagen con Docker
------------------------------

Una imagen es una plantilla que se utiliza para crear contenedores. Puedes crear una imagen utilizando el comando `docker build`. Por ejemplo:

```bash
docker build -t mi-imagen .
```

Este comando crea una imagen llamada `mi-imagen` a partir del archivo `Dockerfile` en la carpeta actual.

## Información pendiente
------------------------

*   Configuración de Docker para utilizar un registro de imágenes.
*   Creación de contenedores con variables de entorno.
*   Uso de volumenes para persistir datos en los contenedores