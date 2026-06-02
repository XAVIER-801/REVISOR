# Arquitectura del sistema

## Stack tecnológico

- **Frontend**: Next.js 16 + React 19 (puerto 3005)
- **Backend**: FastAPI Python 3.12 (puerto 8005)
- **Auditoría XML**: lxml (parsing directo del .docx OOXML)
- **OCR opcional**: Tesseract + pyspellchecker
- **NLP**: spaCy con modelo `es_core_news_sm`
- **Renderizado**: LibreOffice headless para conversión .doc → .docx
- **Containerización**: docker-compose

## Flujo de auditoría

```
Usuario sube .docx
       ↓
Frontend Next.js (/api/upload)
       ↓
POST a Python (/audit)
       ↓
DocConverter (estandariza a .docx si era .doc)
       ↓
WordAuditEngine.run_audit()
       ↓
30+ auditores modulares (en serie)
       ↓
DocxAnnotator (inyecta comentarios al margen)
       ↓
LearningSystem.ingest() (registra en knowledge_base)
       ↓
Respuesta JSON + .docx auditado en base64
```

## Componentes principales

### `services/word_engine.py`

Motor orquestador. Extrae propiedades XML (estilos, párrafos, tablas, footers, secciones, OMML, textboxes, drawings) y delega a los auditores.

### `services/auditors/*.py`

30+ auditores especializados. Cada uno hereda de `BaseAuditor` y valida un aspecto específico.

### `services/docx_annotator.py`

Inyecta comentarios nativos de Word con colores diferenciados (rojo / amarillo / verde / turquesa).

### `ai_engine/`

Subsistema paralelo opcional:

- `image_ocr.py` — Tesseract OCR
- `scanned_auditor.py` — Audita Hoja de Jurados, Turnitin, Autorización
- `knowledge_base.py` — Persistencia en JSON del corpus aprendido
- `learning_system.py` — Estadísticas + sugerencias progresivas

## Cola de procesamiento

Para procesamiento asíncrono con múltiples usuarios:

```python
POST /audit/queue          → encola tesis, devuelve task_id
GET  /audit/status/{id}    → consulta estado
GET  /audit/result/{id}    → obtiene resultado cuando esté completed
```

Implementación: dict en memoria + FastAPI BackgroundTasks. Para alta escala, sustituir por Celery + Redis.
