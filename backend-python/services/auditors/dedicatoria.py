"""
dedicatoria.py - Auditoría de la sección de DEDICATORIA (Obligatoria).

Reglas de la guía:
- El autor dedica la tesis a quien estime conveniente en una página.
- Si son dos tesistas, cada uno debe redactar su dedicatoria en páginas separadas.
- Título principal 'DEDICATORIA': 16pt, Centrado, Negrita, Espaciado anterior 0pt y posterior 10pt, Interlineado 2.0.
- La dedicatoria puede estar escrita con cualquier tipo de fuente y estilo de fuente (libre).
"""
import re
from .base_auditor import BaseAuditor


class DedicatoriaAuditor(BaseAuditor):

    def audit(self):
        found_section = False
        p_idx = 0
        
        for i, p in enumerate(self.paragraphs):
            if i <= self.last_index_idx:
                continue
            sec_upper = p.get('section', '').upper()
            if any(k in sec_upper for k in ['ÍNDICE', 'INDICE', 'TABLA DE CONTENIDOS', 'TABLA DE CONTENIDO']):
                continue

            norm = p["norm"]
            if "DEDICATORIA" in norm:
                found_section = True
                p_idx = p["index"]
                
                # Auditar el título "DEDICATORIA"
                txt = p["text"].strip()
                size, is_bold_props, _, _ = self._get_p_props(p)
                size = size or 0
                align = p.get("alignment", "left")
                is_bold = is_bold_props or any(r.get("bold") for r in p.get("runs", []))
                s_before = p.get("spacing_before", 0)
                s_after = p.get("spacing_after", 0)
                line_spacing = p.get("line_spacing", 2.0)

                ok_size = size == 16 or size == 0
                ok_align = align == "center"
                ok_bold = is_bold
                ok_spacing = (s_before is None or s_before < 1) and (s_after is None or abs(s_after - 10) < 2)
                ok_line_spacing = line_spacing is not None and abs(line_spacing - 2.0) < 0.15

                passed = ok_size and ok_align and ok_bold and ok_spacing and ok_line_spacing
                
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
                    self._add("Preliminares", "Título Dedicatoria", "error",
                              "El título 'DEDICATORIA' debe tener tamaño 16pt, estar centrado, en negrita, con espaciado anterior 0pt y posterior 10pt, e interlineado 2.0.",
                              ", ".join(req_list), ", ".join(act_list), p_idx=p_idx, p_text=txt)
                break

        if not found_section:
            self._add("Preliminares", "Presencia de Dedicatoria", "error",
                      "No se encontró la sección obligatoria de 'DEDICATORIA' en las páginas preliminares.",
                      "Presente", "Ausente")
