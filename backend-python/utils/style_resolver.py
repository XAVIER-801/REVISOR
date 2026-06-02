"""
Módulo de resolución de estilos usando lxml para parsear directamente el XML del .docx.
Optimizado para detectar Negrita y Alineación heredada de estilos complejos.
"""
import zipfile
from lxml import etree

NSMAP = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}

def _val(el, attr='w:val'):
    if el is None: return None
    ns_attr = attr.replace('w:', f'{{{NSMAP["w"]}}}')
    return el.get(ns_attr)

def parse_rpr(rpr_el):
    """Extrae propiedades de run desde un elemento w:rPr."""
    if rpr_el is None: return {}
    props = {}
    
    # Bold
    b = rpr_el.find('w:b', NSMAP)
    if b is not None:
        v = _val(b)
        props['bold'] = (v is None or v in ['1', 'true', 'on'])
    
    # Italic
    i = rpr_el.find('w:i', NSMAP)
    if i is not None:
        v = _val(i)
        props['italic'] = (v is None or v in ['1', 'true', 'on'])

    # Font size
    sz = rpr_el.find('w:sz', NSMAP)
    if sz is not None:
        v = _val(sz)
        if v: props['font_size'] = int(v) / 2

    # Font name
    fonts = rpr_el.find('w:rFonts', NSMAP)
    if fonts is not None:
        ns = f'{{{NSMAP["w"]}}}'
        for a in ['ascii', 'hAnsi', 'cs', 'eastAsia']:
            fname = fonts.get(f'{ns}{a}')
            if fname: 
                props['font_name'] = fname
                break
    return props

def parse_ppr(ppr_el):
    """Extrae propiedades de párrafo."""
    if ppr_el is None: return {}
    props = {}

    # Alignment
    jc = ppr_el.find('w:jc', NSMAP)
    if jc is not None: props['alignment'] = _val(jc)

    # Indents (convertir de twips a cm: twips * 2.54 / 1440)
    ind = ppr_el.find('w:ind', NSMAP)
    if ind is not None:
        ns = f'{{{NSMAP["w"]}}}'
        l = ind.get(f'{ns}left') or ind.get(f'{ns}start')
        f = ind.get(f'{ns}firstLine')
        h = ind.get(f'{ns}hanging')
        # Convertir de twips a cm: dividir por 567.717 (≈ 1440/2.54)
        if l: props['indent_left'] = round(int(l) * 2.54 / 1440, 3)
        if f: props['indent_first'] = round(int(f) * 2.54 / 1440, 3)
        if h: props['indent_hanging'] = round(int(h) * 2.54 / 1440, 3)

    # Style
    style = ppr_el.find('w:pStyle', NSMAP)
    if style is not None: props['style_id'] = _val(style)

    # Spacing
    spacing = ppr_el.find('w:spacing', NSMAP)
    if spacing is not None:
        ns = f'{{{NSMAP["w"]}}}'
        line = spacing.get(f'{ns}line')
        if line: props['line_spacing'] = round(int(line) / 240, 2)
        before = spacing.get(f'{ns}before')
        after = spacing.get(f'{ns}after')
        if before: props['spacing_before'] = int(before) / 20 
        if after: props['spacing_after'] = int(after) / 20 

    return props

class StyleResolver:
    def __init__(self, docx_path):
        self.docx_path = docx_path
        self.style_map = {}
        self.default_rpr = {}
        self.default_ppr = {}
        self.section_props = {}
        self._load_styles()
        self._load_section_props()

    def _load_styles(self):
        try:
            with zipfile.ZipFile(self.docx_path, 'r') as z:
                if 'word/styles.xml' not in z.namelist(): return
                root = etree.fromstring(z.read('word/styles.xml'))
            
            # Defaults
            defs = root.find('w:docDefaults', NSMAP)
            if defs is not None:
                self.default_rpr = parse_rpr(defs.find('.//w:rPrDefault/w:rPr', NSMAP))
                self.default_ppr = parse_ppr(defs.find('.//w:pPrDefault/w:pPr', NSMAP))

            # Load styles and their inheritance
            for s_el in root.findall('w:style', NSMAP):
                sid = s_el.get(f'{{{NSMAP["w"]}}}styleId')
                if not sid: continue
                
                rpr = parse_rpr(s_el.find('w:rPr', NSMAP))
                ppr_el = s_el.find('w:pPr', NSMAP)
                ppr = parse_ppr(ppr_el)
                if ppr_el is not None:
                    rpr.update(parse_rpr(ppr_el.find('w:rPr', NSMAP)))
                
                parent = _val(s_el.find('w:basedOn', NSMAP))
                self.style_map[sid] = {'rpr': rpr, 'ppr': ppr, 'parent': parent}

            # Resolver cadenas de herencia
            for _ in range(5):
                changed = False
                for sid, data in self.style_map.items():
                    if data['parent'] and data['parent'] in self.style_map:
                        parent = self.style_map[data['parent']]
                        for k, v in parent['rpr'].items():
                            if k not in data['rpr']:
                                data['rpr'][k] = v
                                changed = True
                        for k, v in parent['ppr'].items():
                            if k not in data['ppr']:
                                data['ppr'][k] = v
                                changed = True
                if not changed: break
        except: pass

    def _load_section_props(self):
        """
        Carga propiedades de TODAS las secciones (no solo la primera).
        Cada sección puede tener orientación distinta (portrait/landscape) y
        márgenes propios. La lista se guarda en self.section_props["sections"].

        Para retrocompatibilidad, los valores de la PRIMERA sección se exponen
        también en self.section_props['paper']/'margin_top'/etc.
        """
        try:
            with zipfile.ZipFile(self.docx_path, 'r') as z:
                root = etree.fromstring(z.read('word/document.xml'))

            ns = f'{{{NSMAP["w"]}}}'
            to_cm = lambda x: round(int(x) / 1440 * 2.54, 2) if x else 0

            sections = []
            # Todas las sectPr del documento (final + intermedias dentro de pPr)
            for sect in root.iter(f'{ns}sectPr'):
                pgSz = sect.find('w:pgSz', NSMAP)
                section_data = {}
                if pgSz is not None:
                    w_attr = pgSz.get(f'{ns}w')
                    h_attr = pgSz.get(f'{ns}h')
                    orient = pgSz.get(f'{ns}orient') or 'portrait'
                    section_data['width'] = int(w_attr) / 1440 if w_attr else 0
                    section_data['height'] = int(h_attr) / 1440 if h_attr else 0
                    section_data['orient'] = orient
                    section_data['is_landscape'] = (orient == 'landscape') or (
                        section_data['width'] > section_data['height']
                    )
                    section_data['paper'] = (
                        'A4' if abs(section_data['width'] - 8.27) < 0.2
                              and abs(section_data['height'] - 11.69) < 0.2
                        else 'A4-landscape' if abs(section_data['width'] - 11.69) < 0.2
                              and abs(section_data['height'] - 8.27) < 0.2
                        else f"{section_data['width']:.1f}x{section_data['height']:.1f}"
                    )

                pgMar = sect.find('w:pgMar', NSMAP)
                if pgMar is not None:
                    section_data['margin_top'] = to_cm(pgMar.get(f'{ns}top'))
                    section_data['margin_bottom'] = to_cm(pgMar.get(f'{ns}bottom'))
                    section_data['margin_left'] = to_cm(pgMar.get(f'{ns}left'))
                    section_data['margin_right'] = to_cm(pgMar.get(f'{ns}right'))

                # Posición XML donde está esta sectPr (para mapear párrafos a sección)
                section_data['xml_position'] = sect.sourceline if hasattr(sect, 'sourceline') else -1

                sections.append(section_data)

            self.section_props['sections'] = sections

            # Retrocompatibilidad: exponer la PRIMERA sección como propiedades de
            # nivel superior (motor y configuracion_pagina.py las usan así)
            if sections:
                first = sections[0]
                self.section_props['paper'] = first.get('paper', 'unknown')
                self.section_props['margin_top'] = first.get('margin_top', 0)
                self.section_props['margin_bottom'] = first.get('margin_bottom', 0)
                self.section_props['margin_left'] = first.get('margin_left', 0)
                self.section_props['margin_right'] = first.get('margin_right', 0)
                self.section_props['is_landscape'] = first.get('is_landscape', False)
        except Exception:
            pass

    def resolve(self, style_id, explicit_ppr, explicit_rpr=None):
        res_ppr = {**self.default_ppr}
        res_rpr = {**self.default_rpr}
        if style_id and style_id in self.style_map:
            res_ppr.update(self.style_map[style_id]['ppr'])
            res_rpr.update(self.style_map[style_id]['rpr'])
        res_ppr.update(explicit_ppr)
        if explicit_rpr: res_rpr.update(explicit_rpr)
        return res_ppr, res_rpr
