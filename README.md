# Guía de uso de lbctl `Liburutegia Control`

Este proyecto está diseñado para facilitar la gestión de la **biblioteca Liburutegia**.

> Podra buscar libros por Titulo, Author y ISBN, y añadirlo a la bases de datos.

## Requisitos

Para poder utilizar este proyecto necesitas tener ejecutandi la aplicacion web de Liburutegia 


- [Liburutegia](https://github.com/lopuma/liburutegia)

Para utilizar Liburutegia e Liburutegia control (**lbctl**) debes tener instalado Docker y Docker Compose en tu sistema operativo. Puedes descargar ambas herramientas de los siguientes enlaces:

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Cómo utilizar `LBCTL`

### Menú de opciones para lbctl

Puedes utilizar una de las siguientes opciones:

1. Buscar un libro por título: `lbctl find -t <título>`
2. Buscar un libro por autor: `lbctl find -a <autor>`
3. Buscar un libro por ISBN: `lbctl find -i <ISBN>`
4. Buscar libro por titulo, author y ISBN `lbctl find -t <título> -a <autor> -i <ISBN>`
5. help `lbctl -h / --help`


### Configuración

Antes de utilizar el proyecto, debes configurar las variables de entorno necesarias. Para ello debes tener configurado un fichero .env, se puede utilizar el mismo fichero .env utilizado en el proyecto la app web **Liburutegia**, añadiendo los siguientes.

```
# WebDriver
- COVER_DIR: es el directorio en el que se encuentran las imágenes de portada para los libros de Liburutegia.
- WEBDRIVER_HOST: es el nombre del host donde se ejecuta el servicio de WebDriver, el cual se utiliza para realizar pruebas automatizadas en la aplicación.

# MySql
- MYSQL_USER: es el nombre de usuario de la base de datos MySQL que utiliza la aplicación.
```

### Pasos comunes

- Descarga el archivo docker-compose.yml del proyecto [Liburutegia control](https://github.com/lopuma/lbctl).

- Modifica los valores de las variables de entorno en el archivo .env de acuerdo a tus necesidades.

- En una terminal o consola, navega hasta la carpeta donde descargaste el archivo docker-compose.yml.

## Puedes seguir estas 2 opciones para Linux

1. **Crea un alias en tu archivo .bashrc:**

- #### Editar .bashrc.

> sudo vi ~/.bashrc

- #### Añade lo siguiente.

```
alias lbctl='docker-compose run --rm --name lbctl-liburutegia lbctl-liburutegia "$@"'
```

_Este comando crea un alias lbctl que ejecuta el contenedor de Docker, la primera vez construira el contenedor._

- Recarga tu archivo .bashrc con el comando <sup> source ~/.bashrc </sup>

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

- #### Dale permisos de ejecución al script:

```
sudo chmod +x /usr/local/bin/lbctl
```

- #### Ahora puedes ejecutar el script en cualquier lugar utilizando el siguiente comando:

```
lbctl find -t Pokemon
```

