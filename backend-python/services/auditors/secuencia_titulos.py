"""
secuencia_titulos.py - Auditoría ESTRICTA de Secuencia Jerárquica de Títulos.

Reglas implementadas:
- La jerarquía de títulos debe seguir el orden 1 → 2 → 3 → 4 → 5 sin saltos.
- No se permite, por ejemplo, ir de Nivel 1 directamente a Nivel 3.
- Después de un Nivel N, solo puede venir:
    a) Otro Nivel N
    b) Un Nivel N+1
    c) Cualquier nivel <= N (volver a niveles anteriores)
- Es ERROR si el siguiente título es N+2, N+3, N+4 (saltos hacia adelante).

También verifica el número de capítulo: CAPÍTULO I → II → III → IV en orden.
"""
import re
from .base_auditor import BaseAuditor


ROMAN_TO_INT = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7,
                'VIII': 8, 'IX': 9, 'X': 10}


class SecuenciaTitulosAuditor(BaseAuditor):

    def audit(self):
        self._audit_level_sequence()
        self._audit_chapter_sequence()
        self._audit_trailing_dot_consistency()

    def _audit_level_sequence(self):
        """Valida que los niveles de títulos sigan orden 1 → 2 → 3 → 4 → 5."""
        last_level = 0
        last_title_text = ""
        last_title_idx = -1

        for p in self.paragraphs:
            if not p.get("is_in_body"):
                continue
            if p.get("in_table"):
                continue

            body_level = p.get("body_level", 0)
            if body_level == 0:
                continue

            txt = p["text"].strip()
            norm = p["norm"]

            # Detectar si el párrafo es un título real
            is_capitulo = bool(re.match(r"^CAP[ÍI]TULO\s+(I|V|X|L|C|[0-9]+)", norm))
            es_seccion_principal = any(k in norm for k in [
                "INTRODUCCION", "MARCO TEORICO", "METODOLOGIA",
                "MATERIALES Y METODOS", "RESULTADOS Y DISCUSION",
                "CONCLUSIONES", "RECOMENDACIONES", "REFERENCIAS BIBLIOGRAFICAS"
            ]) and (
                p.get('style_id', '').upper().startswith('HEADING')
                or txt.isupper()
                or any(r.get('bold') for r in p.get('runs', []))
            )

            numbering_match = re.match(r'^(\d+(?:\.\d+)+)\.?(?:[\s\t]+|\S)', txt)
            is_title = (
                p.get('is_heading')
                or numbering_match
                or is_capitulo
                or es_seccion_principal
            )
            if not is_title:
                continue

            # Validar salto hacia adelante
            if last_level > 0 and body_level > last_level + 1:
                self._add(
                    "Jerarquía",
                    f"Salto de Nivel Inválido: Nivel {last_level} → Nivel {body_level}",
                    "error",
                    f"Se detectó un SALTO en la jerarquía de títulos. Después de un "
                    f"título de Nivel {last_level} (\"{last_title_text[:40]}...\"), "
                    f"apareció un título de Nivel {body_level} (\"{txt[:40]}...\") sin "
                    f"pasar por los niveles intermedios. La secuencia obligatoria es "
                    f"1 → 2 → 3 → 4 → 5 sin saltos hacia adelante. Inserte los niveles "
                    f"intermedios faltantes o ajuste el nivel actual.",
                    f"Nivel siguiente válido: ≤ {last_level + 1}",
                    f"Nivel detectado: {body_level} (saltó {body_level - last_level - 1} nivel(es))",
                    p_idx=p['index'],
                    p_text=txt[:60],
                )

            last_level = body_level
            last_title_text = txt
            last_title_idx = p['index']

    def _audit_chapter_sequence(self):
        """
        Valida que los capítulos sigan orden: CAPÍTULO I → II → III → IV.
        Las secciones finales (V. CONCLUSIONES, VI. RECOMENDACIONES, VII. REFERENCIAS)
        también deben mantener orden, pero usan formato distinto.
        """
        chapter_pattern = re.compile(r"^CAP[ÍI]TULO\s+([IVXLC]+)\b", re.IGNORECASE)
        last_chapter_num = 0
        last_chapter_text = ""

        for p in self.paragraphs:
            if not p.get("is_in_body"):
                continue
            if p.get("in_table"):
                continue
            txt = p["text"].strip()
            m = chapter_pattern.match(txt)
            if not m:
                continue
            roman = m.group(1).upper()
            num = ROMAN_TO_INT.get(roman)
            if num is None:
                continue

            # Capítulo debe ser secuencial: I=1, II=2, III=3, IV=4
            if num <= 4:
                expected_next = last_chapter_num + 1
                if last_chapter_num > 0 and num != expected_next:
                    self._add(
                        "Jerarquía",
                        f"Secuencia de Capítulos: {txt[:30]}",
                        "error",
                        f"Los capítulos deben ir en orden CAPÍTULO I → II → III → IV. "
                        f"Después de \"{last_chapter_text[:30]}...\" se esperaba el "
                        f"CAPÍTULO {self._int_to_roman(expected_next)}, pero apareció "
                        f"CAPÍTULO {roman}.",
                        f"CAPÍTULO {self._int_to_roman(expected_next)}",
                        f"CAPÍTULO {roman}",
                        p_idx=p['index'],
                        p_text=txt[:60],
                    )
                last_chapter_num = num
                last_chapter_text = txt

    def _int_to_roman(self, n):
        for roman, val in [('I', 1), ('II', 2), ('III', 3), ('IV', 4),
                           ('V', 5), ('VI', 6), ('VII', 7), ('VIII', 8)]:
            if val == n:
                return roman
        return str(n)

    def _audit_trailing_dot_consistency(self):
        """
        Valida que TODOS los títulos numerados (nivel 2+) usen el mismo estilo
        de punto final en su numeración:
        - Si un título usa "2.3.1." (con punto final), todos deben tener punto final.
        - Si un título usa "2.3.1" (sin punto final), todos deben omitirlo.
        - Mezclar estilos es un error de formato.

        Solo aplica a niveles 2-5 (Nivel 1 = capítulos centrados, no aplica).
        """
        with_dot = []      # Títulos cuya numeración termina con punto
        without_dot = []   # Títulos cuya numeración NO termina con punto

        for p in self.paragraphs:
            if not p.get("is_in_body"):
                continue
            if p.get("in_table"):
                continue

            txt = p["text"].strip()
            if not txt:
                continue

            # Solo títulos reales (headings o numeración manual)
            if not p.get("is_heading") and not re.match(r'^\d+(?:\.\d+)+', txt):
                continue

            # Extraer la numeración
            m = re.match(r'^(\d+(?:\.\d+)+)(\.?)(\s+|\t+)(.*)', txt)
            if not m:
                # También aceptar numeración pegada al texto (sin espacio)
                m = re.match(r'^(\d+(?:\.\d+)+)(\.?)(\S)', txt)
                if not m:
                    continue
                # Si no tiene espacio, solo extraemos las partes relevantes
                num_part = m.group(1)
                has_trailing_dot = bool(m.group(2))
            else:
                num_part = m.group(1)
                has_trailing_dot = bool(m.group(2))

            # Solo niveles 2+ (1 punto = nivel 2, 2 puntos = nivel 3, etc.)
            dot_count = num_part.count('.')
            level = dot_count + 1
            if level < 2:
                continue

            entry = {
                "p_idx": p["index"],
                "txt": txt,
                "num": num_part + ("." if has_trailing_dot else ""),
            }

            if has_trailing_dot:
                with_dot.append(entry)
            else:
                without_dot.append(entry)

        # Si no hay mezcla, no hay error
        if not with_dot or not without_dot:
            return

        # Determinar el estilo mayoritario (ese es el "correcto")
        # El grupo minoritario recibe los errores
        if len(with_dot) >= len(without_dot):
            # Mayoría usa punto final → los que NO lo tienen están mal
            dominant_style = "con punto final"
            offenders = without_dot
            for entry in offenders:
                self._add(
                    "Jerarquía",
                    f"Punto Final en Numeración: {entry['txt'][:30]}...",
                    "error",
                    f"La numeración '{entry['num']}' no termina con punto final, pero la "
                    f"mayoría de los títulos del documento SÍ lo incluyen ({len(with_dot)} "
                    f"con punto vs {len(without_dot)} sin punto). "
                    f"Todos los títulos numerados deben usar el MISMO estilo de punto final "
                    f"para mantener uniformidad.",
                    f"{entry['num']}. (con punto final)",
                    f"{entry['num']} (sin punto final)",
                    p_idx=entry["p_idx"],
                    p_text=entry["txt"][:60],
                )
        else:
            # Mayoría NO usa punto final → los que SÍ lo tienen están mal
            dominant_style = "sin punto final"
            offenders = with_dot
            for entry in offenders:
                num_without = entry['num'].rstrip('.')
                self._add(
                    "Jerarquía",
                    f"Punto Final en Numeración: {entry['txt'][:30]}...",
                    "error",
                    f"La numeración '{entry['num']}' termina con punto final, pero la "
                    f"mayoría de los títulos del documento NO lo incluyen ({len(without_dot)} "
                    f"sin punto vs {len(with_dot)} con punto). "
                    f"Todos los títulos numerados deben usar el MISMO estilo de punto final "
                    f"para mantener uniformidad.",
                    f"{num_without} (sin punto final)",
                    f"{entry['num']} (con punto final)",
                    p_idx=entry["p_idx"],
                    p_text=entry["txt"][:60],
                )
