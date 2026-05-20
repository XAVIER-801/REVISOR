from docx import Document
from docx.enum.text import WD_COLOR_INDEX, WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.shared import Pt, RGBColor, Cm
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
import os
import traceback

class DocxAnnotator:
    """
    Motor de Anotación RepoStyle 2.0 - High Fidelity (Turnitin Style).
    Sincroniza índices vía XPath y aplica resaltado multicolor.
    """
    def __init__(self, original_path):
        self.original_path = original_path
        self.doc = Document(original_path)
        self._comment_id = 100
        # Mapeo universal de párrafos para coincidencia exacta con el motor
        self._all_paragraphs = self._map_all_paragraphs()

    def _map_all_paragraphs(self):
        """Extrae TODOS los párrafos (incluyendo tablas) en orden XML."""
        p_elements = self.doc.element.xpath('//w:p')
        paragraphs = []
        for p in p_elements:
            p_obj = Paragraph(p, self.doc._parent)
            p_obj._cached_text = p_obj.text
            paragraphs.append(p_obj)
        return paragraphs

    def annotate(self, audit_results):
        try:
            results = audit_results.get("results", [])
            stats = audit_results.get("stats", {})

            # 1. Asegurar infraestructura de comentarios
            self._ensure_comments_part()

            # 2. Procesar observaciones (Priorizando categorías críticas e incrementando el límite a 400)
            annotated_count = 0
            
            critical_cats = ["🗂️ ÍNDICE", "JERARQUÍA", "📊 TABLAS/FIGURAS", "📎 ANEXOS"]
            
            def get_priority(res):
                cat = str(res.get("category", "")).upper()
                is_crit = any(crit in cat for crit in critical_cats)
                return 0 if is_crit else 1

            sorted_results = sorted([r for r in results if r.get("status") != "passed"], key=get_priority)

            already_commented = set()
            for res in sorted_results:
                if annotated_count >= 400:
                    break
                
                target = self._find_paragraph(res)
                if target:
                    try:
                        p_id = id(target)
                        if p_id in already_commented:
                            continue
                        already_commented.add(p_id)
                        
                        # 1. Paleta de Colores "Turnitin Style"
                        cat = res.get("category", "").upper()
                        if "ESTRUCTURA" in cat or "JERARQUÍA" in cat:
                            color = WD_COLOR_INDEX.RED
                        elif "CONFIGURACIÓN" in cat or "FORMATO" in cat or "ÍNDICE" in cat or "INDICE" in cat:
                            color = WD_COLOR_INDEX.YELLOW
                        elif "TABLAS" in cat or "FIGURAS" in cat:
                            color = WD_COLOR_INDEX.BRIGHT_GREEN
                        else:
                            color = WD_COLOR_INDEX.TURQUOISE # Estilo/Escritura
                        
                        # Si es advertencia, bajamos la intensidad a Amarillo siempre
                        if res.get("status") == "warning":
                            color = WD_COLOR_INDEX.YELLOW

                        # 2. Aplicar Resaltado a todo el párrafo (incluyendo w:hyperlink de forma recursiva)
                        r_elements = target._element.xpath('.//w:r')
                        if r_elements:
                            from docx.text.run import Run
                            for r_el in r_elements:
                                run_obj = Run(r_el, target)
                                run_obj.font.highlight_color = color
                        else:
                            # Si no hay runs en absoluto, agregamos uno
                            new_run = target.add_run(target.text if target.text else " ")
                            new_run.font.highlight_color = color
                        
                        # 3. Comentario Nativo
                        page_info = f"Pág. {res.get('page')}" if res.get('page') else "Pág. ??"
                        msg = (f"--------------------------------------------------\n"
                               f"🔍 **OBSERVACIÓN DE FORMATO**\n"
                               f"--------------------------------------------------\n"
                               f"📌 **REGLA:** {res.get('rule')}\n\n"
                               f"❌ **HALLADO:** {res.get('actual')}\n"
                               f"✅ **REQUERIDO:** {res.get('expected')}\n"
                               f"--------------------------------------------------\n"
                               f"💡 **DETALLE:**\n{res.get('message')}\n"
                               f"--------------------------------------------------\n"
                               f"📍 **Ubicación:** {page_info}")
                        
                        self._add_native_comment(target, msg)
                        annotated_count += 1
                    except Exception as e:
                        print(f"Error anotando: {e}")

            # 3. Reporte Ejecutivo al inicio
            self._add_institutional_report(stats, results)

            out_name = f"auditado_{os.path.basename(self.original_path)}"
            out_path = os.path.join(os.path.dirname(self.original_path), out_name)
            self.doc.save(out_path)
            return out_path, out_name
        except Exception as e:
            print(f"🛑 Error en Anotador: {str(e)}")
            traceback.print_exc()
            return self.original_path, os.path.basename(self.original_path)

    def _find_paragraph(self, res):
        p_text = res.get("paragraphText")
        p_idx = res.get("paragraphIndex")
        
        # 1. Sincronización por Índice XML (Máxima Precisión)
        if p_idx is not None and p_idx < len(self._all_paragraphs):
            p = self._all_paragraphs[p_idx]
            # Verificación de integridad del texto
            p_txt_val = getattr(p, '_cached_text', None) or p.text
            if not p_text or p_text[:15] in p_txt_val:
                return p
        
        # 2. Fallback: Búsqueda por Texto cerca de p_idx
        if p_text and len(str(p_text).strip()) > 5:
            search_txt = str(p_text).strip()
            
            # Buscar en un radio de 50 párrafos alrededor de p_idx
            if p_idx is not None:
                start_idx = max(0, p_idx - 50)
                end_idx = min(len(self._all_paragraphs), p_idx + 50)
                search_range = self._all_paragraphs[start_idx:end_idx]
            else:
                search_range = self._all_paragraphs
                
            for p in search_range:
                p_txt_val = getattr(p, '_cached_text', None) or p.text
                if search_txt in p_txt_val: return p
                
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
            
            # Dividir en párrafos y parsear formato negrita (**texto**)
            lines = text.split('\n')
            for line in lines:
                p_line = OxmlElement('w:p')
                parts = line.split('**')
                is_bold = False
                for part in parts:
                    r = OxmlElement('w:r')
                    if is_bold:
                        rPr = OxmlElement('w:rPr')
                        b = OxmlElement('w:b')
                        rPr.append(b)
                        r.append(rPr)
                    t = OxmlElement('w:t')
                    t.set(qn('xml:space'), 'preserve')
                    t.text = part
                    r.append(t)
                    p_line.append(r)
                    is_bold = not is_bold
                comment.append(p_line)
            comments_xml.append(comment)
            
            # 2. Marcar el rango en el documento
            # Al inicio del párrafo (después de w:pPr para cumplir con el esquema OOXML)
            pPr = paragraph._element.find(qn('w:pPr'))
            insert_idx = paragraph._element.index(pPr) + 1 if pPr is not None else 0
            
            range_start = OxmlElement('w:commentRangeStart')
            range_start.set(qn('w:id'), cid)
            paragraph._element.insert(insert_idx, range_start)
            
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
        
        # Totales
        first.insert_paragraph_before(
            f"🔴 Errores: {stats.get('errors', 0)}  |  "
            f"🟡 Advertencias: {stats.get('warnings', 0)}  |  "
            f"🟢 Aprobados: {stats.get('passed', 0)}"
        )
        
        first.insert_paragraph_before("_"*80)
        header = first.insert_paragraph_before("📋 DETALLE DE OBSERVACIONES (ordenado por página)")
        header.runs[0].bold = True
        header.runs[0].font.size = Pt(13)
        header.runs[0].font.color.rgb = RGBColor(0, 51, 102)

        # Filtrar solo errores y advertencias, ordenar por número de página
        failed = [r for r in results if r.get("status") != "passed"]
        failed_sorted = sorted(failed, key=lambda r: (r.get("page") or 9999, r.get("section") or ""))

        # Limitar la lista del reporte Word a los primeros 80 errores detallados
        failed_display = failed_sorted[:80]

        idx = 1
        last_section = None
        for res in failed_display:
            section = res.get("section") or "General"
            page = res.get("page")
            page_label = f"Pág. {page}" if page else "Pág. ??"

            # Encabezado de sección cuando cambia
            if section != last_section:
                sec_p = first.insert_paragraph_before(f"▶ Sección: {section}")
                sec_p.runs[0].bold = True
                sec_p.runs[0].font.color.rgb = RGBColor(0, 70, 127)
                last_section = section

            icon = "🔴" if res.get("status") == "error" else "🟡"
            p = first.insert_paragraph_before(
                f"  {idx}. {icon} [{page_label}] [{res.get('category')}] {res.get('rule')}"
            )
            p.runs[0].bold = True
            p.runs[0].font.color.rgb = RGBColor(204, 51, 0) if res.get("status") == "error" else RGBColor(180, 120, 0)

            # Detalle en línea secundaria
            det_p = first.insert_paragraph_before(
                f"      ❌ Encontrado: {res.get('actual')}  →  ✅ Esperado: {res.get('expected')}"
            )
            det_p.runs[0].font.size = Pt(10)
            det_p.runs[0].font.color.rgb = RGBColor(80, 80, 80)

            # Texto del párrafo afectado (si existe)
            p_text = res.get("paragraphText") or ""
            if p_text and p_text.strip():
                snip = p_text.strip()[:80] + ("..." if len(p_text.strip()) > 80 else "")
                ctx_p = first.insert_paragraph_before(f"      📝 Texto: \"{snip}\"")
                ctx_p.runs[0].font.size = Pt(9)
                ctx_p.runs[0].font.color.rgb = RGBColor(120, 120, 120)
                ctx_p.runs[0].italic = True

            idx += 1

        if len(failed_sorted) > 80:
            extra_count = len(failed_sorted) - 80
            p_extra = first.insert_paragraph_before(
                f"\n✨ Se omitieron {extra_count} observaciones de menor importancia en este reporte Word para mantener el documento legible. "
                f"Por favor, revise la plataforma web de RepoStyle para examinar el listado completo e interactivo."
            )
            p_extra.runs[0].italic = True
            p_extra.runs[0].bold = True
            p_extra.runs[0].font.size = Pt(11)
            p_extra.runs[0].font.color.rgb = RGBColor(0, 102, 102)

        first.insert_paragraph_before("").add_run().add_break(WD_BREAK.PAGE)
