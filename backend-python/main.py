"""
main.py - API FastAPI del REVISOR.

Endpoints:
- POST /audit            → Auditoría síncrona (compatibilidad con frontend actual)
- POST /audit/queue      → Encolar tesis para procesamiento asíncrono
- GET  /audit/status/{id}→ Consultar estado de una tarea en cola
- GET  /audit/result/{id}→ Obtener resultado de una tarea completada
- GET  /ai/insights      → Estadísticas globales del corpus aprendido
- GET  /ai/stats/schools → Ranking de escuelas profesionales
- GET  /ai/stats/faculties→ Ranking de facultades
- GET  /ai/stats/categories→ Errores por categoría
- GET  /ai/stats/curiosities→ Estadísticas curiosas / dashboard
- GET  /ai/stats/writing → Ranking de calidad de redacción
- GET  /health           → Health check
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import shutil
import base64
import uuid
import asyncio
import time
from typing import Dict
from services.word_engine import WordAuditEngine
from services.docx_annotator import DocxAnnotator

# ── ai_engine: carga OPCIONAL ──
try:
    from ai_engine.scanned_auditor import ScannedAuditor
    from ai_engine.learning_system import LearningSystem
    from ai_engine.knowledge_base import KnowledgeBase
    AI_ENGINE_AVAILABLE = True
except Exception as _e:
    print(f"ℹ️  ai_engine no disponible (opcional): {_e}")
    AI_ENGINE_AVAILABLE = False


app = FastAPI(title="REVISOR — Auditor de Tesis UNAP", version="3.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "/tmp/audit_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── Cola de procesamiento (en memoria) ──────────────────────────────────
# Para production con miles de tesis simultáneas, sustituir por Celery/Redis.
# Aquí usamos un dict simple + BackgroundTasks de FastAPI para no requerir
# infraestructura extra.
TASKS: Dict[str, dict] = {}
MAX_KEEP_TASKS = 500  # FIFO


def _cleanup_old_tasks():
    """Limpia tareas antiguas para evitar crecimiento ilimitado."""
    if len(TASKS) > MAX_KEEP_TASKS:
        oldest = sorted(TASKS.items(), key=lambda x: x[1].get("created", 0))
        for tid, _ in oldest[: len(TASKS) - MAX_KEEP_TASKS]:
            TASKS.pop(tid, None)


def _run_audit_pipeline(file_path: str, filename: str) -> dict:
    """Pipeline completo de auditoría. Reutilizable por endpoints sync y async."""
    engine = WordAuditEngine(file_path)
    audit_results = engine.run_audit()

    # OCR opcional
    if AI_ENGINE_AVAILABLE:
        try:
            scanned = ScannedAuditor(engine.working_path)
            ocr_results = scanned.audit()
            if ocr_results:
                audit_results.setdefault("results", []).extend(ocr_results)
                new_errors = sum(1 for r in ocr_results if r.get("status") == "error")
                new_warnings = sum(1 for r in ocr_results if r.get("status") == "warning")
                audit_results["stats"]["errors"] += new_errors
                audit_results["stats"]["warnings"] += new_warnings
        except Exception as e:
            print(f"ℹ️  OCR opcional no ejecutado: {e}")

    # Anotación
    annotated_base64 = None
    annotator_path = None
    try:
        annotator = DocxAnnotator(engine.working_path)
        annotator_path, _ = annotator.annotate(audit_results)
        if os.path.exists(annotator_path):
            with open(annotator_path, "rb") as f:
                annotated_base64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"⚠️ Error generando anotaciones: {e}")

    # Aprendizaje con metadata auto-detectada
    suggestions = []
    if AI_ENGINE_AVAILABLE:
        try:
            metadata = engine.extract_metadata()
            metadata["filename"] = filename
            ls = LearningSystem()
            ls.ingest(audit_results, metadata)
            suggestions = ls.suggest_improvements(audit_results, metadata)
        except Exception as e:
            print(f"ℹ️  Sistema de aprendizaje opcional: {e}")

    # Limpieza
    if annotator_path and os.path.exists(annotator_path):
        os.remove(annotator_path)
    if engine.working_path != file_path and os.path.exists(engine.working_path):
        os.remove(engine.working_path)

    return {
        **audit_results,
        "annotatedBase64": annotated_base64,
        "engine": "python-hifi",
        "ai_suggestions": suggestions,
    }


# ══════════════════════════════════════════════════════════════════════
# ENDPOINTS DE AUDITORÍA
# ══════════════════════════════════════════════════════════════════════

@app.post("/audit")
async def perform_audit(file: UploadFile = File(...)):
    """Auditoría SÍNCRONA — respuesta inmediata con todos los resultados."""
    session_id = str(uuid.uuid4())
    temp_file_path = os.path.join(UPLOAD_DIR, f"{session_id}_{file.filename}")

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = _run_audit_pipeline(temp_file_path, file.filename)
        return result
    except Exception as e:
        print(f"🛑 Error Maestro: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {e}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@app.post("/audit/queue")
async def queue_audit(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    Encola una tesis para procesamiento ASÍNCRONO.
    Útil cuando varios usuarios suben tesis simultáneamente.

    Retorna un task_id. Use GET /audit/status/{task_id} para consultar estado
    y GET /audit/result/{task_id} para obtener resultado cuando esté listo.
    """
    task_id = str(uuid.uuid4())
    temp_file_path = os.path.join(UPLOAD_DIR, f"{task_id}_{file.filename}")
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    TASKS[task_id] = {
        "status": "queued",
        "filename": file.filename,
        "created": time.time(),
        "result": None,
        "error": None,
    }
    _cleanup_old_tasks()

    background_tasks.add_task(_process_queued, task_id, temp_file_path, file.filename)

    return {
        "task_id": task_id,
        "status": "queued",
        "message": "Tesis encolada para procesamiento. Consulte /audit/status/" + task_id,
    }


def _process_queued(task_id: str, file_path: str, filename: str):
    """Worker que procesa una tesis encolada."""
    TASKS[task_id]["status"] = "processing"
    TASKS[task_id]["started"] = time.time()
    try:
        result = _run_audit_pipeline(file_path, filename)
        TASKS[task_id]["status"] = "completed"
        TASKS[task_id]["result"] = result
        TASKS[task_id]["completed"] = time.time()
    except Exception as e:
        TASKS[task_id]["status"] = "failed"
        TASKS[task_id]["error"] = str(e)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@app.get("/audit/status/{task_id}")
async def audit_status(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return {
        "task_id": task_id,
        "status": task["status"],
        "filename": task.get("filename"),
        "created": task.get("created"),
        "started": task.get("started"),
        "completed": task.get("completed"),
        "error": task.get("error"),
    }


@app.get("/audit/result/{task_id}")
async def audit_result(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    if task["status"] != "completed":
        return JSONResponse(
            status_code=202,
            content={"status": task["status"], "message": "Aún no listo"},
        )
    return task["result"]


@app.get("/audit/queue/list")
async def list_queue():
    """Lista pública del estado de la cola (sin resultados, solo metadatos)."""
    return {
        "total": len(TASKS),
        "queued": sum(1 for t in TASKS.values() if t["status"] == "queued"),
        "processing": sum(1 for t in TASKS.values() if t["status"] == "processing"),
        "completed": sum(1 for t in TASKS.values() if t["status"] == "completed"),
        "failed": sum(1 for t in TASKS.values() if t["status"] == "failed"),
        "tasks": [
            {
                "task_id": tid,
                "status": t["status"],
                "filename": t.get("filename"),
                "created": t.get("created"),
            }
            for tid, t in list(TASKS.items())[-50:]
        ],
    }


# ══════════════════════════════════════════════════════════════════════
# ENDPOINTS DE ESTADÍSTICAS (ai_engine)
# ══════════════════════════════════════════════════════════════════════

def _ai_required():
    if not AI_ENGINE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="ai_engine no disponible. Instale dependencias: pip install -r ai_engine/requirements.txt",
        )


@app.get("/ai/insights")
async def ai_insights():
    _ai_required()
    try:
        ls = LearningSystem()
        return {"available": True, **ls.global_insights()}
    except Exception as e:
        return {"available": False, "error": str(e)}


@app.get("/ai/stats/curiosities")
async def stats_curiosities():
    """Estadísticas curiosas e interesantes del corpus (para dashboard)."""
    _ai_required()
    kb = KnowledgeBase()
    return kb.curiosities()


@app.get("/ai/stats/schools")
async def stats_schools(min_thesis: int = 1, limit: int = 20):
    """Ranking de escuelas profesionales por puntaje promedio."""
    _ai_required()
    kb = KnowledgeBase()
    return {"ranking": kb.ranking_schools(min_thesis=min_thesis, limit=limit)}


@app.get("/ai/stats/faculties")
async def stats_faculties(min_thesis: int = 1):
    """Ranking de facultades por puntaje promedio."""
    _ai_required()
    kb = KnowledgeBase()
    return {"ranking": kb.ranking_faculties(min_thesis=min_thesis)}


@app.get("/ai/stats/categories")
async def stats_categories():
    """Distribución de errores por categoría en todo el corpus."""
    _ai_required()
    kb = KnowledgeBase()
    return {"categories": kb.errors_by_category()}


@app.get("/ai/stats/writing")
async def stats_writing(limit: int = 10):
    """Ranking de calidad de redacción por escuela."""
    _ai_required()
    kb = KnowledgeBase()
    return {"ranking": kb.writing_quality_ranking(limit=limit)}


@app.get("/ai/stats/top-errors")
async def stats_top_errors(n: int = 20):
    """Top N errores más frecuentes en el corpus."""
    _ai_required()
    kb = KnowledgeBase()
    return {"top_errors": kb.top_errors(n)}


# ══════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ══════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "3.1.0",
        "ai_engine_available": AI_ENGINE_AVAILABLE,
        "queue_size": len(TASKS),
    }


@app.get("/")
async def root():
    return {
        "name": "REVISOR — Auditor de Tesis UNAP",
        "version": "3.1.0",
        "endpoints": {
            "audit_sync": "POST /audit",
            "audit_async": "POST /audit/queue",
            "stats_curiosities": "GET /ai/stats/curiosities",
            "stats_schools": "GET /ai/stats/schools",
            "stats_faculties": "GET /ai/stats/faculties",
            "stats_categories": "GET /ai/stats/categories",
            "stats_writing": "GET /ai/stats/writing",
            "stats_top_errors": "GET /ai/stats/top-errors",
            "health": "GET /health",
            "docs": "/docs",
        },
    }
