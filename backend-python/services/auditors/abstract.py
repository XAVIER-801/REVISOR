"""
abstract.py - Auditoría de la sección de ABSTRACT (Inglés).

Reglas implementadas (Guía UNAP pág. 17):
- Título 'ABSTRACT' a 16pt, centrado, negrita
- Contenido: 12pt, justificado, normal, interlineado 2.0, sin sangría
- Extensión: entre 250 y 300 palabras
- "Keywords:" en NEGRITA, primera letra MAYÚSCULA
- Keywords separadas por comas y ordenadas ALFABÉTICAMENTE
"""
import re
from .base_auditor import BaseAuditor


class AbstractAuditor(BaseAuditor):

    def audit(self):
        content = []
        content_paragraphs = []
        capture = False
        abstract_p_idx = -1

        for i, p in enumerate(self.paragraphs):
            # Skip index zone and index entries to avoid matching the index page's "ABSTRACT"
            if self.last_index_idx != -1 and i <= self.last_index_idx:
                continue
            
            txt = p["text"]
            if "\t" in txt or "...." in txt or bool(re.search(r"\d+$", txt.strip())):
                continue

            norm = p["norm"]
            if norm == "ABSTRACT" and abstract_p_idx == -1:
                abstract_p_idx = i
                capture = True
                self._audit_title(i, p)
                continue
            if ("KEYWORDS" in norm or "KEY WORDS" in norm) and capture:
                capture = False
                self._audit_keywords(i, p)
                break
            if capture:
                # Guard: stop capturing if we hit another major section
                _OTHER_SECTIONS = {
                    "RESUMEN", "INTRODUCCION", "INDICE GENERAL",
                    "INDICE DE TABLAS", "INDICE DE FIGURAS",
                    "INDICE DE CUADROS", "INDICE DE ILUSTRACIONES",
                    "DEDICATORIA", "AGRADECIMIENTOS", "CONCLUSIONES",
                    "RECOMENDACIONES", "REFERENCIAS BIBLIOGRAFICAS",
                    "ANEXOS", "DECLARACION JURADA",
                    "AUTORIZACION PARA EL DEPOSITO", "ACRONIMOS",
                }
                if norm in _OTHER_SECTIONS or (p.get("is_heading") and norm != "ABSTRACT"):
                    capture = False
                    break
                if p["text"].strip():
                    content.append(p["text"])
                    content_paragraphs.append((i, p))

        if content:
            full_text = " ".join(content)
            words = len(full_text.split())
            ok_words = words <= 300
            self._add(
                "Resumen y Abstract",
                "Extensión del Abstract",
                "passed" if ok_words else "error",
                f"El abstract no debe superar las 300 palabras. Hallado: {words} palabras.",
                "Máximo 300 palabras",
                f"{words} palabras",
                p_idx=abstract_p_idx if abstract_p_idx != -1 else None,
            )

        for i, p in content_paragraphs:
            self._audit_content_paragraph(i, p)

    def _audit_title(self, idx, p):
        txt = p["text"].strip()
        size, bold, italic, font = self._get_p_props(p)
        align = p.get("alignment", "left")
        line_spacing = p.get("line_spacing")
        s_before = p.get("spacing_before", 0)
        s_after = p.get("spacing_after", 0)
        l_cm = round((p.get("indent_left") or 0) / 567.0, 2)

        if abs(size - 16) > 0.5:
            self._add("Resumen y Abstract", "Tamaño Título ABSTRACT", "error",
                      "El título 'ABSTRACT' debe ser de 16pt.",
                      "16pt", f"{size}pt", p_idx=idx, p_text=txt)
        if align != "center":
            self._add("Resumen y Abstract", "Alineación Título ABSTRACT", "error",
                      "El título 'ABSTRACT' debe estar centrado.",
                      "Centrado", align, p_idx=idx, p_text=txt)
        if not bold:
            self._add("Resumen y Abstract", "Negrita Título ABSTRACT", "error",
                      "El título 'ABSTRACT' debe estar en negrita.",
                      "Negrita", "Normal", p_idx=idx, p_text=txt)
        if line_spacing and abs(line_spacing - 2.0) > 0.2:
            self._add("Resumen y Abstract", "Interlineado Título ABSTRACT", "error",
                      "El título 'ABSTRACT' debe tener interlineado 2.0.",
                      "2.0", str(line_spacing), p_idx=idx, p_text=txt)
        if abs(s_after - 10.0) > 1.0:
            self._add("Resumen y Abstract", "Espaciado Posterior Título ABSTRACT", "error",
                      "El título 'ABSTRACT' debe tener espaciado posterior 10pt.",
                      "10pt", f"{s_after}pt", p_idx=idx, p_text=txt)
        if l_cm > 0.1:
            self._add("Resumen y Abstract", "Sangría Título ABSTRACT", "error",
                      "El título 'ABSTRACT' no debe tener sangría.",
                      "Sin sangría (0cm)", f"Izq {l_cm}cm", p_idx=idx, p_text=txt)

    def _audit_content_paragraph(self, idx, p):
        txt = p["text"].strip()
        if len(txt) < 30:
            return
        size, bold, italic, font = self._get_p_props(p)
        align = p.get("alignment", "left")
        line_spacing = p.get("line_spacing")
        l_cm = round((p.get("indent_left") or 0) / 567.0, 2)
        f_cm = round((p.get("indent_first") or 0) / 567.0, 2)

        if abs(size - 12) > 0.5:
            self._add("Resumen y Abstract", "Tamaño Contenido Abstract", "error",
                      "El contenido del abstract debe ser de 12pt.",
                      "12pt", f"{size}pt", p_idx=idx, p_text=txt[:40])
        if align not in ("both", "justify"):
            self._add("Resumen y Abstract", "Alineación Contenido Abstract", "error",
                      "El contenido del abstract debe estar justificado.",
                      "Justificada", align, p_idx=idx, p_text=txt[:40])
        if line_spacing and abs(line_spacing - 2.0) > 0.2:
            self._add("Resumen y Abstract", "Interlineado Contenido Abstract", "error",
                      "El contenido del abstract debe tener interlineado 2.0.",
                      "2.0", str(line_spacing), p_idx=idx, p_text=txt[:40])
        if bold:
            self._add("Resumen y Abstract", "Estilo Contenido Abstract", "warning",
                      "El contenido del abstract debe estar en estilo Normal (sin negrita).",
                      "Normal", "Negrita", p_idx=idx, p_text=txt[:40])
        if l_cm > 0.1 or f_cm > 0.1:
            self._add("Resumen y Abstract", "Sangría Contenido Abstract", "error",
                      "El contenido del abstract NO debe tener sangría de ningún tipo.",
                      "Izq 0cm, Prim 0cm",
                      f"Izq {l_cm}cm, Prim {f_cm}cm", p_idx=idx, p_text=txt[:40])

    def _audit_keywords(self, idx, p):
        txt = p["text"].strip()

        if not txt.startswith("Keywords:"):
            self._add(
                "Resumen y Abstract",
                "Formato Keywords",
                "error",
                "Debe empezar exactamente con 'Keywords:' (K mayúscula, resto minúsculas, dos puntos).",
                "Keywords:",
                txt[:30],
                p_idx=idx,
                p_text=txt,
            )

        label = "Keywords:"
        if not self._check_prefix_bold(p, len(label)):
            self._add(
                "Resumen y Abstract",
                "Negrita Etiqueta Keywords",
                "error",
                "La etiqueta 'Keywords:' debe estar en NEGRITA.",
                "Negrita",
                "Normal",
                p_idx=idx,
                p_text=txt,
            )

        if ":" in txt:
            keywords_part = txt.split(":", 1)[1].strip().rstrip(".")
            keywords = [k.strip() for k in keywords_part.split(",") if k.strip()]

            if len(keywords) < 2:
                self._add(
                    "Resumen y Abstract",
                    "Separación Keywords",
                    "error",
                    "Las keywords deben estar separadas por comas (,). Mínimo 2.",
                    "Separadas por comas, mínimo 2",
                    f"{len(keywords)} elemento(s)",
                    p_idx=idx,
                    p_text=txt,
                )
                return

            for kw in keywords:
                if not kw:
                    continue
                if not kw[0].isupper():
                    self._add(
                        "Resumen y Abstract",
                        f"Capitalización keyword: {kw[:20]}",
                        "warning",
                        "Cada keyword debe iniciar con mayúscula y continuar en minúsculas.",
                        "Mayúscula inicial",
                        kw,
                        p_idx=idx,
                        p_text=txt,
                    )

            sorted_kw = sorted(keywords, key=lambda x: x.lower())
            if keywords != sorted_kw:
                self._add(
                    "Resumen y Abstract",
                    "Orden Alfabético Keywords",
                    "warning",
                    "Las keywords deben estar ordenadas alfabéticamente.",
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
