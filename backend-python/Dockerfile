FROM python:3.12-slim

# Instalar dependencias de sistema (LibreOffice para conversión y dependencias de PyMuPDF)
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-java-common \
    default-jre \
    libmupdf-dev \
    libfreetype6-dev \
    libjbig2dec0-dev \
    libjpeg-dev \
    libopenjp2-7-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Crear directorio para subidas temporales
RUN mkdir -p tmp_uploads && chmod 777 tmp_uploads

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
