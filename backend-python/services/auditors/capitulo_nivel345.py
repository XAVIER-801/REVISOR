"""
capitulo_nivel345.py - Auditoría de Títulos de Nivel 3, 4 y 5 Y su Contenido.

Cubre: Títulos como "2.3.1. Origen e importancia de la pitahaya"
y los párrafos de contenido que están directamente bajo estos títulos.

Reglas de TÍTULO Nivel 3:
- Alineación: Justificada o Izquierda
- Estilo: Negrita
- Capitalización: Minúsculas (mayúscula inicial)
- Interlineado: 2.0
- Espaciado: anterior 0pt, posterior 10pt
- Sangría: Izq 1.25cm, Francesa 1.25cm

Reglas de TÍTULO Nivel 4/5:
- Igual que nivel 3 pero con Sangría: Izq 2.5cm, Francesa 1.5cm

Reglas de CONTENIDO bajo Nivel 3:
- Sangría: Izquierda 1.25cm, Primera Línea 1.25cm

Reglas de CONTENIDO bajo Nivel 4/5:
- Sangría: Izquierda 2.5cm, Primera Línea 1.25cm
"""
import re
from .base_auditor import BaseAuditor


class CapituloNivel345Auditor(BaseAuditor):

    INDENT_SPECS = {
        3: (1.25, 1.25),
        4: (2.5, 1.5),
        5: (2.5, 1.5),
    }

    CONTENT_INDENT_SPECS = {
        3: (1.25, 1.25),
        4: (2.5, 1.25),
        5: (2.5, 1.25),
    }

    def audit(self):
        for i, p in enumerate(self.paragraphs):
            if not p.get("is_in_body"):
                continue

            body_level = p.get("body_level", 0)
            if body_level < 3:
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
            bold = any(r.get('bold') for r in p.get('runs', []))
            align = p.get('alignment', 'left')
            l_cm = round(p.get('indent_left') or 0, 2)
            f_cm = round(p.get('indent_first') or 0, 2)
            h_cm = round(p.get('indent_hanging') or 0, 2)

            is_bullet = p.get('is_bullet', False)
            is_title = p.get('is_heading', False)

            # Detectar título por numeración
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

            # Un título es Nivel 3/4/5 si tiene numeración manual >= 3,
            # o si es un párrafo de título con body_level >= 3.
            is_title_at_level = (numbering_level is not None and numbering_level >= 3) or (is_title and body_level >= 3)
            eff_level = numbering_level if numbering_level is not None else body_level

            level_label = f"Nivel {body_level}" if body_level <= 5 else "Nivel 5+"

            # ═══ TÍTULO NIVEL 3/4/5 ═══
            if is_title_at_level and eff_level == body_level:
                # ── REGLA: Separación entre numeración y título ──
                # La numeración debe estar separada del texto del título por al menos
                # un espacio o tabulación. Ej: "2.3.1. Título" ✓, "2.3.1.Título" ✗
                if numbering_match and numbering_level is not None and numbering_level >= 3:
                    space_sep = numbering_match.group(3)
                    title_text_part = numbering_match.group(4).strip()
                    if title_text_part and not space_sep:
                        num_str = numbering_match.group(1) + numbering_match.group(2)
                        self._add("Jerarquía", f"Separación Numeración-Título {level_label}: {txt[:30]}...", "error",
                                  f"La numeración '{num_str}' está pegada al texto del título '{title_text_part[:20]}...'. "
                                  f"Debe haber al menos un espacio o tabulación entre la numeración y el título.",
                                  f"{num_str} {title_text_part[:20]}...",
                                  f"{num_str}{title_text_part[:20]}...",
                                  p_idx=p['index'], p_text=txt)

                # Negrita
                if not bold:
                    self._add("Jerarquía", f"Estilo de Fuente Título {level_label}", "error",
                              f"El título de {level_label.lower()} debe estar en Negrita.",
                              "Negrita", "Normal", p_idx=p['index'], p_text=txt)

                # Alineación
                if align not in ['both', 'justify', 'left']:
                    self._add("Jerarquía", f"Alineación Título {level_label}", "error",
                              f"El título de {level_label.lower()} debe tener alineación justificada o a la izquierda.",
                              "Justificada o Izquierda", align, p_idx=p['index'], p_text=txt)

                # Interlineado
                line_spacing = p.get('line_spacing')
                if line_spacing is not None and abs(line_spacing - 2.0) > 0.2:
                    self._add("Jerarquía", f"Interlineado Título {level_label}", "error",
                              f"El título de {level_label.lower()} debe tener interlineado 2.0.",
                              "2.0", str(line_spacing), p_idx=p['index'], p_text=txt)

                # Espaciado
                s_before = p.get('spacing_before', 0)
                s_after = p.get('spacing_after', 0)
                if s_before > 0.5:
                    self._add("Jerarquía", f"Espaciado Anterior Título {level_label}", "error",
                              f"El título de {level_label.lower()} debe tener espaciado anterior de 0pt.",
                              "0pt", f"{s_before}pt", p_idx=p['index'], p_text=txt)
                if abs(s_after - 10.0) > 0.5:
                    self._add("Jerarquía", f"Espaciado Posterior Título {level_label}", "error",
                              f"El título de {level_label.lower()} debe tener espaciado posterior de 10pt.",
                              "10pt", f"{s_after}pt", p_idx=p['index'], p_text=txt)

                # VALIDAR TILDES: "TÍTULO" con tilde (si contiene la palabra)
                if "TITULO" in norm and "TÍTULO" not in txt:
                    self._add("Jerarquía", f"Tilde en Título {level_label}: {txt[:20]}...", "observation",
                              f"El texto '{txt[:30]}...' debe escribirse 'TÍTULO' con tilde, no 'TITULO'.",
                              "TÍTULO (con tilde)", "TITULO (sin tilde)", p_idx=p['index'], p_text=txt)

                # Capitalización: minúsculas (mayúscula inicial)
                txt_letters = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ]', '', txt)
                if txt_letters and not any(c.islower() for c in txt_letters):
                    self._add("Jerarquía", f"Capitalización Título {level_label}", "error",
                              f"Los títulos de {level_label.lower()} deben estar en minúsculas (con mayúscula inicial).",
                              "Minúsculas (mayúscula inicial)", txt[:40], p_idx=p['index'], p_text=txt)

                # Sangría del título
                effective_level = min(body_level, 5)
                exp_l, exp_h = self.INDENT_SPECS.get(effective_level, self.INDENT_SPECS[5])
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
                    self._add("Jerarquía", f"Sangría Título {level_label}", "error",
                              f"{level_label} debe tener Sangría Izquierda {exp_l}cm y Francesa {exp_h}cm.",
                              ", ".join(req_list), ", ".join(act_list), p_idx=p['index'], p_text=txt)

                    # Detección de desalineación
                    detected_indent_level = None
                    all_specs = {2: (0.0, 1.25), **self.INDENT_SPECS}
                    for chk_lvl, (chk_l, chk_h) in all_specs.items():
                        if abs(l_cm - chk_l) <= 0.15 and abs(h_cm - chk_h) <= 0.15:
                            detected_indent_level = chk_lvl
                            break

                    if detected_indent_level is not None and detected_indent_level != body_level:
                        self._add("Jerarquía", f"⚠️ Desalineación Título {level_label}", "warning",
                                  f"El título '{txt[:30]}...' tiene numeración de {level_label} pero su sangría corresponde al Nivel {detected_indent_level}.",
                                  f"Sangría de {level_label} (Izq {exp_l}cm, Fran {exp_h}cm)",
                                  f"Sangría de Nivel {detected_indent_level} (Izq {l_cm}cm, Fran {h_cm}cm)",
                                  p_idx=p['index'], p_text=txt)
                continue

            # ═══ VIÑETAS → se auditan en vinetas.py ═══
            if is_bullet:
                continue

            # ═══ OTROS TÍTULOS ═══
            if is_title:
                continue

            # ═══ CONTENIDO bajo Nivel 3/4/5 ═══
            # Auditar TODOS los párrafos que no sean títulos, viñetas o notas
            if txt.upper().startswith("NOTA:") or txt.upper().startswith("FUENTE:"):
                continue
            if re.match(r"^(TABLA|FIGURA)\s+\d+", norm):
                continue
            # Párrafos muy cortos pueden ser títulos o fragmentos
            if len(txt) <= 10:
                continue

            if bold:
                self._add("Estructura", f"Estilo de Fuente Contenido ({level_label})", "warning",
                          f"El contenido bajo {level_label.lower()} debe estar en estilo Normal (Sin Negrita).",
                          "Normal (Sin Negrita)", "Negrita", p_idx=p['index'], p_text=txt[:40])

            if align not in ['both', 'justify']:
                self._add("Estructura", f"Alineación Contenido ({level_label})", "error",
                          f"El contenido bajo {level_label.lower()} debe tener alineación justificada.",
                          "Justificada", align, p_idx=p['index'], p_text=txt[:40])

            line_spacing = p.get('line_spacing')
            if line_spacing is not None and abs(line_spacing - 2.0) > 0.2:
                self._add("Estructura", f"Interlineado Contenido ({level_label})", "error",
                          f"El contenido bajo {level_label.lower()} debe tener interlineado 2.0.",
                          "2.0", str(line_spacing), p_idx=p['index'], p_text=txt[:40])

            s_before = p.get('spacing_before', 0)
            s_after = p.get('spacing_after', 0)
            if s_before > 1.0:
                self._add("Estructura", f"Espaciado Anterior Contenido ({level_label})", "error",
                          f"El contenido bajo {level_label.lower()} DEBE tener espaciado anterior de 0pt.",
                          "0pt", f"{s_before}pt", p_idx=p['index'], p_text=txt[:40])
            if abs(s_after - 10.0) > 1.0:
                self._add("Estructura", f"Espaciado Posterior Contenido ({level_label})", "error",
                          f"El contenido bajo {level_label.lower()} DEBE tener espaciado posterior de 10pt.",
                          "10pt", f"{s_after}pt", p_idx=p['index'], p_text=txt[:40])

            # Sangría del contenido
            effective_level = min(body_level, 5)
            exp_l_c, exp_f_c = self.CONTENT_INDENT_SPECS.get(effective_level, self.CONTENT_INDENT_SPECS[5])
            ok_l = abs(l_cm - exp_l_c) <= 0.1
            ok_f = abs(f_cm - exp_f_c) <= 0.1
            if not ok_l or not ok_f:
                req_list = []
                act_list = []
                if not ok_l:
                    req_list.append(f"Izq {exp_l_c}cm")
                    act_list.append(f"Izq {l_cm}cm")
                if not ok_f:
                    req_list.append(f"Prim {exp_f_c}cm")
                    act_list.append(f"Prim {f_cm}cm")
                self._add("Estructura", f"Sangría de Contenido ({level_label})", "error",
                          f"El contenido bajo {level_label.lower()} DEBE tener Sangría Izquierda {exp_l_c}cm y Primera Línea {exp_f_c}cm.",
                          ", ".join(req_list), ", ".join(act_list), p_idx=p['index'], p_text=txt[:40])
