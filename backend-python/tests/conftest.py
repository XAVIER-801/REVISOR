"""
conftest.py - Fixtures compartidas de pytest.
"""
import os
import sys
import pytest

# Asegurar que el directorio backend-python esté en sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def sample_thesis_path():
    """Ruta a una tesis real para tests end-to-end."""
    candidates = [
        r'D:\REVISOR\TESIS PARA AUDITAR\0.006_TESIS_FINAL (1).docx',
        os.path.join(os.path.dirname(__file__), 'fixtures', 'sample.docx'),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    pytest.skip("No hay tesis de muestra disponible para tests end-to-end")


@pytest.fixture
def empty_results():
    """Resultado vacío para tests del anotador."""
    return {
        "stats": {"score": 100, "errors": 0, "warnings": 0, "passed": 0},
        "results": [],
    }
