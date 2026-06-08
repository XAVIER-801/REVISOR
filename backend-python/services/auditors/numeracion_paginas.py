"""
numeracion_paginas.py - Auditoría de NUMERACIÓN DE PÁGINAS.

Reglas de la Guía UNAP:
1. La numeración se cuenta desde la primera página (portada = página 1).
2. Las páginas preliminares (portada → acrónimos) existen pero NO muestran
   número visible.
3. A partir del RESUMEN, el número de página es VISIBLE, CENTRADO y SIN NEGRITA
   en el pie de página.
4. Los números de página listados en el ÍNDICE GENERAL deben coincidir con
   la página real donde se encuentra cada título/sección.
"""
import zipfile
import re
from lxml import etree
from utils.style_resolver import ALIGN_MAP
from .base_auditor import BaseAuditor


NSMAP = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}


class NumeracionPaginasAuditor(BaseAuditor):

    def audit(self):
        docx_path = self.engine.working_path
        try:
            with zipfile.ZipFile(docx_path, 'r') as z:
                self._audit_footer_structure(z)
                self._audit_footer_format(z)
        except Exception as e:
            self._add(
                "Numeración de Páginas", "Error en análisis", "warning",
                f"No se pudo analizar la numeración de páginas: {e}",
                "Análisis exitoso", "Error",
            )

        self._cross_reference_index_pages()

    # ─── 1. ESTRUCTURA DE PIES DE PÁGINA ─────────────────────────────────

    def _audit_footer_structure(self, z):
        """Verifica que existan footers y que la configuración evite números
        visibles en páginas preliminares."""
        footers = [n for n in z.namelist()
                   if n.startswith('word/footer') and n.endswith('.xml')]
        if not footers:
            self._add(
                "Numeración de Páginas", "Sin pies de página", "error",
                "No se detectaron pies de página. La Guía UNAP requiere "
                "número centado visible desde el Resumen.",
                "Footer con número centrado", "Sin footer",
            )
            return False

        # Detectar campo PAGE en footers
        footers_with_page = []
        for fpath in footers:
            try:
                f_xml = etree.fromstring(z.read(fpath))
                has_page = False
                for inst in f_xml.iter(f'{{{NSMAP["w"]}}}instrText'):
                    if inst.text and 'PAGE' in inst.text.upper():
                        has_page = True
                        break
                for fld in f_xml.iter(f'{{{NSMAP["w"]}}}fldSimple'):
                    instr = fld.get(f'{{{NSMAP["w"]}}}instr', '')
                    if 'PAGE' in instr.upper():
                        has_page = True
                        break
                if has_page:
                    footers_with_page.append(fpath)
            except Exception:
                pass

        if not footers_with_page:
            self._add(
                "Numeración de Páginas", "Sin campo PAGE", "error",
                "Ningún pie de página contiene el campo de número de página "
                "(PAGE). Inserte número de página: Insertar → Núm. de página "
                "→ Parte inferior → Centrado.",
                "Campo PAGE en footer", "Ausente",
            )
            return False

        # Analizar secciones
        doc_xml = etree.fromstring(z.read('word/document.xml'))
        sect_prs = doc_xml.findall('.//w:sectPr', NSMAP)

        sections_info = []
        for s_idx, sect in enumerate(sect_prs):
            footer_refs = sect.findall('w:footerReference', NSMAP)
            title_pg = sect.find('w:titlePg', NSMAP)
            sections_info.append({
                "index": s_idx,
                "has_title_pg": title_pg is not None,
                "footer_refs": [
                    (ref.get(f'{{{NSMAP["w"]}}}type') or 'default',
                     ref.get(f'{{{NSMAP["r"]}}}id'))
                    for ref in footer_refs
                ],
            })

        # Si hay UNA sección y tiene número → error (visible desde portada)
        if len(sections_info) == 1 and footers_with_page:
            section = sections_info[0]
            footer_types = [t for t, _ in section["footer_refs"]]
            has_first_footer = 'first' in footer_types
            if not section["has_title_pg"] and not has_first_footer:
                self._add(
                    "Numeración de Páginas", "Número visible en preliminares",
                    "error",
                    "La numeración se muestra en TODAS las páginas incluyendo "
                    "preliminares. SOLUCIÓN: divida en secciones (después de "
                    "acrónimos) y quite el número del footer de la 1ra sección.",
                    "Visible solo desde Resumen", "Visible en todas",
                )
                return False

        self._add(
            "Numeración de Páginas", "Configuración de secciones", "passed",
            "La estructura de secciones permite ocultar el número en "
            "páginas preliminares.",
            f"{len(sections_info)} sección(es)",
            f"{len(footers_with_page)} footer(es) con número",
        )
        return True

    # ─── 2. FORMATO DEL NÚMERO EN FOOTER ─────────────────────────────────

    def _audit_footer_format(self, z):
        """Verifica que el número de página esté CENTRADO y SIN NEGRITA
        en los footers que contienen el campo PAGE."""
        footers = [n for n in z.namelist()
                   if n.startswith('word/footer') and n.endswith('.xml')]

        for fpath in footers:
            try:
                f_xml = etree.fromstring(z.read(fpath))
                # Buscar párrafos que contengan PAGE
                for p in f_xml.iter(f'{{{NSMAP["w"]}}}p'):
                    has_page = False
                    for inst in p.iter(f'{{{NSMAP["w"]}}}instrText'):
                        if inst.text and 'PAGE' in inst.text.upper():
                            has_page = True
                            break
                    for fld in p.iter(f'{{{NSMAP["w"]}}}fldSimple'):
                        instr = fld.get(f'{{{NSMAP["w"]}}}instr', '')
                        if 'PAGE' in instr.upper():
                            has_page = True
                            break
                    if not has_page:
                        continue

                    # Alineación (usar ALIGN_MAP para normalizar, igual que el resto del sistema)
                    ppr = p.find('w:pPr', NSMAP)
                    align = 'left'
                    if ppr is not None:
                        jc = ppr.find('w:jc', NSMAP)
                        if jc is not None:
                            raw = (jc.get(f'{{{NSMAP["w"]}}}val') or 'left').lower().strip()
                            align = ALIGN_MAP.get(raw, raw)

                    if align != 'center':
                        self._add(
                            "Numeración de Páginas",
                            "Alineación número en footer",
                            "error",
                            "El número de página debe estar CENTRADO en el "
                            "pie de página.",
                            "center (Centrado)", self._align_display(align),
                        )

                    # Negrita en runs alrededor del campo PAGE
                    all_normal = True
                    for r in p.iter(f'{{{NSMAP["w"]}}}r'):
                        rpr = r.find('w:rPr', NSMAP)
                        if rpr is not None:
                            b = rpr.find('w:b', NSMAP)
                            if b is not None:
                                b_val = b.get(f'{{{NSMAP["w"]}}}val')
                                if b_val is None or b_val not in ('0', 'false', 'off'):
                                    all_normal = False
                                    break
                    if not all_normal:
                        self._add(
                            "Numeración de Páginas",
                            "Negrita número en footer",
                            "error",
                            "El número de página debe estar SIN NEGRITA en "
                            "el pie de página.",
                            "Sin negrita", "Negrita",
                        )

            except Exception:
                pass

    # ─── 3. VERIFICACIÓN CRUZADA CONTRA EL ÍNDICE ────────────────────────

    @staticmethod
    def _roman_to_int(s):
        s = s.strip().upper()
        vals = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100}
        total = 0
        prev = 0
        for ch in reversed(s):
            cur = vals.get(ch, 0)
            if cur < prev:
                total -= cur
            else:
                total += cur
            prev = cur
        return total

    def _cross_reference_index_pages(self):
        """
        Verifica que los números de página listados en el ÍNDICE GENERAL
        coincidan con la página real donde se encuentra cada título.
        """
        paragraphs = self.engine.paragraphs
        if not paragraphs:
            return

        # Encontrar el rango del índice general
        idx_start, idx_end = self._find_index_range()
        if idx_start == -1:
            return

        mismatches = []
        total_checked = 0

        for i in range(idx_start + 1, idx_end):
            p = paragraphs[i]
            txt = p['text'].strip()
            if not txt or len(txt) < 3:
                continue
            upper = txt.upper()
            if bool(re.match(r'^P[ÁA]G\.?:?$', upper)):
                continue
            if "ÍNDICE GENERAL" in upper or "INDICE GENERAL" in upper:
                continue

            # Saltar secciones preliminares (no llevan número visible en el índice)
            preliminares = [
                'DEDICATORIA', 'AGRADECIMIENTO', 'AGRADECIMIENTOS',
                'ACRÓNIMOS', 'ACRONIMOS',
            ]
            clean_upper = re.sub(r'[\.\s]+', '', upper).strip()
            if clean_upper in preliminares:
                continue

            # Saltar entradas centradas (CAPÍTULO I-IV, INTRODUCCIÓN, etc.)
            # que no llevan número de página visible en el índice
            if '....' not in txt:
                continue

            # Extraer número de página (arábigo o romano, tras relleno de puntos)
            page_match = re.search(r'\.{2,}(\d+|[ivxlcdm]+)\s*$', txt, re.IGNORECASE)
            if not page_match:
                continue
            page_str = page_match.group(1)
            try:
                if re.match(r'^[ivxlcdm]+$', page_str, re.IGNORECASE):
                    idx_page = self._roman_to_int(page_str)
                else:
                    idx_page = int(page_str)
            except ValueError:
                continue

            # Extraer el título (sin el número de página ni relleno)
            title_text = re.sub(r'(?:\.{2,}|\s+)(?:\d+|[ivxlcdm]+)\s*$', '', txt, flags=re.IGNORECASE).strip()
            title_text = re.sub(r'\.{2,}', '', title_text).strip()
            if not title_text:
                continue

            # Buscar el título en el cuerpo del documento (después del índice)
            found_page = self._find_title_page(title_text, idx_end)
            if found_page is not None:
                total_checked += 1
                if found_page != idx_page:
                    mismatches.append((title_text[:30], idx_page, found_page, p))

        if mismatches:
            for title, expected, actual, p in mismatches[:5]:
                self._add(
                    "Numeración de Páginas",
                    f"Página incorrecta en índice: {title}...",
                    "error",
                    f"El índice indica página {expected} para '{title}...' "
                    f"pero el contenido está realmente en la página {actual}.",
                    f"Pág. {actual}", f"Pág. {expected}", p_idx=p['index'], p_text=p['text'],
                )
            if len(mismatches) > 5:
                self._add(
                    "Numeración de Páginas",
                    "Páginas incorrectas adicionales",
                    "warning",
                    f"Hay {len(mismatches) - 5} entradas adicionales con "
                    f"número de página incorrecto en el índice.",
                    "Coinciden", "No coinciden",
                )
        elif total_checked > 0:
            self._add(
                "Numeración de Páginas",
                "Páginas del índice vs contenido",
                "passed",
                f"Todas las {total_checked} entradas del índice general "
                f"coinciden con la página real del contenido.",
                "Coinciden", "Coinciden",
            )

    def _find_index_range(self):
        """Encuentra inicio y fin del ÍNDICE GENERAL."""
        paragraphs = self.engine.paragraphs
        idx_start = idx_end = -1
        section_keywords = [
            'ÍNDICE DE TABLAS', 'INDICE DE TABLAS',
            'ÍNDICE DE FIGURAS', 'INDICE DE FIGURAS',
            'ÍNDICE DE ANEXOS', 'INDICE DE ANEXOS',
            'RESUMEN', 'ABSTRACT',
            'ACRÓNIMOS', 'ACRONIMOS',
            'DEDICATORIA', 'AGRADECIMIENTO', 'AGRADECIMIENTOS',
            'INTRODUCCION', 'INTRODUCCIÓN',
            'CAPITULO', 'CAPÍTULO',
        ]
        for i, p in enumerate(paragraphs):
            txt = p['text'].strip().upper()
            if idx_start == -1:
                if 'ÍNDICE GENERAL' in txt or 'INDICE GENERAL' in txt:
                    if not ('....' in p['text'] or re.search(r'\s+\d+\s*$', p['text'])):
                        idx_start = i
            else:
                if not txt or len(txt) <= 3:
                    continue
                style = p.get('style_id', '')
                if style and style.upper().startswith('TDC'):
                    continue
                if any(k in txt for k in section_keywords):
                    align = p.get('alignment', 'left')
                    size = p['runs'][0].get('size', 0) if p.get('runs') else 0
                    filler = '....' in p['text']
                    page_num = bool(re.search(r'\s+\d+\s*$', p['text']))
                    is_heading = style and ('Heading' in style or 'titulo' in style.lower())
                    looks_like_title = align == 'center' and size >= 14 and not filler and not page_num
                    if is_heading or looks_like_title:
                        idx_end = i
                        break
        if idx_start == -1:
            return -1, -1
        if idx_end == -1:
            idx_end = min(idx_start + 300, len(paragraphs))
        return idx_start, idx_end

    def _find_title_page(self, title, idx_end):
        """
        Busca un título en los párrafos del cuerpo (después del índice)
        y retorna su página estimada. idx_end es el fin del rango del índice.
        """
        paragraphs = self.engine.paragraphs
        norm_title = self._norm(title)

        # Primero buscar por texto normalizado exacto (solo en cuerpo, después del índice)
        for i in range(len(paragraphs) - 1, idx_end, -1):
            p = paragraphs[i]
            if self._norm(p['text'].strip()) == norm_title:
                return p.get('estimated_page', 1)

        # Fallback: búsqueda parcial (solo en cuerpo, después del índice)
        for i in range(len(paragraphs) - 1, idx_end, -1):
            p = paragraphs[i]
            p_txt = p['text'].strip()
            if not p_txt:
                continue
            if title.lower() in p_txt.lower() or p_txt.lower() in title.lower():
                return p.get('estimated_page', 1)

        return None

    def _norm(self, text):
        text = text.upper()
        text = text.replace('Í', 'I').replace('Ó', 'O').replace('É', 'E')
        text = text.replace('Á', 'A').replace('Ú', 'U').replace('Ñ', 'N')
        text = re.sub(r'[^A-Z0-9\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text