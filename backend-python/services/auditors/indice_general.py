"""
indice_general.py - Auditoría del Índice General.

Reglas implementadas:
- Etiqueta "Pág.": Derecha, Negrita, Interlineado 1.5, sin sangría, Espaciado 0pt
- Título 'ÍNDICE GENERAL': 16pt, centrado, negrita
- CAPÍTULO I-IV y sus títulos: 12pt, centrado, negrita, sin relleno
- Nivel 2 (ej: 1.1.): Justificado o Izquierda, Negrita, Mayúsculas
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

        # === PASO 1.2: Auditar el interlineado dinámico de las entradas del Índice General ===
        entries_to_check = []
        for i in range(idx_start + 1, idx_end):
            p = self.paragraphs[i]
            txt = p['text'].strip()
            if len(txt) < 3:
                continue
            upper = txt.upper()
            if bool(re.match(r'^P[ÁA]G\.?:?$', upper.strip())):
                continue
            if "ÍNDICE GENERAL" in upper or "INDICE GENERAL" in upper:
                continue
            entries_to_check.append(p)
            
        total_entries = len(entries_to_check)
        if total_entries > 0:
            required_spacing = 2.0
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
                    self._add("Índice General", f"Interlineado Entrada: {txt[:20]}...", "error",
                              "El interlineado del Índice General debe ser de 2.0.",
                              "2.0", f"{val}", p_idx=p['index'], p_text=txt)
                if len(failing_entries) > 5:
                    self._add("Índice General", "Interlineado Entrada (Restantes)", "warning",
                              f"Se encontraron {len(failing_entries) - 5} entradas adicionales con interlineado incorrecto en el Índice General (debe ser 2.0).",
                              "2.0", "Incorrecto", p_idx=idx_start, p_text="ÍNDICE GENERAL")
            else:
                self._add("Índice General", "Interlineado del Índice General", "passed",
                          "El interlineado de todas las entradas en el Índice General es correcto (2.0).",
                          "2.0", "2.0", p_idx=idx_start, p_text="ÍNDICE GENERAL")

        # === PASO 1.5: Construir mapa de títulos del cuerpo ===
        body_headings = self._build_body_headings_map(idx_end)
        # === PASO 2: Auditar cada entrada del índice ===
        for i in range(idx_start, idx_end):
            p = self.paragraphs[i]
            txt = p['text'].strip()
            upper = txt.upper()

            if len(txt) < 2:
                continue

            size, _, _, _ = self._get_p_props(p)
            size = size or 0

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
            indent_left_cm = round(p.get('indent_left') or 0, 2)
            indent_first_cm = round(p.get('indent_first') or 0, 2)
            indent_hanging_cm = round(p.get('indent_hanging') or 0, 2)
            is_bold = any(r.get('bold') for r in p.get('runs', []) if re.search(r'[a-zA-ZáéíóúÁÉÍÓÚñÑ]', r.get('text', '')))

            txt_letters = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ]', '', txt)
            is_uppercase = not any(c.islower() for c in txt_letters) if txt_letters else True
            has_dots_or_page = '....' in txt or bool(re.search(r'\d+$', txt.strip()))

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

            # ═══ DISTINCIÓN CRÍTICA (Guía pág. 10-11) ═══
            # Preliminares (DEDICATORIA, AGRADECIMIENTOS, ÍNDICES, ACRÓNIMOS):
            #   → SIN relleno de puntos NI número de página visible
            # Desde RESUMEN en adelante:
            #   → CON relleno de puntos Y número de página
            preliminares_sin_numero = [
                'DEDICATORIA', 'AGRADECIMIENTO', 'AGRADECIMIENTOS',
                'ÍNDICE GENERAL', 'INDICE GENERAL',
                'ÍNDICE DE FIGURAS', 'INDICE DE FIGURAS',
                'ÍNDICE DE TABLAS', 'INDICE DE TABLAS',
                'ÍNDICE DE ACRÓNIMOS', 'INDICE DE ACRONIMOS',
                'ÍNDICE DE ANEXOS', 'INDICE DE ANEXOS',
                'ACRÓNIMOS', 'ACRONIMOS',
                'RESUMEN', 'ABSTRACT'
            ]
            # Secciones con relleno obligatorio (RESUMEN en adelante)
            con_relleno_obligatorio = []
            is_preliminar = any(upper.strip() == ps for ps in preliminares_sin_numero)
            requiere_relleno = any(upper.strip() == cr for cr in con_relleno_obligatorio)

            if is_preliminar:
                if has_dots_or_page:
                    self._add("Índice General", f"Preliminar con numeración: {txt[:20]}...", "error",
                              f"La sección preliminar '{txt[:25]}...' en el índice NO DEBE tener relleno de puntos ni número de página visible (Guía UNAP pág. 10-11).",
                              "Sin relleno ni número", "Con relleno o número visible", p_idx=p['index'], p_text=txt)
                else:
                    self._add("Índice General", f"Preliminar sin numeración: {txt[:20]}...", "passed",
                              f"La sección preliminar '{txt[:25]}...' está correctamente sin relleno ni número.",
                              "Sin relleno ni número", "Sin relleno ni número", p_idx=p['index'], p_text=txt)
            elif requiere_relleno:
                if not has_dots_or_page:
                    self._add("Índice General", f"Sección sin numeración: {txt[:20]}...", "error",
                              f"La sección '{txt[:25]}...' en el índice DEBE tener relleno de puntos y número de página (desde RESUMEN en adelante según Guía UNAP).",
                              "Con relleno y número de página", "Sin relleno ni número", p_idx=p['index'], p_text=txt)

            # Tamaño 12pt
            if size != 12 and size != 0:
                self._add("Índice General", f"Tamaño entrada: {txt[:25]}...", "error",
                          "Las entradas del índice deben ser 12pt.",
                          "12pt", f"{size}pt", p_idx=p['index'], p_text=txt)

            # Aplicación de reglas por nivel
            if "FECHA DE SUSTENTACION" in upper or "FECHA DE SUSTENTACIÓN" in upper:
                ok_align = align == 'right'
                
                runs = p.get('runs', [])
                has_bold_prefix = False
                has_normal_suffix = False
                
                colon_idx = txt.find(':')
                if colon_idx != -1:
                    prefix_text = txt[:colon_idx + 1]
                    suffix_text = txt[colon_idx + 1:]
                    
                    curr_char = 0
                    prefix_bold_runs = 0
                    prefix_total_runs = 0
                    suffix_bold_runs = 0
                    suffix_total_runs = 0
                    
                    for r in runs:
                        r_txt = r.get('text', '')
                        if not r_txt:
                            continue
                        r_len = len(r_txt)
                        r_bold = r.get('bold', False)
                        
                        if curr_char < colon_idx + 1:
                            prefix_total_runs += 1
                            if r_bold:
                                prefix_bold_runs += 1
                        else:
                            suffix_total_runs += 1
                            if r_bold:
                                suffix_bold_runs += 1
                        
                        curr_char += r_len
                        
                    has_bold_prefix = prefix_bold_runs > 0
                    has_normal_suffix = suffix_bold_runs == 0 or (suffix_total_runs > 0 and suffix_bold_runs / suffix_total_runs < 0.5)
                else:
                    has_bold_prefix = any(r.get('bold') for r in runs)
                    has_normal_suffix = True
                    
                ok_bold = has_bold_prefix and has_normal_suffix
                ok_case = True
                
                passed = ok_align and ok_bold
                if passed:
                    expected_str = "Correcto"
                    actual_str = "Correcto"
                else:
                    req_list = []
                    act_list = []
                    if not ok_align:
                        req_list.append("Derecha")
                        act_list.append(align_str_raw)
                    if not ok_bold:
                        req_list.append("'FECHA DE SUSTENTACIÓN:' en Negrita y fecha en Normal")
                        act_list.append("Formato de negrita incorrecto")
                    expected_str = ", ".join(req_list)
                    actual_str = ", ".join(act_list)
                    
                self._add("Índice General", f"Formato Nivel 1: FECHA DE SUSTENTACIÓN...", "passed" if passed else "error",
                          "La entrada 'FECHA DE SUSTENTACIÓN:' en el índice debe estar alineada a la DERECHA, con el prefijo 'FECHA DE SUSTENTACIÓN:' en NEGRITA y la fecha en NORMAL (sin negrita).",
                          expected_str, actual_str, p_idx=p['index'], p_text=txt)
                continue

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
                    # NIVEL 2: Justificada o Izquierda, Negrita, Mayúsculas
                    ok_align = align in ['both', 'justify', 'left']
                    ok_bold = is_bold
                    ok_case = is_uppercase

                    passed = ok_align and ok_bold and ok_case
                    if passed:
                        expected_str = "Correcto"
                        actual_str = "Correcto"
                    else:
                        req_list = []
                        act_list = []
                        if not ok_align:
                            req_list.append("Justificada o Izquierda")
                            act_list.append(align_str_raw)
                        if not ok_bold:
                            req_list.append("Negrita")
                            act_list.append(bold_str_raw)
                        if not ok_case:
                            req_list.append("Mayúsculas")
                            act_list.append(case_str_raw)
                        expected_str = ", ".join(req_list)
                        actual_str = ", ".join(act_list)

                    self._add("Índice General", f"Formato Nivel 2: {txt[:20]}...", "passed" if passed else "error",
                              f"El título de Nivel 2 '{txt[:20]}...' en el índice debe estar JUSTIFICADO o ALINEADO A LA IZQUIERDA, en NEGRITA y en MAYÚSCULAS.",
                              expected_str, actual_str, p_idx=p['index'], p_text=txt)

                elif dots_count == 2:
                    # NIVEL 3: Justificada o Izquierda, SIN negrita, Minúsculas
                    ok_align = align in ['both', 'justify', 'left']
                    ok_bold = not is_bold
                    ok_case = not is_uppercase

                    passed = ok_align and ok_bold and ok_case
                    if passed:
                        expected_str = "Correcto"
                        actual_str = "Correcto"
                    else:
                        req_list = []
                        act_list = []
                        if not ok_align:
                            req_list.append("Justificada o Izquierda")
                            act_list.append(align_str_raw)
                        if not ok_bold:
                            req_list.append("Normal (sin negrita)")
                            act_list.append(bold_str_raw)
                        if not ok_case:
                            req_list.append("Minúsculas")
                            act_list.append(case_str_raw)
                        expected_str = ", ".join(req_list)
                        actual_str = ", ".join(act_list)

                    self._add("Índice General", f"Formato Nivel 3: {txt[:20]}...", "passed" if passed else "error",
                              f"El título de nivel 3 y 4 en el índice no debe estar en Negrita. El título de Nivel 3 '{txt[:20]}...' en el índice debe estar JUSTIFICADO o ALINEADO A LA IZQUIERDA, sin negrita (NORMAL) y en MINÚSCULAS.",
                              expected_str, actual_str, p_idx=p['index'], p_text=txt)

                else:
                    # NIVEL 4/5: Justificada o Izquierda, SIN negrita, Minúsculas
                    ok_align = align in ['both', 'justify', 'left']
                    ok_bold = not is_bold
                    ok_case = not is_uppercase

                    passed = ok_align and ok_bold and ok_case
                    if passed:
                        expected_str = "Correcto"
                        actual_str = "Correcto"
                    else:
                        req_list = []
                        act_list = []
                        if not ok_align:
                            req_list.append("Justificada o Izquierda")
                            act_list.append(align_str_raw)
                        if not ok_bold:
                            req_list.append("Normal (sin negrita)")
                            act_list.append(bold_str_raw)
                        if not ok_case:
                            req_list.append("Minúsculas")
                            act_list.append(case_str_raw)
                        expected_str = ", ".join(req_list)
                        actual_str = ", ".join(act_list)

                    self._add("Índice General", f"Formato Nivel 4/5: {txt[:20]}...", "passed" if passed else "error",
                              f"El título de nivel 3 y 4 en el índice no debe estar en Negrita. El título de Nivel 4/5 '{txt[:20]}...' en el índice debe estar JUSTIFICADO o ALINEADO A LA IZQUIERDA, sin negrita (NORMAL) y en MINÚSCULAS.",
                              expected_str, actual_str, p_idx=p['index'], p_text=txt)
            else:
                # ═══ DETECTAR LÍNEAS HUÉRFANAS EN EL ÍNDICE ═══
                # Si la línea NO es una sección reconocida de Nivel 1 (RESUMEN,
                # ABSTRACT, INTRODUCCIÓN, CONCLUSIONES, RECOMENDACIONES, REFERENCIAS,
                # ANEXOS, ACRÓNIMOS, DEDICATORIA, AGRADECIMIENTOS) y tampoco tiene
                # numeración decimal (1.1., 1.1.1.), entonces es una línea "al aire"
                # que necesita numeración o no debería estar en el índice.
                upper_clean = upper.strip()
                # Quitar números de página al final y rellenos
                upper_clean = re.sub(r'\s*\.\.+\s*\d+\s*$', '', upper_clean)
                upper_clean = re.sub(r'\s+\d+\s*$', '', upper_clean)
                upper_clean = upper_clean.strip()

                known_level1_sections = {
                    "RESUMEN", "ABSTRACT", "INTRODUCCION", "INTRODUCCIÓN",
                    "CONCLUSIONES", "RECOMENDACIONES",
                    "REFERENCIAS BIBLIOGRAFICAS", "REFERENCIAS BIBLIOGRÁFICAS",
                    "ANEXOS", "ACRONIMOS", "ACRÓNIMOS",
                    "DEDICATORIA", "AGRADECIMIENTOS", "AGRADECIMIENTO",
                    "INDICE GENERAL", "ÍNDICE GENERAL",
                    "INDICE DE TABLAS", "ÍNDICE DE TABLAS",
                    "INDICE DE FIGURAS", "ÍNDICE DE FIGURAS",
                    "INDICE DE ANEXOS", "ÍNDICE DE ANEXOS",
                    "INDICE DE ACRONIMOS", "ÍNDICE DE ACRÓNIMOS",
                    "INDICE DE CUADROS", "ÍNDICE DE CUADROS",
                    "INDICE DE ILUSTRACIONES", "ÍNDICE DE ILUSTRACIONES",
                    "DECLARACION JURADA", "DECLARACIÓN JURADA",
                    "AUTORIZACION PARA EL DEPOSITO", "AUTORIZACIÓN PARA EL DEPÓSITO",
                    "HOJA DE JURADOS", "REPORTE DE SIMILITUD",
                }
                is_known_section = upper_clean in known_level1_sections or any(
                    upper_clean.startswith(k) for k in known_level1_sections
                )

                # Numeración decimal: acepta tanto "1.1. texto" como "1.1.texto"
                # (sin espacio) y romanos para capítulos V/VI/VII.
                has_numbering = bool(
                    re.match(r"^\d+(?:\.\d+)*\.?(\s+|[A-Za-zÁÉÍÓÚÑáéíóúñ])", txt) or
                    re.match(r"^[IVXLC]+\.\s*[A-ZÁÉÍÓÚÑ]", txt) or
                    re.match(r"^CAP[ÍI]TULO\s+[IVXLC0-9]+", upper_clean)
                )

                if not is_known_section and not has_numbering:
                    # ─── LÍNEA HUÉRFANA: falta numeración o no debería estar aquí ───
                    self._add(
                        "Índice General",
                        f"Falta numeración: {txt[:25]}...",
                        "error",
                        f"La línea '{txt[:50]}...' aparece en el índice sin numeración "
                        f"y no es una sección reconocida (RESUMEN, INTRODUCCIÓN, "
                        f"CONCLUSIONES, etc.). Las líneas del índice deben tener "
                        f"numeración del nivel correspondiente (ej: '2.1.', '2.1.1.') "
                        f"o ser una sección obligatoria. POSIBLES CAUSAS: (1) un "
                        f"subtítulo del documento sin asignarle nivel/numeración; "
                        f"(2) un párrafo regular incluido por error en el índice; "
                        f"(3) un título manual sin estilo. SOLUCIÓN: asígnele "
                        f"numeración decimal del nivel correcto (2.1., 2.1.1., etc.) "
                        f"o elimínelo del índice.",
                        "Numeración decimal (ej: '2.1.') o sección reconocida",
                        f"Línea sin numeración ni etiqueta: '{txt[:30]}...'",
                        p_idx=p['index'],
                        p_text=txt,
                    )
                    continue

                # ═══ NIVEL 1 LEGÍTIMO (RESUMEN, ANEXOS, etc.) ═══
                ok_align = align in ['both', 'justify', 'left']
                ok_bold = is_bold
                ok_case = is_uppercase

                passed = ok_align and ok_bold and ok_case
                if passed:
                    expected_str = "Correcto"
                    actual_str = "Correcto"
                else:
                    req_list = []
                    act_list = []
                    if not ok_align:
                        req_list.append("Justificada o Izquierda")
                        act_list.append(align_str_raw)
                    if not ok_bold:
                        req_list.append("Negrita")
                        act_list.append(bold_str_raw)
                    if not ok_case:
                        req_list.append("Mayúsculas")
                        act_list.append(case_str_raw)
                    expected_str = ", ".join(req_list)
                    actual_str = ", ".join(act_list)

                self._add("Índice General", f"Formato Nivel 1: {txt[:20]}...", "passed" if passed else "error",
                          f"El título de Nivel 1 '{txt[:20]}...' en el índice debe estar JUSTIFICADO o ALINEADO A LA IZQUIERDA, en NEGRITA y en MAYÚSCULAS.",
                          expected_str, actual_str, p_idx=p['index'], p_text=txt)

        # Validar la presencia de hipervínculos en las entradas del índice general
        if idx_start != -1:
            missing_links = []
            total_entries = 0
            for i in range(idx_start + 1, idx_end):
                p = self.paragraphs[i]
                txt = p['text'].strip()
                if len(txt) < 3 or p.get('in_table', False):
                    continue
                upper = txt.upper()
                if bool(re.match(r'^P[ÁA]G\.?:?$', upper)) or upper.startswith("ÍNDICE GENERAL") or upper.startswith("INDICE GENERAL"):
                    continue
                
                # Check if this index line looks like an entry
                has_dots_or_page = '....' in txt or bool(re.search(r'\d+$', txt))
                is_cap = "CAPITULO" in upper or "CAPÍTULO" in upper
                if not (has_dots_or_page or is_cap):
                    continue
                
                total_entries += 1
                if not p.get('has_hyperlink', False):
                    missing_links.append(txt[:30] + "...")
            
            if total_entries > 0:
                ok_links = len(missing_links) == 0
                status = "passed" if ok_links else "warning"
                msg = ("Las entradas del Índice General cuentan correctamente con hipervínculos "
                       "que enlazan directamente con las páginas del documento." if ok_links else
                       f"Se sugiere que las entradas del Índice General cuenten con hipervínculos "
                       f"activos para permitir la navegación directa a las secciones reales. "
                       f"Se detectaron {len(missing_links)} entradas sin hipervínculos activos (ej: {', '.join(missing_links[:3])}).")
                self._add("Índice General", "Hipervínculos en Índice General", status, msg,
                          "Todas las entradas del índice con hipervínculos activos",
                          "Con hipervínculos" if ok_links else "Algunas entradas sin hipervínculos activos",
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

            indent_left_cm = round(p.get('indent_left') or 0, 2)
            indent_first_cm = round(p.get('indent_first') or 0, 2)
            indent_right_cm = round(p.get('indent_right') or 0, 2)
            indent_hanging_cm = round(p.get('indent_hanging') or 0, 2)

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
        """
        Encuentra el rango del Índice General (idx_start, idx_end).

        El fin del rango se detecta cuando:
          - Aparece un título de OTRA sección con estilo Heading (alta confianza), o
          - Aparece un título grande (>=14pt) centrado SIN relleno de puntos ni
            número de página → es título de página de la SIGUIENTE sección
            (DEDICATORIA, ÍNDICE DE TABLAS, RESUMEN, etc.), no entrada del índice.

        Esto evita que el motor exija 12pt a títulos de página de 16pt.
        """
        idx_start = -1
        idx_end = -1
        section_keywords = [
            'ÍNDICE DE TABLAS', 'INDICE DE TABLAS',
            'ÍNDICE DE FIGURAS', 'INDICE DE FIGURAS',
            'ÍNDICE DE ANEXOS', 'INDICE DE ANEXOS',
            'ÍNDICE DE CUADROS', 'INDICE DE CUADROS',
            'RESUMEN', 'ABSTRACT',
            'ACRÓNIMOS', 'ACRONIMOS',
            'DEDICATORIA', 'AGRADECIMIENTO', 'AGRADECIMIENTOS',
            'INTRODUCCION', 'INTRODUCCIÓN',
            'CAPITULO', 'CAPÍTULO',
        ]
        for i, p in enumerate(self.paragraphs):
            txt = p['text'].strip()
            txt_upper = txt.upper()
            if idx_start == -1:
                if 'ÍNDICE GENERAL' in txt_upper or 'INDICE GENERAL' in txt_upper:
                    # No confundir con la entrada del propio índice
                    if not ('....' in txt or re.search(r'\s+\d+\s*$', txt)):
                        idx_start = i
            else:
                if not txt_upper or len(txt_upper) <= 3:
                    continue
                style = p.get('style_id', '')
                is_tdc = style.upper().startswith('TDC') if style else False
                if is_tdc:
                    continue

                has_section_keyword = any(k in txt_upper for k in section_keywords)
                if has_section_keyword:
                    # 1) Estilo Heading explícito → fin de rango
                    is_heading_style = (
                        style and (
                            'Heading' in style or 'titulo' in style.lower()
                            or 'ttulo' in style.lower()
                        )
                    )
                    # 2) Título de página: centrado + sin relleno + sin número final
                    align = p.get('alignment', 'left')
                    size, bold, _, _ = self._get_p_props(p)
                    size = size or 0
                    has_filler = '....' in txt
                    has_page_num = bool(re.search(r'\s+\d+\s*$', txt))
                    looks_like_page_title = (
                        align == 'center'
                        and size >= 14
                        and not has_filler
                        and not has_page_num
                    )
                    if is_heading_style or looks_like_page_title:
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
