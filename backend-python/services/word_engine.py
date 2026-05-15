from docx import Document
import os
import re
import unicodedata
import zipfile
from lxml import etree
from utils.style_resolver import StyleResolver, parse_rpr, parse_ppr, NSMAP
from utils.converter import DocConverter

class WordAuditEngine:
    def __init__(self, file_path):
        self.original_path = file_path
        self.working_path = file_path
        self.stats = {"score": 100, "errors": 0, "warnings": 0, "passed": 0}
        self.results = []
        self.paragraphs = []

    def run_audit(self):
        try:
            output_dir = os.path.dirname(self.original_path)
            self.working_path = DocConverter.standardize_to_docx(self.original_path, output_dir)
            self.document = Document(self.working_path)
            self.resolver = StyleResolver(self.working_path)
            self._extract_data()
            
            self._audit_config_general()
            self._audit_content_flow()
            self._audit_resumen_abstract()
            self._audit_global_formatting()
            
            return self._finalize()
        except Exception as e:
            self._add("Sistema", "Error Crítico", "error", str(e))
            return self._finalize()

    def _extract_data(self):
        with zipfile.ZipFile(self.working_path, 'r') as z:
            root = etree.fromstring(z.read('word/document.xml'))
        body = root.find('w:body', NSMAP)
        for idx, p_el in enumerate(body.iter(f'{{{NSMAP["w"]}}}p')):
            ppr_el = p_el.find('w:pPr', NSMAP)
            explicit_ppr = parse_ppr(ppr_el)
            style_id = explicit_ppr.get('style_id', 'Normal')
            res_ppr, _ = self.resolver.resolve(style_id, explicit_ppr)
            
            txt = ""
            runs = []
            for r_el in p_el.findall('w:r', NSMAP):
                t = "".join([t.text for t in r_el.findall('w:t', NSMAP) if t.text])
                txt += t
                explicit_rpr = parse_rpr(r_el.find('w:rPr', NSMAP))
                _, res_rpr = self.resolver.resolve(style_id, explicit_ppr, explicit_rpr)
                runs.append({
                    "bold": res_rpr.get('bold', False), 
                    "italic": res_rpr.get('italic', False),
                    "size": res_rpr.get('font_size', 12), 
                    "font": res_rpr.get('font_name', 'Times New Roman'),
                    "text": t
                })

            self.paragraphs.append({
                "text": txt,
                "norm": self._norm(txt),
                "alignment": res_ppr.get('alignment', 'left'),
                "line_spacing": res_ppr.get('line_spacing'),
                "indent_first": res_ppr.get('indent_first'),
                "runs": runs,
                "index": idx
            })

    def _norm(self, t):
        if not t: return ""
        return unicodedata.normalize('NFD', t).encode('ascii', 'ignore').decode('ascii').upper().strip()

    def _add(self, cat, rule, status, msg, expected="", actual="", p_idx=None, p_text=""):
        if status == "error": self.stats["errors"] += 1
        elif status == "warning": self.stats["warnings"] += 1
        self.results.append({
            "category": cat, "rule": rule, "status": status, "message": msg, 
            "expected": str(expected), "actual": str(actual),
            "paragraphIndex": p_idx, "paragraphText": p_text
        })

    def _get_p_props(self, p):
        if not p["runs"]: return 12, False, False, "Times New Roman"
        for r in p["runs"]:
            if r["text"].strip():
                return r["size"], r["bold"], r["italic"], r["font"]
        return 12, False, False, "Times New Roman"

    def _audit_config_general(self):
        sp = self.resolver.section_props
        paper = sp.get('paper', 'Unknown')
        ok_paper = paper == 'A4'
        self._add("Configuración", "Tamaño de Papel", "passed" if ok_paper else "error", 
                  "El papel debe ser A4.", "A4", paper)
        
        margins = [
            ('Superior', sp.get('margin_top'), 2.5),
            ('Inferior', sp.get('margin_bottom'), 2.5),
            ('Derecho', sp.get('margin_right'), 2.5),
            ('Izquierdo', sp.get('margin_left'), 3.0)
        ]
        for name, actual, expected in margins:
            ok = abs((actual or 0) - expected) < 0.1
            self._add("Configuración", f"Margen {name}", "passed" if ok else "error",
                      f"Margen {name} debe ser {expected} cm.", f"{expected} cm", f"{actual} cm")

    def _audit_content_flow(self):
        for i, p in enumerate(self.paragraphs):
            txt = p["text"].strip()
            norm = p["norm"]
            if not norm: continue

            size, bold, italic, font = self._get_p_props(p)
            is_index = "...." in txt or re.search(r"\d+$", txt)

            keywords = ["DEDICATORIA", "AGRADECIMIENTOS", "INDICE GENERAL", "RESUMEN", "ABSTRACT", 
                        "CONCLUSIONES", "RECOMENDACIONES", "REFERENCIAS BIBLIOGRAFICAS", "ANEXOS"]
            is_cap = re.match(r"^CAPITULO\s+(I|V|X|L|C|[0-9]+)", norm)
            
            if norm in keywords or is_cap:
                if not is_index:
                    expected_size = 16
                    ok_size = abs(size - expected_size) < 0.5
                    ok_bold = bold == True
                    ok_align = p["alignment"] == 'center'
                    
                    status = "passed" if (ok_size and ok_bold and ok_align) else "error"
                    msg = f"Título {norm} debe ser {expected_size}pt, Negrita (Bold) y Centrado."
                    self._add("Jerarquía", f"Título Nivel 1: {norm}", status, msg, 
                              f"{expected_size}pt, Bold, Center", f"{size}pt, {'Bold' if bold else 'Normal'}, {p['alignment']}", p_idx=i, p_text=txt)
                else:
                    ok_idx = abs(size - 12) < 0.5
                    self._add("Estructura", f"Índice: {txt[:30]}...", "passed" if ok_idx else "error",
                              "Entradas de índice deben ser 12pt.", "12pt", f"{size}pt", p_idx=i, p_text=txt)

            if norm == "INTRODUCCION" and not is_index:
                ok_intro = abs(size - 14) < 0.5 and bold and p["alignment"] == 'center'
                self._add("Jerarquía", "Título: INTRODUCCIÓN", "passed" if ok_intro else "error",
                          "La Introducción debe ser 14pt, Negrita (Bold) y Centrada.", "14pt, Bold, Center", f"{size}pt, {'Bold' if bold else 'Normal'}, {p['alignment']}", p_idx=i, p_text=txt)

            hierarchy_match = re.match(r"^(\d+\.\d+)(\.\d+)?\s+(.*)", txt)
            if hierarchy_match and not is_index:
                level_str = hierarchy_match.group(1) + (hierarchy_match.group(2) or "")
                level_depth = level_str.count('.') + 1
                if level_depth == 2:
                    ok = abs(size - 14) < 0.5 and bold
                    self._add("Jerarquía", f"Nivel 2: {level_str}", "passed" if ok else "error",
                              "Nivel 2 debe ser 14pt y Negrita (Bold).", "14pt, Bold", f"{size}pt, {'Bold' if bold else 'Normal'}", p_idx=i, p_text=txt)
                elif level_depth >= 3:
                    ok = abs(size - 12) < 0.5 and bold
                    self._add("Jerarquía", f"Nivel {level_depth}: {level_str}", "passed" if ok else "error",
                              f"Nivel {level_depth} debe ser 12pt y Negrita (Bold).", "12pt, Bold", f"{size}pt, {'Bold' if bold else 'Normal'}", p_idx=i, p_text=txt)

            if re.match(r"^(TABLA|FIGURA)\s+\d+", norm):
                ok_label = abs(size - 12) < 0.5 and bold
                self._add("Tablas/Figuras", f"Etiqueta: {txt[:20]}", "passed" if ok_label else "error",
                          "Etiquetas de Tablas/Figuras deben ser 12pt y Negrita (Bold).", "12pt, Bold", f"{size}pt, {'Bold' if bold else 'Normal'}", p_idx=i, p_text=txt)

    def _audit_resumen_abstract(self):
        content = []
        capture = False
        for p in self.paragraphs:
            norm = p["norm"]
            if norm == "RESUMEN":
                capture = True
                continue
            if "PALABRAS CLAVE" in norm:
                capture = False
                pk_txt = p["text"].lower()
                if pk_txt.startswith("palabras clave:"):
                    self._add("Contenido", "Formato Palabras Clave", "passed", "Tag 'Palabras clave:' detectado.")
                else:
                    self._add("Contenido", "Formato Palabras Clave", "error", "Debe empezar con 'Palabras clave:' en minúscula (excepto P).")
                break
            if capture:
                content.append(p["text"])
        
        if content:
            full_text = " ".join(content)
            words = len(full_text.split())
            ok_words = 250 <= words <= 300
            self._add("Contenido", "Extensión del Resumen", "passed" if ok_words else "warning",
                      f"El resumen debe tener entre 250 y 300 palabras. Hallado: {words}", "250-300", words)

    def _audit_global_formatting(self):
        sample = [p for p in self.paragraphs if len(p['text']) > 150][:30]
        if sample:
            indent_ok = sum(1 for p in sample if (p.get('indent_first') or 0) >= 700)
            justified_ok = sum(1 for p in sample if p.get('alignment') == 'both')
            
            self._add("Configuración", "Sangría de Primera Línea", "passed" if indent_ok > len(sample)*0.6 else "warning",
                      "Los párrafos deben tener sangría de 1.25 cm.", "1.25 cm", f"{indent_ok}/{len(sample)} detectados")
            self._add("Configuración", "Alineación Justificada", "passed" if justified_ok > len(sample)*0.6 else "error",
                      "El cuerpo del texto debe estar justificado.", "Justificado", f"{justified_ok}/{len(sample)} detectados")

    def _finalize(self):
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "passed")
        self.stats.update({"passed": passed, "score": max(0, round((passed/total)*100)) if total > 0 else 0})
        return {"stats": self.stats, "results": self.results}
