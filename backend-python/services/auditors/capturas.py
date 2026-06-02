"""
capturas.py - Detección de imágenes que parecen capturas de pantalla con texto.

Algunos estudiantes insertan capturas de pantalla con texto (de páginas web,
PDFs, otros documentos) en lugar de transcribir el contenido. Esta práctica:
- Puede ocultar plagio (Turnitin no procesa texto dentro de imágenes)
- Rompe la accesibilidad
- Impide validar formato del texto

Heurística de detección:
- Imagen grande (>10cm de ancho)
- Proporción no cuadrada (típicamente 16:9 o 4:3 de pantalla)
- NO está cerca de una etiqueta "Figura N" (porque entonces es figura legítima)
- Está en el cuerpo del documento (no en jurados, similitud, dedicatoria)

Cuando se detecta, sugerir transcripción.
"""
import re
from .base_auditor import BaseAuditor


class CapturasAuditor(BaseAuditor):

    def audit(self):
        captures_found = 0
        for i, p in enumerate(self.paragraphs):
            if not p.get("looks_like_screenshot"):
                continue
            # Excluir páginas preliminares
            if p.get("is_cover"):
                continue
            sec_upper = (p.get("section") or "").upper()
            if any(k in sec_upper for k in [
                "JURADOS", "SIMILITUD", "DEDICATORIA", "AGRADECIMIENTO",
                "ÍNDICE", "INDICE", "PORTADA"
            ]):
                continue
            # Excluir si pertenece a una figura legítima (etiqueta "Figura N" cerca)
            if self._is_legitimate_figure(i):
                continue

            drawing = p.get("screenshot_drawing") or {}
            w = drawing.get("width", 0)
            h = drawing.get("height", 0)
            page = p.get("estimated_page", "?")
            section = p.get("section") or "General"

            captures_found += 1
            self._add(
                "Capturas de Pantalla",
                f"Posible captura con texto en pág. {page}",
                "warning",
                f"Se detectó una IMAGEN GRANDE ({w}cm × {h}cm) en el cuerpo de la "
                f"tesis (sección '{section}') que parece ser una CAPTURA DE PANTALLA "
                f"con texto. Las capturas de pantalla con texto NO SON ACEPTABLES "
                f"como contenido de tesis porque: (1) Turnitin no puede verificar "
                f"originalidad del texto dentro de imágenes, (2) rompen la accesibilidad, "
                f"(3) impiden la validación de formato. DEBE TRANSCRIBIR el texto "
                f"de la imagen como párrafos normales. Si la imagen es legítimamente "
                f"una figura (gráfico, fotografía, esquema), agréguele su etiqueta "
                f"'Figura N. Título descriptivo' arriba en cursiva.",
                "Texto transcrito a párrafos o Figura con etiqueta",
                f"Imagen sin contexto: {w}cm × {h}cm",
                p_idx=p["index"],
                p_text="[Imagen detectada como posible captura]",
            )

        if captures_found > 0:
            self._add(
                "Capturas de Pantalla",
                f"Resumen: {captures_found} posibles capturas detectadas",
                "warning",
                f"Se detectaron {captures_found} imágenes grandes sin etiqueta de "
                f"figura, que podrían ser capturas de pantalla con texto. Revise "
                f"cada una: si son figuras legítimas, agrégueles su etiqueta "
                f"'Figura N. Título descriptivo'. Si contienen texto, transcríbalo.",
                "0 capturas / todas las imágenes etiquetadas como Figura",
                f"{captures_found} posibles capturas",
            )

    def _is_legitimate_figure(self, idx, window=4):
        """
        Verifica si el párrafo de la imagen tiene una etiqueta 'Figura N' cerca
        (arriba dentro de los `window` párrafos previos).
        """
        for k in range(idx - 1, max(-1, idx - window), -1):
            prev_p = self.paragraphs[k]
            prev_txt = prev_p["text"].strip()
            if not prev_txt:
                continue
            if re.match(r'^Figura\s+\d+', prev_txt, re.IGNORECASE):
                return True
            # Si encontramos un título de nivel, no seguir buscando
            if prev_p.get("is_heading"):
                break
        return False
