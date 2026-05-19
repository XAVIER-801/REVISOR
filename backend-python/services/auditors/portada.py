"""
portada.py - Auditoría de la Portada (primera página).

Reglas implementadas:
- Título de la Universidad: 18pt, Negrita, Centrado
- Todo texto fuera de paréntesis: MAYÚSCULAS y Negrita
- Frase "PRESENTADA POR:" debe terminar con dos puntos
- Frase "PARA OPTAR EL TÍTULO PROFESIONAL DE:" debe terminar con dos puntos
- Logo: dimensiones 4.33cm x 4.68cm
- Fuente: Times New Roman en toda la portada
"""
import re
from .base_auditor import BaseAuditor


class PortadaAuditor(BaseAuditor):

    def audit(self):
        cover_paragraphs = [p for p in self.paragraphs if p.get("is_cover")]
        if not cover_paragraphs:
            return

        # 1. Validar que la portada empiece con "UNIVERSIDAD NACIONAL DEL ALTIPLANO"
        first_text_p = None
        for p in cover_paragraphs:
            if p["text"].strip():
                first_text_p = p
                break

        if first_text_p:
            txt = first_text_p["text"].strip()
            norm = first_text_p["norm"]
            size, bold, italic, font = self._get_p_props(first_text_p)
            align = first_text_p.get("alignment", "left")

            is_unap = "UNIVERSIDAD NACIONAL DEL ALTIPLANO" in norm or "UNIVEROSDAD" in norm or "UNIVERSIDAD NACIONAL" in norm

            if is_unap:
                ok_size = abs(size - 18) < 0.5
                ok_bold = bold == True
                ok_align = align == "center"

                status = "passed" if (ok_size and ok_bold and ok_align) else "error"
                msg = "El título inicial de la Universidad en la portada debe ser de tamaño 18pt, en Negrita y Centrado."
                self._add("Portada", "Título de la Universidad", status, msg,
                          "18pt, Negrita, Centrado", f"{size}pt, {'Negrita' if bold else 'Normal'}, {align}",
                          p_idx=first_text_p["index"], p_text=txt)
            else:
                self._add("Portada", "Título de la Universidad", "error",
                          "La portada debe empezar con el nombre de la universidad: 'UNIVERSIDAD NACIONAL DEL ALTIPLANO' en tamaño 18pt, en Negrita y Centrado.",
                          "UNIVERSIDAD NACIONAL DEL ALTIPLANO", txt[:40],
                          p_idx=first_text_p["index"], p_text=txt)
        else:
            self._add("Portada", "Título de la Universidad", "error",
                      "No se encontró texto en la portada.", "UNIVERSIDAD NACIONAL DEL ALTIPLANO", "Vacío")

        # 2. Auditar mayúsculas, negrita y dos puntos en la portada
        for p in cover_paragraphs:
            txt = p["text"].strip()
            if not txt:
                continue

            norm = p["norm"]
            size, bold, italic, font = self._get_p_props(p)

            # A. Identificar qué caracteres están dentro de paréntesis para excluirlos
            inside = False
            is_char_inside = []
            for char in txt:
                if char == '(':
                    inside = True
                    is_char_inside.append(True)
                elif char == ')':
                    is_char_inside.append(True)
                    inside = False
                else:
                    is_char_inside.append(inside)

            # B. Validar MAYÚSCULAS en texto fuera de paréntesis
            has_lowercase = False
            for idx_c, c in enumerate(txt):
                if idx_c < len(is_char_inside) and not is_char_inside[idx_c]:
                    if c.isalpha() and c.islower():
                        has_lowercase = True
                        break

            if has_lowercase:
                self._add("Portada", "Mayúsculas en Portada", "error",
                          f"Todo el texto de la portada (fuera de paréntesis) debe estar en MAYÚSCULAS.",
                          "MAYÚSCULAS", txt[:40], p_idx=p["index"], p_text=txt)
            else:
                self._add("Portada", "Mayúsculas en Portada", "passed",
                          "El texto fuera de paréntesis está correctamente en mayúsculas.",
                          "MAYÚSCULAS", "MAYÚSCULAS", p_idx=p["index"], p_text=txt)

            # C. Validar NEGRITA en texto fuera de paréntesis
            char_idx = 0
            missing_bold = False
            for r in p.get('runs', []):
                r_txt = r['text']
                r_bold = r.get('bold', False)
                for c in r_txt:
                    if char_idx < len(is_char_inside):
                        if not is_char_inside[char_idx]:
                            if c.strip() and c.isalnum() and not r_bold:
                                missing_bold = True
                                break
                    char_idx += 1
                if missing_bold:
                    break

            if missing_bold:
                self._add("Portada", "Estilo de Fuente Portada", "error",
                          f"Todo el texto de la portada (fuera de paréntesis) debe estar en Negrita.",
                          "Negrita", "Normal/Sin Negrita detectado", p_idx=p["index"], p_text=txt)
            else:
                self._add("Portada", "Estilo de Fuente Portada", "passed",
                          "El texto fuera de paréntesis está correctamente en Negrita.",
                          "Negrita", "Negrita", p_idx=p["index"], p_text=txt)

            # D. Validar dos puntos obligatorios solo en las dos frases específicas
            is_presentada = "PRESENTAD" in norm and "POR" in norm
            if is_presentada:
                has_colon = txt.endswith(":")
                status = "passed" if has_colon else "error"
                self._add("Portada", "Frase Presentada Por", status,
                          "La frase 'PRESENTADA POR:' debe terminar obligatoriamente con dos puntos (:).",
                          "PRESENTADA POR:", txt, p_idx=p["index"], p_text=txt)

            is_para_optar = "PARA OPTAR" in norm and "PROFESIONAL DE" in norm
            if is_para_optar:
                has_colon = txt.endswith(":")
                status = "passed" if has_colon else "error"
                self._add("Portada", "Frase Para Optar", status,
                          "La frase 'PARA OPTAR EL TÍTULO PROFESIONAL DE:' debe terminar obligatoriamente con dos puntos (:).",
                          "PARA OPTAR EL TÍTULO PROFESIONAL DE:", txt, p_idx=p["index"], p_text=txt)

        # 3. Validar las dimensiones del logo en la portada
        logo_found = False
        for p in cover_paragraphs:
            drawings = p.get("drawings", [])
            if drawings:
                logo = drawings[0]
                w = logo["width"]
                h = logo["height"]

                ok_width = abs(w - 4.33) <= 0.05
                ok_height = abs(h - 4.68) <= 0.05

                status = "passed" if (ok_width and ok_height) else "error"
                msg = f"El logo de la Universidad en la portada debe tener dimensiones de 4.33 cm de ancho y 4.68 cm de alto. Hallado: {w} cm de ancho, {h} cm de alto."
                self._add("Portada", "Dimensiones del Logo", status, msg,
                          "Ancho: 4.33cm, Alto: 4.68cm", f"Ancho: {w}cm, Alto: {h}cm",
                          p_idx=p["index"])
                logo_found = True
                break

        if not logo_found:
            self._add("Portada", "Dimensiones del Logo", "error",
                      "No se encontró el logo oficial de la Universidad en la portada.",
                      "Ancho: 4.33cm, Alto: 4.68cm", "No encontrado")

        # 4. Validar que la fuente de la portada sea estrictamente Times New Roman
        cover_font_errors = []
        for idx_p, p in enumerate(cover_paragraphs):
            txt = p["text"].strip()
            if not txt:
                continue
            size, bold, italic, font = self._get_p_props(p)
            if font and "times" not in font.lower():
                cover_font_errors.append(f"Párrafo {idx_p+1}: '{txt[:30]}...' tiene fuente '{font}'")

        if cover_font_errors:
            self._add("Portada", "Fuente Times New Roman", "error",
                      "Todos los textos de la portada deben estar escritos en la fuente Times New Roman.",
                      "Times New Roman", f"Se encontraron fuentes distintas: {cover_font_errors[0]}", p_idx=cover_paragraphs[0]["index"])
        else:
            self._add("Portada", "Fuente Times New Roman", "passed",
                      "Todos los textos de la portada están correctamente en la fuente Times New Roman.",
                      "Times New Roman", "Times New Roman", p_idx=cover_paragraphs[0]["index"])
