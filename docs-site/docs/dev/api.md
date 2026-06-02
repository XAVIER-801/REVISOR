# API REST

Documentación interactiva: `http://localhost:8005/docs` (Swagger UI auto-generado por FastAPI).

## Endpoints

### Auditoría

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/audit` | Auditoría síncrona, respuesta inmediata |
| POST | `/audit/queue` | Encola tesis para procesamiento asíncrono |
| GET | `/audit/status/{task_id}` | Estado de una tarea encolada |
| GET | `/audit/result/{task_id}` | Resultado de tarea completada |
| GET | `/audit/queue/list` | Lista del estado de la cola |

### Estadísticas (ai_engine)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/ai/insights` | Resumen global de aprendizaje |
| GET | `/ai/stats/curiosities` | Estadísticas curiosas (dashboard) |
| GET | `/ai/stats/schools` | Ranking de escuelas profesionales |
| GET | `/ai/stats/faculties` | Ranking de facultades |
| GET | `/ai/stats/categories` | Errores por categoría |
| GET | `/ai/stats/writing` | Ranking de calidad de redacción |
| GET | `/ai/stats/top-errors` | Top N errores más frecuentes |

### Salud

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Estado del servicio |
| GET | `/` | Información general y lista de endpoints |

## Ejemplo: auditoría síncrona

```bash
curl -X POST http://localhost:8005/audit \
  -F "file=@mi_tesis.docx"
```

Respuesta:

```json
{
  "stats": { "score": 72, "errors": 45, "warnings": 110, "passed": 250 },
  "results": [ ... ],
  "annotatedBase64": "UEsDBBQABgAIAAAA...",
  "engine": "python-hifi",
  "ai_suggestions": [ ... ]
}
```

## Ejemplo: cola

```bash
# Encolar
TASK=$(curl -X POST http://localhost:8005/audit/queue -F "file=@tesis.docx" | jq -r '.task_id')

# Consultar estado
curl http://localhost:8005/audit/status/$TASK

# Cuando complete, obtener resultado
curl http://localhost:8005/audit/result/$TASK
```
