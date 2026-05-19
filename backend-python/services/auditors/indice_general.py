"""
indice_general.py - Auditoría del Índice General.

Reglas implementadas:
- Etiqueta "Pág.": Derecha, Negrita, Interlineado 1.5, sin sangría, Espaciado 0pt
- Título 'ÍNDICE GENERAL': 16pt, centrado, negrita
- CAPÍTULO I-IV y sus títulos: 12pt, centrado, negrita, sin relleno
- Nivel 2 (ej: 1.1.): Justificado, Negrita, Mayúsculas
- Nivel 3 (ej: 1.1.1.): Justificado, SIN negrita, Minúsculas
- Nivel 4/5: Justificado, SIN negrita, Minúsculas
- Nivel 1 (RESUMEN, ANEXOS, etc.): Justificado o Izquierda, Negrita, Mayúsculas
- Consistencia de páginas del índice vs páginas reales del documento
- Tamaño 12pt para todas las entradas
"""
import re
from .base_auditor import BaseAuditor


class IndiceGeneralAuditor(BaseAuditor):

    def audit(self):
        # === PASO 0: Auditar todas las etiquetas "Pág." en cualquier índice ===
        self._audit_pag_labels()

        # === PASO 1: Localizar el ÍNDICE GENERAL ===
        idx_start, idx_end = self._find_index_range()
        if idx_start == -1:
            return

        # === PASO 1.5: Construir mapa de títulos del cuerpo ===
        body_headings = self._build_body_headings_map(idx_end)
        general_mismatches = []

        # === PASO 2: Auditar cada entrada del índice ===
        for i in range(idx_start, idx_end):
            p = self.paragraphs[i]
            txt = p['text'].strip()
            upper = txt.upper()

            if len(txt) < 2:
                continue

            size = 0
            if p.get('runs') and len(p['runs']) > 0:
                size = p['runs'][0].get('size', 0)

            align = p.get('alignment', 'left')

            # Etiqueta "Pág." → Ya auditada en Paso 0
            es_etiqueta_pag = bool(re.match(r'^P[ÁA]G\.?:?$', upper.strip()))
            if es_etiqueta_pag:
                continue

            # Título principal 'ÍNDICE GENERAL'
            if i == idx_start:
                if size != 16 and size != 0:
                    self._add("Índice General", f"Tamaño título: {txt}", "error",
                             "El título 'ÍNDICE GENERAL' debe ser 16pt.",
                             "16pt", f"{size}pt", p_idx=p['index'], p_text=txt)
                if align != 'center':
                    self._add("Índice General", f"Alineación título: {txt}", "error",
                             "El título 'ÍNDICE GENERAL' debe estar centrado.",
                             "Centrado", align, p_idx=p['index'], p_text=txt)
                continue

            # Formato de la entrada
            indent_left_cm = round((p.get('indent_left') or 0) / 567.0, 2)
            indent_first_cm = round((p.get('indent_first') or 0) / 567.0, 2)
            indent_hanging_cm = round((p.get('indent_hanging') or 0) / 567.0, 2)
            is_bold = any(r.get('bold') for r in p.get('runs', []) if re.search(r'[a-zA-ZáéíóúÁÉÍÓÚñÑ]', r.get('text', '')))

            txt_letters = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ]', '', txt)
            is_uppercase = not any(c.islower() for c in txt_letters) if txt_letters else True
            has_dots_or_page = '....' in txt or bool(re.search(r'\d+$', txt.strip()))

            # Validar coincidencia de número de página
            page_match = re.search(r'(\d+)$', txt.strip())
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

                if actual_page is not None and actual_page != page_num:
                    general_mismatches.append({
                        "title": clean_title,
                        "idx_page": page_num,
                        "real_page": actual_page
                    })

            align_str_raw = "Centrado" if align == "center" else ("Izquierda" if align == "left" else ("Derecha" if align == "right" else "Justificada"))
            bold_str_raw = "Negrita" if is_bold else "Normal"
            case_str_raw = "Mayúsculas" if is_uppercase else "Minúsculas"

            # Identificar capítulos (I-IV)
            cap_match = re.search(r'CAP[ÍI]TULO\s+([IVXLCDM0-9]+)', upper)
            es_capitulo = bool(cap_match)
            roman_num = cap_match.group(1) if cap_match else ""

            es_capitulo_v_or_higher = False
            if es_capitulo and roman_num:
                if any(k in roman_num for k in ['V', 'X', 'L', 'C']) and roman_num != 'IV':
                    es_capitulo_v_or_higher = True

            nombres_capitulos_centrados = [
                'INTRODUCCION', 'INTRODUCCIÓN',
                'REVISION DE LITERATURA', 'REVISIÓN DE LITERATURA',
                'MATERIALES Y METODOS', 'MATERIALES Y MÉTODOS',
                'RESULTADOS Y DISCUSION', 'RESULTADOS Y DISCUSIÓN'
            ]

            era_capitulo_previo = False
            previo_era_v_or_higher = False
            for prev_idx in range(i - 1, idx_start, -1):
                prev_text = self.paragraphs[prev_idx]['text'].strip()
                if prev_text:
                    prev_upper = prev_text.upper()
                    prev_cap_match = re.search(r'CAP[ÍI]TULO\s+([IVXLCDM0-9]+)', prev_upper)
                    if prev_cap_match:
                        era_capitulo_previo = True
                        prev_roman = prev_cap_match.group(1)
                        if any(k in prev_roman for k in ['V', 'X', 'L', 'C']) and prev_roman != 'IV':
                            previo_era_v_or_higher = True
                    break

            es_centrado_req = (es_capitulo and not es_capitulo_v_or_higher) or \
                              (upper.strip() in nombres_capitulos_centrados) or \
                              (era_capitulo_previo and not previo_era_v_or_higher and not has_dots_or_page)

            # Filtrar si no parece índice
            style = p.get('style_id', '')
            is_tdc = style.upper().startswith('TDC') if style else False
            in_table = p.get('in_table', False)

            looks_like_index = has_dots_or_page or es_capitulo or es_centrado_req or any(k in upper for k in ['RESUMEN', 'ABSTRACT', 'CONCLUSIONES', 'RECOMENDACIONES', 'REFERENCIAS', 'ANEXOS', 'DEDICATORIA', 'AGRADECIMIENTO', 'ÍNDICE'])
            if not is_tdc and not in_table and not looks_like_index and i > idx_start + 3:
                continue

            # Validar que los preliminares no tengan número ni relleno
            preliminares_sin_numero = [
                'DEDICATORIA', 'AGRADECIMIENTO', 'AGRADECIMIENTOS',
                'ÍNDICE DE FIGURAS', 'INDICE DE FIGURAS',
                'ÍNDICE DE TABLAS', 'INDICE DE TABLAS',
                'ÍNDICE DE ACRÓNIMOS', 'INDICE DE ACRONIMOS',
                'ÍNDICE DE ANEXOS', 'INDICE DE ANEXOS',
                'ACRÓNIMOS', 'ACRONIMOS'
            ]
            if any(upper.strip() == p for p in preliminares_sin_numero):
                if has_dots_or_page:
                    self._add("Índice General", f"Preliminar con numeración: {txt[:20]}...", "error",
                              f"La sección '{txt[:25]}...' en el índice NO DEBE tener relleno de puntos ni número de página visible.",
                              "Sin relleno ni número", "Con relleno o número visible", p_idx=p['index'], p_text=txt)

            # Tamaño 12pt
            if size != 12 and size != 0:
                self._add("Índice General", f"Tamaño entrada: {txt[:25]}...", "error",
                          "Las entradas del índice deben ser 12pt.",
                          "12pt", f"{size}pt", p_idx=p['index'], p_text=txt)

            # Aplicación de reglas por nivel
            if es_centrado_req:
                ok_align = align == 'center'
                ok_indent = True
                ok_bold = is_bold
                ok_no_fill = not has_dots_or_page

                align_part = align_str_raw if ok_align else f"**{align_str_raw}**"
                bold_part = bold_str_raw if ok_bold else f"**{bold_str_raw}**"
                fill_part = "sin relleno" if ok_no_fill else f"**con relleno/número de página**"

                actual_str = f"{align_part}, {bold_part}, {fill_part}"
                expected_str = "Centrado, Negrita, sin relleno de página"

                passed = ok_align and ok_bold and ok_no_fill
                self._add("Índice General", f"Capítulo (I-IV): {txt[:20]}...", "passed" if passed else "error",
                          f"El '{txt[:25]}...' en el índice debe estar CENTRADO, en NEGRITA y SIN relleno de puntos ni numeración.",
                          expected_str, actual_str, p_idx=p['index'], p_text=txt)
                continue

            # Detectar sub-niveles por numeración
            hierarchy_match = re.match(r'^(\d+(?:\.\d+)+)\.?(\s+|\t)', txt.strip())

            if hierarchy_match:
                num_part = hierarchy_match.group(1)
                dots_count = num_part.count('.')

                if dots_count == 1:
                    # NIVEL 2: Justificada, Negrita, Mayúsculas
                    ok_align = align in ['both', 'justify']
                    ok_bold = is_bold
                    ok_case = is_uppercase

                    align_part = align_str_raw if ok_align else f"**{align_str_raw}**"
                    bold_part = bold_str_raw if ok_bold else f"**{bold_str_raw}**"
                    case_part = case_str_raw if ok_case else f"**{case_str_raw}**"

                    actual_str = f"{align_part}, {bold_part}, {case_part}"
                    expected_str = "Justificada, Negrita, Mayúsculas"

                    passed = ok_align and ok_bold and ok_case
                    self._add("Índice General", f"Formato Nivel 2: {txt[:20]}...", "passed" if passed else "error",
                              f"El título de Nivel 2 '{txt[:20]}...' en el índice debe estar JUSTIFICADO, en NEGRITA y en MAYÚSCULAS.",
                              expected_str, actual_str, p_idx=p['index'], p_text=txt)

                elif dots_count == 2:
                    # NIVEL 3: Justificada, SIN negrita, Minúsculas
                    ok_align = align in ['both', 'justify']
                    ok_bold = not is_bold
                    ok_case = not is_uppercase

                    align_part = align_str_raw if ok_align else f"**{align_str_raw}**"
                    bold_part = bold_str_raw if ok_bold else f"**{bold_str_raw}**"
                    case_part = case_str_raw if ok_case else f"**{case_str_raw}**"

                    actual_str = f"{align_part}, {bold_part}, {case_part}"
                    expected_str = "Justificada, Normal (sin negrita), Minúsculas"

                    passed = ok_align and ok_bold and ok_case
                    self._add("Índice General", f"Formato Nivel 3: {txt[:20]}...", "passed" if passed else "error",
                              f"El título de Nivel 3 '{txt[:20]}...' en el índice debe estar JUSTIFICADO, sin negrita (NORMAL) y en MINÚSCULAS.",
                              expected_str, actual_str, p_idx=p['index'], p_text=txt)

                else:
                    # NIVEL 4/5: Justificada, SIN negrita, Minúsculas
                    ok_align = align in ['both', 'justify']
                    ok_bold = not is_bold
                    ok_case = not is_uppercase

                    align_part = align_str_raw if ok_align else f"**{align_str_raw}**"
                    bold_part = bold_str_raw if ok_bold else f"**{bold_str_raw}**"
                    case_part = case_str_raw if ok_case else f"**{case_str_raw}**"

                    actual_str = f"{align_part}, {bold_part}, {case_part}"
                    expected_str = "Justificada, Normal (sin negrita), Minúsculas"

                    passed = ok_align and ok_bold and ok_case
                    self._add("Índice General", f"Formato Nivel 4/5: {txt[:20]}...", "passed" if passed else "error",
                              f"El título de Nivel 4/5 '{txt[:20]}...' en el índice debe estar JUSTIFICADO, sin negrita (NORMAL) y en MINÚSCULAS.",
                              expected_str, actual_str, p_idx=p['index'], p_text=txt)
            else:
                # NIVEL 1 (RESUMEN, ANEXOS, etc.)
                ok_align = align in ['both', 'justify', 'left']
                ok_bold = is_bold
                ok_case = is_uppercase

                align_part = align_str_raw if ok_align else f"**{align_str_raw}**"
                bold_part = bold_str_raw if ok_bold else f"**{bold_str_raw}**"
                case_part = case_str_raw if ok_case else f"**{case_str_raw}**"

                actual_str = f"{align_part}, {bold_part}, {case_part}"
                expected_str = "Justificada o Izquierda, Negrita, Mayúsculas"

                passed = ok_align and ok_bold and ok_case
                self._add("Índice General", f"Formato Nivel 1: {txt[:20]}...", "passed" if passed else "error",
                          f"El título de Nivel 1 '{txt[:20]}...' en el índice debe estar JUSTIFICADO o ALINEADO A LA IZQUIERDA, en NEGRITA y en MAYÚSCULAS.",
                          expected_str, actual_str, p_idx=p['index'], p_text=txt)

        # Reportar consistencia de páginas
        if idx_start != -1:
            if len(general_mismatches) > 0:
                ejemplos = ", ".join([f"'{m['title']}' (Índice: {m['idx_page']} vs Real: {m['real_page']})" for m in general_mismatches[:3]])
                if len(general_mismatches) > 3:
                    ejemplos += "..."
                    
                # Encontrar el párrafo exacto del primer error para colocar el globo ahí
                first_error_idx = idx_start
                for i in range(idx_start, idx_end):
                    if general_mismatches[0]['title'] in self.paragraphs[i]['text']:
                        first_error_idx = i
                        break
                        
                self._add("Índice General", "Consistencia de Páginas del Índice General", "warning",
                          f"La numeración de las páginas en el Índice General no coincide con la ubicación real de las secciones en el documento. Se detectaron {len(general_mismatches)} inconsistencias (Ejemplos: {ejemplos}). El número en el índice debe ser el mismo que le corresponde a la hoja física real.",
                          "Páginas del índice coincidentes con las hojas reales", "Páginas con desajustes",
                          p_idx=first_error_idx, p_text=self.paragraphs[first_error_idx]['text'])
            else:
                self._add("Índice General", "Consistencia de Páginas del Índice General", "passed",
                          "La numeración de todas las páginas en el Índice General coincide perfectamente con la ubicación real de las secciones en el documento.",
                          "Páginas del índice coincidentes con las hojas reales", "Coincidente",
                          p_idx=idx_start, p_text="ÍNDICE GENERAL")

    # ── Métodos auxiliares privados ──────────────────────────────────────

    def _audit_pag_labels(self):
        """Auditar todas las etiquetas 'Pág.' en cualquier índice de la tesis."""
        for p in self.paragraphs:
            txt = p['text'].strip()
            upper = txt.upper()
            es_etiqueta_pag = bool(re.match(r'^P[ÁA]G\.?:?$', upper))
            if not es_etiqueta_pag:
                continue

            is_bold = any(r.get('bold') for r in p.get('runs', []))
            is_italic = any(r.get('italic') for r in p.get('runs', []))
            align = p.get('alignment', 'left')
            align_str = "Centrado" if align == "center" else ("Izquierda" if align == "left" else ("Derecha" if align == "right" else "Justificada"))

            indent_left_cm = round((p.get('indent_left') or 0) / 567.0, 2)
            indent_first_cm = round((p.get('indent_first') or 0) / 567.0, 2)
            indent_right_cm = round((p.get('indent_right') or 0) / 567.0, 2)
            indent_hanging_cm = round((p.get('indent_hanging') or 0) / 567.0, 2)

            line_spacing = p.get('line_spacing')
            s_before = p.get('spacing_before', 0)
            s_after = p.get('spacing_after', 0)

            ok_text = txt == "Pág."
            ok_align = align == 'right'
            ok_bold = is_bold and not is_italic
            ok_spacing = (s_before is None or s_before < 1) and (s_after is None or s_after < 1)
            ok_line_spacing = line_spacing is not None and abs(line_spacing - 1.5) < 0.15
            ok_indent = abs(indent_left_cm) < 0.1 and abs(indent_first_cm) < 0.1 and abs(indent_right_cm) < 0.1 and abs(indent_hanging_cm) < 0.1

            self._add("Índice General", "Etiqueta \"Pág.\" - Texto",
                      "passed" if ok_text else "error",
                      "La etiqueta de cabecera de página debe estar escrita exactamente como 'Pág.' (con tilde y punto final).",
                      "Pág.", txt, p_idx=p['index'], p_text=txt)

            expected_desc = "Espaciado: anterior 0pt y posterior 0pt, Alineación: derecha, Interlineado: 1.5, Estilo de fuente: negrita, Sangría: sin sangría de ningún tipo"
            actual_spacing = f"Espaciado: ant {s_before or 0}pt y post {s_after or 0}pt"
            actual_align = f"Alineación: {align_str}"
            actual_line_spacing = f"Interlineado: {line_spacing or 'Por defecto'}"
            actual_bold = "Negrita" if is_bold else "Normal"
            actual_italic = " Cursiva" if is_italic else ""
            actual_indent = f"Sangría: izq {indent_left_cm}cm, der {indent_right_cm}cm, 1ra {indent_first_cm}cm"
            actual_desc = f"{actual_spacing}, {actual_align}, {actual_line_spacing}, {actual_bold}{actual_italic}, {actual_indent}"

            passed = ok_align and ok_bold and ok_spacing and ok_line_spacing and ok_indent
            self._add("Índice General", "Etiqueta \"Pág.\" - Formato",
                      "passed" if passed else "error",
                      "La etiqueta de cabecera 'Pág.' debe tener espaciado 0pt (anterior/posterior), alineación derecha, interlineado 1.5, negrita y sin sangrías.",
                      expected_desc, actual_desc, p_idx=p['index'], p_text=txt)

    def _find_index_range(self):
        idx_start = -1
        idx_end = -1
        for i, p in enumerate(self.paragraphs):
            txt_upper = p['text'].strip().upper()
            if idx_start == -1:
                if 'ÍNDICE GENERAL' in txt_upper or 'INDICE GENERAL' in txt_upper:
                    idx_start = i
            else:
                style = p.get('style_id', '')
                is_tdc = style.upper().startswith('TDC') if style else False
                if not is_tdc and txt_upper and len(txt_upper) > 3:
                    if any(k in txt_upper for k in ['ÍNDICE DE TABLAS', 'INDICE DE TABLAS',
                           'ÍNDICE DE FIGURAS', 'INDICE DE FIGURAS', 'RESUMEN', 'ABSTRACT',
                           'ACRÓNIMOS', 'ACRONIMOS', 'DEDICATORIA', 'AGRADECIMIENTO']):
                        if style and ('Ttulo' in style or 'Heading' in style or 'titulo' in style.lower()):
                            idx_end = i
                            break

        if idx_start == -1:
            return -1, -1
        if idx_end == -1:
            idx_end = min(idx_start + 300, len(self.paragraphs))
        return idx_start, idx_end

    def _build_body_headings_map(self, start_body_search):
        body_headings = {}
        for idx_b in range(start_body_search, len(self.paragraphs)):
            p_b = self.paragraphs[idx_b]
            txt_b = p_b['text'].strip()
            if not txt_b:
                continue

            norm_b = self._norm_alphanumeric(txt_b)
            is_head = p_b.get('is_heading', False)
            first_run_size = p_b['runs'][0].get('size', 0) if p_b.get('runs') else 0
            is_section_keyword = self._norm(txt_b) in [
                "RESUMEN", "ABSTRACT", "INTRODUCCION", "INTRODUCCIÓN",
                "CONCLUSIONES", "RECOMENDACIONES", "REFERENCIAS BIBLIOGRAFICAS", "ANEXOS"
            ]

            if is_head or first_run_size >= 12 or is_section_keyword:
                if norm_b and norm_b not in body_headings:
                    body_headings[norm_b] = p_b.get('estimated_page', 1)
        return body_headings
