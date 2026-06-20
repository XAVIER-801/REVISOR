"""
conclusiones_recomendaciones.py - Auditoría de las secciones obligatorias de CONCLUSIONES y RECOMENDACIONES.

Reglas de la guía:
- Títulos 'V. CONCLUSIONES' y 'VI. RECOMENDACIONES': 16pt, centrado, negrita.
- Contenido (Casos permitidos):
  * CASO 1 (Enumerativo):
    - Comienza con 'PRIMERA:', 'SEGUNDA:', etc. en Negrita y Mayúsculas.
    - Alineación: Justificada.
    - Interlineado: 2.0.
    - Sangría Izquierda: 0cm, Sangría Francesa: 2.5cm.
  * CASO 2 (Viñetas):
    - Usa viñeta '-' o '•'.
    - Alineación: Justificada.
    - Interlineado: 2.0.
    - Sangría Izquierda: 0cm, Sangría Francesa: 0.75cm.
"""
import re
from .base_auditor import BaseAuditor


class ConclusionesRecomendacionesAuditor(BaseAuditor):

    def audit(self):
        self._audit_section("CONCLUSIONES", "V. CONCLUSIONES")
        self._audit_section("RECOMENDACIONES", "VI. RECOMENDACIONES")

    def _audit_section(self, key_search, title_expected):
        found_section = False
        p_idx = 0
        paragraphs_in_sec = []

        # 1. Capturar párrafos de la sección usando el campo `section`
        #    (calculado por word_engine.py, evita falsos positivos por
        #     palabras como "conclusiones" en texto corriente)
        in_section = False
        for p in self.paragraphs:
            sec = p.get("section", "").upper()
            if not in_section:
                if key_search == sec and not p.get("in_table", False):
                    txt_raw = p["text"]
                    # Saltar entrada del Índice General
                    if "...." in txt_raw or re.search(r"\s+\d+\s*$", txt_raw.strip()):
                        continue
                    found_section = True
                    in_section = True
                    p_idx = p["index"]
                    continue
            else:
                # Salir cuando cambie la sección
                if key_search != sec or p.get("in_table", False):
                    break
                if p["text"].strip():
                    paragraphs_in_sec.append(p)

        if not found_section:
            self._add("Secciones Obligatorias", f"Presencia de {key_search}", "error",
                      f"No se encontró la sección obligatoria de '{title_expected}' en el documento.",
                      "Presente", "Ausente")
            return

        self._add("Secciones Obligatorias", f"Presencia de {key_search}", "passed",
                  f"Se encontró correctamente la sección obligatoria de '{title_expected}'.",
                  "Presente", "Presente", p_idx=p_idx, p_text=title_expected)

        # 2. Auditar cada párrafo del contenido de Conclusiones/Recomendaciones
        for p in paragraphs_in_sec:
            txt = p["text"].strip()
            if len(txt) < 3:
                continue

            align = p.get("alignment", "left")
            l_cm = round(p.get("indent_left") or 0, 2)
            f_cm = round(p.get("indent_first") or 0, 2)
            h_cm = round(p.get("indent_hanging") or 0, 2)
            line_spacing = p.get("line_spacing", 2.0)

            # Identificar si es CASO 1 (Enumeración "PRIMERA:", etc.)
            is_caso1 = bool(re.match(r'^(PRIMER[AO]|SEGUND[AO]|TERCER[AO]|CUART[AO]|QUINT[AO]|SEXT[AO]|SÉPTIM[AO]|OCTAV[AO]|NOVEN[AO]|DÉCIM[AO])\s*:', txt.upper()))
            
            # Identificar si es CASO 2 (Viñetas "-" o "•")
            is_bullet = p.get("is_bullet", False) or txt.startswith("-") or txt.startswith("•")
            
            s_after = p.get("spacing_after", 0)
            s_before = p.get("spacing_before", 0)

            if is_caso1:
                # Validar CASO 1: Sangría izquierda 0cm, francesa 2.5cm
                # Adicional: espaciado anterior 0/posterior 10, etiqueta PRIMERA: en negrita
                ok_align = align == 'both'
                ok_indent = abs(l_cm) < 0.1 and abs(h_cm - 2.5) < 0.2
                ok_no_first = abs(f_cm) < 0.1
                ok_spacing = line_spacing is not None and abs(line_spacing - 2.0) < 0.15

                # Espaciado anterior 0pt
                if s_before > 1.0:
                    self._add("Secciones Obligatorias",
                              f"Espaciado Anterior {key_search} (Caso 1): {txt[:15]}...",
                              "error",
                              f"Las conclusiones/recomendaciones del Caso 1 deben tener espaciado "
                              f"anterior de 0pt.",
                              "0pt", f"{s_before}pt", p_idx=p["index"], p_text=txt)

                # Sin sangría de primera línea
                if not ok_no_first:
                    self._add("Secciones Obligatorias",
                              f"Sangría primera línea {key_search} (Caso 1): {txt[:15]}...",
                              "error",
                              f"Las conclusiones/recomendaciones del Caso 1 NO deben tener sangría "
                              f"de primera línea.",
                              "0cm", f"{f_cm}cm", p_idx=p["index"], p_text=txt)

                # Espaciado posterior 10pt
                if abs(s_after - 10.0) > 1.5:
                    self._add("Secciones Obligatorias",
                              f"Espaciado Posterior {key_search} (Caso 1): {txt[:15]}...",
                              "error",
                              f"Las conclusiones/recomendaciones del Caso 1 deben tener espaciado "
                              f"posterior de 10pt entre cada una.",
                              "10pt", f"{s_after}pt", p_idx=p["index"], p_text=txt)

                # PRIMERA:, SEGUNDA:, etc. deben tener etiqueta en negrita
                m_label = re.match(r'^(PRIMER[AO]|SEGUND[AO]|TERCER[AO]|CUART[AO]|QUINT[AO]|'
                                   r'SEXT[AO]|S[ÉE]PTIM[AO]|OCTAV[AO]|NOVEN[AO]|D[ÉE]CIM[AO]):',
                                   txt.upper())
                if m_label:
                    label = m_label.group(0)
                    if not self._check_prefix_bold(p, len(label)):
                        self._add("Secciones Obligatorias",
                                  f"Etiqueta en negrita {key_search}: {label}",
                                  "warning",
                                  f"La etiqueta '{label}' debería estar en negrita para destacarla.",
                                  "Negrita", "Normal", p_idx=p["index"], p_text=txt)

                passed = ok_align and ok_indent and ok_no_first and ok_spacing
                if passed:
                    self._add("Secciones Obligatorias", f"Formato {key_search} (Caso 1): {txt[:15]}...", "passed",
                              f"La conclusión/recomendación sigue correctamente las reglas del Caso 1 (Sangría francesa 2.5cm, Justificado, Interlineado 2.0, sin sangría primera línea).",
                              "Justificado, Izq 0cm, Francesa 2.5cm, Interlineado 2.0, Sin 1ra línea", "Cumple", p_idx=p["index"], p_text=txt)
                else:
                    req_list = []
                    act_list = []
                    if not ok_align:
                        req_list.append("Justificada")
                        act_list.append(self._align_display(align))
                    if not ok_indent:
                        req_list.append("Izq 0cm, Francesa 2.5cm")
                        act_list.append(f"Izq {l_cm}cm, Francesa {h_cm}cm")
                    if not ok_no_first:
                        req_list.append("Sin sangría 1ra línea")
                        act_list.append(f"1ra línea {f_cm}cm")
                    if not ok_spacing:
                        req_list.append("Interlineado 2.0")
                        act_list.append(str(line_spacing))
                    self._add("Secciones Obligatorias", f"Formato {key_search} (Caso 1): {txt[:15]}...", "error",
                              f"Para el Caso 1 (enumerativo), el texto debe estar Justificado, con interlineado 2.0, sangría izquierda 0cm y sangría francesa de 2.5cm, sin sangría de primera línea.",
                              ", ".join(req_list), ", ".join(act_list), p_idx=p["index"], p_text=txt)

            elif is_bullet:
                # Validar CASO 2: Sangría izquierda 0cm, francesa 0.75cm
                ok_align = align == 'both'
                ok_indent = abs(l_cm) < 0.1 and abs(h_cm - 0.75) < 0.2
                ok_spacing = line_spacing is not None and abs(line_spacing - 2.0) < 0.15

                # Espaciado anterior 0pt
                if s_before > 1.0:
                    self._add("Secciones Obligatorias",
                              f"Espaciado Anterior {key_search} (Caso 2): {txt[:15]}...",
                              "error",
                              f"Las viñetas de conclusiones/recomendaciones (Caso 2) deben tener "
                              f"espaciado anterior de 0pt.",
                              "0pt", f"{s_before}pt", p_idx=p["index"], p_text=txt)

                # Espaciado posterior 10pt entre viñetas (igual que Caso 1)
                if abs(s_after - 10.0) > 1.5:
                    self._add("Secciones Obligatorias",
                              f"Espaciado Posterior {key_search} (Caso 2): {txt[:15]}...",
                              "warning",
                              f"Las viñetas de conclusiones/recomendaciones (Caso 2) deben tener "
                              f"espaciado posterior de 10pt.",
                              "10pt", f"{s_after}pt", p_idx=p["index"], p_text=txt)

                passed = ok_align and ok_indent and ok_spacing
                if passed:
                    self._add("Secciones Obligatorias", f"Formato {key_search} (Caso 2): {txt[:15]}...", "passed",
                              f"La conclusión/recomendación sigue correctamente las reglas del Caso 2 (Sangría francesa 0.75cm, Justificado, Interlineado 2.0).",
                              "Justificado, Izq 0cm, Francesa 0.75cm, Interlineado 2.0", "Cumple", p_idx=p["index"], p_text=txt)
                else:
                    req_list = []
                    act_list = []
                    if not ok_align:
                        req_list.append("Justificada")
                        act_list.append(self._align_display(align))
                    if not ok_indent:
                        req_list.append("Izq 0cm, Francesa 0.75cm")
                        act_list.append(f"Izq {l_cm}cm, Francesa {h_cm}cm")
                    if not ok_spacing:
                        req_list.append("Interlineado 2.0")
                        act_list.append(str(line_spacing))
                    self._add("Secciones Obligatorias", f"Formato {key_search} (Caso 2): {txt[:15]}...", "error",
                              f"Para el Caso 2 (viñetas), el texto debe estar Justificado, con interlineado 2.0, sangría izquierda 0cm y sangría francesa de 0.75cm.",
                              ", ".join(req_list), ", ".join(act_list), p_idx=p["index"], p_text=txt)
            else:
                # No encaja en ningún caso oficial de la UNA Puno
                self._add("Secciones Obligatorias", f"Estructura de entrada {key_search}: {txt[:15]}...", "warning",
                          f"Las conclusiones y recomendaciones deben redactarse bajo el Caso 1 (Ej: 'PRIMERA: ...') o el Caso 2 (Ej: '- ...'). Por favor, adapte el formato.",
                          "Caso 1 (PRIMERA:) o Caso 2 (Viñetas)", "Texto libre ordinario", p_idx=p["index"], p_text=txt)

    def _check_prefix_bold(self, p, prefix_len):
        accumulated = 0
        for r in p.get("runs", []):
            r_txt = r.get("text", "")
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
