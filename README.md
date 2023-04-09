[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)

# Guía de uso de lbctl `Liburutegia Control` :books:

Este proyecto está diseñado para facilitar la gestión de la **biblioteca Liburutegia**.

> Podra buscar libros :orange_book: por Titulo, Author y ISBN, y añadirlo a la bases de datos.

## Índice de contenidos
* [Requisitos](#requisitos)
* [Uso](#uso)
* [Configuracion](#configuracion)
* [Pasos comunes](#pasos)
  - [Linux](#linux)
  - [Windows](#windows)


<a name="requisitos"></a>
## Requisitos

- Para utilizar Liburutegia e Liburutegia control (**lbctl**), debes tener instalado Docker y Docker Compose en tu sistema operativo. Puedes descargar ambas herramientas de los siguientes enlaces:

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

- Necesitas tener ejecutando la aplicacion web de Liburutegia 

_Podras descargar el proyecto en:_

- [Liburutegia](https://github.com/lopuma/liburutegia)

#### Alemnos tener ejecutando estos servicios:

- [ ] Nginx
- [ ] App Liburutegia
- [x] Mysql
- [x] Minio
- [x] Redis
- [ ] Redis commander

- Ademas de tener ejecutando selenium

_selenium_

<a name="uso"></a>
## Cómo utilizar `LBCTL`

### Menú de opciones para lbctl

Puedes utilizar una de las siguientes opciones:

1. Buscar un libro por título: `lbctl find -t <título>`
2. Buscar un libro por autor: `lbctl find -a <autor>`
3. Buscar un libro por ISBN: `lbctl find -i <ISBN>`
4. Buscar libro por titulo, author y ISBN `lbctl find -t <título> -a <autor> -i <ISBN>`
5. help `lbctl -h / --help`

<a name="configuracion"></a>
## Configuración

Antes de utilizar el proyecto, debes configurar las variables de entorno necesarias. Para ello debes tener configurado un fichero .env, se puede utilizar el mismo fichero .env utilizado en el proyecto web **Liburutegia**, añadiendo las siguientes variables.

```
# WebDriver
- COVER_DIR: es el directorio en el que se encuentran las imágenes de portada para los libros de Liburutegia.
- WEBDRIVER_HOST: es el nombre del host donde se ejecuta el servicio de WebDriver, el cual se utiliza para realizar pruebas automatizadas en la aplicación.

# MySql
- MYSQL_USER: es el nombre de usuario de la base de datos MySQL que utiliza la aplicación.
```
<a name="pasos"></a>
## Pasos comunes

- Descarga el archivo docker-compose.yml del proyecto [Liburutegia control](https://github.com/lopuma/lbctl).

- Modifica los valores de las variables de entorno en el archivo .env de acuerdo a tus necesidades.

- En una terminal o consola, navega hasta la carpeta donde descargaste el archivo docker-compose.yml.

<a name="linux"></a>
### Puedes seguir estas 2 opciones para Linux

1. **Crea un alias en tu archivo .bashrc:**

- #### Editar .bashrc.

> sudo vi ~/.bashrc

- #### Añade lo siguiente.

```
alias lbctl='docker-compose run --rm --name lbctl-liburutegia lbctl-liburutegia "$@"'
```

_Este comando crea un alias lbctl que ejecuta el contenedor de Docker, la primera vez construira el contenedor._

- Recarga tu archivo .bashrc con el comando ``source ~/.bashrc``

- Ahora puedes utilizar el comando lbctl seguido de los parámetros que desees. Por ejemplo:

```
lbctl find -t Pokemon
```

2. **Crea un archivo de script en /usr/local/bin/ utilizando el siguiente comando:**

```
sudo vi /usr/local/bin/lbctl
```
- #### Copia y pega el siguiente código en el archivo y guarda los cambios:

```
#!/bin/bash
docker-compose run --rm --name lbctl-liburutegia lbctl-liburutegia "$@"
```

_La ultima linea_

```
El comando docker-compose run se utiliza para ejecutar un comando en un servicio específico de Docker Compose.

En este caso, el comando se está ejecutando con las siguientes opciones:

--rm: elimina el contenedor después de que se detiene el proceso de ejecución del comando.
--name: le da un nombre al contenedor que se está creando. En este caso, el nombre es lbctl-liburutegia.
lbctl-liburutegia: es el nombre del servicio de Docker Compose que se va a utilizar para ejecutar el comando.
Por lo tanto, el comando completo docker-compose run --rm --name lbctl-liburutegia lbctl-liburutegia está ejecutando un comando en el servicio lbctl-liburutegia y se está creando un contenedor con el mismo nombre. El contenedor se eliminará automáticamente cuando se detenga el proceso de ejecución del comando.

"$@" : espera mas parametros
```

- #### Dale permisos de ejecución al script:

```
sudo chmod +x /usr/local/bin/lbctl
```
- #### Ahora puedes ejecutar el script en cualquier lugar utilizando el siguiente comando:

```
lbctl find -t Pokemon
```
<a name="windows"></a>
### Puedes seguir estas opciones para Windows

1. **Crea un archivo lbctl.bat con el siguiente contenido:**

```
@echo off
@set "COMPOSE_FILE=C:\Users\<usuario>\docker-compose.yml"
@docker-compose run --rm --name lbctl-liburutegia lbctl-liburutegia %*

```
:file_folder: _En COMPOSE_FILE=, debes remplazar por el path, donde se encuentra el docker-compose.yml de (**lbctl**)_

_La ultima linea_

```
El comando docker-compose run se utiliza para ejecutar un comando en un servicio específico de Docker Compose.

En este caso, el comando se está ejecutando con las siguientes opciones:

--rm: elimina el contenedor después de que se detiene el proceso de ejecución del comando.
--name: le da un nombre al contenedor que se está creando. En este caso, el nombre es lbctl-liburutegia.
lbctl-liburutegia: es el nombre del servicio de Docker Compose que se va a utilizar para ejecutar el comando.
Por lo tanto, el comando completo docker-compose run --rm --name lbctl-liburutegia lbctl-liburutegia está ejecutando un comando en el servicio lbctl-liburutegia y se está creando un contenedor con el mismo nombre. El contenedor se eliminará automáticamente cuando se detenga el proceso de ejecución del comando.

%* : espera mas parametros
```

_Este archivo permite utilizar el comando lbctl en la consola de Windows._

#### Agrega la ruta del archivo lbctl.bat a la variable de entorno PATH para que el comando sea reconocido en la consola.

1. **Para agregar la ruta del archivo lbctl.bat a la variable de entorno PATH en modo gráfico en Windows, sigue estos pasos:**

  - Haz clic en el botón de "Inicio" y busca "Sistema" en la barra de búsqueda.
  - Haz clic en "Editar las variables de entorno del sistema" en la lista de resultados de búsqueda.
    - En la ventana que aparece, haz clic en el botón "Variables de entorno".
  - Busca la variable de sistema "Path" y haz clic en "Editar".
  - Haz clic en "Nuevo" y agrega la ruta completa de la carpeta que contiene el archivo lbctl.bat.
  - Haz clic en "Aceptar" en todas las ventanas abiertas.
_Nota: Es importante separar cada ruta en la variable PATH con un punto y coma (;)._

Ahora puedes utilizar el comando lbctl seguido de los parámetros que desees. Por ejemplo:
```
lbctl find -t Pokemon
```
:ok_hand:

2. **Para agregar la ruta del archivo lbctl.bat a la variable de entorno PATH desde la línea de comandos en Windows, se puede seguir estos pasos:**

  - Abrir la línea de comandos (pulsando la tecla Windows + R, escribiendo "cmd" y pulsando Enter).
  - Escribir el siguiente comando y pulsar Enter:
  ```
  setx PATH "%PATH%;C:\ruta\hacia\lbctl.bat"
  ```
:file_folder: _Donde "C:\ruta\hacia\lbctl.bat" es la ruta donde se encuentra el archivo lbctl.bat. Si la ruta tiene espacios en blanco, asegurarse de colocarla entre comillas dobles (")._

  - Cerrar y volver a abrir la línea de comandos para que los cambios surtan efecto.

Después de esto, se debería poder ejecutar el comando lbctl desde cualquier ubicación en la línea de comandos sin tener que especificar la ruta completa hacia el archivo lbctl.bat. Por ejemplo:
```
lbctl find -t Pokemon
```
:ok_hand:
