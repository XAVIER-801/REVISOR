"""
cuadros_texto.py - Detección de cuadros de texto (text boxes) en el cuerpo.

Algunos estudiantes meten texto dentro de cuadros de texto (text boxes) para que
herramientas como Turnitin no detecten el contenido. Esta práctica:
- NO es aceptable académicamente
- Rompe la accesibilidad del documento
- Puede ocultar plagio
- Impide validar formato (interlineado, sangrías, etc.) del texto interno

Regla (sugerencia firme): todo texto debe estar como párrafos normales, no en
text boxes. El sistema marca todos los text boxes encontrados con sugerencia de
transcribir el contenido a párrafos regulares.
"""
from .base_auditor import BaseAuditor


class CuadrosTextoAuditor(BaseAuditor):

    def audit(self):
        textboxes_found = 0
        for i, p in enumerate(self.paragraphs):
            if not p.get("has_textbox"):
                continue
            # Saltar portada (logo institucional puede tener algunos elementos)
            if p.get("is_cover"):
                continue

            textbox_text = p.get("textbox_text") or ""
            preview = textbox_text[:80] + ("..." if len(textbox_text) > 80 else "")
            section = p.get("section") or "General"

            textboxes_found += 1
            self._add(
                "Cuadros de Texto",
                f"Texto en cuadro de texto: {preview[:30]}",
                "warning",
                f"Se detectó texto dentro de un CUADRO DE TEXTO (text box) en la "
                f"sección '{section}'. El uso de cuadros de texto para colocar "
                f"contenido textual NO ESTÁ ACEPTADO en la tesis porque: (1) "
                f"herramientas de similitud como Turnitin pueden no procesar este "
                f"contenido correctamente, (2) rompe la estructura semántica del "
                f"documento, (3) impide validar formato (interlineado, sangrías, "
                f"justificación). DEBE TRANSCRIBIR este contenido como párrafos "
                f"normales del documento.\n\n"
                f"Texto detectado: \"{preview}\"",
                "Texto en párrafos normales del cuerpo del documento",
                "Texto dentro de cuadro de texto",
                p_idx=p["index"],
                p_text=p["text"][:60] or "[Cuadro de texto]",
            )

        if textboxes_found > 0:
            # Resumen final
            self._add(
                "Cuadros de Texto",
                f"Resumen: {textboxes_found} cuadros de texto en el documento",
                "warning",
                f"Total de {textboxes_found} cuadros de texto detectados. Revise "
                f"cada uno y transcriba su contenido a párrafos normales para "
                f"asegurar la integridad del documento y la verificación de "
                f"originalidad.",
                "0 cuadros de texto",
                f"{textboxes_found} cuadros de texto",
            )
