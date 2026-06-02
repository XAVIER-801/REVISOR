"""
secuencia_tabla_figura.py - Validación ESTRICTA de la secuencia de presentación
de Tablas y Figuras según la Guía UNAP págs. 21-22.

Orden obligatorio:
    1. Etiqueta:        "Tabla N" / "Figura N"           (negrita, 12pt, izquierda)
    2. Título descriptivo:                               (cursiva, sin negrita, 12pt)
    3. La tabla/figura en sí                             (la imagen o la tabla XML)
    4. Nota: o Fuente:                                   (cursiva, dos puntos, 10pt)

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
            # Saltar el índice de tablas/figuras (allí no aplica esta regla)
            sec_upper = (p.get("section") or "").upper()
            if any(k in sec_upper for k in [
                "ÍNDICE DE TABLAS", "INDICE DE TABLAS",
                "ÍNDICE DE FIGURAS", "INDICE DE FIGURAS",
                "ÍNDICE GENERAL", "INDICE GENERAL",
            ]):
                continue

            upper = txt.upper()
            # Detectar etiqueta de tabla o figura
            m_tabla = re.match(r"^Tabla\s+(\d+)", txt)
            m_figura = re.match(r"^Figura\s+(\d+)", txt)
            if not (m_tabla or m_figura):
                continue

            kind = "Tabla" if m_tabla else "Figura"
            num = (m_tabla or m_figura).group(1)
            label = f"{kind} {num}"

            self._validate_sequence(i, p, kind, num, label)

    def _validate_sequence(self, idx, label_p, kind, num, label):
        """
        Verifica que después de la etiqueta venga, en orden:
            - título descriptivo en cursiva
            - contenido (imagen o tabla)
            - nota/fuente en cursiva
        """
        n = len(self.paragraphs)
        # Buscar próximo párrafo no vacío después de la etiqueta
        title_idx = self._next_meaningful(idx)
        if title_idx == -1:
            return

        title_p = self.paragraphs[title_idx]
        title_txt = title_p["text"].strip()

        # ── PASO 1: El siguiente párrafo debe ser TÍTULO DESCRIPTIVO en cursiva ──
        # Excepción: si el título está en el mismo párrafo que la etiqueta (caso
        # "Tabla 1   Título descriptivo"), eso ya se valida en tablas.py / figuras.py
        title_in_same_para = self._has_title_in_same_para(label_p, kind, num)
        if not title_in_same_para:
            # Verificar que NO sea la imagen, NO sea la nota directamente
            title_upper = title_txt.upper()
            has_drawing = False
            drawings = title_p.get("drawings") or []
            for d in drawings:
                if d.get("width", 0) >= 3.0:
                    has_drawing = True
                    break

            if (re.match(r"^Tabla\s+\d+", title_txt) or
                re.match(r"^Figura\s+\d+", title_txt) or
                title_upper.startswith("NOTA") or
                title_upper.startswith("FUENTE") or
                title_p.get("in_table") or
                has_drawing):
                # Falta el título descriptivo entre la etiqueta y lo siguiente
                self._add(
                    "Secuencia Tabla/Figura",
                    f"Falta título descriptivo: {label}",
                    "error",
                    f"Después de la etiqueta '{label}' debe venir un título descriptivo "
                    f"en CURSIVA (sin negrita), antes de la {kind.lower()} en sí o la nota. "
                    f"El orden obligatorio es: etiqueta → título descriptivo → "
                    f"{kind.lower()} → Nota/Fuente.",
                    "Etiqueta → Título descriptivo → contenido → Nota",
                    f"Etiqueta seguida directamente de '{title_txt[:40]}'",
                    p_idx=label_p["index"],
                    p_text=label_p["text"],
                )
                return  # No seguir validando si falta esta pieza

            # Verificar que el título sea cursiva
            title_italic = self._is_meaningfully_italic(title_p)
            title_bold = self._is_meaningfully_bold(title_p)
            if not title_italic:
                self._add(
                    "Secuencia Tabla/Figura",
                    f"Título descriptivo sin cursiva: {label}",
                    "error",
                    f"El título descriptivo de '{label}' (\"{title_txt[:40]}...\") debe "
                    f"estar en CURSIVA, sin negrita.",
                    "Cursiva sin negrita",
                    "Normal" if not title_bold else "Negrita",
                    p_idx=title_p["index"],
                    p_text=title_txt,
                )

        # ── PASO 2: Localizar el contenido (imagen para figura, tabla para tabla) ──
        content_idx = self._find_content(
            start=title_idx + 1 if not title_in_same_para else idx + 1,
            kind=kind,
        )
        if content_idx == -1:
            self._add(
                "Secuencia Tabla/Figura",
                f"Contenido ausente: {label}",
                "warning",
                f"No se detectó el contenido (imagen o tabla) después de la etiqueta "
                f"'{label}' y su título. Verifique que la {kind.lower()} esté "
                f"correctamente insertada inmediatamente después del título descriptivo.",
                f"{kind} con contenido visible",
                "Contenido no detectado",
                p_idx=label_p["index"],
                p_text=label_p["text"],
            )
            return

        # ── PASO 3: Localizar Nota/Fuente DESPUÉS del contenido ──
        nota_idx = self._find_nota_fuente(content_idx + 1, label_p["index"])
        if nota_idx == -1:
            self._add(
                "Secuencia Tabla/Figura",
                f"Falta Nota/Fuente: {label}",
                "error",
                f"Después del contenido de '{label}' debe ir una línea que comience "
                f"con 'Nota:' o 'Fuente:' (con dos puntos, en CURSIVA, 10pt).",
                "Nota: o Fuente: en cursiva después del contenido",
                "Ausente",
                p_idx=label_p["index"],
                p_text=label_p["text"],
            )
            return

        # ── PASO 4: Validar alineación de las 3 piezas al nivel contextual ──
        context_level = self._find_context_level(label_p["index"])
        expected_indent = self._level_to_indent(context_level)

        for piece_idx, piece_name in [
            (label_p["index"], f"Etiqueta '{label}'"),
            (title_idx, f"Título descriptivo de {label}") if not title_in_same_para else (None, None),
            (nota_idx, f"Nota/Fuente de {label}"),
        ]:
            if piece_idx is None:
                continue
            piece_p = self.paragraphs[piece_idx]
            piece_l_cm = round((piece_p.get("indent_left") or 0) / 567.0, 2) if (piece_p.get("indent_left") or 0) > 10 else round(piece_p.get("indent_left") or 0, 2)
            if (piece_p.get("indent_left") or 0) > 10:
                piece_l_cm = round(piece_p.get("indent_left") / 567.0, 2)
            else:
                piece_l_cm = round(piece_p.get("indent_left") or 0, 2)
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

    def _next_meaningful(self, idx):
        """Próximo párrafo no vacío después de idx."""
        for j in range(idx + 1, len(self.paragraphs)):
            if self.paragraphs[j]["text"].strip():
                return j
        return -1

    def _has_title_in_same_para(self, p, kind, num):
        """¿La etiqueta y el título están en el mismo párrafo?"""
        txt = p["text"].strip()
        m = re.match(rf"^{kind}\s+{num}\.?(.*)", txt, re.IGNORECASE)
        if not m:
            return False
        remaining = m.group(1).strip()
        # Limpiar separadores comunes al inicio como :, -, o espacios
        remaining = re.sub(r'^[:\-\s\t\.]+', '', remaining).strip()
        return len(remaining) > 2


    def _find_content(self, start, kind):
        """
        Busca el contenido de la tabla o figura desde `start`.
        Para 'Figura': busca un párrafo con drawing.
        Para 'Tabla': busca un párrafo in_table.
        Limita la búsqueda a 8 párrafos para no irse muy lejos.
        """
        for j in range(start, min(start + 8, len(self.paragraphs))):
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

    def _find_nota_fuente(self, start, label_idx):
        """Busca el primer 'Nota:' o 'Fuente:' después de `start`."""
        for j in range(start, min(start + 30, len(self.paragraphs))):
            p = self.paragraphs[j]
            txt = p["text"].strip().upper()
            if not txt:
                continue
            # Saltar contenido dentro de la tabla
            if p.get("in_table"):
                continue
            # Si encontramos otra etiqueta o título → no hay nota
            if (re.match(r"^TABLA\s+\d+", txt) or
                re.match(r"^FIGURA\s+\d+", txt) or
                re.match(r"^CAP[ÍI]TULO\s+(I|V|X|L|C|[0-9]+)", txt) or
                re.match(r"^\d+(\.\d+)*\.?\s+[A-Z]", p["text"].strip())):
                return -1
            if txt.startswith("NOTA") or txt.startswith("FUENTE"):
                return j
        return -1

    def _level_to_indent(self, level):
        """Sangría izquierda esperada según el nivel del título contextual."""
        if level in (1, 2):
            return 0.0
        if level == 3:
            return 1.25
        return 2.5  # niveles 4 y 5
