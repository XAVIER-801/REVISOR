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
            # Solo párrafos del cuerpo, bajo nivel 1, no en tabla/anexos/referencias
            if not p.get("is_in_body"):
                continue
            if p.get("body_level") != 1:
                continue
            sec_upper = p.get("section", "").upper()
            if "REFERENCIAS BIBLIOGRAFICAS" in sec_upper or "REFERENCIAS BIBLIOGRÁFICAS" in sec_upper:
                continue
            # Saltar entradas del índice por si llegan aquí por mala detección
            txt_raw = p['text']
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
            size = p['runs'][0].get('size', 0) if p.get('runs') else 0
            # Detección de negrita por MAYORÍA de caracteres visibles
            # (evita falsos positivos cuando solo un espacio o signo tiene bold)
            bold = self._is_meaningfully_bold(p)
            align = p.get('alignment', 'left')
            l_cm = round(p.get('indent_left') or 0, 2)
            f_cm = round(p.get('indent_first') or 0, 2)
            h_cm = round(p.get('indent_hanging') or 0, 2)

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
            if numbering_match or (is_title and p.get('level', 1) > 1):
                es_seccion_principal = False

            # ═══ TÍTULO NIVEL 1 ═══
            # Distinción crítica (Guía pág. 18):
            #   - is_capitulo (CAPÍTULO I, II, III, IV) → 16pt, posterior 5pt
            #   - es_titulo_capitulo (INTRODUCCIÓN, REVISIÓN DE LITERATURA, etc.) → 14pt, posterior 10pt
            #   - secciones finales (V. CONCLUSIONES, VI. RECOMENDACIONES, VII. REFERENCIAS) → 16pt, posterior 10pt
            es_titulo_capitulo = es_seccion_principal and any(k in norm for k in [
                "INTRODUCCION", "MARCO TEORICO", "METODOLOGIA",
                "MATERIALES Y METODOS", "RESULTADOS Y DISCUSION",
                "REVISION DE LITERATURA"
            ])
            # Secciones que SÍ son 16pt (no 14pt como los títulos de capítulo)
            es_seccion_final = es_seccion_principal and any(k in norm for k in [
                "CONCLUSIONES", "RECOMENDACIONES", "REFERENCIAS BIBLIOGRAFICAS"
            ])

            if is_capitulo or es_seccion_principal:
                ok_align = align == 'center'
                ok_bold = bold == True
                ok_case = txt.upper() == txt
                ok_indent = abs(l_cm) < 0.1 and abs(f_cm) < 0.1 and abs(h_cm) < 0.1

                # ═══ VALIDAR TILDES (ERROR, no observation) ═══
                # Según la RAE, las MAYÚSCULAS también llevan tilde.
                # "CAPÍTULO" y "TÍTULO" deben escribirse con tilde aunque estén en mayúsculas.
                has_proper_tilde = True
                if "CAPITULO" in norm and "CAPÍTULO" not in txt:
                    has_proper_tilde = False
                    self._add(
                        "Jerarquía",
                        f"Tilde en Capítulo: {txt[:20]}...",
                        "error",
                        f"El texto '{txt[:30]}...' debe escribirse 'CAPÍTULO' con tilde, "
                        f"no 'CAPITULO'. Según la Real Academia Española, las palabras en "
                        f"MAYÚSCULAS conservan la tilde cuando les corresponde por reglas "
                        f"de acentuación.",
                        "CAPÍTULO (con tilde)",
                        "CAPITULO (sin tilde)",
                        p_idx=p['index'], p_text=txt,
                    )

                # Validar si hay "TITULO" sin tilde
                if "TITULO" in norm and "TÍTULO" not in txt:
                    self._add(
                        "Jerarquía",
                        f"Tilde en Título: {txt[:20]}...",
                        "error",
                        f"El texto '{txt[:30]}...' debe escribirse 'TÍTULO' con tilde, "
                        f"no 'TITULO'. Las mayúsculas también llevan tilde según la RAE.",
                        "TÍTULO (con tilde)",
                        "TITULO (sin tilde)",
                        p_idx=p['index'], p_text=txt,
                    )

                if not ok_align:
                    self._add("Jerarquía", f"Alineación Capítulo/Nivel 1: {txt[:20]}...", "error",
                              f"El título de capítulo o nivel 1 '{txt[:30]}...' debe estar CENTRADO.",
                              "Centrado", self._align_display(align), p_idx=p['index'], p_text=txt)

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

                # ═══ TAMAÑO Y ESPACIADO DIFERENCIADOS ═══
                s_after = p.get('spacing_after', 0)
                s_before = p.get('spacing_before', 0)
                line_spacing = p.get('line_spacing')

                if is_capitulo:
                    # CAPÍTULO I, II, III, IV → 16pt + posterior 5pt
                    if size and abs(size - 16) > 0.5:
                        self._add("Jerarquía", f"Tamaño Capítulo X: {txt[:20]}...", "error",
                                  f"La etiqueta 'CAPÍTULO X' debe ser de 16pt según la Guía UNAP.",
                                  "16pt", f"{size}pt", p_idx=p['index'], p_text=txt)
                    if abs(s_after - 5.0) > 1.0:
                        self._add("Jerarquía", f"Espaciado Posterior Capítulo: {txt[:20]}...", "error",
                                  f"Después de 'CAPÍTULO X' debe haber espaciado posterior de 5pt (la Guía UNAP así lo indica).",
                                  "5pt", f"{s_after}pt", p_idx=p['index'], p_text=txt)
                    if s_before > 1.0:
                        self._add("Jerarquía", f"Espaciado Anterior Capítulo: {txt[:20]}...", "error",
                                  f"'CAPÍTULO X' debe tener espaciado anterior de 0pt.",
                                  "0pt", f"{s_before}pt", p_idx=p['index'], p_text=txt)
                elif es_titulo_capitulo:
                    # INTRODUCCIÓN, REVISIÓN DE LITERATURA, etc. → 14pt + posterior 10pt
                    if size and abs(size - 14) > 0.5:
                        self._add("Jerarquía", f"Tamaño Título del Capítulo: {txt[:20]}...", "error",
                                  f"El título del capítulo (INTRODUCCIÓN, REVISIÓN DE LITERATURA, etc.) debe ser de 14pt según la Guía UNAP.",
                                  "14pt", f"{size}pt", p_idx=p['index'], p_text=txt)
                    if abs(s_after - 10.0) > 1.0:
                        self._add("Jerarquía", f"Espaciado Posterior Título del Capítulo: {txt[:20]}...", "error",
                                  f"El título del capítulo debe tener espaciado posterior de 10pt.",
                                  "10pt", f"{s_after}pt", p_idx=p['index'], p_text=txt)
                    if s_before > 1.0:
                        self._add("Jerarquía", f"Espaciado Anterior Título del Capítulo: {txt[:20]}...", "error",
                                  f"El título del capítulo debe tener espaciado anterior de 0pt.",
                                  "0pt", f"{s_before}pt", p_idx=p['index'], p_text=txt)
                elif es_seccion_final:
                    # V. CONCLUSIONES, VI. RECOMENDACIONES, VII. REFERENCIAS → 16pt + posterior 10pt
                    if size and abs(size - 16) > 0.5:
                        self._add("Jerarquía", f"Tamaño Sección Final: {txt[:20]}...", "error",
                                  f"La sección final (CONCLUSIONES, RECOMENDACIONES, REFERENCIAS) debe ser de 16pt.",
                                  "16pt", f"{size}pt", p_idx=p['index'], p_text=txt)
                    if abs(s_after - 10.0) > 1.0:
                        self._add("Jerarquía", f"Espaciado Posterior Sección Final: {txt[:20]}...", "error",
                                  f"La sección final debe tener espaciado posterior de 10pt.",
                                  "10pt", f"{s_after}pt", p_idx=p['index'], p_text=txt)

                # Interlineado 2.0 para todos los títulos de nivel 1
                if line_spacing and abs(line_spacing - 2.0) > 0.2:
                    self._add("Jerarquía", f"Interlineado Título Nivel 1: {txt[:20]}...", "error",
                              f"El título de nivel 1 debe tener interlineado 2.0.",
                              "2.0", str(line_spacing), p_idx=p['index'], p_text=txt)

                continue

            # ═══ VIÑETAS bajo Nivel 1 → se auditan en vinetas.py ═══
            if is_bullet:
                continue

            # ═══ TÍTULOS numerados (que en realidad son nivel 2+) → se auditan en su nivel ═══
            if is_title:
                continue

            # ═══ CONTENIDO bajo Nivel 1 ═══
            # Aumentar umbral de longitud mínima para evitar falsos positivos
            if len(txt) <= 80:
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
            if align != 'both':
                self._add("Estructura", "Alineación Contenido (Nivel 1)", "error",
                          "El contenido bajo nivel 1 debe tener alineación justificada.",
                          "Justificada", self._align_display(align), p_idx=p['index'], p_text=txt[:40])

            # Interlineado
            line_spacing = p.get('line_spacing')
            if line_spacing is not None and abs(line_spacing - 2.0) > 0.2:
                self._add("Estructura", "Interlineado Contenido (Nivel 1)", "error",
                          "El contenido bajo nivel 1 debe tener interlineado 2.0.",
                          "2.0", str(line_spacing), p_idx=p['index'], p_text=txt[:40])

            # Espaciado
            s_before = p.get('spacing_before', 0)
            s_after = p.get('spacing_after', 0)
            if s_before > 3.0:  # Tolerar hasta 3pt (Word usa valores ligeramente distintos de 0)
                self._add("Estructura", "Espaciado Anterior Contenido (Nivel 1)", "error",
                          "El contenido bajo nivel 1 DEBE tener espaciado anterior de 0pt.",
                          "0pt", f"{s_before}pt", p_idx=p['index'], p_text=txt[:40])
            # Tolerar un rango de 8-12pt o 0pt (Muchas tesis correctas usan 0pt o 12pt)
            is_after_ok = (abs(s_after - 0.0) <= 1.0) or (8.0 <= s_after <= 12.0)
            if not is_after_ok:
                self._add("Estructura", "Espaciado Posterior Contenido (Nivel 1)", "error",
                          "El contenido bajo nivel 1 DEBE tener espaciado posterior de 10pt (se tolera 8-12pt o 0pt).",
                          "10pt (o 0pt / 8-12pt)", f"{s_after}pt", p_idx=p['index'], p_text=txt[:40])

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
                self._add("Estructura", "Sangría de Contenido (Nivel 1)", "error",
                          "El contenido bajo nivel 1 DEBE tener Sangría Izquierda 0cm y Primera Línea 1.25cm.",
                          ", ".join(req_list), ", ".join(act_list), p_idx=p['index'], p_text=txt[:40])
