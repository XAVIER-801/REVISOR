"""Tests end-to-end del motor con una tesis real."""
import pytest
import os
import shutil
import tempfile
from services.word_engine import WordAuditEngine
from services.docx_annotator import DocxAnnotator


def test_engine_runs_without_errors(sample_thesis_path):
    """El motor debe ejecutar todos los auditores sin lanzar excepciones."""
    tmpdir = tempfile.mkdtemp()
    test_file = os.path.join(tmpdir, "test.docx")
    shutil.copy(sample_thesis_path, test_file)

    engine = WordAuditEngine(test_file)
    result = engine.run_audit()

    assert "stats" in result
    assert "results" in result
    assert len(result["results"]) > 0
    assert result["stats"]["score"] >= 0
    assert result["stats"]["score"] <= 100

    if engine.working_path != test_file and os.path.exists(engine.working_path):
        os.remove(engine.working_path)
    os.remove(test_file)
    os.rmdir(tmpdir)


def test_metadata_extraction(sample_thesis_path):
    """El motor debe extraer metadata de la portada."""
    tmpdir = tempfile.mkdtemp()
    test_file = os.path.join(tmpdir, "test.docx")
    shutil.copy(sample_thesis_path, test_file)

    engine = WordAuditEngine(test_file)
    engine.run_audit()
    meta = engine.extract_metadata()

    assert "faculty" in meta
    assert "school" in meta
    assert "year" in meta
    assert "degree_type" in meta

    if engine.working_path != test_file and os.path.exists(engine.working_path):
        os.remove(engine.working_path)
    os.remove(test_file)
    os.rmdir(tmpdir)


def test_annotator_generates_output(sample_thesis_path):
    """El anotador debe generar un docx anotado válido."""
    tmpdir = tempfile.mkdtemp()
    test_file = os.path.join(tmpdir, "test.docx")
    shutil.copy(sample_thesis_path, test_file)

    engine = WordAuditEngine(test_file)
    result = engine.run_audit()

    annotator = DocxAnnotator(engine.working_path)
    out_path, out_name = annotator.annotate(result)

    assert os.path.exists(out_path)
    assert os.path.getsize(out_path) > 1000  # No vacío

    os.remove(out_path)
    if engine.working_path != test_file and os.path.exists(engine.working_path):
        os.remove(engine.working_path)
    os.remove(test_file)
    os.rmdir(tmpdir)
