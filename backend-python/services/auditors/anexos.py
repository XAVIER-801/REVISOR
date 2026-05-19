"""
anexos.py - Auditoría de la sección de Anexos.

Reglas implementadas:
- Título principal 'ANEXOS': 16pt, centrado, negrita
- Declaración Jurada de Autenticidad: presente
- Autorización para el Depósito: presente
- Títulos individuales (Anexo X. Título): formato, punto, secuencia, negrita, capitalización
- Sangría: sin sangría
- Interlineado 2.0, alineación izquierda
- Tamaño 12pt
"""
import re
from .base_auditor import BaseAuditor


class AnexosAuditor(BaseAuditor):

    def audit(self):
        self._audit_mandatory_documents()
        self._audit_formatting()

    def _audit_mandatory_documents(self):
        """Verifica la presencia de documentos obligatorios de la UNAP en Anexos."""
        found_jurada = False
        found_deposito = False

        for p in self.paragraphs:
            txt = p['text'].upper()
            if "DECLARACION JURADA DE AUTENTICIDAD" in txt: found_jurada = True
            if "AUTORIZACION PARA EL DEPOSITO" in txt: found_deposito = True

        if not found_jurada:
            self._add("Anexos", "Declaración Jurada", "error",
                     "No se encontró la 'Declaración Jurada de Autenticidad de Tesis' en los anexos.", "Presente", "Ausente")
        if not found_deposito:
            self._add("Anexos", "Autorización de Depósito", "error",
                     "No se encontró la 'Autorización para el Depósito de Tesis' en los anexos.", "Presente", "Ausente")

    def _audit_formatting(self):
        """Audita el formato de la sección de Anexos y sus títulos individuales."""
        # 1. Verificar título principal 'ANEXOS'
        anexos_p = None
        anexos_idx = -1
        for i, p in enumerate(self.paragraphs):
            if p['norm'] == "ANEXOS":
                anexos_p = p
                anexos_idx = i
                break

        if anexos_idx == -1:
            self._add("Anexos", "Título Principal 'ANEXOS'", "error",
                      "No se encontró la sección o el título principal 'ANEXOS' de tamaño 16pt, centrado y en negrita.",
                      "Presente", "No identificado")
            return

        self.anexos_start_idx = anexos_idx

        size, bold, italic, font = self._get_p_props(anexos_p)
        ok_size = abs(size - 16) < 0.5
        ok_align = anexos_p.get('alignment') == 'center'
        ok_bold = bold == True

        self._add("Anexos", "Título Principal 'ANEXOS'", "passed" if (ok_size and ok_align and ok_bold) else "error",
                  "El título 'ANEXOS' debe ser de tamaño 16pt, centrado y en negrita.",
                  "16pt, Centrado, Negrita", f"{size}pt, {anexos_p.get('alignment')}, {'Negrita' if bold else 'Normal'}",
                  p_idx=anexos_idx, p_text=anexos_p['text'])

        # 2. Auditar cada párrafo en la sección de Anexos
        found_annex_titles = []

        for i in range(anexos_idx + 1, len(self.paragraphs)):
            p = self.paragraphs[i]
            txt = p['text'].strip()
            if not txt or p.get('in_table'):
                continue

            size, bold, italic, font = self._get_p_props(p)
            align = p.get('alignment', 'left')
            l_ind = p.get('indent_left')
            f_ind = p.get('indent_first')
            h_ind = p.get('indent_hanging')
            l_cm = round((l_ind or 0) / 567.0, 2)
            f_cm = round((f_ind or 0) / 567.0, 2)
            h_cm = round((h_ind or 0) / 567.0, 2)

            annex_match = re.match(r"^Anexo\s+(\d+)(?:\.\s*|\s+\.\s*|\s+)(.*)", txt, re.IGNORECASE)

            if annex_match:
                num_str = annex_match.group(1)
                num = int(num_str)
                title_txt = annex_match.group(2).strip()
                found_annex_titles.append(num)

                has_dot = bool(re.match(r"^Anexo\s+\d+\.", txt, re.IGNORECASE))
                if not has_dot:
                    self._add("Anexos", f"Formato Anexo {num}", "error",
                              f"La etiqueta 'Anexo {num}' debe estar seguida por un punto (.) y un espacio.",
                              f"Anexo {num}.", txt[:25], p_idx=i, p_text=txt)

                expected_num = len(found_annex_titles)
                if num != expected_num:
                    self._add("Anexos", f"Secuencia Anexo {num}", "error",
                              f"La numeración de los anexos debe ser secuencial (Anexo 1, Anexo 2...). Hallado: Anexo {num}.",
                              f"Anexo {expected_num}", f"Anexo {num}", p_idx=i, p_text=txt)

                # Validar negrita en etiqueta y normal en título
                label_text = f"Anexo {num}."
                label_ok = True
                title_ok = True
                prefix_matched = ""

                for r in p['runs']:
                    r_txt = r['text']
                    if not r_txt.strip(): continue
                    if len(prefix_matched) < len(label_text):
                        prefix_matched += r_txt
                        if not r.get('bold'):
                            label_ok = False
                    else:
                        if r.get('bold'):
                            title_ok = False

                if not label_ok:
                    self._add("Anexos", f"Negrita Etiqueta Anexo {num}", "error",
                              f"La etiqueta 'Anexo {num}.' debe estar en negrita.",
                              "Negrita", "Normal", p_idx=i, p_text=txt)
                if not title_ok:
                    self._add("Anexos", f"Estilo Título Anexo {num}", "error",
                              f"El título del anexo '{title_txt[:30]}...' debe estar sin negrita.",
                              "Normal (Sin Negrita)", "Negrita", p_idx=i, p_text=txt)

                # Capitalización
                if title_txt:
                    first_letter = title_txt[0]
                    ok_case = first_letter.isupper()
                    rest = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ]', '', title_txt[1:])
                    ok_rest = not rest.isupper() if (ok_case and rest) else True
                    if not ok_case or not ok_rest:
                        self._add("Anexos", f"Capitalización Anexo {num}", "error",
                                  f"El título del anexo debe iniciar con mayúscula y continuar en minúsculas.",
                                  "Mayúscula inicial, resto minúsculas", title_txt[:30], p_idx=i, p_text=txt)

                has_indent = l_cm > 0.1 or f_cm > 0.1 or h_cm > 0.1
                if has_indent:
                    self._add("Anexos", f"Sangría Título Anexo {num}", "error",
                              f"El título del Anexo {num} debe estar sin sangría de ningún tipo.",
                              "Izq 0cm, Prim 0cm, Fran 0cm", f"Izq {l_cm}cm, Prim {f_cm}cm, Fran {h_cm}cm", p_idx=i, p_text=txt)

                ok_align = align == 'left'
                if not ok_align:
                    self._add("Anexos", f"Alineación Título Anexo {num}", "error",
                              f"El título del Anexo {num} debe estar alineado a la izquierda.",
                              "Izquierda", align, p_idx=i, p_text=txt)

                line_spacing = p.get('line_spacing') or 2.0
                ok_spacing = abs(line_spacing - 2.0) < 0.2
                if not ok_spacing:
                    self._add("Anexos", f"Interlineado Título Anexo {num}", "error",
                              f"El título del Anexo {num} debe tener interlineado 2.0.",
                              "2.0", str(line_spacing), p_idx=i, p_text=txt)

                ok_size = abs(size - 12) < 0.5
                if not ok_size:
                    self._add("Anexos", f"Tamaño Título Anexo {num}", "error",
                              f"El título del Anexo {num} debe ser de tamaño 12pt.",
                              "12pt", f"{size}pt", p_idx=i, p_text=txt)
            else:
                # Párrafo normal en Anexos
                is_sub_title = any(kw in txt.upper() for kw in ["DECLARACIÓN JURADA", "DECLARACION JURADA", "AUTORIZACIÓN PARA EL DEPOSITO", "AUTORIZACION PARA EL DEPOSITO"])

                has_indent = l_cm > 0.1 or f_cm > 0.1 or h_cm > 0.1
                if has_indent and not is_sub_title:
                    self._add("Anexos", "Sangría Contenido Anexo", "error",
                              "El contenido de los anexos debe estar sin sangría de ningún tipo.",
                              "Izq 0cm, Prim 0cm, Fran 0cm", f"Izq {l_cm}cm, Prim {f_cm}cm, Fran {h_cm}cm", p_idx=i, p_text=txt[:40])

                if not is_sub_title and len(txt) > 30:
                    ok_align = align == 'left'
                    if not ok_align:
                        self._add("Anexos", "Alineación Contenido Anexo", "warning",
                                  "El contenido de los anexos debe estar alineado a la izquierda.",
                                  "Izquierda", align, p_idx=i, p_text=txt[:40])

                    line_spacing = p.get('line_spacing') or 2.0
                    ok_spacing = abs(line_spacing - 2.0) < 0.2
                    if not ok_spacing:
                        self._add("Anexos", "Interlineado Contenido Anexo", "warning",
                                  "El contenido de los anexos debe tener interlineado 2.0.",
                                  "2.0", str(line_spacing), p_idx=i, p_text=txt[:40])

                    ok_size = abs(size - 12) < 0.5
                    if not ok_size:
                        self._add("Anexos", "Tamaño Contenido Anexo", "error",
                                  "El contenido de los anexos debe ser de tamaño 12pt.",
                                  "12pt", f"{size}pt", p_idx=i, p_text=txt[:40])

        if not found_annex_titles:
            self._add("Anexos", "Títulos de Anexos Individuales", "error",
                      "No se identificaron títulos de anexos secuenciales (Anexo 1, Anexo 2...).",
                      "Anexo 1, Anexo 2...", "No encontrados")
