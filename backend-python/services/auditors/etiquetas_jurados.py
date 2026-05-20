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

    def audit(self):
        found_any = False
        
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
        - Negrita
        - Alineación: Derecha
        - Espaciado: anterior 10pt, posterior 0pt
        - Sangría: sin sangría de ningún tipo
        """
        align = p.get('alignment', 'left')
        is_bold = any(r.get('bold') for r in p.get('runs', []) if r.get('text', '').strip())
        indent_left_cm = round(p.get('indent_left') or 0, 2)
        indent_first_cm = round(p.get('indent_first') or 0, 2)
        indent_hanging_cm = round(p.get('indent_hanging') or 0, 2)
        s_before = p.get('spacing_before', 0) or 0
        s_after = p.get('spacing_after', 0) or 0

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

        align_str = "Centrado" if align == "center" else ("Izquierda" if align == "left" else ("Derecha" if align == "right" else "Justificada"))

        passed = ok_case and ok_bold and ok_align and ok_s_before and ok_s_after and ok_indent

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
            expected_str = ", ".join(req_list)
            actual_str = ", ".join(act_list)

        self._add("Hoja de Jurados", "Formato \"FECHA DE SUSTENTACIÓN:\"",
                  "passed" if passed else "error",
                  "La etiqueta 'FECHA DE SUSTENTACIÓN:' debe estar en MAYÚSCULAS, Negrita, alineada a la DERECHA, con espaciado anterior de 10pt y posterior de 0pt, y sin sangría de ningún tipo.",
                  expected_str, actual_str,
                  p_idx=p['index'], p_text=txt)

    def _audit_area_tema(self, p, txt, etiqueta):
        """
        ÁREA: y TEMA: deben cumplir:
        - Etiqueta en MAYÚSCULAS
        - Negrita
        - Alineación: Izquierda
        - Espaciado: anterior 0pt, posterior 0pt
        - Sangría: sin sangría de ningún tipo
        """
        align = p.get('alignment', 'left')
        is_bold = any(r.get('bold') for r in p.get('runs', []) if r.get('text', '').strip())
        indent_left_cm = round(p.get('indent_left') or 0, 2)
        indent_first_cm = round(p.get('indent_first') or 0, 2)
        indent_hanging_cm = round(p.get('indent_hanging') or 0, 2)
        s_before = p.get('spacing_before', 0) or 0
        s_after = p.get('spacing_after', 0) or 0

        # Validar que la etiqueta esté en MAYÚSCULAS
        label_text = txt.split(':')[0] + ':'
        label_letters = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ]', '', label_text)
        is_uppercase = label_letters == label_letters.upper() if label_letters else True

        # Evaluar cada regla
        ok_case = is_uppercase
        ok_bold = is_bold
        ok_align = align == 'left'
        ok_s_before = s_before < 1.0
        ok_s_after = s_after < 1.0
        ok_indent = abs(indent_left_cm) < 0.1 and abs(indent_first_cm) < 0.1 and abs(indent_hanging_cm) < 0.1

        align_str = "Centrado" if align == "center" else ("Izquierda" if align == "left" else ("Derecha" if align == "right" else "Justificada"))

        passed = ok_case and ok_bold and ok_align and ok_s_before and ok_s_after and ok_indent

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
            expected_str = ", ".join(req_list)
            actual_str = ", ".join(act_list)

        self._add("Hoja de Jurados", f"Formato \"{etiqueta}:\"",
                  "passed" if passed else "error",
                  f"La etiqueta '{etiqueta}:' debe estar en MAYÚSCULAS, Negrita, alineada a la IZQUIERDA, con espaciado anterior y posterior de 0pt, y sin sangría de ningún tipo.",
                  expected_str, actual_str,
                  p_idx=p['index'], p_text=txt)
