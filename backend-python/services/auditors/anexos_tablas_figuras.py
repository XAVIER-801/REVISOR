"""
anexos_tablas_figuras.py - Auditoría de Tablas y Figuras en la sección de Anexos.

SOLO se activa si se encuentra al menos una etiqueta "Tabla N" o "Figura N"
en la sección de Anexos. Las reglas son las mismas que en el contenido general:
- Etiqueta: 12pt, Negrita, Izquierda, Sangría 0cm (nivel 1)
- Título: 12pt, Cursiva, sin negrita, Izquierda
- Nota/Fuente: 10pt, Cursiva, con dos puntos, 15pt espaciado posterior
- Secuencia: Etiqueta (sola) → Título → Contenido → Nota/Fuente
- Contenido de tabla: encabezados en negrita, contenido sin negrita
"""
import re
from .base_auditor import BaseAuditor


class AnexosTablasFigurasAuditor(BaseAuditor):

    def audit(self):
        if self.anexos_start_idx == -1:
            return

        anexos_paragraphs = self.paragraphs[self.anexos_start_idx:]

        labels = []
        for p in anexos_paragraphs:
            txt = p['text'].strip().upper()
            if txt and not p.get('in_table'):
                if re.match(r'^TABLA\s+\d+', txt):
                    labels.append(("Tabla", p))
                elif re.match(r'^FIGURA\s+\d+', txt):
                    labels.append(("Figura", p))

        if not labels:
            return

        for kind, p in labels:
            self._audit_anexo_label(kind, p)

        self._audit_anexo_table_contents()

    def _audit_anexo_label(self, kind, p):
        txt = p['text'].strip()
        lbl_type = kind
        label_match = re.match(r'^((?:Tabla|Figura)\s+\d+\.?\s*)(.*)', txt, re.IGNORECASE)
        label_text = label_match.group(1).strip() if label_match else txt
        title_in_same = label_match.group(2).strip() if label_match else ""
        align = p.get('alignment', 'left')
        l_cm = round(p.get('indent_left') or 0, 2)

        if abs(l_cm) > 0.15:
            self._add("Anexos Tablas/Figuras", f"Sangría Etiqueta: {label_text}", "warning",
                      f"La etiqueta de {lbl_type} en Anexos debe tener sangría 0cm.",
                      "0cm", f"{l_cm}cm", p_idx=p['index'], p_text=txt)

        if align not in ('left', 'both'):
            self._add("Anexos Tablas/Figuras", f"Alineación Etiqueta: {label_text}", "error",
                      f"La etiqueta de {lbl_type} en Anexos debe estar alineada a la Izquierda.",
                      "Izquierda", self._align_display(align), p_idx=p['index'], p_text=txt)

        if not self._is_meaningfully_bold(p, threshold=0.5):
            self._add("Anexos Tablas/Figuras", f"Estilo Etiqueta: {label_text}", "error",
                      f"Las etiquetas de {lbl_type} en Anexos deben estar en Negrita.",
                      "Negrita", "Normal", p_idx=p['index'], p_text=txt)

        font_size = p['runs'][0].get('size', 0) if p.get('runs') else 0
        if font_size > 0 and abs(font_size - 12) > 0.5:
            self._add("Anexos Tablas/Figuras", f"Tamaño Etiqueta: {label_text}", "error",
                      f"La etiqueta de {lbl_type} en Anexos debe estar en 12pt. Hallado: {font_size}pt.",
                      "12pt", f"{font_size}pt", p_idx=p['index'], p_text=txt)

        s_before = p.get('spacing_before', 0)
        s_after = p.get('spacing_after', 0)
        if s_before > 1.0:
            self._add("Anexos Tablas/Figuras", f"Espaciado Anterior Etiqueta: {label_text}", "error",
                      "La etiqueta debe tener espaciado anterior de 0pt.", "0pt", f"{s_before}pt",
                      p_idx=p['index'], p_text=txt)
        if s_after > 1.0:
            self._add("Anexos Tablas/Figuras", f"Espaciado Posterior Etiqueta: {label_text}", "error",
                      "La etiqueta debe tener espaciado posterior de 0pt.", "0pt", f"{s_after}pt",
                      p_idx=p['index'], p_text=txt)

        line_spacing = p.get('line_spacing')
        if line_spacing is not None and abs(line_spacing - 2.0) > 0.2:
            self._add("Anexos Tablas/Figuras", f"Interlineado Etiqueta: {label_text}", "error",
                      "La etiqueta debe tener interlineado 2.0.", "2.0", str(line_spacing),
                      p_idx=p['index'], p_text=txt)

        if title_in_same:
            self._add("Anexos Tablas/Figuras", f"Etiqueta con título en misma línea: {label_text}", "error",
                      f"La etiqueta de {lbl_type} en Anexos debe estar SOLA en su línea. "
                      "El título descriptivo va en la línea siguiente en CURSIVA.",
                      "Etiqueta sola en su línea", "Título en la misma línea",
                      p_idx=p['index'], p_text=txt)
        else:
            next_idx = -1
            for j in range(p['index'] + 1, len(self.paragraphs)):
                if self.paragraphs[j]['text'].strip():
                    next_idx = j
                    break

            if next_idx == -1:
                self._add("Anexos Tablas/Figuras", f"Falta título: {label_text}", "error",
                          f"Falta el título descriptivo de {label_text}. Debe ir en la línea "
                          "siguiente en CURSIVA.", "Título (Cursiva)", "Ausente",
                          p_idx=p['index'], p_text=txt)
            else:
                np = self.paragraphs[next_idx]
                ntxt = np['text'].strip()
                nupper = ntxt.upper()

                if np.get('in_table') or nupper.startswith("NOTA") or nupper.startswith("FUENTE"):
                    self._add("Anexos Tablas/Figuras", f"Falta título: {label_text}", "error",
                              f"Falta el título descriptivo de {label_text}. El título debe ir "
                              "en la línea siguiente, entre la etiqueta y la tabla/figura.",
                              "Título (Cursiva)", "No se encontró", p_idx=p['index'], p_text=txt)
                else:
                    is_italic = any(r.get('italic') for r in np.get('runs', []))
                    is_bold = any(r.get('bold') for r in np.get('runs', []))
                    n_align = np.get('alignment', 'left')

                    if not is_italic or is_bold:
                        req = []
                        act = []
                        if not is_italic:
                            req.append("Cursiva")
                            act.append("Normal")
                        if is_bold:
                            req.append("Sin Negrita")
                            act.append("Negrita")
                        self._add("Anexos Tablas/Figuras", f"Estilo Título: {ntxt[:20]}...", "error",
                                  f"El título descriptivo de {lbl_type} en Anexos debe estar en "
                                  "CURSIVA y SIN NEGRITA.", ", ".join(req), ", ".join(act),
                                  p_idx=np['index'], p_text=ntxt)

                    n_size = np['runs'][0].get('size', 0) if np.get('runs') else 0
                    if n_size > 0 and abs(n_size - 12) > 0.5:
                        self._add("Anexos Tablas/Figuras", f"Tamaño Título: {ntxt[:20]}...", "error",
                                  f"El título de {lbl_type} en Anexos debe estar en 12pt. Hallado: {n_size}pt.",
                                  "12pt", f"{n_size}pt", p_idx=np['index'], p_text=ntxt)

                    n_s_before = np.get('spacing_before', 0)
                    n_s_after = np.get('spacing_after', 0)
                    if n_s_before > 1.0:
                        self._add("Anexos Tablas/Figuras", f"Espaciado Anterior Título: {ntxt[:20]}...", "error",
                                  "El título debe tener espaciado anterior de 0pt.", "0pt", f"{n_s_before}pt",
                                  p_idx=np['index'], p_text=ntxt)
                    if n_s_after > 1.0:
                        self._add("Anexos Tablas/Figuras", f"Espaciado Posterior Título: {ntxt[:20]}...", "error",
                                  "El título debe tener espaciado posterior de 0pt.", "0pt", f"{n_s_after}pt",
                                  p_idx=np['index'], p_text=ntxt)

                    n_line_spacing = np.get('line_spacing')
                    if n_line_spacing is not None and abs(n_line_spacing - 2.0) > 0.2:
                        self._add("Anexos Tablas/Figuras", f"Interlineado Título: {ntxt[:20]}...", "error",
                                  "El título debe tener interlineado 2.0.", "2.0", str(n_line_spacing),
                                  p_idx=np['index'], p_text=ntxt)

                    if n_align not in ('left', 'both'):
                        self._add("Anexos Tablas/Figuras", f"Alineación Título: {ntxt[:20]}...", "error",
                                  "El título descriptivo debe estar alineado a la Izquierda.",
                                  "Izquierda", self._align_display(n_align), p_idx=np['index'], p_text=ntxt)

        encontro_nota = False
        for j in range(p['index'] + 1, min(p['index'] + 150, len(self.paragraphs))):
            pn = self.paragraphs[j]
            ntxt = pn['text'].strip().upper()
            if not ntxt:
                continue
            if (re.match(r'^TABLA\s+\d+', ntxt) or
                re.match(r'^FIGURA\s+\d+', ntxt) or
                re.match(r'^CAP[ÍI]TULO\s+(I|V|X|L|C|[0-9]+)', ntxt)):
                break
            if ntxt.startswith("NOTA") or ntxt.startswith("FUENTE"):
                encontro_nota = True
                fp = self.paragraphs[j]
                ftxt = fp['text'].strip()
                ffirst = ftxt.split(' ', 1)[0]
                has_colon = ffirst.endswith(':')
                f_italic = any(r.get('italic') for r in fp.get('runs', []))
                f_bold = any(r.get('bold') for r in fp.get('runs', []))
                f_size = fp['runs'][0].get('size', 0) if fp.get('runs') else 0

                if not has_colon:
                    self._add("Anexos Tablas/Figuras", f"Sintaxis Nota/Fuente: {ftxt[:15]}...", "error",
                              "Las palabras 'Nota' o 'Fuente' deben terminar con dos puntos (:).",
                              "Nota: o Fuente:", ffirst, p_idx=fp['index'], p_text=ftxt)
                if not f_italic:
                    self._add("Anexos Tablas/Figuras", f"Estilo Nota/Fuente: {ftxt[:15]}...", "error",
                              "La palabra 'Nota:' o 'Fuente:' DEBE estar en CURSIVA.",
                              "Cursiva", "Normal", p_idx=fp['index'], p_text=ftxt)
                if f_bold:
                    self._add("Anexos Tablas/Figuras", f"Estilo Nota/Fuente: {ftxt[:15]}...", "error",
                              "La palabra 'Nota:' o 'Fuente:' NO debe estar en Negrita.",
                              "Sin Negrita", "Negrita", p_idx=fp['index'], p_text=ftxt)
                if f_size != 10 and f_size != 0:
                    self._add("Anexos Tablas/Figuras", f"Tamaño Nota: {ftxt[:20]}", "error",
                              "Las notas o fuentes deben tener tamaño 10pt.", "10pt", f"{f_size}pt",
                              p_idx=fp['index'], p_text=ftxt)
                f_s_before = fp.get('spacing_before', 0)
                if f_s_before > 1.0:
                    self._add("Anexos Tablas/Figuras", f"Espaciado Anterior Nota: {ftxt[:15]}...", "error",
                              "La Nota o Fuente debe tener espaciado anterior de 0pt.",
                              "0pt", f"{f_s_before}pt", p_idx=fp['index'], p_text=ftxt)
                f_s_after = fp.get('spacing_after', 0)
                if abs(f_s_after - 15.0) > 2.0:
                    self._add("Anexos Tablas/Figuras", f"Espaciado Posterior Nota: {ftxt[:15]}...", "error",
                              "La Nota o Fuente DEBE tener espaciado posterior de 15pt.",
                              "15pt", f"{f_s_after}pt", p_idx=fp['index'], p_text=ftxt)
                f_line = fp.get('line_spacing')
                if f_line is not None and abs(f_line - 1.5) > 0.2:
                    self._add("Anexos Tablas/Figuras", f"Interlineado Nota: {ftxt[:15]}...", "warning",
                              "La Nota o Fuente debe tener interlineado 1.5.", "1.5", str(f_line),
                              p_idx=fp['index'], p_text=ftxt)
                break

        if not encontro_nota:
            self._add("Anexos Tablas/Figuras", f"Nota/Fuente: {label_text}", "error",
                      f"No se encontró la nota o fuente obligatoria para {label_text} en Anexos.",
                      "Nota: o Fuente: debajo", "Ausente", p_idx=p['index'], p_text=txt)

    def _audit_anexo_table_contents(self):
        headers_by_table = {}
        content_by_table = {}
        table_first_p = {}

        for p in self.paragraphs[self.anexos_start_idx:]:
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

        for tbl_id, header_paragraphs in headers_by_table.items():
            non_bold = []
            for hp in header_paragraphs:
                if not self._is_meaningfully_bold(hp, threshold=0.3):
                    non_bold.append(hp)
            if non_bold:
                ref = table_first_p[tbl_id]
                page = ref.get('estimated_page', '?')
                examples = ", ".join(f"\"{c['text'].strip()[:25]}\"" for c in non_bold[:3])
                count = len(non_bold)
                self._add("Anexos Tablas/Figuras",
                          f"Encabezado sin negrita (Anexos, pág. {page})", "error",
                          f"La tabla en Anexos (pág. {page}) tiene {count} celda{'s' if count != 1 else ''} "
                          f"de encabezado sin negrita. {examples}",
                          "Todas las celdas del encabezado en negrita",
                          f"{count} celda{'s' if count != 1 else ''} sin negrita",
                          p_idx=non_bold[0]['index'], p_text=non_bold[0]['text'][:60])

        all_table_paragraphs = {}
        for p in self.paragraphs[self.anexos_start_idx:]:
            if not p.get('in_table') or not p['text'].strip():
                continue
            tbl_id = p.get('tbl_id')
            if tbl_id:
                all_table_paragraphs.setdefault(tbl_id, []).append(p)

        for tbl_id, table_paragraphs in all_table_paragraphs.items():
            wrong_spacing = []
            for tp in table_paragraphs:
                ls = tp.get('line_spacing', 1.0) or 1.0
                if abs(ls - 1.0) > 0.2 and abs(ls - 1.5) > 0.2:
                    wrong_spacing.append(tp)
            if wrong_spacing:
                ref = table_first_p.get(tbl_id, wrong_spacing[0])
                page = ref.get('estimated_page', '?')
                count = len(wrong_spacing)
                found = wrong_spacing[0].get('line_spacing', '?')
                self._add("Anexos Tablas/Figuras",
                          f"Interlineado tabla en Anexos (pág. {page})", "warning",
                          f"La tabla en Anexos (pág. {page}) tiene {count} celda{'s' if count != 1 else ''} "
                          f"con interlineado incorrecto. Debe ser 1.0 o 1.5.",
                          "1.0 o 1.5", str(found),
                          p_idx=wrong_spacing[0]['index'], p_text=wrong_spacing[0]['text'][:60])
