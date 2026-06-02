"""Tests del knowledge_base y learning_system."""
import pytest
import os
import tempfile
from ai_engine.knowledge_base import KnowledgeBase
from ai_engine.learning_system import LearningSystem


@pytest.fixture
def temp_kb():
    """KnowledgeBase con directorio temporal aislado."""
    tmpdir = tempfile.mkdtemp()
    kb = KnowledgeBase(base_dir=tmpdir)
    yield kb
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_record_audit_increments_count(temp_kb):
    assert temp_kb.total_thesis() == 0
    audit = {
        "stats": {"score": 85, "errors": 5, "warnings": 10, "passed": 100},
        "results": [
            {"category": "Portada", "rule": "Tamaño Logo", "status": "error",
             "actual": "4.20cm", "expected": "4.33cm"},
        ],
    }
    temp_kb.record_audit(audit, {"filename": "tesis_1.docx", "school": "Sociología"})
    assert temp_kb.total_thesis() == 1


def test_top_errors(temp_kb):
    """Top errors debe reflejar las reglas más frecuentes."""
    for i in range(5):
        audit = {
            "stats": {"score": 70, "errors": 1, "warnings": 0, "passed": 0},
            "results": [
                {"category": "Viñetas", "rule": "Símbolo Prohibido", "status": "error"},
            ],
        }
        temp_kb.record_audit(audit, {"filename": f"t{i}.docx"})
    top = temp_kb.top_errors(5)
    assert len(top) >= 1
    assert top[0]["count"] == 5
    assert "Símbolo Prohibido" in top[0]["rule"]


def test_ranking_schools(temp_kb):
    audits = [
        ({"score": 90, "errors": 1, "warnings": 0, "passed": 30}, {"school": "Sociología"}),
        ({"score": 95, "errors": 0, "warnings": 0, "passed": 30}, {"school": "Sociología"}),
        ({"score": 60, "errors": 5, "warnings": 10, "passed": 20}, {"school": "Ingeniería"}),
    ]
    for stats, meta in audits:
        temp_kb.record_audit({"stats": stats, "results": []}, {**meta, "filename": "f.docx"})
    ranking = temp_kb.ranking_schools()
    assert ranking[0]["school"] == "Sociología"
    assert ranking[0]["avg_score"] == 92.5


def test_curiosities(temp_kb):
    temp_kb.record_audit(
        {"stats": {"score": 80, "errors": 3, "warnings": 5, "passed": 50}, "results": []},
        {"filename": "t.docx", "school": "Sociología", "faculty": "Ciencias Sociales"},
    )
    cur = temp_kb.curiosities()
    assert cur["total_thesis"] == 1
    assert cur["global_avg_score"] == 80.0
