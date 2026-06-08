"""
agradecimientos.py - Auditoría de los Agradecimientos.

Reglas implementadas:
- Título 'AGRADECIMIENTOS': 16pt, Centrado, Negrita, Espaciado 0/10, Interlineado 2.0
- Extensión: máximo 1 página (~600 palabras).
- Contenido: justificado.
- Nombre(s) al final: alineado(s) a la derecha y en negrita.
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

        # Auditar título
        if title_p:
            txt = title_p["text"].strip()
            size, is_bold_props, _, _ = self._get_p_props(title_p)
            size = size or 0
            align = title_p.get("alignment", "left")
            is_bold = is_bold_props or any(r.get("bold") for r in title_p.get("runs", []))
            s_before = title_p.get("spacing_before", 0) or 0
            s_after = title_p.get("spacing_after", 0) or 0
            line_spacing = title_p.get("line_spacing", 2.0)

            ok_size = size == 16 or size == 0
            ok_align = align == "center"
            ok_bold = is_bold
            ok_s_before = s_before < 1.0
            ok_s_after = abs(s_after - 10) < 2
            ok_line_spacing = line_spacing is not None and abs(line_spacing - 2.0) < 0.15

            passed = ok_size and ok_align and ok_bold and ok_s_before and ok_s_after and ok_line_spacing
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
                if not ok_s_before:
                    req_list.append("Esp. ant 0pt")
                    act_list.append(f"{s_before}pt")
                if not ok_s_after:
                    req_list.append("Esp. post 10pt")
                    act_list.append(f"{s_after}pt")
                if not ok_line_spacing:
                    req_list.append("Interlineado 2.0")
                    act_list.append(f"{line_spacing}")
                self._add("Resumen y Abstract", "Título Agradecimientos", "error",
                          "El título de Agradecimientos debe tener tamaño 16pt, centrado, negrita, espaciado anterior 0pt y posterior 10pt, e interlineado 2.0.",
                          ", ".join(req_list), ", ".join(act_list), p_idx=title_p["index"], p_text=txt)

        # Auditar contenido
        if agr_paragraphs:
            # 1. Extensión
            words_agr = len(" ".join(content_agr).split())
            ok_agr = words_agr < 600
            self._add("Resumen y Abstract", "Extensión de Agradecimientos", "passed" if ok_agr else "error",
                      f"Los agradecimientos deben ocupar máximo 1 página. Hallado: ~{words_agr} palabras.",
                      "< 600 palabras", f"~{words_agr} palabras", p_idx=agr_paragraphs[0]["index"], p_text=content_agr[0][:30])

            # 2. Contenido justificado
            for p in agr_paragraphs[:-2]:
                p_align = p.get("alignment", "left")
                if p_align != 'both':
                    self._add("Resumen y Abstract", "Alineación contenido Agradecimientos", "warning",
                              "El contenido de los agradecimientos debe estar justificado.",
                              "Justificado", self._align_display(p_align), p_idx=p["index"], p_text=p["text"][:30])

            # 3. Nombre(s) al final: derecha y negrita
            for p in agr_paragraphs[-2:]:
                txt_p = p["text"].strip()
                if not txt_p:
                    continue
                if len(txt_p.split()) < 2:
                    continue
                p_align = p.get("alignment", "left")
                p_bold = any(r.get("bold") for r in p.get("runs", []) if r.get("text", "").strip())
                if p_align != "right":
                    self._add("Resumen y Abstract", f"Alineación nombre: {txt_p[:20]}...", "error",
                              "Los nombres al final de los agradecimientos deben estar alineados a la DERECHA.",
                              "Derecha", self._align_display(p_align), p_idx=p["index"], p_text=txt_p)
                if not p_bold:
                    self._add("Resumen y Abstract", f"Negrita nombre: {txt_p[:20]}...", "error",
                              "Los nombres al final de los agradecimientos deben estar en NEGRITA.",
                              "Negrita", "Normal", p_idx=p["index"], p_text=txt_p)