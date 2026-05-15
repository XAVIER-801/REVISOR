from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import base64
import uuid
from services.word_engine import WordAuditEngine
from services.docx_annotator import DocxAnnotator

app = FastAPI(title="VRI-SCANNER Expert Engine", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "/tmp/audit_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/audit")
async def perform_audit(file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    temp_file_path = os.path.join(UPLOAD_DIR, f"{session_id}_{file.filename}")
    annotated_path = None

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 1. Ejecutar Auditoría Experta (Python High-Fidelity)
        engine = WordAuditEngine(temp_file_path)
        audit_results = engine.run_audit()

        # 2. GENERAR ANOTACIONES Y COMENTARIOS (Usando el archivo convertido)
        annotated_base64 = None
        try:
            # IMPORTANTE: Usamos engine.working_path (el .docx estandarizado)
            # para que el anotador pueda poner los comentarios sin errores de formato
            annotator = DocxAnnotator(engine.working_path)
            annotated_path, _ = annotator.annotate(audit_results)
            
            if os.path.exists(annotated_path):
                with open(annotated_path, "rb") as f:
                    annotated_base64 = base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            print(f"⚠️ Error generando anotaciones: {str(e)}")

        return {
            **audit_results,
            "annotatedBase64": annotated_base64,
            "engine": "python-hifi"
        }

    except Exception as e:
        print(f"🛑 Error Maestro: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        # Limpieza efímera (Privacidad Total)
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if annotated_path and os.path.exists(annotated_path):
            os.remove(annotated_path)
        # Limpiar también el archivo de trabajo si es distinto al temporal
        if hasattr(engine, 'working_path') and engine.working_path != temp_file_path:
            if os.path.exists(engine.working_path):
                os.remove(engine.working_path)
