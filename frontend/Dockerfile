# --- ETAPA 1: Producción ---
# Usamos una imagen base ligera de Nginx
# FROM nginx:alpine AS production-stage

# 1. Copiamos la configuración de Nginx personalizada.
# CLAVE: La ruta de origen es relativa al CONTEXTO de Docker (la raíz del proyecto)
# y ahora el archivo nginx.conf está directamente en frontend/
# COPY ./frontend/nginx.conf /etc/nginx/conf.d/default.conf

# 2. Copiamos los archivos estáticos de la página web (index.html, etc.).
# COPY ./frontend/ /usr/share/nginx/html

# Exponer el puerto 80 (puerto por defecto de Nginx)
# EXPOSE 80

# El CMD por defecto de Nginx inicia el servicio


# Usamos una imagen base de Node.js
FROM node:20-alpine

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar archivos de configuración para instalar dependencias primero
# Asume que estos están en la carpeta 'frontend' de tu host
COPY frontend/package*.json ./

# Instalar dependencias
RUN npm install

# Copiar el resto de los archivos del frontend (incluyendo src/, public/, index.html)
# NOTA: Este paso se usa principalmente para la construcción final, pero es buena práctica.
# En desarrollo, el VOLUME en docker-compose.yml lo sobreescribe.
COPY frontend/ .

# El puerto por defecto para el servidor de desarrollo de Vite
EXPOSE 5173

# CLAVE: Ejecutar el binario de vite directamente. 
# Esto asegura que el servidor se enlace correctamente a todas las interfaces (0.0.0.0)
# y al puerto 5173, donde se espera encontrar el index.html
CMD ["sh", "-c", "npx vite --host 0.0.0.0 --port 5173"]
