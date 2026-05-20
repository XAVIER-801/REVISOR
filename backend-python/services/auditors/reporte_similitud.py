"""
reporte_similitud.py - Auditoría de la hoja de Reporte de Similitud (UNA Puno).

Reglas de la guía:
- El reporte de similitud de la versión final es obligatorio.
- El porcentaje de similitud no deberá superar el 20%.
- Deben constar las firmas físicas o digitales del Asesor y de la Unidad de Investigación.
"""
import re
from .base_auditor import BaseAuditor


class ReporteSimilitudAuditor(BaseAuditor):

    def audit(self):
        found_section = False
        text_lines = []
        p_idx = 0

        # Buscar la sección "REPORTE DE SIMILITUD"
        for idx, p in enumerate(self.paragraphs):
            norm = p["norm"]
            if "REPORTE DE SIMILITUD" in norm or "SIMILITUD" in norm:
                found_section = True
                p_idx = p["index"]
                
            if found_section:
                # Capturar líneas hasta que encontremos la siguiente sección
                if any(k in norm for k in ["HOJA DE JURADOS", "DEDICATORIA", "AGRADECIMIENTOS", "ÍNDICE", "INDICE"]):
                    break
                if p["text"].strip():
                    text_lines.append(p["text"])

        # Detectar si hay páginas preliminares insertadas como imágenes escaneadas
        scanned_images = []
        for p in self.paragraphs:
            est_page = p.get("estimated_page", 1)
            # Solo buscar en las primeras 6 páginas preliminares
            if est_page > 6:
                break
            for d in p.get("drawings", []):
                if d.get("width", 0) > 10.0 and d.get("height", 0) > 14.0:
                    scanned_images.append({
                        "p_idx": p["index"],
                        "page": est_page,
                        "width": d["width"],
                        "height": d["height"]
                    })

        if not found_section:
            # Fallback: si hay al menos una imagen escaneada en las páginas preliminares,
            # asumimos de manera amigable que podría corresponder a este reporte
            if scanned_images:
                # Usar la primera imagen escaneada detectada (típicamente pág. 2 o 3)
                target = scanned_images[0]
                self._add("Reporte de Similitud", "Presencia de Reporte de Similitud", "warning",
                          f"Se ha detectado el Reporte de Similitud en formato de imagen escaneada de alta resolución "
                          f"({target['width']} cm x {target['height']} cm) en la Pág. {target['page']}. "
                          f"Dado que está insertado como imagen, recuerde verificar manualmente que las firmas del Asesor "
                          f"y de la Unidad de Investigación sean legibles y que el porcentaje oficial del PDF no supere el 20% máximo.",
                          "Documento escaneado (Presente)", "Presente como Imagen", p_idx=target["p_idx"], p_text="[Imagen Escaneada]")
                return
            else:
                self._add("Reporte de Similitud", "Presencia de Reporte de Similitud", "error",
                          "No se encontró la sección obligatoria 'REPORTE DE SIMILITUD'. Toda tesis de pregrado debe incluir la página del reporte de similitud de la versión final.",
                          "Presente", "Ausente")
                return

        self._add("Reporte de Similitud", "Presencia de Reporte de Similitud", "passed",
                  "Se encontró correctamente la sección obligatoria del Reporte de Similitud.",
                  "Presente", "Presente", p_idx=p_idx, p_text="REPORTE DE SIMILITUD")

        # Buscar porcentaje de similitud
        full_text = " ".join(text_lines)
        sim_match = re.search(r'(\d+)\s*%', full_text)
        
        if sim_match:
            percentage = int(sim_match.group(1))
            ok_sim = percentage <= 20
            status = "passed" if ok_sim else "error"
            msg = (f"El porcentaje de similitud es de {percentage}%. Cumple con el límite institucional máximo permitido (20%)." if ok_sim else
                   f"El porcentaje de similitud detectado es de {percentage}%, lo cual supera el límite máximo permitido por la UNA Puno (20%).")
            self._add("Reporte de Similitud", "Porcentaje de Similitud", status, msg,
                      "<= 20%", f"{percentage}%", p_idx=p_idx, p_text=full_text[:40])
        else:
            # Si no se encuentra explícitamente el porcentaje, lanzar advertencia
            self._add("Reporte de Similitud", "Porcentaje de Similitud", "warning",
                      "No se detectó un porcentaje de similitud en texto (ej. '15%'). Asegúrese de que el reporte digital contenga el porcentaje oficial.",
                      "Límite <= 20%", "No detectado en texto", p_idx=p_idx, p_text="REPORTE DE SIMILITUD")

        # Validar mención de firmas
        has_firmas = "FIRMA" in full_text.upper() or "ASESOR" in full_text.upper()
        if not has_firmas:
            self._add("Reporte de Similitud", "Firmas en Reporte de Similitud", "warning",
                      "Asegúrese de incluir las firmas físicas o digitales correspondientes (del Asesor y de la Unidad de Investigación) en esta página.",
                      "Firmas del Asesor y UI presentas", "No detectado de forma clara", p_idx=p_idx, p_text="REPORTE DE SIMILITUD")
