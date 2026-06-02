import pytest
from services.auditors.secuencia_tabla_figura import SecuenciaTablaFiguraAuditor
from services.auditors.tablas import TablasAuditor
from services.auditors.figuras import FigurasAuditor

class MockEngine:
    def __init__(self, paragraphs, tables_info=None):
        self.paragraphs = paragraphs
        self.tables_info = tables_info or {}
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
            "message": msg,
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
        "indent_left": 0.0,
        "indent_hanging": 0.0,
        "alignment": "left",
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


def test_inline_title_without_space_detected_correctly():
    """
    Verifica que si la etiqueta y el título descriptivo están pegados en el mismo párrafo
    (e.g., 'Tabla 1Ubicación y coordenadas...'), el validador de secuencia lo identifique como
    'title_in_same_para' y NO intente usar la primera celda de la tabla como título descriptivo.
    """
    auditor = SecuenciaTablaFiguraAuditor.__new__(SecuenciaTablaFiguraAuditor)
    
    # Párrafo 0: Etiqueta y título en el mismo párrafo sin espacio
    runs = [
        {"text": "Tabla ", "bold": True, "italic": False, "size": 12},
        {"text": "1", "bold": True, "italic": False, "size": 12},
        {"text": "Ubicación y coordenadas...", "bold": False, "italic": True, "size": 12}
    ]
    p0 = _make_paragraph("Tabla 1Ubicación y coordenadas...", idx=0, runs=runs)
    
    # Párrafo 1: Primera celda de la tabla (in_table = True)
    p1 = _make_paragraph("CÓDIGO DE MUESTRA", idx=1, in_table=True)
    
    # Párrafo 2: Nota/Fuente
    p2 = _make_paragraph("Nota: Elaboración propia.", idx=2)
    
    auditor.engine = MockEngine([p0, p1, p2])
    auditor.audit()
    
    # No debería haber errores de "Título descriptivo sin cursiva" que contengan "CÓDIGO DE MUESTRA"
    for r in auditor.engine.results:
        if r["rule"].startswith("Título descriptivo sin cursiva"):
            assert "CÓDIGO" not in r["message"], f"Error: identificó incorrectamente la celda de la tabla como el título: {r['message']}"


def test_table_split_page_header_repetition():
    """
    Verifica que se valide correctamente si una tabla dividida repite su encabezado.
    """
    # Caso 1: crosses_pages = True y first_row_has_header = False (Debe reportar error)
    auditor = TablasAuditor.__new__(TablasAuditor)
    
    p0 = _make_paragraph("Tabla en pág. 1", idx=0, in_table=True, tbl_id=123)
    
    tables_info = {
        123: {
            "jc": "left",
            "row_count": 20,
            "first_row_has_header": False,
            "header_row_count": 1,
            "explicit_header_rows": [],
            "has_merged_cells": False,
            "crosses_pages": True,
            "first_cell_text": "Celdas",
        }
    }
    
    auditor.engine = MockEngine([p0], tables_info=tables_info)
    auditor._audit_table_alignment_and_split()
    
    errors = [r for r in auditor.engine.results if r["status"] == "error"]
    assert len(errors) == 1
    assert "Encabezado Repetido (Tabla dividida)" in errors[0]["rule"]
    
    # Caso 2: crosses_pages = True y first_row_has_header = True (Debe pasar/no reportar error)
    auditor2 = TablasAuditor.__new__(TablasAuditor)
    tables_info2 = {
        123: {
            "jc": "left",
            "row_count": 20,
            "first_row_has_header": True,
            "header_row_count": 1,
            "explicit_header_rows": [0],
            "has_merged_cells": False,
            "crosses_pages": True,
            "first_cell_text": "Celdas",
        }
    }
    auditor2.engine = MockEngine([p0], tables_info=tables_info2)
    auditor2._audit_table_alignment_and_split()
    
    errors2 = [r for r in auditor2.engine.results if r["status"] == "error"]
    assert len(errors2) == 0


# ═══════════════════════════════════════════════════════════════════════
# Componente 9: Tests de reconocimiento de título descriptivo faltante
# ═══════════════════════════════════════════════════════════════════════

def test_tablas_missing_title_when_table_cell_follows():
    """
    Cuando la etiqueta 'Tabla 1' es seguida directamente por un párrafo que
    está dentro de la tabla (in_table=True), el auditor debe reportar
    'título faltante' y NO intentar validar el estilo de la celda.
    """
    auditor = TablasAuditor.__new__(TablasAuditor)

    p0 = _make_paragraph("Tabla 1", idx=0,
                         runs=[{"text": "Tabla 1", "bold": True, "italic": False, "size": 12}])
    p1 = _make_paragraph("CÓDIGO DE MUESTRA", idx=1, in_table=True, tbl_id=99)
    p2 = _make_paragraph("Nota: Elaboración propia.", idx=2,
                         runs=[{"text": "Nota:", "bold": False, "italic": True, "size": 10},
                               {"text": " Elaboración propia.", "bold": False, "italic": True, "size": 10}],
                         spacing_after=15, line_spacing=1.5)

    auditor.engine = MockEngine([p0, p1, p2])
    auditor._audit_table_labels_and_titles()

    # Debe haber un error de secuencia por "título faltante"
    missing = [r for r in auditor.engine.results
               if "Secuencia" in r["rule"] or "Falta" in r["message"]]
    assert len(missing) >= 1, "Debería detectar título descriptivo faltante"

    # NO debe haber error de estilo sobre "CÓDIGO DE MUESTRA"
    style_errors = [r for r in auditor.engine.results
                    if "Estilo Título" in r["rule"] and "CÓDIGO" in r.get("message", "")]
    assert len(style_errors) == 0, "No debe auditar estilo de una celda de tabla como título"


def test_tablas_blank_lines_between_label_and_title():
    """
    Cuando hay párrafos vacíos (líneas en blanco) entre la etiqueta y el
    título descriptivo real, el auditor debe saltar los vacíos y encontrar
    el título correctamente.
    """
    auditor = TablasAuditor.__new__(TablasAuditor)

    p0 = _make_paragraph("Tabla 2", idx=0,
                         runs=[{"text": "Tabla 2", "bold": True, "italic": False, "size": 12}])
    p1 = _make_paragraph("", idx=1)  # línea en blanco
    p2 = _make_paragraph("Ubicación y coordenadas del área de estudio", idx=2,
                         runs=[{"text": "Ubicación y coordenadas del área de estudio",
                                "bold": False, "italic": True, "size": 12}])
    p3 = _make_paragraph("Datos de la tabla", idx=3, in_table=True, tbl_id=100)
    p4 = _make_paragraph("Fuente: Elaboración propia.", idx=4,
                         runs=[{"text": "Fuente:", "bold": False, "italic": True, "size": 10},
                               {"text": " Elaboración propia.", "bold": False, "italic": True, "size": 10}],
                         spacing_after=15, line_spacing=1.5)

    auditor.engine = MockEngine([p0, p1, p2, p3, p4])
    auditor._audit_table_labels_and_titles()

    # NO debe haber error de título faltante
    missing = [r for r in auditor.engine.results
               if "Falta" in r.get("message", "") and "título" in r.get("message", "").lower()]
    assert len(missing) == 0, f"No debería detectar título faltante cuando el título real existe: {missing}"


def test_secuencia_missing_title_when_table_follows():
    """
    El auditor de secuencia debe detectar 'Falta título descriptivo' cuando
    el párrafo siguiente a la etiqueta es una celda de tabla (in_table=True).
    """
    auditor = SecuenciaTablaFiguraAuditor.__new__(SecuenciaTablaFiguraAuditor)

    p0 = _make_paragraph("Tabla 1", idx=0,
                         runs=[{"text": "Tabla 1", "bold": True, "italic": False, "size": 12}])
    p1 = _make_paragraph("CÓDIGO DE MUESTRA", idx=1, in_table=True)
    p2 = _make_paragraph("Nota: Elaboración propia.", idx=2)

    auditor.engine = MockEngine([p0, p1, p2])
    auditor.audit()

    missing = [r for r in auditor.engine.results
               if "Falta título descriptivo" in r["rule"]]
    assert len(missing) == 1, f"Debe reportar 1 error de título faltante, encontrados: {len(missing)}"


def test_figuras_missing_title_when_drawing_follows():
    """
    El auditor de figuras debe detectar título faltante cuando el párrafo
    siguiente a la etiqueta 'Figura 1' contiene un dibujo/imagen.
    """
    auditor = FigurasAuditor.__new__(FigurasAuditor)

    p0 = _make_paragraph("Figura 1", idx=0,
                         runs=[{"text": "Figura 1", "bold": True, "italic": False, "size": 12}])
    # Párrafo con un drawing grande (la imagen de la figura)
    p1 = _make_paragraph("", idx=1,
                         drawings=[{"width": 10.0, "height": 8.0}])
    p2 = _make_paragraph("Fuente: Elaboración propia.", idx=2,
                         runs=[{"text": "Fuente:", "bold": False, "italic": True, "size": 10},
                               {"text": " Elaboración propia.", "bold": False, "italic": True, "size": 10}],
                         spacing_after=15, line_spacing=1.5)

    auditor.engine = MockEngine([p0, p1, p2])
    auditor._audit_figure_labels_and_titles()

    missing = [r for r in auditor.engine.results
               if "Secuencia" in r["rule"] and "falta" in r.get("message", "").lower()]
    assert len(missing) >= 1, "Debe detectar título faltante cuando la imagen sigue a la etiqueta directamente"

    # NO debe reportar errores de estilo sobre un párrafo vacío/dibujo
    style = [r for r in auditor.engine.results if "Estilo Título" in r["rule"]]
    assert len(style) == 0, "No debe auditar estilo de un dibujo como si fuera el título"

