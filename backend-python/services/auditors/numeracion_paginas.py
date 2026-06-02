"""
numeracion_paginas.py - Auditoría de la NUMERACIÓN DE PÁGINAS.

Regla de la Guía UNAP (pág. 2):
    "La numeración se cuenta mentalmente a partir de la primera página (portada)
    hasta la lista de acrónimos, SOLO A PARTIR DEL RESUMEN debe marcarse el
    número."

Es decir:
  - PORTADA → ACRÓNIMOS: las páginas existen pero NO muestran número visible
  - RESUMEN → ANEXOS: las páginas muestran número (continuando el conteo mental)

Implementación:
  1. Leer todos los footer*.xml del .docx
  2. Detectar si algún footer contiene un campo PAGE (numeración automática)
  3. Inspeccionar las secciones del documento:
       - ¿Tienen <w:titlePg/> (primera página distinta)?
       - ¿Tienen footers separados para preliminares vs cuerpo?
  4. Si TODAS las páginas (incluyendo preliminares) muestran número → ERROR
  5. Si la configuración es correcta (preliminares sin número) → PASSED
"""
import zipfile
from lxml import etree
from .base_auditor import BaseAuditor


NSMAP = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}


class NumeracionPaginasAuditor(BaseAuditor):

    def audit(self):
        docx_path = self.engine.working_path
        try:
            with zipfile.ZipFile(docx_path, 'r') as z:
                # 1. Encontrar todos los archivos footer*.xml
                footers = [n for n in z.namelist()
                           if n.startswith('word/footer') and n.endswith('.xml')]
                if not footers:
                    self._add(
                        "Numeración de Páginas",
                        "Numeración no detectada",
                        "warning",
                        "No se detectaron pies de página en el documento. La Guía UNAP "
                        "requiere que las páginas desde el Resumen en adelante muestren "
                        "su número centrado en la parte inferior. Verifique manualmente.",
                        "Numeración desde Resumen",
                        "Sin pies de página",
                    )
                    return

                # 2. ¿Algún footer contiene campo PAGE (numeración automática)?
                footers_with_page = []
                for fpath in footers:
                    try:
                        f_xml = etree.fromstring(z.read(fpath))
                        # Buscar instrucciones de campo PAGE
                        has_page_field = False
                        for inst in f_xml.iter(f'{{{NSMAP["w"]}}}instrText'):
                            if inst.text and 'PAGE' in inst.text.upper():
                                has_page_field = True
                                break
                        # Verificar también <w:fldSimple w:instr="PAGE">
                        for fld in f_xml.iter(f'{{{NSMAP["w"]}}}fldSimple'):
                            instr_attr = fld.get(f'{{{NSMAP["w"]}}}instr', '')
                            if 'PAGE' in instr_attr.upper():
                                has_page_field = True
                                break
                        if has_page_field:
                            footers_with_page.append(fpath)
                    except Exception:
                        pass

                # 3. Si NINGÚN footer tiene número → falta numeración
                if not footers_with_page:
                    self._add(
                        "Numeración de Páginas",
                        "Numeración ausente",
                        "error",
                        "Ninguno de los pies de página contiene el campo de número de "
                        "página. La Guía UNAP requiere numeración centrada en la parte "
                        "inferior, comenzando a mostrarse desde el RESUMEN. Inserte el "
                        "número de página: pestaña Insertar → Número de página → "
                        "Parte inferior → Centrado.",
                        "Campo PAGE en footer, visible desde Resumen",
                        "Sin numeración automática",
                    )
                    return

                # 4. Analizar las secciones del documento
                doc_xml = etree.fromstring(z.read('word/document.xml'))
                sect_prs = doc_xml.findall('.//w:sectPr', NSMAP)

                # Mapear footers a sus secciones
                # Una sección tiene <w:footerReference> que apunta al footer por rId
                # La regla UNAP requiere AL MENOS DOS configuraciones:
                #   - Una sección preliminar SIN número (footer vacío o titlePg)
                #   - Una sección de cuerpo CON número
                sections_info = []
                for s_idx, sect in enumerate(sect_prs):
                    footer_refs = sect.findall('w:footerReference', NSMAP)
                    title_pg = sect.find('w:titlePg', NSMAP)
                    has_title_pg = title_pg is not None
                    section_data = {
                        "index": s_idx,
                        "has_title_pg": has_title_pg,
                        "footer_refs": [
                            (
                                ref.get(f'{{{NSMAP["w"]}}}type') or 'default',
                                ref.get(f'{{{NSMAP["r"]}}}id'),
                            )
                            for ref in footer_refs
                        ],
                    }
                    sections_info.append(section_data)

                # 5. Heurística de evaluación
                #    Si hay UNA SOLA sección y SU footer tiene número → numeración
                #    se aplica desde portada (ERROR)
                if len(sections_info) == 1 and footers_with_page:
                    section = sections_info[0]
                    # Si no hay titlePg ni footers separados (par/impar/first),
                    # entonces todas las páginas tienen número
                    footer_types = [t for t, _ in section["footer_refs"]]
                    has_first_footer = 'first' in footer_types
                    if not section["has_title_pg"] and not has_first_footer:
                        self._add(
                            "Numeración de Páginas",
                            "Numeración visible en páginas preliminares",
                            "error",
                            "La numeración de páginas se muestra en TODAS las páginas, "
                            "incluyendo las preliminares (portada, hoja de jurados, "
                            "dedicatoria, agradecimientos, índices, acrónimos). Según la "
                            "Guía UNAP, la numeración se cuenta mentalmente desde la "
                            "portada pero SOLO SE MUESTRA a partir del Resumen. "
                            "SOLUCIÓN: divida el documento en al menos dos secciones "
                            "(Insertar → Salto de sección → Página siguiente, después "
                            "de la lista de acrónimos) y elimine la numeración del "
                            "footer de la primera sección.",
                            "Numeración visible solo desde Resumen",
                            "Numeración visible en todas las páginas",
                        )
                        return

                # 6. Caso correcto (múltiples secciones o titlePg configurado)
                self._add(
                    "Numeración de Páginas",
                    "Configuración de numeración",
                    "passed",
                    "El documento tiene una configuración válida de numeración de páginas. "
                    "Verifique manualmente que las páginas preliminares (portada hasta "
                    "acrónimos) no muestren número y que la numeración comience "
                    "visualmente desde el Resumen.",
                    "Numeración visible desde Resumen",
                    f"{len(sections_info)} sección(es), {len(footers_with_page)} footer(s) con número",
                )

        except Exception as e:
            self._add(
                "Numeración de Páginas",
                "Error en análisis de numeración",
                "warning",
                f"No se pudo analizar la numeración de páginas: {e}",
                "Análisis exitoso",
                "Error",
            )
