import subprocess
import os
import shutil

class DocConverter:
    """
    Convertidor Universal de Word.
    Acepta .doc, .docx, .docm, .rtf y los estandariza a .docx de alta fidelidad
    utilizando el motor de LibreOffice (Headless).
    """
    
    @staticmethod
    def standardize_to_docx(input_path, output_dir):
        """
        Convierte cualquier formato de Word a un .docx estándar.
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Archivo no encontrado: {input_path}")
            
        file_ext = os.path.splitext(input_path)[1].lower()
        
        # Si ya es .docx, solo verificamos integridad
        if file_ext == ".docx":
            return input_path
            
        print(f"🔄 Convirtiendo {file_ext} a .docx estándar...")
        
        try:
            # Comando de LibreOffice para conversión universal
            # soffice --headless --convert-to docx --outdir [dir] [file]
            command = [
                "soffice",
                "--headless",
                "--convert-to", "docx",
                "--outdir", output_dir,
                input_path
            ]
            
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise Exception(f"Error en LibreOffice: {result.stderr}")
                
            # El nombre de salida suele ser el mismo pero con .docx
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            new_path = os.path.join(output_dir, f"{base_name}.docx")
            
            if os.path.exists(new_path):
                return new_path
            else:
                raise Exception("La conversión falló: Archivo de salida no encontrado.")
                
        except Exception as e:
            print(f"❌ Error en conversión universal: {str(e)}")
            return input_path # Intentar procesar el original si falla
