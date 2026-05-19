import spacy
import os

class LinguisticAnalyzer:
    """
    Cerebro lingüístico artesanal.
    Analiza la gramática, longitud de párrafos y coherencia sin usar APIs externas.
    """
    def __init__(self):
        try:
            # Cargamos el modelo de español (debe estar pre-descargado en Docker)
            self.nlp = spacy.load("es_core_news_sm")
        except:
            self.nlp = None

    def analyze_paragraph(self, text, run_nlp=True):
        if not text.strip():
            return []

        alerts = []

        # --- FAST CHECKS (Microseconds execution) ---
        # 1. Verificación de mayúsculas al inicio
        if text.strip() and text.strip()[0].islower():
            alerts.append("El párrafo comienza con minúscula.")

        # 2. Errores de puntuación y espacios (Micro-edición)
        if "  " in text:
            alerts.append("Se detectaron espacios dobles innecesarios.")
        
        if " ," in text or " ." in text:
            alerts.append("Espacio detectado antes de signo de puntuación (punto o coma).")
            
        if any(f"{sign}{letter}" in text for sign in [",", "."] for letter in "abcdefghijklmnopqrstuvwxyzáéíóú"):
            alerts.append("Falta espacio después de un signo de puntuación.")

        # 3. Puntos sueltos o finales
        if text.strip().endswith(",") or (not text.strip().endswith(".") and len(text) > 20):
            if not text.strip().endswith(":") and not text.strip().endswith(";"):
                 alerts.append("El párrafo no termina con un punto final.")

        # --- HEAVY CHECKS (SpaCy NLP) ---
        if run_nlp and self.nlp:
            try:
                doc = self.nlp(text)
                # 4. Detectar oraciones excesivamente largas (Dificultan la lectura)
                for sent in doc.sents:
                    if len(sent) > 50:
                        alerts.append(f"Oración muy larga ({len(sent)} palabras). Considere dividirla.")

                # 5. Detectar párrafos sin verbos (Posibles errores de pegado)
                has_verb = any(token.pos_ == "VERB" for token in doc)
                if not has_verb and len(text) > 40:
                    alerts.append("El párrafo parece no tener verbos de acción.")
            except:
                pass

        return alerts
