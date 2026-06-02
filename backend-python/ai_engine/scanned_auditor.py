"""
scanned_auditor.py - Auditor de documentos escaneados en el .docx.

Usa OCR para verificar presencia y validez de documentos que comúnmente vienen
como imágenes escaneadas en una tesis:

1. Hoja de Jurados (con firmas físicas)
2. Reporte de Similitud (Turnitin) - debe mostrar porcentaje ≤ 20%
3. Declaración Jurada de Autenticidad
4. Autorización para el Depósito (con licencia Creative Commons)

Este auditor es OPCIONAL y solo se ejecuta si:
- Tesseract OCR está instalado
- El motor principal lo invoca explícitamente
"""
import re
from typing import List, Dict
from .image_ocr import ImageOCR


class ScannedAuditor:
    """
    Audita documentos escaneados en el .docx mediante OCR.

    Uso:
        scanned = ScannedAuditor(docx_path)
        results = scanned.audit()
        # Cada result tiene la misma estructura que los auditores normales
        # para integrarse fácilmente al reporte principal
    """

    def __init__(self, docx_path: str):
        self.docx_path = docx_path
        self.ocr = ImageOCR(docx_path)

    def audit(self) -> List[Dict]:
        """Ejecuta todas las auditorías de documentos escaneados."""
        if not self.ocr.is_available():
            return [{
                "category": "OCR Imágenes",
                "rule": "Disponibilidad Tesseract",
                "status": "warning",
                "message": (
                    "Tesseract OCR no está disponible. Para activar el reconocimiento "
                    "de documentos escaneados (Hoja de Jurados, Turnitin, etc.), "
                    "instale Tesseract OCR y ejecute: pip install pytesseract Pillow."
                ),
                "expected": "Tesseract instalado",
                "actual": "No disponible",
            }]

        results = []
        all_images = self.ocr.extract_all_texts()

        results.extend(self._audit_hoja_jurados(all_images))
        results.extend(self._audit_turnitin(all_images))
        results.extend(self._audit_declaracion_jurada(all_images))
        results.extend(self._audit_autorizacion(all_images))

        return results

    # ── 1. Hoja de Jurados ────────────────────────────────────────────────

    def _audit_hoja_jurados(self, all_images: List[Dict]) -> List[Dict]:
        """Busca imagen escaneada de la Hoja de Jurados (firma de los 4 jurados)."""
        out = []
        target = self._find_with_keywords(all_images, ["PRESIDENTE"], ["MIEMBRO", "ASESOR"])
        if not target:
            out.append({
                "category": "OCR Imágenes",
                "rule": "Hoja de Jurados (Imagen)",
                "status": "warning",
                "message": (
                    "No se detectó una imagen escaneada con texto de Hoja de Jurados. "
                    "Si la hoja viene como texto en el Word, se valida en el auditor "
                    "etiquetas_jurados.py."
                ),
                "expected": "Imagen escaneada con cargos de jurados",
                "actual": "No detectada",
            })
            return out

        text = target.get("text", "").upper()
        # Verificar los 4 cargos
        cargos_esperados = [
            ("PRESIDENTE", "Presidente"),
            ("PRIMER MIEMBRO", "Primer Miembro"),
            ("SEGUNDO MIEMBRO", "Segundo Miembro"),
            ("ASESOR", "Asesor de Tesis"),
        ]
        missing = []
        for key, label in cargos_esperados:
            if key not in text:
                missing.append(label)

        if missing:
            out.append({
                "category": "OCR Imágenes",
                "rule": "Cargos en Hoja de Jurados",
                "status": "warning",
                "message": (
                    f"En la imagen escaneada de la Hoja de Jurados no se reconocieron "
                    f"todos los cargos obligatorios. Faltantes (puede ser por baja calidad de OCR): "
                    f"{', '.join(missing)}. Verifique manualmente."
                ),
                "expected": "Presidente, Primer Miembro, Segundo Miembro, Asesor",
                "actual": f"Faltantes según OCR: {', '.join(missing)}",
            })
        else:
            out.append({
                "category": "OCR Imágenes",
                "rule": "Cargos en Hoja de Jurados",
                "status": "passed",
                "message": "OCR detectó los 4 cargos obligatorios en la Hoja de Jurados escaneada.",
                "expected": "4 cargos",
                "actual": "4 cargos detectados",
            })

        return out

    # ── 2. Reporte de Similitud (Turnitin) ────────────────────────────────

    def _audit_turnitin(self, all_images: List[Dict]) -> List[Dict]:
        """Busca el Reporte de Similitud y extrae el porcentaje (debe ser ≤20%)."""
        out = []
        # Buscar imagen con texto de "similitud" o "%"
        target = None
        for img in all_images:
            txt = img.get("text", "").upper()
            if any(kw in txt for kw in ["SIMILITUD", "TURNITIN", "ORIGINALITY", "OVERALL"]):
                target = img
                break

        if not target:
            out.append({
                "category": "OCR Imágenes",
                "rule": "Reporte de Similitud (Imagen)",
                "status": "warning",
                "message": (
                    "No se detectó imagen del Reporte de Similitud. "
                    "Asegúrese de incluirlo en las páginas preliminares."
                ),
                "expected": "Imagen del Reporte de Similitud presente",
                "actual": "No detectada por OCR",
            })
            return out

        text = target.get("text", "")
        # Extraer porcentajes (e.g. "12%", "18 %")
        percentages = re.findall(r"(\d{1,3})\s*%", text)
        if percentages:
            valid_pcts = [int(p) for p in percentages if 0 <= int(p) <= 100]
            if valid_pcts:
                # Tomar el más probable: usualmente el más grande (índice global)
                detected = max(valid_pcts)
                if detected > 20:
                    out.append({
                        "category": "OCR Imágenes",
                        "rule": "Porcentaje de Similitud",
                        "status": "error",
                        "message": (
                            f"El porcentaje de similitud detectado en la imagen del reporte es "
                            f"{detected}%, que SUPERA el límite del 20% establecido por la UNAP."
                        ),
                        "expected": "≤ 20%",
                        "actual": f"{detected}%",
                    })
                else:
                    out.append({
                        "category": "OCR Imágenes",
                        "rule": "Porcentaje de Similitud",
                        "status": "passed",
                        "message": (
                            f"El porcentaje de similitud detectado por OCR es {detected}%, "
                            f"dentro del límite del 20%."
                        ),
                        "expected": "≤ 20%",
                        "actual": f"{detected}%",
                    })
        else:
            out.append({
                "category": "OCR Imágenes",
                "rule": "Porcentaje de Similitud",
                "status": "warning",
                "message": (
                    "Se detectó el Reporte de Similitud pero no se pudo extraer el porcentaje. "
                    "Verifique manualmente que sea ≤ 20%."
                ),
                "expected": "≤ 20%",
                "actual": "No legible por OCR",
            })
        return out

    # ── 3. Declaración Jurada de Autenticidad ─────────────────────────────

    def _audit_declaracion_jurada(self, all_images: List[Dict]) -> List[Dict]:
        out = []
        target = None
        for img in all_images:
            txt = img.get("text", "").upper()
            if "DECLARACI" in txt and ("JURADA" in txt or "AUTENTICIDAD" in txt):
                target = img
                break

        if not target:
            # Puede que esté solo como texto, no como imagen. El auditor
            # declaracion_autenticidad.py ya lo valida en ese caso.
            return out

        text = target.get("text", "").upper()
        # Verificar elementos clave
        checks = [
            ("DNI" in text or "IDENTIDAD" in text, "Número de DNI/Identidad"),
            ("ESCUELA" in text or "FACULTAD" in text, "Datos de escuela/facultad"),
            ("FIRMA" in text or self._likely_has_signature(target), "Indicio de firma"),
        ]
        missing = [label for ok, label in checks if not ok]

        if missing:
            out.append({
                "category": "OCR Imágenes",
                "rule": "Contenido Declaración Jurada (Imagen)",
                "status": "warning",
                "message": (
                    f"En la imagen escaneada de la Declaración Jurada no se reconocieron "
                    f"los siguientes elementos: {', '.join(missing)}. Verifique manualmente."
                ),
                "expected": "DNI, Escuela, Firma",
                "actual": f"Faltantes según OCR: {', '.join(missing)}",
            })
        else:
            out.append({
                "category": "OCR Imágenes",
                "rule": "Contenido Declaración Jurada (Imagen)",
                "status": "passed",
                "message": "OCR confirma los datos clave en la Declaración Jurada.",
                "expected": "DNI, Escuela, Firma",
                "actual": "Detectado",
            })
        return out

    # ── 4. Autorización para el Depósito ──────────────────────────────────

    def _audit_autorizacion(self, all_images: List[Dict]) -> List[Dict]:
        out = []
        target = None
        for img in all_images:
            txt = img.get("text", "").upper()
            if "AUTORIZACI" in txt and ("DEP" in txt or "REPOSITORIO" in txt):
                target = img
                break

        if not target:
            return out

        text = target.get("text", "").upper()
        has_creative_commons = "CREATIVE COMMONS" in text or "LICENCIA" in text or "ATRIBUCI" in text
        has_firma = "FIRMA" in text or self._likely_has_signature(target)

        if not has_creative_commons:
            out.append({
                "category": "OCR Imágenes",
                "rule": "Licencia Creative Commons (Imagen)",
                "status": "warning",
                "message": (
                    "En la imagen escaneada de la Autorización para el Depósito no se "
                    "detectó mención a la licencia Creative Commons. La guía UNAP "
                    "requiere especificar el tipo de licencia."
                ),
                "expected": "Licencia Creative Commons mencionada",
                "actual": "No detectada por OCR",
            })

        if not has_firma:
            out.append({
                "category": "OCR Imágenes",
                "rule": "Firma Autorización Depósito (Imagen)",
                "status": "warning",
                "message": "No se detectó firma en la imagen de Autorización. Verifique manualmente.",
                "expected": "Firma presente",
                "actual": "No detectada",
            })
        return out

    # ── Helpers ───────────────────────────────────────────────────────────

    def _find_with_keywords(
        self,
        all_images: List[Dict],
        must_have: List[str],
        any_of: List[str] = None
    ) -> Dict:
        any_of = any_of or []
        for img in all_images:
            text_upper = img.get("text", "").upper()
            if all(kw.upper() in text_upper for kw in must_have):
                if not any_of or any(kw.upper() in text_upper for kw in any_of):
                    return img
        return None

    def _likely_has_signature(self, img_info: Dict) -> bool:
        """
        Heurística simple: si la imagen es grande y el OCR detectó MUY pocas
        palabras de texto, probablemente contiene firmas/sellos manuscritos
        no reconocibles por OCR.
        """
        text = img_info.get("text", "")
        word_count = len(text.split())
        size_kb = img_info.get("size_kb", 0)
        # Imagen grande con poco texto → probablemente tiene firma
        return size_kb > 100 and word_count < 50
