FROM python:3.10

# Crea un directorio de trabajo para tu aplicación
WORKDIR /app

# Copia el archivo `requirements.txt` a tu imagen
COPY ./conf/requirements.txt .

RUN python -m pip install --upgrade pip

# Instala las dependencias de tu aplicación
RUN pip install --no-cache-dir -r requirements.txt

ARG COVER_DIR

RUN mkdir -p /app/${COVER_DIR}

# Copia todo el código de tu aplicación a la imagen
COPY . .

# Instala el cliente de Docker
# RUN apt-get update && \
#     apt-get install -y apt-transport-https ca-certificates curl gnupg2 software-properties-common && \
#     curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - && \
#     add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" && \
#     apt-get update && \
#     apt-get install -y docker-ce-cli

# Define el comando para ejecutar tu script
ENTRYPOINT ["python", "/app/src/lbctl.py"]


# FROM python:3.10 AS build

# WORKDIR /app

# COPY ./conf/requirements.txt .

# RUN python -m pip install --upgrade pip

# RUN pip install --no-cache-dir -r requirements.txt

# COPY . .

# ARG COVER_DIR

# RUN mkdir -p /app/${COVER_DIR}

# #RUN python setup.py install

# # Stage 2: Create the final image
# FROM python:3.10-slim

# WORKDIR /app

# COPY --from=build /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# COPY --from=build . .

# ENTRYPOINT ["python", "/app/src/lbctl.py"]