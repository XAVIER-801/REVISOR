# Cómo usar el sistema

## 5 pasos simples

### 1. Subir tu tesis

Desde la pantalla principal, arrastra tu archivo `.docx` o haz clic en **Subir Tesis**. El sistema acepta archivos hasta 50 MB. Si subes un `.doc` antiguo, se convierte automáticamente.

!!! warning "Antes de subir"
    Cierra el archivo en Microsoft Word. Word bloquea el archivo mientras está abierto y puede causar errores de carga.

### 2. Esperar el análisis

El motor experto Python recorre **30+ auditores**:

- Portada (tamaños 18/16/14 pt, logo 4.33×4.68 cm, fuente Times New Roman)
- Hoja de Jurados (cargos, sangría 6 cm, nombres a 11 pt)
- Índices (formato Pág., relleno de puntos, hipervínculos, sangrías francesas exactas)
- Capítulos nivel 1-5 (espaciados, sangrías, mayúsculas/minúsculas según nivel)
- Tablas (encabezado centrado/negrita, Nota:/Fuente: cursiva, alineación izquierda)
- Figuras (igual que tablas, sin contenido tabular)
- Viñetas (solo guion, punto, alfanuméricos; sangrías por nivel)
- Anexos obligatorios (Declaración Jurada, Autorización para Depósito)
- Estilo de escritura (doble espacio, Enter múltiples, oraciones largas)
- Ortografía (errores tipográficos evidentes)
- Y muchos más

Tiempo estimado: **30 segundos a 2 minutos** según tamaño.

### 3. Revisar el reporte interactivo

El dashboard te muestra:

- **Puntaje de cumplimiento** (sobre 100)
- **Errores críticos** (rojo) que bloquean el depósito
- **Advertencias** (amarillo) para mejorar
- **Sugerencias** (verde claro / turquesa) opcionales

Puedes filtrar por categoría haciendo clic en cualquier sección del dashboard.

### 4. Descargar el Word auditado

Al hacer clic en **Descargar Reporte**, obtienes tu mismo documento de vuelta con:

| Color | Significado |
|-------|-------------|
| 🔴 Rojo | Error crítico (con comentario al margen) |
| 🟡 Amarillo | Advertencia (resaltado lateral) |
| 🟢 Verde claro | Sugerencia ortográfica |
| 🔵 Turquesa | Observación menor |

Cada comentario al margen sigue el formato:

```
OBSERVACIÓN DE FORMATO

Regla: ...
Categoría: ...
Severidad: ...

Hallado: ...
Requerido: ...

Descripción: ...

Ubicación: Página N
```

### 5. Corregir y volver a subir

Aplica las correcciones en tu Word original. **Vuelve a subir** el archivo y verifica que el puntaje subió y que ya no quedan errores críticos.

!!! success "Meta"
    Llegar a **90+/100** sin errores críticos antes del depósito en el Repositorio Institucional.

## Limitaciones

- El sistema verifica **formato y estructura**, no contenido académico
- El plagio se verifica por separado con Turnitin (REVISOR sí detecta técnicas de evasión)
- Algunas reglas pueden fallar en documentos con macros complejas o protección habilitada
