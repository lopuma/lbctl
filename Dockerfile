# # Instala el cliente de Docker
# # RUN apt-get update && \
# #     apt-get install -y apt-transport-https ca-certificates curl gnupg2 software-properties-common && \
# #     curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - && \
# #     add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" && \
# #     apt-get update && \
# #     apt-get install -y docker-ce-cli

FROM python:3.10 AS build

# Establecer el directorio de trabajo
WORKDIR /app

# Asegurarse de que el usuario tenga los permisos necesarios para escribir en el directorio
RUN chown ${MY_USER}:${MY_USER} /app

# Cambiar a ese usuario
USER ${MY_USER}

# Actualizar pip
RUN python -m pip install --upgrade pip

# Instalar las dependencias
COPY ./conf/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Crear el directorio covers-liburutegia
RUN mkdir -p /app/${BUCKET_NAME}

# Copiar el código fuente
COPY . .

#Stage 2: Create the final image
FROM python:3.13.0a3-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar las dependencias y el código fuente desde la etapa de build
COPY --from=build /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=build /app /app

# Establecer el usuario por defecto
USER ${MY_USER}

# Establecer el comando por defecto
ENTRYPOINT ["python", "/app/src/lbctl.py"]