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

            bold = self._is_meaningfully_bold(p)
            align = p.get('alignment', 'left')
            l_cm = round(p.get('indent_left') or 0, 2)
            h_cm = round(p.get('indent_hanging') or 0, 2)

            is_bullet, is_symbol_ok, detected_symbol = self._check_is_bullet(p, txt)

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

            # Si el símbolo no es permitido, solo registrar error y no continuar validación
            if not is_symbol_ok:
                self._add("Viñetas", "Símbolo de Viñeta No Permitido", "error",
                          f"El símbolo '{detected_symbol}' no está permitido. Solo se aceptan: guion (-), punto (•) o numeración alfanumérica.",
                          "Guion (-), Punto (•) o Numeración alfanumérica", f"Símbolo '{detected_symbol}'",
                          p_idx=p['index'], p_text=txt)
                continue

            # ═══ NIVEL CONTEXTUAL ═══
            # Determinar el nivel del último título antes de esta viñeta usando
            # tanto el rastreo local (current_level) como _find_context_level
            # como respaldo. Las sangrías de viñetas dependen del nivel del título.
            ctx_level = self._find_context_level(i) or current_level
            # Tomar el más confiable: si current_level está bien rastreado, usarlo;
            # si no, fallback a ctx_level
            effective_level = current_level if current_level in (1, 2, 3, 4, 5) else ctx_level

            # Las sub-viñetas se detectan por SÍMBOLO DIFERENTE al de la
            # viñeta principal, NO por sangría (todas comparten la misma sangría)
            is_sub_bullet = (
                current_bullet_symbol is not None
                and detected_symbol != current_bullet_symbol
            )

            # Para uso interno del resto de la función, current_level apunta al efectivo
            current_level = effective_level

            # Determinar si es la última viñeta del bloque
            is_last_bullet = True
            if i + 1 < len(self.paragraphs):
                next_p = self.paragraphs[i+1]
                next_txt = next_p['text'].strip()
                if next_txt:
                    next_is_bullet, _, _ = self._check_is_bullet(next_p, next_txt)
                    if next_is_bullet:
                        is_last_bullet = False

            # 1. Bold, Alignment, Interlineado
            if bold:
                self._add("Viñetas", "Estilo de Fuente Viñeta", "warning",
                          "Las viñetas deben estar en estilo Normal (Sin Negrita).",
                          "Normal (Sin Negrita)", "Negrita", p_idx=p['index'], p_text=txt)

            if align != 'both':
                self._add("Viñetas", "Alineación Viñeta", "warning",
                          "Las viñetas deben tener alineación justificada.",
                          "Justificada", self._align_display(align), p_idx=p['index'], p_text=txt)

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
                    self._add("Viñetas", "Espaciado Posterior Última Viñeta", "error",
                              "La última viñeta del bloque DEBE tener espaciado posterior de 10pt obligatoriamente.",
                              "10pt", f"{s_after}pt", p_idx=p['index'], p_text=txt)
            else:
                if s_after > 1.0:
                    self._add("Viñetas", "Espaciado Posterior Viñeta", "error",
                              "Las viñetas intermedias deben tener espaciado posterior de 0pt.",
                              "0pt", f"{s_after}pt", p_idx=p['index'], p_text=txt)

            # 3. Indents (misma sangría para viñetas y sub-viñetas)
            if current_level in [1, 2]:
                exp_l = 0.5
                ok_l = abs(l_cm - exp_l) <= 0.1
                ok_h = abs(h_cm - 0.75) <= 0.1
                if not ok_l or not ok_h:
                    self._add("Viñetas", "Sangría de Viñeta (Nivel 1/2)", "error",
                              "Las viñetas bajo nivel 1 o 2 deben tener Sangría Izquierda 0.5cm y Francesa 0.75cm.",
                              f"Izq 0.5cm, Fran 0.75cm", f"Izq {l_cm}cm, Fran {h_cm}cm", p_idx=p['index'], p_text=txt)
            elif current_level == 3:
                exp_l = 1.75
                ok_l = abs(l_cm - exp_l) <= 0.1
                ok_h = abs(h_cm - 0.75) <= 0.1
                if not ok_l or not ok_h:
                    self._add("Viñetas", "Sangría de Viñeta (Nivel 3)", "error",
                              "Las viñetas bajo nivel 3 deben tener Sangría Izquierda 1.75cm y Francesa 0.75cm.",
                              f"Izq 1.75cm, Fran 0.75cm", f"Izq {l_cm}cm, Fran {h_cm}cm", p_idx=p['index'], p_text=txt)
            elif current_level >= 4:
                exp_l = 3.0
                ok_l = abs(l_cm - exp_l) <= 0.1
                ok_h = abs(h_cm - 0.75) <= 0.1
                if not ok_l or not ok_h:
                    self._add("Viñetas", "Sangría de Viñeta (Nivel 4/5)", "error",
                              "Las viñetas bajo nivel 4 o 5 deben tener Sangría Izquierda 3.0cm y Francesa 0.75cm.",
                              f"Izq 3.0cm, Fran 0.75cm", f"Izq {l_cm}cm, Fran {h_cm}cm", p_idx=p['index'], p_text=txt)

            # 4. Symbol consistency (Guía UNAP pág. 20)
            # "Las viñetas con un único tipo de símbolo"
            # "Las sub-viñetas con un único tipo de símbolo"
            # → ERROR (no warning) porque es regla explícita de la guía
            bullet_char = detected_symbol

            # Si el bloque aún no tiene símbolo principal, esta viñeta lo define
            if current_bullet_symbol is None:
                current_bullet_symbol = bullet_char

            if is_sub_bullet:
                # Consistencia entre sub-viñetas (automáticamente distinto al
                # símbolo principal porque is_sub_bullet se define como cambio de símbolo)
                if current_sub_bullet_symbol is None:
                    current_sub_bullet_symbol = bullet_char
                elif bullet_char != current_sub_bullet_symbol:
                    self._add("Viñetas", "Consistencia Símbolo Sub-Viñeta", "error",
                              f"Las sub-viñetas deben usar UN ÚNICO tipo de símbolo en toda la lista "
                              f"(Guía UNAP pág. 20). Se detectó cambio de '{current_sub_bullet_symbol}' a "
                              f"'{bullet_char}'.",
                              f"Único símbolo: '{current_sub_bullet_symbol}'",
                              f"Símbolo mezclado: '{bullet_char}'",
                              p_idx=p['index'], p_text=txt)
            else:
                # Consistencia entre viñetas principales
                if bullet_char != current_bullet_symbol:
                    self._add("Viñetas", "Consistencia Símbolo Viñeta", "error",
                              f"Las viñetas deben usar UN ÚNICO tipo de símbolo en toda la lista "
                              f"(Guía UNAP pág. 20). Se detectó cambio de '{current_bullet_symbol}' a "
                              f"'{bullet_char}'.",
                              f"Único símbolo: '{current_bullet_symbol}'",
                              f"Símbolo mezclado: '{bullet_char}'",
                              p_idx=p['index'], p_text=txt)

    def _check_is_bullet(self, p, txt):
        """
        Detección ESTRICTA de viñetas. Solo acepta:
        - Guion: -
        - Punto: • (bullet)
        - Alfanuméricos: a), 1), (1), etc.

        RECHAZA explícitamente: ➢, ❑, ✓, ●, ○, y otros símbolos decorativos
        """
        txt_strip = txt.strip()

        is_bullet = False
        is_symbol_ok = True
        detected_symbol = ''

        # ==================== SÍMBOLOS PERMITIDOS ====================
        # Solo estos 3 tipos están permitidos según la guía
        allowed_single_chars = ['-', '•', '*']  # guion, punto, asterisco

        # Conjunto de símbolos PROHIBIDOS (rechaza estos primero)
        prohibited_symbols = {
            '➢', '➔', '➤', '→', '⇒',  # Flechas
            '❑', '■', '□', '◆', '◇', '▲', '▼', '◀', '▶',  # Formas
            '●', '○', '◎', '◉',  # Círculos
            '✓', '✔', '✗', '✘',  # Checks
            '♦', '❖',  # Diamantes
            '\uf0d8', '\uf0a7', '\uf0fc'  # Códigos Word problemáticos
        }

        # 1. DETECCIÓN DE VIÑETAS AUTOMÁTICAS DE WORD
        list_fmt = p.get('list_fmt')
        list_lvl_text = p.get('list_lvl_text') or ''
        style_id = p.get('style_id', '').lower()

        is_automatic_bullet = (list_fmt == 'bullet') or any(k in style_id for k in ['bullet', 'viñeta', 'vinet', 'listbullet'])

        if is_automatic_bullet:
            # Si Word dice que es automática, verificar el símbolo
            if list_lvl_text:
                detected_symbol = list_lvl_text[0] if list_lvl_text else '•'
            else:
                detected_symbol = txt_strip[0] if txt_strip else '•'

            # RECHAZO EXPLÍCITO de símbolos prohibidos
            if detected_symbol in prohibited_symbols or ('\ue000' <= detected_symbol <= '\uf8ff'):
                # Es viñeta automática PERO con símbolo prohibido
                is_bullet = True
                is_symbol_ok = False
                # Estandarizar el símbolo para reportar
                if detected_symbol in ['➢', '➔', '➤', '\uf0d8', '→', '⇒']:
                    detected_symbol = '➢'
                elif detected_symbol in ['❑', '■', '□', '◆', '◇', '\uf0a7']:
                    detected_symbol = '❑'
                elif detected_symbol in ['✓', '✔', '\uf0fc']:
                    detected_symbol = '✓'
            else:
                # Símbolo automático permitido
                is_bullet = True
                is_symbol_ok = detected_symbol in allowed_single_chars or detected_symbol in ['\u2022', '\u00b7', '\uf0b7']

                if not is_symbol_ok:
                    # Símbolo automático no reconocido (pero no es prohibido)
                    is_bullet = False
        else:
            # 2. DETECCIÓN DE VIÑETAS ESCRITAS MANUALMENTE (más estricta)
            if txt_strip:
                first_char = txt_strip[0]
                h_cm = round((p.get('indent_hanging') or 0) / 567.0, 2)
                l_cm = round((p.get('indent_left') or 0) / 567.0, 2)
                next_char_is_separator = len(txt_strip) > 1 and txt_strip[1] in (' ', '\t')
                looks_like_bullet_paragraph = (h_cm > 0.3 or l_cm > 0.3 or next_char_is_separator)

                # PRIMERO: Verificar si comienza con símbolo PROHIBIDO
                if first_char in prohibited_symbols or ('\ue000' <= first_char <= '\uf8ff'):
                    # CAMBIO CRÍTICO: si el párrafo PARECE viñeta (sangría
                    # francesa, izquierda, o separador después del símbolo),
                    # lo marcamos como viñeta CON símbolo prohibido (para que
                    # se reporte el error). Antes retornaba is_bullet=False
                    # y nunca se reportaba.
                    if not looks_like_bullet_paragraph:
                        return False, True, ''
                    is_bullet = True
                    is_symbol_ok = False
                    detected_symbol = first_char
                    if first_char in ['➢', '➔', '➤', '→', '⇒', '\uf0d8']:
                        detected_symbol = '➢'
                    elif first_char in ['❑', '■', '□', '◆', '◇', '\uf0a7']:
                        detected_symbol = '❑'
                    elif first_char in ['✓', '✔', '\uf0fc']:
                        detected_symbol = '✓'
                    return is_bullet, is_symbol_ok, detected_symbol

                # SEGUNDO: Detectar viñetas PERMITIDAS
                # Patrón alfanumérico: a), 1), (a), (1), etc.
                alphanumeric_match = re.match(r'^(\(?[a-zA-Z0-9]+\)?\.?)\s+', txt_strip)
                is_alphanumeric = bool(alphanumeric_match)

                # Viñeta con guion o punto
                is_dash_or_dot = (first_char in allowed_single_chars and len(txt_strip) > 1 and txt_strip[1] in [' ', '\t'])

                # Solo es viñeta si cumple ALGUNA de estas condiciones Y tiene sangría francesa
                if (is_dash_or_dot or is_alphanumeric) and h_cm > 0.3:
                    is_bullet = True
                    is_symbol_ok = True
                    detected_symbol = first_char if is_dash_or_dot else alphanumeric_match.group(1)[0]

        return is_bullet, is_symbol_ok, detected_symbol
