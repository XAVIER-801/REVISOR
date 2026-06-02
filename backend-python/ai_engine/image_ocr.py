"""
image_ocr.py - Reconocimiento Óptico de Caracteres (OCR) en imágenes del Word.

Usa Tesseract OCR (Google, open source, gratuito) para extraer texto de:
- Hoja de Jurados (escaneada con firmas)
- Reporte de Similitud (Turnitin)
- Autorización para Depósito
- Declaración Jurada de Autenticidad
- Cualquier otra imagen con texto en el documento

Requiere:
- pip install pytesseract Pillow
- Tesseract OCR instalado en el sistema
  (Windows: https://github.com/UB-Mannheim/tesseract/wiki)
"""
import os
import zipfile
import io
from typing import List, Dict, Optional

# Imports tolerantes: si las librerías no están, el módulo no rompe
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False


class ImageOCR:
    """
    Extrae texto de imágenes embebidas en un .docx usando Tesseract OCR.

    Uso:
        ocr = ImageOCR(docx_path)
        if ocr.is_available():
            results = ocr.extract_all_texts(min_image_size_kb=20)
            for r in results:
                print(f"Imagen {r['filename']}: {r['text'][:100]}...")
    """

    # Tamaños mínimos típicos de documentos escaneados (filtra logos pequeños)
    DEFAULT_MIN_KB = 20
    DEFAULT_MIN_WIDTH = 400  # píxeles

    def __init__(self, docx_path: str, lang: str = "spa+eng"):
        self.docx_path = docx_path
        self.lang = lang  # idiomas Tesseract: spa (español), eng (inglés)

    def is_available(self) -> bool:
        """Verifica si las dependencias (PIL + Tesseract) están instaladas."""
        if not HAS_PIL or not HAS_TESSERACT:
            return False
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def extract_all_texts(
        self,
        min_image_size_kb: int = DEFAULT_MIN_KB,
        min_width: int = DEFAULT_MIN_WIDTH,
    ) -> List[Dict]:
        """
        Extrae texto de todas las imágenes del .docx que parezcan documentos
        escaneados (tamaño suficiente para contener texto legible).

        Retorna lista de:
            {
                "filename": "image1.png",
                "size_kb": 245,
                "width_px": 1200,
                "height_px": 1600,
                "text": "Texto reconocido...",
                "confidence": 87.5  # promedio de confianza Tesseract
            }
        """
        if not self.is_available():
            return [{
                "error": "Tesseract/PIL no disponible. Instale con: pip install pytesseract Pillow",
                "filename": None,
                "text": "",
            }]

        results = []
        try:
            with zipfile.ZipFile(self.docx_path, "r") as z:
                image_files = [
                    f for f in z.namelist()
                    if f.startswith("word/media/") and not f.endswith(".wdp")
                ]
                for img_path in image_files:
                    try:
                        img_data = z.read(img_path)
                        size_kb = len(img_data) // 1024
                        if size_kb < min_image_size_kb:
                            continue
                        img = Image.open(io.BytesIO(img_data))
                        w, h = img.size
                        if w < min_width:
                            continue
                        # Convertir a RGB si es necesario
                        if img.mode not in ("RGB", "L"):
                            img = img.convert("RGB")
                        text = pytesseract.image_to_string(img, lang=self.lang)
                        # Confianza promedio (Tesseract data)
                        try:
                            data = pytesseract.image_to_data(
                                img, lang=self.lang,
                                output_type=pytesseract.Output.DICT
                            )
                            confidences = [int(c) for c in data.get("conf", []) if str(c).isdigit() and int(c) >= 0]
                            avg_conf = sum(confidences) / len(confidences) if confidences else 0
                        except Exception:
                            avg_conf = 0

                        results.append({
                            "filename": os.path.basename(img_path),
                            "path": img_path,
                            "size_kb": size_kb,
                            "width_px": w,
                            "height_px": h,
                            "text": text.strip(),
                            "confidence": round(avg_conf, 1),
                        })
                    except Exception as e:
                        results.append({
                            "filename": os.path.basename(img_path),
                            "error": str(e),
                            "text": "",
                        })
        except Exception as e:
            results.append({"error": f"Error abriendo docx: {e}", "text": ""})
        return results

    def find_document_by_keywords(self, keywords: List[str], min_confidence: float = 30.0) -> Optional[Dict]:
        """
        Busca una imagen cuyo texto OCR contenga TODAS las keywords dadas
        (case-insensitive). Útil para identificar:
        - Hoja de Jurados: keywords=['PRESIDENTE', 'SUSTENTACIÓN']
        - Turnitin: keywords=['similitud', '%']
        - Declaración Jurada: keywords=['JURADA', 'AUTENTICIDAD']
        - Autorización: keywords=['AUTORIZACIÓN', 'DEPÓSITO', 'REPOSITORIO']
        """
        results = self.extract_all_texts()
        keywords_upper = [k.upper() for k in keywords]
        for r in results:
            if r.get("confidence", 0) < min_confidence:
                continue
            text_upper = r.get("text", "").upper()
            if all(kw in text_upper for kw in keywords_upper):
                return r
        return None
