"""
abstract.py - Auditoría de la sección de ABSTRACT (Inglés).

Reglas implementadas:
- Extensión del Abstract: entre 250 y 300 palabras.
- Formato de Keywords: etiqueta obligatoria "Keywords: " con K mayúscula y resto minúsculas.
"""
from .base_auditor import BaseAuditor


class AbstractAuditor(BaseAuditor):

    def audit(self):
        content = []
        capture = False
        
        for p in self.paragraphs:
            norm = p["norm"]
            if norm == "ABSTRACT":
                capture = True
                continue
            if "KEYWORDS" in norm or "KEY WORDS" in norm:
                capture = False
                pk_txt = p["text"].strip()
                if pk_txt.startswith("Keywords:"):
                    self._add("Resumen y Abstract", "Formato Keywords", "passed", 
                              "Etiqueta 'Keywords:' correcta.", "Keywords:", pk_txt[:20])
                else:
                    self._add("Resumen y Abstract", "Formato Keywords", "error", 
                              "Debe empezar exactamente con 'Keywords:' (K mayúscula, resto minúsculas y dos puntos).", 
                              "Keywords:", pk_txt[:20])
                break
            if capture:
                if p["text"].strip():
                    content.append(p["text"])

        if content:
            full_text = " ".join(content)
            words = len(full_text.split())
            ok_words = 250 <= words <= 300
            self._add("Resumen y Abstract", "Extensión del Abstract", "passed" if ok_words else "error",
                      f"El abstract debe tener entre 250 y 300 palabras. Hallado: {words} palabras.", 
                      "250-300 palabras", f"{words} palabras")
