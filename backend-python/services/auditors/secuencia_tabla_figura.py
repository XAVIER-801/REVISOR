"""
secuencia_tabla_figura.py - Validación ESTRICTA de la secuencia de presentación
de Tablas y Figuras según la Guía UNAP págs. 21-22.

Orden obligatorio (cada elemento en su propia línea):
    1. Etiqueta:        "Tabla N" / "Figura N"           SOLA en su línea
    2. Título descriptivo:                               (cursiva, sin negrita, 12pt)
    3. La tabla/figura en sí                             (la imagen o la tabla XML)
    4. Nota: o Fuente:                                   (cursiva, dos puntos, 10pt)

La etiqueta NO debe contener el título en la misma línea.
El título descriptivo debe estar en la línea SIGUIENTE a la etiqueta.

Las 4 partes deben tener sangría izquierda alineada al nivel del último título
contextual (Nivel 1 = 0cm, Nivel 3 = 1.25cm, Nivel 4-5 = 2.5cm).

Si la TABLA se divide en dos páginas, la primera fila (encabezado) debe estar
marcada como "Repetir como fila de encabezado" (validado en tablas.py).

Este auditor se enfoca exclusivamente en el ORDEN SECUENCIAL.
"""
import re
from .base_auditor import BaseAuditor


class SecuenciaTablaFiguraAuditor(BaseAuditor):

    def audit(self):
        for i, p in enumerate(self.paragraphs):
            txt = p["text"].strip()
            if not txt or p.get("in_table"):
                continue

            sec_upper = (p.get("section") or "").upper()
            if any(k in sec_upper for k in [
                "ÍNDICE DE TABLAS", "INDICE DE TABLAS",
                "ÍNDICE DE FIGURAS", "INDICE DE FIGURAS",
                "ÍNDICE GENERAL", "INDICE GENERAL",
            ]):
                continue

            upper = txt.upper()
            m_tabla = re.match(r"^TABLA\s+(\d+)", upper)
            m_figura = re.match(r"^FIGURA\s+(\d+)", upper)
            if not (m_tabla or m_figura):
                continue

            kind = "Tabla" if m_tabla else "Figura"
            num = (m_tabla or m_figura).group(1)
            label = f"{kind} {num}"

            self._validate_full_sequence(i, p, kind, num, label)

    def _validate_full_sequence(self, label_idx, label_p, kind, num, label):
        """
        Valida la secuencia completa de 4 pasos:
          1. Etiqueta "Figura/Tabla X" (SOLA en su línea, sin título adjunto)
          2. Título descriptivo (cursiva, sin negrita) en la línea siguiente
          3. Contenido (imagen para figura, XML table para tabla)
          4. Nota o Fuente

        Reporta TODAS las partes faltantes/incorrectas, no solo la primera.
        """
        n = len(self.paragraphs)
        issues = []

        # ── REGLA 0: La etiqueta debe estar SOLA en su línea ──
        title_in_same = self._has_title_in_same_para(label_p, kind, num)
        if title_in_same:
            issues.append(("error", "Etiqueta con título en la misma línea",
                           f"La etiqueta '{label}' tiene texto del título descriptivo en la MISMA línea. "
                           f"La etiqueta debe estar SOLA en su línea. "
                           f"El título descriptivo debe ir en la línea SIGUIENTE, en CURSIVA.",
                           "Etiqueta sola en su línea", "Etiqueta y título en el mismo párrafo"))

        # ── PASO 1: Localizar Título descriptivo en la línea siguiente ──
        title_idx = -1
        title_in_italic = False
        title_is_bold = False
        title_text = ""

        title_idx = self._find_title_after(label_idx, kind, num)
        if title_idx != -1:
            title_p = self.paragraphs[title_idx]
            title_text = title_p["text"].strip()
            title_in_italic = self._is_meaningfully_italic(title_p)
            title_is_bold = self._is_meaningfully_bold(title_p)

        if title_idx == -1 or not title_text:
            issues.append(("error", "Falta título descriptivo",
                           f"La {kind.lower()} '{label}' no tiene título descriptivo en la línea siguiente. "
                           f"Después de la etiqueta debe ir el título en CURSIVA en la línea siguiente. "
                           f"El orden obligatorio es: Etiqueta (sola) → Título (CURSIVA) → {kind.lower()} → Nota/Fuente.",
                           "Título descriptivo después de la etiqueta", "Ausente"))
        else:
            if not title_in_italic:
                issues.append(("error", "Título sin cursiva",
                               f"El título descriptivo de '{label}' DEBE estar en CURSIVA (sin negrita). "
                               f"Hallado: {'Normal' if not title_is_bold else 'Negrita'}.",
                               "Cursiva", "Normal" if not title_is_bold else "Negrita"))
            if title_is_bold:
                issues.append(("error", "Título con negrita",
                               f"El título descriptivo de '{label}' NO debe estar en Negrita. Debe ir solo en CURSIVA.",
                               "Sin Negrita", "Negrita"))

        # ── PASO 2: Localizar Contenido (imagen o tabla) ──
        content_idx = -1
        content_found = False
        if title_idx != -1:
            search_start = title_idx + 1
        else:
            search_start = label_idx + 1

        content_idx = self._find_content(search_start, kind)
        if content_idx == -1:
            issues.append(("error", f"Contenido ausente",
                           f"No se detectó {'imagen' if kind == 'Figura' else 'tabla XML'} para '{label}' "
                           f"después de la etiqueta y su título. "
                           f"Verifique que {'la imagen esté insertada' if kind == 'Figura' else 'la tabla esté presente'} "
                           f"inmediatamente después del título descriptivo.",
                           f"{kind} visible", "No detectado"))
        else:
            content_found = True

        # ── PASO 3: Localizar Nota o Fuente ──
        nota_idx = -1
        nota_text = ""
        nota_in_italic = False
        nota_is_bold = False
        nota_has_colon = False

        if content_idx != -1:
            nota_search_start = content_idx + 1
        elif title_idx != -1:
            nota_search_start = max(title_idx, label_idx) + 1
        else:
            nota_search_start = label_idx + 1

        nota_idx = self._find_nota_fuente(nota_search_start, label_idx, kind)
        if nota_idx != -1:
            nota_p = self.paragraphs[nota_idx]
            nota_text = nota_p["text"].strip()
            nota_in_italic = self._is_meaningfully_italic(nota_p)
            nota_is_bold = self._is_meaningfully_bold(nota_p)
            first_word = nota_text.split(" ", 1)[0]
            nota_has_colon = first_word.endswith(":")

        if nota_idx == -1:
            issues.append(("error", "Falta nota o fuente",
                           f"La {kind.lower()} '{label}' debe incluir una línea 'Nota:' o 'Fuente:' "
                           f"(con dos puntos, en CURSIVA, 10pt) después del contenido. "
                           f"Toda {kind.lower()} debe llevar su correspondiente Nota o Fuente.",
                           "Nota: o Fuente:", "Ausente"))
        else:
            if not nota_has_colon:
                issues.append(("error", "Nota/fuente sin dos puntos",
                               f"La palabra '{nota_text.split(' ', 1)[0]}' debe terminar con dos puntos (:).",
                               "Nota: o Fuente:", nota_text.split(" ", 1)[0]))
            if not nota_in_italic:
                issues.append(("error", "Nota/fuente sin cursiva",
                               f"La palabra 'Nota:' o 'Fuente:' DEBE estar en CURSIVA (sin negrita).",
                               "Cursiva", "Normal"))
            if nota_is_bold:
                issues.append(("error", "Nota/fuente con negrita",
                               f"La palabra 'Nota:' o 'Fuente:' NO debe estar en Negrita.",
                               "Sin Negrita", "Negrita"))

        # ── PASO 4: Validar ORDEN de la secuencia ──
        if content_found and nota_idx != -1 and nota_idx < content_idx:
            issues.insert(0, ("error", "ORDEN INCORRECTO: Nota/Fuente antes que contenido",
                              f"La Nota/Fuente aparece ANTES que el contenido de la {kind.lower()} "
                              f"'{label}'. El orden correcto es: Etiqueta → Título → {kind} → Nota/Fuente.",
                              f"Nota/Fuente después del contenido",
                              f"Nota/Fuente en párrafo {nota_idx}, contenido en párrafo {content_idx}"))

        if title_idx != -1 and content_found and content_idx < title_idx:
            issues.insert(0, ("error", "ORDEN INCORRECTO: Contenido antes que título",
                              f"El contenido de la {kind.lower()} '{label}' aparece ANTES que el título "
                              f"descriptivo. El orden correcto es: Etiqueta → Título → {kind} → Nota/Fuente.",
                              "Título → Contenido",
                              f"Contenido en párrafo {content_idx}, título en párrafo {title_idx}"))

        if nota_idx != -1 and title_idx != -1 and nota_idx < title_idx:
            issues.insert(0, ("error", "ORDEN INCORRECTO: Nota/Fuente antes que título",
                              f"La Nota/Fuente aparece ANTES que el título descriptivo de la "
                              f"{kind.lower()} '{label}'. El orden correcto es: Etiqueta → Título → {kind} → Nota/Fuente.",
                              "Título → Contenido → Nota/Fuente",
                              f"Nota/Fuente en párrafo {nota_idx}, título en párrafo {title_idx}"))

        # ── Reportar TODOS los issues encontrados ──
        for severity, rule_name, msg, expected, actual in issues:
            self._add(
                "Secuencia Tabla/Figura",
                f"{rule_name}: {label}",
                severity,
                msg,
                expected,
                actual,
                p_idx=label_p["index"],
                p_text=label_p["text"],
            )

        # ── PASO 5 (opcional): Validar alineación contextual si la secuencia está completa ──
        if not issues:
            context_level = self._find_context_level(label_idx)
            expected_indent = self._level_to_indent(context_level)

            for piece_idx, piece_name in [
                (label_idx, f"Etiqueta '{label}'"),
                (title_idx, f"Título descriptivo de {label}"),
                (nota_idx, f"Nota/Fuente de {label}"),
            ]:
                if piece_idx is None:
                    continue
                piece_p = self.paragraphs[piece_idx]
                raw_indent = piece_p.get("indent_left") or 0
                if raw_indent > 10:
                    piece_l_cm = round(raw_indent / 567.0, 2)
                else:
                    piece_l_cm = round(raw_indent, 2)
                if abs(piece_l_cm - expected_indent) > 0.15:
                    self._add(
                        "Secuencia Tabla/Figura",
                        f"Alineación contextual: {piece_name}",
                        "warning",
                        f"{piece_name} debe estar alineada al nivel contextual "
                        f"(Nivel {context_level} → sangría izquierda {expected_indent}cm). "
                        f"Las 3 piezas (etiqueta, título descriptivo, nota/fuente) deben "
                        f"compartir la misma sangría izquierda según el nivel del título "
                        f"contextual al que pertenece la {label.split()[0].lower()}.",
                        f"Izquierda {expected_indent}cm",
                        f"Izquierda {piece_l_cm}cm",
                        p_idx=piece_idx,
                        p_text=piece_p["text"][:60],
                    )

    # ── Helpers ──

    def _find_title_after(self, label_idx, kind, num):
        """Busca el título descriptivo después de la etiqueta."""
        for j in range(label_idx + 1, min(label_idx + 30, len(self.paragraphs))):
            p = self.paragraphs[j]
            txt = p["text"].strip()
            if not txt:
                continue
            if p.get("in_table"):
                continue
            upper = txt.upper()

            # Si es otra etiqueta de tabla o figura → no hay título
            if re.match(r"^(TABLA|FIGURA)\s+\d+", upper):
                return -1

            # Si empieza con NOTA o FUENTE → no hay título
            if upper.startswith("NOTA") or upper.startswith("FUENTE"):
                return -1

            # Si tiene un drawing grande → no es título, es la imagen
            drawings = p.get("drawings") or []
            if any(d.get("width", 0) >= 3.0 for d in drawings):
                return -1

            # Si es un encabezado de sección → no hay título
            if re.match(r"^CAP[ÍI]TULO\s+(I|V|X|L|C|[0-9]+)", upper):
                return -1

            # Es un candidato a título
            return j

        return -1

    def _has_title_in_same_para(self, p, kind, num):
        txt = p["text"].strip()
        m = re.match(rf"^{kind}\s+{num}\.?\s*[:\-]?\s*(.+)", txt, re.IGNORECASE)
        if not m:
            return False
        remaining = m.group(1).strip()
        return len(remaining) > 2

    def _find_content(self, start, kind):
        """
        Busca el contenido de la tabla o figura desde `start`.
        Para 'Figura': busca un párrafo con drawing >= 3.0cm.
        Para 'Tabla': busca un párrafo in_table.
        """
        limit = min(start + 15, len(self.paragraphs))
        for j in range(start, limit):
            p = self.paragraphs[j]
            if kind == "Figura":
                drawings = p.get("drawings") or []
                for d in drawings:
                    if d.get("width", 0) >= 3.0:
                        return j
            elif kind == "Tabla":
                if p.get("in_table"):
                    return j
        return -1

    def _find_nota_fuente(self, start, label_idx, kind):
        """Busca el primer 'Nota:' o 'Fuente:' después de `start`."""
        limit = min(start + 40, len(self.paragraphs))
        for j in range(start, limit):
            p = self.paragraphs[j]
            txt = p["text"].strip().upper()
            if not txt:
                continue
            if p.get("in_table"):
                continue

            if (re.match(r"^(TABLA|FIGURA)\s+\d+", txt) or
                re.match(r"^CAP[ÍI]TULO\s+(I|V|X|L|C|[0-9]+)", txt)):
                return -1

            if txt.startswith("NOTA") or txt.startswith("FUENTE"):
                return j

        return -1

    def _level_to_indent(self, level):
        if level in (1, 2):
            return 0.0
        if level == 3:
            return 1.25
        return 2.5

    def _check_run_style(self, p, style, start_after_prefix=False):
        """
        Verifica el estilo (italic/bold) en los runs de un párrafo.
        Si start_after_prefix=True, solo revisa después del prefijo 
        (para cuando título está en el mismo párrafo que la etiqueta).
        """
        if start_after_prefix:
            m = re.match(r"^(Figura|Tabla)\s+\d+\.?\s*[:\-]?\s*", p["text"], re.IGNORECASE)
            prefix_len = len(m.group(0)) if m else 0
            accumulated = 0
            for r in p.get("runs", []):
                r_txt = r.get("text", "")
                if not r_txt:
                    continue
                for _ in r_txt:
                    if accumulated >= prefix_len:
                        if r.get(style):
                            return True
                    accumulated += 1
            return False

        return any(r.get(style) for r in p.get("runs", []) if r.get("text", "").strip())
