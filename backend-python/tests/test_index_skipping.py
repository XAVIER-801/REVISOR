"""
Tests to verify index and table of contents skipping in Chapter and Section auditors.
"""
import pytest
from services.auditors.capitulo_nivel1 import CapituloNivel1Auditor
from services.auditors.capitulo_nivel2 import CapituloNivel2Auditor


class MockEngine:
    def __init__(self, paragraphs):
        self.paragraphs = paragraphs
        self.results = []
        self.stats = {"score": 100, "errors": 0, "warnings": 0, "passed": 0}
        self.anexos_start_idx = -1
        self.last_index_idx = 1  # Simulated index zone from index 0 to 1

    def _add(self, cat, rule, status, msg, expected="", actual="",
             p_idx=None, p_text="", page=None, section=None):
        if status == "error":
            self.stats["errors"] += 1
        elif status == "warning":
            self.stats["warnings"] += 1
        self.results.append({
            "category": cat, "rule": rule, "status": status,
            "actual": actual, "expected": expected,
            "p_idx": p_idx, "p_text": p_text
        })


def _make_paragraph(text, idx=0, **kwargs):
    base = {
        "text": text,
        "norm": text.upper(),
        "index": idx,
        "estimated_page": 1,
        "section": "General",
        "is_cover": False,
        "in_table": False,
        "is_in_body": True,
        "body_level": 1,
        "level": 1,
        "is_heading": False,
        "indent_left": 0.0,
        "indent_first": 0.0,
        "indent_hanging": 0.0,
        "alignment": "left",
        "line_spacing": 2.0,
        "spacing_before": 0,
        "spacing_after": 0,
        "runs": [{"text": text, "bold": True, "italic": False, "size": 12, "font": "Times New Roman"}],
        "list_fmt": None,
        "list_lvl_text": "",
        "style_id": "Normal",
    }
    base.update(kwargs)
    return base


def test_capitulo_nivel1_skips_index_entries():
    """CapituloNivel1Auditor must ignore paragraphs that belong to TOC or have index features."""
    # Index paragraph (TOC style, dots or page number pattern, or inside index zone)
    p_index_1 = _make_paragraph("CAPITULO II. MARCO TEORICO ...................... 27", idx=0, is_in_body=False, body_level=0, section="INDICE GENERAL")
    p_index_2 = _make_paragraph("CAPITULO II", idx=1, is_in_body=False, body_level=0, section="INDICE GENERAL", indent_left=1.25)
    
    # Real body paragraph (centered, bold, size 16pt, no indent)
    p_body = _make_paragraph(
        "CAPÍTULO II", idx=2, is_in_body=True, body_level=1, section="CAPITULO II",
        alignment="center", spacing_before=0, spacing_after=5.0, style_id="Heading 1",
        runs=[{"text": "CAPÍTULO II", "bold": True, "size": 16}]
    )

    auditor = CapituloNivel1Auditor.__new__(CapituloNivel1Auditor)
    auditor.engine = MockEngine([p_index_1, p_index_2, p_body])
    auditor.audit()

    # The index paragraphs must not generate errors like "Tilde en Capítulo" or "Sangría Capítulo"
    # The real body paragraph is perfectly compliant, so it should not generate any errors either.
    assert len(auditor.engine.results) == 0


def test_capitulo_nivel1_flags_malformed_body_capitulo():
    """CapituloNivel1Auditor must flag standard formatting errors on real body chapters."""
    # Real body paragraph, but lacks tilde, has indentation, not bold, size is 12pt
    p_body = _make_paragraph(
        "CAPITULO II", idx=2, is_in_body=True, body_level=1, section="CAPITULO II",
        alignment="left", indent_left=1.25, spacing_before=6.0, spacing_after=6.0,
        runs=[{"text": "CAPITULO II", "bold": False, "size": 12}]
    )

    auditor = CapituloNivel1Auditor.__new__(CapituloNivel1Auditor)
    # last_index_idx is 1, so p_body must be at index 2 or higher in paragraphs list
    p_dummy1 = _make_paragraph("dummy1", idx=0, is_in_body=False, body_level=0)
    p_dummy2 = _make_paragraph("dummy2", idx=1, is_in_body=False, body_level=0)
    auditor.engine = MockEngine([p_dummy1, p_dummy2, p_body])
    auditor.engine.last_index_idx = 1
    auditor.audit()

    errors = [r["rule"] for r in auditor.engine.results]
    assert any("Tilde en Capítulo" in e for e in errors)
    assert any("Sangría Capítulo" in e for e in errors)
    assert any("Alineación Capítulo" in e for e in errors)
    assert any("Estilo Capítulo" in e for e in errors)


def test_ortografia_skips_index_zone():
    """OrtografiaAuditor must skip index zone and non-body paragraphs entirely."""
    from services.auditors.ortografia import OrtografiaAuditor
    # An index line with a spelling/typo issue like "INVESTIGACIÓN27"
    p_index = _make_paragraph(
        "Esta es la INVESTIGACIÓN27 sobre el tema de tesis", idx=0,
        is_in_body=False, body_level=0, section="INDICE GENERAL"
    )
    # A body line with the same spelling/typo issue
    p_body = _make_paragraph(
        "Esta es la INVESTIGACIÓN27 sobre el tema de tesis", idx=2,
        is_in_body=True, body_level=1, section="MARCO TEORICO"
    )

    auditor = OrtografiaAuditor.__new__(OrtografiaAuditor)
    auditor.engine = MockEngine([p_index, p_body])
    auditor.engine.last_index_idx = 0
    auditor.audit()

    # The result should contain the warning for p_body at idx 2, but not for p_index at idx 0
    typos = [r for r in auditor.engine.results if "INVESTIGACIÓN27" in r["rule"] or "INVESTIGACIÓN27" in r.get("p_text", "")]
    assert len(typos) == 1
    assert typos[0]["p_idx"] == 2


def test_abstract_word_count_only_max_300():
    """AbstractAuditor must only enforce maximum 300 words, no minimum 250 words."""
    from services.auditors.abstract import AbstractAuditor
    # Under 250 words (e.g. 243 words) should PASS
    text_under_250 = "word " * 243
    p_title = _make_paragraph("ABSTRACT", idx=0)
    p_content = _make_paragraph(text_under_250, idx=1)
    p_keywords = _make_paragraph("Keywords: test", idx=2)

    auditor = AbstractAuditor.__new__(AbstractAuditor)
    auditor.engine = MockEngine([p_title, p_content, p_keywords])
    auditor.engine.last_index_idx = -1
    auditor.audit()

    # Verify that "Extensión del Abstract" passed
    results = auditor.engine.results
    abstract_ext_result = [r for r in results if r["rule"] == "Extensión del Abstract"]
    assert len(abstract_ext_result) == 1
    assert abstract_ext_result[0]["status"] == "passed"

    # Over 300 words (e.g. 305 words) should FAIL
    text_over_300 = "word " * 305
    p_content_over = _make_paragraph(text_over_300, idx=1)
    auditor_over = AbstractAuditor.__new__(AbstractAuditor)
    auditor_over.engine = MockEngine([p_title, p_content_over, p_keywords])
    auditor_over.engine.last_index_idx = -1
    auditor_over.audit()

    results_over = auditor_over.engine.results
    abstract_ext_result_over = [r for r in results_over if r["rule"] == "Extensión del Abstract"]
    assert len(abstract_ext_result_over) == 1
    assert abstract_ext_result_over[0]["status"] == "error"


