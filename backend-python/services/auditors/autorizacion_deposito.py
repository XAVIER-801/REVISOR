"""
autorizacion_deposito.py - Auditoría del Anexo N: Autorización para el Depósito.

Documento OBLIGATORIO según la Guía de Presentación de Tesis 2.0 UNAP (pág. 28).
Sin este documento la tesis NO PUEDE depositarse en el Repositorio Institucional.

Reglas implementadas:
- Presencia obligatoria al final de los anexos
- Etiqueta "Anexo N." en negrita + título sin negrita + primera mayúscula
- Debe incluir: Nombre de la escuela profesional, Título de la tesis
- Marcas de autorización (3 opciones según la guía)
- Información de licencia Creative Commons
- Tamaño 12pt, alineación izquierda, sangría 0, interlineado 2.0

Referencia oficial:
http://repositorio.unap.edu.pe/handle/20.500.14082/19116
"""
import re
from .base_auditor import BaseAuditor


class AutorizacionDepositoAuditor(BaseAuditor):

    KEYWORDS = [
        "AUTORIZACION PARA EL DEPOSITO",
        "AUTORIZACIÓN PARA EL DEPÓSITO",
        "AUTORIZACION PARA EL DEPÓSITO",
        "AUTORIZACIÓN PARA EL DEPOSITO",
        "AUTORIZACION DE DEPOSITO",
        "AUTORIZACIÓN DE DEPÓSITO",
    ]

    def audit(self):
        auth_idx, auth_p = self._find_authorization()

        if auth_idx == -1:
            self._add(
                "Anexos Obligatorios",
                "Autorización para el Depósito",
                "error",
                "No se encontró el 'Anexo N. Autorización para el Depósito de Tesis en el "
                "Repositorio Institucional'. Este documento es OBLIGATORIO según la guía UNAP. "
                "Sin él, la tesis no puede depositarse.",
                "Presente al final de Anexos",
                "Ausente",
            )
            return

        # Validar que esté dentro de la sección de anexos
        if self.anexos_start_idx != -1 and auth_idx < self.anexos_start_idx:
            self._add(
                "Anexos Obligatorios",
                "Ubicación Autorización Depósito",
                "error",
                "La 'Autorización para el Depósito' debe estar dentro de la sección ANEXOS, "
                "no antes.",
                "Dentro de Anexos",
                f"Antes de ANEXOS (índice {auth_idx})",
                p_idx=auth_idx,
                p_text=auth_p["text"][:60],
            )

        self._audit_format(auth_idx, auth_p)
        self._audit_content(auth_idx)
        self._audit_signatures(auth_idx)
        self._audit_order_after_declaration(auth_idx)

    def _find_authorization(self):
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
            # Etiqueta debe ser negrita
            label_bold_ok = self._check_prefix_bold(p, len(label))
            if not label_bold_ok:
                self._add(
                    "Anexos Obligatorios",
                    "Negrita Etiqueta Autorización",
                    "error",
                    "La etiqueta 'Anexo N.' de la Autorización debe estar en negrita.",
                    "Negrita",
                    "Normal",
                    p_idx=idx,
                    p_text=txt,
                )

        if abs(size - 12) > 0.5:
            self._add(
                "Anexos Obligatorios",
                "Tamaño Autorización Depósito",
                "error",
                "El título 'Anexo N. Autorización para el Depósito...' debe ser de tamaño 12pt.",
                "12pt",
                f"{size}pt",
                p_idx=idx,
                p_text=txt,
            )

        if align != "left":
            self._add(
                "Anexos Obligatorios",
                "Alineación Autorización Depósito",
                "error",
                "El título de la Autorización debe estar alineado a la izquierda.",
                "Izquierda",
                self._align_display(align),
                p_idx=idx,
                p_text=txt,
            )

        if l_cm > 0.1 or f_cm > 0.1:
            self._add(
                "Anexos Obligatorios",
                "Sangría Autorización Depósito",
                "error",
                "El título de la Autorización no debe tener sangría.",
                "Izq 0cm, Prim 0cm",
                f"Izq {l_cm}cm, Prim {f_cm}cm",
                p_idx=idx,
                p_text=txt,
            )

    def _audit_content(self, idx):
        """Verifica menciones a escuela, título y licencia Creative Commons."""
        end_idx = min(len(self.paragraphs), idx + 60)
        joined = " ".join(p["text"].upper() for p in self.paragraphs[idx:end_idx])

        has_school = "ESCUELA PROFESIONAL" in joined
        has_thesis = "TITULO" in joined or "TÍTULO" in joined or "TESIS" in joined
        has_license = (
            "CREATIVE COMMONS" in joined
            or "LICENCIA" in joined
            or "ATRIBUCIÓN" in joined
            or "ATRIBUCION" in joined
            or "NO COMERCIAL" in joined
        )

        if not has_school:
            self._add(
                "Anexos Obligatorios",
                "Datos Autorización (Escuela)",
                "warning",
                "La Autorización debe incluir el nombre de la escuela profesional.",
                "Mención a 'Escuela Profesional'",
                "No detectado",
                p_idx=idx,
            )

        if not has_thesis:
            self._add(
                "Anexos Obligatorios",
                "Datos Autorización (Título Tesis)",
                "warning",
                "La Autorización debe incluir el título de la tesis.",
                "Mención al título de la tesis",
                "No detectado",
                p_idx=idx,
            )

        if not has_license:
            self._add(
                "Anexos Obligatorios",
                "Licencia Creative Commons",
                "warning",
                "La Autorización debe incluir información sobre la licencia Creative Commons "
                "(Atribución No Comercial Compartir Igual).",
                "Licencia Creative Commons mencionada",
                "No detectada",
                p_idx=idx,
            )

    def _audit_signatures(self, idx):
        end_idx = min(len(self.paragraphs), idx + 30)
        has_image = False
        for p in self.paragraphs[idx:end_idx]:
            if p.get("drawings"):
                has_image = True
                break

        if not has_image:
            self._add(
                "Anexos Obligatorios",
                "Firma Autorización Depósito",
                "warning",
                "No se detectó imagen de firma en la Autorización de Depósito. "
                "Verifique manualmente que esté firmada.",
                "Firma presente (imagen)",
                "No detectada",
                p_idx=idx,
            )

    def _audit_order_after_declaration(self, auth_idx):
        """La Autorización debe ir después de la Declaración Jurada (último anexo)."""
        decl_idx = -1
        for i, p in enumerate(self.paragraphs):
            up = p["text"].upper()
            if "DECLARACION JURADA" in up or "DECLARACIÓN JURADA" in up:
                decl_idx = i
                break

        if decl_idx != -1 and auth_idx < decl_idx:
            self._add(
                "Anexos Obligatorios",
                "Orden Anexos Obligatorios",
                "warning",
                "La Autorización para el Depósito debería ir DESPUÉS de la Declaración Jurada "
                "(orden: Declaración → Autorización al final del documento).",
                "Declaración → Autorización",
                "Autorización antes que Declaración",
                p_idx=auth_idx,
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
