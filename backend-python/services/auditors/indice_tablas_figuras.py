"""
indice_tablas_figuras.py - Auditoría de Índices de Tablas, Figuras y Anexos.

Reglas implementadas:
- Capitalización de etiquetas (Tabla, Figura, Anexo en formato Tipo Título)
- Punto después de la etiqueta (no debe llevar punto)
- Tabulación correcta entre etiqueta y descripción
- Consistencia de páginas del índice vs páginas reales
"""
import re
from collections import Counter
from .base_auditor import BaseAuditor


class IndiceTablasFigurasAuditor(BaseAuditor):

    def audit(self):
        # ═══ VALIDAR TÍTULOS DE PÁGINA (16pt) ═══
        self._audit_page_titles()

        # Pre-construir mapa de elementos reales del cuerpo para cruce de páginas
        body_items = self._build_body_items_map()

        table_idx_start = -1
        figure_idx_start = -1
        annex_idx_start = -1
        table_entries = []   # para cruce de páginas
        figure_entries = []  # para cruce de páginas
        annex_entries = []   # para cruce de páginas

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

                # Regla 0: Capitalización ESTRICTA (Tabla, Figura, Anexo - no MAYÚSCULAS)
                ok_case = raw_prefix == prefix
                if not ok_case:
                    self._add(
                        "Índice de Tablas/Figuras",
                        f"Capitalización Etiqueta: {raw_prefix} {num}",
                        "error",
                        f"La etiqueta '{raw_prefix} {num}' DEBE escribirse EXACTAMENTE como "
                        f"'{prefix} {num}' (primera letra mayúscula, resto minúsculas), "
                        f"según la Guía UNAP pág. 12-14. No use mayúsculas completas ni "
                        f"minúsculas iniciales.",
                        f"'{prefix} {num}'",
                        f"'{raw_prefix} {num}'",
                        p_idx=p['index'],
                        p_text=txt,
                    )

                # Regla 1: NO punto después del número en el índice
                # (en la SECCIÓN de anexos sí va con punto, pero en el ÍNDICE no)
                if has_dot:
                    self._add(
                        "Índice de Tablas/Figuras",
                        f"Punto en Etiqueta: {label}",
                        "error",
                        f"La etiqueta '{prefix} {num}.' en el ÍNDICE tiene un punto final "
                        f"innecesario. En el índice debe ser '{prefix} {num}' SIN punto, "
                        f"separado del título por una tabulación. (En la sección de Anexos "
                        f"sí lleva punto, pero aquí en el índice no.)",
                        f"'{prefix} {num}' (sin punto, con tab)",
                        f"'{prefix} {num}.' (con punto)",
                        p_idx=p['index'],
                        p_text=txt,
                    )

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

                # Regla 3: Sangría francesa específica por tipo de índice (Guía UNAP pág. 12-14)
                # Tablas: 2.0 cm | Figuras: 2.15 cm | Anexos: 2.25 cm
                h_cm = round(p.get('indent_hanging') or 0, 2)

                expected_hang = None
                if is_in_tables_index:
                    expected_hang = 2.0
                elif is_in_figures_index:
                    expected_hang = 2.15
                elif is_in_annexes_index:
                    expected_hang = 2.25

                if expected_hang is not None and abs(h_cm - expected_hang) > 0.15:
                    self._add("Índice de Tablas/Figuras", f"Sangría Francesa: {prefix} {num}", "error",
                              f"La entrada '{prefix} {num}' debe tener sangría francesa de {expected_hang}cm "
                              f"(específica para el tipo de índice según Guía UNAP).",
                              f"Francesa {expected_hang}cm", f"Francesa {h_cm}cm",
                              p_idx=p['index'], p_text=txt)

                # Regla 4: Alineación justificada (Guía pág. 12-14)
                align = p.get('alignment', 'left')
                if align != 'both':
                    self._add("Índice de Tablas/Figuras", f"Alineación: {prefix} {num}", "error",
                              f"Las entradas del índice deben estar justificadas.",
                              "Justificada", self._align_display(align), p_idx=p['index'], p_text=txt)

                # ═══ Regla 5: ESTILO DIFERENCIADO DE LA ENTRADA ═══
                # La etiqueta ("Tabla N" / "Figura N" / "Anexo N") debe ir en NEGRITA.
                # La descripción posterior (después del tab) debe ir SIN negrita.
                # Esto se evalúa por separado para no marcar falsos positivos.
                label_text = f"{prefix} {num}"
                label_is_bold = self._check_prefix_bold(p, len(label_text))
                desc_is_bold = self._check_description_bold(p, len(label_text))
                desc_is_italic = self._check_description_italic(p, len(label_text))

                if not label_is_bold:
                    self._add(
                        "Índice de Tablas/Figuras",
                        f"Etiqueta sin negrita: {prefix} {num}",
                        "error",
                        f"La etiqueta '{prefix} {num}' en el índice DEBE estar en NEGRITA. "
                        f"Solo la descripción que sigue (después del tab) va sin negrita.",
                        f"'{prefix} {num}' en negrita",
                        "Sin negrita",
                        p_idx=p['index'], p_text=txt,
                    )

                if desc_is_bold:
                    self._add(
                        "Índice de Tablas/Figuras",
                        f"Descripción en negrita: {prefix} {num}",
                        "error",
                        f"La descripción que sigue a '{prefix} {num}' debe estar SIN negrita. "
                        f"Solo la etiqueta '{prefix} {num}' lleva negrita.",
                        "Descripción sin negrita",
                        "Descripción en negrita",
                        p_idx=p['index'], p_text=txt,
                    )

                if desc_is_italic:
                    self._add(
                        "Índice de Tablas/Figuras",
                        f"Descripción en cursiva: {prefix} {num}",
                        "warning",
                        f"La descripción de '{prefix} {num}' no debe ir en cursiva. "
                        f"Excepción: nombres científicos sí pueden ir en cursiva.",
                        "Sin cursiva (excepto nombres científicos)",
                        "Cursiva",
                        p_idx=p['index'], p_text=txt,
                    )

                # Regla 6: Tamaño 12pt
                size = p['runs'][0].get('size', 0) if p.get('runs') else 0
                if size > 0 and abs(size - 12) > 0.5:
                    self._add("Índice de Tablas/Figuras", f"Tamaño: {prefix} {num}", "error",
                              f"Las entradas del índice deben ser de 12pt.",
                              "12pt", f"{size}pt", p_idx=p['index'], p_text=txt)

                # Recolectar entrada para cruce de páginas
                page_match = re.search(r'(?:\.{2,}|\s+)(\d+)\s*$', txt)
                if page_match:
                    entry = {'label': label, 'page': int(page_match.group(1)), 'p': p}
                    if is_in_tables_index:
                        table_entries.append(entry)
                    elif is_in_figures_index:
                        figure_entries.append(entry)
                    elif is_in_annexes_index:
                        annex_entries.append(entry)

        # Cruce de páginas del índice vs contenido real
        self._cross_reference_pages(table_entries, body_items, "Tablas", "ÍNDICE DE TABLAS")
        self._cross_reference_pages(figure_entries, body_items, "Figuras", "ÍNDICE DE FIGURAS")
        self._cross_reference_pages(annex_entries, body_items, "Anexos", "ÍNDICE DE ANEXOS")

        # Reportar presencia de hipervínculos
        self._report_hyperlinks(table_idx_start, "Tablas", "ÍNDICE DE TABLAS")
        self._report_hyperlinks(figure_idx_start, "Figuras", "ÍNDICE DE FIGURAS")
        self._report_hyperlinks(annex_idx_start, "Anexos", "ÍNDICE DE ANEXOS")

        # Reportar interlineado dinámico (1.5 si > 50 entradas, 2.0 si <= 50)
        self._audit_index_spacing("ÍNDICE DE TABLAS", "Tablas")
        self._audit_index_spacing("ÍNDICE DE FIGURAS", "Figuras")
        self._audit_index_spacing("ÍNDICE DE ANEXOS", "Anexos")

    def _build_body_items_map(self):
        body_items = {}
        in_annexes = False
        for p in self.paragraphs:
            txt = p['text'].strip()
            if not txt:
                continue

            # Saltar párrafos dentro de los propios índices (falsos positivos)
            sec_upper = p.get('section', '').upper()
            if any(k in sec_upper for k in ['ÍNDICE DE TABLAS', 'INDICE DE TABLAS',
                                             'ÍNDICE DE FIGURAS', 'INDICE DE FIGURAS',
                                             'ÍNDICE DE ANEXOS', 'INDICE DE ANEXOS',
                                             'ÍNDICE DE CUADROS', 'INDICE DE CUADROS',
                                             'ÍNDICE DE ILUSTRACIONES', 'INDICE DE ILUSTRACIONES']):
                continue

            m = re.match(r'^(Tabla|Figura|Anexo)\s+([A-Z0-9]+)', txt, re.IGNORECASE)
            if m:
                pfx = m.group(1).capitalize()
                num = m.group(2)
                key = f"{pfx} {num}"
                page = p.get('estimated_page', p.get('page', 1))
                if key not in body_items and not in_annexes:
                    body_items[key] = page

            # Trackear si entramos a la sección de anexos
            upper = txt.upper()
            if any(k in upper for k in ['ÍNDICE DE ANEXOS', 'INDICE DE ANEXOS']) and '....' not in txt:
                in_annexes = True
        return body_items

    def _cross_reference_pages(self, entries, body_items, label, section_name):
        if not entries:
            return
        diffs = []
        for e in entries:
            label_key = e['label']
            body_page = body_items.get(label_key)
            if body_page is not None:
                diff = body_page - e['page']
                diffs.append(diff)

        if not diffs:
            return

        # Calcular offset como moda de diferencias
        diff_counter = Counter(diffs)
        offset = diff_counter.most_common(1)[0][0]

        mismatches = [(e, body_items.get(e['label'])) for e in entries
                      if e['label'] in body_items
                      and (body_items[e['label']] - e['page']) != offset]

        total_checked = sum(1 for e in entries if e['label'] in body_items)
        ok = len(mismatches) == 0

        if ok and total_checked > 0:
            first_label = entries[0]['label']
            first_body = body_items.get(first_label)
            first_detail = (f"'{first_label}' aparece en página {first_body} del documento"
                            if first_body is not None
                            else f"'{first_label}' (no encontrado en el cuerpo)")
            self._add(
                "Índice de Tablas/Figuras",
                f"Cruce de páginas: {section_name}",
                "passed",
                f"Todas las páginas del {section_name} coinciden con el contenido real "
                f"(offset estimado: {offset:+d}, basado en {total_checked} entradas). "
                f"Ej: {first_detail} "
                f"y listada como página {entries[0]['page']} en el índice "
                f"(diferencia: {offset:+d}).",
                f"Coinciden ({total_checked}/{total_checked})",
                f"Coinciden",
            )
        else:
            for e, body_p in mismatches[:5]:
                list_diff = body_p - e['page']
                self._add(
                    "Índice de Tablas/Figuras",
                    f"Cruce de páginas: {e['label']}",
                    "error",
                    f"El {section_name} lista '{e['label']}' en página {e['page']}, "
                    f"pero el elemento real está en página {body_p} del documento "
                    f"(diferencia observada: {list_diff:+d}, offset esperado: {offset:+d}). "
                    f"Esto puede deberse a que se añadió o quitó contenido sin actualizar el índice.",
                    f"Página {body_p}",
                    f"Página {e['page']} (listada)",
                    p_idx=e['p']['index'],
                    p_text=e['p']['text'],
                )
            if len(mismatches) > 5:
                self._add(
                    "Índice de Tablas/Figuras",
                    f"Cruce de páginas: {section_name} (restantes)",
                    "warning",
                    f"Se encontraron {len(mismatches)} entradas con página incorrecta en el "
                    f"{section_name} (offset esperado: {offset:+d}).",
                    f"Coincidentes: {total_checked - len(mismatches)}/{total_checked}",
                    f"Incorrectas: {len(mismatches)}/{total_checked}",
                )

    def _audit_page_titles(self):
        """
        Audita los TÍTULOS DE PÁGINA "ÍNDICE DE TABLAS", "ÍNDICE DE FIGURAS",
        "ÍNDICE DE ANEXOS" — los que aparecen como encabezado de su propia
        página (no como entrada del Índice General).

        Heurística para distinguir:
          - Es título de página si: centrado + tamaño grande (>=14pt) + sin
            relleno de puntos ni número de página al final.
          - Es entrada del índice general si: tiene relleno '....' o termina
            con un número de página, o si su tamaño es <= 12pt.
        """
        TARGETS = {
            "ÍNDICE DE TABLAS", "INDICE DE TABLAS",
            "ÍNDICE DE FIGURAS", "INDICE DE FIGURAS",
            "ÍNDICE DE ANEXOS", "INDICE DE ANEXOS",
            "ÍNDICE DE CUADROS", "INDICE DE CUADROS",
            "ÍNDICE DE ILUSTRACIONES", "INDICE DE ILUSTRACIONES",
        }
        for p in self.paragraphs:
            txt = p['text'].strip()
            if not txt:
                continue
            upper = txt.upper()
            # Limpiar relleno de puntos y número de página
            upper_clean = re.sub(r'\s*\.\.+\s*\d+\s*$', '', upper)
            upper_clean = re.sub(r'\s+\d+\s*$', '', upper_clean).strip()

            if upper_clean not in TARGETS:
                continue

            # ¿Es entrada del índice (relleno o número de página)?
            has_filler = '....' in txt
            has_page_num = bool(re.search(r'\s+\d+\s*$', txt))
            is_index_entry = has_filler or has_page_num
            if is_index_entry:
                continue  # Ya se valida en indice_general.py como entrada (12pt)

            # Heurística adicional: si está dentro del rango del Índice General
            # y NO tiene estilo Heading, considerarlo entrada
            in_index_general_range = False
            if (hasattr(self.engine, 'last_index_idx')
                    and self.engine.last_index_idx > 0
                    and p['index'] <= self.engine.last_index_idx):
                style_id = (p.get('style_id') or '').lower()
                is_heading_style = 'heading' in style_id or 'titulo' in style_id or 'ttulo' in style_id
                if not is_heading_style:
                    in_index_general_range = True
            if in_index_general_range:
                continue

            # ── ES TÍTULO DE PÁGINA: validar 16pt, centrado, negrita ──
            size, bold, _, _ = self._get_p_props(p)
            size = size or 0
            align = p.get('alignment', 'left')
            s_after = p.get('spacing_after', 0)
            line_spacing = p.get('line_spacing')

            problems = []
            if size and abs(size - 16) > 0.5:
                problems.append(("tamaño", f"{size}pt", "16pt"))
            if align != 'center':
                problems.append(("alineación", align, "centrado"))
            if not bold:
                problems.append(("estilo", "Normal", "Negrita"))
            if line_spacing and abs(line_spacing - 2.0) > 0.2:
                problems.append(("interlineado", str(line_spacing), "2.0"))
            if abs(s_after - 10.0) > 1.5:
                problems.append(("esp. posterior", f"{s_after}pt", "10pt"))

            section_label = upper_clean
            if problems:
                req = ", ".join(f"{name}: {exp}" for name, _, exp in problems)
                act = ", ".join(f"{name}: {act}" for name, act, _ in problems)
                self._add(
                    "Índice de Tablas/Figuras",
                    f"Título de página: {section_label}",
                    "error",
                    f"El título de página '{section_label}' debe ser 16pt, centrado, "
                    f"negrita, interlineado 2.0, espaciado posterior 10pt según la "
                    f"Guía UNAP pág. 12-14. NOTA: cuando este mismo texto aparece "
                    f"como ENTRADA en el ÍNDICE GENERAL es 12pt — son contextos "
                    f"distintos.",
                    req,
                    act,
                    p_idx=p['index'],
                    p_text=txt,
                )
            else:
                self._add(
                    "Índice de Tablas/Figuras",
                    f"Título de página: {section_label}",
                    "passed",
                    f"El título de página '{section_label}' cumple con el formato "
                    f"16pt centrado negrita.",
                    "16pt, Centrado, Negrita",
                    "Cumple",
                    p_idx=p['index'],
                    p_text=txt,
                )

    def _check_prefix_bold(self, p, prefix_len):
        """Verifica si los primeros `prefix_len` caracteres están en negrita."""
        accumulated = 0
        for r in p.get("runs", []):
            r_txt = r.get("text", "")
            if not r_txt:
                continue
            for _ in r_txt:
                if accumulated < prefix_len:
                    if not r.get("bold"):
                        return False
                    accumulated += 1
                else:
                    return True
        return accumulated >= prefix_len

    def _check_description_bold(self, p, prefix_len):
        """Verifica si la parte DESPUÉS del prefijo (descripción) está en negrita."""
        accumulated = 0
        for r in p.get("runs", []):
            r_txt = r.get("text", "")
            if not r_txt:
                continue
            for _ in r_txt:
                accumulated += 1
                if accumulated > prefix_len + 3:  # +3 para saltar tab/espacios
                    # Verificar runs posteriores
                    if r.get("bold") and r_txt.strip() and not r_txt.strip().isdigit():
                        return True
                    break
        return False

    def _check_description_italic(self, p, prefix_len):
        """
        Verifica si la descripción (post-prefix) tiene cursiva problemática.

        Tolerancias:
        - Hasta 3 palabras en cursiva → aceptado (nombres científicos, términos
          extranjeros como 'in vitro', etc.)
        - TODA la descripción en cursiva → aceptado (título descriptivo APA,
          que va en cursiva por norma)
        - Cursiva parcial con > 3 palabras → flagged como warning

        Retorna True si se debe reportar como problema.
        """
        # Recopilar caracteres de la descripción con su estado de cursiva
        chars_with_italic = []
        accumulated = 0
        for r in p.get("runs", []):
            r_txt = r.get("text", "")
            if not r_txt:
                continue
            is_italic = bool(r.get("italic"))
            for c in r_txt:
                accumulated += 1
                if accumulated > prefix_len + 3:  # +3 para saltar tab/espacios
                    chars_with_italic.append((c, is_italic))

        if not chars_with_italic:
            return False

        # Construir palabras y rastrear si cada una está en cursiva
        words = []
        current_word = ""
        italic_chars_in_word = 0
        total_chars_in_word = 0

        for c, is_italic in chars_with_italic:
            if c.isalnum() or c in "áéíóúñÁÉÍÓÚÑüÜ":
                current_word += c
                total_chars_in_word += 1
                if is_italic:
                    italic_chars_in_word += 1
            else:
                if current_word and total_chars_in_word > 0:
                    word_is_italic = (italic_chars_in_word / total_chars_in_word) >= 0.5
                    words.append((current_word, word_is_italic))
                current_word = ""
                italic_chars_in_word = 0
                total_chars_in_word = 0

        # Última palabra pendiente
        if current_word and total_chars_in_word > 0:
            word_is_italic = (italic_chars_in_word / total_chars_in_word) >= 0.5
            words.append((current_word, word_is_italic))

        if not words:
            return False

        italic_word_count = sum(1 for _, is_it in words if is_it)
        total_word_count = len(words)

        # Si TODA la descripción está en cursiva → título descriptivo APA, aceptable
        if italic_word_count == total_word_count:
            return False

        # Si ≤ 3 palabras en cursiva → probablemente nombres científicos, aceptable
        if italic_word_count <= 3:
            return False

        # Cursiva parcial con > 3 palabras → flagged
        return True

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
