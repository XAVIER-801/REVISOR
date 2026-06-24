"""
figuras.py - Auditoría de Figuras y Tablas en bloques completos.

Cada bloque detectado (etiqueta + título + contenido + nota/fuente) se audita
como una sola unidad. Se valida:
- Estructura: debe seguir el orden Etiqueta → Título → Figura/Tabla → Nota/Fuente
- Formato de cada componente según su rol dentro del bloque
- Presencia obligatoria de Nota o Fuente al final del bloque
- Alineación y sangría de imágenes
"""
import re
from .base_auditor import BaseAuditor


SKIP_SECTIONS = [
    'JURADOS', 'SIMILITUD', 'DEDICATORIA',
    'ÍNDICE DE TABLAS', 'INDICE DE TABLAS',
    'ÍNDICE DE FIGURAS', 'INDICE DE FIGURAS',
    'ÍNDICE GENERAL', 'INDICE GENERAL',
    'ÍNDICE DE CUADROS', 'INDICE DE CUADROS',
    'ÍNDICE DE ILUSTRACIONES', 'INDICE DE ILUSTRACIONES',
    'TABLA DE CONTENIDOS', 'TABLA DE CONTENIDO',
]

STOP_LABELS = [
    r'^TABLA\s+\d+',
    r'^FIGURA\s+\d+',
    r'^CAP[ÍI]TULO\s+(I|V|X|L|C|[0-9]+)',
    r'^\d+(\.\d+)*\.?\s+[A-Z]',
]

STOP_KEYWORDS = [
    "INTRODUCCION", "RESUMEN", "ABSTRACT", "CONCLUSIONES",
    "RECOMENDACIONES", "REFERENCIAS BIBLIOGRAFICAS", "ANEXOS",
]


def _expected_indent(level):
    if level in (1, 2):
        return 0.0
    elif level == 3:
        return 1.25
    return 2.5


class FigurasAuditor(BaseAuditor):

    def audit(self):
        self._audit_blocks()
        self._audit_table_contents()

    # ═══════════════════════════════════════════════════════════════════
    # DETECCIÓN Y AGRUPACIÓN DE BLOQUES
    # ═══════════════════════════════════════════════════════════════════

    def _find_block_end(self, start_idx):
        """Retorna el índice (exclusivo) donde termina el bloque que
        comienza en start_idx (etiqueta Tabla/Figura)."""
        for j in range(start_idx + 1, len(self.paragraphs)):
            p = self.paragraphs[j]
            txt = p["text"].strip()
            upper = txt.upper()
            if not txt:
                continue
            for pat in STOP_LABELS:
                if re.match(pat, upper):
                    return j
            if upper in STOP_KEYWORDS:
                return j
            if p.get("is_heading"):
                return j
        return len(self.paragraphs)

    def _collect_block_components(self, start_idx):
        """Recolecta los párrafos del bloque en un dict."""
        label_p = self.paragraphs[start_idx]
        label_match = re.match(
            r'^((?:Tabla|Figura)\s+\d+\.?\s*)(.*)',
            label_p["text"].strip(), re.IGNORECASE,
        )
        label_text = label_match.group(1).strip() if label_match else label_p["text"].strip()
        title_in_same = (label_match.group(2).strip() if label_match else "")

        is_table = bool(re.match(r'^TABLA\s+\d+', label_p["text"].strip().upper()))
        lbl_type = "Tabla" if is_table else "Figura"

        title_para = None
        title_text = ""
        content_paras = []
        note_para = None
        note_text = ""

        end_idx = self._find_block_end(start_idx)
        idx = start_idx + 1

        # 1) Título (si no va en la misma línea)
        if not title_in_same:
            while idx < end_idx:
                p = self.paragraphs[idx]
                txt = p["text"].strip()
                if not txt:
                    idx += 1
                    continue
                if txt.upper().split(" ", 1)[0].rstrip(":") in ("NOTA", "FUENTE"):
                    break
                if p.get("drawings") or p.get("in_table"):
                    break
                title_para = p
                title_text = txt
                idx += 1
                break

        # 2) Contenido (drawings / in_table / resto hasta Nota/Fuente)
        while idx < end_idx:
            p = self.paragraphs[idx]
            txt = p["text"].strip()
            if not txt:
                content_paras.append(p)
                idx += 1
                continue
            if txt.upper().split(" ", 1)[0].rstrip(":") in ("NOTA", "FUENTE"):
                break
            content_paras.append(p)
            idx += 1

        # 3) Nota/Fuente
        if idx < end_idx:
            p = self.paragraphs[idx]
            txt = p["text"].strip()
            if txt.upper().split(" ", 1)[0].rstrip(":") in ("NOTA", "FUENTE"):
                note_para = p
                note_text = txt

        return {
            "label_idx": start_idx,
            "label_p": label_p,
            "label_text": label_text,
            "lbl_type": lbl_type,
            "title_para": title_para,
            "title_text": title_text,
            "title_in_same": title_in_same,
            "content_paras": content_paras,
            "note_para": note_para,
            "note_text": note_text,
            "end_idx": end_idx,
        }

    # ═══════════════════════════════════════════════════════════════════
    # AUDITORÍA DE BLOQUE COMPLETO
    # ═══════════════════════════════════════════════════════════════════

    def _audit_blocks(self):
        """Itera párrafos, detecta etiquetas Tabla/Figura y audita cada
        bloque completo como una unidad."""
        i = 0
        while i < len(self.paragraphs):
            p = self.paragraphs[i]
            txt = p["text"].strip()
            sec_upper = p.get("section", "").upper()
            if any(k in sec_upper for k in SKIP_SECTIONS):
                i += 1
                continue
            upper = txt.upper()
            if not re.match(r'^(TABLA|FIGURA)\s+\d+', upper):
                i += 1
                continue
            if p.get("in_table"):
                i += 1
                continue

            block = self._collect_block_components(i)
            self._audit_block_structure(block)
            self._audit_block_formatting(block)
            self._audit_block_images(block)
            i = block["end_idx"]

    # ═══════════════════════════════════════════════════════════════════
    # VALIDACIONES ESTRUCTURALES DEL BLOQUE
    # ═══════════════════════════════════════════════════════════════════

    def _audit_block_structure(self, block):
        """Valida que el bloque tenga la secuencia correcta."""
        bid = f"{block['lbl_type']} {block['label_text']}"
        errors = []

        if not block["title_text"]:
            errors.append(f"Falta el título descriptivo para {bid}. Debe ir después de la etiqueta, en CURSIVA y sin negrita.")

        if block["note_para"] is None:
            errors.append(f"No se encontró Nota o Fuente obligatoria para {bid}. Toda {block['lbl_type'].lower()} debe incluir su correspondiente Nota o Fuente debajo.")
        else:
            first_word = block["note_text"].split(" ", 1)[0]
            if not first_word.endswith(":"):
                errors.append(f"La palabra '{first_word}' en la nota/fuente de {bid} debe terminar con dos puntos (:).")

        if errors:
            self._add(
                "Figuras" if block["lbl_type"] == "Figura" else "Tablas",
                f"Estructura: {bid}",
                "error",
                " | ".join(errors),
                "Secuencia: Etiqueta → Título → Contenido → Nota/Fuente",
                "Estructura incompleta",
                p_idx=block["label_idx"],
                p_text=block["label_text"],
            )

    # ═══════════════════════════════════════════════════════════════════
    # VALIDACIONES DE FORMATO POR COMPONENTE
    # ═══════════════════════════════════════════════════════════════════

    def _audit_block_formatting(self, block):
        """Audita formato de cada componente del bloque."""
        self._audit_label_format(block)
        if block["title_para"]:
            self._audit_title_format(block)
        elif block["title_in_same"]:
            self._audit_title_in_same(block)
        if block["note_para"]:
            self._audit_note_format(block)

    def _audit_label_format(self, block):
        bid = f"{block['lbl_type']} {block['label_text']}"
        p = block["label_p"]
        txt = p["text"].strip()
        idx = p["index"]
        level = self._find_context_level(idx)
        exp_l_cm = _expected_indent(level)
        l_cm = round(p.get("indent_left") or 0, 2)
        align = p.get("alignment", "left")
        is_bold = self._is_meaningfully_bold(p)
        font_size = p["runs"][0].get("size", 0) if p.get("runs") else 0
        s_before = p.get("spacing_before", 0)
        s_after = p.get("spacing_after", 0)
        line_spacing = p.get("line_spacing")

        errors = []

        if align != "left" and align != "both":
            errors.append(f"Alineación: debe ser Izquierda, hallado {self._align_display(align)}")

        if abs(l_cm - exp_l_cm) > 0.1:
            errors.append(f"Sangría: debe ser {exp_l_cm}cm (Nivel {level}), hallado {l_cm}cm")

        if not is_bold:
            errors.append("Estilo: debe ser Negrita, hallado Normal")

        if font_size > 0 and abs(font_size - 12) > 0.5:
            errors.append(f"Tamaño: debe ser 12pt, hallado {font_size}pt")

        if s_before > 1.0:
            errors.append(f"Espaciado anterior: debe ser 0pt, hallado {s_before}pt")
        if s_after > 1.0:
            errors.append(f"Espaciado posterior: debe ser 0pt, hallado {s_after}pt")

        if line_spacing is not None and abs(line_spacing - 2.0) > 0.2:
            errors.append(f"Interlineado: debe ser 2.0, hallado {line_spacing}")

        if errors:
            self._add(
                "Figuras" if block["lbl_type"] == "Figura" else "Tablas",
                f"Formato Etiqueta: {bid}",
                "error",
                " | ".join(errors),
                "12pt, Negrita, Izquierda, Sangría según nivel, Espaciado 0/0, Interlineado 2.0",
                "Formato incorrecto",
                p_idx=idx, p_text=txt,
            )

    def _audit_title_format(self, block):
        bid = f"{block['lbl_type']} {block['label_text']}"
        p = block["title_para"]
        txt = p["text"].strip()
        idx = p["index"]
        level = self._find_context_level(idx)
        exp_l_cm = _expected_indent(level)
        l_cm = round(p.get("indent_left") or 0, 2)
        align = p.get("alignment", "left")
        is_italic = any(r.get("italic") for r in p.get("runs", []))
        is_bold = any(r.get("bold") for r in p.get("runs", []))
        font_size = p["runs"][0].get("size", 0) if p.get("runs") else 0
        s_before = p.get("spacing_before", 0)
        s_after = p.get("spacing_after", 0)
        line_spacing = p.get("line_spacing")

        errors = []

        if not is_italic or is_bold:
            style_parts = []
            if not is_italic:
                style_parts.append("debe ser Cursiva")
            if is_bold:
                style_parts.append("no debe ser Negrita")
            errors.append(f"Estilo: {', '.join(style_parts)}")

        if align != "left" and align != "both":
            errors.append(f"Alineación: debe ser Izquierda, hallado {self._align_display(align)}")

        if abs(l_cm - exp_l_cm) > 0.1:
            errors.append(f"Sangría: debe ser {exp_l_cm}cm (Nivel {level}), hallado {l_cm}cm")

        if font_size > 0 and abs(font_size - 12) > 0.5:
            errors.append(f"Tamaño: debe ser 12pt, hallado {font_size}pt")

        if s_before > 1.0:
            errors.append(f"Espaciado anterior: debe ser 0pt, hallado {s_before}pt")
        if s_after > 1.0:
            errors.append(f"Espaciado posterior: debe ser 0pt, hallado {s_after}pt")

        if line_spacing is not None and abs(line_spacing - 2.0) > 0.2:
            errors.append(f"Interlineado: debe ser 2.0, hallado {line_spacing}")

        if errors:
            self._add(
                "Figuras" if block["lbl_type"] == "Figura" else "Tablas",
                f"Formato Título: {bid}",
                "error",
                " | ".join(errors),
                "12pt, Cursiva, Sin Negrita, Izquierda, Sangría según nivel",
                "Formato incorrecto",
                p_idx=idx, p_text=txt,
            )

    def _audit_title_in_same(self, block):
        """Audita el título cuando está en el mismo párrafo que la etiqueta."""
        bid = f"{block['lbl_type']} {block['label_text']}"
        p = block["label_p"]
        txt = p["text"].strip()
        idx = p["index"]

        label_match = re.match(r'^((?:Tabla|Figura)\s+\d+\.?\s*)(.*)', txt, re.IGNORECASE)
        label_len = len(label_match.group(1)) if label_match else len(txt)

        title_runs = []
        char_count = 0
        for run in p.get("runs", []):
            run_text = run.get("text", "")
            if char_count + len(run_text) > label_len:
                title_runs.append(run)
            char_count += len(run_text)

        if title_runs:
            is_italic = any(r.get("italic") for r in title_runs)
            is_bold = any(r.get("bold") for r in title_runs)
            if not is_italic or is_bold:
                style_parts = []
                if not is_italic:
                    style_parts.append("debe ser Cursiva")
                if is_bold:
                    style_parts.append("no debe ser Negrita")
                self._add(
                    "Figuras" if block["lbl_type"] == "Figura" else "Tablas",
                    f"Formato Título: {bid}",
                    "error",
                    f"Título '{block['title_text'][:30]}...': {', '.join(style_parts)}",
                    "Cursiva, Sin Negrita",
                    f"{'Cursiva' if is_italic else 'Normal'} {'+ Negrita' if is_bold else ''}",
                    p_idx=idx, p_text=txt,
                )

    def _audit_note_format(self, block):
        bid = f"{block['lbl_type']} {block['label_text']}"
        p = block["note_para"]
        txt = p["text"].strip()
        idx = p["index"]
        level = self._find_context_level(idx)
        exp_l_cm = _expected_indent(level)
        l_cm = round(p.get("indent_left") or 0, 2)
        font_size = p["runs"][0].get("size", 0) if p.get("runs") else 0
        s_before = p.get("spacing_before", 0)
        s_after = p.get("spacing_after", 0)
        line_spacing = p.get("line_spacing")

        # Estilo palabra "Nota:"/"Fuente:" (cursiva, sin negrita)
        first_word = txt.split(" ", 1)[0]
        label_len = len(first_word)
        accumulated = 0
        label_is_italic = True
        label_is_bold = False
        for r in p.get("runs", []):
            r_txt = r.get("text", "")
            if not r_txt:
                continue
            for ch in r_txt:
                if accumulated < label_len:
                    if not r.get("italic"):
                        label_is_italic = False
                    if r.get("bold"):
                        label_is_bold = True
                    accumulated += 1

        errors = []

        if not first_word.endswith(":"):
            errors.append(f"'{first_word}' debe terminar con dos puntos (:)")

        if not label_is_italic or label_is_bold:
            style_parts = []
            if not label_is_italic:
                style_parts.append("Cursiva requerida")
            if label_is_bold:
                style_parts.append("Negrita no permitida")
            errors.append(f"Estilo '{first_word}': {', '.join(style_parts)}")

        if font_size > 0 and abs(font_size - 10) > 0.5:
            errors.append(f"Tamaño: debe ser 10pt, hallado {font_size}pt")

        if abs(l_cm - exp_l_cm) > 0.1:
            errors.append(f"Sangría: debe ser {exp_l_cm}cm (Nivel {level}), hallado {l_cm}cm")

        if s_before > 1.0:
            errors.append(f"Espaciado anterior: debe ser 0pt, hallado {s_before}pt")
        if abs(s_after - 15.0) > 2.0:
            errors.append(f"Espaciado posterior: debe ser 15pt, hallado {s_after}pt")

        if line_spacing is not None and abs(line_spacing - 1.5) > 0.2:
            errors.append(f"Interlineado: debe ser 1.5, hallado {line_spacing}")

        if errors:
            category = "Figuras" if block["lbl_type"] == "Figura" else "Tablas"
            self._add(
                category,
                f"Formato Nota/Fuente: {bid}",
                "error",
                " | ".join(errors),
                "10pt, Normal, Cursiva solo 'Nota:', Sangría según nivel, Espaciado 0/15",
                "Formato incorrecto",
                p_idx=idx, p_text=txt,
            )

    # ═══════════════════════════════════════════════════════════════════
    # VALIDACIÓN DE IMÁGENES (párrafos con drawings)
    # ═══════════════════════════════════════════════════════════════════

    def _audit_block_images(self, block):
        """Valida alineación y sangría de imágenes dentro del bloque."""
        for p in block["content_paras"]:
            drawings = p.get("drawings", [])
            if not drawings:
                continue
            self._audit_single_image(p, block)

    def _audit_single_image(self, p, block):
        bid = f"{block['lbl_type']} {block['label_text']}"
        drawings = p.get("drawings", [])
        is_large = any(d.get("width", 0) >= 13.0 for d in drawings)
        align = p.get("alignment", "left")
        idx = p["index"]
        level = self._find_context_level(idx)
        exp_l_cm = _expected_indent(level)
        l_cm = round(p.get("indent_left") or 0, 2)
        category = "Figuras" if block["lbl_type"] == "Figura" else "Tablas"

        img_errors = []

        # Alineación
        if is_large:
            if align not in ("left", "both", "justify", "center"):
                img_errors.append(f"Alineación: debe ser Izquierda o Centrado, hallado {self._align_display(align)}")
        else:
            if align not in ("left", "both"):
                img_errors.append(f"Alineación: debe ser Izquierda, hallado {self._align_display(align)}")

        # Sangría (solo si alineación izquierda)
        if align in ("left", "both") and abs(l_cm - exp_l_cm) > 0.1:
            img_errors.append(f"Sangría: debe ser {exp_l_cm}cm (Nivel {level}), hallado {l_cm}cm")

        if img_errors:
            self._add(
                category,
                f"Formato Imagen: {bid}",
                "error",
                " | ".join(img_errors),
                "Izquierda, Sangría según nivel",
                "Formato incorrecto",
                p_idx=idx, p_text=f"[Imagen de {block['lbl_type'].lower()}]",
            )

    # ═══════════════════════════════════════════════════════════════════
    # CONTENIDO DE TABLA
    # ═══════════════════════════════════════════════════════════════════

    def _audit_table_contents(self):
        """Audita el contenido dentro de las tablas (Encabezado, Interlineado)."""
        for p in self.paragraphs:
            if not p.get('in_table'):
                continue

            txt = p['text'].strip()
            if not txt:
                continue

            if p.get('is_table_header'):
                has_xml_bold = any(r.get('bold') for r in p.get('runs', []))
                txt_letters = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ]', '', txt)
                has_caps_bold = len(txt_letters) > 1 and txt_letters == txt_letters.upper()
                is_bold = has_xml_bold or has_caps_bold
                align = p.get('alignment', 'left')

                if not is_bold or align != 'center':
                    self._add("Tablas", f"Encabezado Tabla: {txt[:20]}...", "error",
                             "El encabezado de las tablas (primera fila) debe estar centrado y en negrita.",
                             "Centrado, Negrita", f"{self._align_display(align)}, {'Negrita' if is_bold else 'Normal'}", p_idx=p['index'], p_text=txt)

            line_spacing = p.get('line_spacing', 1.0)
            if abs(line_spacing - 1.0) > 0.2 and abs(line_spacing - 1.5) > 0.2:
                self._add("Tablas", f"Interlineado Tabla: {txt[:20]}...", "warning",
                         "El contenido de la tabla debe tener interlineado 1.0 o 1.5.",
                         "1.0 o 1.5", str(line_spacing), p_idx=p['index'], p_text=txt)

    # ═══════════════════════════════════════════════════════════════════
    # HELPERS (heredados de BaseAuditor: _find_context_level)
    # ═══════════════════════════════════════════════════════════════════
