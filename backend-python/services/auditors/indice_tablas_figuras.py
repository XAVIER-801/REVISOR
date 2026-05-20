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

                if is_in_tables_index and table_idx_start == -1:
                    table_idx_start = p['index']
                elif is_in_figures_index and figure_idx_start == -1:
                    figure_idx_start = p['index']
                elif is_in_annexes_index and annex_idx_start == -1:
                    annex_idx_start = p['index']

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

        # Reportar presencia de hipervínculos
        self._report_hyperlinks(table_idx_start, "Tablas", "ÍNDICE DE TABLAS")
        self._report_hyperlinks(figure_idx_start, "Figuras", "ÍNDICE DE FIGURAS")
        self._report_hyperlinks(annex_idx_start, "Anexos", "ÍNDICE DE ANEXOS")

        # Reportar interlineado dinámico (1.5 si > 50 entradas, 2.0 si <= 50)
        self._audit_index_spacing("ÍNDICE DE TABLAS", "Tablas")
        self._audit_index_spacing("ÍNDICE DE FIGURAS", "Figuras")
        self._audit_index_spacing("ÍNDICE DE ANEXOS", "Anexos")

    def _find_index_range(self, section_name):
        idx_start = -1
        idx_end = -1
        for i, p in enumerate(self.paragraphs):
            txt_upper = p['text'].strip().upper()
            if idx_start == -1:
                is_match = False
                if section_name == "ÍNDICE DE TABLAS":
                    is_match = any(k in txt_upper for k in ['ÍNDICE DE TABLAS', 'INDICE DE TABLAS', 'ÍNDICE DE CUADROS', 'INDICE DE CUADROS'])
                elif section_name == "ÍNDICE DE FIGURAS":
                    is_match = any(k in txt_upper for k in ['ÍNDICE DE FIGURAS', 'INDICE DE FIGURAS', 'ÍNDICE DE ILUSTRACIONES', 'INDICE DE ILUSTRACIONES'])
                else:
                    is_match = section_name in txt_upper
                
                if is_match:
                    if "...." not in p['text'] and not bool(re.search(r"\d+$", p['text'].strip())):
                        idx_start = i
            else:
                style = p.get('style_id', '')
                is_tdc = style.upper().startswith('TDC') if style else False
                if not is_tdc and txt_upper and len(txt_upper) > 3:
                    if any(k in txt_upper for k in ['ÍNDICE', 'INDICE', 'RESUMEN', 'ABSTRACT', 'ACRÓNIMOS', 'ACRONIMOS', 'DEDICATORIA', 'AGRADECIMIENTO', 'CAPITULO', 'INTRODUCCION']):
                        if style and ('Ttulo' in style or 'Heading' in style or 'titulo' in style.lower()):
                            idx_end = i
                            break
        if idx_start == -1:
            return -1, -1
        if idx_end == -1:
            idx_end = min(idx_start + 150, len(self.paragraphs))
        return idx_start, idx_end

    def _audit_index_spacing(self, section_name, label):
        idx_start, idx_end = self._find_index_range(section_name)
        if idx_start == -1:
            return
        
        entries_to_check = []
        for i in range(idx_start + 1, idx_end):
            p = self.paragraphs[i]
            txt = p['text'].strip()
            if not txt:
                continue
            upper = txt.upper()
            if bool(re.match(r'^P[ÁA]G\.?:?$', upper.strip())):
                continue
            if section_name in upper:
                continue
            
            is_item = re.match(r'^(TABLA|FIGURA|ANEXO)\s+([A-Z0-9]+)', upper)
            if is_item:
                entries_to_check.append(p)
                
        total_entries = len(entries_to_check)
        if total_entries == 0:
            return
            
        if section_name == "ÍNDICE DE ANEXOS":
            required_spacing = 2.0
        else:
            required_spacing = 1.5 if total_entries > 50 else 2.0
        
        failing_entries = []
        for p in entries_to_check:
            line_spacing = p.get('line_spacing')
            val_spacing = line_spacing if line_spacing is not None else 1.0
            ok_spacing = abs(val_spacing - required_spacing) < 0.25
            if not ok_spacing:
                failing_entries.append((p, val_spacing))
                
        if failing_entries:
            for p, val in failing_entries[:5]:
                txt = p['text'].strip()
                self._add("Índice de Tablas/Figuras", f"Interlineado {label}: {txt[:20]}...", "error",
                          f"El interlineado del {section_name} debe ser de {required_spacing} (ya que el índice tiene {total_entries} entradas).",
                          f"{required_spacing}", f"{val}", p_idx=p['index'], p_text=txt)
            if len(failing_entries) > 5:
                self._add("Índice de Tablas/Figuras", f"Interlineado {label} (Restantes)", "warning",
                          f"Se encontraron {len(failing_entries) - 5} entradas adicionales con interlineado incorrecto en el {section_name} (debe ser {required_spacing}).",
                          f"{required_spacing}", "Incorrecto", p_idx=idx_start, p_text=section_name)
        else:
            self._add("Índice de Tablas/Figuras", f"Interlineado {label}", "passed",
                      f"El interlineado de todas las entradas en el {section_name} es correcto ({required_spacing}).",
                      f"{required_spacing}", f"{required_spacing}", p_idx=idx_start, p_text=section_name)

    def _report_hyperlinks(self, idx_start, label, section_name):
        if idx_start == -1:
            return
        
        missing_links = []
        total_entries = 0
        
        for p in self.paragraphs:
            txt = p['text'].strip()
            if not txt:
                continue
            
            sec_upper = p.get('section', '').upper()
            
            # Comprobar si corresponde a la sección del índice
            is_sec = False
            if label == "Tablas":
                is_sec = any(k in sec_upper for k in ['ÍNDICE DE TABLAS', 'INDICE DE TABLAS', 'ÍNDICE DE CUADROS', 'INDICE DE CUADROS'])
            elif label == "Figuras":
                is_sec = any(k in sec_upper for k in ['ÍNDICE DE FIGURAS', 'INDICE DE FIGURAS', 'ÍNDICE DE ILUSTRACIONES', 'INDICE DE ILUSTRACIONES'])
            elif label == "Anexos":
                is_sec = any(k in sec_upper for k in ['ÍNDICE DE ANEXOS', 'INDICE DE ANEXOS'])
                
            if is_sec:
                upper = txt.upper()
                is_item = re.match(r'^(TABLA|FIGURA|ANEXO)\s+([A-Z0-9]+)', upper)
                if is_item:
                    total_entries += 1
                    if not p.get('has_hyperlink', False):
                        missing_links.append(txt[:30] + "...")
        
        if total_entries > 0:
            ok_links = len(missing_links) == 0
            status = "passed" if ok_links else "warning"
            msg = (f"Las entradas del Índice de {label} cuentan correctamente con hipervínculos "
                   f"que enlazan directamente con los elementos en el documento." if ok_links else
                   f"Se sugiere que las entradas del Índice de {label} cuenten con hipervínculos "
                   f"activos para permitir la navegación directa a las secciones reales. "
                   f"Se detectaron {len(missing_links)} entradas sin hipervínculos activos (ej: {', '.join(missing_links[:3])}).")
            self._add("Índice de Tablas/Figuras", f"Hipervínculos en Índice de {label}", status, msg,
                      "Todas las entradas del índice con hipervínculos activos",
                      "Con hipervínculos" if ok_links else "Algunas entradas sin hipervínculos activos",
                      p_idx=idx_start, p_text=section_name)
