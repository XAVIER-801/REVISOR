"""
capitulo_nivel1.py - Auditoría de Títulos de Nivel 1 Y su Contenido.

Cubre: CAPITULO I, INTRODUCCIÓN, CONCLUSIONES, RECOMENDACIONES, etc.
y los párrafos de contenido que están directamente bajo estos títulos.

Reglas de TÍTULO Nivel 1:
- Alineación: Centrado
- Estilo: Negrita
- Capitalización: MAYÚSCULAS
- Sangría: Sin sangría (0cm)

Reglas de CONTENIDO bajo Nivel 1:
- Estilo: Normal (Sin Negrita)
- Alineación: Justificada
- Interlineado: 2.0
- Espaciado: anterior 0pt, posterior 10pt
- Sangría: Izquierda 0cm, Primera Línea 1.25cm
"""
import re
from .base_auditor import BaseAuditor


class CapituloNivel1Auditor(BaseAuditor):

    def audit(self):
        for i, p in enumerate(self.paragraphs):
            # Solo párrafos del cuerpo, bajo nivel 1, no en tabla/anexos
            if not p.get("is_in_body"):
                continue
            if p.get("body_level") != 1:
                continue

            txt = p['text'].strip()
            if not txt:
                continue

            norm = p['norm']
            size = p['runs'][0].get('size', 0) if p.get('runs') else 0
            bold = any(r.get('bold') for r in p.get('runs', []))
            align = p.get('alignment', 'left')
            l_cm = round((p.get('indent_left') or 0) / 567.0, 2)
            f_cm = round((p.get('indent_first') or 0) / 567.0, 2)
            h_cm = round((p.get('indent_hanging') or 0) / 567.0, 2)

            is_bullet = p.get('is_bullet', False)
            is_title = p.get('is_heading', False)

            # Detectar secciones principales de nivel 1
            es_seccion_principal = any(k in norm for k in [
                "INTRODUCCION", "MARCO TEORICO", "METODOLOGIA",
                "MATERIALES Y METODOS", "RESULTADOS Y DISCUSION",
                "CONCLUSIONES", "RECOMENDACIONES", "REFERENCIAS BIBLIOGRAFICAS"
            ]) and (p.get('style_id', '').upper().startswith('HEADING') or txt.isupper() or bold)
            is_capitulo = bool(re.match(r"^CAP[ÍI]TULO\s+(I|V|X|L|C|[0-9]+)", norm))
            
            numbering_match = re.match(r'^(\d+(?:\.\d+)+)\.?(?:[\s\t]+|$)', txt.strip())
            if numbering_match:
                es_seccion_principal = False

            # ═══ TÍTULO NIVEL 1 ═══
            if is_capitulo or es_seccion_principal:
                ok_align = align == 'center'
                ok_bold = bold == True
                ok_case = txt.upper() == txt
                ok_indent = abs(l_cm) < 0.1 and abs(f_cm) < 0.1 and abs(h_cm) < 0.1

                if not ok_align:
                    self._add("Jerarquía", f"Alineación Capítulo/Nivel 1: {txt[:20]}...", "error",
                              f"El título de capítulo o nivel 1 '{txt[:30]}...' debe estar CENTRADO.",
                              "Centrado", align, p_idx=p['index'], p_text=txt)

                if not ok_bold:
                    self._add("Jerarquía", f"Estilo Capítulo/Nivel 1: {txt[:20]}...", "error",
                              f"El título de capítulo o nivel 1 '{txt[:30]}...' debe estar en NEGRITA.",
                              "Negrita", "Normal", p_idx=p['index'], p_text=txt)

                if not ok_case:
                    self._add("Jerarquía", f"Capitalización Capítulo/Nivel 1: {txt[:20]}...", "error",
                              f"El título de capítulo o nivel 1 '{txt[:30]}...' debe estar completamente en MAYÚSCULAS.",
                              "MAYÚSCULAS", txt[:30], p_idx=p['index'], p_text=txt)

                if not ok_indent:
                    self._add("Jerarquía", f"Sangría Capítulo/Nivel 1: {txt[:20]}...", "error",
                              f"El título de capítulo o nivel 1 '{txt[:30]}...' no debe tener ninguna sangría.",
                              "Sin sangría (0cm)", f"Sangría Izq: {l_cm}cm", p_idx=p['index'], p_text=txt)
                continue

            # ═══ VIÑETAS bajo Nivel 1 → se auditan en vinetas.py ═══
            if is_bullet:
                continue

            # ═══ TÍTULOS numerados (que en realidad son nivel 2+) → se auditan en su nivel ═══
            if is_title:
                continue

            # ═══ CONTENIDO bajo Nivel 1 ═══
            if len(txt) <= 50:
                continue
            if txt.upper().startswith("NOTA:") or txt.upper().startswith("FUENTE:"):
                continue
            if re.match(r"^(TABLA|FIGURA)\s+\d+", norm):
                continue

            # Estilo
            if bold:
                self._add("Estructura", "Estilo de Fuente Contenido (Nivel 1)", "warning",
                          "El contenido bajo nivel 1 debe estar en estilo Normal (Sin Negrita).",
                          "Normal (Sin Negrita)", "Negrita", p_idx=p['index'], p_text=txt[:40])

            # Alineación
            if align not in ['both', 'justify']:
                self._add("Estructura", "Alineación Contenido (Nivel 1)", "error",
                          "El contenido bajo nivel 1 debe tener alineación justificada.",
                          "Justificada", align, p_idx=p['index'], p_text=txt[:40])

            # Interlineado
            line_spacing = p.get('line_spacing')
            if line_spacing is not None and abs(line_spacing - 2.0) > 0.2:
                self._add("Estructura", "Interlineado Contenido (Nivel 1)", "error",
                          "El contenido bajo nivel 1 debe tener interlineado 2.0.",
                          "2.0", str(line_spacing), p_idx=p['index'], p_text=txt[:40])

            # Espaciado
            s_before = p.get('spacing_before', 0)
            s_after = p.get('spacing_after', 0)
            if s_before > 1.0:
                self._add("Estructura", "Espaciado Anterior Contenido (Nivel 1)", "warning",
                          "El contenido bajo nivel 1 debe tener espaciado anterior de 0pt.",
                          "0pt", f"{s_before}pt", p_idx=p['index'], p_text=txt[:40])
            if abs(s_after - 10.0) > 2.0:
                self._add("Estructura", "Espaciado Posterior Contenido (Nivel 1)", "warning",
                          "El contenido bajo nivel 1 debe tener espaciado posterior de 10pt.",
                          "10pt", f"{s_after}pt", p_idx=p['index'], p_text=txt[:40])

            # Sangría: Izq 0cm, Primera Línea 1.25cm
            ok_l = abs(l_cm - 0.0) <= 0.1
            ok_f = abs(f_cm - 1.25) <= 0.1
            l_part = f"Izq {l_cm}cm" if ok_l else f"**Izq {l_cm}cm**"
            f_part = f"Prim {f_cm}cm" if ok_f else f"**Prim {f_cm}cm**"
            if not ok_l or not ok_f:
                self._add("Estructura", "Sangría de Contenido (Nivel 1)", "warning",
                          "El contenido bajo nivel 1 debe tener Sangría Izquierda 0cm y Primera Línea 1.25cm.",
                          "Izq 0cm, Prim 1.25cm", f"{l_part}, {f_part}", p_idx=p['index'], p_text=txt[:40])
