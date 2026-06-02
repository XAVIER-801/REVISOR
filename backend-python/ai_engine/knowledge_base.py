"""
knowledge_base.py - Base de conocimiento persistente del REVISOR.

Almacena en JSON:
- Patrones de errores observados en tesis previas
- Estadísticas por categoría / escuela / facultad
- Sugerencias generadas
- Corpus de auditorías históricas

Sin servicios externos. Todo en archivos JSON locales.
"""
import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class KnowledgeBase:
    """
    Base de conocimiento persistente basada en archivos JSON.

    Estructura:
        knowledge/
            error_patterns.json   ← {rule_id: {count, examples, severity_distribution}}
            thesis_corpus.json    ← lista de auditorías históricas (resumen)
            suggestions.json      ← sugerencias generadas
            metadata.json         ← metadatos de la base
    """

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = os.path.join(os.path.dirname(__file__), "knowledge")
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.patterns_file = self.base_dir / "error_patterns.json"
        self.corpus_file = self.base_dir / "thesis_corpus.json"
        self.suggestions_file = self.base_dir / "suggestions.json"
        self.metadata_file = self.base_dir / "metadata.json"

        self._init_files()

    def _init_files(self):
        """Crea los archivos JSON si no existen."""
        defaults = {
            self.patterns_file: {},
            self.corpus_file: [],
            self.suggestions_file: [],
            self.metadata_file: {
                "created": datetime.now().isoformat(),
                "total_thesis": 0,
                "last_update": datetime.now().isoformat(),
                "version": "0.1.0",
            },
        }
        for path, default in defaults.items():
            if not path.exists():
                self._save_json(path, default)

    # ── Carga/Guardado ────────────────────────────────────────────────────

    def _load_json(self, path: Path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _save_json(self, path: Path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ── API principal ─────────────────────────────────────────────────────

    def record_audit(self, audit_results: Dict, metadata: Dict = None) -> str:
        """
        Registra una auditoría completa en la base de conocimiento.

        audit_results = {
            "stats": {"score": 75, "errors": 12, "warnings": 8, "passed": 50},
            "results": [{"category": "...", "rule": "...", "status": "...", ...}, ...]
        }
        metadata = {
            "filename": "tesis_xxx.docx",
            "school": "Sociología",   # opcional
            "faculty": "Ciencias Sociales",  # opcional
        }

        Retorna: hash único de esta auditoría.
        """
        metadata = metadata or {}
        results = audit_results.get("results", [])
        stats = audit_results.get("stats", {})

        # Hash único basado en filename + timestamp
        audit_id = hashlib.sha1(
            f"{metadata.get('filename', '')}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        # 1. Actualizar patrones de error
        self._update_patterns(results)

        # 2. Agregar al corpus (resumen, no detalle completo)
        self._append_to_corpus({
            "id": audit_id,
            "timestamp": datetime.now().isoformat(),
            "filename": metadata.get("filename", ""),
            "school": metadata.get("school", ""),
            "faculty": metadata.get("faculty", ""),
            "score": stats.get("score", 0),
            "errors": stats.get("errors", 0),
            "warnings": stats.get("warnings", 0),
            "passed": stats.get("passed", 0),
            "total_observations": len(results),
        })

        # 3. Actualizar metadata
        meta = self._load_json(self.metadata_file) or {}
        meta["total_thesis"] = meta.get("total_thesis", 0) + 1
        meta["last_update"] = datetime.now().isoformat()
        self._save_json(self.metadata_file, meta)

        return audit_id

    def _update_patterns(self, results: List[Dict]):
        """Actualiza estadísticas de patrones de error."""
        patterns = self._load_json(self.patterns_file) or {}

        for r in results:
            if r.get("status") == "passed":
                continue
            rule = r.get("rule", "?")
            category = r.get("category", "?")
            status = r.get("status", "?")
            key = f"{category}::{rule}"

            if key not in patterns:
                patterns[key] = {
                    "rule": rule,
                    "category": category,
                    "count": 0,
                    "error_count": 0,
                    "warning_count": 0,
                    "first_seen": datetime.now().isoformat(),
                    "examples": [],  # últimos 5 ejemplos de "actual" diferentes
                }

            p = patterns[key]
            p["count"] += 1
            if status == "error":
                p["error_count"] += 1
            elif status == "warning":
                p["warning_count"] += 1

            # Capturar ejemplos diversos (max 5)
            actual = str(r.get("actual", ""))[:120]
            if actual and actual not in p["examples"] and len(p["examples"]) < 5:
                p["examples"].append(actual)

            p["last_seen"] = datetime.now().isoformat()

        self._save_json(self.patterns_file, patterns)

    def _append_to_corpus(self, entry: Dict):
        corpus = self._load_json(self.corpus_file) or []
        corpus.append(entry)
        # Mantener máximo 5000 registros (FIFO)
        if len(corpus) > 5000:
            corpus = corpus[-5000:]
        self._save_json(self.corpus_file, corpus)

    # ── Consultas analíticas ──────────────────────────────────────────────

    def top_errors(self, n: int = 10) -> List[Dict]:
        """Retorna los N errores más frecuentes en el corpus."""
        patterns = self._load_json(self.patterns_file) or {}
        sorted_patterns = sorted(
            patterns.values(), key=lambda x: x["count"], reverse=True
        )
        return sorted_patterns[:n]

    def stats_by_category(self) -> Dict:
        """Estadísticas agregadas por categoría."""
        patterns = self._load_json(self.patterns_file) or {}
        agg = {}
        for p in patterns.values():
            cat = p.get("category", "?")
            if cat not in agg:
                agg[cat] = {"count": 0, "rules": 0, "errors": 0, "warnings": 0}
            agg[cat]["count"] += p.get("count", 0)
            agg[cat]["rules"] += 1
            agg[cat]["errors"] += p.get("error_count", 0)
            agg[cat]["warnings"] += p.get("warning_count", 0)
        return agg

    def average_score(self, school: str = None, faculty: str = None) -> float:
        """Promedio de score de tesis procesadas (opcionalmente filtrado)."""
        corpus = self._load_json(self.corpus_file) or []
        if school:
            corpus = [c for c in corpus if c.get("school", "").lower() == school.lower()]
        if faculty:
            corpus = [c for c in corpus if c.get("faculty", "").lower() == faculty.lower()]
        if not corpus:
            return 0.0
        return round(sum(c.get("score", 0) for c in corpus) / len(corpus), 2)

    def total_thesis(self) -> int:
        meta = self._load_json(self.metadata_file) or {}
        return meta.get("total_thesis", 0)

    # ── ESTADÍSTICAS CURIOSAS (para dashboard) ────────────────────────────

    def ranking_schools(self, min_thesis: int = 1, limit: int = 20) -> list:
        """
        Ranking de escuelas profesionales por puntaje promedio.
        Solo escuelas con >= min_thesis tesis registradas.
        """
        corpus = self._load_json(self.corpus_file) or []
        by_school = {}
        for c in corpus:
            school = (c.get("school") or "").strip()
            if not school:
                continue
            if school not in by_school:
                by_school[school] = {"scores": [], "errors": 0, "faculty": c.get("faculty", "")}
            by_school[school]["scores"].append(c.get("score", 0))
            by_school[school]["errors"] += c.get("errors", 0)

        ranking = []
        for school, data in by_school.items():
            if len(data["scores"]) < min_thesis:
                continue
            ranking.append({
                "school": school,
                "faculty": data["faculty"],
                "thesis_count": len(data["scores"]),
                "avg_score": round(sum(data["scores"]) / len(data["scores"]), 2),
                "total_errors": data["errors"],
                "avg_errors": round(data["errors"] / len(data["scores"]), 2),
            })
        ranking.sort(key=lambda x: x["avg_score"], reverse=True)
        return ranking[:limit]

    def ranking_faculties(self, min_thesis: int = 1) -> list:
        """Ranking de facultades por puntaje promedio."""
        corpus = self._load_json(self.corpus_file) or []
        by_faculty = {}
        for c in corpus:
            faculty = (c.get("faculty") or "").strip()
            if not faculty:
                continue
            if faculty not in by_faculty:
                by_faculty[faculty] = {"scores": [], "errors": 0, "warnings": 0}
            by_faculty[faculty]["scores"].append(c.get("score", 0))
            by_faculty[faculty]["errors"] += c.get("errors", 0)
            by_faculty[faculty]["warnings"] += c.get("warnings", 0)

        ranking = []
        for faculty, data in by_faculty.items():
            if len(data["scores"]) < min_thesis:
                continue
            ranking.append({
                "faculty": faculty,
                "thesis_count": len(data["scores"]),
                "avg_score": round(sum(data["scores"]) / len(data["scores"]), 2),
                "total_errors": data["errors"],
                "total_warnings": data["warnings"],
            })
        ranking.sort(key=lambda x: x["avg_score"], reverse=True)
        return ranking

    def errors_by_category(self) -> dict:
        """Distribución total de errores por categoría en todo el corpus."""
        patterns = self._load_json(self.patterns_file) or {}
        out = {}
        for p in patterns.values():
            cat = p.get("category", "Otros")
            if cat not in out:
                out[cat] = {"errors": 0, "warnings": 0, "total": 0, "unique_rules": 0}
            out[cat]["errors"] += p.get("error_count", 0)
            out[cat]["warnings"] += p.get("warning_count", 0)
            out[cat]["total"] += p.get("count", 0)
            out[cat]["unique_rules"] += 1
        return out

    def top_errors_by_school(self, school: str, n: int = 10) -> list:
        """Top N errores más recurrentes en una escuela específica."""
        # Esta lectura requiere reconstruir del corpus + patterns
        # Para simplificar: retornamos top global filtrado por escuela si hay
        # suficientes datos
        corpus = self._load_json(self.corpus_file) or []
        school_thesis = [
            c for c in corpus if (c.get("school") or "").lower() == school.lower()
        ]
        if not school_thesis:
            return []
        # Por ahora retornamos top global como aproximación
        return self.top_errors(n)

    def writing_quality_ranking(self, limit: int = 10) -> list:
        """
        Ranking de escuelas por CALIDAD DE REDACCIÓN (basado en errores de las
        categorías Estilo y Escritura + Ortografía).
        """
        corpus = self._load_json(self.corpus_file) or []
        by_school = {}
        for c in corpus:
            school = (c.get("school") or "").strip()
            if not school:
                continue
            if school not in by_school:
                by_school[school] = {"thesis": 0, "score_sum": 0, "faculty": c.get("faculty", "")}
            by_school[school]["thesis"] += 1
            by_school[school]["score_sum"] += c.get("score", 0)

        ranking = [
            {
                "school": school,
                "faculty": data["faculty"],
                "thesis_count": data["thesis"],
                "avg_score": round(data["score_sum"] / data["thesis"], 2),
            }
            for school, data in by_school.items()
            if data["thesis"] >= 1
        ]
        ranking.sort(key=lambda x: x["avg_score"], reverse=True)
        return ranking[:limit]

    def curiosities(self) -> dict:
        """Estadísticas curiosas e interesantes del corpus."""
        corpus = self._load_json(self.corpus_file) or []
        patterns = self._load_json(self.patterns_file) or {}
        meta = self._load_json(self.metadata_file) or {}

        if not corpus:
            return {"total_thesis": 0, "message": "Aún no hay tesis en el corpus"}

        scores = [c.get("score", 0) for c in corpus]
        total_errors = sum(c.get("errors", 0) for c in corpus)
        total_warnings = sum(c.get("warnings", 0) for c in corpus)

        # Tesis con mejor y peor score
        best = max(corpus, key=lambda c: c.get("score", 0))
        worst = min(corpus, key=lambda c: c.get("score", 0))

        # Categoría más problemática del corpus
        cat_stats = self.errors_by_category()
        most_problematic_cat = (
            max(cat_stats.items(), key=lambda x: x[1]["errors"])[0]
            if cat_stats else "—"
        )

        # Regla más violada
        most_violated = (
            max(patterns.values(), key=lambda p: p.get("count", 0))
            if patterns else None
        )

        # Distribución por facultad
        faculty_counts = {}
        for c in corpus:
            f = c.get("faculty") or "Desconocida"
            faculty_counts[f] = faculty_counts.get(f, 0) + 1

        # Score promedio por facultad
        faculty_scores = {}
        for c in corpus:
            f = c.get("faculty") or "Desconocida"
            faculty_scores.setdefault(f, []).append(c.get("score", 0))
        avg_by_faculty = {
            f: round(sum(s) / len(s), 1) for f, s in faculty_scores.items()
        }

        return {
            "total_thesis": len(corpus),
            "global_avg_score": round(sum(scores) / len(scores), 2),
            "median_score": sorted(scores)[len(scores) // 2],
            "min_score": min(scores),
            "max_score": max(scores),
            "total_errors_across_corpus": total_errors,
            "total_warnings_across_corpus": total_warnings,
            "avg_errors_per_thesis": round(total_errors / len(corpus), 1),
            "best_thesis": {
                "filename": best.get("filename"),
                "school": best.get("school"),
                "score": best.get("score"),
            },
            "worst_thesis": {
                "filename": worst.get("filename"),
                "school": worst.get("school"),
                "score": worst.get("score"),
            },
            "most_problematic_category": most_problematic_cat,
            "most_violated_rule": {
                "rule": most_violated.get("rule") if most_violated else "—",
                "category": most_violated.get("category") if most_violated else "—",
                "count": most_violated.get("count") if most_violated else 0,
            },
            "faculty_distribution": faculty_counts,
            "avg_score_by_faculty": avg_by_faculty,
            "last_updated": meta.get("last_update"),
        }
