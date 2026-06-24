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
import threading
from typing import Dict
from dotenv import load_dotenv
from services.word_engine import WordAuditEngine
from services.docx_annotator import DocxAnnotator

load_dotenv()  # Carga backend-python/.env

# ── ai_engine: carga OPCIONAL ──
try:
    from ai_engine.scanned_auditor import ScannedAuditor
    from ai_engine.learning_system import LearningSystem
    from ai_engine.knowledge_base import KnowledgeBase
    from ai_engine.groq_assistant import GroqAssistant
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

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "tmp_uploads")
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


def _save_audit_to_supabase_worker(filename: str, audit_result: dict):
    """Worker que persiste en Supabase (se ejecuta en un hilo separado, no bloquea)."""
    try:
        from ai_engine.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        if not supabase:
            print("[Supabase] ⚠️ No configurado — omitiendo guardado.")
            return

        stats = audit_result.get("stats", {})
        all_results = audit_result.get("results", [])

        # Snapshot resumido (solo errores y warnings, máx 200 para no saturar)
        snapshot_items = [r for r in all_results if r.get("status") in ("error", "warning")]
        original_snapshot = [
            {"rule": r["rule"], "category": r["category"], "status": r["status"],
             "severity": r.get("severity", r["status"]),
             "actual": str(r.get("actual", ""))[:200],
             "expected": str(r.get("expected", ""))[:200]}
            for r in snapshot_items[:200]
        ]

        thesis_data = {
            "filename": filename,
            "score": stats.get("score", 0),
            "errors_count": stats.get("errors", 0),
            "warnings_count": stats.get("warnings", 0),
            "passed_count": stats.get("passed", 0),
            "status": "pending_review",
            "annotated_docx_base64": audit_result.get("annotatedBase64"),
            "original_results_snapshot": original_snapshot,
        }

        resp = supabase.table("thesis_audits").insert(thesis_data).execute()
        if not resp.data:
            print("[Supabase] ❌ Error insertando thesis_audit")
            return
        thesis_id = resp.data[0]["id"]
        print(f"[Supabase] ✅ Tesis guardada: {thesis_id}")

        # Guardar observaciones (máx 500, en lotes de 100)
        obs_to_save = [
            {
                "thesis_id": thesis_id,
                "rule": r.get("rule", ""),
                "category": r.get("category", ""),
                "severity": r.get("severity", r["status"]),
                "message": r.get("message", ""),
                "expected": str(r.get("expected", ""))[:500] if r.get("expected") else None,
                "actual": str(r.get("actual", ""))[:500] if r.get("actual") else None,
                "paragraph_index": r.get("paragraphIndex"),
                "paragraph_text": str(r.get("paragraphText", ""))[:1000] if r.get("paragraphText") else None,
                "status": "pending",
            }
            for r in snapshot_items[:500]
        ]

        # Insertar en lotes de 100
        batch_size = 100
        for i in range(0, len(obs_to_save), batch_size):
            batch = obs_to_save[i:i + batch_size]
            try:
                supabase.table("thesis_observations").insert(batch).execute()
            except Exception as batch_err:
                print(f"[Supabase] ⚠️ Error en lote {i//batch_size + 1}: {batch_err}")

        print(f"[Supabase] ✅ {len(obs_to_save)} observaciones guardadas para {thesis_id}")

    except Exception as e:
        import traceback
        print(f"[Supabase] ❌ Error inesperado: {e}")
        traceback.print_exc()


def save_audit_to_supabase(filename: str, audit_result: dict):
    """Lanza el guardado en Supabase en un hilo background para no bloquear la respuesta."""
    t = threading.Thread(
        target=_save_audit_to_supabase_worker,
        args=(filename, audit_result),
        daemon=True,
    )
    t.start()


def _run_audit_pipeline(file_path: str, filename: str) -> dict:
    """Pipeline completo de auditoría. Reutilizable por endpoints sync y async."""
    engine = WordAuditEngine(file_path)
    audit_results = engine.run_audit()

    # OCR opcional temporalmente desactivado para evitar demoras de 200s
    # if AI_ENGINE_AVAILABLE:
    #     try:
    #         scanned = ScannedAuditor(engine.working_path)
    #         ocr_results = scanned.audit()
    #         if ocr_results:
    #             audit_results.setdefault("results", []).extend(ocr_results)
    #             new_errors = sum(1 for r in ocr_results if r.get("status") == "error")
    #             new_warnings = sum(1 for r in ocr_results if r.get("status") == "warning")
    #             audit_results["stats"]["errors"] += new_errors
    #             audit_results["stats"]["warnings"] += new_warnings
    #     except Exception as e:
    #         print(f"ℹ️  OCR opcional no ejecutado: {e}")

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
            
            # Post-procesamiento con Asistente IA Groq (opcional)
            groq = GroqAssistant()
            if groq.is_available():
                print("Iniciando revisión inteligente con Groq...")
                audit_results = groq.review_observations(audit_results)
                
        except Exception as e:
            print(f"Sistema de aprendizaje/asistente opcional: {e}")

    # Construir respuesta
    result_dict = {
        **audit_results,
        "annotatedBase64": annotated_base64,
        "engine": "python-hifi",
        "ai_suggestions": suggestions,
    }

    # Limpieza de archivos temporales ANTES de guardar en Supabase
    if annotator_path and os.path.exists(annotator_path):
        os.remove(annotator_path)
    if engine.working_path != file_path and os.path.exists(engine.working_path):
        os.remove(engine.working_path)

    # Persistencia en Supabase en background (no bloquea la respuesta al frontend)
    save_audit_to_supabase(filename, result_dict)

    return result_dict


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
# ENDPOINTS DEL ASISTENTE GROQ
# ══════════════════════════════════════════════════════════════════════

from pydantic import BaseModel

class CorrectionReq(BaseModel):
    type: str  # "corrections", "false_positives", "clarifications"
    issue: str
    fix: str
    rule_affected: str = ""

@app.post("/ai/learn")
async def ai_learn(correction: CorrectionReq):
    """Enseña al asistente IA una corrección o regla para futuras auditorías."""
    _ai_required()
    groq = GroqAssistant()
    
    data = {
        "issue": correction.issue,
        "fix": correction.fix,
        "rule_affected": correction.rule_affected
    }
    
    success = groq.learn_from_correction(correction.type, data)
    if not success:
        raise HTTPException(status_code=400, detail="Tipo de corrección inválido (debe ser: corrections, false_positives o clarifications)")
        
    return {"status": "success", "message": "Memoria de IA actualizada"}

@app.get("/ai/memory")
async def ai_memory():
    """Ver el estado actual de la memoria del asistente IA."""
    _ai_required()
    groq = GroqAssistant()
    return groq.get_memory()


# ══════════════════════════════════════════════════════════════════════
# ENDPOINTS DEL AUTOFIXER (IA)
# ══════════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_auto_fix():
    """Al arrancar el servidor, si hay feedback pendiente, lanza el AutoFixer en background."""
    if AI_ENGINE_AVAILABLE:
        import asyncio
        asyncio.create_task(_run_autofix_background())

async def _run_autofix_background():
    import asyncio
    await asyncio.sleep(10)  # Espera 10s que el server termine de iniciar
    try:
        from ai_engine.auto_fixer import AutoFixer
        fixer = AutoFixer()
        result = fixer.run()
        if "error" not in result:
            print(f"[STARTUP AutoFixer] {result.get('applied', 0)} mejoras aplicadas, {result.get('reverted', 0)} revertidas.")
        else:
            print(f"[STARTUP AutoFixer] Error: {result['error']}")
    except Exception as e:
        print(f"[STARTUP AutoFixer] Exception: {e}")

@app.post("/ai/autofix/run")
async def run_autofix():
    """Ejecuta el AutoFixer manualmente. Solo disponible mientras el servidor está activo."""
    _ai_required()
    try:
        from ai_engine.auto_fixer import AutoFixer
        fixer = AutoFixer()
        result = fixer.run()
        if "error" in result:
             raise HTTPException(status_code=500, detail=result["error"])
        return {
            "fixes_applied": result.get('applied', 0),
            "fixes_reverted": result.get('reverted', 0),
            "fixes_pending_retry": result.get('retrying', 0),
            "fixes_manual_review": result.get('manual_review', 0),
            "details": result.get('details', [])
        }
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@app.get("/ai/autofix/history")
async def autofix_history(limit: int = 50):
    """Historial de cambios de código automáticos desde Supabase."""
    _ai_required()
    from ai_engine.supabase_client import get_supabase_client
    supabase = get_supabase_client()
    if not supabase:
        return {"history": []}
    try:
        resp = supabase.table("ai_code_fixes")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        return {"history": resp.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ══════════════════════════════════════════════════════════════════════
# DIAGNÓSTICO
# ══════════════════════════════════════════════════════════════════════

@app.get("/debug/supabase")
async def debug_supabase():
    """Verifica la conexión a Supabase y muestra las variables de entorno."""
    from ai_engine.supabase_client import get_supabase_client
    
    url = os.getenv("SUPABASE_URL") or "(no configurado)"
    key_preview = (os.getenv("SUPABASE_ANON_KEY") or "None")[:12] + "..." if os.getenv("SUPABASE_ANON_KEY") else "None"
    
    supabase = get_supabase_client()
    if not supabase:
        return {
            "connected": False,
            "supabase_url": url,
            "supabase_key": key_preview,
            "env_file_loaded": True,
            "error": "No se pudo crear el cliente. Verifica las credenciales en backend-python/.env",
        }
    
    try:
        resp = supabase.table("thesis_audits").select("count", count="exact").limit(0).execute()
        return {
            "connected": True,
            "supabase_url": url,
            "supabase_key": key_preview,
            "table_thesis_audits": "existe",
            "total_audits": resp.count,
        }
    except Exception as e:
        return {
            "connected": True,
            "supabase_url": url,
            "supabase_key": key_preview,
            "table_thesis_audits": f"error: {e}",
            "suggestion": "Ejecuta el script supabase-schema.sql en Supabase SQL Editor para crear las tablas",
        }


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
