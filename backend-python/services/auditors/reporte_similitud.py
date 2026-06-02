"""
reporte_similitud.py - Auditoría de la hoja de Reporte de Similitud (Turnitin).

IMPORTANTE: El Reporte de Similitud (Turnitin) viene SIEMPRE como UNA HOJA ESCANEADA
(imagen) en las páginas preliminares. NO se audita su texto interno como párrafos normales.

Reglas:
- Verificar PRESENCIA del título/anexo "REPORTE DE SIMILITUD" en páginas preliminares
- Detectar si la página correspondiente contiene una IMAGEN ESCANEADA grande
- El porcentaje (≤ 20%) y las firmas se validan vía OCR (ai_engine/scanned_auditor.py)
  cuando Tesseract está disponible. Aquí solo verificamos presencia.
- NO buscar números/porcentajes en texto del cuerpo (causaba falsos positivos)
"""
import re
from .base_auditor import BaseAuditor


class ReporteSimilitudAuditor(BaseAuditor):

    def audit(self):
        # 1. Buscar el título o anexo "REPORTE DE SIMILITUD" en páginas preliminares
        section_title_idx = -1
        section_title_p = None

        for idx, p in enumerate(self.paragraphs):
            norm = p["norm"]
            est_page = p.get("estimated_page", 1)
            # Solo en páginas preliminares (antes del cuerpo)
            if est_page > 10:
                break
            if ("REPORTE DE SIMILITUD" in norm or norm == "SIMILITUD"
                or "REPORTE TURNITIN" in norm or "TURNITIN" in norm):
                # Asegurar que no esté dentro del índice
                sec_upper = p.get("section", "").upper()
                if "INDICE" in sec_upper or "ÍNDICE" in sec_upper:
                    continue
                # Asegurar que no sea línea de índice (con relleno de puntos o número de página)
                if "...." in p["text"] or re.search(r"\s+\d+$", p["text"].strip()):
                    continue
                section_title_idx = idx
                section_title_p = p
                break

        # 2. Buscar imágenes escaneadas grandes en las primeras 8 páginas
        #    (típico tamaño: > 10cm x > 14cm — equivalente a una hoja A4 completa)
        scanned_images = []
        for p in self.paragraphs:
            est_page = p.get("estimated_page", 1)
            if est_page > 8:
                break
            for d in p.get("drawings", []):
                if d.get("width", 0) > 10.0 and d.get("height", 0) > 14.0:
                    scanned_images.append({
                        "p_idx": p["index"],
                        "page": est_page,
                        "width": d["width"],
                        "height": d["height"],
                    })

        # 3. Lógica de validación
        if section_title_idx == -1 and not scanned_images:
            # Ni título ni imagen → ausente
            self._add(
                "Reporte de Similitud",
                "Presencia de Reporte de Similitud",
                "error",
                "No se encontró la página obligatoria del 'Reporte de Similitud' "
                "(Turnitin) en las páginas preliminares. Esta hoja escaneada con el "
                "porcentaje de similitud (debe ser menor o igual a 20%) es de "
                "presentación obligatoria según la guía UNAP.",
                "Reporte de Similitud presente (como imagen escaneada)",
                "No detectado",
            )
            return

        if section_title_idx != -1 and not scanned_images:
            # Tiene título pero no imagen → probablemente el reporte está como texto, lo cual es atípico
            self._add(
                "Reporte de Similitud",
                "Formato del Reporte de Similitud",
                "warning",
                "Se encontró el título 'REPORTE DE SIMILITUD' pero no una imagen "
                "escaneada del reporte oficial. El reporte de Turnitin debe insertarse "
                "como imagen escaneada con las firmas del Asesor y de la Unidad de "
                "Investigación.",
                "Imagen escaneada del reporte Turnitin",
                "Solo título de sección, sin imagen",
                p_idx=section_title_idx,
                p_text=section_title_p["text"] if section_title_p else "",
            )
            return

        # 4. Hay imagen escaneada → presencia confirmada
        target = scanned_images[0]
        # Buscar la imagen escaneada más cercana al título (si existe)
        if section_title_idx != -1:
            for img in scanned_images:
                if abs(img["p_idx"] - section_title_idx) < 20:
                    target = img
                    break

        self._add(
            "Reporte de Similitud",
            "Presencia de Reporte de Similitud",
            "passed",
            f"Se detectó la hoja escaneada del Reporte de Similitud "
            f"({target['width']} cm × {target['height']} cm) en la página {target['page']}. "
            f"El porcentaje exacto y las firmas se verifican mediante OCR si Tesseract "
            f"está disponible. Verifique manualmente que el porcentaje no supere el 20% y "
            f"que estén las firmas del Asesor y de la Unidad de Investigación.",
            "Imagen escaneada presente",
            f"Presente en página {target['page']}",
            p_idx=target["p_idx"],
            p_text="[Hoja escaneada del Reporte de Similitud]",
        )

        # 5. Aviso informativo: la verificación profunda (porcentaje + firmas)
        #    requiere OCR opcional
        self._add(
            "Reporte de Similitud",
            "Verificación de Porcentaje y Firmas",
            "warning",
            "El porcentaje de similitud y las firmas del Reporte de Turnitin no se "
            "validan automáticamente sobre el texto del documento (es una hoja "
            "escaneada). Si el módulo OCR (Tesseract) está disponible, el sistema "
            "intentará extraer estos datos. Caso contrario, verifique manualmente: "
            "(1) que el porcentaje sea menor o igual a 20%, (2) que las firmas del "
            "Asesor y de la Unidad de Investigación estén presentes (físicas o digitales, "
            "no combinadas).",
            "Porcentaje ≤ 20% y firmas presentes",
            "Pendiente de verificación manual o por OCR",
            p_idx=target["p_idx"],
        )
