"""
word_engine.py - Motor principal de auditoría de tesis.

Este archivo es el ORQUESTADOR que:
1. Extrae los datos del documento Word (.docx)
2. Delega cada aspecto de la auditoría a un módulo especializado en services/auditors/
3. Consolida y devuelve los resultados

Módulos de auditoría (en services/auditors/):
- portada.py              → Portada (primera página)
- indice_general.py       → Índice General (tabla de contenidos)
- indice_tablas_figuras.py → Índices de Tablas, Figuras y Anexos
- tablas_figuras.py       → Tablas y Figuras en el cuerpo
- titulos_nivel1.py       → Títulos de Nivel 1 (Capítulos, secciones principales)
- titulos_nivel2345.py    → Títulos de Nivel 2, 3, 4 y 5
- vinetas.py              → Viñetas (todo el documento)
- contenido_parrafos.py   → Párrafos de contenido
- configuracion_pagina.py → Configuración de página y márgenes
- resumen_abstract.py     → Resumen, Abstract y Agradecimientos
- anexos.py               → Sección de Anexos
- estilo_escritura.py     → Estilo de escritura y hábitos de formato
"""
from docx import Document
import os
import re
import unicodedata
import zipfile
from lxml import etree
from utils.style_resolver import StyleResolver, parse_rpr, parse_ppr, NSMAP
from utils.converter import DocConverter
from services.linguistic_analyzer import LinguisticAnalyzer

# Importar todos los auditores modulares
from services.auditors.portada import PortadaAuditor
from services.auditors.indice_general import IndiceGeneralAuditor
from services.auditors.indice_tablas_figuras import IndiceTablasFigurasAuditor
from services.auditors.tablas_figuras import TablasFigurasAuditor
from services.auditors.capitulo_nivel1 import CapituloNivel1Auditor
from services.auditors.capitulo_nivel2 import CapituloNivel2Auditor
from services.auditors.capitulo_nivel345 import CapituloNivel345Auditor
from services.auditors.vinetas import VinetasAuditor
from services.auditors.configuracion_pagina import ConfiguracionPaginaAuditor
from services.auditors.resumen_abstract import ResumenAbstractAuditor
from services.auditors.anexos import AnexosAuditor
from services.auditors.estilo_escritura import EstiloEscrituraAuditor

# Palabras aproximadas por página en formato tesis
_WORDS_PER_PAGE = 350


class WordAuditEngine:
    def __init__(self, file_path):
        self.original_path = file_path
        self.working_path = file_path
        self.stats = {"score": 100, "errors": 0, "warnings": 0, "passed": 0}
        self.results = []
        self.paragraphs = []
        self.sections_found = set()
        self.linguistic = LinguisticAnalyzer()
        # Contexto de posición
        self._current_section = "Inicio del Documento"
        self._word_count_accum = 0
        self.anexos_start_idx = -1

    def run_audit(self):
        try:
            output_dir = os.path.dirname(self.original_path)
            self.working_path = DocConverter.standardize_to_docx(self.original_path, output_dir)
            self.document = Document(self.working_path)
            self.resolver = StyleResolver(self.working_path)
            self._extract_data()

            # ── Ejecutar cada auditor modular ──────────────────────────
            PortadaAuditor(self).audit()              # 📄 Portada
            IndiceGeneralAuditor(self).audit()         # 🗂️ Índice General
            IndiceTablasFigurasAuditor(self).audit()   # 🗂️ Índice Tablas/Figuras
            ResumenAbstractAuditor(self).audit()       # 📋 Resumen/Abstract
            TablasFigurasAuditor(self).audit()         # 📊 Tablas y Figuras
            CapituloNivel1Auditor(self).audit()        # 📌 Nivel 1: Títulos + Contenido
            CapituloNivel2Auditor(self).audit()        # 📌 Nivel 2: Títulos + Contenido
            CapituloNivel345Auditor(self).audit()      # 📌 Nivel 3-5: Títulos + Contenido
            VinetasAuditor(self).audit()               # 🔹 Viñetas (todos los niveles)
            ConfiguracionPaginaAuditor(self).audit()   # ⚙️ Configuración de página
            EstiloEscrituraAuditor(self).audit()       # ✍️ Estilo de escritura
            AnexosAuditor(self).audit()                # 📎 Anexos

            return self._finalize()
        except Exception as e:
            self._add("Sistema", "Error Crítico", "error", str(e))
            return self._finalize()

    # ══════════════════════════════════════════════════════════════════════
    # EXTRACCIÓN DE DATOS DEL DOCUMENTO
    # ══════════════════════════════════════════════════════════════════════

    def _extract_data(self):
        with zipfile.ZipFile(self.working_path, 'r') as z:
            root = etree.fromstring(z.read('word/document.xml'))
        body = root.find('w:body', NSMAP)

        accumulated_words = 0
        current_page = 1
        page_words = 0
        current_section = "Inicio del Documento"
        in_index_zone = False
        # Secciones estructurales que queremos rastrear
        SECTION_KEYWORDS = [
            "DEDICATORIA", "AGRADECIMIENTOS", "INDICE GENERAL", 
            "INDICE DE TABLAS", "INDICE DE FIGURAS", "INDICE DE CUADROS", "INDICE DE ILUSTRACIONES",
            "RESUMEN", "ABSTRACT", "INTRODUCCION", "CONCLUSIONES", "RECOMENDACIONES", 
            "REFERENCIAS BIBLIOGRAFICAS", "ANEXOS", "DECLARACION JURADA", "AUTORIZACION PARA EL DEPOSITO"
        ]
        
        table_eq_cache = {}

        for idx, p_el in enumerate(body.iter(f'{{{NSMAP["w"]}}}p')):
            ppr_el = p_el.find('w:pPr', NSMAP)
            explicit_ppr = parse_ppr(ppr_el)
            style_id = explicit_ppr.get('style_id', 'Normal')
            res_ppr, _ = self.resolver.resolve(style_id, explicit_ppr)

            # Detectar salto de página explícito en el XML
            has_page_break = bool(
                p_el.find('.//w:br[@w:type="page"]', NSMAP) or
                p_el.find('.//w:lastRenderedPageBreak', NSMAP)
            )

            # Detectar dibujos/imagenes en el párrafo
            drawings = []
            for ext_el in p_el.xpath('.//*[local-name()="extent"]'):
                cx = ext_el.get('cx')
                cy = ext_el.get('cy')
                if cx and cy:
                    try:
                        width_cm = round(int(cx) / 360000.0, 2)
                        height_cm = round(int(cy) / 360000.0, 2)
                        drawings.append({
                            "width": width_cm,
                            "height": height_cm
                        })
                    except ValueError:
                        pass

            txt = ""
            runs = []
            for r_el in p_el.findall('.//w:r', NSMAP):
                t = "".join([t.text for t in r_el.findall('w:t', NSMAP) if t.text])
                txt += t
                explicit_rpr = parse_rpr(r_el.find('w:rPr', NSMAP))
                _, res_rpr = self.resolver.resolve(style_id, explicit_ppr, explicit_rpr)
                runs.append({
                    "bold": res_rpr.get('bold', False), 
                    "italic": res_rpr.get('italic', False),
                    "size": res_rpr.get('font_size', 12), 
                    "font": res_rpr.get('font_name', 'Times New Roman'),
                    "text": t
                })

            word_count = len(txt.split()) if txt.strip() else 0
            accumulated_words += word_count

            if has_page_break:
                current_page += 1
                page_words = word_count
            else:
                page_words += word_count
                if page_words >= _WORDS_PER_PAGE:
                    pages_to_add = page_words // _WORDS_PER_PAGE
                    current_page += pages_to_add
                    page_words = page_words % _WORDS_PER_PAGE

            estimated_page = current_page

            # Detectar si este párrafo inicia una sección conocida
            norm_txt = self._norm(txt)
            if norm_txt == "INDICE GENERAL":
                in_index_zone = True

            is_real_resumen_or_abstract = (norm_txt in ["RESUMEN", "ABSTRACT"]) and \
                                           (not "...." in txt) and \
                                           (not bool(re.search(r"\d+$", txt.strip()))) and \
                                           (res_ppr.get('alignment', 'left') == 'center')
            if is_real_resumen_or_abstract:
                in_index_zone = False

            is_index_line = "...." in txt or bool(re.search(r"\d+$", txt.strip()))

            for kw in SECTION_KEYWORDS:
                if norm_txt == kw and not is_index_line:
                    current_section = txt.strip()
                    if kw == "ANEXOS" and self.anexos_start_idx == -1:
                        first_run_size = runs[0].get('size', 0) if runs else 0
                        is_centered = res_ppr.get('alignment', 'left') == 'center'
                        is_bold = any(r.get('bold') for r in runs) if runs else False
                        if 14 <= first_run_size <= 18 and is_centered and is_bold:
                            self.anexos_start_idx = idx
                    break

            if not in_index_zone:
                cap_match = re.match(r"^CAPITULO\s+(I|V|X|L|C|[0-9]+)", norm_txt)
                if cap_match:
                    current_section = txt.strip()
                    self.current_level = 1

            if not hasattr(self, 'current_level'):
                self.current_level = 1

            in_table = False
            is_table_header = False
            w_tbl = f"{{{NSMAP['w']}}}tbl"
            w_tr = f"{{{NSMAP['w']}}}tr"

            tbl = next(p_el.iterancestors(w_tbl), None)
            if tbl is not None:
                tbl_id = id(tbl)
                if tbl_id in table_eq_cache:
                    is_eq = table_eq_cache[tbl_id]
                else:
                    is_eq = False
                    if tbl.xpath('.//*[local-name()="oMath" or local-name()="oMathPara"]'):
                        is_eq = True
                    else:
                        rows_iter = tbl.iter(w_tr)
                        rows = []
                        for _ in range(3):
                            try:
                                rows.append(next(rows_iter))
                            except StopIteration:
                                break
                        if len(rows) <= 2:
                            w_tc = f"{{{NSMAP['w']}}}tc"
                            w_t = f"{{{NSMAP['w']}}}t"
                            for row in rows:
                                cells = list(row.iter(w_tc))
                                if len(cells) <= 3:
                                    for cell in cells:
                                        cell_text = "".join([t.text for t in cell.iter(w_t) if t.text]).strip()
                                        if re.match(r'^\(\s*\d+(\s*\.\s*\d+)*\s*\)$', cell_text):
                                            is_eq = True
                                            break
                                if is_eq:
                                    break
                    table_eq_cache[tbl_id] = is_eq

                if not is_eq:
                    in_table = True
                    p_row = next(p_el.iterancestors(w_tr), None)
                    if p_row is not None:
                        first_row = next(tbl.iter(w_tr), None)
                        if p_row == first_row:
                            is_table_header = True

            # Determinar si es un título (manual o automático de Word)
            is_heading = False
            heading_level = None

            hierarchy_match = re.match(r"^(\d+(?:\.\d+)+)\.?(?:[\s\t]+(.*))?$", txt.strip())
            if hierarchy_match and not in_table:
                is_heading = True
                heading_level = hierarchy_match.group(1).count('.') + 1

            num_pr = ppr_el.find('w:numPr', NSMAP) if ppr_el is not None else None
            is_heading_style = bool(re.search(r'(heading|ttulo|titulo)', style_id, re.IGNORECASE))

            if is_heading_style and not in_table:
                is_heading = True
                if num_pr is not None:
                    ilvl_el = num_pr.find('w:ilvl', NSMAP)
                    if ilvl_el is not None:
                        heading_level = int(ilvl_el.get(f'{{{NSMAP["w"]}}}val')) + 1

                if heading_level is None:
                    m_style = re.search(r'(heading|ttulo|titulo)\s*(\d+)', style_id, re.IGNORECASE)
                    if m_style:
                        style_num = int(m_style.group(2))
                        if style_num == 1:
                            dec_match = re.match(r'^(\d+(?:\.\d+)+)', txt.strip())
                            if dec_match and dec_match.group(1).count('.') >= 1:
                                heading_level = 2
                            else:
                                heading_level = 1
                        elif style_num == 2:
                            heading_level = 2
                        elif style_num == 3:
                            heading_level = 3
                        elif style_num == 4:
                            heading_level = 4
                        elif style_num == 5:
                            heading_level = 5
                        else:
                            heading_level = style_num

            if not is_heading and num_pr is not None and not in_table:
                ilvl_el = num_pr.find('w:ilvl', NSMAP)
                if ilvl_el is not None:
                    ilvl_val = int(ilvl_el.get(f'{{{NSMAP["w"]}}}val'))
                    inferred_level = ilvl_val + 1
                    if len(txt.strip()) < 200 and inferred_level >= 2:
                        is_heading = True
                        if heading_level is None:
                            heading_level = inferred_level

            if is_heading and heading_level is not None:
                self.current_level = heading_level

            self.paragraphs.append({
                "text": txt,
                "norm": norm_txt,
                "alignment": res_ppr.get('alignment', 'left'),
                "line_spacing": res_ppr.get('line_spacing'),
                "indent_first": res_ppr.get('indent_first'),
                "spacing_after": res_ppr.get('spacing_after', 0),
                "spacing_before": res_ppr.get('spacing_before', 0),
                "runs": runs,
                "index": idx,
                "estimated_page": estimated_page,
                "section": current_section,
                "has_page_break": has_page_break,
                "style_id": style_id,
                "in_table": in_table,
                "is_table_header": is_table_header,
                "level": self.current_level,
                "is_heading": is_heading,
                "indent_left": res_ppr.get('indent_left'),
                "indent_hanging": res_ppr.get('indent_hanging'),
                "drawings": drawings
            })

        # Identificar la portada (primera página)
        in_cover = True
        for idx, p in enumerate(self.paragraphs):
            txt = p["text"].strip()
            norm = p["norm"]

            if not in_cover:
                p["is_cover"] = False
                continue

            if norm in ["DEDICATORIA", "AGRADECIMIENTOS", "INDICE GENERAL", "RESUMEN", "ABSTRACT", "INTRODUCCION"]:
                in_cover = False
                p["is_cover"] = False
                continue

            p["is_cover"] = in_cover

            if p.get("has_page_break") or p.get("estimated_page", 1) > 1:
                in_cover = False

        # Encontrar el final del bloque de índices
        self.last_index_idx = -1
        self.index_start_idx = -1
        for idx, p_data in enumerate(self.paragraphs):
            norm_txt = p_data["norm"]
            if "INDICE GENERAL" in norm_txt or "ÍNDICE GENERAL" in norm_txt:
                self.index_start_idx = idx
                break

        if self.index_start_idx != -1:
            for idx in range(self.index_start_idx + 1, len(self.paragraphs)):
                p_data = self.paragraphs[idx]
                txt = p_data["text"].strip()
                norm_txt = p_data["norm"]
                style = p_data.get("style_id", "")
                is_tdc = style.upper().startswith("TOC") or style.upper().startswith("TDC") if style else False
                is_idx_line = "...." in txt or bool(re.search(r"\d+$", txt)) or is_tdc
                if is_idx_line:
                    self.last_index_idx = idx
                else:
                    is_major_section = norm_txt in [
                        "INDICE DE TABLAS", "INDICE DE FIGURAS", "INDICE DE CUADROS", "INDICE DE ILUSTRACIONES",
                        "RESUMEN", "ABSTRACT", "INTRODUCCION"
                    ] or "CAPITULO" in norm_txt
                    if is_major_section:
                        break

        # ── Pre-computar body_level y is_in_body para cada párrafo ──
        # Esto permite que los auditores por nivel filtren sin duplicar lógica de rastreo
        current_body_level = 1
        in_body = False
        for i, p in enumerate(self.paragraphs):
            txt = p["text"].strip()
            norm = p["norm"]

            # Determinar si estamos en el cuerpo del documento
            if self.last_index_idx != -1 and i <= self.last_index_idx:
                p["is_in_body"] = False
                p["body_level"] = 0
                continue

            is_index_line = "...." in txt or bool(re.search(r"\d+$", txt))
            if not is_index_line and ("CAPITULO" in norm or "INTRODUCCION" in norm):
                in_body = True
                current_body_level = 1

            if not in_body or p.get('in_table') or (self.anexos_start_idx != -1 and i >= self.anexos_start_idx):
                p["is_in_body"] = False
                p["body_level"] = 0
                continue

            p["is_in_body"] = True

            # Detectar viñetas
            is_bullet = bool(txt) and (txt[0] in '-\u2022*•' or (len(txt) >= 1 and txt[0] == ''))
            p["is_bullet"] = is_bullet

            # Actualizar nivel basado en títulos
            is_capitulo = bool(re.match(r"^CAP[ÍI]TULO\s+(I|V|X|L|C|[0-9]+)", norm))
            es_seccion_principal = any(k in norm for k in [
                "INTRODUCCION", "MARCO TEORICO", "METODOLOGIA",
                "MATERIALES Y METODOS", "RESULTADOS Y DISCUSION",
                "CONCLUSIONES", "RECOMENDACIONES", "REFERENCIAS BIBLIOGRAFICAS"
            ]) and (p.get('style_id', '').upper().startswith('HEADING') or txt.isupper())

            numbering_match = re.match(r'^(\d+(?:\.\d+)+)\.?(?:[\s\t]+|$)', txt)
            if numbering_match:
                current_body_level = numbering_match.group(1).count('.') + 1
            elif is_capitulo or es_seccion_principal:
                current_body_level = 1
            elif p.get('is_heading') and p.get('level'):
                current_body_level = p['level']

            p["body_level"] = current_body_level

        # Registrar secciones encontradas
        for p in self.paragraphs:
            norm = p["norm"]
            for kw in SECTION_KEYWORDS:
                if norm == kw:
                    self.sections_found.add(norm)
                    break
            if re.match(r"^CAPITULO\s+(I|V|X|L|C|[0-9]+)", norm):
                self.sections_found.add("CAPITULO")

    # ══════════════════════════════════════════════════════════════════════
    # UTILIDADES COMPARTIDAS
    # ══════════════════════════════════════════════════════════════════════

    def _norm(self, t):
        if not t: return ""
        return unicodedata.normalize('NFD', t).encode('ascii', 'ignore').decode('ascii').upper().strip()

    def _norm_alphanumeric(self, t):
        n = self._norm(t)
        return re.sub(r'[^A-Z0-9]', '', n)

    def _add(self, cat, rule, status, msg, expected="", actual="", p_idx=None, p_text="", page=None, section=None):
        if status == "error": self.stats["errors"] += 1
        elif status == "warning": self.stats["warnings"] += 1
        if p_idx is not None and p_idx < len(self.paragraphs):
            p_data = self.paragraphs[p_idx]
            if page is None:
                page = p_data.get("estimated_page")
            if section is None:
                section = p_data.get("section")
        self.results.append({
            "category": cat, "rule": rule, "status": status, "message": msg, 
            "expected": str(expected), "actual": str(actual),
            "paragraphIndex": p_idx, "paragraphText": p_text,
            "page": page,
            "section": section or "General",
        })

    def _get_p_props(self, p):
        if not p["runs"]: return 12, False, False, "Times New Roman"
        for r in p["runs"]:
            if r["text"].strip():
                return r["size"], r["bold"], r["italic"], r["font"]
        return 12, False, False, "Times New Roman"

    def _finalize(self):
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "passed")
        self.stats.update({"passed": passed, "score": max(0, round((passed/total)*100)) if total > 0 else 0})
        return {"stats": self.stats, "results": self.results}
