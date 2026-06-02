"""
learning_system.py - Sistema de aprendizaje progresivo del REVISOR.

Este NO es deep learning ni LLM. Es **inteligencia estadística aplicada**:
mientras más tesis se procesan, mejor entiende qué errores son comunes,
qué escuelas tienen más problemas, qué sugerencias dar.

Flujo:
1. ingest(audit_results, metadata) → registra la auditoría en knowledge_base
2. suggest_improvements(audit_results, metadata) → genera sugerencias basadas en patrones aprendidos
3. global_insights() → reporte general del corpus acumulado

Sin servicios externos. Todo localmente.
"""
from typing import Dict, List
from .knowledge_base import KnowledgeBase


class LearningSystem:
    """
    Sistema de aprendizaje progresivo basado en estadísticas del corpus.

    Uso:
        ls = LearningSystem()
        ls.ingest(audit_results, {"filename": "tesis.docx", "school": "Sociología"})
        suggestions = ls.suggest_improvements(audit_results, metadata)
        # suggestions es lista de strings o dicts con sugerencias contextuales
    """

    def __init__(self):
        self.kb = KnowledgeBase()

    # ── Ingestión ─────────────────────────────────────────────────────────

    def ingest(self, audit_results: Dict, metadata: Dict = None) -> str:
        """Registra esta auditoría para aprender de ella en el futuro."""
        return self.kb.record_audit(audit_results, metadata or {})

    # ── Sugerencias ───────────────────────────────────────────────────────

    def suggest_improvements(
        self,
        audit_results: Dict = None,
        metadata: Dict = None
    ) -> List[Dict]:
        """
        Genera sugerencias contextuales basadas en patrones aprendidos.

        Tipos de sugerencias generadas:
        1. "Top error global": el error más frecuente en el corpus completo
        2. "Top error en tu escuela": si se pasa metadata.school
        3. "Patrón en tu auditoría": coincidencias entre errores del usuario y top globales
        4. "Mejora rápida": errores con muchos ejemplos diversos → sugiere revisión sistemática
        """
        suggestions = []
        total = self.kb.total_thesis()

        if total < 3:
            suggestions.append({
                "type": "info",
                "title": "Sistema en aprendizaje",
                "message": (
                    f"El sistema ha procesado {total} tesis hasta el momento. "
                    "Las sugerencias serán más precisas con cada nueva auditoría."
                ),
            })
            return suggestions

        # 1. Top 3 errores globales
        top = self.kb.top_errors(3)
        if top:
            suggestions.append({
                "type": "global_pattern",
                "title": f"Los {len(top)} errores más comunes en {total} tesis procesadas:",
                "items": [
                    {
                        "rule": p["rule"],
                        "category": p["category"],
                        "frequency": p["count"],
                        "tip": self._tip_for_rule(p["rule"]),
                    }
                    for p in top
                ],
            })

        # 2. Si el usuario tiene errores que coinciden con los top globales
        if audit_results:
            user_errors = {
                r.get("rule") for r in audit_results.get("results", [])
                if r.get("status") in ("error", "warning")
            }
            top_rules = {p["rule"] for p in self.kb.top_errors(10)}
            common_with_user = user_errors & top_rules
            if common_with_user:
                suggestions.append({
                    "type": "personal_match",
                    "title": "Tus errores coinciden con problemas frecuentes",
                    "message": (
                        "Los siguientes errores que detectamos en tu tesis son MUY comunes "
                        "en otras tesis. Solucionarlos elevará tu calidad considerablemente:"
                    ),
                    "rules": list(common_with_user)[:5],
                })

        # 3. Promedio del corpus
        avg = self.kb.average_score()
        if avg > 0 and audit_results:
            user_score = audit_results.get("stats", {}).get("score", 0)
            diff = user_score - avg
            if diff > 5:
                suggestions.append({
                    "type": "comparison",
                    "title": "Tu tesis está por encima del promedio",
                    "message": (
                        f"Tu puntaje ({user_score}) está {abs(diff):.0f} puntos por encima "
                        f"del promedio del corpus ({avg:.0f}). ¡Excelente trabajo!"
                    ),
                })
            elif diff < -5:
                suggestions.append({
                    "type": "comparison",
                    "title": "Margen de mejora",
                    "message": (
                        f"Tu puntaje ({user_score}) está {abs(diff):.0f} puntos por debajo "
                        f"del promedio del corpus ({avg:.0f}). Revise los errores prioritarios."
                    ),
                })

        # 4. Stats por categoría
        cat_stats = self.kb.stats_by_category()
        if cat_stats:
            top_cat = sorted(
                cat_stats.items(),
                key=lambda x: x[1]["errors"],
                reverse=True
            )[:1]
            if top_cat:
                cat_name, cat_data = top_cat[0]
                suggestions.append({
                    "type": "category_alert",
                    "title": f"Categoría más problemática: {cat_name}",
                    "message": (
                        f"En el corpus acumulado, la categoría '{cat_name}' acumula "
                        f"{cat_data['errors']} errores totales. Presta atención especial "
                        f"a esta área."
                    ),
                })

        return suggestions

    # ── Insights globales ─────────────────────────────────────────────────

    def global_insights(self) -> Dict:
        """Reporte agregado del corpus completo."""
        return {
            "total_thesis": self.kb.total_thesis(),
            "average_score": self.kb.average_score(),
            "top_10_errors": self.kb.top_errors(10),
            "stats_by_category": self.kb.stats_by_category(),
        }

    # ── Tips heurísticos por regla ────────────────────────────────────────

    def _tip_for_rule(self, rule: str) -> str:
        """Genera un tip humano para una regla específica."""
        rule_lower = rule.lower()
        if "interlineado" in rule_lower:
            return ("Selecciona todo el texto del cuerpo y aplica interlineado 2.0 "
                    "desde Diseño de Página → Espaciado.")
        if "sangría" in rule_lower or "sangria" in rule_lower:
            return ("Verifica las sangrías en el panel de Estilos. La sangría correcta "
                    "depende del nivel del título al que pertenece el texto.")
        if "espaciado" in rule_lower or "spacing" in rule_lower:
            return ("Configura el espaciado anterior (0pt) y posterior (10pt) en "
                    "Diseño de Página → Espaciado.")
        if "negrita" in rule_lower or "bold" in rule_lower:
            return "Usa Ctrl+B para activar/desactivar negrita en el texto seleccionado."
        if "tabla" in rule_lower or "figura" in rule_lower:
            return ("Las etiquetas (Tabla N, Figura N) van en negrita y 12pt, "
                    "los títulos en cursiva sin negrita, y las notas en 10pt.")
        if "viñeta" in rule_lower or "vineta" in rule_lower:
            return ("Solo se permiten viñetas con guion (-), punto (•) o numeración "
                    "alfanumérica (a., 1.). Evita símbolos decorativos como ➢, ❑, ✓.")
        if "tilde" in rule_lower:
            return "Asegúrate de escribir 'CAPÍTULO' y 'TÍTULO' con tilde."
        if "palabras clave" in rule_lower or "keywords" in rule_lower:
            return ("Las palabras clave deben ir separadas por comas, ordenadas "
                    "alfabéticamente, y con primera letra mayúscula.")
        return "Consulte la guía oficial para esta regla específica."
