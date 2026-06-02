"""Tests del auditor de ortografía."""
import pytest
from services.auditors.ortografia import OrtografiaAuditor


class MockEngine:
    """Mock simple del engine para tests aislados."""
    def __init__(self, paragraphs):
        self.paragraphs = paragraphs
        self.results = []
        self.stats = {"score": 100, "errors": 0, "warnings": 0, "passed": 0}
        self.sections_found = set()
        self.anexos_start_idx = -1
        self.last_index_idx = -1
        self.index_start_idx = -1

    def _add(self, cat, rule, status, msg, expected="", actual="",
             p_idx=None, p_text="", page=None, section=None):
        if status == "error":
            self.stats["errors"] += 1
        elif status == "warning":
            self.stats["warnings"] += 1
        self.results.append({
            "category": cat, "rule": rule, "status": status,
            "message": msg, "expected": expected, "actual": actual,
        })


def _make_paragraph(text, idx=0):
    return {
        "text": text,
        "norm": text.upper(),
        "index": idx,
        "estimated_page": 1,
        "section": "General",
        "is_cover": False,
        "in_table": False,
        "has_omml": False,
        "is_display_equation": False,
    }


def test_detects_triple_letter():
    auditor = OrtografiaAuditor.__new__(OrtografiaAuditor)
    auditor.engine = MockEngine([
        _make_paragraph("Este es un texto con la palabra siiii mal escrita y otras palabras normales para llegar al mínimo de longitud requerido.")
    ])
    auditor.audit()
    rules = [r["rule"] for r in auditor.engine.results]
    assert any("siiii" in r for r in rules), f"No se detectó 'siiii': {rules}"


def test_detects_letter_digit_mix():
    auditor = OrtografiaAuditor.__new__(OrtografiaAuditor)
    auditor.engine = MockEngine([
        _make_paragraph("Este párrafo tiene la palabra ho1a con un cero pegado a las letras y debería ser detectado como error.")
    ])
    auditor.audit()
    rules = [r["rule"] for r in auditor.engine.results]
    assert any("ho1a" in r for r in rules), f"No detectó mezcla letras/dígitos: {rules}"


def test_allows_valid_codes():
    """Códigos válidos como H2O, CO2, IPv4 no deben marcarse."""
    auditor = OrtografiaAuditor.__new__(OrtografiaAuditor)
    auditor.engine = MockEngine([
        _make_paragraph("La fórmula del agua H2O y el dióxido CO2 son ejemplos del lenguaje químico estándar usado en química.")
    ])
    auditor.audit()
    rules = [r["rule"] for r in auditor.engine.results if "Palabra" in r.get("rule", "")]
    # H2O y CO2 NO deben aparecer como error
    assert not any("H2O" in r or "CO2" in r for r in rules)


def test_detects_repeated_words():
    auditor = OrtografiaAuditor.__new__(OrtografiaAuditor)
    auditor.engine = MockEngine([
        _make_paragraph("Este párrafo tiene la la palabra repetida dos veces consecutivas y debería ser detectado correctamente.")
    ])
    auditor.audit()
    rules = [r["rule"] for r in auditor.engine.results]
    assert any("repetida" in r.lower() for r in rules), f"No detectó repetición: {rules}"


def test_no_false_positives_short_paragraph():
    """Párrafos muy cortos no se evalúan."""
    auditor = OrtografiaAuditor.__new__(OrtografiaAuditor)
    auditor.engine = MockEngine([_make_paragraph("Hola.")])
    auditor.audit()
    # No debería reportar nada salvo el resumen ('passed')
    error_reports = [r for r in auditor.engine.results if r["status"] != "passed"]
    assert len(error_reports) == 0


def test_repeated_words_ignores_parentheses():
    """OrtografiaAuditor must ignore repeated words separated by parentheses or punctuation."""
    auditor = OrtografiaAuditor.__new__(OrtografiaAuditor)
    auditor.engine = MockEngine([
        _make_paragraph("El dragón (Dragón) de la leyenda vivía en una cueva muy profunda cerca de la colina y aterrorizaba al pueblo de dragón Dragón."),
    ])
    auditor.audit()
    
    rules = [r["rule"] for r in auditor.engine.results if "Palabra repetida" in r["rule"]]
    assert len(rules) == 1
    assert "dragón Dragón" in rules[0]

