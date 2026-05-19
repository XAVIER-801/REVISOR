"""
indice_tablas_figuras.py - Auditoría de Índices de Tablas, Figuras y Anexos.

Reglas implementadas:
- Capitalización de etiquetas (Tabla, Figura, Anexo en formato Tipo Título)
- Punto después de la etiqueta (no debe llevar punto)
- Tabulación correcta entre etiqueta y descripción
- Consistencia de páginas del índice vs páginas reales
"""
import re
from .base_auditor import BaseAuditor


class IndiceTablasFigurasAuditor(BaseAuditor):

    def audit(self):
        # Pre-construir mapa de ítems reales del documento
        body_items = {}
        for p_b in self.paragraphs:
            txt_b = p_b['text'].strip()
            if not txt_b:
                continue
            m_b = re.match(r'^(Tabla|Figura|Anexo)\s+([A-Z0-9]+)', txt_b, re.IGNORECASE)
            if m_b:
                prefix_b = m_b.group(1).capitalize()
                num_b = m_b.group(2)
                key_b = f"{prefix_b} {num_b}"
                if key_b not in body_items:
                    body_items[key_b] = p_b.get('estimated_page', 1)

        table_mismatches = []
        figure_mismatches = []
        annex_mismatches = []
        table_idx_start = -1
        figure_idx_start = -1
        annex_idx_start = -1

        for i, p in enumerate(self.paragraphs):
            txt = p['text'].strip()
            if not txt:
                continue

            sec_upper = p.get('section', '').upper()

            is_in_tables_index = any(k in sec_upper for k in ['ÍNDICE DE TABLAS', 'INDICE DE TABLAS', 'ÍNDICE DE CUADROS', 'INDICE DE CUADROS'])
            is_in_figures_index = any(k in sec_upper for k in ['ÍNDICE DE FIGURAS', 'INDICE DE FIGURAS', 'ÍNDICE DE ILUSTRACIONES', 'INDICE DE ILUSTRACIONES'])
            is_in_annexes_index = any(k in sec_upper for k in ['ÍNDICE DE ANEXOS', 'INDICE DE ANEXOS'])

            if not (is_in_tables_index or is_in_figures_index or is_in_annexes_index):
                continue

            upper = txt.upper()
            is_item = re.match(r'^(TABLA|FIGURA|ANEXO)\s+([A-Z0-9]+)', upper)
            if not is_item:
                continue

            match = re.match(r'^(Tabla|Figura|Anexo)\s+([A-Z0-9]+)(\.?)(.*)', txt, re.IGNORECASE)
            if match:
                raw_prefix = match.group(1)
                prefix = raw_prefix.capitalize()
                num = match.group(2)
                has_dot = match.group(3) == "."
                rest = match.group(4)

                # Validar coincidencia de página
                page_match = re.search(r'(\d+)$', txt.strip())
                if page_match:
                    page_num = int(page_match.group(1))
                    key_item = f"{prefix} {num}"
                    actual_page = body_items.get(key_item)

                    if actual_page is not None and actual_page != page_num:
                        mismatch_info = {"title": f"{prefix} {num}", "idx_page": page_num, "real_page": actual_page}
                        if is_in_tables_index:
                            table_mismatches.append(mismatch_info)
                            if table_idx_start == -1: table_idx_start = p['index']
                        elif is_in_figures_index:
                            figure_mismatches.append(mismatch_info)
                            if figure_idx_start == -1: figure_idx_start = p['index']
                        elif is_in_annexes_index:
                            annex_mismatches.append(mismatch_info)
                            if annex_idx_start == -1: annex_idx_start = p['index']

                label = f"{prefix} {num}"

                # Regla 0: Capitalización
                ok_case = raw_prefix == prefix
                if not ok_case:
                    self._add("Índice de Tablas/Figuras", f"Capitalización Etiqueta: {raw_prefix} {num}", "error",
                              f"La etiqueta '{raw_prefix} {num}' debe estar escrita en formato Tipo Título (por ejemplo: '{prefix} {num}').",
                              f"'{prefix} {num}'", f"'{raw_prefix} {num}'", p_idx=p['index'], p_text=txt)
                else:
                    self._add("Índice de Tablas/Figuras", f"Capitalización Etiqueta: {label}", "passed",
                              f"La capitalización de la etiqueta '{label}' es correcta (Tipo Título).",
                              f"'{prefix} {num}'", f"'{raw_prefix} {num}'", p_idx=p['index'], p_text=txt)

                # Regla 1: No punto después del número
                if has_dot:
                    self._add("Índice de Tablas/Figuras", f"Punto en Etiqueta: {label}", "error",
                              f"La etiqueta '{prefix} {num}.' en el índice tiene un punto final innecesario. Según la norma, debe ser '{prefix} {num}' (sin punto).",
                              f"Sin punto final (ej: '{prefix} {num}')", f"Con punto final (ej: '{prefix} {num}.')", p_idx=p['index'], p_text=txt)
                else:
                    self._add("Índice de Tablas/Figuras", f"Punto en Etiqueta: {label}", "passed",
                              f"La etiqueta '{prefix} {num}' en el índice está correctamente escrita sin punto final.",
                              f"Sin punto final (ej: '{prefix} {num}')", f"Sin punto final (ej: '{prefix} {num}')", p_idx=p['index'], p_text=txt)

                # Regla 2: Tabulación
                has_tab_separator = rest.startswith('\t') or '\t' in rest[:4]
                if not has_tab_separator:
                    self._add("Índice de Tablas/Figuras", f"Página de Entrada: {prefix} {num}", "error",
                              f"La descripción o título de la '{prefix} {num}' en el índice no está tabulada. Debe usar un carácter de tabulación (tecla Tab) para separar la descripción de la etiqueta, asegurando que no estén pegados.",
                              "Tabulado (con tecla Tab) y no pegado", "**Pegado o separado por espacios simples**", p_idx=p['index'], p_text=txt)
                else:
                    self._add("Índice de Tablas/Figuras", f"Página de Entrada: {prefix} {num}", "passed",
                              f"La descripción de la '{prefix} {num}' en el índice está correctamente tabulada y separada de la etiqueta.",
                              "Tabulado", "Tabulado", p_idx=p['index'], p_text=txt)

        # Reportar advertencias agrupadas
        self._report_mismatches(table_mismatches, table_idx_start, "Tablas", "ÍNDICE DE TABLAS")
        self._report_mismatches(figure_mismatches, figure_idx_start, "Figuras", "ÍNDICE DE FIGURAS")
        self._report_mismatches(annex_mismatches, annex_idx_start, "Anexos", "ÍNDICE DE ANEXOS")

    def _report_mismatches(self, mismatches, idx_start, label, p_text):
        if len(mismatches) > 0 and idx_start != -1:
            ejemplos = ", ".join([f"'{m['title']}' (Índice: {m['idx_page']} vs Real: {m['real_page']})" for m in mismatches[:3]])
            if len(mismatches) > 3:
                ejemplos += "..."
            self._add("Índice de Tablas/Figuras", f"Consistencia de Páginas del Índice de {label}", "warning",
                      f"La numeración de las páginas en el Índice de {label} no coincide con la ubicación real en el documento. Se detectaron {len(mismatches)} inconsistencias (Ejemplos: {ejemplos}).",
                      "Páginas del índice coincidentes con las hojas reales", "Páginas con desajustes",
                      p_idx=idx_start, p_text=p_text)
