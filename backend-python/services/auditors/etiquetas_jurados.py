"""
etiquetas_jurados.py - Auditoría de etiquetas de la Hoja de Jurados.

Reglas implementadas:
- "FECHA DE SUSTENTACIÓN:": Mayúsculas, Negrita, Alineación Derecha,
  Espaciado anterior 10pt / posterior 0pt, Sin sangría.
- "ÁREA:": Mayúsculas, Negrita, Alineación Izquierda,
  Espaciado anterior 0pt / posterior 0pt, Sin sangría.
- "TEMA:": Mayúsculas, Negrita, Alineación Izquierda,
  Espaciado anterior 0pt / posterior 0pt, Sin sangría.

Estas etiquetas se buscan en CUALQUIER parte del documento.
"""
import re
from .base_auditor import BaseAuditor


class EtiquetasJuradosAuditor(BaseAuditor):

    # Cargos esperados en la Hoja de Jurados (Guía pág. 7)
    EXPECTED_CARGOS = [
        ("PRESIDENTE", "PRESIDENTE:"),
        ("PRIMER MIEMBRO", "PRIMER MIEMBRO:"),
        ("SEGUNDO MIEMBRO", "SEGUNDO MIEMBRO:"),
        ("ASESOR DE TESIS", "ASESOR DE TESIS:"),
    ]

    def audit(self):
        found_any = False
        found_cargos = set()

        # Primero buscar etiquetas de texto
        for i, p in enumerate(self.paragraphs):
            txt = p['text'].strip()
            if not txt:
                continue

            norm = p['norm']

            # ═══ FECHA DE SUSTENTACIÓN: ═══
            if 'FECHA DE SUSTENTACION' in norm or 'FECHA DE SUSTENTACIÓN' in txt.upper():
                self._audit_fecha_sustentacion(p, txt)
                found_any = True

            # ═══ ÁREA: ═══
            elif re.match(r'^[ÁA]REA\s*:', txt, re.IGNORECASE):
                self._audit_area_tema(p, txt, 'ÁREA')
                found_any = True

            # ═══ TEMA: ═══
            elif re.match(r'^TEMA\s*:', txt, re.IGNORECASE):
                self._audit_area_tema(p, txt, 'TEMA')
                found_any = True

            # ═══ CARGOS DEL JURADO (Guía pág. 7) ═══
            for cargo_key, cargo_label in self.EXPECTED_CARGOS:
                if cargo_key in norm and ':' in txt:
                    self._audit_cargo_jurado(p, txt, cargo_label)
                    found_cargos.add(cargo_key)
                    found_any = True
                    break

        # Verificar que se hayan encontrado los 4 cargos obligatorios
        if found_cargos:
            missing = [c[1] for c in self.EXPECTED_CARGOS if c[0] not in found_cargos]
            if missing:
                self._add(
                    "Hoja de Jurados",
                    "Cargos faltantes",
                    "warning",
                    f"No se detectaron todos los cargos obligatorios en la Hoja de Jurados. "
                    f"Faltan: {', '.join(missing)}.",
                    "PRESIDENTE, PRIMER MIEMBRO, SEGUNDO MIEMBRO, ASESOR DE TESIS",
                    f"Faltan: {', '.join(missing)}",
                )

        # Si no se encontró ninguna etiqueta en texto, buscar si hay una imagen escaneada preliminar
        if not found_any:
            scanned_images = []
            for p in self.paragraphs:
                est_page = p.get("estimated_page", 1)
                # Solo buscar en las páginas preliminares
                if est_page > 6:
                    break
                for d in p.get("drawings", []):
                    if d.get("width", 0) > 10.0 and d.get("height", 0) > 14.0:
                        scanned_images.append({
                            "p_idx": p["index"],
                            "page": est_page,
                            "width": d["width"],
                            "height": d["height"]
                        })

            if scanned_images:
                # Si hay más de una imagen escaneada, la segunda suele ser la Hoja de Jurados / Acta
                target = scanned_images[1] if len(scanned_images) >= 2 else scanned_images[0]
                self._add("Hoja de Jurados", "Presencia de Hoja de Jurados", "warning",
                          f"Se ha detectado la Hoja de Jurados / Acta de Sustentación en formato de documento escaneado "
                          f"({target['width']} cm x {target['height']} cm) en la Pág. {target['page']}. "
                          f"Esto es correcto para conservar las firmas manuscritas. Asegúrese de que no haya firmas mezcladas "
                          f"(físicas y digitales en el mismo folio) y que la legibilidad de los jurados sea óptima.",
                          "Documento escaneado firmado", "Presente como Imagen", p_idx=target["p_idx"], p_text="[Imagen Escaneada]")
            else:
                self._add("Hoja de Jurados", "Presencia de Hoja de Jurados", "warning",
                          "No se detectaron etiquetas de texto de la Hoja de Jurados ('ÁREA:', 'TEMA:', 'FECHA DE SUSTENTACIÓN:') "
                          "ni imágenes de documentos escaneados en las hojas preliminares. Asegúrese de insertar este folio obligatorio.",
                          "Presente (Texto o Escáner)", "No detectado")

    def _audit_fecha_sustentacion(self, p, txt):
        """
        FECHA DE SUSTENTACIÓN: debe cumplir:
        - Etiqueta en MAYÚSCULAS
        - Toda la línea en Negrita
        - Alineación: Derecha
        - Espaciado: anterior 10pt, posterior 0pt
        - Sangría: sin sangría de ningún tipo
        """
        align = p.get('alignment', 'left')
        bold_runs = [r.get('bold') for r in p.get('runs', []) if r.get('text', '').strip()]
        is_bold = all(bold_runs) if bold_runs else False
        indent_left_cm = round(p.get('indent_left') or 0, 2)
        indent_first_cm = round(p.get('indent_first') or 0, 2)
        indent_hanging_cm = round(p.get('indent_hanging') or 0, 2)
        s_before = p.get('spacing_before', 0) or 0
        s_after = p.get('spacing_after', 0) or 0
        line_spacing = p.get('line_spacing')

        # Validar que la etiqueta esté en MAYÚSCULAS
        label_match = re.match(r'^(FECHA\s+DE\s+SUSTENTACI[ÓO]N\s*:)', txt, re.IGNORECASE)
        label_text = label_match.group(1) if label_match else txt.split(':')[0] + ':'
        label_letters = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ]', '', label_text)
        is_uppercase = label_letters == label_letters.upper() if label_letters else True

        # Evaluar cada regla
        ok_case = is_uppercase
        ok_bold = is_bold
        ok_align = align == 'right'
        ok_s_before = abs(s_before - 10.0) < 2.0
        ok_s_after = s_after < 1.0
        ok_indent = abs(indent_left_cm) < 0.1 and abs(indent_first_cm) < 0.1 and abs(indent_hanging_cm) < 0.1
        ok_line_spacing = line_spacing is None or abs(line_spacing - 1.5) < 0.15

        align_str = self._align_display(align)

        passed = ok_case and ok_bold and ok_align and ok_s_before and ok_s_after and ok_indent and ok_line_spacing

        if passed:
            expected_str = "Correcto"
            actual_str = "Correcto"
        else:
            req_list = []
            act_list = []
            if not ok_case:
                req_list.append("MAYÚSCULAS")
                act_list.append("Minúsculas")
            if not ok_bold:
                req_list.append("Negrita")
                act_list.append("Normal")
            if not ok_align:
                req_list.append("Derecha")
                act_list.append(align_str)
            if not ok_s_before:
                req_list.append("Esp. ant 10pt")
                act_list.append(f"{s_before}pt")
            if not ok_s_after:
                req_list.append("Esp. post 0pt")
                act_list.append(f"{s_after}pt")
            if not ok_indent:
                req_list.append("Sin sangría")
                act_list.append(f"Sangría: izq {indent_left_cm}cm, 1ra {indent_first_cm}cm, fran {indent_hanging_cm}cm")
            if not ok_line_spacing:
                req_list.append("Interlineado 1.5")
                act_list.append(f"{line_spacing}")
            expected_str = ", ".join(req_list)
            actual_str = ", ".join(act_list)

        self._add("Hoja de Jurados", "Formato \"FECHA DE SUSTENTACIÓN:\"",
                  "passed" if passed else "error",
                  "La etiqueta 'FECHA DE SUSTENTACIÓN:' debe estar en MAYÚSCULAS, Negrita, alineada a la DERECHA, con espaciado anterior de 10pt y posterior de 0pt, sin sangría de ningún tipo e interlineado 1.5.",
                  expected_str, actual_str,
                  p_idx=p['index'], p_text=txt)

    def _audit_area_tema(self, p, txt, etiqueta):
        """
        ÁREA: y TEMA: deben cumplir:
        - Etiqueta (ÁREA: / TEMA:) en MAYÚSCULAS y NEGRITA
        - Contenido después en minúscula y SIN negrita
        - Alineación: Izquierda
        - Espaciado: anterior 0pt, posterior 0pt
        - Sangría: sin sangría de ningún tipo
        """
        align = p.get('alignment', 'left')
        indent_left_cm = round(p.get('indent_left') or 0, 2)
        indent_first_cm = round(p.get('indent_first') or 0, 2)
        indent_hanging_cm = round(p.get('indent_hanging') or 0, 2)
        s_before = p.get('spacing_before', 0) or 0
        s_after = p.get('spacing_after', 0) or 0
        line_spacing = p.get('line_spacing')

        # Separar label (ÁREA: / TEMA:) del contenido
        colon_idx = txt.find(':')
        label_text = txt[:colon_idx + 1] if colon_idx != -1 else txt
        content_text = txt[colon_idx + 1:].strip() if colon_idx != -1 else ""

        # Verificar label en MAYÚSCULAS y NEGRITA
        label_letters = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ]', '', label_text)
        label_is_upper = label_letters == label_letters.upper() if label_letters else True

        # Verificar bold por runs (label vs content)
        label_bold = False
        content_bold = False
        content_lower = True
        acc = 0
        for r in p.get('runs', []):
            r_txt = r.get('text', '')
            if not r_txt:
                continue
            r_bold = r.get('bold', False)
            r_upper = r_txt.isupper() if r_txt.strip() else True
            for c in r_txt:
                if acc < colon_idx + 1:
                    if not label_bold and r_bold:
                        label_bold = True
                else:
                    if not content_bold and r_bold:
                        content_bold = True
                    if c.isalpha() and c.isupper():
                        content_lower = False
                acc += 1

        ok_align = align == 'left'
        ok_s_before = s_before < 1.0
        ok_s_after = s_after < 1.0
        ok_indent = abs(indent_left_cm) < 0.1 and abs(indent_first_cm) < 0.1 and abs(indent_hanging_cm) < 0.1
        ok_line_spacing = line_spacing is None or abs(line_spacing - 1.5) < 0.15

        align_str = self._align_display(align)

        req_list = []
        act_list = []
        if not label_is_upper:
            req_list.append("Label MAYÚSCULAS")
            act_list.append("Label minúscula")
        if not label_bold:
            req_list.append("Label NEGRITA")
            act_list.append("Label normal")
        if content_bold:
            req_list.append("Contenido sin negrita")
            act_list.append("Contenido en negrita")
        if not content_lower and content_text:
            req_list.append("Contenido minúscula")
            act_list.append("Contenido mayúscula")
        if not ok_align:
            req_list.append("Izquierda")
            act_list.append(align_str)
        if not ok_s_before:
            req_list.append("Esp. ant 0pt")
            act_list.append(f"{s_before}pt")
        if not ok_s_after:
            req_list.append("Esp. post 0pt")
            act_list.append(f"{s_after}pt")
        if not ok_indent:
            req_list.append("Sin sangría")
            act_list.append(f"Sangría: izq {indent_left_cm}cm, 1ra {indent_first_cm}cm, fran {indent_hanging_cm}cm")
        if not ok_line_spacing:
            req_list.append("Interlineado 1.5")
            act_list.append(f"{line_spacing}")

        passed = len(req_list) == 0
        expected_str = ", ".join(req_list) if req_list else "Correcto"
        actual_str = ", ".join(act_list) if act_list else "Correcto"

        self._add("Hoja de Jurados", f"Formato \"{etiqueta}:\"",
                  "passed" if passed else "error",
                  f"La etiqueta '{etiqueta}:' debe estar en MAYÚSCULAS y NEGRITA; el contenido después debe ir en minúscula y SIN negrita. Alineación izquierda, espaciado 0pt, sin sangría, interlineado 1.5.",
                  expected_str, actual_str,
                  p_idx=p['index'], p_text=txt)

    def _audit_cargo_jurado(self, p, txt, cargo_label):
        """
        Valida formato de cargos del jurado (Guía UNAP pág. 7):
        - Etiqueta en MAYÚSCULAS, negrita
        - Sangría izquierda 6cm
        - Espaciado posterior 30pt (separa de siguiente cargo)
        - Tamaño 12pt
        - Verificar que en la línea siguiente esté el nombre del jurado a 11pt
        """
        align = p.get('alignment', 'left')
        bold_runs = [r.get('bold') for r in p.get('runs', []) if r.get('text', '').strip()]
        is_bold = all(bold_runs) if bold_runs else False
        l_cm = round(p.get('indent_left') or 0, 2)
        s_before = p.get('spacing_before', 0) or 0
        s_after = p.get('spacing_after', 0) or 0
        size, _, _, _ = self._get_p_props(p)
        line_spacing = p.get('line_spacing')

        # Interlineado 1.5 (Guía UNAP)
        if line_spacing is not None and abs(line_spacing - 1.5) > 0.15:
            self._add(
                "Hoja de Jurados",
                f"Interlineado Cargo \"{cargo_label}\"",
                "error",
                f"El cargo '{cargo_label}' debe tener interlineado 1.5.",
                "1.5",
                f"{line_spacing}",
                p_idx=p['index'],
                p_text=txt,
            )

        # Capitalización: MAYÚSCULAS
        txt_letters = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ]', '', txt)
        is_uppercase = not any(c.islower() for c in txt_letters) if txt_letters else True

        # Alineación Izquierda
        if align != 'left':
            self._add(
                "Hoja de Jurados",
                f"Alineación Cargo \"{cargo_label}\"",
                "error",
                f"El cargo '{cargo_label}' debe estar alineado a la IZQUIERDA.",
                "Izquierda",
                self._align_display(align),
                p_idx=p['index'],
                p_text=txt,
            )

        # Tamaño 12pt
        if size and abs(size - 12) > 0.5:
            self._add(
                "Hoja de Jurados",
                f"Tamaño Cargo \"{cargo_label}\"",
                "error",
                f"El cargo '{cargo_label}' debe ser de 12pt.",
                "12pt",
                f"{size}pt",
                p_idx=p['index'],
                p_text=txt,
            )

        # Sangría: sin sangría de ningún tipo
        if abs(l_cm - 0.0) > 0.1:
            self._add(
                "Hoja de Jurados",
                f"Sangría Cargo \"{cargo_label}\"",
                "error",
                f"El cargo '{cargo_label}' debe estar sin sangría de ningún tipo.",
                "Sin sangría",
                f"Izq {l_cm}cm",
                p_idx=p['index'],
                p_text=txt,
            )

        # Negrita: debe estar en NEGRITA
        if not is_bold:
            self._add(
                "Hoja de Jurados",
                f"Negrita Cargo \"{cargo_label}\"",
                "error",
                f"El cargo '{cargo_label}' debe estar en NEGRITA.",
                "Negrita",
                "Normal",
                p_idx=p['index'],
                p_text=txt,
            )

        # MAYÚSCULAS
        if not is_uppercase:
            self._add(
                "Hoja de Jurados",
                f"Mayúsculas Cargo \"{cargo_label}\"",
                "error",
                f"El cargo '{cargo_label}' debe estar en MAYÚSCULAS.",
                "Mayúsculas",
                "Minúsculas",
                p_idx=p['index'],
                p_text=txt,
            )

        # Espaciado anterior 0pt / posterior 0pt
        if abs(s_before - 0.0) > 1.0:
            self._add(
                "Hoja de Jurados",
                f"Espaciado Anterior Cargo \"{cargo_label}\"",
                "error",
                f"El cargo '{cargo_label}' debe tener espaciado anterior de 0pt.",
                "0pt",
                f"{s_before}pt",
                p_idx=p['index'],
                p_text=txt,
            )
        if abs(s_after - 0.0) > 1.0:
            self._add(
                "Hoja de Jurados",
                f"Espaciado Posterior Cargo \"{cargo_label}\"",
                "error",
                f"El cargo '{cargo_label}' debe tener espaciado posterior de 0pt.",
                "0pt",
                f"{s_after}pt",
                p_idx=p['index'],
                p_text=txt,
            )

        # Buscar el siguiente párrafo no vacío (debería ser el nombre del jurado a 11pt)
        idx = p['index']
        for j in range(idx + 1, min(idx + 5, len(self.paragraphs))):
            next_p = self.paragraphs[j]
            next_txt = next_p['text'].strip()
            if not next_txt:
                continue
            # Saltar separadores como "_____________"
            if re.match(r'^[_\s—–\-]+$', next_txt):
                continue
            # Verificar tamaño del nombre del jurado
            next_size, _, _, _ = self._get_p_props(next_p)
            if next_size and abs(next_size - 11) > 0.5:
                self._add(
                    "Hoja de Jurados",
                    f"Tamaño Nombre Jurado ({cargo_label})",
                    "warning",
                    f"El nombre del jurado correspondiente a '{cargo_label}' debe ser de 11pt "
                    f"(excepción a la regla general de 12pt, según Guía UNAP pág. 7).",
                    "11pt",
                    f"{next_size}pt",
                    p_idx=next_p['index'],
                    p_text=next_txt,
                )
            break
