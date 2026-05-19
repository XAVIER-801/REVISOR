"""
tablas_figuras.py - Auditoría de Tablas y Figuras en el cuerpo del documento.

Reglas implementadas:
- Etiqueta (Tabla 1, Figura 1): 12pt, Negrita, Izquierda, Sangría según nivel
- Título descriptivo: 12pt, Cursiva (sin negrita), Izquierda, Sangría según nivel
- Nota/Fuente: 10pt, Normal (sin cursiva/negrita), con dos puntos, 15pt espaciado posterior
- Secuencia: Etiqueta → Título (cursiva) → Tabla/Figura → Nota/Fuente
- Encabezado de tabla (primera fila): Centrado, Negrita
- Interlineado de tabla: 1.0 o 1.5
"""
import re
from .base_auditor import BaseAuditor


class TablasFigurasAuditor(BaseAuditor):

    def audit(self):
        self._audit_labels_and_titles()
        self._audit_table_contents()

    def _audit_labels_and_titles(self):
        """Audita etiquetas, títulos y notas/fuentes de tablas y figuras."""
        def expected_indent(level):
            if level in [1, 2]: return 0.0
            elif level == 3: return 1.25
            else: return 2.5

        for i, p in enumerate(self.paragraphs):
            txt = p['text'].strip()
            sec_upper = p.get('section', '').upper()
            if any(k in sec_upper for k in ['ÍNDICE DE TABLAS', 'INDICE DE TABLAS',
                                            'ÍNDICE DE FIGURAS', 'INDICE DE FIGURAS',
                                            'ÍNDICE GENERAL', 'INDICE GENERAL',
                                            'ÍNDICE DE CUADROS', 'INDICE DE CUADROS',
                                            'ÍNDICE DE ILUSTRACIONES', 'INDICE DE ILUSTRACIONES',
                                            'TABLA DE CONTENIDOS', 'TABLA DE CONTENIDO']):
                continue

            upper = txt.upper()
            align = p.get('alignment', 'left')
            l_cm = round((p.get('indent_left') or 0) / 567.0, 2)
            exp_l_cm = expected_indent(p.get('level', 1))

            is_table_label = re.match(r'^TABLA\s+\d+', upper)
            is_figure_label = re.match(r'^FIGURA\s+\d+', upper)

            if (is_table_label or is_figure_label) and p.get('in_table'):
                continue

            if is_table_label or is_figure_label:
                lbl_type = "Tabla" if is_table_label else "Figura"

                label_match = re.match(r'^((?:Tabla|Figura)\s+\d+\.?\s*)(.*)', txt, re.IGNORECASE)
                label_text = label_match.group(1).strip() if label_match else txt
                title_in_same_para = label_match.group(2).strip() if label_match else ""

                # 1. Alineación y Sangría
                if align != 'left' and align != 'both':
                    self._add("Tablas y Figuras", f"Alineación Etiqueta: {label_text}", "error",
                             f"La etiqueta de {lbl_type} debe estar alineada a la Izquierda.", "Izquierda", align, p_idx=p['index'], p_text=txt)

                if abs(l_cm - exp_l_cm) > 0.1:
                    self._add("Tablas y Figuras", f"Sangría Etiqueta: {label_text}", "warning",
                             f"La etiqueta de {lbl_type} debe tener la misma sangría que el título de Nivel {p.get('level')} ({exp_l_cm}cm). *Si la figura/tabla es muy grande, puede ignorarse esta advertencia.",
                             f"Izq {exp_l_cm}cm", f"Izq {l_cm}cm", p_idx=p['index'], p_text=txt)

                # 2. Estilo (Negrita)
                is_bold = any(r.get('bold') for r in p.get('runs', []))
                if not is_bold:
                    self._add("Tablas y Figuras", f"Estilo Etiqueta: {label_text}", "error",
                             f"Las etiquetas de {lbl_type} deben estar en Negrita.", "Negrita", "Normal", p_idx=p['index'], p_text=txt)

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
                            self._add("Tablas y Figuras", f"Estilo Título: {title_in_same_para[:25]}...", "error",
                                     f"El título descriptivo de la {lbl_type} debe estar en CURSIVA y SIN NEGRITA.",
                                     "Cursiva (Sin Negrita)", f"{'Cursiva' if is_italic else '**Normal**'} {'**y Negrita**' if is_title_bold else ''}", p_idx=p['index'], p_text=txt)
                else:
                    if i + 1 < len(self.paragraphs):
                        next_p = self.paragraphs[i+1]
                        if next_p.get('in_table'):
                            self._add("Tablas y Figuras", f"Secuencia: Título de {label_text}", "error",
                                     f"Falta el título descriptivo de la {lbl_type.lower()} '{label_text}'. El título debe estar FUERA de la {lbl_type.lower()}, arriba de ella, y en CURSIVA. La secuencia correcta es: {label_text} → Título (cursiva) → {lbl_type} → Nota/Fuente.",
                                     "Título (Cursiva) fuera de la tabla", "No se encontró título antes de la tabla", p_idx=p['index'], p_text=txt)
                        else:
                            is_italic = any(r.get('italic') for r in next_p.get('runs', []))
                            is_next_bold = any(r.get('bold') for r in next_p.get('runs', []))
                            n_align = next_p.get('alignment', 'left')
                            n_l_cm = round((next_p.get('indent_left') or 0) / 567.0, 2)

                            if (not is_italic) or is_next_bold:
                                self._add("Tablas y Figuras", f"Estilo Título: {next_p['text'][:20]}...", "error",
                                         f"El título descriptivo de la {lbl_type} debe estar en CURSIVA y SIN NEGRITA.",
                                         "Cursiva (Sin Negrita)", f"{'Cursiva' if is_italic else '**Normal**'} {'**y Negrita**' if is_next_bold else ''}", p_idx=next_p['index'], p_text=next_p['text'])

                            if n_align != 'left' and n_align != 'both':
                                self._add("Tablas y Figuras", f"Alineación Título: {next_p['text'][:20]}...", "error",
                                         f"El título descriptivo de la {lbl_type} debe estar alineado a la Izquierda.", "Izquierda", n_align, p_idx=next_p['index'], p_text=next_p['text'])

                            if abs(n_l_cm - exp_l_cm) > 0.1:
                                self._add("Tablas y Figuras", f"Sangría Título: {next_p['text'][:20]}...", "warning",
                                         f"El título descriptivo debe tener la misma sangría que el título de Nivel {next_p.get('level')} ({exp_l_cm}cm). *Puede ignorarse si la tabla es grande.",
                                         f"Izq {exp_l_cm}cm", f"Izq {n_l_cm}cm", p_idx=next_p['index'], p_text=next_p['text'])

                # 3.b: Verificar presencia de Nota o Fuente
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
                    self._add("Tablas y Figuras", f"Nota/Fuente: {label_text}", "error",
                             f"No se encontró la nota o fuente obligatoria para la {lbl_type.lower()} '{label_text}'. Toda tabla y figura debe incluir su correspondiente Nota o Fuente debajo.",
                             "Nota: o Fuente: debajo", "Ausente", p_idx=p['index'], p_text=txt)

            # 4. Detectar "Nota" o "Fuente" y verificar formato
            if upper.startswith("NOTA") or upper.startswith("FUENTE"):
                first_word = txt.split(' ', 1)[0]
                has_colon = first_word.endswith(':')

                if not has_colon:
                    self._add("Tablas y Figuras", f"Sintaxis Nota/Fuente: {txt[:15]}...", "error",
                             "Las palabras 'Nota' o 'Fuente' deben terminar obligatoriamente con dos puntos (:).",
                             "Nota: o Fuente:", first_word, p_idx=p['index'], p_text=txt)

                is_italic = any(r.get('italic') for r in p.get('runs', []))
                is_bold = any(r.get('bold') for r in p.get('runs', []))

                if is_italic or is_bold:
                    self._add("Tablas y Figuras", f"Estilo Nota/Fuente: {txt[:15]}...", "error",
                             "La palabra 'Nota:' o 'Fuente:' (y su contenido) NO debe estar en cursiva ni en negrita.",
                             "Normal (Sin Cursiva/Negrita)", f"{'Cursiva' if is_italic else ''} {'Negrita' if is_bold else ''}".strip(), p_idx=p['index'], p_text=txt)

                size = p['runs'][0].get('size', 0) if p.get('runs') else 0
                if size != 10 and size != 0:
                    self._add("Tablas y Figuras", f"Tamaño Nota: {txt[:20]}", "error",
                             "Las notas o fuentes deben tener tamaño 10pt.", "10pt", f"{size}pt", p_idx=p['index'], p_text=txt)

                if abs(l_cm - exp_l_cm) > 0.1:
                    self._add("Tablas y Figuras", f"Sangría Nota: {txt[:15]}", "warning",
                             f"La nota/fuente debe tener la misma sangría que el título de Nivel {p.get('level')} ({exp_l_cm}cm).",
                             f"Izq {exp_l_cm}cm", f"Izq {l_cm}cm", p_idx=p['index'], p_text=txt)

                post_spacing = p.get('spacing_after', 0)
                if post_spacing < 14:
                    self._add("Tablas y Figuras", f"Espaciado Nota: {txt[:15]}", "warning",
                             "La nota/fuente debe tener un espaciado posterior de 15pt para separar de la siguiente sección.",
                             "15pt", f"{post_spacing}pt", p_idx=p['index'], p_text=txt)

    def _audit_table_contents(self):
        """Audita el contenido dentro de las tablas (Encabezado, Interlineado)."""
        for p in self.paragraphs:
            if not p.get('in_table'):
                continue

            txt = p['text'].strip()
            if not txt:
                continue

            if p.get('is_table_header'):
                has_xml_bold = any(r.get('bold') for r in p.get('runs', []))
                txt_letters = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ]', '', txt)
                has_caps_bold = len(txt_letters) > 1 and txt_letters == txt_letters.upper()
                is_bold = has_xml_bold or has_caps_bold
                align = p.get('alignment', 'left')

                if not is_bold or align != 'center':
                    self._add("Tablas y Figuras", f"Encabezado Tabla: {txt[:20]}...", "error",
                             "El encabezado de las tablas (primera fila) debe estar centrado y en negrita.",
                             "Centrado, Negrita", f"{align}, {'Negrita' if is_bold else 'Normal'}", p_idx=p['index'], p_text=txt)

            line_spacing = p.get('line_spacing', 1.0)
            if abs(line_spacing - 1.0) > 0.2 and abs(line_spacing - 1.5) > 0.2:
                self._add("Tablas y Figuras", f"Interlineado Tabla: {txt[:20]}...", "warning",
                         "El contenido de la tabla debe tener interlineado 1.0 o 1.5.",
                         "1.0 o 1.5", str(line_spacing), p_idx=p['index'], p_text=txt)
