"""
capitulo_nivel2.py - Auditoría de Títulos de Nivel 2 Y su Contenido.

Cubre: Títulos como "2.1. PLANTEAMIENTO DEL PROBLEMA"
y los párrafos de contenido que están directamente bajo estos títulos.

Reglas de TÍTULO Nivel 2:
- Alineación: Justificada o Izquierda
- Estilo: Negrita
- Capitalización: MAYÚSCULAS
- Interlineado: 2.0
- Espaciado: anterior 0pt, posterior 10pt
- Sangría: Izq 0cm, Francesa 1.25cm

Reglas de CONTENIDO bajo Nivel 2:
- Estilo: Normal (Sin Negrita)
- Alineación: Justificada
- Interlineado: 2.0
- Espaciado: anterior 0pt, posterior 10pt
- Sangría: Izquierda 0cm, Primera Línea 1.25cm
"""
import re
from .base_auditor import BaseAuditor


class CapituloNivel2Auditor(BaseAuditor):

    def audit(self):
        for i, p in enumerate(self.paragraphs):
            if not p.get("is_in_body"):
                continue
            if p.get("body_level") != 2:
                continue

            # Saltar entradas del índice por si llegan aquí por mala detección
            txt_raw = p['text']
            sec_upper = p.get("section", "").upper()
            style_id = p.get('style_id', '').upper()
            is_toc_style = any(k in style_id for k in ['TOC', 'TDC', 'INDICE', 'ÍNDICE'])
            has_index_content = "\t" in txt_raw or "..." in txt_raw or bool(re.search(r"\s+\d+$", txt_raw.strip()))
            is_in_index_zone = self.last_index_idx != -1 and i <= self.last_index_idx
            is_in_prelim_section = any(k in sec_upper for k in ['ÍNDICE', 'INDICE', 'TABLA DE CONTENIDOS', 'TABLA DE CONTENIDO'])

            if is_toc_style or has_index_content or is_in_index_zone or is_in_prelim_section:
                continue

            txt = p['text'].strip()
            if not txt:
                continue

            norm = p['norm']
            bold = self._is_meaningfully_bold(p)
            align = p.get('alignment', 'left')
            # Indents ya están en cm desde parse_ppr
            l_cm = round(p.get('indent_left') or 0, 2)
            f_cm = round(p.get('indent_first') or 0, 2)
            h_cm = round(p.get('indent_hanging') or 0, 2)

            is_bullet = p.get('is_bullet', False)
            is_title = p.get('is_heading', False)

            # Detectar título de nivel 2 por numeración
            # Regex amplia: captura numeración con o sin espacio tras ella
            numbering_match = re.match(r'^(\d+(?:\.\d+)+)(\.?)(\s*)(.*)', txt.strip())
            numbering_level = None
            if numbering_match:
                num_part = numbering_match.group(1)
                trailing_dot = numbering_match.group(2)
                space_sep = numbering_match.group(3)
                title_text_part = numbering_match.group(4)
                dot_count = num_part.count('.')
                numbering_level = dot_count + 1
                # Solo considerar si realmente tiene texto de título o es un número solo
                if numbering_level < 2 or (not title_text_part.strip() and not space_sep):
                    numbering_level = None

            # Un título es Nivel 2 si tiene numeración manual de nivel 2,
            # o si es un párrafo de título con body_level == 2.
            is_nivel2_title = (numbering_level == 2) or (is_title and p.get('body_level') == 2)

            # ═══ TÍTULO NIVEL 2 ═══
            if is_nivel2_title:
                # ── REGLA: Separación entre numeración y título ──
                # La numeración debe estar separada del texto del título por al menos
                # un espacio o tabulación. Ej: "2.1. TÍTULO" ✓, "2.1.TÍTULO" ✗
                if numbering_match and numbering_level == 2:
                    space_sep = numbering_match.group(3)
                    title_text_part = numbering_match.group(4).strip()
                    if title_text_part and not space_sep:
                        num_str = numbering_match.group(1) + numbering_match.group(2)
                        self._add("Jerarquía", f"Separación Numeración-Título Nivel 2: {txt[:30]}...", "error",
                                  f"La numeración '{num_str}' está pegada al texto del título '{title_text_part[:20]}...'. "
                                  f"Debe haber al menos un espacio o tabulación entre la numeración y el título.",
                                  f"{num_str} {title_text_part[:20]}...",
                                  f"{num_str}{title_text_part[:20]}...",
                                  p_idx=p['index'], p_text=txt)

                # Negrita
                if not bold:
                    self._add("Jerarquía", "Estilo de Fuente Título Nivel 2", "error",
                              "El título de nivel 2 debe estar en Negrita.",
                              "Negrita", "Normal", p_idx=p['index'], p_text=txt)

                # Alineación (Justificada o Izquierda son válidas)
                if align not in ['both', 'justify', 'left']:
                    self._add("Jerarquía", "Alineación Título Nivel 2", "error",
                              "El título de nivel 2 debe tener alineación justificada o alineado a la izquierda.",
                              "Justificada o Izquierda", self._align_display(align), p_idx=p['index'], p_text=txt)

                # Interlineado
                line_spacing = p.get('line_spacing')
                if line_spacing is not None and abs(line_spacing - 2.0) > 0.2:
                    self._add("Jerarquía", "Interlineado Título Nivel 2", "error",
                              "El título de nivel 2 debe tener interlineado 2.0.",
                              "2.0", str(line_spacing), p_idx=p['index'], p_text=txt)

                # Espaciado
                s_before = p.get('spacing_before', 0)
                s_after = p.get('spacing_after', 0)
                if s_before > 1.0:
                    self._add("Jerarquía", "Espaciado Anterior Título Nivel 2", "error",
                              "El título de nivel 2 debe tener espaciado anterior de 0pt.",
                              "0pt", f"{s_before}pt", p_idx=p['index'], p_text=txt)
                if abs(s_after - 10.0) > 1.0:
                    self._add("Jerarquía", "Espaciado Posterior Título Nivel 2", "error",
                              "El título de nivel 2 debe tener espaciado posterior de 10pt.",
                              "10pt", f"{s_after}pt", p_idx=p['index'], p_text=txt)

                # VALIDAR TILDES: "TÍTULO" con tilde (si contiene la palabra)
                if "TITULO" in norm and "TÍTULO" not in txt:
                    self._add("Jerarquía", f"Tilde en Título Nivel 2: {txt[:20]}...", "observation",
                              f"El texto '{txt[:30]}...' debe escribirse 'TÍTULO' con tilde, no 'TITULO'.",
                              "TÍTULO (con tilde)", "TITULO (sin tilde)", p_idx=p['index'], p_text=txt)

                # Capitalización: MAYÚSCULAS
                txt_letters = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ]', '', txt)
                if txt_letters and txt_letters != txt_letters.upper():
                    self._add("Jerarquía", "Capitalización Título Nivel 2", "error",
                              "Los títulos de nivel 2 deben estar completamente en mayúsculas.",
                              "MAYÚSCULAS", txt[:40], p_idx=p['index'], p_text=txt)

                # Sangría: Izq 0cm, Francesa 1.25cm
                exp_l, exp_h = 0.0, 1.25
                ok_l = abs(l_cm - exp_l) <= 0.15
                ok_h = abs(h_cm - exp_h) <= 0.15
                if not ok_l or not ok_h:
                    req_list = []
                    act_list = []
                    if not ok_l:
                        req_list.append(f"Izq {exp_l}cm")
                        act_list.append(f"Izq {l_cm}cm")
                    if not ok_h:
                        req_list.append(f"Fran {exp_h}cm")
                        act_list.append(f"Fran {h_cm}cm")
                    self._add("Jerarquía", "Sangría Título Nivel 2", "error",
                              f"Nivel 2 debe tener Sangría Izquierda {exp_l}cm y Francesa {exp_h}cm.",
                              ", ".join(req_list), ", ".join(act_list), p_idx=p['index'], p_text=txt)
                continue

            # ═══ VIÑETAS → se auditan en vinetas.py ═══
            if is_bullet:
                continue

            # ═══ OTROS TÍTULOS (nivel 3+ que aparecen aquí transitoriamente) ═══
            if is_title:
                continue

            # ═══ CONTENIDO bajo Nivel 2 ═══
            if len(txt) <= 50:
                continue
            if txt.upper().startswith("NOTA:") or txt.upper().startswith("FUENTE:"):
                continue
            if re.match(r"^(TABLA|FIGURA)\s+\d+", norm):
                continue

            if bold:
                self._add("Estructura", "Estilo de Fuente Contenido (Nivel 2)", "warning",
                          "El contenido bajo nivel 2 debe estar en estilo Normal (Sin Negrita).",
                          "Normal (Sin Negrita)", "Negrita", p_idx=p['index'], p_text=txt[:40])

            if align != 'both':
                self._add("Estructura", "Alineación Contenido (Nivel 2)", "error",
                          "El contenido bajo nivel 2 debe tener alineación justificada.",
                          "Justificada", self._align_display(align), p_idx=p['index'], p_text=txt[:40])

            line_spacing = p.get('line_spacing')
            if line_spacing is not None and abs(line_spacing - 2.0) > 0.2:
                self._add("Estructura", "Interlineado Contenido (Nivel 2)", "error",
                          "El contenido bajo nivel 2 debe tener interlineado 2.0.",
                          "2.0", str(line_spacing), p_idx=p['index'], p_text=txt[:40])

            s_before = p.get('spacing_before', 0)
            s_after = p.get('spacing_after', 0)
            if s_before > 1.0:
                self._add("Estructura", "Espaciado Anterior Contenido (Nivel 2)", "error",
                          "El contenido bajo nivel 2 DEBE tener espaciado anterior de 0pt.",
                          "0pt", f"{s_before}pt", p_idx=p['index'], p_text=txt[:40])
            if abs(s_after - 10.0) > 1.0:
                self._add("Estructura", "Espaciado Posterior Contenido (Nivel 2)", "error",
                          "El contenido bajo nivel 2 DEBE tener espaciado posterior de 10pt.",
                          "10pt", f"{s_after}pt", p_idx=p['index'], p_text=txt[:40])

            # Sangría: Izq 0cm, Primera Línea 1.25cm
            ok_l = abs(l_cm - 0.0) <= 0.1
            ok_f = abs(f_cm - 1.25) <= 0.1
            if not ok_l or not ok_f:
                req_list = []
                act_list = []
                if not ok_l:
                    req_list.append("Izq 0.0cm")
                    act_list.append(f"Izq {l_cm}cm")
                if not ok_f:
                    req_list.append("Prim 1.25cm")
                    act_list.append(f"Prim {f_cm}cm")
                self._add("Estructura", "Sangría de Contenido (Nivel 2)", "error",
                          "El contenido bajo nivel 2 DEBE tener Sangría Izquierda 0cm y Primera Línea 1.25cm.",
                          ", ".join(req_list), ", ".join(act_list), p_idx=p['index'], p_text=txt[:40])
