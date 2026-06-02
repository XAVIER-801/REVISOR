# ai_engine — Motor de IA del REVISOR

Carpeta **PARALELA** al motor de auditoría. No interfiere con la funcionalidad principal.

## Componentes

```
ai_engine/
├── __init__.py
├── README.md                  ← este archivo
├── requirements.txt           ← dependencias adicionales
├── image_ocr.py               ← OCR de imágenes con Tesseract
├── scanned_auditor.py         ← auditor de documentos escaneados (Jurados, Turnitin, Autorización)
├── learning_system.py         ← sistema de aprendizaje propio
├── knowledge_base.py          ← base de conocimiento persistente (JSON)
├── knowledge/                 ← archivos JSON aprendidos (auto-generados)
│   ├── error_patterns.json    ← patrones de errores frecuentes
│   ├── thesis_corpus.json     ← corpus de tesis procesadas
│   └── suggestions.json       ← sugerencias generadas
└── models/                    ← modelos entrenados (opcional)
```

## Activación

Por defecto **NO se ejecuta** durante una auditoría normal. Para activarlo:

1. Instalar dependencias adicionales:
   ```bash
   pip install -r ai_engine/requirements.txt
   ```

2. Instalar Tesseract OCR (sistema):
   - **Windows**: descargar de https://github.com/UB-Mannheim/tesseract/wiki
   - **Linux**: `apt-get install tesseract-ocr tesseract-ocr-spa`
   - **macOS**: `brew install tesseract tesseract-lang`

3. En `main.py`, importar y llamar opcionalmente:
   ```python
   from ai_engine.scanned_auditor import ScannedAuditor
   from ai_engine.learning_system import LearningSystem

   # Auditar imágenes escaneadas
   scanned = ScannedAuditor(engine.working_path)
   image_results = scanned.audit()
   audit_results['results'].extend(image_results)

   # Aprender de esta tesis
   ls = LearningSystem()
   ls.ingest(audit_results, file_metadata)
   suggestions = ls.suggest_improvements()
   ```

## Tecnologías (todas gratuitas)

- **Tesseract OCR** (Google, open source): reconoce texto en imágenes
- **Pillow**: manejo de imágenes
- **NumPy**: manejo de matrices/datos
- **scikit-learn** (opcional): clasificación simple
- **JSON**: base de conocimiento persistente

**NO usa**: Gemini, OpenAI, GPT, ni ningún servicio de pago.

## Sistema de aprendizaje (resumen)

El sistema aprende de forma simple pero efectiva:

1. **Captura** cada auditoría: errores encontrados, frecuencias, contexto.
2. **Agrupa** errores por patrón (regla + contexto similar).
3. **Estadísticas** por categoría: % de tesis con cierto error, top errores, escuelas con más problemas.
4. **Sugerencias** basadas en los patrones más frecuentes: "El 80% de las tesis de tu escuela cometen este error, presta atención."
5. **Evolución**: mientras más tesis se procesen, mejores serán las sugerencias.

No es deep learning ni LLM. Es **inteligencia estadística aplicada** — interpretable,
auditable, sin costo de API.
