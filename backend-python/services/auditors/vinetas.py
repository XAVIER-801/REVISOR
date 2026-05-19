"""
vinetas.py - Auditoría de Viñetas en todo el documento.

Reglas implementadas:
- Estilo: Normal (Sin Negrita)
- Alineación: Justificada
- Interlineado: 2.0
- Espaciado: anterior 0pt, posterior 0pt (última viñeta: 10pt)
- Sangría según nivel:
    Nivel 1/2: Izq 0.5cm, Francesa 0.75cm
    Nivel 3: Izq 1.75cm, Francesa 0.75cm
    Nivel 4/5: Izq 3.0cm, Francesa 0.75cm
- Consistencia de símbolo de viñeta
"""
import re
from .base_auditor import BaseAuditor


class VinetasAuditor(BaseAuditor):

    def audit(self):
        current_level = 1
        in_index_or_prelim = True
        current_bullet_symbol = None
        current_sub_bullet_symbol = None

        for i, p in enumerate(self.paragraphs):
            txt = p['text'].strip()
            if not txt:
                continue

            norm = p['norm']

            # Omitir párrafos del índice
            if hasattr(self.engine, 'last_index_idx') and self.engine.last_index_idx != -1 and i <= self.engine.last_index_idx:
                continue

            is_index_line = "...." in txt or bool(re.search(r"\d+$", txt))
            if not is_index_line and ("CAPITULO" in norm or "INTRODUCCION" in norm):
                in_index_or_prelim = False

            if in_index_or_prelim or p.get('in_table') or (self.anexos_start_idx != -1 and i >= self.anexos_start_idx):
                continue

            bold = any(r.get('bold') for r in p.get('runs', []))
            align = p.get('alignment', 'left')
            l_cm = round((p.get('indent_left') or 0) / 567.0, 2)
            h_cm = round((p.get('indent_hanging') or 0) / 567.0, 2)

            is_bullet = ('-' in txt[:3] or '\u2022' in txt[:3] or '' in txt[:3] or '*' in txt[:3] or '•' in txt[:3])

            # Actualizar nivel del título actual
            is_title = p.get('is_heading', False)
            numbering_match = re.match(r'^(\d+(?:\.\d+)+)\.?(?:[\s\t]+|$)', txt.strip())
            if numbering_match:
                current_level = numbering_match.group(1).count('.') + 1
            elif is_title:
                current_level = p.get('level', current_level)

            es_seccion_principal = any(k in norm for k in [
                "INTRODUCCION", "MARCO TEORICO", "METODOLOGIA",
                "MATERIALES Y METODOS", "RESULTADOS Y DISCUSION",
                "CONCLUSIONES", "RECOMENDACIONES", "REFERENCIAS BIBLIOGRAFICAS"
            ])
            is_capitulo = bool(re.match(r"^CAP[ÍI]TULO\s+(I|V|X|L|C|[0-9]+)", norm))
            if is_capitulo or es_seccion_principal:
                current_level = 1

            if not is_bullet:
                current_bullet_symbol = None
                current_sub_bullet_symbol = None
                continue

            # Determinar si es sub-viñeta
            is_sub_bullet = False
            exp_l_cm = 0.5
            if current_level in [1, 2]:
                exp_l_cm = 0.5
                if l_cm > 1.0: is_sub_bullet = True
            elif current_level == 3:
                exp_l_cm = 1.75
                if l_cm > 2.2: is_sub_bullet = True
            elif current_level >= 4:
                exp_l_cm = 3.0
                if l_cm > 3.5: is_sub_bullet = True

            # Determinar si es la última viñeta del bloque
            is_last_bullet = True
            if i + 1 < len(self.paragraphs):
                next_p = self.paragraphs[i+1]
                next_txt = next_p['text'].strip()
                if next_txt:
                    next_is_bullet = ('-' in next_txt[:3] or '\u2022' in next_txt[:3] or '' in next_txt[:3] or '*' in next_txt[:3] or '•' in next_txt[:3])
                    if next_is_bullet:
                        is_last_bullet = False

            # 1. Bold, Alignment, Interlineado
            if bold:
                self._add("Viñetas", "Estilo de Fuente Viñeta", "warning",
                          "Las viñetas deben estar en estilo Normal (Sin Negrita).",
                          "Normal (Sin Negrita)", "Negrita", p_idx=p['index'], p_text=txt)

            if align not in ['both', 'justify']:
                self._add("Viñetas", "Alineación Viñeta", "warning",
                          "Las viñetas deben tener alineación justificada.",
                          "Justificada", align, p_idx=p['index'], p_text=txt)

            line_spacing = p.get('line_spacing')
            if line_spacing is not None and abs(line_spacing - 2.0) > 0.2:
                self._add("Viñetas", "Interlineado Viñeta", "error",
                          "Las viñetas deben tener interlineado 2.0.",
                          "2.0", str(line_spacing), p_idx=p['index'], p_text=txt)

            # 2. Spacing
            s_before = p.get('spacing_before', 0)
            s_after = p.get('spacing_after', 0)
            if s_before > 1.0:
                self._add("Viñetas", "Espaciado Anterior Viñeta", "warning",
                          "Las viñetas deben tener espaciado anterior de 0pt.",
                          "0pt", f"{s_before}pt", p_idx=p['index'], p_text=txt)

            if is_last_bullet:
                if abs(s_after - 10.0) > 2.0:
                    self._add("Viñetas", "Espaciado Posterior Última Viñeta", "warning",
                              "La última viñeta del bloque debe tener espaciado posterior de 10pt.",
                              "10pt", f"{s_after}pt", p_idx=p['index'], p_text=txt)
            else:
                if s_after > 1.0:
                    self._add("Viñetas", "Espaciado Posterior Viñeta", "warning",
                              "Las viñetas intermedias deben tener espaciado posterior de 0pt.",
                              "0pt", f"{s_after}pt", p_idx=p['index'], p_text=txt)

            # 3. Indents
            if not is_sub_bullet:
                if current_level in [1, 2]:
                    ok_l = abs(l_cm - 0.5) <= 0.1
                    ok_h = abs(h_cm - 0.75) <= 0.1
                    l_part = f"Izq {l_cm}cm" if ok_l else f"**Izq {l_cm}cm**"
                    h_part = f"Fran {h_cm}cm" if ok_h else f"**Fran {h_cm}cm**"
                    if not ok_l or not ok_h:
                        self._add("Viñetas", "Sangría de Viñeta (Nivel 1/2)", "error",
                                  "Las viñetas bajo nivel 1 o 2 deben tener Sangría Izquierda 0.5cm y Francesa 0.75cm.",
                                  "Izq 0.5cm, Fran 0.75cm", f"{l_part}, {h_part}", p_idx=p['index'], p_text=txt)
                elif current_level == 3:
                    ok_l = abs(l_cm - 1.75) <= 0.1
                    ok_h = abs(h_cm - 0.75) <= 0.1
                    l_part = f"Izq {l_cm}cm" if ok_l else f"**Izq {l_cm}cm**"
                    h_part = f"Fran {h_cm}cm" if ok_h else f"**Fran {h_cm}cm**"
                    if not ok_l or not ok_h:
                        self._add("Viñetas", "Sangría de Viñeta (Nivel 3)", "error",
                                  "Las viñetas bajo nivel 3 deben tener Sangría Izquierda 1.75cm y Francesa 0.75cm.",
                                  "Izq 1.75cm, Fran 0.75cm", f"{l_part}, {h_part}", p_idx=p['index'], p_text=txt)
                elif current_level >= 4:
                    ok_l = abs(l_cm - 3.0) <= 0.1
                    ok_h = abs(h_cm - 0.75) <= 0.1
                    l_part = f"Izq {l_cm}cm" if ok_l else f"**Izq {l_cm}cm**"
                    h_part = f"Fran {h_cm}cm" if ok_h else f"**Fran {h_cm}cm**"
                    if not ok_l or not ok_h:
                        self._add("Viñetas", "Sangría de Viñeta (Nivel 4/5)", "error",
                                  "Las viñetas bajo nivel 4 o 5 deben tener Sangría Izquierda 3.0cm y Francesa 0.75cm.",
                                  "Izq 3.0cm, Fran 0.75cm", f"{l_part}, {h_part}", p_idx=p['index'], p_text=txt)

            # 4. Symbol consistency
            bullet_char = txt[0]
            if is_sub_bullet:
                if current_sub_bullet_symbol is None:
                    current_sub_bullet_symbol = bullet_char
                elif bullet_char != current_sub_bullet_symbol:
                    self._add("Viñetas", "Consistencia Símbolo Sub-Viñeta", "warning",
                              "Las sub-viñetas deben usar un único tipo de símbolo en toda la lista.",
                              current_sub_bullet_symbol, bullet_char, p_idx=p['index'], p_text=txt)
            else:
                if current_bullet_symbol is None:
                    current_bullet_symbol = bullet_char
                elif bullet_char != current_bullet_symbol:
                    self._add("Viñetas", "Consistencia Símbolo Viñeta", "warning",
                              "Las viñetas deben usar un único tipo de símbolo en toda la lista.",
                              current_bullet_symbol, bullet_char, p_idx=p['index'], p_text=txt)
