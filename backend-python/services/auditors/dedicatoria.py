"""
dedicatoria.py - Auditoría de la sección de DEDICATORIA (Obligatoria).

Reglas de la guía:
- El autor dedica la tesis a quien estime conveniente en una página.
- Si son dos tesistas, cada uno debe redactar su dedicatoria en páginas separadas.
- Título principal 'DEDICATORIA': 16pt, Centrado, Negrita, Espaciado anterior 0pt y posterior 10pt, Interlineado 2.0, sin sangría.
- Contenido: justificado, fuente libre.
- Nombre del autor al final: alineado a la derecha y en negrita.
"""
import re
from .base_auditor import BaseAuditor


class DedicatoriaAuditor(BaseAuditor):

    def audit(self):
        found_section = False
        p_idx = 0
        content_start = -1
        content_end = -1

        for i, p in enumerate(self.paragraphs):
            if i <= self.last_index_idx:
                continue
            sec_upper = p.get('section', '').upper()
            if any(k in sec_upper for k in ['ÍNDICE', 'INDICE', 'TABLA DE CONTENIDOS', 'TABLA DE CONTENIDO']):
                continue

            norm = p["norm"]
            if "DEDICATORIA" in norm and content_start == -1:
                found_section = True
                p_idx = p["index"]

                # Auditar el título "DEDICATORIA"
                txt = p["text"].strip()
                size, is_bold_props, _, _ = self._get_p_props(p)
                size = size or 0
                align = p.get("alignment", "left")
                is_bold = is_bold_props or any(r.get("bold") for r in p.get("runs", []))
                s_before = p.get("spacing_before", 0) or 0
                s_after = p.get("spacing_after", 0) or 0
                line_spacing = p.get("line_spacing", 2.0)

                ok_size = size == 16 or size == 0
                ok_align = align == "center"
                ok_bold = is_bold
                ok_s_before = s_before < 1.0
                ok_s_after = abs(s_after - 10) < 2
                ok_line_spacing = line_spacing is not None and abs(line_spacing - 2.0) < 0.15

                passed = ok_size and ok_align and ok_bold and ok_s_before and ok_s_after and ok_line_spacing

                if passed:
                    self._add("Preliminares", "Título Dedicatoria", "passed",
                              "El título 'DEDICATORIA' cumple perfectamente con la jerarquía de Nivel 1 preliminar.",
                              "16pt, Centrado, Negrita, Espaciado 0/10, Interlineado 2.0", "Cumple", p_idx=p_idx, p_text=txt)
                else:
                    req_list = []
                    act_list = []
                    if not ok_size:
                        req_list.append("16pt")
                        act_list.append(f"{size}pt")
                    if not ok_align:
                        req_list.append("Centrado")
                        act_list.append(align)
                    if not ok_bold:
                        req_list.append("Negrita")
                        act_list.append("Normal")
                    if not ok_s_before:
                        req_list.append("Esp. ant 0pt")
                        act_list.append(f"{s_before}pt")
                    if not ok_s_after:
                        req_list.append("Esp. post 10pt")
                        act_list.append(f"{s_after}pt")
                    if not ok_line_spacing:
                        req_list.append("Interlineado 2.0")
                        act_list.append(f"{line_spacing}")
                    self._add("Preliminares", "Título Dedicatoria", "error",
                              "El título 'DEDICATORIA' debe tener tamaño 16pt, centrado, negrita, espaciado anterior 0pt y posterior 10pt, e interlineado 2.0.",
                              ", ".join(req_list), ", ".join(act_list), p_idx=p_idx, p_text=txt)

                content_start = i + 1
                continue

            # Auditar contenido de la dedicatoria (después del título)
            if content_start != -1 and i >= content_start:
                # Detectar fin de sección (siguiente título de sección)
                txt = p["text"].strip()
                norm = p["norm"]
                if norm in ["AGRADECIMIENTOS", "AGRADECIMIENTO", "INDICE GENERAL", "ÍNDICE GENERAL",
                            "RESUMEN", "ABSTRACT", "INTRODUCCION", "INTRODUCCIÓN"]:
                    content_end = i
                    break

                if not txt:
                    continue

                content_end = i + 1
                content_align = p.get("alignment", "left")
                is_bold = any(r.get("bold") for r in p.get("runs", []) if r.get("text", "").strip())

                # Contenido debe estar justificado
                if content_align != 'both':
                    self._add("Preliminares", "Alineación contenido Dedicatoria", "warning",
                              "El contenido de la dedicatoria debe estar justificado.",
                              "Justificado", self._align_display(content_align), p_idx=p["index"], p_text=txt)

        # Auditar la última línea (nombre del autor) - alineado derecha y negrita
        if content_start != -1 and content_end != -1:
            for i in range(content_end - 1, content_start - 1, -1):
                p = self.paragraphs[i]
                txt = p["text"].strip()
                if not txt:
                    continue
                # Primera línea no vacía desde el final = nombre del autor
                name_align = p.get("alignment", "left")
                name_bold = any(r.get("bold") for r in p.get("runs", []) if r.get("text", "").strip())
                if name_align != "right":
                    self._add("Preliminares", "Nombre autor Dedicatoria", "error",
                              "El nombre del autor en la dedicatoria debe estar alineado a la DERECHA.",
                              "Derecha", self._align_display(name_align), p_idx=p["index"], p_text=txt)
                if not name_bold:
                    self._add("Preliminares", "Nombre autor Dedicatoria", "error",
                              "El nombre del autor en la dedicatoria debe estar en NEGRITA.",
                              "Negrita", "Normal", p_idx=p["index"], p_text=txt)
                break

        if not found_section:
            self._add("Preliminares", "Presencia de Dedicatoria", "error",
                      "No se encontró la sección obligatoria de 'DEDICATORIA' en las páginas preliminares.",
                      "Presente", "Ausente")
