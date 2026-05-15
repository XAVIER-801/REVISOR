import os
import zipfile

class VisionAuditService:
    """
    SERVICIO DE VISION IA (POSTERGADO)
    Este servicio se encargara de:
    1. Extraer imagenes de actas del Word.
    2. Enviarlas a Gemini Pro Vision / OCR Avanzado.
    3. Validar firmas, sellos y texto manuscrito.
    
    NOTA: Este modulo esta listo para activarse cuando el usuario lo solicite.
    Por ahora todas las funciones retornan placeholders.
    """
    
    @staticmethod
    def analyze_images(image_paths):
        # TODO: Implementar cuando el usuario lo solicite
        # from google import generativeai as genai
        # model = genai.GenerativeModel('gemini-pro-vision')
        # response = model.generate_content([image, "Analiza esta acta..."])
        return {
            "status": "postponed",
            "message": "Modulo de vision IA listo para implementacion futura.",
            "detected_signatures": []
        }

    @staticmethod
    def extract_images_from_docx(docx_path, output_dir):
        """Extrae todas las imagenes del archivo .docx (que es un ZIP)."""
        os.makedirs(output_dir, exist_ok=True)
        images = []
        with zipfile.ZipFile(docx_path, 'r') as zip_ref:
            for file in zip_ref.namelist():
                if file.startswith('word/media/'):
                    zip_ref.extract(file, output_dir)
                    images.append(os.path.join(output_dir, file))
        return images
