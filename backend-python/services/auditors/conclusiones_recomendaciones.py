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

        # 1. Capturar párrafos de la sección
        for p in self.paragraphs:
            norm = p["norm"]
            if key_search in norm and not p.get("in_table", False):
                # Asegurar que no sea una mención en índices
                sec_upper = p.get("section", "").upper()
                if "INDICE" in sec_upper or "ÍNDICE" in sec_upper:
                    continue
                found_section = True
                p_idx = p["index"]
                continue
                
            if found_section:
                # Terminar captura si empieza otra sección principal
                if any(k in norm for k in ["RECOMENDACIONES", "REFERENCIAS", "ANEXOS"]) and not p.get("in_table", False):
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
            h_cm = round(p.get("indent_hanging") or 0, 2)
            line_spacing = p.get("line_spacing", 2.0)

            # Identificar si es CASO 1 (Enumeración "PRIMERA:", etc.)
            is_caso1 = bool(re.match(r'^(PRIMER[AO]|SEGUND[AO]|TERCER[AO]|CUART[AO]|QUINT[AO]|SEXT[AO]|SÉPTIM[AO]|OCTAV[AO]|NOVEN[AO]|DÉCIM[AO])\s*:', txt.upper()))
            
            # Identificar si es CASO 2 (Viñetas "-" o "•")
            is_bullet = p.get("is_bullet", False) or txt.startswith("-") or txt.startswith("•")
            
            if is_caso1:
                # Validar CASO 1: Sangría izquierda 0cm, francesa 2.5cm
                ok_align = align in ["both", "justify"]
                ok_indent = abs(l_cm) < 0.1 and abs(h_cm - 2.5) < 0.2
                ok_spacing = line_spacing is not None and abs(line_spacing - 2.0) < 0.15

                passed = ok_align and ok_indent and ok_spacing
                if passed:
                    self._add("Secciones Obligatorias", f"Formato {key_search} (Caso 1): {txt[:15]}...", "passed",
                              f"La conclusión/recomendación sigue correctamente las reglas del Caso 1 (Sangría francesa 2.5cm, Justificado, Interlineado 2.0).",
                              "Justificado, Izq 0cm, Francesa 2.5cm, Interlineado 2.0", "Cumple", p_idx=p["index"], p_text=txt)
                else:
                    req_list = []
                    act_list = []
                    if not ok_align:
                        req_list.append("Justificada")
                        act_list.append(align)
                    if not ok_indent:
                        req_list.append("Izq 0cm, Francesa 2.5cm")
                        act_list.append(f"Izq {l_cm}cm, Francesa {h_cm}cm")
                    if not ok_spacing:
                        req_list.append("Interlineado 2.0")
                        act_list.append(str(line_spacing))
                    self._add("Secciones Obligatorias", f"Formato {key_search} (Caso 1): {txt[:15]}...", "error",
                              f"Para el Caso 1 (enumerativo), el texto debe estar Justificado, con interlineado 2.0, sangría izquierda 0cm y sangría francesa de 2.5cm.",
                              ", ".join(req_list), ", ".join(act_list), p_idx=p["index"], p_text=txt)

            elif is_bullet:
                # Validar CASO 2: Sangría izquierda 0cm, francesa 0.75cm
                ok_align = align in ["both", "justify"]
                ok_indent = abs(l_cm) < 0.1 and abs(h_cm - 0.75) < 0.2
                ok_spacing = line_spacing is not None and abs(line_spacing - 2.0) < 0.15

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
                        act_list.append(align)
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
