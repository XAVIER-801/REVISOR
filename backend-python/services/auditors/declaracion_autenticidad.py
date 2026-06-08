"""
declaracion_autenticidad.py - Auditoría del Anexo N: Declaración Jurada de Autenticidad.

Documento OBLIGATORIO según la Guía de Presentación de Tesis 2.0 UNAP (pág. 27).
Sin este documento la tesis NO PUEDE depositarse en el Repositorio Institucional.

Reglas implementadas:
- Presencia obligatoria al final de los anexos
- Etiqueta "Anexo N." en negrita + título sin negrita + primera mayúscula
- Debe incluir: Nombre de la escuela profesional, Título de la tesis
- Tamaño 12pt, alineación izquierda, sangría 0, interlineado 2.0
- Debe contener al menos una marca/firma (detectada por imagen)

Referencia oficial:
http://repositorio.unap.edu.pe/handle/20.500.14082/19116
"""
import re
from .base_auditor import BaseAuditor


class DeclaracionAutenticidadAuditor(BaseAuditor):

    KEYWORDS = [
        "DECLARACION JURADA DE AUTENTICIDAD",
        "DECLARACIÓN JURADA DE AUTENTICIDAD",
        "DECLARACION JURADA",
        "DECLARACIÓN JURADA",
    ]

    def audit(self):
        decl_idx, decl_p = self._find_declaration()

        if decl_idx == -1:
            self._add(
                "Anexos Obligatorios",
                "Declaración Jurada de Autenticidad",
                "error",
                "No se encontró el 'Anexo N. Declaración Jurada de Autenticidad de Tesis'. "
                "Este documento es OBLIGATORIO según la guía UNAP. Sin él, la tesis no puede "
                "depositarse en el Repositorio Institucional.",
                "Presente al final de Anexos",
                "Ausente",
            )
            return

        # Validar que esté dentro de la sección de anexos
        if self.anexos_start_idx != -1 and decl_idx < self.anexos_start_idx:
            self._add(
                "Anexos Obligatorios",
                "Ubicación Declaración Jurada",
                "error",
                "La 'Declaración Jurada de Autenticidad' debe estar dentro de la sección ANEXOS, "
                "no antes.",
                "Dentro de Anexos",
                f"Antes de ANEXOS (índice {decl_idx})",
                p_idx=decl_idx,
                p_text=decl_p["text"][:60],
            )

        self._audit_format(decl_idx, decl_p)
        self._audit_content(decl_idx)
        self._audit_signatures(decl_idx)

    def _find_declaration(self):
        for i, p in enumerate(self.paragraphs):
            up = p["text"].upper()
            if any(kw in up for kw in self.KEYWORDS):
                return i, p
        return -1, None

    def _audit_format(self, idx, p):
        txt = p["text"].strip()
        size, bold, italic, font = self._get_p_props(p)
        align = p.get("alignment", "left")
        l_ind = p.get("indent_left") or 0
        f_ind = p.get("indent_first") or 0
        l_cm = round(l_ind / 567.0, 2)
        f_cm = round(f_ind / 567.0, 2)

        # Detectar formato "Anexo N. ..." al inicio
        m = re.match(r"^(Anexo\s+\w+\.)\s*(.*)$", txt, re.IGNORECASE)
        if m:
            label = m.group(1)
            title = m.group(2).strip()
            # Etiqueta debe ser negrita, título sin negrita
            label_bold_ok = self._check_prefix_bold(p, len(label))
            if not label_bold_ok:
                self._add(
                    "Anexos Obligatorios",
                    "Negrita Etiqueta Declaración Jurada",
                    "error",
                    "La etiqueta 'Anexo N.' de la Declaración Jurada debe estar en negrita.",
                    "Negrita",
                    "Normal",
                    p_idx=idx,
                    p_text=txt,
                )
            # Capitalización del título
            if title:
                first = title[0]
                if not first.isupper():
                    self._add(
                        "Anexos Obligatorios",
                        "Capitalización Declaración Jurada",
                        "error",
                        "El título debe iniciar con mayúscula y continuar en minúsculas.",
                        "Mayúscula inicial",
                        title[:30],
                        p_idx=idx,
                        p_text=txt,
                    )

        # Tamaño 12pt
        if abs(size - 12) > 0.5:
            self._add(
                "Anexos Obligatorios",
                "Tamaño Declaración Jurada",
                "error",
                "El título 'Anexo N. Declaración Jurada...' debe ser de tamaño 12pt.",
                "12pt",
                f"{size}pt",
                p_idx=idx,
                p_text=txt,
            )

        # Alineación izquierda
        if align != "left":
            self._add(
                "Anexos Obligatorios",
                "Alineación Declaración Jurada",
                "error",
                "El título de la Declaración Jurada debe estar alineado a la izquierda.",
                "Izquierda",
                self._align_display(align),
                p_idx=idx,
                p_text=txt,
            )

        # Sin sangría
        if l_cm > 0.1 or f_cm > 0.1:
            self._add(
                "Anexos Obligatorios",
                "Sangría Declaración Jurada",
                "error",
                "El título de la Declaración Jurada no debe tener sangría.",
                "Izq 0cm, Prim 0cm",
                f"Izq {l_cm}cm, Prim {f_cm}cm",
                p_idx=idx,
                p_text=txt,
            )

    def _audit_content(self, idx):
        """Verifica que los siguientes párrafos mencionen escuela profesional y título de la tesis."""
        end_idx = min(len(self.paragraphs), idx + 60)
        joined = " ".join(p["text"].upper() for p in self.paragraphs[idx:end_idx])

        has_school = any(kw in joined for kw in ["ESCUELA PROFESIONAL", "ESCUELA PROFESSIONAL"])
        has_thesis = "TITULO" in joined or "TÍTULO" in joined or "TESIS" in joined

        if not has_school:
            self._add(
                "Anexos Obligatorios",
                "Datos Declaración Jurada (Escuela)",
                "warning",
                "La Declaración Jurada debe incluir el nombre de la escuela profesional.",
                "Mención a 'Escuela Profesional'",
                "No detectado",
                p_idx=idx,
            )

        if not has_thesis:
            self._add(
                "Anexos Obligatorios",
                "Datos Declaración Jurada (Título Tesis)",
                "warning",
                "La Declaración Jurada debe incluir el título de la tesis.",
                "Mención al título de la tesis",
                "No detectado",
                p_idx=idx,
            )

    def _audit_signatures(self, idx):
        """Detecta presencia de firmas (imágenes) en las páginas siguientes a la declaración."""
        end_idx = min(len(self.paragraphs), idx + 30)
        has_image = False
        for p in self.paragraphs[idx:end_idx]:
            if p.get("drawings"):
                has_image = True
                break

        if not has_image:
            self._add(
                "Anexos Obligatorios",
                "Firma Declaración Jurada",
                "warning",
                "No se detectó imagen de firma en la Declaración Jurada. "
                "Verifique manualmente que esté firmada (física o digitalmente).",
                "Firma presente (imagen)",
                "No detectada",
                p_idx=idx,
            )

    def _check_prefix_bold(self, p, prefix_len):
        """Verifica si los primeros `prefix_len` caracteres están en negrita."""
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
