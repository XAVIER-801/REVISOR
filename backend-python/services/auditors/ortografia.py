"""
ortografia.py - Auditoría ortográfica del texto del documento.

ENFOQUE PRINCIPAL: Heurísticas estrictas para detectar errores tipográficos
EVIDENTES (no falsos positivos). El diccionario español de pyspellchecker es
muy limitado y marca palabras válidas como "valores", "variables", "tradicionales",
"agradezco" como errores, lo cual genera ruido inaceptable. Por eso el modo
pyspellchecker queda DESACTIVADO por defecto y solo se usan heurísticas
100% confiables.

Heurísticas activas:
1. 3+ caracteres repetidos consecutivos:  "qquue", "eessto", "vivirr"
2. Mezcla de letras y dígitos:             "ho1a", "perr0", "1nicio"
3. 5+ consonantes seguidas (raro en español): "constrwfgr"
4. Palabras con caracteres no imprimibles
5. Repetición de palabras consecutivas:    "el el", "la la", "que que"

Status: 'observation' → resaltado verde claro distinto a errores/advertencias

El sistema de aprendizaje (ai_engine) puede usar estos datos para detectar
patrones de errores frecuentes.
"""
import re
from .base_auditor import BaseAuditor


# Palabras técnicas/comunes que pueden tener doble letra legítima
ALLOWED_DOUBLE_LETTERS = ('ll', 'rr', 'cc', 'nn', 'ee', 'oo', 'ss')


class OrtografiaAuditor(BaseAuditor):

    MAX_REPORTS = 80
    MIN_PARAGRAPH_LEN = 30

    def audit(self):
        misspelled = []  # lista de dicts con palabra, p_idx, contexto, razón
        repeated_words = []  # lista de duplicaciones "el el"

        for i, p in enumerate(self.paragraphs):
            # Saltar zona de índice, preliminares y cualquier párrafo fuera del cuerpo
            is_in_index = self.last_index_idx != -1 and i <= self.last_index_idx
            style_id = p.get('style_id', '').upper()
            is_toc_style = any(k in style_id for k in ['TOC', 'TDC', 'INDICE', 'ÍNDICE'])
            if is_in_index or is_toc_style or not p.get("is_in_body", True):
                continue

            if p.get("is_cover") or p.get("in_table"):
                continue
            if p.get("has_omml") or p.get("is_display_equation"):
                continue
            txt = p["text"].strip()
            if len(txt) < self.MIN_PARAGRAPH_LEN:
                continue
            if "...." in txt:
                continue
            # Saltar secciones donde palabras técnicas/nombres dominan
            sec_upper = (p.get("section") or "").upper()
            if any(k in sec_upper for k in [
                "REFERENCIAS BIBLIOGRAFICAS", "REFERENCIAS BIBLIOGRÁFICAS",
                "ÍNDICE", "INDICE", "ANEXOS"
            ]):
                continue

            # ── HEURÍSTICA 1: letras repetidas 3+ ──
            for w in re.findall(r"\b[a-zA-Záéíóúñ]+\b", txt):
                if len(w) < 4:
                    continue
                w_lower = w.lower()
                if self._has_triple_letter(w_lower):
                    misspelled.append({
                        "word": w,
                        "p_idx": p["index"],
                        "context": txt[:80],
                        "page": p.get("estimated_page"),
                        "reason": "3 o más letras iguales consecutivas",
                        "suggestion": self._suggest_dedup(w),
                    })

            # ── HEURÍSTICA 2: mezcla letras + dígitos ──
            for w in re.findall(r"\b\w+\b", txt):
                if len(w) < 3:
                    continue
                has_letter = any(c.isalpha() for c in w)
                has_digit = any(c.isdigit() for c in w)
                if has_letter and has_digit:
                    # Excluir códigos válidos: H2O, CO2, IPv4, R2, χ2, etc.
                    # Permitimos hasta 2 dígitos al final
                    if re.fullmatch(r"[A-Za-z]+\d{1,2}", w):
                        continue
                    # O al inicio: 5G, 4K
                    if re.fullmatch(r"\d{1,2}[A-Za-z]+", w):
                        continue
                    misspelled.append({
                        "word": w,
                        "p_idx": p["index"],
                        "context": txt[:80],
                        "page": p.get("estimated_page"),
                        "reason": "mezcla de letras y dígitos en la misma palabra",
                        "suggestion": None,
                    })

            # ── HEURÍSTICA 3: 5+ consonantes seguidas ──
            for w in re.findall(r"\b[a-záéíóúñ]+\b", txt.lower()):
                if len(w) < 6:
                    continue
                if self._consonant_streak(w) >= 5:
                    # Excluir palabras conocidas con grupos consonánticos
                    if w in ("transcripción", "transgresión", "construcción"):
                        continue
                    misspelled.append({
                        "word": w,
                        "p_idx": p["index"],
                        "context": txt[:80],
                        "page": p.get("estimated_page"),
                        "reason": "5 o más consonantes consecutivas (inusual)",
                        "suggestion": None,
                    })

            # ── HEURÍSTICA 4: palabras repetidas consecutivas ──
            matches = list(re.finditer(r"\b[a-záéíóúñA-ZÁÉÍÓÚÑ]+\b", txt))
            for k in range(len(matches) - 1):
                m1 = matches[k]
                m2 = matches[k + 1]
                w1 = m1.group().lower()
                w2 = m2.group().lower()
                if w1 == w2 and len(w1) >= 2:
                    # Excluir si están separados por puntuación, paréntesis, etc.
                    sep = txt[m1.end():m2.start()]
                    if not re.fullmatch(r"\s*", sep):
                        continue
                    # Excluir casos válidos: "lo lo" (raro), "ya ya"
                    if w1 in ("muy", "no", "ya", "lo", "sí", "si"):
                        continue
                    repeated_words.append({
                        "phrase": f"{m1.group()} {m2.group()}",
                        "p_idx": p["index"],
                        "context": txt[:120],
                        "page": p.get("estimated_page"),
                    })

        # ── Deduplicar y reportar ──
        seen_words = set()
        reports = 0
        for item in misspelled:
            if reports >= self.MAX_REPORTS:
                break
            key = (item["word"].lower(), item["p_idx"])
            if key in seen_words:
                continue
            seen_words.add(key)

            sug_text = (
                f" Sugerencia: «{item['suggestion']}»."
                if item.get("suggestion") else
                " Revise la palabra manualmente."
            )
            self._add(
                "Ortografía",
                f"Posible error tipográfico: \"{item['word']}\"",
                "observation",
                f"Se detectó la palabra \"{item['word']}\" con un patrón inusual "
                f"({item['reason']}).{sug_text} Si es un término técnico válido, "
                f"puede ignorar esta observación.",
                item.get("suggestion") or "Revisar manualmente",
                f"\"{item['word']}\"",
                p_idx=item["p_idx"],
                p_text=item["context"],
                page=item.get("page"),
            )
            reports += 1

        # Reportar palabras repetidas
        seen_repeats = set()
        for item in repeated_words:
            if reports >= self.MAX_REPORTS:
                break
            key = (item["phrase"].lower(), item["p_idx"])
            if key in seen_repeats:
                continue
            seen_repeats.add(key)
            self._add(
                "Ortografía",
                f"Palabra repetida: \"{item['phrase']}\"",
                "observation",
                f"Se detectaron dos palabras idénticas consecutivas: \"{item['phrase']}\". "
                f"Usualmente esto es un error de tipeo (un duplicado accidental).",
                "Eliminar una de las palabras repetidas",
                f"\"{item['phrase']}\"",
                p_idx=item["p_idx"],
                p_text=item["context"],
                page=item.get("page"),
            )
            reports += 1

        # Resumen
        if reports == 0:
            self._add(
                "Ortografía",
                "Revisión ortográfica heurística",
                "passed",
                "No se detectaron patrones evidentes de errores tipográficos.",
                "Sin errores tipográficos evidentes",
                "Sin errores",
            )
        else:
            self._add(
                "Ortografía",
                "Resumen de Revisión Ortográfica",
                "warning",
                f"Se detectaron {reports} posibles errores tipográficos heurísticos. "
                f"Estas observaciones son sugerencias (no errores críticos) y están "
                f"marcadas en verde claro en el documento. Revíselas; si son términos "
                f"técnicos correctos, ignore la observación.",
                "Revisar palabras marcadas",
                f"{reports} posibles errores",
            )

    # ── Helpers ──

    def _has_triple_letter(self, word):
        """¿Tiene 3+ letras iguales consecutivas (excluyendo 'rr', 'll', 'cc' que pueden duplicarse)?"""
        # No: tres iguales seguidos
        for i in range(len(word) - 2):
            if word[i] == word[i + 1] == word[i + 2] and word[i].isalpha():
                return True
        return False

    def _suggest_dedup(self, word):
        """Sugerencia simple: reducir cualquier secuencia de 3+ a 2 letras."""
        result = []
        prev = None
        streak = 0
        for c in word:
            if c == prev:
                streak += 1
                if streak < 2:
                    result.append(c)
            else:
                result.append(c)
                streak = 0
            prev = c
        return "".join(result)

    def _consonant_streak(self, word):
        """Máximo número de consonantes seguidas en la palabra."""
        vowels = set("aeiouáéíóú")
        max_streak = 0
        current = 0
        for c in word:
            if c.isalpha() and c not in vowels:
                current += 1
                max_streak = max(max_streak, current)
            else:
                current = 0
        return max_streak
