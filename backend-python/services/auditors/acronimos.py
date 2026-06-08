"""
acronimos.py - Auditoría de la sección de ACRÓNIMOS.

Reglas implementadas:
- Título "ACRÓNIMOS":
  - Tamaño: 16pt
  - Estilo: Negrita (Bold)
  - Spacing: anterior 0pt, posterior 10pt
  - Alineación: Centrado
  - Interlineado: 2.0
  - Sangría: Sin sangría (0cm)

- Entradas de Acrónimos (Contenido):
  - No deben estar dentro de una tabla.
  - Formato: Acrónimo + Dos Puntos (:) + Tabulaciones (\t) + Significado (ej. "CADH:\tConvención...").
  - Obligatorio: Sin espacios antes de los dos puntos (:)
  - Obligatorio: Separación mediante tabulaciones (al menos una \t) después de los dos puntos.
  - Estilo de fuente: Sin negrita ni cursiva en todo el párrafo.
  - Alineación: Izquierda
  - Interlineado: 1.0, 1.5 o 2.0
  - Espaciado: anterior 0pt, posterior 0pt
  - Sangría: Izquierda 0cm, Sangría Francesa 3.75cm
"""
import re
from .base_auditor import BaseAuditor


class AcronimosAuditor(BaseAuditor):

    def audit(self):
        in_acronimos = False
        header_p = None
        entries = []

        # 1. Identificar la sección de ACRÓNIMOS
        for i, p in enumerate(self.paragraphs):
            if i <= self.last_index_idx:
                continue
            sec_upper = p.get('section', '').upper()
            if any(k in sec_upper for k in ['ÍNDICE', 'INDICE', 'TABLA DE CONTENIDOS', 'TABLA DE CONTENIDO']):
                continue

            txt = p['text'].strip()
            norm = p['norm']
            
            # Detectar cabecera de la sección
            if norm == "ACRONIMOS" or norm == "ACRÓNIMOS":
                # Asegurar que no sea una línea del índice general o tabla de contenido
                if "...." not in txt and not bool(re.search(r"\d+$", txt)):
                    in_acronimos = True
                    header_p = p
                    continue
            
            # Si entramos en la sección, recolectamos hasta la siguiente sección conocida
            if in_acronimos:
                # Si encontramos otra sección principal de la tesis, salimos
                if norm in ["RESUMEN", "ABSTRACT", "INTRODUCCION", "INTRODUCCIÓN", "MARCO TEORICO", "INDICE GENERAL"]:
                    break
                if norm.startswith("CAPITULO") or norm.startswith("CAPÍTULO"):
                    break
                
                # Agregar a las entradas de acrónimos
                # Ignorar párrafos completamente vacíos
                if txt:
                    entries.append(p)

        # 2. Auditar Cabecera "ACRÓNIMOS"
        if header_p:
            txt_head = header_p['text'].strip()
            align = header_p.get('alignment', 'left')
            size, is_bold_props, _, _ = self._get_p_props(header_p)
            size = size or 0
            bold = is_bold_props or any(r.get('bold') for r in header_p.get('runs', []))
            s_before = header_p.get('spacing_before', 0)
            s_after = header_p.get('spacing_after', 0)
            line_spacing = header_p.get('line_spacing')
            l_cm = round(header_p.get('indent_left') or 0, 2)
            f_cm = round(header_p.get('indent_first') or 0, 2)
            h_cm = round(header_p.get('indent_hanging') or 0, 2)

            ok_align = align == 'center'
            ok_size = size == 16
            ok_bold = bold == True
            ok_s_before = s_before < 1.0
            ok_s_after = abs(s_after - 10.0) < 2.0
            ok_line = line_spacing is not None and abs(line_spacing - 2.0) < 0.2
            ok_indent = abs(l_cm) < 0.1 and abs(f_cm) < 0.1 and abs(h_cm) < 0.1

            passed = ok_align and ok_size and ok_bold and ok_s_before and ok_s_after and ok_line and ok_indent
            
            if not passed:
                req_list = []
                act_list = []
                if not ok_align:
                    req_list.append("Centrado")
                    act_list.append(self._align_display(align))
                if not ok_size:
                    req_list.append("16pt")
                    act_list.append(f"{size}pt")
                if not ok_bold:
                    req_list.append("Negrita")
                    act_list.append("Normal")
                if not ok_s_before:
                    req_list.append("Esp. ant 0pt")
                    act_list.append(f"{s_before}pt")
                if not ok_s_after:
                    req_list.append("Esp. post 10pt")
                    act_list.append(f"{s_after}pt")
                if not ok_line:
                    req_list.append("Interlineado 2.0")
                    act_list.append(str(line_spacing))
                if not ok_indent:
                    req_list.append("Sin sangría")
                    act_list.append(f"Sangría: izq {l_cm}cm")

                self._add("Acrónimos", "Formato Cabecera ACRÓNIMOS", "error",
                          "El título 'ACRÓNIMOS' debe estar centrado, en 16pt, en negrita, interlineado 2.0, con espaciado anterior 0pt y posterior 10pt, y sin sangría.",
                          ", ".join(req_list), ", ".join(act_list), p_idx=header_p['index'], p_text=txt_head)
            else:
                self._add("Acrónimos", "Formato Cabecera ACRÓNIMOS", "passed", "Título 'ACRÓNIMOS' correcto.", "Correcto", "Correcto", p_idx=header_p['index'], p_text=txt_head)

        # 3. Auditar Entradas
        for p in entries:
            txt = p['text'].strip()
            p_idx = p['index']
            
            # --- Regla: No deben estar dentro de una tabla ---
            if p.get('in_table', False):
                self._add("Acrónimos", "Estructura Acrónimos (No Tabla)", "error",
                          "La sección de acrónimos no debe redactarse dentro de una tabla. Debe redactarse como texto libre separado por tabulaciones.",
                          "Párrafos con tabulaciones", "Dentro de una tabla", p_idx=p_idx, p_text=txt)
                continue

            # --- Regla: Sin negrita ni cursiva ---
            bold = any(r.get('bold') for r in p.get('runs', []))
            italic = any(r.get('italic') for r in p.get('runs', []))
            
            if bold or italic:
                req_list = []
                act_list = []
                if bold:
                    req_list.append("Normal (Sin negrita)")
                    act_list.append("Negrita")
                if italic:
                    req_list.append("Normal (Sin cursiva)")
                    act_list.append("Cursiva")
                self._add("Acrónimos", "Estilo de Fuente Acrónimo", "error",
                          "Los acrónimos y sus significados en la hoja de acrónimos se escriben sin negrita ni cursiva.",
                          ", ".join(req_list), ", ".join(act_list), p_idx=p_idx, p_text=txt)

            # --- Regla: Formato 'ACRONIMO:' + \t ---
            colon_idx = txt.find(':')
            if colon_idx == -1:
                self._add("Acrónimos", "Formato de Dos Puntos", "error",
                          "El acrónimo o abreviatura debe estar seguido obligatoriamente de dos puntos (:).",
                          "Llevar dos puntos (ej. 'OMS:')", "Sin dos puntos", p_idx=p_idx, p_text=txt)
            else:
                prefix = txt[:colon_idx]
                if prefix and prefix[-1].isspace():
                    self._add("Acrónimos", "Espacio antes de Dos Puntos", "error",
                              "No debe haber ningún espacio entre el acrónimo y los dos puntos (ej. 'CADH:' y no 'CADH :').",
                              "Sin espacio antes de los dos puntos", "Con espacio antes de los dos puntos", p_idx=p_idx, p_text=txt)
                
                suffix = txt[colon_idx + 1:]
                # Verificamos si hay al menos un carácter de tabulación '\t'
                if '\t' not in suffix:
                    self._add("Acrónimos", "Separación por Tabulaciones", "error",
                              "El espacio entre el acrónimo con su significado debe estar separado por tabulaciones.",
                              "Separado por tabulaciones (\\t)", "Espacios en lugar de tabulación", p_idx=p_idx, p_text=txt)

            # --- Regla: Alineación, Interlineado, Espaciado, Sangría ---
            align = p.get('alignment', 'left')
            line_spacing = p.get('line_spacing')
            s_before = p.get('spacing_before', 0)
            s_after = p.get('spacing_after', 0)
            l_cm = round((p.get('indent_left') or 0) / 567.0, 2)
            h_cm = round((p.get('indent_hanging') or 0) / 567.0, 2)

            ok_align = align == 'left'
            
            # Si hay más de 50 acrónimos, se acepta 1.0 o 1.5. De lo contrario, se exige 2.0.
            total_acronyms = len(entries)
            if total_acronyms > 50:
                targets = [1.0, 1.5]
                req_spacing_str = "1.0 o 1.5"
            else:
                targets = [2.0]
                req_spacing_str = "2.0"
                
            val_spacing = line_spacing if line_spacing is not None else 1.0
            ok_line = any(abs(val_spacing - target) < 0.25 for target in targets)
            
            ok_s_before = s_before < 1.0
            ok_s_after = s_after < 1.0
            ok_l_cm = abs(l_cm - 0.0) <= 0.1
            ok_h_cm = abs(h_cm - 3.75) <= 0.25

            passed_layout = ok_align and ok_line and ok_s_before and ok_s_after and ok_l_cm and ok_h_cm

            if not passed_layout:
                req_list = []
                act_list = []
                if not ok_align:
                    req_list.append("Izquierda")
                    act_list.append(self._align_display(align))
                if not ok_line:
                    req_list.append(req_spacing_str)
                    act_list.append(str(line_spacing if line_spacing is not None else "Defecto/1.0"))
                if not ok_s_before:
                    req_list.append("Esp. ant 0pt")
                    act_list.append(f"{s_before}pt")
                if not ok_s_after:
                    req_list.append("Esp. post 0pt")
                    act_list.append(f"{s_after}pt")
                if not ok_l_cm:
                    req_list.append("Izq 0.0cm")
                    act_list.append(f"Izq {l_cm}cm")
                if not ok_h_cm:
                    req_list.append("Francesa 3.75cm")
                    act_list.append(f"Francesa {h_cm}cm")

                self._add("Acrónimos", "Formato de Párrafo de Acrónimo", "warning",
                          f"Las entradas de acrónimos deben tener alineación izquierda, interlineado de {req_spacing_str} (ya que la lista tiene {total_acronyms} acrónimos), espaciado anterior y posterior de 0pt, sangría izquierda de 0cm y francesa de 3.75cm.",
                          ", ".join(req_list), ", ".join(act_list), p_idx=p_idx, p_text=txt)
