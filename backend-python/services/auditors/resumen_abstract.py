"""
resumen_abstract.py - Auditoría del Resumen y Abstract.

Reglas implementadas:
- Agradecimientos: máximo 1 página (~600 palabras)
- Resumen: entre 250 y 300 palabras
- Palabras clave: formato correcto "Palabras clave:" con P mayúscula
"""
import re
from .base_auditor import BaseAuditor


class ResumenAbstractAuditor(BaseAuditor):

    def audit(self):
        # 1. Auditoría de Agradecimientos (Máximo 1 página)
        content_agr = []
        capture_agr = False

        for p in self.paragraphs:
            norm = p["norm"]
            if "AGRADECIMIENTOS" in norm:
                capture_agr = True
                continue
            if capture_agr and any(k in norm for k in ["INDICE GENERAL", "RESUMEN", "ABSTRACT"]):
                capture_agr = False
                break
            if capture_agr:
                content_agr.append(p["text"])

        if content_agr:
            words_agr = len(" ".join(content_agr).split())
            ok_agr = words_agr < 600
            self._add("Resumen y Abstract", "Extensión de Agradecimientos", "passed" if ok_agr else "error",
                      f"Los agradecimientos deben ocupar máximo 1 página. Hallado: ~{words_agr} palabras.", "< 600 palabras", f"~{words_agr} palabras")

        # 2. Auditoría de Resumen
        content = []
        capture = False
        for p in self.paragraphs:
            norm = p["norm"]
            if norm == "RESUMEN":
                capture = True
                continue
            if "PALABRAS CLAVE" in norm:
                capture = False
                pk_txt = p["text"].lower()
                if pk_txt.startswith("palabras clave:"):
                    self._add("Resumen y Abstract", "Formato Palabras Clave", "passed", "Tag 'Palabras clave:' detectado.")
                else:
                    self._add("Resumen y Abstract", "Formato Palabras Clave", "error", "Debe empezar con 'Palabras clave:' en minúscula (excepto P).")
                break
            if capture:
                content.append(p["text"])

        if content:
            full_text = " ".join(content)
            words = len(full_text.split())
            ok_words = 250 <= words <= 300
            self._add("Resumen y Abstract", "Extensión del Resumen", "passed" if ok_words else "error",
                      f"El resumen debe tener entre 250 y 300 palabras. Hallado: {words}", "250-300", words)
