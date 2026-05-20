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
        # 1. Pre-construir mapas de elementos reales del cuerpo
        body_headings = self._build_body_headings_map()
        body_items = self._build_body_items_map()

        # 2. Auditar cada uno de los 4 tipos de índices
        self._audit_indice_general_pages(body_headings)
        self._audit_indice_tablas_pages(body_items)
        self._audit_indice_figuras_pages(body_items)
        self._audit_indice_anexos_pages(body_items)

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

        # Aplicar el algoritmo estadístico de offset óptimo
        if pairs:
            diffs = [p["page_num"] - p["actual_page"] for p in pairs]
            # Encontrar el offset más común (moda)
            most_common_diff = Counter(diffs).most_common(1)[0][0]

            for p in pairs:
                # Si no coincide con el offset común, hay una inconsistencia real
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

            detail = (f"La numeración de las páginas en el Índice General no coincide con la ubicación real en el documento. "
                      f"Se detectaron {len(mismatches)} inconsistencias (Ejemplos: {examples_str}).")

            self._add("Índice General", "Consistencia de Páginas del Índice General", "error", detail,
                      "Páginas del índice coincidentes con las hojas reales",
                      f"Se detectaron {len(mismatches)} inconsistencias", p_idx=idx_start, p_text="ÍNDICE GENERAL")
        else:
            self._add("Índice General", "Consistencia de Páginas del Índice General", "passed",
                      "Todas las páginas del Índice General coinciden exactamente con la ubicación real de sus títulos en el documento.",
                      "Páginas coincidentes", "Páginas coincidentes")

    def _audit_indice_tablas_pages(self, body_items):
        self._audit_special_index_pages(body_items, "ÍNDICE DE TABLAS", "Tabla", "Índice de Tablas")

    def _audit_indice_figuras_pages(self, body_items):
        self._audit_special_index_pages(body_items, "ÍNDICE DE FIGURAS", "Figura", "Índice de Figuras")

    def _audit_indice_anexos_pages(self, body_items):
        self._audit_special_index_pages(body_items, "ÍNDICE DE ANEXOS", "Anexo", "Índice de Anexos")

    def _audit_special_index_pages(self, body_items, section_keyword, label_prefix, rule_name):
        """Valida de forma genérica la paginación de un índice especial (Tablas, Figuras o Anexos)."""
        idx_start, idx_end = self._find_index_range(section_keyword)
        if idx_start == -1:
            return

        mismatches = []
        pairs = []

        for i in range(idx_start + 1, idx_end):
            p = self.paragraphs[i]
            txt = p['text'].strip()
            if not txt:
                continue

            upper = txt.upper()
            is_item = re.match(rf'^{label_prefix.upper()}\s+([A-Z0-9]+)', upper)
            if not is_item:
                continue

            match = re.match(rf'^({label_prefix})\s+([A-Z0-9]+)(\.?)(.*)', txt, re.IGNORECASE)
            if match:
                prefix = match.group(1).capitalize()
                num = match.group(2)

                page_match = re.search(r'(\d+)$', txt.strip())
                if page_match:
                    page_num = int(page_match.group(1))
                    key_item = f"{prefix} {num}"
                    actual_page = body_items.get(key_item)

                    if actual_page is not None:
                        pairs.append({
                            "title": f"{prefix} {num}",
                            "page_num": page_num,
                            "actual_page": actual_page
                        })

        if pairs:
            diffs = [p["page_num"] - p["actual_page"] for p in pairs]
            most_common_diff = Counter(diffs).most_common(1)[0][0]

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

            detail = (f"La numeración de las páginas en el {rule_name} no coincide con la ubicación real en el documento. "
                      f"Se detectaron {len(mismatches)} inconsistencias (Ejemplos: {examples_str}).")

            self._add("Índice de Tablas/Figuras", f"Consistencia de Páginas del {rule_name}", "error", detail,
                      "Páginas del índice coincidentes con las hojas reales",
                      f"Se detectaron {len(mismatches)} inconsistencias", p_idx=idx_start, p_text=section_keyword)
        else:
            self._add("Índice de Tablas/Figuras", f"Consistencia de Páginas del {rule_name}", "passed",
                      f"Todas las páginas del {rule_name} coinciden exactamente con la ubicación real de los elementos en el documento.",
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

    def _build_body_items_map(self):
        body_items = {}
        for p in self.paragraphs:
            txt = p['text'].strip()
            if not txt or not p.get('is_in_body', False):
                continue
            
            m = re.match(r'^(Tabla|Figura|Anexo)\s+([A-Z0-9]+)', txt, re.IGNORECASE)
            if m:
                prefix = m.group(1).capitalize()
                num = m.group(2)
                key = f"{prefix} {num}"
                if key not in body_items:
                    body_items[key] = p.get('estimated_page', 1)
        return body_items

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
