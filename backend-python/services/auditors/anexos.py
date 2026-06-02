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
        # NOTA: La validación de Declaración Jurada y Autorización para Depósito
        # se delega ahora a los auditores especializados:
        #   - declaracion_autenticidad.py
        #   - autorizacion_deposito.py
        # Aquí solo validamos el formato general de la sección Anexos y la
        # numeración secuencial.
        self._audit_formatting()

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

            # Aceptar tanto numerados (Anexo 1.) como literales (Anexo N.)
            # Guía UNAP pág. 27-28 usa "Anexo N." para Declaración Jurada y
            # Autorización para Depósito (que van al final sin numerar).
            annex_match = re.match(
                r"^Anexo\s+(\d+|N)(?:\.\s*|\s+\.\s*|\s+)(.*)",
                txt,
                re.IGNORECASE,
            )

            if annex_match:
                num_str = annex_match.group(1)
                is_literal_N = num_str.upper() == "N"
                num = 0 if is_literal_N else int(num_str)
                title_txt = annex_match.group(2).strip()
                if not is_literal_N:
                    found_annex_titles.append(num)

                num_display = "N" if is_literal_N else str(num)

                # ═══ Validación ESTRICTA de capitalización: "Anexo" (no ANEXO ni anexo) ═══
                prefix_raw = re.match(r"^(\S+)\s+(\d+|N)", txt, re.IGNORECASE)
                if prefix_raw:
                    prefix_str = prefix_raw.group(1)
                    if prefix_str != "Anexo":
                        self._add(
                            "Anexos",
                            f"Capitalización Etiqueta: {prefix_str} {num_display}",
                            "error",
                            f"La etiqueta debe escribirse EXACTAMENTE como 'Anexo' "
                            f"(primera letra A mayúscula, resto minúsculas). "
                            f"Ejemplo correcto: 'Anexo {num_display}. Título del anexo'.",
                            "Anexo (formato Tipo Título)",
                            f"'{prefix_str}'",
                            p_idx=i,
                            p_text=txt[:40],
                        )

                # ═══ Validación del punto después del número/N ═══
                has_dot = bool(re.match(r"^Anexo\s+(\d+|N)\.", txt, re.IGNORECASE))
                if not has_dot:
                    self._add(
                        "Anexos",
                        f"Formato Anexo {num_display}",
                        "error",
                        f"La etiqueta 'Anexo {num_display}' en la sección de Anexos DEBE "
                        f"estar seguida por un punto (.) y un espacio antes del título. "
                        f"Formato correcto: 'Anexo {num_display}. Autorización para el depósito "
                        f"de tesis en el Repositorio Institucional'. "
                        f"Nota: en el ÍNDICE de Anexos NO va punto (formato distinto).",
                        f"Anexo {num_display}.",
                        txt[:25],
                        p_idx=i,
                        p_text=txt,
                    )

                # ═══ Secuencia (solo para anexos numerados) ═══
                if not is_literal_N:
                    expected_num = len(found_annex_titles)
                    if num != expected_num:
                        self._add(
                            "Anexos",
                            f"Secuencia Anexo {num}",
                            "error",
                            f"La numeración de los anexos debe ser secuencial "
                            f"(Anexo 1, Anexo 2...). Hallado: Anexo {num}.",
                            f"Anexo {expected_num}",
                            f"Anexo {num}",
                            p_idx=i,
                            p_text=txt,
                        )

                # ═══ NEGRITA: validación robusta usando _check_prefix_bold ═══
                label_text = f"Anexo {num_display}."
                label_ok = self._check_prefix_bold(p, len(label_text))
                title_bold = self._check_suffix_bold(p, len(label_text))

                if not label_ok:
                    self._add(
                        "Anexos",
                        f"Negrita Etiqueta Anexo {num_display}",
                        "error",
                        f"La etiqueta '{label_text}' DEBE estar en NEGRITA. "
                        f"Formato correcto: '{label_text}' en negrita + título del anexo "
                        f"en estilo normal (sin negrita). Ejemplo: "
                        f"'Anexo {num_display}. Autorización para el depósito de tesis en el "
                        f"Repositorio Institucional'.",
                        "Etiqueta en negrita",
                        "Etiqueta sin negrita o parcialmente",
                        p_idx=i,
                        p_text=txt,
                    )
                if title_bold:
                    self._add(
                        "Anexos",
                        f"Estilo Título Anexo {num_display}",
                        "error",
                        f"El título del anexo (\"{title_txt[:40]}...\") debe estar SIN negrita. "
                        f"Solo la etiqueta 'Anexo {num_display}.' va en negrita; el título del "
                        f"anexo va en estilo normal.",
                        "Título en estilo Normal (sin negrita)",
                        "Título en negrita",
                        p_idx=i,
                        p_text=txt,
                    )

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

    # ── Helpers de formato de runs ──

    def _check_prefix_bold(self, p, prefix_len):
        """¿Los primeros prefix_len caracteres del párrafo están en negrita?"""
        accumulated = 0
        for r in p.get("runs", []):
            r_txt = r.get("text", "") or ""
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

    def _check_suffix_bold(self, p, prefix_len):
        """¿Hay caracteres alfanuméricos en negrita DESPUÉS del prefijo?"""
        accumulated = 0
        for r in p.get("runs", []):
            r_txt = r.get("text", "") or ""
            if not r_txt:
                continue
            for c in r_txt:
                accumulated += 1
                if accumulated > prefix_len + 2:  # +2 para tolerar espacios
                    if r.get("bold") and c.isalnum():
                        return True
        return False
