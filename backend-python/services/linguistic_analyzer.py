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

    def analyze_paragraph(self, text):
        if not self.nlp or not text.strip():
            return []

        doc = self.nlp(text)
        alerts = []

        # 1. Detectar oraciones excesivamente largas (Dificultan la lectura)
        for sent in doc.sents:
            if len(sent) > 50:
                alerts.append(f"Oración muy larga ({len(sent)} palabras). Considere dividirla.")

        # 2. Detectar párrafos sin verbos (Posibles errores de pegado)
        has_verb = any(token.pos_ == "VERB" for token in doc)
        if not has_verb and len(text) > 40:
            alerts.append("El párrafo parece no tener verbos de acción.")

        # 3. Verificación de mayúsculas al inicio
        if text[0].islower():
            alerts.append("El párrafo comienza con minúscula.")

        return alerts
