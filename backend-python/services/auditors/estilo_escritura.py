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
        """
        Detecta malos hábitos de formato (Guía UNAP):
        - Múltiples Enters seguidos en vez de Saltos de Página → ERROR
        - Doble espacio en texto → ERROR (drástico)
        """
        # 1. ENTERS MÚLTIPLES PARA SIMULAR SALTOS DE PÁGINA
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
                    self._add(
                        "Estilo y Escritura",
                        "Uso de Enters para saltar página",
                        "error",
                        f"Se detectaron {consecutive_empty} Enters consecutivos para simular "
                        f"un salto de página. ESTO NO ES PROFESIONAL. Debe usar la función "
                        f"'Insertar > Salto de página' (Ctrl + Enter) en su lugar. Los Enters "
                        f"sucesivos rompen la maquetación al editar el documento.",
                        "Usar Insertar > Salto de página (Ctrl+Enter)",
                        f"{consecutive_empty} párrafos vacíos consecutivos",
                        p_idx=i - 1,
                    )
                consecutive_empty = 0

        # 2. DOBLE ESPACIO (MENOS AGRESIVO)
        # Detectamos párrafos con espacios múltiples y los reportamos como WARNING.
        # Excluimos encabezados, portadas, tablas, dedicatorias, agradecimientos y firmas.
        double_space_count = 0
        for i, p in enumerate(self.paragraphs):
            txt = p["text"]
            if not txt or len(txt.strip()) < 10:
                continue
            if p.get("is_cover") or p.get("in_table") or p.get("is_heading"):
                continue
            
            # Excluir secciones de formato especial
            p_sec = str(p.get("section") or "").upper()
            if any(k in p_sec for k in ["DEDICATORIA", "AGRADECIMIENTO", "ANEXO", "FIRMA"]):
                continue

            # Zona de índice: pueden haber dobles espacios por alineación con tabs/puntos
            if self.last_index_idx != -1 and i <= self.last_index_idx:
                continue

            # Verificar si hay 3+ espacios consecutivos o más de 2 ocurrencias de doble espacio
            has_triple_space = "   " in txt
            double_space_occurrences = txt.count("  ")
            
            if (has_triple_space or double_space_occurrences > 2) and "\t" not in txt[:80]:
                double_space_count += 1
                self._add(
                    "Estilo y Escritura",
                    "Espacios múltiples detectados",
                    "warning",
                    "Se detectaron múltiples espacios consecutivos en este párrafo. Esto "
                    "puede afectar la legibilidad del documento. Use buscar y reemplazar "
                    "(Ctrl+H) para limpiar el espaciado doble sobrante.",
                    "Un solo espacio entre palabras",
                    f"Espacios múltiples detectados ({double_space_occurrences} dobles espacios)",
                    p_idx=i,
                    p_text=txt.strip()[:60],
                )
                # Limitar a 30 reportes para no saturar
                if double_space_count >= 30:
                    self._add(
                        "Estilo y Escritura",
                        "Espacios múltiples (otros)",
                        "warning",
                        f"Se detectaron espacios múltiples en más párrafos no listados aquí. "
                        f"Total inicial reportado: {double_space_count}. Use Ctrl+H para "
                        f"reemplazar todos los dobles espacios de una sola vez.",
                        "Un solo espacio entre palabras",
                        "Múltiples párrafos afectados",
                    )
                    break

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
            if len(txt) > 15 and not p.get('in_table') and not p.get('is_formula_explanation'):
                run_nlp = False
                if nlp_calls < 80:
                    run_nlp = True
                    nlp_calls += 1

                alerts = linguistic.analyze_paragraph(p["text"], run_nlp=run_nlp)

                # Excluir punto final en títulos, Dedicatoria, Agradecimientos e Índice
                is_in_index = False
                if self.index_start_idx != -1 and self.last_index_idx != -1:
                    if self.index_start_idx <= i <= self.last_index_idx:
                        is_in_index = True

                p_sec_norm = self._norm(p.get("section", ""))
                if (p.get("is_heading") or "DEDICATORIA" in p_sec_norm
                        or "AGRADECIMIENTOS" in p_sec_norm
                        or is_in_index or "INDICE" in p_sec_norm):
                    alerts = [a for a in alerts if "punto final" not in a]

                if alerts:
                    count += 1
                    for alert in alerts:
                        self._add("Estilo y Escritura", "Sugerencia Lingüística", "warning", alert, p_idx=i, p_text=txt)
