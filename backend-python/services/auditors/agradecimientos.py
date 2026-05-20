"""
agradecimientos.py - Auditoría de los Agradecimientos.

Reglas implementadas:
- Extensión de los Agradecimientos: máximo 1 página (~600 palabras).
"""
from .base_auditor import BaseAuditor


class AgradecimientosAuditor(BaseAuditor):

    def audit(self):
        content_agr = []
        capture_agr = False
        title_p = None
        agr_paragraphs = []

        for i, p in enumerate(self.paragraphs):
            if i <= self.last_index_idx:
                continue
            sec_upper = p.get("section", "").upper()
            if "INDICE" in sec_upper or "ÍNDICE" in sec_upper:
                continue

            norm = p["norm"]
            if "AGRADECIMIENTOS" in norm:
                capture_agr = True
                title_p = p
                continue
            if capture_agr and any(k in norm for k in ["INDICE GENERAL", "RESUMEN", "ABSTRACT", "CAPITULO", "INTRODUCCION"]):
                capture_agr = False
                break
            if capture_agr:
                if p["text"].strip():
                    content_agr.append(p["text"])
                    agr_paragraphs.append(p)

        if title_p:
            txt = title_p["text"].strip()
            size, is_bold_props, _, _ = self._get_p_props(title_p)
            size = size or 0
            align = title_p.get("alignment", "left")
            is_bold = is_bold_props or any(r.get("bold") for r in title_p.get("runs", []))
            s_before = title_p.get("spacing_before", 0)
            s_after = title_p.get("spacing_after", 0)
            line_spacing = title_p.get("line_spacing", 2.0)

            ok_size = size == 16 or size == 0
            ok_align = align == "center"
            ok_bold = is_bold
            ok_spacing = (s_before is None or s_before < 1) and (s_after is None or abs(s_after - 10) < 2)
            ok_line_spacing = line_spacing is not None and abs(line_spacing - 2.0) < 0.15

            passed = ok_size and ok_align and ok_bold and ok_spacing and ok_line_spacing
            if passed:
                self._add("Resumen y Abstract", "Título Agradecimientos", "passed",
                          "El título 'AGRADECIMIENTOS' cumple perfectamente con la jerarquía de Nivel 1 preliminar.",
                          "16pt, Centrado, Negrita, Espaciado 0/10, Interlineado 2.0", "Cumple", p_idx=title_p["index"], p_text=txt)
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
                self._add("Resumen y Abstract", "Título Agradecimientos", "error",
                          "El título de Agradecimientos debe tener tamaño 16pt, estar centrado, en negrita, con espaciado anterior 0pt y posterior 10pt, e interlineado 2.0.",
                          ", ".join(req_list), ", ".join(act_list), p_idx=title_p["index"], p_text=txt)

        if content_agr:
            # 1. Extensión
            words_agr = len(" ".join(content_agr).split())
            ok_agr = words_agr < 600
            self._add("Resumen y Abstract", "Extensión de Agradecimientos", "passed" if ok_agr else "error",
                      f"Los agradecimientos deben ocupar máximo 1 página. Hallado: ~{words_agr} palabras.",
                      "< 600 palabras", f"~{words_agr} palabras", p_idx=agr_paragraphs[0]["index"], p_text=content_agr[0][:30])

            # 2. Firmas al final (si son dos tesistas, deben alinearse a la derecha)
            # Detectar líneas de firmas
            firmas = []
            for p in agr_paragraphs[-3:]:
                txt_p = p["text"].strip()
                # Un nombre suele ser de 2 a 4 palabras sin signos de puntuación
                if txt_p and len(txt_p.split()) in [3, 4] and not any(c in txt_p for c in [".", ",", ":", ";"]):
                    firmas.append(p)

            if len(firmas) >= 2:
                # Hay dos firmas (2 tesistas)
                for f in firmas:
                    f_align = f.get("alignment", "left")
                    if f_align != "right":
                        self._add("Resumen y Abstract", f"Alineación Firma: {f['text']}", "error",
                                  "Si son dos tesistas, los nombres al final de los agradecimientos deben estar alineados obligatoriamente a la DERECHA.",
                                  "Derecha", f_align, p_idx=f["index"], p_text=f["text"])
                    else:
                        self._add("Resumen y Abstract", f"Alineación Firma: {f['text']}", "passed",
                                  "Nombre de tesista correctamente alineado a la derecha en los agradecimientos.",
                                  "Derecha", "Derecha", p_idx=f["index"], p_text=f["text"])
