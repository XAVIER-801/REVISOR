"""
resumen.py - Auditoría de la sección de RESUMEN (Español).

Reglas implementadas (Guía UNAP pág. 16):
- Título 'RESUMEN' a 16pt, centrado, negrita, anterior 0/posterior 10pt
- Contenido: 12pt, justificado, normal, interlineado 2.0, sin sangría
- Extensión: entre 250 y 300 palabras
- "Palabras clave:" en NEGRITA, primera letra MAYÚSCULA
- Palabras clave separadas por comas y ordenadas ALFABÉTICAMENTE
- Palabras en minúscula con primera letra mayúscula
"""
import re
from .base_auditor import BaseAuditor


class ResumenAuditor(BaseAuditor):

    def audit(self):
        content = []
        content_paragraphs = []
        capture = False
        resumen_p_idx = -1
        keywords_p = None
        keywords_idx = -1

        for i, p in enumerate(self.paragraphs):
            # Skip index zone and index entries to avoid matching the index page's "RESUMEN"
            if self.last_index_idx != -1 and i <= self.last_index_idx:
                continue
            
            txt = p["text"]
            if "\t" in txt or "...." in txt or bool(re.search(r"\d+$", txt.strip())):
                continue

            norm = p["norm"]
            if norm == "RESUMEN" and resumen_p_idx == -1:
                resumen_p_idx = i
                capture = True
                self._audit_title(i, p)
                continue
            if "PALABRAS CLAVE" in norm and capture:
                capture = False
                keywords_p = p
                keywords_idx = i
                self._audit_keywords(i, p)
                break
            if capture:
                # Guard: stop capturing if we hit another major section
                _OTHER_SECTIONS = {
                    "ABSTRACT", "INTRODUCCION", "INDICE GENERAL",
                    "INDICE DE TABLAS", "INDICE DE FIGURAS",
                    "INDICE DE CUADROS", "INDICE DE ILUSTRACIONES",
                    "DEDICATORIA", "AGRADECIMIENTOS", "CONCLUSIONES",
                    "RECOMENDACIONES", "REFERENCIAS BIBLIOGRAFICAS",
                    "ANEXOS", "DECLARACION JURADA",
                    "AUTORIZACION PARA EL DEPOSITO", "ACRONIMOS",
                }
                if norm in _OTHER_SECTIONS or (p.get("is_heading") and norm != "RESUMEN"):
                    capture = False
                    break
                if p["text"].strip():
                    content.append(p["text"])
                    content_paragraphs.append((i, p))

        # Extensión
        if content:
            full_text = " ".join(content)
            words = len(full_text.split())
            ok_words = 250 <= words <= 300
            self._add(
                "Resumen y Abstract",
                "Extensión del Resumen",
                "passed" if ok_words else "error",
                f"El resumen debe tener entre 250 y 300 palabras. Hallado: {words} palabras.",
                "250-300 palabras",
                f"{words} palabras",
                p_idx=resumen_p_idx if resumen_p_idx != -1 else None,
            )

        # Formato del contenido
        for i, p in content_paragraphs:
            self._audit_content_paragraph(i, p)

    # ── Validación del título "RESUMEN" ──────────────────────────────────

    def _audit_title(self, idx, p):
        txt = p["text"].strip()
        size, bold, italic, font = self._get_p_props(p)
        align = p.get("alignment", "left")
        s_before = p.get("spacing_before", 0)
        s_after = p.get("spacing_after", 0)
        line_spacing = p.get("line_spacing")
        l_cm = round((p.get("indent_left") or 0) / 567.0, 2)

        if abs(size - 16) > 0.5:
            self._add("Resumen y Abstract", "Tamaño Título RESUMEN", "error",
                      "El título 'RESUMEN' debe ser de 16pt.",
                      "16pt", f"{size}pt", p_idx=idx, p_text=txt)

        if align != "center":
            self._add("Resumen y Abstract", "Alineación Título RESUMEN", "error",
                      "El título 'RESUMEN' debe estar centrado.",
                      "Centrado", self._align_display(align), p_idx=idx, p_text=txt)

        if not bold:
            self._add("Resumen y Abstract", "Negrita Título RESUMEN", "error",
                      "El título 'RESUMEN' debe estar en negrita.",
                      "Negrita", "Normal", p_idx=idx, p_text=txt)

        if line_spacing and abs(line_spacing - 2.0) > 0.2:
            self._add("Resumen y Abstract", "Interlineado Título RESUMEN", "error",
                      "El título 'RESUMEN' debe tener interlineado 2.0.",
                      "2.0", str(line_spacing), p_idx=idx, p_text=txt)

        if s_before > 1.0:
            self._add("Resumen y Abstract", "Espaciado Anterior Título RESUMEN", "error",
                      "El título 'RESUMEN' debe tener espaciado anterior 0pt.",
                      "0pt", f"{s_before}pt", p_idx=idx, p_text=txt)

        if abs(s_after - 10.0) > 1.0:
            self._add("Resumen y Abstract", "Espaciado Posterior Título RESUMEN", "error",
                      "El título 'RESUMEN' debe tener espaciado posterior 10pt.",
                      "10pt", f"{s_after}pt", p_idx=idx, p_text=txt)

        if l_cm > 0.1:
            self._add("Resumen y Abstract", "Sangría Título RESUMEN", "error",
                      "El título 'RESUMEN' no debe tener sangría.",
                      "Sin sangría (0cm)", f"Izq {l_cm}cm", p_idx=idx, p_text=txt)

    # ── Validación del contenido del resumen ──────────────────────────────

    def _audit_content_paragraph(self, idx, p):
        txt = p["text"].strip()
        if len(txt) < 30:
            return  # No validar líneas muy cortas

        size, bold, italic, font = self._get_p_props(p)
        align = p.get("alignment", "left")
        line_spacing = p.get("line_spacing")
        l_cm = round((p.get("indent_left") or 0) / 567.0, 2)
        f_cm = round((p.get("indent_first") or 0) / 567.0, 2)
        s_before = p.get("spacing_before", 0)
        s_after = p.get("spacing_after", 0)

        if abs(size - 12) > 0.5:
            self._add("Resumen y Abstract", "Tamaño Contenido Resumen", "error",
                      "El contenido del resumen debe ser de 12pt.",
                      "12pt", f"{size}pt", p_idx=idx, p_text=txt[:40])

        if align != 'both':
            self._add("Resumen y Abstract", "Alineación Contenido Resumen", "error",
                      "El contenido del resumen debe estar justificado.",
                      "Justificada", self._align_display(align), p_idx=idx, p_text=txt[:40])

        if line_spacing and abs(line_spacing - 2.0) > 0.2:
            self._add("Resumen y Abstract", "Interlineado Contenido Resumen", "error",
                      "El contenido del resumen debe tener interlineado 2.0.",
                      "2.0", str(line_spacing), p_idx=idx, p_text=txt[:40])

        if bold:
            self._add("Resumen y Abstract", "Estilo Contenido Resumen", "warning",
                      "El contenido del resumen debe estar en estilo Normal (sin negrita).",
                      "Normal", "Negrita", p_idx=idx, p_text=txt[:40])

        if l_cm > 0.1 or f_cm > 0.1:
            self._add("Resumen y Abstract", "Sangría Contenido Resumen", "error",
                      "El contenido del resumen NO debe tener sangría de ningún tipo.",
                      "Izq 0cm, Prim 0cm",
                      f"Izq {l_cm}cm, Prim {f_cm}cm", p_idx=idx, p_text=txt[:40])

        if s_before > 1.0:
            self._add("Resumen y Abstract", "Espaciado Anterior Contenido Resumen", "warning",
                      "El contenido del resumen debe tener espaciado anterior 0pt.",
                      "0pt", f"{s_before}pt", p_idx=idx, p_text=txt[:40])

    # ── Validación de "Palabras clave:" ───────────────────────────────────

    def _audit_keywords(self, idx, p):
        txt = p["text"].strip()

        # 1. Formato exacto "Palabras clave:" (P mayúscula, resto minúsculas)
        if not txt.startswith("Palabras clave:"):
            self._add(
                "Resumen y Abstract",
                "Formato Palabras Clave",
                "error",
                "Debe empezar exactamente con 'Palabras clave:' (P mayúscula, resto en minúsculas, "
                "seguido de dos puntos).",
                "Palabras clave:",
                txt[:30],
                p_idx=idx,
                p_text=txt,
            )

        # 2. "Palabras clave:" en NEGRITA (primeros 16 caracteres)
        label = "Palabras clave:"
        label_bold_ok = self._check_prefix_bold(p, len(label))
        if not label_bold_ok:
            self._add(
                "Resumen y Abstract",
                "Negrita Etiqueta Palabras Clave",
                "error",
                "La etiqueta 'Palabras clave:' debe estar en NEGRITA.",
                "Negrita",
                "Normal",
                p_idx=idx,
                p_text=txt,
            )

        # 3. Extraer lista de palabras clave después de ":"
        if ":" in txt:
            keywords_part_raw = txt.split(":", 1)[1].strip()
            # Validar punto final obligatorio
            if not keywords_part_raw.endswith("."):
                self._add(
                    "Resumen y Abstract",
                    "Punto Final Palabras Clave",
                    "error",
                    "La lista de palabras clave debe terminar con un punto (.) al final.",
                    "Terminar con punto",
                    "Sin punto final",
                    p_idx=idx,
                    p_text=txt,
                )

            keywords_part = keywords_part_raw.rstrip(".")
            keywords = [k.strip() for k in keywords_part.split(",") if k.strip()]

            # Validar que esté separado por comas (mínimo 2 palabras)
            if len(keywords) < 2:
                self._add(
                    "Resumen y Abstract",
                    "Separación Palabras Clave",
                    "error",
                    "Las palabras clave deben estar separadas por comas (,). "
                    "Se requieren al menos 2 palabras clave.",
                    "Separadas por comas, mínimo 2",
                    f"{len(keywords)} elemento(s)",
                    p_idx=idx,
                    p_text=txt,
                )
                return

            # 4. Validar MAYÚSCULA inicial y minúsculas en el resto
            bad_first = []   # primera letra no es mayúscula
            bad_rest = []    # resto no es minúscula
            for kw in keywords:
                if not kw:
                    continue
                if not kw[0].isupper():
                    bad_first.append(kw)
                elif len(kw) > 1 and not kw[1:].islower():
                    bad_rest.append(kw)

            if bad_first:
                self._add(
                    "Resumen y Abstract",
                    "Capitalización Palabras Clave",
                    "warning",
                    f"Las siguientes palabras clave deben iniciar con MAYÚSCULA: "
                    f"{' | '.join(bad_first[:5])}{'...' if len(bad_first) > 5 else ''}.",
                    "Mayúscula inicial",
                    f"{len(bad_first)} palabra(s) sin mayúscula inicial",
                    p_idx=idx,
                    p_text=txt,
                )

            if bad_rest:
                self._add(
                    "Resumen y Abstract",
                    "Minúsculas en Palabras Clave",
                    "warning",
                    f"Solo la primera letra debe ser mayúscula; el resto en minúsculas: "
                    f"{' | '.join(bad_rest[:5])}{'...' if len(bad_rest) > 5 else ''}.",
                    "Resto en minúsculas",
                    f"{len(bad_rest)} palabra(s) con mayúsculas internas",
                    p_idx=idx,
                    p_text=txt,
                )

            # 5. Validar ORDEN ALFABÉTICO
            sorted_kw = sorted(keywords, key=lambda x: x.lower())
            if keywords != sorted_kw:
                self._add(
                    "Resumen y Abstract",
                    "Orden Alfabético Palabras Clave",
                    "warning",
                    "Las palabras clave deben estar ordenadas alfabéticamente.",
                    " → ".join(sorted_kw[:5]),
                    " → ".join(keywords[:5]),
                    p_idx=idx,
                    p_text=txt,
                )

    def _check_prefix_bold(self, p, prefix_len):
        accumulated = 0
        for r in p.get("runs", []):
            r_txt = r["text"]
            if not r_txt:
                continue
            for _ in r_txt:
                if accumulated < prefix_len:
                    if not r.get("bold"):
                        return False
                    accumulated += 1
                else:
                    return True
        return accumulated >= prefix_len
