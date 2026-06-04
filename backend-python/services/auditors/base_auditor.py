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

    def _is_meaningfully_bold(self, paragraph, threshold: float = 0.5):
        """
        Determina si un párrafo está en negrita basándose en la MAYORÍA de los
        caracteres ALFANUMÉRICOS visibles (no en cualquier run insignificante).

        Esto evita falsos positivos cuando solo un espacio, signo de puntuación
        o run vacío tiene la marca bold pero el texto visible no lo está.

        Args:
            paragraph: dict con 'runs' (cada uno con 'text' y 'bold')
            threshold: proporción mínima de caracteres en negrita para considerar
                       el párrafo como "bold" (default 0.5 = mayoría)

        Returns:
            True si el párrafo es perceptiblemente negrita.
        """
        total_chars = 0
        bold_chars = 0
        for r in paragraph.get('runs', []):
            text = r.get('text', '') or ''
            for c in text:
                if c.isalnum():
                    total_chars += 1
                    if r.get('bold'):
                        bold_chars += 1
        if total_chars == 0:
            return False
        return (bold_chars / total_chars) >= threshold

    def _is_meaningfully_italic(self, paragraph, threshold: float = 0.5):
        """Análogo a _is_meaningfully_bold pero para cursiva."""
        total_chars = 0
        italic_chars = 0
        for r in paragraph.get('runs', []):
            text = r.get('text', '') or ''
            for c in text:
                if c.isalnum():
                    total_chars += 1
                    if r.get('italic'):
                        italic_chars += 1
        if total_chars == 0:
            return False
        return (italic_chars / total_chars) >= threshold

    def _has_any_bold_word(self, paragraph, min_word_len: int = 2):
        """
        Indica si HAY al menos una PALABRA completa (≥ min_word_len caracteres)
        en negrita en el párrafo. Útil para casos donde una sola palabra resaltada
        sí debe contar como error.
        """
        for r in paragraph.get('runs', []):
            if not r.get('bold'):
                continue
            text = (r.get('text', '') or '').strip()
            # Contar caracteres alfanuméricos seguidos
            current_run = 0
            for c in text:
                if c.isalnum():
                    current_run += 1
                    if current_run >= min_word_len:
                        return True
                else:
                    current_run = 0
        return False

    def _find_context_level(self, paragraph_index, max_distance=150):
        """
        Busca hacia atrás desde paragraph_index para encontrar el último nivel de título.
        Retorna el nivel efectivo (1-5) del contexto más próximo.

        Busca en orden de prioridad:
        1. Párrafos marcados como is_heading=True (tienen body_level calculado)
        2. Párrafos con numeración manual (1.2.3...)
        3. Párrafos detectados como CAPÍTULO, INTRODUCCIÓN, etc.

        Si no encuentra nada, retorna 1 (nivel por defecto).
        """
        for k in range(paragraph_index - 1, max(0, paragraph_index - max_distance), -1):
            p = self.paragraphs[k]

            # Opción 1: Título con heading marcado (body_level ya está calculado)
            if p.get('is_heading', False):
                level = p.get('body_level', 1)
                if level > 0:
                    return level

            # Opción 2: Numeración manual (1.2.3)
            norm_txt = self._norm(p['text'].strip())
            numbering_match = re.match(r'^(\d+(?:\.\d+)+)', norm_txt)
            if numbering_match:
                numbering_level = numbering_match.group(1).count('.') + 1
                if 1 <= numbering_level <= 5:
                    return numbering_level

            # Opción 3: CAPÍTULO X o sección principal
            if any(k in norm_txt for k in ['CAPITULO', 'INTRODUCCION', 'CONCLUSIONES']):
                return 1

        return 1

    # ── Métodos para interactuar con el AST (Document Tree) ──────────────
    
    @property
    def document_tree(self):
        return getattr(self.engine, 'document_tree', None)

    def get_paragraphs_in_node(self, node_title, exact=False):
        """
        Busca un nodo en el AST por su título y devuelve todos los párrafos 
        comprendidos en su rango de índices.
        """
        if not self.document_tree:
            return []

        def _search(node):
            if exact:
                if node["title"] == node_title: return node
            else:
                if node_title in node["title"]: return node
            for child in node["children"]:
                res = _search(child)
                if res: return res
            return None

        target_node = _search(self.document_tree)
        if target_node and target_node["start_idx"] != -1 and target_node["end_idx"] != -1:
            return self.paragraphs[target_node["start_idx"]:target_node["end_idx"] + 1]
        return []

    def get_ast_path(self, paragraph_index):
        """
        Devuelve la ruta de títulos (jerarquía) a la que pertenece un párrafo.
        Útil para saber si un párrafo está dentro de "Anexos", "Capítulo 1", etc.
        """
        if not self.document_tree:
            return []

        path = []
        def _traverse(node):
            if node["start_idx"] <= paragraph_index <= node["end_idx"]:
                path.append(node["title"])
                for child in node["children"]:
                    _traverse(child)
        
        _traverse(self.document_tree)
        return path

    def audit(self):
        """Método principal que cada auditor debe implementar."""
        raise NotImplementedError("Cada auditor debe implementar audit()")
