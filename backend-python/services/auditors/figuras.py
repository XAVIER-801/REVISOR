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

    def _get_expected_indent_for_level(self, level):
        """Retorna sangría esperada para un nivel."""
        if level in [1, 2]:
            return 0.0
        elif level == 3:
            return 1.25
        else:  # 4, 5
            return 2.5

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
                font_size = 0
                if p.get('runs'):
                    font_size = p['runs'][0].get('size', 0) // 2 if p['runs'][0].get('size') else 0

                if font_size > 0 and font_size != 12:
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

                # 2. Estilo (Negrita)
                is_bold = any(r.get('bold') for r in p.get('runs', []))
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
                    if i + 1 < len(self.paragraphs):
                        next_p = self.paragraphs[i+1]
                        is_italic = any(r.get('italic') for r in next_p.get('runs', []))
                        is_next_bold = any(r.get('bold') for r in next_p.get('runs', []))
                        n_align = next_p.get('alignment', 'left')
                        n_l_cm = round((next_p.get('indent_left') or 0) / 567.0, 2)

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
                            n_font_size = next_p['runs'][0].get('size', 0) // 2 if next_p['runs'][0].get('size') else 0
                        if n_font_size > 0 and n_font_size != 12:
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

                    is_italic = any(r.get('italic') for r in p.get('runs', []))
                    is_bold = any(r.get('bold') for r in p.get('runs', []))

                    if is_italic or is_bold:
                        req_list = []
                        act_list = []
                        if is_italic:
                            req_list.append("Sin cursiva")
                            act_list.append("Cursiva")
                        if is_bold:
                            req_list.append("Sin negrita")
                            act_list.append("Negrita")
                        self._add("Figuras", f"Estilo Nota/Fuente: {txt[:15]}...", "error",
                                 "La palabra 'Nota:' o 'Fuente:' (y su contenido) NO debe estar en cursiva ni en negrita.",
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

                    note_level = p.get('body_level') or p.get('level') or 1
                    note_context_level = self._find_context_level(i)
                    note_exp_l_cm = self._get_expected_indent_for_level(note_context_level)
                    if abs(l_cm - note_exp_l_cm) > 0.1:
                        self._add("Figuras", f"Sangría Nota: {txt[:15]}", "warning",
                                 f"La nota/fuente de la figura debe tener la misma sangría que el título de Nivel {note_context_level} ({note_exp_l_cm}cm).",
                                 f"Izq {note_exp_l_cm}cm", f"Izq {l_cm}cm", p_idx=p['index'], p_text=txt)

                    post_spacing = p.get('spacing_after', 0)
                    if post_spacing < 14:
                        self._add("Figuras", f"Espaciado Nota: {txt[:15]}", "warning",
                                 "La nota/fuente debe tener un espaciado posterior de 15pt para separar de la siguiente sección.",
                                 "15pt", f"{post_spacing}pt", p_idx=p['index'], p_text=txt)
