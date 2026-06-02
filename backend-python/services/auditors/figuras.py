"""
figuras.py - Auditoría de Figuras en el cuerpo del documento.

Reglas implementadas:
- Etiqueta (Figura X): 12pt, Negrita, Izquierda, Sangría según nivel.
- Título descriptivo: 12pt, Cursiva (sin negrita), Izquierda, Sangría según nivel.
- Nota/Fuente: 10pt, Normal (sin cursiva/negrita), con dos puntos, 15pt espaciado posterior.
- Secuencia: Etiqueta → Título (cursiva) → Figura → Nota/Fuente.
"""
import re
from .base_auditor import BaseAuditor


class FigurasAuditor(BaseAuditor):

    def audit(self):
        self._audit_figure_labels_and_titles()
        self._audit_figure_image_alignment()

    def _audit_figure_image_alignment(self):
        """
        Valida que el párrafo que contiene la imagen (drawing) de una figura o tabla
        esté alineado a la IZQUIERDA, no centrado. Su sangría debe coincidir con la
        del nivel del título contextual en que se encuentra.
        """
        for i, p in enumerate(self.paragraphs):
            drawings = p.get('drawings', [])
            has_drawing = len(drawings) > 0
            if not has_drawing:
                continue

            # Saltar imágenes en páginas preliminares (jurados, turnitin)
            sec_upper = p.get('section', '').upper()
            if any(k in sec_upper for k in ['JURADOS', 'SIMILITUD', 'DEDICATORIA']):
                continue

            # Buscar la etiqueta "Figura N" o "Tabla N" más cercana hacia arriba para contexto (máximo 10 párrafos atrás)
            label_text = ""
            is_table = False
            for k in range(i - 1, max(-1, i - 10), -1):
                prev_txt = self.paragraphs[k]['text'].strip()
                prev_upper = prev_txt.upper()
                if re.match(r'^FIGURA\s+\d+', prev_upper):
                    label_text = prev_txt[:30]
                    is_table = False
                    break
                elif re.match(r'^TABLA\s+\d+', prev_upper):
                    label_text = prev_txt[:30]
                    is_table = True
                    break

            # Si no hay etiqueta de Figura o Tabla cercana, no la auditamos bajo esta regla
            if not label_text:
                continue
                
            # Si tiene etiqueta, la auditamos (incluso si p.get('in_table') es True,
            # ya que a veces los tesistas usan tablas invisibles para colocar imágenes lado a lado).

            category = "Tablas" if is_table else "Figuras"
            element_type = "tabla" if is_table else "figura"
            ref = f" ({label_text})"

            # Verificar si es de "mayor tamaño" (ancho > 13cm)
            is_large = any(d.get('width', 0) >= 13.0 for d in drawings)

            # 1. Validar Alineación
            align = p.get('alignment', 'left')
            
            if is_large:
                # Figuras grandes pueden estar centradas
                if align not in ('left', 'both', 'justify', 'center'):
                    self._add(
                        category,
                        f"Alineación de Imagen: {label_text}",
                        "error",
                        f"La imagen de la {element_type}{ref} de mayor tamaño debe estar centrada o alineada a la IZQUIERDA.",
                        "Alineación: Izquierda/Centrado",
                        f"Alineación: {align.capitalize()}",
                        p_idx=p['index'],
                        p_text=f"[Imagen de {element_type}]",
                    )
                else:
                    self._add(category, f"Alineación de Imagen: {label_text}", "passed", "Alineación correcta", "Izquierda/Centrado", align, p_idx=p['index'])
            else:
                if align not in ('left', 'both', 'justify'):
                    self._add(
                        category,
                        f"Alineación de Imagen: {label_text}",
                        "error",
                        f"La imagen de la {element_type}{ref} debe estar alineada a la IZQUIERDA, no centrada. "
                        f"La sangría es la que la posiciona horizontalmente según el nivel del título contextual al que pertenece.",
                        "Alineación: Izquierda",
                        f"Alineación: {align.capitalize()}",
                        p_idx=p['index'],
                        p_text=f"[Imagen de {element_type}]",
                    )
                else:
                    self._add(category, f"Alineación de Imagen: {label_text}", "passed", "Alineación correcta", "Izquierda", align, p_idx=p['index'])

            # 2. Validar Sangría (debe coincidir con su nivel de título contextual)
            context_level = self._find_context_level(i)
            exp_l_cm = self._get_expected_indent_for_level(context_level)
            
            l_val = p.get('indent_left') or 0
            l_cm = round(l_val / 567.0, 2) if l_val > 10 else round(l_val, 2)
            
            if align in ('left', 'both', 'justify'):
                if abs(l_cm - exp_l_cm) > 0.1:
                    self._add(
                        category,
                        f"Sangría de Imagen: {label_text}",
                        "warning",
                        f"La sangría izquierda de la imagen de la {element_type}{ref} debe coincidir con la del título de Nivel {context_level} ({exp_l_cm}cm). "
                        f"Hallado: {l_cm}cm.",
                        f"Izq {exp_l_cm}cm",
                        f"Izq {l_cm}cm",
                        p_idx=p['index'],
                        p_text=f"[Imagen de {element_type}]",
                    )
                else:
                    self._add(category, f"Sangría de Imagen: {label_text}", "passed", "Sangría correcta", f"{exp_l_cm}cm", f"{l_cm}cm", p_idx=p['index'])

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

    def _audit_figure_labels_and_titles(self):
        """Audita etiquetas, títulos y notas/fuentes de figuras."""
        for i, p in enumerate(self.paragraphs):
            txt = p['text'].strip()
            sec_upper = p.get('section', '').upper()
            if any(k in sec_upper for k in ['ÍNDICE DE FIGURAS', 'INDICE DE FIGURAS',
                                            'ÍNDICE GENERAL', 'INDICE GENERAL',
                                            'TABLA DE CONTENIDOS', 'TABLA DE CONTENIDO']):
                continue

            upper = txt.upper()
            align = p.get('alignment', 'left')
            l_cm = round(p.get('indent_left') or 0, 2)

            # Obtener el nivel contextual del título anterior
            context_level = self._find_context_level(i)
            exp_l_cm = self._get_expected_indent_for_level(context_level)

            is_figure_label = bool(re.match(r'^FIGURA\s+\d+', upper))

            if is_figure_label and p.get('in_table'):
                continue

            if is_figure_label:
                label_match = re.match(r'^(Figura\s+\d+\.?\s*)(.*)', txt, re.IGNORECASE)
                label_text = label_match.group(1).strip() if label_match else txt
                title_in_same_para = label_match.group(2).strip() if label_match else ""

                # NUEVO: Validar tamaño de fuente (DEBE ser 12pt)
                # NOTA: style_resolver ya retorna size en puntos enteros
                font_size = 0
                if p.get('runs'):
                    font_size = p['runs'][0].get('size', 0)

                if font_size > 0 and abs(font_size - 12) > 0.5:
                    self._add("Figuras", f"Tamaño Etiqueta: {label_text}", "error",
                             f"La etiqueta de Figura debe estar en 12 puntos. Hallado: {font_size}pt.",
                             "12pt", f"{font_size}pt", p_idx=p['index'], p_text=txt)

                # NUEVO: Validar espaciado (anterior 0pt, posterior 0pt)
                s_before = p.get('spacing_before', 0)
                s_after = p.get('spacing_after', 0)
                if s_before > 1.0:
                    self._add("Figuras", f"Espaciado Anterior Etiqueta: {label_text}", "error",
                             "La etiqueta de Figura debe tener espaciado anterior de 0pt.",
                             "0pt", f"{s_before}pt", p_idx=p['index'], p_text=txt)
                if s_after > 1.0:
                    self._add("Figuras", f"Espaciado Posterior Etiqueta: {label_text}", "error",
                             "La etiqueta de Figura debe tener espaciado posterior de 0pt.",
                             "0pt", f"{s_after}pt", p_idx=p['index'], p_text=txt)

                # NUEVO: Validar interlineado (DEBE ser 2.0)
                line_spacing = p.get('line_spacing')
                if line_spacing is not None and abs(line_spacing - 2.0) > 0.2:
                    self._add("Figuras", f"Interlineado Etiqueta: {label_text}", "error",
                             "La etiqueta de Figura debe tener interlineado 2.0.",
                             "2.0", str(line_spacing), p_idx=p['index'], p_text=txt)

                # 1. Alineación y Sangría
                if align != 'left' and align != 'both':
                    self._add("Figuras", f"Alineación Etiqueta: {label_text}", "error",
                             "La etiqueta de Figura debe estar alineada a la Izquierda.", "Izquierda", align, p_idx=p['index'], p_text=txt)

                if abs(l_cm - exp_l_cm) > 0.1:
                    self._add("Figuras", f"Sangría Etiqueta: {label_text}", "warning",
                             f"La etiqueta de Figura debe tener la misma sangría que el título de Nivel {context_level} ({exp_l_cm}cm).",
                             f"Izq {exp_l_cm}cm", f"Izq {l_cm}cm", p_idx=p['index'], p_text=txt)

                # 2. Estilo (Negrita) — usa detección por mayoría de caracteres
                is_bold = self._is_meaningfully_bold(p)
                if not is_bold:
                    self._add("Figuras", f"Estilo Etiqueta: {label_text}", "error",
                             "Las etiquetas de Figura deben estar en Negrita.", "Negrita", "Normal", p_idx=p['index'], p_text=txt)

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
                            self._add("Figuras", f"Estilo Título: {title_in_same_para[:25]}...", "error",
                                     "El título descriptivo de la Figura debe estar en CURSIVA y SIN NEGRITA.",
                                     ", ".join(req_list), ", ".join(act_list), p_idx=p['index'], p_text=txt)
                else:
                    # Buscar el próximo párrafo no vacío después de la etiqueta
                    next_idx = -1
                    for j in range(i + 1, len(self.paragraphs)):
                        pj = self.paragraphs[j]
                        if pj['text'].strip() or pj.get('drawings'):
                            next_idx = j
                            break

                    if next_idx == -1:
                        self._add("Figuras", f"Secuencia: Título de {label_text}", "error",
                                 f"Falta el título descriptivo de la figura '{label_text}'. El título debe estar FUERA de la figura, arriba de ella, y en CURSIVA.",
                                 "Título (Cursiva) fuera de la figura", "No se encontró título antes de la figura", p_idx=p['index'], p_text=txt)
                    else:
                        next_p = self.paragraphs[next_idx]
                        next_upper = next_p['text'].strip().upper()

                        has_drawing = False
                        drawings = next_p.get("drawings") or []
                        for d in drawings:
                            if d.get("width", 0) >= 3.0:
                                has_drawing = True
                                break

                        if has_drawing or next_upper.startswith("NOTA") or next_upper.startswith("FUENTE") or next_p.get('in_table'):
                            self._add("Figuras", f"Secuencia: Título de {label_text}", "error",
                                     f"Falta el título descriptivo de la figura '{label_text}'. El título debe estar FUERA de la figura, arriba de ella, y en CURSIVA.",
                                     "Título (Cursiva) fuera de la figura", "No se encontró título antes de la figura", p_idx=p['index'], p_text=txt)
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
                                self._add("Figuras", f"Estilo Título: {next_p['text'][:20]}...", "error",
                                         "El título descriptivo de la Figura debe estar en CURSIVA y SIN NEGRITA.",
                                         ", ".join(req_list), ", ".join(act_list), p_idx=next_p['index'], p_text=next_p['text'])

                            # NUEVO: Validar tamaño de fuente del título (12pt)
                            n_font_size = 0
                            if next_p.get('runs'):
                                n_font_size = next_p['runs'][0].get('size', 0)
                            if n_font_size > 0 and abs(n_font_size - 12) > 0.5:
                                self._add("Figuras", f"Tamaño Título: {next_p['text'][:20]}...", "error",
                                         f"El título de Figura debe estar en 12 puntos. Hallado: {n_font_size}pt.",
                                         "12pt", f"{n_font_size}pt", p_idx=next_p['index'], p_text=next_p['text'])

                            # NUEVO: Validar espaciado del título (anterior 0pt, posterior 0pt)
                            n_s_before = next_p.get('spacing_before', 0)
                            n_s_after = next_p.get('spacing_after', 0)
                            if n_s_before > 1.0:
                                self._add("Figuras", f"Espaciado Anterior Título: {next_p['text'][:20]}...", "error",
                                         "El título de Figura debe tener espaciado anterior de 0pt.",
                                         "0pt", f"{n_s_before}pt", p_idx=next_p['index'], p_text=next_p['text'])
                            if n_s_after > 1.0:
                                self._add("Figuras", f"Espaciado Posterior Título: {next_p['text'][:20]}...", "error",
                                         "El título de Figura debe tener espaciado posterior de 0pt.",
                                         "0pt", f"{n_s_after}pt", p_idx=next_p['index'], p_text=next_p['text'])

                            # NUEVO: Validar interlineado del título (2.0)
                            n_line_spacing = next_p.get('line_spacing')
                            if n_line_spacing is not None and abs(n_line_spacing - 2.0) > 0.2:
                                self._add("Figuras", f"Interlineado Título: {next_p['text'][:20]}...", "error",
                                         "El título de Figura debe tener interlineado 2.0.",
                                         "2.0", str(n_line_spacing), p_idx=next_p['index'], p_text=next_p['text'])

                            if n_align != 'left' and n_align != 'both':
                                self._add("Figuras", f"Alineación Título: {next_p['text'][:20]}...", "error",
                                         "El título descriptivo de la Figura debe estar alineado a la Izquierda.", "Izquierda", n_align, p_idx=next_p['index'], p_text=next_p['text'])

                            if abs(n_l_cm - exp_l_cm) > 0.1:
                                self._add("Figuras", f"Sangría Título: {next_p['text'][:20]}...", "warning",
                                         f"El título descriptivo debe tener la misma sangría que el título de Nivel {context_level} ({exp_l_cm}cm).",
                                         f"Izq {exp_l_cm}cm", f"Izq {n_l_cm}cm", p_idx=next_p['index'], p_text=next_p['text'])

                # 3.b: Verificar presencia de Nota o Fuente para la Figura
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
                    self._add("Figuras", f"Nota/Fuente: {label_text}", "error",
                             f"No se encontró la nota o fuente obligatoria para la figura '{label_text}'. Toda figura debe incluir su correspondiente Nota o Fuente debajo.",
                             "Nota: o Fuente: debajo", "Ausente", p_idx=p['index'], p_text=txt)

            # 4. Detectar "Nota" o "Fuente" y verificar formato (Solo si corresponde a una figura previa)
            if upper.startswith("NOTA") or upper.startswith("FUENTE"):
                # Verificar si el elemento previo más cercano con etiqueta era Tabla o Figura
                es_de_figura = False
                for k in range(i - 1, max(-1, i - 150), -1):
                    prev_txt = self.paragraphs[k]['text'].strip().upper()
                    if prev_txt.startswith("TABLA"):
                        es_de_figura = False
                        break
                    elif prev_txt.startswith("FIGURA"):
                        es_de_figura = True
                        break

                if es_de_figura:
                    first_word = txt.split(' ', 1)[0]
                    has_colon = first_word.endswith(':')

                    if not has_colon:
                        self._add("Figuras", f"Sintaxis Nota/Fuente: {txt[:15]}...", "error",
                                 "Las palabras 'Nota' o 'Fuente' deben terminar obligatoriamente con dos puntos (:).",
                                 "Nota: o Fuente:", first_word, p_idx=p['index'], p_text=txt)

                    # REGLA ACTUALIZADA: "Nota:" / "Fuente:" debe estar en CURSIVA y con dos puntos.
                    # El BOLD sigue prohibido.
                    is_italic = any(r.get('italic') for r in p.get('runs', []))
                    is_bold = any(r.get('bold') for r in p.get('runs', []))

                    label_word = txt.split(' ', 1)[0]  # "Nota:" o "Fuente:"
                    label_is_italic = self._check_prefix_italic(p, len(label_word))

                    if not label_is_italic or is_bold:
                        req_list = []
                        act_list = []
                        if not label_is_italic:
                            req_list.append("Cursiva")
                            act_list.append("Normal")
                        if is_bold:
                            req_list.append("Sin negrita")
                            act_list.append("Negrita")
                        self._add("Figuras", f"Estilo Nota/Fuente: {txt[:15]}...", "error",
                                 "La palabra 'Nota:' o 'Fuente:' DEBE estar en CURSIVA y "
                                 "terminada con dos puntos (:). NO debe estar en negrita.",
                                 ", ".join(req_list), ", ".join(act_list), p_idx=p['index'], p_text=txt)

                    size = p['runs'][0].get('size', 0) if p.get('runs') else 0
                    if size != 10 and size != 0:
                        self._add("Figuras", f"Tamaño Nota: {txt[:20]}", "error",
                                 "Las notas o fuentes de figuras deben tener tamaño 10pt.", "10pt", f"{size}pt", p_idx=p['index'], p_text=txt)

                    # NUEVO: Validar espaciado anterior (0pt)
                    s_before = p.get('spacing_before', 0)
                    if s_before > 1.0:
                        self._add("Figuras", f"Espaciado Anterior Nota: {txt[:15]}...", "error",
                                 "La Nota o Fuente debe tener espaciado anterior de 0pt.",
                                 "0pt", f"{s_before}pt", p_idx=p['index'], p_text=txt)

                    # NUEVO Y CRÍTICO: Validar espaciado posterior (15pt OBLIGATORIO)
                    s_after = p.get('spacing_after', 0)
                    if abs(s_after - 15.0) > 2.0:
                        self._add("Figuras", f"Espaciado Posterior Nota: {txt[:15]}...", "error",
                                 "La Nota o Fuente DEBE tener espaciado posterior de 15pt. Este es un requisito obligatorio.",
                                 "15pt", f"{s_after}pt", p_idx=p['index'], p_text=txt)

                    # NUEVO: Validar interlineado (1.5)
                    line_spacing = p.get('line_spacing')
                    if line_spacing is not None and abs(line_spacing - 1.5) > 0.2:
                        self._add("Figuras", f"Interlineado Nota: {txt[:15]}...", "warning",
                                 "La Nota o Fuente debe tener interlineado 1.5.",
                                 "1.5", str(line_spacing), p_idx=p['index'], p_text=txt)

                    note_context_level = self._find_context_level(i)
                    note_exp_l_cm = self._get_expected_indent_for_level(note_context_level)
                    if abs(l_cm - note_exp_l_cm) > 0.1:
                        self._add("Figuras", f"Sangría Nota: {txt[:15]}", "warning",
                                 f"La nota/fuente de la figura debe tener la misma sangría que el título de Nivel {note_context_level} ({note_exp_l_cm}cm).",
                                 f"Izq {note_exp_l_cm}cm", f"Izq {l_cm}cm", p_idx=p['index'], p_text=txt)
