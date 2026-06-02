"""Tests del auditor de viñetas."""
import pytest
from services.auditors.vinetas import VinetasAuditor


class MockEngine:
    def __init__(self, paragraphs):
        self.paragraphs = paragraphs
        self.results = []
        self.stats = {"score": 100, "errors": 0, "warnings": 0, "passed": 0}
        self.anexos_start_idx = -1
        self.last_index_idx = -1

    def _add(self, cat, rule, status, msg, expected="", actual="",
             p_idx=None, p_text="", page=None, section=None):
        if status == "error":
            self.stats["errors"] += 1
        elif status == "warning":
            self.stats["warnings"] += 1
        self.results.append({
            "category": cat, "rule": rule, "status": status,
            "actual": actual, "expected": expected,
        })


def _make_paragraph(text, idx=0, **kwargs):
    base = {
        "text": text,
        "norm": text.upper(),
        "index": idx,
        "estimated_page": 1,
        "section": "Capítulo I",
        "is_cover": False,
        "in_table": False,
        "is_in_body": True,
        "body_level": 1,
        "level": 1,
        "is_heading": False,
        "indent_left": 0.5 * 567,  # 0.5cm en twips
        "indent_hanging": 0.75 * 567,
        "alignment": "both",
        "line_spacing": 2.0,
        "spacing_before": 0,
        "spacing_after": 0,
        "runs": [{"text": text, "bold": False, "italic": False, "size": 12}],
        "list_fmt": None,
        "list_lvl_text": "",
        "style_id": "Normal",
    }
    base.update(kwargs)
    return base


def test_arrow_symbol_detected_as_prohibited():
    """Una viñeta con '➢' debe reportarse como símbolo no permitido."""
    auditor = VinetasAuditor.__new__(VinetasAuditor)
    capitulo = _make_paragraph("CAPITULO I", idx=0, is_in_body=True, body_level=1, is_heading=True)
    intro = _make_paragraph("INTRODUCCION", idx=1, is_in_body=True, body_level=1, is_heading=True)
    bullet = _make_paragraph("➢ Primera viñeta con flecha prohibida", idx=2)
    auditor.engine = MockEngine([capitulo, intro, bullet])
    auditor.audit()
    rules = [r["rule"] for r in auditor.engine.results]
    assert any("Símbolo de Viñeta No Permitido" in r for r in rules), f"No detectó símbolo prohibido: {rules}"


def test_dash_symbol_accepted():
    """Una viñeta con '-' es válida."""
    auditor = VinetasAuditor.__new__(VinetasAuditor)
    capitulo = _make_paragraph("CAPITULO I", idx=0, is_heading=True)
    intro = _make_paragraph("INTRODUCCION", idx=1, is_heading=True)
    bullet = _make_paragraph("- Primera viñeta correcta con guion", idx=2)
    auditor.engine = MockEngine([capitulo, intro, bullet])
    auditor.audit()
    rules = [r["rule"] for r in auditor.engine.results]
    assert not any("Símbolo de Viñeta No Permitido" in r for r in rules)
