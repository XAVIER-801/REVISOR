# 📋 AUDITORÍA DE TABLAS Y FIGURAS - VALIDACIONES FALTANTES

## ✅ Ya Implementado

### Tablas (`tablas.py`):
- [x] Etiqueta: Alineación izquierda, Negrita, Sangría según nivel
- [x] Título: Cursiva, Sin negrita, Alineación izquierda, Sangría según nivel
- [x] Nota/Fuente: Debe tener dos puntos (:)
- [x] Detección de ausencia de Nota/Fuente

### Figuras (`figuras.py`):
- [x] Etiqueta: Alineación izquierda, Negrita, Sangría según nivel
- [x] Título: Cursiva, Sin negrita, Alineación izquierda, Sangría según nivel
- [x] Nota/Fuente: Debe tener dos puntos (:)
- [x] Detección de ausencia de Nota/Fuente

---

## ❌ FALTANTE - TABLAS

### 1. TAMAÑO DE FUENTE
- [ ] Etiqueta "Tabla X": debe ser **12pt**
- [ ] Título descriptivo: debe ser **12pt**
- [ ] Contenido de tabla: debe ser **12pt** (encabezado)
- [ ] Nota/Fuente: debe ser **10pt**

### 2. ESPACIADO
- [ ] Etiqueta: anterior **0pt**, posterior **0pt**
- [ ] Título: anterior **0pt**, posterior **0pt**
- [ ] Nota/Fuente: anterior **0pt**, posterior **15pt** ⚠️ CRÍTICO

### 3. INTERLINEADO
- [ ] Etiqueta: **2.0**
- [ ] Título: **2.0**
- [ ] Contenido de tabla: **1.0 o 1.5**
- [ ] Nota/Fuente: **1.5**

### 4. ENCABEZADO DE TABLA
- [ ] Primera fila debe estar **CENTRADA**
- [ ] Primera fila debe estar **NEGRITA**
- [ ] Líneas horizontales presentes (formato APA)

### 5. REQUISITOS GENERALES
- [ ] Tabla NO debe ser imagen (importar desde Excel)
- [ ] Si se extiende a 2 hojas: encabezado en ambas páginas
- [ ] Alineada con margen izquierdo del nivel

---

## ❌ FALTANTE - FIGURAS

### 1. TAMAÑO DE FUENTE
- [ ] Etiqueta "Figura X": debe ser **12pt**
- [ ] Título descriptivo: debe ser **12pt**
- [ ] Nota/Fuente: debe ser **10pt**

### 2. ESPACIADO
- [ ] Etiqueta: anterior **0pt**, posterior **0pt**
- [ ] Título: anterior **0pt**, posterior **0pt**
- [ ] Nota/Fuente: anterior **0pt**, posterior **15pt** ⚠️ CRÍTICO

### 3. INTERLINEADO
- [ ] Etiqueta: **2.0**
- [ ] Título: **2.0**
- [ ] Nota/Fuente: **1.5**

### 4. REQUISITOS GENERALES
- [ ] Si ocupa 2 páginas: comienza en primer renglón de página siguiente
- [ ] Alineada con margen izquierdo del nivel
- [ ] Calidad óptima (detectable?)

---

## 📊 MATRIZ DE IMPLEMENTACIÓN

| Validación | Tablas | Figuras | Prioridad |
|-----------|--------|---------|-----------|
| Tamaño etiqueta (12pt) | ❌ | ❌ | 🔴 ALTA |
| Tamaño título (12pt) | ❌ | ❌ | 🔴 ALTA |
| Tamaño nota (10pt) | ❌ | ❌ | 🔴 ALTA |
| Espaciado ant. etiqueta (0pt) | ❌ | ❌ | 🟡 MEDIA |
| Espaciado post. etiqueta (0pt) | ❌ | ❌ | 🟡 MEDIA |
| Espaciado ant. título (0pt) | ❌ | ❌ | 🟡 MEDIA |
| Espaciado post. título (0pt) | ❌ | ❌ | 🟡 MEDIA |
| Espaciado post. nota (15pt) | ❌ | ❌ | 🔴 ALTA |
| Interlineado etiqueta (2.0) | ❌ | ❌ | 🟡 MEDIA |
| Interlineado título (2.0) | ❌ | ❌ | 🟡 MEDIA |
| Interlineado contenido (1.0/1.5) | ❌ | N/A | 🟡 MEDIA |
| Interlineado nota (1.5) | ❌ | ❌ | 🟡 MEDIA |
| Encabezado centrado | ❌ | N/A | 🔴 ALTA |
| Encabezado negrita | ❌ | N/A | 🔴 ALTA |

---

## 🎯 ORDEN DE IMPLEMENTACIÓN

### Fase 1 (CRÍTICA) - Espaciado posterior de Nota: 15pt
```
PRIORIDAD: 🔴 ROJA
RAZÓN: Es el requisito más diferente y fácil de perder
IMPACTO: Bloquea depósito si no está correcto
```

### Fase 2 (ALTA) - Tamaños de fuente
```
PRIORIDAD: 🔴 ROJA
RAZÓN: Especificado en guía, fácil de validar
IMPACTO: Mejora validación general
```

### Fase 3 (MEDIA) - Espaciado anterior/posterior
```
PRIORIDAD: 🟡 NARANJA
RAZÓN: Consistencia con contenido
IMPACTO: Formato más limpio
```

### Fase 4 (MEDIA) - Interlineado
```
PRIORIDAD: 🟡 NARANJA
RAZÓN: Especificado pero raro verlo incorrecto
IMPACTO: Consistencia total
```

---

## 💾 Archivos a Modificar

```
backend-python/services/auditors/
├── tablas.py              → Agregar tamaño, espaciado, interlineado, encabezado
└── figuras.py             → Agregar tamaño, espaciado, interlineado
```

---

## 📝 NOTAS IMPLEMENTACIÓN

1. **Tamaño de fuente**: Usar `p['runs'][0].get('size', 0)` para obtener pts
2. **Espaciado**: `p.get('spacing_before')` y `p.get('spacing_after')`
3. **Interlineado**: `p.get('line_spacing')`
4. **Encabezado tabla**: Detectar primera fila dentro de tabla, validar centrado + negrita
5. **Nota/Fuente spacing posterior**: ERROR si no es 15pt ±2.0

