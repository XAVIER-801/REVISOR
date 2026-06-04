"""
tablas.py - Auditoría de Tablas en el cuerpo del documento.

Reglas implementadas:
- Etiqueta (Tabla X): 12pt, Negrita, Izquierda, Sangría según nivel.
- Título descriptivo: 12pt, Cursiva (sin negrita), Izquierda, Sangría según nivel.
- Nota/Fuente: 10pt, Normal (sin cursiva/negrita), con dos puntos, 15pt espaciado posterior.
- Secuencia: Etiqueta → Título (cursiva) → Tabla → Nota/Fuente.
- Encabezado de tabla (primera fila): Centrado, Negrita.
- Interlineado de tabla: 1.0 o 1.5.
"""
import re
from .base_auditor import BaseAuditor


class TablasAuditor(BaseAuditor):

    def audit(self):
        self._audit_table_labels_and_titles()
        self._audit_table_contents()
        self._audit_table_alignment_and_split()

    def _get_expected_indent_for_level(self, level):
        """Retorna sangría esperada para un nivel."""
        if level in [1, 2]:
            return 0.0
        elif level == 3:
            return 1.25
        else:  # 4, 5
            return 2.5

    def _check_prefix_italic(self, p, prefix_len):
        """Verifica si los primeros `prefix_len` caracteres del párrafo están en cursiva."""
        accumulated = 0
        for r in p.get("runs", []):
            r_txt = r.get("text", "")
            if not r_txt:
                continue
            for _ in r_txt:
                if accumulated < prefix_len:
                    if not r.get("italic"):
                        return False
                    accumulated += 1
                else:
                    return True
        return accumulated >= prefix_len

    def _audit_table_labels_and_titles(self):
        """Audita etiquetas, títulos y notas/fuentes de tablas."""
        for i, p in enumerate(self.paragraphs):
            txt = p['text'].strip()
            sec_upper = p.get('section', '').upper()
            if any(k in sec_upper for k in ['ÍNDICE DE TABLAS', 'INDICE DE TABLAS',
                                            'ÍNDICE GENERAL', 'INDICE GENERAL',
                                            'TABLA DE CONTENIDOS', 'TABLA DE CONTENIDO']):
                continue

            upper = txt.upper()
            align = p.get('alignment', 'left')
            l_cm = round(p.get('indent_left') or 0, 2)

            # ═══ NIVEL CONTEXTUAL ═══
            # Encuentra el nivel del ÚLTIMO TÍTULO antes de esta tabla.
            # La sangría de la tabla debe coincidir con la del título contextual.
            # (Guía UNAP pág. 21: "alineadas con el margen izquierdo del nivel del título al que pertenecen")
            context_level = self._find_context_level(i)
            level = context_level
            exp_l_cm = self._get_expected_indent_for_level(level)

            is_table_label = bool(re.match(r'^TABLA\s+\d+', upper))

            if is_table_label and p.get('in_table'):
                continue

            if is_table_label:
                label_match = re.match(r'^(Tabla\s+\d+\.?\s*)(.*)', txt, re.IGNORECASE)
                label_text = label_match.group(1).strip() if label_match else txt
                title_in_same_para = label_match.group(2).strip() if label_match else ""

                # NUEVO: Validar tamaño de fuente (DEBE ser 12pt)
                # NOTA: style_resolver ya retorna size en puntos enteros (NO half-points)
                font_size = 0
                if p.get('runs'):
                    font_size = p['runs'][0].get('size', 0)

                if font_size > 0 and abs(font_size - 12) > 0.5:
                    self._add("Tablas", f"Tamaño Etiqueta: {label_text}", "error",
                             f"La etiqueta de Tabla debe estar en 12 puntos. Hallado: {font_size}pt.",
                             "12pt", f"{font_size}pt", p_idx=p['index'], p_text=txt)

                # NUEVO: Validar espaciado (anterior 0pt, posterior 0pt)
                s_before = p.get('spacing_before', 0)
                s_after = p.get('spacing_after', 0)
                if s_before > 1.0:
                    self._add("Tablas", f"Espaciado Anterior Etiqueta: {label_text}", "error",
                             "La etiqueta de Tabla debe tener espaciado anterior de 0pt.",
                             "0pt", f"{s_before}pt", p_idx=p['index'], p_text=txt)
                if s_after > 1.0:
                    self._add("Tablas", f"Espaciado Posterior Etiqueta: {label_text}", "error",
                             "La etiqueta de Tabla debe tener espaciado posterior de 0pt.",
                             "0pt", f"{s_after}pt", p_idx=p['index'], p_text=txt)

                # NUEVO: Validar interlineado (DEBE ser 2.0)
                line_spacing = p.get('line_spacing')
                if line_spacing is not None and abs(line_spacing - 2.0) > 0.2:
                    self._add("Tablas", f"Interlineado Etiqueta: {label_text}", "error",
                             "La etiqueta de Tabla debe tener interlineado 2.0.",
                             "2.0", str(line_spacing), p_idx=p['index'], p_text=txt)

                # 1. Alineación y Sangría
                if align != 'left' and align != 'both':
                    self._add("Tablas", f"Alineación Etiqueta: {label_text}", "error",
                             "La etiqueta de Tabla debe estar alineada a la Izquierda.", "Izquierda", align, p_idx=p['index'], p_text=txt)

                if abs(l_cm - exp_l_cm) > 0.1:
                    self._add("Tablas", f"Sangría Etiqueta: {label_text}", "warning",
                             f"La etiqueta de Tabla debe tener la misma sangría que el título de Nivel {level} ({exp_l_cm}cm).",
                             f"Izq {exp_l_cm}cm", f"Izq {l_cm}cm", p_idx=p['index'], p_text=txt)

                # 2. Estilo (Negrita)
                is_bold = any(r.get('bold') for r in p.get('runs', []))
                if not is_bold:
                    self._add("Tablas", f"Estilo Etiqueta: {label_text}", "error",
                             "Las etiquetas de Tabla deben estar en Negrita.", "Negrita", "Normal", p_idx=p['index'], p_text=txt)

                # 3. Título descriptivo
                if title_in_same_para:
                    label_len = len(label_match.group(1)) if label_match else len(txt)
                    title_runs = []
                    char_count = 0
                    for run in p.get('runs', []):
                        run_text = run.get('text', '')
                        if char_count + len(run_text) > label_len:
                            title_runs.append(run)
                        char_count += len(run_text)

                    if title_runs:
                        is_italic = any(r.get('italic') for r in title_runs)
                        is_title_bold = any(r.get('bold') for r in title_runs)
                        if not is_italic or is_title_bold:
                            req_list = []
                            act_list = []
                            if not is_italic:
                                req_list.append("Cursiva")
                                act_list.append("Normal")
                            if is_title_bold:
                                req_list.append("Sin Negrita")
                                act_list.append("Negrita")
                            self._add("Tablas", f"Estilo Título: {title_in_same_para[:25]}...", "error",
                                     "El título descriptivo de la Tabla debe estar en CURSIVA y SIN NEGRITA.",
                                     ", ".join(req_list), ", ".join(act_list), p_idx=p['index'], p_text=txt)
                else:
                    # Buscar el próximo párrafo no vacío después de la etiqueta
                    next_idx = -1
                    for j in range(i + 1, len(self.paragraphs)):
                        if self.paragraphs[j]['text'].strip():
                            next_idx = j
                            break

                    if next_idx == -1:
                        self._add("Tablas", f"Secuencia: Título de {label_text}", "error",
                                 f"Falta el título descriptivo de la tabla '{label_text}'. El título debe estar FUERA de la tabla, arriba de ella, y en CURSIVA.",
                                 "Título (Cursiva) fuera de la tabla", "No se encontró título antes de la tabla", p_idx=p['index'], p_text=txt)
                    else:
                        next_p = self.paragraphs[next_idx]
                        next_upper = next_p['text'].strip().upper()

                        if next_p.get('in_table') or next_upper.startswith("NOTA") or next_upper.startswith("FUENTE"):
                            self._add("Tablas", f"Secuencia: Título de {label_text}", "error",
                                     f"Falta el título descriptivo de la tabla '{label_text}'. El título debe estar FUERA de la tabla, arriba de ella, y en CURSIVA.",
                                     "Título (Cursiva) fuera de la tabla", "No se encontró título antes de la tabla", p_idx=p['index'], p_text=txt)
                        else:
                            is_italic = any(r.get('italic') for r in next_p.get('runs', []))
                            is_next_bold = any(r.get('bold') for r in next_p.get('runs', []))
                            n_align = next_p.get('alignment', 'left')
                            if (next_p.get('indent_left') or 0) > 10:
                                n_l_cm = round(next_p.get('indent_left') / 567.0, 2)
                            else:
                                n_l_cm = round(next_p.get('indent_left') or 0, 2)

                            if (not is_italic) or is_next_bold:
                                req_list = []
                                act_list = []
                                if not is_italic:
                                    req_list.append("Cursiva")
                                    act_list.append("Normal")
                                if is_next_bold:
                                    req_list.append("Sin Negrita")
                                    act_list.append("Negrita")
                                self._add("Tablas", f"Estilo Título: {next_p['text'][:20]}...", "error",
                                         "El título descriptivo de la Tabla debe estar en CURSIVA y SIN NEGRITA.",
                                         ", ".join(req_list), ", ".join(act_list), p_idx=next_p['index'], p_text=next_p['text'])

                            # NUEVO: Validar tamaño de fuente del título (12pt)
                            n_font_size = 0
                            if next_p.get('runs'):
                                n_font_size = next_p['runs'][0].get('size', 0)
                            if n_font_size > 0 and abs(n_font_size - 12) > 0.5:
                                self._add("Tablas", f"Tamaño Título: {next_p['text'][:20]}...", "error",
                                         f"El título de Tabla debe estar en 12 puntos. Hallado: {n_font_size}pt.",
                                         "12pt", f"{n_font_size}pt", p_idx=next_p['index'], p_text=next_p['text'])

                            # NUEVO: Validar espaciado del título (anterior 0pt, posterior 0pt)
                            n_s_before = next_p.get('spacing_before', 0)
                            n_s_after = next_p.get('spacing_after', 0)
                            if n_s_before > 1.0:
                                self._add("Tablas", f"Espaciado Anterior Título: {next_p['text'][:20]}...", "error",
                                         "El título de Tabla debe tener espaciado anterior de 0pt.",
                                         "0pt", f"{n_s_before}pt", p_idx=next_p['index'], p_text=next_p['text'])
                            if n_s_after > 1.0:
                                self._add("Tablas", f"Espaciado Posterior Título: {next_p['text'][:20]}...", "error",
                                         "El título de Tabla debe tener espaciado posterior de 0pt.",
                                         "0pt", f"{n_s_after}pt", p_idx=next_p['index'], p_text=next_p['text'])

                            # NUEVO: Validar interlineado del título (2.0)
                            n_line_spacing = next_p.get('line_spacing')
                            if n_line_spacing is not None and abs(n_line_spacing - 2.0) > 0.2:
                                self._add("Tablas", f"Interlineado Título: {next_p['text'][:20]}...", "error",
                                         "El título de Tabla debe tener interlineado 2.0.",
                                         "2.0", str(n_line_spacing), p_idx=next_p['index'], p_text=next_p['text'])

                            if n_align != 'left' and n_align != 'both':
                                self._add("Tablas", f"Alineación Título: {next_p['text'][:20]}...", "error",
                                         "El título descriptivo de la Tabla debe estar alineado a la Izquierda.", "Izquierda", n_align, p_idx=next_p['index'], p_text=next_p['text'])

                            if abs(n_l_cm - exp_l_cm) > 0.1:
                                next_level = next_p.get('body_level') or next_p.get('level') or 1
                                self._add("Tablas", f"Sangría Título: {next_p['text'][:20]}...", "warning",
                                         f"El título descriptivo debe tener la misma sangría que el título de Nivel {next_level} ({exp_l_cm}cm).",
                                         f"Izq {exp_l_cm}cm", f"Izq {n_l_cm}cm", p_idx=next_p['index'], p_text=next_p['text'])

                # 3.b: Verificar presencia de Nota o Fuente para la Tabla
                encontro_nota_fuente = False
                for j in range(i + 1, min(i + 150, len(self.paragraphs))):
                    p_next = self.paragraphs[j]
                    next_txt = p_next['text'].strip()
                    next_upper = next_txt.upper()

                    if (re.match(r'^TABLA\s+\d+', next_upper) or
                        re.match(r'^FIGURA\s+\d+', next_upper) or
                        re.match(r'^CAP[ÍI]TULO\s+(I|V|X|L|C|[0-9]+)', next_upper) or
                        re.match(r'^\d+(\.\d+)*\.?\s+[A-Z]', next_txt) or
                        next_upper in ["INTRODUCCION", "RESUMEN", "ABSTRACT", "CONCLUSIONES", "RECOMENDACIONES", "REFERENCIAS BIBLIOGRAFICAS", "ANEXOS"]):
                        break

                    if next_upper.startswith("NOTA") or next_upper.startswith("FUENTE"):
                        encontro_nota_fuente = True
                        break

                if not encontro_nota_fuente:
                    self._add("Tablas", f"Nota/Fuente: {label_text}", "error",
                             f"No se encontró la nota o fuente obligatoria para la tabla '{label_text}'. Toda tabla debe incluir su correspondiente Nota o Fuente debajo.",
                             "Nota: o Fuente: debajo", "Ausente", p_idx=p['index'], p_text=txt)

            # 4. Detectar "Nota" o "Fuente" y verificar formato (Solo si corresponde a una tabla previa)
            if upper.startswith("NOTA") or upper.startswith("FUENTE"):
                # Verificar si el elemento previo más cercano con etiqueta era Tabla o Figura
                es_de_tabla = True
                for k in range(i - 1, max(-1, i - 150), -1):
                    prev_txt = self.paragraphs[k]['text'].strip().upper()
                    if prev_txt.startswith("TABLA"):
                        es_de_tabla = True
                        break
                    elif prev_txt.startswith("FIGURA"):
                        es_de_tabla = False
                        break

                if es_de_tabla:
                    first_word = txt.split(' ', 1)[0]
                    has_colon = first_word.endswith(':')

                    if not has_colon:
                        self._add("Tablas", f"Sintaxis Nota/Fuente: {txt[:15]}...", "error",
                                 "Las palabras 'Nota' o 'Fuente' deben terminar obligatoriamente con dos puntos (:).",
                                 "Nota: o Fuente:", first_word, p_idx=p['index'], p_text=txt)

                    # REGLA ACTUALIZADA: "Nota:" / "Fuente:" debe estar en CURSIVA
                    # (cambio respecto a versiones anteriores) y con dos puntos.
                    # El BOLD sigue prohibido SOLO para la palabra "Nota:"/"Fuente:" misma.
                    # El resto del párrafo puede tener el formato que el estudiante quiera.

                    # Verificar la palabra inicial "Nota:" / "Fuente:" específicamente
                    label_word = txt.split(' ', 1)[0]  # "Nota:" o "Fuente:"
                    label_len = len(label_word)
                    label_is_italic = self._check_prefix_italic(p, label_len)

                    # Verificar si la palabra inicial está en negrita
                    label_is_bold = False
                    accumulated = 0
                    for r in p.get('runs', []):
                        r_txt = r.get('text', '')
                        if not r_txt:
                            continue
                        for _ in r_txt:
                            if accumulated < label_len:
                                if r.get('bold'):
                                    label_is_bold = True
                                    break
                                accumulated += 1
                            else:
                                break
                        if label_is_bold or accumulated >= label_len:
                            break

                    if not label_is_italic or label_is_bold:
                        req_list = []
                        act_list = []
                        if not label_is_italic:
                            req_list.append("Cursiva")
                            act_list.append("Normal")
                        if label_is_bold:
                            req_list.append("Sin negrita")
                            act_list.append("Negrita")
                        self._add("Tablas", f"Estilo Nota/Fuente: {txt[:15]}...", "error",
                                 "La palabra 'Nota:' o 'Fuente:' DEBE estar en CURSIVA y "
                                 "terminada con dos puntos (:). NO debe estar en negrita.",
                                 ", ".join(req_list), ", ".join(act_list), p_idx=p['index'], p_text=txt)

                    size = p['runs'][0].get('size', 0) if p.get('runs') else 0
                    if size != 10 and size != 0:
                        self._add("Tablas", f"Tamaño Nota: {txt[:20]}", "error",
                                 "Las notas o fuentes de tablas deben tener tamaño 10pt.", "10pt", f"{size}pt", p_idx=p['index'], p_text=txt)

                    # NUEVO: Validar espaciado anterior (0pt)
                    s_before = p.get('spacing_before', 0)
                    if s_before > 1.0:
                        self._add("Tablas", f"Espaciado Anterior Nota: {txt[:15]}...", "error",
                                 "La Nota o Fuente debe tener espaciado anterior de 0pt.",
                                 "0pt", f"{s_before}pt", p_idx=p['index'], p_text=txt)

                    # NUEVO Y CRÍTICO: Validar espaciado posterior (15pt OBLIGATORIO)
                    s_after = p.get('spacing_after', 0)
                    if abs(s_after - 15.0) > 2.0:
                        self._add("Tablas", f"Espaciado Posterior Nota: {txt[:15]}...", "error",
                                 "La Nota o Fuente DEBE tener espaciado posterior de 15pt. Este es un requisito obligatorio.",
                                 "15pt", f"{s_after}pt", p_idx=p['index'], p_text=txt)

                    # NUEVO: Validar interlineado (1.5)
                    line_spacing = p.get('line_spacing')
                    if line_spacing is not None and abs(line_spacing - 1.5) > 0.2:
                        self._add("Tablas", f"Interlineado Nota: {txt[:15]}...", "warning",
                                 "La Nota o Fuente debe tener interlineado 1.5.",
                                 "1.5", str(line_spacing), p_idx=p['index'], p_text=txt)

                    # Para la Nota/Fuente, usar también el nivel contextual del último título
                    note_level = self._find_context_level(i)
                    note_exp_l_cm = self._get_expected_indent_for_level(note_level)
                    if abs(l_cm - note_exp_l_cm) > 0.1:
                        self._add("Tablas", f"Sangría Nota: {txt[:15]}", "warning",
                                 f"La nota/fuente de la tabla debe tener la misma sangría que el título de Nivel {note_level} ({note_exp_l_cm}cm).",
                                 f"Izq {note_exp_l_cm}cm", f"Izq {l_cm}cm", p_idx=p['index'], p_text=txt)

    def _audit_table_alignment_and_split(self):
        """
        Valida a nivel de TABLA completa (no de párrafos internos):
        1. La tabla debe estar alineada a la IZQUIERDA (no centrada).
           La sangría de su título es la que la posiciona según el nivel contextual.
        2. Si la tabla se divide entre dos páginas (cruza un page break),
           la primera fila debe estar marcada como tblHeader para repetirse
           como encabezado en la siguiente página.
        """
        tables_info = getattr(self.engine, 'tables_info', {}) or {}
        if not tables_info:
            return

        # Para localizar la tabla en el reporte, usamos el primer párrafo que
        # pertenezca a esa tabla (tiene tbl_id) y reportamos el error ahí.
        tbl_to_first_p = {}
        for i, p in enumerate(self.paragraphs):
            tbl_id = p.get('tbl_id')
            if tbl_id is not None and tbl_id not in tbl_to_first_p:
                tbl_to_first_p[tbl_id] = (i, p)

        for tbl_id, info in tables_info.items():
            first_entry = tbl_to_first_p.get(tbl_id)
            if not first_entry:
                continue
            first_idx, first_p = first_entry
            p_idx = first_p['index']
            ref_text = info.get('first_cell_text') or first_p['text'].strip()[:30]
            label = f"Tabla en pág. {first_p.get('estimated_page', '?')}"
            if ref_text:
                label += f" ({ref_text[:25]})"

            # ═══ Regla 1: Alineación izquierda ═══
            jc = info.get('jc', 'left')
            if jc != 'left':
                self._add(
                    "Tablas",
                    f"Alineación de Tabla: {label}",
                    "error",
                    "La tabla en sí (el cuadro completo) debe estar alineada a la IZQUIERDA. "
                    "La sangría de su título es la que la posiciona horizontalmente según el nivel "
                    "del título contextual. No debe usarse alineación centrada para la tabla.",
                    "Alineación: Izquierda",
                    f"Alineación: {jc.capitalize()}",
                    p_idx=p_idx,
                    p_text=ref_text,
                )

            # ═══ Regla 2: Tabla dividida en 2 páginas → encabezado repetido ═══
            if info.get('crosses_pages', False):
                if not info.get('first_row_has_header', False):
                    self._add(
                        "Tablas",
                        f"Encabezado Repetido (Tabla dividida): {label}",
                        "error",
                        "La tabla se extiende a más de una página, pero la primera fila "
                        "NO está marcada como encabezado repetido. Según la Guía UNAP "
                        "(pág. 21), 'si la tabla se extiende a lo largo de dos hojas, es "
                        "necesario incluir el encabezado de la tabla en ambas páginas'. "
                        "En Word: clic derecho sobre la primera fila → Propiedades de tabla "
                        "→ Fila → marcar 'Repetir como fila de encabezado en cada página'.",
                        "Primera fila con repetición de encabezado activada",
                        "Encabezado NO se repite en página siguiente",
                        p_idx=p_idx,
                        p_text=ref_text,
                    )
                else:
                    self._add(
                        "Tablas",
                        f"Encabezado Repetido (Tabla dividida): {label}",
                        "passed",
                        "La tabla cruza páginas y su primera fila está correctamente "
                        "configurada para repetirse como encabezado en cada página.",
                        "Encabezado repetido en páginas siguientes",
                        "Configurado correctamente",
                        p_idx=p_idx,
                        p_text=ref_text,
                    )

    def _audit_table_contents(self):
        """
        Audita el contenido dentro de las tablas con reportes CONSOLIDADOS por tabla.

        Reglas (Guía UNAP pág. 21):
        - Las filas de encabezado (pueden ser múltiples si hay celdas combinadas) en negrita y centradas
        - El resto de filas: NO debe estar en negrita
        - Interlineado interno: 1.0 o 1.5

        Mejora: reconoce encabezados multi-fila (con celdas combinadas vertical
        u horizontalmente). No reporta falsos positivos por negritas en filas
        que forman parte del encabezado visual combinado.
        """
        # Agrupar párrafos de tabla por tabla a la que pertenecen
        headers_by_table = {}    # tbl_id → lista de párrafos del encabezado
        content_by_table = {}    # tbl_id → lista de párrafos de contenido
        table_first_p = {}       # tbl_id → primer párrafo (para reportar ubicación)

        for p in self.paragraphs:
            if not p.get('in_table'):
                continue
            txt = p['text'].strip()
            if not txt:
                continue
            tbl_id = p.get('tbl_id')
            if not tbl_id:
                continue
            if tbl_id not in table_first_p:
                table_first_p[tbl_id] = p
            if p.get('is_table_header'):
                headers_by_table.setdefault(tbl_id, []).append(p)
            else:
                content_by_table.setdefault(tbl_id, []).append(p)

        # ═══ VALIDAR ENCABEZADOS: un reporte consolidado por tabla ═══
        for tbl_id, header_paragraphs in headers_by_table.items():
            non_bold_cells = []
            non_center_cells = []

            for p in header_paragraphs:
                # Threshold más laxo (0.3): basta con que ~30% de los caracteres
                # alfanuméricos estén en negrita. Evita falsos negativos cuando
                # solo una palabra de varias está marcada.
                has_xml_bold = self._is_meaningfully_bold(p, threshold=0.3)
                # Fallback: si todo está en MAYÚSCULAS, también lo aceptamos como
                # "encabezado destacado" (caso común en tablas científicas)
                txt_letters = re.sub(
                    r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ]', '', p['text']
                )
                has_caps_bold = (
                    len(txt_letters) > 1
                    and txt_letters == txt_letters.upper()
                )
                is_bold = has_xml_bold or has_caps_bold

                align = p.get('alignment', 'left')

                if not is_bold:
                    non_bold_cells.append(p)
                if align != 'center':
                    non_center_cells.append(p)

            ref = table_first_p[tbl_id]
            ref_text = ref['text'][:30] if ref['text'] else "Tabla"
            page = ref.get('estimated_page', '?')

            # Un solo reporte por tabla cuando hay celdas sin negrita
            if non_bold_cells:
                examples = ", ".join(
                    f"\"{c['text'].strip()[:25]}\""
                    for c in non_bold_cells[:3]
                )
                count = len(non_bold_cells)
                self._add(
                    "Tablas",
                    f"Encabezado sin negrita (pág. {page}, {count} celda{'s' if count != 1 else ''})",
                    "error",
                    f"La tabla en la página {page} tiene "
                    f"{count} celda{'s' if count != 1 else ''} de encabezado sin negrita. Según la "
                    f"Guía UNAP, todo el contenido de las celdas del encabezado "
                    f"debe estar en negrita. Ejemplo{'s' if count > 1 else ''}: {examples}.",
                    "Todas las celdas del encabezado en negrita",
                    f"{count} celda{'s' if count != 1 else ''} sin negrita",
                    p_idx=non_bold_cells[0]['index'],
                    p_text=non_bold_cells[0]['text'][:60],
                )

            # Un solo reporte por tabla cuando hay celdas sin centrar
            if non_center_cells:
                count = len(non_center_cells)
                self._add(
                    "Tablas",
                    f"Encabezado sin centrar (pág. {page}, {count} celda{'s' if count != 1 else ''})",
                    "error",
                    f"La tabla en la página {page} tiene "
                    f"{count} celda{'s' if count != 1 else ''} de encabezado sin centrar. Según la "
                    f"Guía UNAP, todo el contenido del encabezado debe estar centrado.",
                    "Todas las celdas del encabezado centradas",
                    f"{count} celda{'s' if count != 1 else ''} sin centrar",
                    p_idx=non_center_cells[0]['index'],
                    p_text=non_center_cells[0]['text'][:60],
                )

        # ═══ VALIDAR CONTENIDO: un reporte consolidado por tabla ═══
        for tbl_id, content_paragraphs in content_by_table.items():
            bold_content_cells = [
                p for p in content_paragraphs
                if self._is_meaningfully_bold(p, threshold=0.5)
            ]
            if bold_content_cells:
                ref = table_first_p[tbl_id]
                page = ref.get('estimated_page', '?')
                count = len(bold_content_cells)
                examples = ", ".join(
                    f"\"{c['text'].strip()[:25]}\""
                    for c in bold_content_cells[:3]
                )
                self._add(
                    "Tablas",
                    f"Contenido con negrita (pág. {page}, {count} celda{'s' if count != 1 else ''})",
                    "warning",
                    f"La tabla en la página {page} tiene {count} celda{'s' if count != 1 else ''} "
                    f"de contenido en negrita. Solo las filas del encabezado deben estar "
                    f"en negrita. Las demás filas deben estar en estilo Normal. "
                    f"Ejemplo{'s' if count > 1 else ''}: {examples}.",
                    "Contenido en estilo Normal (sin negrita)",
                    f"{count} celda{'s' if count != 1 else ''} en negrita",
                    p_idx=bold_content_cells[0]['index'],
                    p_text=bold_content_cells[0]['text'][:60],
                )

        # ═══ INTERLINEADO INTERNO: un reporte por tabla ═══
        all_table_paragraphs = {}
        for p in self.paragraphs:
            if not p.get('in_table') or not p['text'].strip():
                continue
            tbl_id = p.get('tbl_id')
            if tbl_id:
                all_table_paragraphs.setdefault(tbl_id, []).append(p)

        for tbl_id, table_paragraphs in all_table_paragraphs.items():
            wrong_spacing = []
            for p in table_paragraphs:
                line_spacing = p.get('line_spacing', 1.0) or 1.0
                if abs(line_spacing - 1.0) > 0.2 and abs(line_spacing - 1.5) > 0.2:
                    wrong_spacing.append(p)
            if wrong_spacing:
                ref = table_first_p.get(tbl_id, wrong_spacing[0])
                page = ref.get('estimated_page', '?')
                count = len(wrong_spacing)
                found_spacing = wrong_spacing[0].get('line_spacing', '?')
                self._add(
                    "Tablas",
                    f"Interlineado tabla (pág. {page})",
                    "warning",
                    f"La tabla en la página {page} tiene {count} celda{'s' if count != 1 else ''} "
                    f"con interlineado incorrecto. El contenido de la tabla debe tener "
                    f"interlineado 1.0 o 1.5 (Guía UNAP pág. 21).",
                    "1.0 o 1.5",
                    str(found_spacing),
                    p_idx=wrong_spacing[0]['index'],
                    p_text=wrong_spacing[0]['text'][:60],
                )
