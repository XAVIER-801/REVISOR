"""
base_auditor.py - Clase base para todos los auditores modulares.

Provee acceso compartido a:
- self.paragraphs: lista de párrafos extraídos del documento
- self.resolver: resolutor de estilos
- self.stats / self.results: acumuladores de resultados
- self._add(): método para registrar observaciones
- self._norm() / self._norm_alphanumeric(): normalización de texto
- self._get_p_props(): extracción de propiedades de un párrafo
- self.anexos_start_idx / self.last_index_idx / self.index_start_idx: límites calculados
"""
import re
import unicodedata


class BaseAuditor:
    """Clase base que todos los auditores heredan. 
    Recibe una referencia al engine principal para acceder a datos compartidos."""

    def __init__(self, engine):
        self.engine = engine

    # ── Accesos directos a datos del engine ──────────────────────────────
    @property
    def paragraphs(self):
        return self.engine.paragraphs

    @property
    def resolver(self):
        return self.engine.resolver

    @property
    def sections_found(self):
        return self.engine.sections_found

    @property
    def anexos_start_idx(self):
        return self.engine.anexos_start_idx

    @anexos_start_idx.setter
    def anexos_start_idx(self, val):
        self.engine.anexos_start_idx = val

    @property
    def last_index_idx(self):
        return getattr(self.engine, 'last_index_idx', -1)

    @property
    def index_start_idx(self):
        return getattr(self.engine, 'index_start_idx', -1)

    # ── Métodos compartidos ──────────────────────────────────────────────
    def _add(self, cat, rule, status, msg, expected="", actual="", p_idx=None, p_text="", page=None, section=None):
        """Registra una observación de auditoría en el engine principal."""
        self.engine._add(cat, rule, status, msg, expected, actual, p_idx, p_text, page, section)

    def _norm(self, t):
        if not t: return ""
        return unicodedata.normalize('NFD', t).encode('ascii', 'ignore').decode('ascii').upper().strip()

    def _norm_alphanumeric(self, t):
        n = self._norm(t)
        return re.sub(r'[^A-Z0-9]', '', n)

    def _get_p_props(self, p):
        if not p["runs"]: return 12, False, False, "Times New Roman"
        for r in p["runs"]:
            if r["text"].strip():
                return r["size"], r["bold"], r["italic"], r["font"]
        return 12, False, False, "Times New Roman"

    def audit(self):
        """Método principal que cada auditor debe implementar."""
        raise NotImplementedError("Cada auditor debe implementar audit()")
