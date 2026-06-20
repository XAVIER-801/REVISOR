"""
espaciado_titulos_contenido.py - Auditoría CENTRALIZADA de espaciado.

Verifica que TODOS los títulos (N1-N5), contenido y viñetas en el cuerpo
del documento cumplan las reglas de espaciado anterior/posterior e interlineado
según la Guía UNAP (extraída de GUIA_FORMATO_PREMIUM.xlsx).

Reglas por tipo:
  CAPÍTULO X (N1, 16pt)      : sb=0, sa=5,  ls=2.0
  Intro/Rev (N1, 14pt)       : sb=0, sa=10, ls=2.0
  V.CONCLUSIONES/etc (N1,16pt): sb=0, sa=10, ls=2.0
  Nivel 2 (14pt)             : sb=0, sa=10, ls=2.0
  Nivel 3 (12pt)             : sb=0, sa=10, ls=2.0
  Nivel 4 (12pt)             : sb=0, sa=10, ls=2.0
  Nivel 5 (12pt)             : sb=0, sa=10, ls=2.0
  Contenido párrafo          : sb=0, sa=10, ls=2.0
  Viñeta intermedia          : sb=0, sa=0,  ls=2.0
  Última viñeta del bloque   : sb=0, sa=10, ls=2.0
"""
import re
from .base_auditor import BaseAuditor


# ─── REGLAS DE ESPACIADO ───────────────────────────────────────────────
# Cada regla: (name, sb_expected, sa_expected, ls_expected, tolerancia_sb, tolerancia_sa, tolerancia_ls)
# sb/spacing_before, sa/spacing_after en puntos, ls/line_spacing en factor (2.0 = doble)
# Tolerancias: sb y sa en pt; ls en factor

RULES = {
    "capitulo_x": {
        "name": "CAPÍTULO X (N1 16pt)",
        "sb": 0, "sa": 5, "ls": 2.0,
        "tol_sb": 1.0, "tol_sa": 1.0, "tol_ls": 0.2,
    },
    "titulo_capitulo_14pt": {
        "name": "Título Capítulo 14pt (Introducción, etc.)",
        "sb": 0, "sa": 10, "ls": 2.0,
        "tol_sb": 1.0, "tol_sa": 2.0, "tol_ls": 0.2,
    },
    "seccion_final_16pt": {
        "name": "Sección Final 16pt (Conclusiones, etc.)",
        "sb": 0, "sa": 10, "ls": 2.0,
        "tol_sb": 1.0, "tol_sa": 2.0, "tol_ls": 0.2,
    },
    "nivel2": {
        "name": "Nivel 2 (14pt)",
        "sb": 0, "sa": 10, "ls": 2.0,
        "tol_sb": 1.0, "tol_sa": 2.0, "tol_ls": 0.2,
    },
    "nivel3": {
        "name": "Nivel 3 (12pt)",
        "sb": 0, "sa": 10, "ls": 2.0,
        "tol_sb": 1.0, "tol_sa": 2.0, "tol_ls": 0.2,
    },
    "nivel4": {
        "name": "Nivel 4 (12pt)",
        "sb": 0, "sa": 10, "ls": 2.0,
        "tol_sb": 1.0, "tol_sa": 2.0, "tol_ls": 0.2,
    },
    "nivel5": {
        "name": "Nivel 5 (12pt)",
        "sb": 0, "sa": 10, "ls": 2.0,
        "tol_sb": 1.0, "tol_sa": 2.0, "tol_ls": 0.2,
    },
    "contenido": {
        "name": "Contenido (párrafo normal)",
        "sb": 0, "sa": 10, "ls": 2.0,
        "tol_sb": 1.0, "tol_sa": 2.0, "tol_ls": 0.2,
    },
    "vineta_intermedia": {
        "name": "Viñeta intermedia",
        "sb": 0, "sa": 0, "ls": 2.0,
        "tol_sb": 1.0, "tol_sa": 1.0, "tol_ls": 0.2,
    },
    "vineta_final": {
        "name": "Última viñeta del bloque",
        "sb": 0, "sa": 10, "ls": 2.0,
        "tol_sb": 1.0, "tol_sa": 2.0, "tol_ls": 0.2,
    },
}


class EspaciadoTitulosContenidoAuditor(BaseAuditor):

    def audit(self):
        for i, p in enumerate(self.paragraphs):
            if not p.get("is_in_body"):
                continue
            txt = p['text'].strip()
            if not txt:
                continue

            # Saltar índice y zonas de preliminares
            if self._is_in_index_or_prelim(i, p):
                continue

            # Saltar tablas, anexos, referencias
            if p.get('in_table'):
                continue
            if self.anexos_start_idx != -1 and i >= self.anexos_start_idx:
                continue
            sec_upper = p.get("section", "").upper()
            if "REFERENCIAS BIBLIOGRAFICAS" in sec_upper:
                continue

            norm = p['norm']
            rule_key, sub_type = self._classify(i, p, txt, norm)

            if rule_key is None:
                continue

            rule = RULES[rule_key]
            sb = p.get('spacing_before', 0)
            sa = p.get('spacing_after', 0)
            ls = p.get('line_spacing')

            # Validar spacing_before
            if abs(sb - rule["sb"]) > rule["tol_sb"]:
                self._add(
                    "Espaciado",
                    f"{rule['name']}: Espaciado anterior",
                    "error",
                    f"Debe tener espaciado anterior de {rule['sb']}pt "
                    f"(se tiene {sb:.1f}pt).",
                    f"{rule['sb']}pt", f"{sb:.1f}pt",
                    p_idx=p['index'], p_text=txt[:50],
                )

            # Validar spacing_after
            if abs(sa - rule["sa"]) > rule["tol_sa"]:
                self._add(
                    "Espaciado",
                    f"{rule['name']}: Espaciado posterior",
                    "error",
                    f"Debe tener espaciado posterior de {rule['sa']}pt "
                    f"(se tiene {sa:.1f}pt).",
                    f"{rule['sa']}pt", f"{sa:.1f}pt",
                    p_idx=p['index'], p_text=txt[:50],
                )

            # Validar interlineado (solo si está definido)
            if ls is not None and abs(ls - rule["ls"]) > rule["tol_ls"]:
                self._add(
                    "Espaciado",
                    f"{rule['name']}: Interlineado",
                    "error",
                    f"Debe tener interlineado {rule['ls']} (se tiene {ls}).",
                    str(rule['ls']), str(ls),
                    p_idx=p['index'], p_text=txt[:50],
                )

    # ─── CLASIFICACIÓN ───────────────────────────────────────────────────

    def _classify(self, i, p, txt, norm):
        """
        Determina la categoría de un párrafo y retorna (rule_key, sub_type).
        Retorna (None, None) si no aplica ninguna regla.
        """
        # 0. SALTAR FIGURAS, TABLAS, CUADROS, NOTAS, FUENTES
        # Estas tienen su propia auditoría en figuras.py / tablas.py y no deben
        # ser validadas con reglas de espaciado de contenido normal.
        if re.match(r'^(FIGURA|TABLA|CUADRO|GRAFICO|ILUSTRACION)\s+\d+', norm):
            return (None, None)
        if norm:
            first_word = norm.split(' ', 1)[0].rstrip(':')
            if first_word in ('NOTA', 'FUENTE'):
                return (None, None)
        if p.get('drawings') and len(p.get('drawings')) > 0:
            return (None, None)

        # Detectar si este párrafo es título descriptivo de figura/tabla
        # (párrafo inmediatamente después de una etiqueta FIGURA/TABLA N:)
        for k in range(i - 1, max(-1, i - 3), -1):
            prev_norm = self.paragraphs[k]['norm']
            if re.match(r'^(FIGURA|TABLA|CUADRO)\s+\d+', prev_norm):
                return (None, None)
            # Si el párrafo anterior tiene dibujos grandes, este podría ser título
            prev_drawings = self.paragraphs[k].get('drawings', [])
            if any(d.get('width', 0) >= 8.0 for d in prev_drawings):
                if len(txt) < 150:
                    return (None, None)

        bold = self._is_meaningfully_bold(p)
        align = p.get('alignment', 'left')
        size = p['runs'][0].get('size', 0) if p.get('runs') else 0
        is_bullet = self._es_vineta(p, txt)

        # 1. VIÑETAS → detectar si es intermedia o final del bloque
        if is_bullet:
            return self._clasifica_vineta(i, p)

        # 2. TÍTULOS NUMERADOS (1.1, 1.1.1, etc.) → detectar nivel
        numbering_match = re.match(r'^(\d+(?:\.\d+)+)\.?(?:[\s\t]+|$)', txt)
        if numbering_match:
            dot_count = numbering_match.group(1).count('.')
            nivel = dot_count + 1
            if nivel == 2:
                return ("nivel2", "n2_title")
            elif nivel == 3:
                return ("nivel3", "n3_title")
            elif nivel == 4:
                return ("nivel4", "n4_title")
            elif nivel >= 5:
                return ("nivel5", "n5_title")

        # 3. TÍTULOS POR NOMBRE
        # CAPÍTULO X
        if re.match(r"^CAP[ÍI]TULO\s+(I|V|X|L|C|[0-9]+)", norm):
            return ("capitulo_x", "capitulo")

        es_seccion_principal = any(k in norm for k in [
            "INTRODUCCION", "MARCO TEORICO", "METODOLOGIA",
            "MATERIALES Y METODOS", "RESULTADOS Y DISCUSION",
            "REVISION DE LITERATURA",
        ])
        if es_seccion_principal:
            return ("titulo_capitulo_14pt", "titulo_14pt")

        es_seccion_final = any(k in norm for k in [
            "V. CONCLUSIONES", "VI. RECOMENDACIONES",
            "VII. REFERENCIAS BIBLIOGRAFICAS", "CONCLUSIONES",
            "RECOMENDACIONES", "REFERENCIAS BIBLIOGRAFICAS",
        ])
        if es_seccion_final:
            return ("seccion_final_16pt", "seccion_final")

        # 4. HEADINGS detectados por Word
        if p.get('is_heading', False):
            level = p.get('level') or p.get('body_level') or 1
            if level == 2:
                return ("nivel2", "n2_heading")
            elif level == 3:
                return ("nivel3", "n3_heading")
            elif level == 4:
                return ("nivel4", "n4_heading")
            elif level >= 5:
                return ("nivel5", "n5_heading")

        # 5. CONTENIDO NORMAL (párrafos largos sin bold, justificados)
        if len(txt) >= 80 and not bold and align == 'both':
            return ("contenido", "content")

        # 6. CONTENIDO CORTO pero claramente no es título ni viñeta
        if len(txt) >= 20 and not bold:
            return ("contenido", "content_short")

        return (None, None)

    def _clasifica_vineta(self, i, p):
        """Determina si una viñeta es intermedia o la última del bloque.
        Escanea hasta 20 párrafos adelante para ubicar la última viñeta real."""
        last_idx = i
        for j in range(i + 1, min(i + 20, len(self.paragraphs))):
            next_p = self.paragraphs[j]
            next_txt = next_p['text'].strip()
            if not next_txt:
                continue
            if self._es_vineta(next_p, next_txt):
                last_idx = j
            else:
                break
        if i == last_idx:
            return ("vineta_final", "bullet_last")
        return ("vineta_intermedia", "bullet_mid")

    def _es_vineta(self, p, txt):
        """Detección simple de viñetas por sangría francesa y símbolo inicial."""
        h_cm = round(p.get('indent_hanging') or 0, 2)
        if h_cm <= 0.3:
            return False
        first_char = txt[0]
        allowed = ['-', '•', '*']
        if first_char in allowed and len(txt) > 1 and txt[1] in (' ', '\t'):
            return True
        if re.match(r'^(\(?[a-zA-Z0-9]+\)?\.?)\s', txt):
            return True
        return False

    def _is_in_index_or_prelim(self, i, p):
        """Determina si el párrafo está en zona de índice o preliminares."""
        if hasattr(self.engine, 'last_index_idx') and self.engine.last_index_idx != -1:
            if i <= self.engine.last_index_idx:
                return True
        style_id = p.get('style_id', '').upper()
        if any(k in style_id for k in ['TOC', 'TDC', 'INDICE', 'ÍNDICE']):
            return True
        txt_raw = p['text']
        if "\t" in txt_raw or "..." in txt_raw or bool(re.search(r"\s+\d+$", txt_raw.strip())):
            return True
        return False
