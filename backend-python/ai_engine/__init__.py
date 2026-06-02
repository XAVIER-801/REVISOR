"""
ai_engine - Motor de IA autónomo del REVISOR.

Esta carpeta es PARALELA al motor de auditoría principal y NO interfiere con su
funcionamiento. Se activa de forma opcional para:

1. OCR (Reconocimiento Óptico de Caracteres) en documentos escaneados:
   - Hoja de Jurados (suele estar escaneada con firmas manuscritas)
   - Reporte de Similitud (Turnitin)
   - Autorización para Depósito (suele estar firmada y escaneada)
   - Declaración Jurada de Autenticidad
   - Anexos con documentos físicos

2. Sistema de aprendizaje propio (sin servicios pagados):
   - Aprende de cada tesis auditada
   - Identifica patrones de errores comunes
   - Sugiere mejoras basadas en el corpus acumulado
   - Mejora progresivamente con cada nueva auditoría

Tecnologías usadas (todas gratuitas/open source):
- pytesseract (Tesseract OCR de Google, gratuito)
- Pillow (manejo de imágenes)
- scikit-learn (opcional, para clasificación simple)
- numpy (manejo de datos)
- JSON (base de conocimiento persistente)

NO usa: Gemini, OpenAI, GPT, ni ningún servicio de pago.
"""
__version__ = "0.1.0"
__author__ = "REVISOR Team"
