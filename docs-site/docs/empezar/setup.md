# Configuración rápida (local)

## Opción 1: Docker (recomendado)

```bash
cd D:\REVISOR
docker-compose up -d
```

Esto levanta:

- Backend Python en `http://localhost:8005`
- Frontend Next.js en `http://localhost:3005`

## Opción 2: Local sin Docker

### Backend Python

```bash
cd D:\REVISOR\backend-python
pip install -r requirements.txt
pip install -r ai_engine/requirements.txt  # opcional (OCR + IA)
python -m spacy download es_core_news_sm
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Next.js

```bash
cd D:\REVISOR\thesis-reviewer
npm install
$env:PYTHON_API_URL = "http://localhost:8000"
npm run dev
```

## Tesseract OCR (opcional)

Para reconocer texto en documentos escaneados (Hoja de Jurados, Turnitin, Autorización):

- **Windows**: descarga desde [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki) e incluye el idioma español
- **Linux**: `sudo apt-get install tesseract-ocr tesseract-ocr-spa`
- **macOS**: `brew install tesseract tesseract-lang`

Si Tesseract no está instalado, el sistema funciona igual; solo se omiten las validaciones OCR.

## Tests

```bash
cd D:\REVISOR\backend-python
python -m pytest tests/ -v
```
