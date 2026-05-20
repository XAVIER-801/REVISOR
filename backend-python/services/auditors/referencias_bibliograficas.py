"""
referencias_bibliograficas.py - Auditoría de la sección obligatoria de REFERENCIAS BIBLIOGRÁFICAS.

Reglas de la guía:
- Título 'VII. REFERENCIAS BIBLIOGRÁFICAS': 16pt, centrado, negrita, espaciado 0/10, interlineado 2.0, sin sangría.
- Entradas de referencia (APA / Vancouver / IEEE, etc.):
  * Tamaño: 12pt.
  * Alineación: Justificada.
  * Interlineado: 1.5 (Obligatorio en esta sección, a diferencia del interlineado 2.0 del resto del documento).
  * Sangría Izquierda: 0cm.
  * Sangría Francesa (Hanging Indent): 1.25cm.
"""
import re
from .base_auditor import BaseAuditor


class ReferenciasBibliograficasAuditor(BaseAuditor):

    def audit(self):
        found_section = False
        p_idx = 0
        paragraphs_in_sec = []

        # 1. Capturar párrafos de la sección de Referencias
        for p in self.paragraphs:
            norm = p["norm"]
            if "REFERENCIAS BIBLIOGRAFICAS" in norm or "REFERENCIAS BIBLIOGRÁFICAS" in norm:
                # Asegurar que no sea una mención en índices
                sec_upper = p.get("section", "").upper()
                if "INDICE" in sec_upper or "ÍNDICE" in sec_upper:
                    continue
                found_section = True
                p_idx = p["index"]
                
                # Auditar el título de Referencias
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
                    self._add("Referencias", "Título Referencias Bibliográficas", "passed",
                              "El título 'REFERENCIAS BIBLIOGRÁFICAS' cumple perfectamente con la jerarquía de Nivel 1 final.",
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
                    self._add("Referencias", "Título Referencias Bibliográficas", "error",
                              "El título de Referencias debe ser de 16pt, centrado, en negrita, con espaciado anterior 0pt y posterior 10pt, e interlineado 2.0.",
                              ", ".join(req_list), ", ".join(act_list), p_idx=p_idx, p_text=txt)
                continue

            if found_section:
                # Terminar captura si empieza ANEXOS
                if "ANEXOS" in norm and not p.get("in_table", False):
                    break
                if p["text"].strip():
                    paragraphs_in_sec.append(p)

        if not found_section:
            self._add("Referencias", "Presencia de Referencias", "error",
                      "No se encontró la sección obligatoria de 'REFERENCIAS BIBLIOGRÁFICAS' en el documento.",
                      "Presente", "Ausente")
            return

        self._add("Referencias", "Presencia de Referencias", "passed",
                  "Se encontró correctamente la sección obligatoria de 'REFERENCIAS BIBLIOGRÁFICAS'.",
                  "Presente", "Presente", p_idx=p_idx, p_text="REFERENCIAS BIBLIOGRÁFICAS")

        # 2. Auditar cada entrada bibliográfica
        for p in paragraphs_in_sec:
            txt = p["text"].strip()
            # Omitir textos muy cortos que puedan ser separadores
            if len(txt) < 10:
                continue

            align = p.get("alignment", "left")
            size, _, _, _ = self._get_p_props(p)
            size = size or 0
            l_cm = round((p.get("indent_left") or 0) / 567.0, 2)
            h_cm = round((p.get("indent_hanging") or 0) / 567.0, 2)
            line_spacing = p.get("line_spacing", 1.5)

            # Comprobar estilo APA o Vancouver
            # Vancouver suele empezar con número "[1]" o "1."
            is_vancouver = bool(re.match(r'^(\[\d+\]|\d+\.?)\s+', txt))

            ok_size = size == 12 or size == 0
            ok_align = align in ["both", "justify"]
            ok_spacing = line_spacing is not None and abs(line_spacing - 1.5) < 0.2
            
            # APA exige sangría francesa de 1.25cm, Vancouver suele ser alineada a la izquierda (francesa 0cm o similar)
            if is_vancouver:
                # Para Vancouver, se permite sangría izquierda de 0cm
                ok_indent = abs(l_cm) < 0.2
                expected_indent_str = "Izq 0cm (Vancouver)"
            else:
                # Para APA, exige sangría francesa de 1.25cm
                ok_indent = abs(l_cm) < 0.1 and abs(h_cm - 1.25) < 0.2
                expected_indent_str = "Izq 0cm, Francesa 1.25cm (APA)"

            passed = ok_size and ok_align and ok_spacing and ok_indent

            if passed:
                self._add("Referencias", f"Formato Entrada: {txt[:20]}...", "passed",
                          "La referencia bibliográfica cumple perfectamente con el formato exigido.",
                          f"12pt, Justificado, Interlineado 1.5, {expected_indent_str}", "Cumple", p_idx=p["index"], p_text=txt)
            else:
                req_list = []
                act_list = []
                if not ok_size:
                    req_list.append("12pt")
                    act_list.append(f"{size}pt")
                if not ok_align:
                    req_list.append("Justificada")
                    act_list.append(align)
                if not ok_spacing:
                    req_list.append("Interlineado 1.5")
                    act_list.append(str(line_spacing))
                if not ok_indent:
                    req_list.append(expected_indent_str)
                    act_list.append(f"Izq {l_cm}cm, Francesa {h_cm}cm")

                self._add("Referencias", f"Formato Entrada: {txt[:20]}...", "error",
                          f"Las entradas de Referencias Bibliográficas deben tener tamaño 12pt, alineación Justificada, interlineado de 1.5 y sangría francesa de 1.25cm (APA).",
                          ", ".join(req_list), ", ".join(act_list), p_idx=p["index"], p_text=txt)
