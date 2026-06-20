"""Tests del auditor de tablas/figuras en Anexos."""
import pytest
from services.auditors.anexos_tablas_figuras import AnexosTablasFigurasAuditor


class MockEngine:
    def __init__(self, paragraphs, anexos_start_idx=0):
        self.paragraphs = paragraphs
        self.anexos_start_idx = anexos_start_idx
        self.results = []
        self.stats = {"score": 100, "errors": 0, "warnings": 0, "passed": 0}
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


def _make_paragraph(text, idx=0, in_table=False, bold=None, italic=None, size=None, **kwargs):
    runs = [{"text": text, "bold": True, "italic": False, "size": 12}]
    if bold is not None or italic is not None or size is not None:
        runs = [{"text": text,
                 "bold": bold if bold is not None else True,
                 "italic": italic if italic is not None else False,
                 "size": size if size is not None else 12}]
    base = {
        "text": text,
        "norm": text.upper(),
        "index": idx,
        "estimated_page": 10,
        "section": "ANEXOS",
        "is_cover": False,
        "in_table": in_table,
        "is_in_body": False,
        "body_level": 0,
        "level": 1,
        "is_heading": False,
        "indent_left": 0.0,
        "indent_hanging": 0.0,
        "indent_first": 0.0,
        "alignment": "left",
        "line_spacing": 2.0,
        "spacing_before": 0,
        "spacing_after": 0,
        "runs": runs,
        "list_fmt": None,
        "list_lvl_text": "",
        "style_id": "Normal",
        "tbl_id": None,
        "is_table_header": False,
        "row_index": -1,
    }
    base.update(kwargs)
    return base


def test_skipped_when_no_anexos():
    """Sin sección Anexos, el auditor no debe generar resultados."""
    auditor = AnexosTablasFigurasAuditor.__new__(AnexosTablasFigurasAuditor)
    p = _make_paragraph("- Texto cualquiera", idx=0)
    auditor.engine = MockEngine([p], anexos_start_idx=-1)
    auditor.audit()
    assert len(auditor.engine.results) == 0


def test_skipped_when_no_labels_in_anexos():
    """Sin etiquetas Tabla/Figura en Anexos, no debe auditar."""
    auditor = AnexosTablasFigurasAuditor.__new__(AnexosTablasFigurasAuditor)
    anexos_title = _make_paragraph("ANEXOS", idx=0, alignment="center", bold=True, size=16)
    content = _make_paragraph("- Contenido normal", idx=1)
    auditor.engine = MockEngine([anexos_title, content], anexos_start_idx=0)
    auditor.audit()
    assert len(auditor.engine.results) == 0


def test_detects_table_label_in_anexos():
    """Etiqueta Tabla 1 en Anexos debe auditarse."""
    auditor = AnexosTablasFigurasAuditor.__new__(AnexosTablasFigurasAuditor)
    anexos = _make_paragraph("ANEXOS", idx=0, size=16, alignment="center")
    label = _make_paragraph("Tabla 1", idx=1, bold=True, size=12)
    title = _make_paragraph("Resultados obtenidos", idx=2,
                            runs=[{"text": "Resultados obtenidos", "bold": False, "italic": True, "size": 12}])
    nota = _make_paragraph("Nota: Datos procesados", idx=3,
                           spacing_after=15, line_spacing=1.5,
                           runs=[{"text": "Nota: Datos procesados", "bold": False, "italic": True, "size": 10}])
    auditor.engine = MockEngine([anexos, label, title, nota], anexos_start_idx=0)
    auditor.audit()
    rules = [r["rule"] for r in auditor.engine.results]
    # No debe haber errores si todo está correcto
    errors = [r for r in auditor.engine.results if r["status"] == "error"]
    assert len(errors) == 0, f"Errors: {errors}"


def test_table_label_missing_bold():
    """Etiqueta sin negrita debe reportar error."""
    auditor = AnexosTablasFigurasAuditor.__new__(AnexosTablasFigurasAuditor)
    anexos = _make_paragraph("ANEXOS", idx=0, size=16, alignment="center")
    label = _make_paragraph("Tabla 1", idx=1, bold=False, size=12)
    title = _make_paragraph("Resultados", idx=2,
                            runs=[{"text": "Resultados", "bold": False, "italic": True, "size": 12}])
    nota = _make_paragraph("Nota: Algo", idx=3,
                           spacing_after=15, line_spacing=1.5,
                           runs=[{"text": "Nota: Algo", "bold": False, "italic": True, "size": 10}])
    auditor.engine = MockEngine([anexos, label, title, nota], anexos_start_idx=0)
    auditor.audit()
    assert any("Estilo Etiqueta" in r["rule"] for r in auditor.engine.results)
    # Solo debe tener el error de estilo, no de espaciado
    assert sum(1 for r in auditor.engine.results if r["status"] == "error") == 1


def test_figure_label_in_anexos():
    """Etiqueta Figura 1 en Anexos también debe auditarse."""
    auditor = AnexosTablasFigurasAuditor.__new__(AnexosTablasFigurasAuditor)
    anexos = _make_paragraph("ANEXOS", idx=0, size=16, alignment="center")
    label = _make_paragraph("Figura 1", idx=1, bold=True, size=12)
    title = _make_paragraph("Gráfico de resultados", idx=2,
                            runs=[{"text": "Gráfico de resultados", "bold": False, "italic": True, "size": 12}])
    nota = _make_paragraph("Fuente: Elaboración propia", idx=3,
                           spacing_after=15, line_spacing=1.5,
                           runs=[{"text": "Fuente: Elaboración propia", "bold": False, "italic": True, "size": 10}])
    auditor.engine = MockEngine([anexos, label, title, nota], anexos_start_idx=0)
    auditor.audit()
    errors = [r for r in auditor.engine.results if r["status"] == "error"]
    assert len(errors) == 0, f"Errors: {errors}"
