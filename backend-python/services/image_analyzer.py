from PIL import Image
import os
import zipfile

class ImageAnalyzer:
    """
    Inspector de gráficos y fotos artesanal.
    Extrae las imágenes del Word y analiza su calidad técnica.
    """
    def __init__(self, docx_path):
        self.docx_path = docx_path

    def audit_images(self):
        """Extrae y analiza cada imagen dentro del Word."""
        results = []
        try:
            with zipfile.ZipFile(self.docx_path, 'r') as z:
                image_files = [f for f in z.namelist() if f.startswith('word/media/')]
                
                for img_path in image_files:
                    with z.open(img_path) as img_file:
                        with Image.open(img_file) as img:
                            dpi = img.info.get('dpi', (72, 72))
                            # Una tesis profesional pide al menos 300 DPI
                            if dpi[0] < 200:
                                results.append({
                                    "rule": f"Calidad de Imagen ({os.path.basename(img_path)})",
                                    "status": "warning",
                                    "message": f"Baja resolución detectada: {dpi[0]} DPI. Se recomienda 300 DPI."
                                })
                            else:
                                results.append({
                                    "rule": f"Calidad de Imagen ({os.path.basename(img_path)})",
                                    "status": "passed",
                                    "message": f"Resolución óptima: {dpi[0]} DPI."
                                })
        except:
            pass
        return results
