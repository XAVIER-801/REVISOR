import fitz # PyMuPDF
import subprocess
import os

class VisualAnalyzer:
    """
    Ojo geométrico artesanal.
    Renderiza el Word internamente para medir coordenadas reales y alineación.
    """
    def __init__(self, docx_path):
        self.docx_path = docx_path
        self.pdf_path = docx_path.replace(".docx", "_render.pdf")
        self.doc = None

    def _render_to_pdf(self):
        """Genera un renderizado invisible para medir píxeles."""
        try:
            command = [
                "soffice", "--headless", "--convert-to", "pdf",
                "--outdir", os.path.dirname(self.pdf_path),
                self.docx_path
            ]
            subprocess.run(command, capture_output=True, timeout=30)
            if os.path.exists(self.pdf_path):
                self.doc = fitz.open(self.pdf_path)
                return True
        except:
            return False
        return False

    def check_visual_margins(self):
        """Mide los márgenes reales basándose en el renderizado."""
        if not self._render_to_pdf():
            return []
        
        results = []
        # Analizar la primera página (Portada) para precisión extrema
        if len(self.doc) > 0:
            page = self.doc[0]
            # Buscamos el bloque de texto más a la izquierda y más a la derecha
            text_blocks = page.get_text("dict")["blocks"]
            
            leftmost = 999
            rightmost = 0
            for b in text_blocks:
                if "lines" in b:
                    leftmost = min(leftmost, b["bbox"][0])
                    rightmost = max(rightmost, b["bbox"][2])
            
            # Convertir puntos a cm (1 pt = 0.03527 cm)
            left_cm = leftmost * 0.03527
            results.append({"rule": "Margen Visual Izquierdo", "actual": f"{left_cm:.2f}cm"})
            
        return results

    def cleanup(self):
        """Elimina el renderizado temporal."""
        if self.doc:
            self.doc.close()
        if os.path.exists(self.pdf_path):
            os.remove(self.pdf_path)
