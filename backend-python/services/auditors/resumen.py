"""
resumen.py - Auditoría de la sección de RESUMEN (Español).

Reglas implementadas:
- Extensión del Resumen: entre 250 y 300 palabras.
- Formato de Palabras clave: etiqueta obligatoria "Palabras clave: " con P mayúscula y resto minúsculas.
"""
from .base_auditor import BaseAuditor


class ResumenAuditor(BaseAuditor):

    def audit(self):
        content = []
        capture = False
        
        for p in self.paragraphs:
            norm = p["norm"]
            if norm == "RESUMEN":
                capture = True
                continue
            if "PALABRAS CLAVE" in norm:
                capture = False
                pk_txt = p["text"].strip()
                if pk_txt.startswith("Palabras clave:"):
                    self._add("Resumen y Abstract", "Formato Palabras Clave", "passed", 
                              "Etiqueta 'Palabras clave:' correcta.", "Palabras clave:", pk_txt[:20])
                else:
                    self._add("Resumen y Abstract", "Formato Palabras Clave", "error", 
                              "Debe empezar exactamente con 'Palabras clave:' (P mayúscula, resto minúsculas y dos puntos).", 
                              "Palabras clave:", pk_txt[:20])
                break
            if capture:
                if p["text"].strip():
                    content.append(p["text"])

        if content:
            full_text = " ".join(content)
            words = len(full_text.split())
            ok_words = 250 <= words <= 300
            self._add("Resumen y Abstract", "Extensión del Resumen", "passed" if ok_words else "error",
                      f"El resumen debe tener entre 250 y 300 palabras. Hallado: {words} palabras.", 
                      "250-300 palabras", f"{words} palabras")
