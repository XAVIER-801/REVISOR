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
        ok_paper = paper == 'A4'
        self._add("Configuración de Página", "Tamaño de Papel", "passed" if ok_paper else "error",
                  "El papel debe ser A4.", "A4", paper)

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
        self._add("Configuración de Página", "Numeración de Líneas", "passed" if not has_lines else "error",
                  "El documento de tesis final y limpio no debe contener numeración de líneas de página (solo se permite en borradores).",
                  "Sin numeración de líneas", "El documento contiene numeración de líneas activa en sus secciones" if has_lines else "Sin numeración de líneas")
