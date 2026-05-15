from docx import Document
from docx.enum.text import WD_COLOR_INDEX, WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.shared import Pt, RGBColor, Cm
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn
import os
import traceback

class DocxAnnotator:
    """
    Motor de Anotación RepoStyle 2.0 con Comentarios Nativos Reales.
    Inyecta comentarios en el margen derecho utilizando manipulación OXML.
    """
    def __init__(self, original_path):
        self.original_path = original_path
        self.doc = Document(original_path)
        self._comment_id = 100

    def annotate(self, audit_results):
        try:
            results = audit_results.get("results", [])
            stats = audit_results.get("stats", {})

            # 1. Asegurar infraestructura de comentarios
            self._ensure_comments_part()

            # 2. Procesar observaciones
            for res in results:
                if res.get("status") == "passed": continue
                
                target = self._find_paragraph(res)
                if target:
                    # Resaltado visual en el texto
                    color = WD_COLOR_INDEX.RED if res["status"] == "error" else WD_COLOR_INDEX.YELLOW
                    for run in target.runs:
                        run.font.highlight_color = color
                    
                    # Inserción de Comentario Nativo (Sidebar)
                    msg = (f"{res.get('rule')}\n"
                           f"Hallazgo: {res.get('actual')}\n"
                           f"Debe ser: {res.get('expected')}\n"
                           f"Observación: {res.get('message')}")
                    self._add_native_comment(target, msg)

            # 3. Reporte Ejecutivo al inicio
            self._add_institutional_report(stats, results)

            out_name = f"auditado_{os.path.basename(self.original_path)}"
            out_path = os.path.join(os.path.dirname(self.original_path), out_name)
            self.doc.save(out_path)
            return out_path, out_name
        except Exception as e:
            traceback.print_exc()
            return self.original_path, os.path.basename(self.original_path)

    def _find_paragraph(self, res):
        p_text = res.get("paragraphText")
        p_idx = res.get("paragraphIndex")
        if p_idx is not None and p_idx < len(self.doc.paragraphs):
            p = self.doc.paragraphs[p_idx]
            if not p_text or p_text.strip() in p.text: return p
        if p_text:
            txt = str(p_text).strip()
            if len(txt) > 5:
                for p in self.doc.paragraphs:
                    if txt in p.text: return p
        return None

    def _ensure_comments_part(self):
        """Inicializa la parte de comentarios en el paquete OOXML."""
        try:
            _ = self.doc.part.comments
        except:
            pass

    def _add_native_comment(self, paragraph, text, author='RepoStyle', initials='RS'):
        """Añade un comentario real que aparece en el margen derecho."""
        try:
            # Obtener el elemento w:comments del documento
            comments_part = self.doc.part._comments_part
            comments_xml = comments_part.element
            
            cid = str(self._comment_id)
            self._comment_id += 1
            
            # 1. Crear la definición del comentario
            comment = OxmlElement('w:comment')
            comment.set(qn('w:id'), cid)
            comment.set(qn('w:author'), author)
            comment.set(qn('w:initials'), initials)
            
            p = OxmlElement('w:p')
            r = OxmlElement('w:r')
            t = OxmlElement('w:t')
            t.text = text
            r.append(t)
            p.append(r)
            comment.append(p)
            comments_xml.append(comment)
            
            # 2. Marcar el rango en el documento
            # Al inicio del párrafo
            range_start = OxmlElement('w:commentRangeStart')
            range_start.set(qn('w:id'), cid)
            paragraph._element.insert(0, range_start)
            
            # Al final del párrafo
            range_end = OxmlElement('w:commentRangeEnd')
            range_end.set(qn('w:id'), cid)
            paragraph._element.append(range_end)
            
            # Referencia visual (el "globo")
            ref_run = OxmlElement('w:r')
            rPr = OxmlElement('w:rPr')
            rStyle = OxmlElement('w:rStyle')
            rStyle.set(qn('w:val'), 'CommentReference')
            rPr.append(rStyle)
            ref_run.append(rPr)
            
            comment_ref = OxmlElement('w:commentReference')
            comment_ref.set(qn('w:id'), cid)
            ref_run.append(comment_ref)
            paragraph._element.append(ref_run)
            
        except Exception as e:
            print(f"Error en comentario nativo: {e}")

    def _add_institutional_report(self, stats, results):
        if not self.doc.paragraphs: self.doc.add_paragraph("")
        first = self.doc.paragraphs[0]
        
        t1 = first.insert_paragraph_before("🏛️ REPORTE INSTITUCIONAL REPOSTYLE 2.0")
        t1.runs[0].bold = True
        t1.runs[0].font.size = Pt(18)
        t1.runs[0].font.color.rgb = RGBColor(0, 102, 102)

        t2 = first.insert_paragraph_before("AUDITOR DE FORMATO Y ESTILO DE TESIS - VRI UNAP")
        t2.runs[0].bold = True
        t2.runs[0].font.size = Pt(12)
        t2.runs[0].font.color.rgb = RGBColor(0, 51, 102)

        first.insert_paragraph_before("_"*80)
        p_score = first.insert_paragraph_before(f"📊 PUNTAJE DE CUMPLIMIENTO: {stats.get('score', 0)}/100")
        p_score.runs[0].bold = True
        p_score.runs[0].font.size = Pt(16)
        p_score.runs[0].font.color.rgb = RGBColor(204, 0, 0)
        
        first.insert_paragraph_before("_"*80)
        idx = 1
        for res in results:
            if res.get("status") == "passed": continue
            p = first.insert_paragraph_before(f"{idx}. [{res.get('category')}] {res.get('rule')}")
            p.runs[0].bold = True
            p.runs[0].font.color.rgb = RGBColor(204, 51, 0)
            idx += 1

        first.insert_paragraph_before("").add_run().add_break(WD_BREAK.PAGE)
