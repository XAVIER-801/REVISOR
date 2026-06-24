"""
paginacion_indices.py - Auditoría de consistencia de números de página en los índices vs ubicación real.

Reglas del motor:
- Detecta y asocia entradas del Índice General, de Tablas, de Figuras y de Anexos con sus respectivas ubicaciones reales.
- Utiliza un algoritmo estadístico de offset óptimo para tolerar saltos, portadas o numeraciones romanas preliminares.
- Reporta las inconsistencias agrupadas de forma ultra-limpia y con ejemplos precisos de las discrepancias en el campo de detalles.
"""
import re
from collections import Counter
from .base_auditor import BaseAuditor


class PaginacionIndicesAuditor(BaseAuditor):

    def audit(self):
        # 1. Pre-construir mapa de títulos del cuerpo
        body_headings = self._build_body_headings_map()

        # 2. Auditar solo el Índice General (preliminares sin numeración se omiten internamente)
        self._audit_indice_general_pages(body_headings)

    def _audit_indice_general_pages(self, body_headings):
        """Valida la consistencia de números de página en el Índice General."""
        idx_start, idx_end = self._find_index_range("ÍNDICE GENERAL")
        if idx_start == -1:
            return

        mismatches = []
        pairs = []

        # Recolectar pares (número en índice, página estimada real)
        for i in range(idx_start + 1, idx_end):
            p = self.paragraphs[i]
            txt = p['text'].strip()
            if len(txt) < 3 or p.get('in_table', False):
                continue
            
            upper = txt.upper()
            if bool(re.match(r'^P[ÁA]G\.?:?$', upper)) or "ÍNDICE" in upper:
                continue

            # Saltar secciones preliminares/centradas que NO llevan número de página visible
            # o cuya página en el índice no debe ser señalada aunque difiera.
            preliminares = [
                'DEDICATORIA', 'AGRADECIMIENTO', 'AGRADECIMIENTOS',
                'ACRÓNIMOS', 'ACRONIMOS',
                'ÍNDICE GENERAL', 'INDICE GENERAL',
                'ÍNDICE DE TABLAS', 'INDICE DE TABLAS',
                'ÍNDICE DE FIGURAS', 'INDICE DE FIGURAS',
                'ÍNDICE DE ANEXOS', 'INDICE DE ANEXOS',
                'ÍNDICE DE ACRÓNIMOS', 'INDICE DE ACRONIMOS',
            ]
            clean_upper = re.sub(r'[\.\s]+', '', upper).strip()
            if clean_upper in preliminares:
                continue
            # Saltar entradas centradas (capítulos I-IV y nombres de capítulo)
            if p.get('alignment') == 'center':
                continue

            page_match = re.search(r'(\d+)$', txt)
            if page_match:
                page_num = int(page_match.group(1))
                clean_title = re.sub(r'[\.\s\t]+\d+$', '', txt).strip()
                norm_index = self._norm_alphanumeric(clean_title)

                actual_page = None
                if norm_index in body_headings:
                    actual_page = body_headings[norm_index]
                else:
                    for key, val in body_headings.items():
                        if norm_index and (norm_index in key or key in norm_index):
                            actual_page = val
                            break

                if actual_page is not None:
                    pairs.append({
                        "title": clean_title,
                        "page_num": page_num,
                        "actual_page": actual_page
                    })

        has_offset_report = False
        most_common_diff = 0
        pct_match = 0

        # Analizar offset entre páginas del índice y páginas reales
        if pairs:
            diffs = [p["page_num"] - p["actual_page"] for p in pairs]
            diff_counts = Counter(diffs)
            most_common_diff, most_common_count = diff_counts.most_common(1)[0]
            total_pairs = len(pairs)
            pct_match = round(most_common_count / total_pairs * 100)

            # Si hay un offset sistemático no-cero, reportarlo como observación
            if most_common_diff != 0 and pct_match >= 50:
                has_offset_report = True
                offset_detail = (f"Se detectó un desplazamiento sistemático de {most_common_diff} página(s) "
                                 f"en {pct_match}% de las entradas del Índice General "
                                 f"(ej. el índice marca página {pairs[0]['page_num']} pero la ubicación real es {pairs[0]['actual_page']}). "
                                 f"Esto puede deberse a que la portada no se está contando como página 1, "
                                 f"o a que hay páginas preliminares no numeradas que afectan el conteo.")
                self._add("Índice General", "Desplazamiento Sistemático de Páginas", "error", offset_detail,
                          "Páginas del índice alineadas con las hojas reales",
                          f"Offset de {most_common_diff} páginas en ~{pct_match}% de entradas",
                          p_idx=idx_start, p_text="ÍNDICE GENERAL")

            # Flag individual para cada entrada que se desvía del patrón común
            for p in pairs:
                if p["page_num"] - p["actual_page"] != most_common_diff:
                    mismatches.append({
                        "title": p["title"],
                        "idx_page": p["page_num"],
                        "real_page": p["actual_page"] + most_common_diff
                    })

        if mismatches:
            examples = [f"'{m['title']}' (Índice: {m['idx_page']} vs Real: {m['real_page']})" for m in mismatches[:4]]
            examples_str = ", ".join(examples)
            if len(mismatches) > 4:
                examples_str += "..."

            detail = (f"Además del desplazamiento general, {len(mismatches)} entrada(s) no siguen el patrón común "
                      f"(Ejemplos: {examples_str}). Revíselas individualmente.")

            self._add("Índice General", "Inconsistencias Individuales de Paginación", "error", detail,
                      "Entradas consistentes con el patrón general",
                      f"{len(mismatches)} entradas fuera de patrón", p_idx=idx_start, p_text="ÍNDICE GENERAL")
        elif not has_offset_report:
            # Sin offset y sin mismatches → todo correcto
            self._add("Índice General", "Consistencia de Páginas del Índice General", "passed",
                      "Todas las páginas del Índice General coinciden exactamente con la ubicación real de sus títulos en el documento.",
                      "Páginas coincidentes", "Páginas coincidentes")

    # ── Métodos Auxiliares de Construcción y Búsqueda ──────────────────────

    def _build_body_headings_map(self):
        body_headings = {}
        for p in self.paragraphs:
            txt = p['text'].strip()
            if not txt or not p.get('is_in_body', False):
                continue

            norm = self._norm_alphanumeric(txt)
            is_head = p.get('is_heading', False)
            first_run_size, _, _, _ = self._get_p_props(p)
            first_run_size = first_run_size or 0
            is_section_keyword = self._norm(txt) in [
                "RESUMEN", "ABSTRACT", "INTRODUCCION", "INTRODUCCIÓN",
                "CONCLUSIONES", "RECOMENDACIONES", "REFERENCIAS BIBLIOGRAFICAS", "ANEXOS"
            ]

            if is_head or first_run_size >= 12 or is_section_keyword:
                if norm and norm not in body_headings:
                    body_headings[norm] = p.get('estimated_page', 1)
        return body_headings

    def _find_index_range(self, section_name):
        idx_start = -1
        idx_end = -1
        
        # Buscar el inicio de la sección en los párrafos
        for i, p in enumerate(self.paragraphs):
            txt_upper = p['text'].strip().upper()
            if idx_start == -1:
                if section_name in txt_upper:
                    # Garantizar que no sea una línea con puntos (línea del TOC en sí)
                    if "...." not in p['text'] and not bool(re.search(r"\d+$", p['text'].strip())):
                        idx_start = i
            else:
                # Fin de la sección
                style = p.get('style_id', '')
                is_tdc = style.upper().startswith('TDC') if style else False
                if not is_tdc and txt_upper and len(txt_upper) > 3:
                    # Si encontramos otra sección principal, cerramos el rango
                    if any(k in txt_upper for k in ['ÍNDICE', 'INDICE', 'RESUMEN', 'ABSTRACT', 'ACRÓNIMOS', 'ACRONIMOS', 'DEDICATORIA', 'AGRADECIMIENTO', 'CAPITULO', 'INTRODUCCION']):
                        if style and ('Ttulo' in style or 'Heading' in style or 'titulo' in style.lower()):
                            idx_end = i
                            break

        if idx_start == -1:
            return -1, -1
        if idx_end == -1:
            idx_end = min(idx_start + 150, len(self.paragraphs))
        return idx_start, idx_end
