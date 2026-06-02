"""
configuracion_pagina.py - Auditoría de Configuración General de Página y Márgenes.

Reglas implementadas:
- Tamaño de papel: A4
- Márgenes: Superior 2.5cm, Inferior 2.5cm, Derecho 2.5cm, Izquierdo 3.5cm
- Sangría de Primera Línea general (muestreo)
- Alineación Justificada general (muestreo)
- Interlineado 2.0 general (muestreo)
- Fuente Times New Roman global (muestreo)
- Secciones obligatorias presentes
"""
import re
from .base_auditor import BaseAuditor


class ConfiguracionPaginaAuditor(BaseAuditor):

    def audit(self):
        # Márgenes y papel
        sp = self.resolver.section_props
        paper = sp.get('paper', 'Unknown')
        ok_paper = paper in ('A4', 'A4-landscape')
        self._add("Configuración de Página", "Tamaño de Papel", "passed" if ok_paper else "error",
                  "El papel debe ser A4.", "A4", paper)

        # Validar márgenes de la sección principal (portrait)
        margins = [
            ('Superior', sp.get('margin_top'), 2.5),
            ('Inferior', sp.get('margin_bottom'), 2.5),
            ('Derecho', sp.get('margin_right'), 2.5),
            ('Izquierdo', sp.get('margin_left'), 3.5)
        ]
        for name, actual, expected in margins:
            ok = abs((actual or 0) - expected) < 0.1
            self._add("Configuración de Página", f"Margen {name}", "passed" if ok else "error",
                      f"Margen {name} debe ser {expected} cm.", f"{expected} cm", f"{actual} cm")

        # ═══ VALIDACIÓN DE SECCIONES HORIZONTALES (LANDSCAPE) ═══
        # En orientación landscape, los márgenes deben mantenerse físicamente
        # equivalentes a portrait:
        #   - El margen "izquierdo" del XML aparece visualmente ARRIBA → debe ser 3.5cm
        #   - El margen "superior" del XML aparece visualmente a la DERECHA → 2.5cm
        #   - El margen "derecho" del XML aparece visualmente ABAJO → 2.5cm
        #   - El margen "inferior" del XML aparece visualmente a la IZQUIERDA → 2.5cm
        # Es decir, el margen izquierdo (3.5cm) se conserva físicamente en el lado
        # de encuadernación, que en landscape es la parte SUPERIOR.
        sections = sp.get('sections', [])
        landscape_sections = [s for s in sections if s.get('is_landscape')]
        if landscape_sections:
            for idx, ls_sect in enumerate(landscape_sections):
                # En landscape, el margen XML que aparece visualmente arriba sigue
                # siendo el "left" del XML (3.5cm esperado para encuadernación).
                ls_left = ls_sect.get('margin_left', 0)
                ls_top = ls_sect.get('margin_top', 0)
                ls_right = ls_sect.get('margin_right', 0)
                ls_bottom = ls_sect.get('margin_bottom', 0)

                ok_left = abs(ls_left - 3.5) < 0.1
                ok_top = abs(ls_top - 2.5) < 0.1
                ok_right = abs(ls_right - 2.5) < 0.1
                ok_bottom = abs(ls_bottom - 2.5) < 0.1

                section_label = f"Sección horizontal #{idx + 1}"
                if ok_left and ok_top and ok_right and ok_bottom:
                    self._add(
                        "Configuración de Página",
                        f"Márgenes {section_label}",
                        "passed",
                        f"La {section_label} en orientación horizontal mantiene los márgenes "
                        f"correctos: 3.5cm en el lado de encuadernación (visualmente arriba).",
                        "Izq XML 3.5cm (arriba visualmente), resto 2.5cm",
                        "Cumple",
                    )
                else:
                    detalles = []
                    if not ok_left:
                        detalles.append(f"Izq XML {ls_left}cm (debería 3.5cm)")
                    if not ok_top:
                        detalles.append(f"Sup XML {ls_top}cm (debería 2.5cm)")
                    if not ok_right:
                        detalles.append(f"Der XML {ls_right}cm (debería 2.5cm)")
                    if not ok_bottom:
                        detalles.append(f"Inf XML {ls_bottom}cm (debería 2.5cm)")
                    self._add(
                        "Configuración de Página",
                        f"Márgenes {section_label}",
                        "error",
                        f"La {section_label} en orientación horizontal debe mantener "
                        f"3.5cm en el lado de encuadernación (que aparece visualmente arriba "
                        f"cuando la página rota a horizontal) y 2.5cm en los otros tres lados.",
                        "Izq XML 3.5cm, resto 2.5cm",
                        ", ".join(detalles),
                    )

        # Muestreo de formato global
        sample = [p for p in self.paragraphs if len(p['text']) > 150 and not p.get('in_table') and not p.get('is_cover')][:30]
        if sample:
            indent_ok = sum(1 for p in sample if (p.get('indent_first') or 0) >= 700)
            justified_ok = sum(1 for p in sample if p.get('alignment') == 'both')
            spacing_ok = sum(1 for p in sample if (p.get('line_spacing') or 0) >= 1.5)

            font_count = 0
            for p in sample:
                _, _, _, font = self._get_p_props(p)
                if font and "times" in font.lower():
                    font_count += 1
            font_ok = font_count > len(sample) * 0.6

            self._add("Configuración de Página", "Sangría de Primera Línea", "passed" if indent_ok > len(sample)*0.6 else "error",
                      "Los párrafos deben tener sangría de 1.25 cm.", "1.25 cm", f"{indent_ok}/{len(sample)} detectados")
            self._add("Configuración de Página", "Alineación Justificada", "passed" if justified_ok > len(sample)*0.6 else "error",
                      "El cuerpo del texto debe estar justificado.", "Justificado", f"{justified_ok}/{len(sample)} detectados")
            self._add("Configuración de Página", "Interlineado 2.0", "passed" if spacing_ok > len(sample)*0.6 else "error",
                      "El documento debe tener interlineado doble (2.0).", "2.0", f"{spacing_ok}/{len(sample)} detectados")
            self._add("Configuración de Página", "Fuente Global", "passed" if font_ok else "error",
                      "El documento completo debe estar escrito en la fuente Times New Roman.", "Times New Roman", f"Times New Roman en {font_count}/{len(sample)} párrafos")

        # Verificar secciones obligatorias
        mandatory = ["INDICE GENERAL", "RESUMEN", "ABSTRACT", "INTRODUCCION", "CONCLUSIONES", "REFERENCIAS BIBLIOGRAFICAS", "DECLARACION JURADA", "AUTORIZACION PARA EL DEPOSITO"]
        for m in mandatory:
            found = any(m in s for s in self.sections_found)
            self._add("Configuración de Página", f"Sección: {m}", "passed" if found else "error",
                      f"La sección '{m}' es obligatoria.", "Presente", "No encontrada" if not found else "Encontrada")

        # Verificar numeración de líneas (borradores)
        has_lines = getattr(self.engine, 'has_line_numbering', False)
        if has_lines:
            self._add(
                "Configuración de Página",
                "Numeración de Líneas Activa",
                "warning",
                "El documento tiene NUMERACIÓN DE LÍNEAS ACTIVA. Esos números secuenciales "
                "(1, 2, 3...) que aparecen al margen izquierdo de cada página solo se permiten "
                "en BORRADORES de revisión, NUNCA en la versión final de la tesis.\n\n"
                "SOLUCIÓN: Pestaña 'Diseño' (o 'Disposición') → 'Números de línea' → "
                "Seleccionar 'Ninguno'. Si tiene varias secciones, repita para cada sección.",
                "Sin numeración de líneas en versión final",
                "Numeración de líneas activa en alguna sección",
            )
        else:
            self._add(
                "Configuración de Página",
                "Numeración de Líneas",
                "passed",
                "El documento no tiene numeración de líneas activa (correcto).",
                "Sin numeración de líneas",
                "Sin numeración de líneas",
            )
