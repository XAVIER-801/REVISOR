"""
estilo_escritura.py - Auditoría de Estilo de Escritura y Hábitos de Formato.

Reglas implementadas:
- Detección de múltiples Enters seguidos (debe usar Salto de Página)
- Análisis lingüístico: puntuación, gramática, estilo (delegado a LinguisticAnalyzer)
- Exclusión de alertas de punto final en Dedicatoria, Agradecimientos e Índice
"""
import re
from .base_auditor import BaseAuditor


class EstiloEscrituraAuditor(BaseAuditor):

    def audit(self):
        self._audit_formatting_habits()
        self._audit_writing_style()

    def _audit_formatting_habits(self):
        """Detecta malos hábitos de formato como múltiples Enters en vez de Saltos de Página."""
        consecutive_empty = 0
        for i, p in enumerate(self.paragraphs):
            if p.get("is_cover"):
                consecutive_empty = 0
                continue
            txt = p["text"].strip()
            if not txt:
                consecutive_empty += 1
            else:
                if consecutive_empty >= 3:
                    self._add("Estilo y Escritura", "Uso de Enters para saltar página", "warning",
                              f"Se detectaron {consecutive_empty} Enters seguidos. Use 'Insertar > Salto de página' para un formato profesional.",
                              "Salto de Página", f"{consecutive_empty} Enters", p_idx=i-1)
                consecutive_empty = 0

    def _audit_writing_style(self):
        """Analiza la calidad de la escritura, puntuación y gramática."""
        linguistic = self.engine.linguistic
        count = 0
        nlp_calls = 0
        for i, p in enumerate(self.paragraphs):
            if count >= 150:
                break
            if p.get("is_cover"):
                continue
            txt = p["text"].strip()
            if len(txt) > 15 and not p.get('in_table'):
                run_nlp = False
                if nlp_calls < 80:
                    run_nlp = True
                    nlp_calls += 1

                alerts = linguistic.analyze_paragraph(p["text"], run_nlp=run_nlp)

                # Excluir punto final en Dedicatoria, Agradecimientos e Índice
                is_in_index = False
                if self.index_start_idx != -1 and self.last_index_idx != -1:
                    if self.index_start_idx <= i <= self.last_index_idx:
                        is_in_index = True

                p_sec_norm = self._norm(p.get("section", ""))
                if "DEDICATORIA" in p_sec_norm or "AGRADECIMIENTOS" in p_sec_norm or is_in_index:
                    alerts = [a for a in alerts if "punto final" not in a]

                if alerts:
                    count += 1
                    for alert in alerts:
                        self._add("Estilo y Escritura", "Sugerencia Lingüística", "warning", alert, p_idx=i, p_text=txt)
