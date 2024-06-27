### Línea de Comandos de Docker, docker run, Volúmenes y Sobreescribir el Punto de Entrada de un Container

- **docker run**: Crea y inicia un nuevo contenedor. Permite especificar opciones como volúmenes, redes, y argumentos que sobrescriben los definidos en el Dockerfile.
- **Volúmenes**: Permiten persistir datos generados y utilizados por los contenedores incluso después de que estos sean detenidos o eliminados. Se pueden montar desde el host o crearlos dentro del contenedor.
- **Sobreescribir el Punto de Entrada**: Al ejecutar un contenedor con `docker run`, puedes sobrescribir el `ENTRYPOINT` definido en el Dockerfile pasando argumentos adicionales. Por ejemplo, si tu Dockerfile tiene `ENTRYPOINT ["python", "app.py"]`, puedes ejecutar `docker run <image> python another_script.py` para ejecutar `another_script.py` en lugar de `app.py`.

### docker inspect y docker network, Comunicación Entre Puertos Internos y Externos

- **docker inspect**: Muestra información detallada sobre un contenedor, imagen, red, volumen, etc. Es útil para entender configuraciones y estados actuales.
- **docker network**: Gestiona las redes de Docker, incluyendo la creación de nuevas redes, conexión de contenedores a redes existentes, y visualización de la topología de red.

### Conceptos de Virtualización Generales y Funcionamiento Interno de Docker

Docker utiliza **contenedores**, que son instancias ligeras de software que emulan un entorno de servidor completo. A diferencia de las máquinas virtuales, los contenedores comparten el mismo kernel del host y solo aísolan las aplicaciones y sus dependencias. Esto hace que los contenedores sean más ligeros y rápidos de iniciar que las máquinas virtuales.

El **funcionamiento interno de Docker** implica varios componentes, incluyendo:

- **Docker Engine**: El motor principal que construye, ejecuta y gestiona los contenedores.
- **Docker Images**: Plantillas que definen el estado de un contenedor. Las imágenes se construyen a partir de Dockerfiles y se pueden compartir entre usuarios.
- **Docker Daemon**: Un demonio que se ejecuta en segundo plano y maneja solicitudes de API de Docker.
- **Docker Hub**: Un registro público donde los desarrolladores pueden buscar, descargar y compartir imágenes de Docker.

En resumen, Docker simplifica la implementación, escalabilidad y administración de aplicaciones al encapsularlas en contenedores ligeros y portátiles, facilitando la distribución y el despliegue de estas aplicaciones en cualquier entorno que tenga Docker instalado.

Citations:
[1] https://docs.docker.com/reference/dockerfile/
[2] https://docs.docker.com/engine/reference/run/
[3] https://stackoverflow.com/questions/41694329/docker-run-override-entrypoint-with-shell-script-which-accepts-arguments
[4] https://www.bmc.com/blogs/docker-cmd-vs-entrypoint/
[5] https://github.com/moby/moby/issues/5539
[6] https://stackoverflow.com/questions/52942913/docker-compose-docker-entrypoint
[7] https://buddy.works/tutorials/docker-commands-cheat-sheet
[8] https://www.quora.com/How-do-you-create-a-Docker-image-from-the-command-line
[9] https://www.squash.io/docker-how-to-workdir-run-cmd-env-variables/
[10] https://www.quora.com/Do-Docker-containers-remember-previously-run-commands

## DHT ( CHORD )

* Casos de uso, dominio de datos, problemas que resuelve
* Extensión de la implementación provista ( inserción y eliminación de datos)
* Función del Hash, balance de datos y consistencia del anillo
* Funcionamiento interno, función sucesor, stabilize y finger_table 

## Nociones básicas de línea de comandos linux

* Comandos esenciales, ls, cd, mkdir, rm
* Arbol de archivos de linux
* Ejecución de programas via línea de comandos

## Misc
* Despliegue de una solución distribuida en docker vs en bare metal ( sin docker )
* Ejecución de varios containers compartiendo una misma base de código
* Inspeccionar imagen de docker, detección de ip de la misma
* Cualquier archivo de cp provisto es susceptible a evaluación
