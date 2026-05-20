"""
secuencia_titulos.py - Auditoría de Secuencia Lógica de Títulos

Reglas implementadas:
- No se puede saltar niveles de títulos (ej. de Nivel 1 a Nivel 3 directamente).
- Siempre debe seguir una secuencia jerárquica estricta.
"""
import re
from .base_auditor import BaseAuditor

class SecuenciaTitulosAuditor(BaseAuditor):
    def audit(self):
        last_level = 0
        
        for p in self.paragraphs:
            if not p.get("is_in_body"):
                continue
                
            body_level = p.get("body_level", 0)
            if body_level == 0:
                continue
                
            txt = p["text"].strip()
            norm = p["norm"]
            
            # Determinar si el párrafo actúa como título
            is_capitulo = bool(re.match(r"^CAP[ÍI]TULO\s+(I|V|X|L|C|[0-9]+)", norm))
            es_seccion_principal = any(k in norm for k in [
                "INTRODUCCION", "MARCO TEORICO", "METODOLOGIA",
                "MATERIALES Y METODOS", "RESULTADOS Y DISCUSION",
                "CONCLUSIONES", "RECOMENDACIONES", "REFERENCIAS BIBLIOGRAFICAS"
            ]) and (p.get('style_id', '').upper().startswith('HEADING') or txt.isupper() or any(r.get('bold') for r in p.get('runs', [])))
            
            numbering_match = re.match(r'^(\d+(?:\.\d+)+)\.?(?:[\s\t]+|$)', txt)
            is_title = p.get('is_heading') or numbering_match or is_capitulo or es_seccion_principal
            
            if not is_title:
                continue
                
            # Verificar salto de nivel
            if last_level > 0 and body_level > last_level + 1:
                self._add("Jerarquía", "Salto de Nivel de Título Invalido", "error",
                          f"Se detectó un salto incorrecto en la jerarquía: de Nivel {last_level} a Nivel {body_level}. Los títulos deben seguir una secuencia estricta y consecutiva.",
                          f"Nivel <= {last_level + 1}", f"Salto a Nivel {body_level}", p_idx=p['index'], p_text=txt[:50])
                          
            last_level = body_level
