# REVISOR — Auditor automático de tesis UNAP

Bienvenido a la documentación oficial del **REVISOR**, el sistema de auditoría automática de formato y estructura de tesis del Vicerrectorado de Investigación de la **Universidad Nacional del Altiplano de Puno**.

## ¿Qué es REVISOR?

REVISOR es una plataforma web que verifica que tu tesis cumpla con las normas de la **Guía de Presentación de Tesis 2.0 UNAP**. Procesa archivos Word (.docx, .doc) y devuelve:

- Un **puntaje de cumplimiento** sobre 100
- Un **documento anotado** con comentarios al margen al estilo Turnitin
- Un **reporte interactivo** filtrable por categoría y severidad

## Características principales

!!! tip "Tecnologías 100% open source"
    Sin servicios de pago. Todo el procesamiento es local: Python + lxml para análisis XML, Tesseract para OCR, pyspellchecker para ortografía, spaCy para análisis lingüístico.

- **30+ auditores especializados** cubren cada aspecto de la guía
- **OCR opcional** para documentos escaneados (Hoja de Jurados, Turnitin, Autorización)
- **IA propia de aprendizaje** que mejora con cada tesis procesada
- **Detección de evasión** Turnitin (cuadros de texto, capturas con texto)
- **Privacidad total**: tu archivo se elimina inmediatamente después del análisis

## Inicio rápido

1. Visita la [plataforma web](http://localhost:3005)
2. Arrastra tu archivo .docx
3. Espera 30-60 segundos
4. Revisa el reporte y descarga el Word anotado

## Estructura de esta documentación

- **[Reglas de auditoría](reglas/config-general.md)** — Todas las reglas que el sistema valida, una por una, con ejemplos
- **[Errores frecuentes](errores-frecuentes.md)** — Los 10 errores que el 80% de las tesis cometen
- **[FAQ](faq.md)** — Preguntas frecuentes
- **[Para desarrolladores](dev/arquitectura.md)** — Cómo extender el sistema con nuevos auditores

## Documento oficial

Toda la lógica de validación parte de la **Guía de Presentación de Tesis 2.0** del Vicerrectorado de Investigación. Si encuentras discrepancias entre el sistema y la guía oficial, reporta el caso para corregirlo.
