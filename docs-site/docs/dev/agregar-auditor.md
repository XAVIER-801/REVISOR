# Cómo agregar un nuevo auditor

Los auditores son módulos independientes que validan un aspecto específico de la tesis.

## Paso 1: Crear archivo

`backend-python/services/auditors/mi_auditor.py`:

```python
"""
mi_auditor.py - Descripción de qué valida.

Reglas implementadas:
- Regla 1: ...
- Regla 2: ...
"""
from .base_auditor import BaseAuditor


class MiAuditor(BaseAuditor):

    def audit(self):
        for i, p in enumerate(self.paragraphs):
            if not p.get("is_in_body"):
                continue
            txt = p["text"].strip()
            if not txt:
                continue

            # Tu lógica de validación
            if alguna_condicion_de_error:
                self._add(
                    "Categoría",                  # category
                    f"Nombre de la regla",        # rule
                    "error",                       # status: error|warning|observation|passed
                    "Mensaje descriptivo",         # message
                    "Esperado",                    # expected
                    "Hallado",                     # actual
                    p_idx=p["index"],
                    p_text=txt,
                )
```

## Paso 2: Registrar en `word_engine.py`

```python
from services.auditors.mi_auditor import MiAuditor

# ... dentro de run_audit():
MiAuditor(self).audit()  # 🆕 Mi nuevo auditor
```

## Paso 3: Escribir tests

`backend-python/tests/test_mi_auditor.py`:

```python
from services.auditors.mi_auditor import MiAuditor

class MockEngine:
    def __init__(self, paragraphs):
        self.paragraphs = paragraphs
        self.results = []
        ...

def test_detecta_caso_x():
    auditor = MiAuditor.__new__(MiAuditor)
    auditor.engine = MockEngine([...])
    auditor.audit()
    assert any("..." in r["rule"] for r in auditor.engine.results)
```

## Datos disponibles en `self.paragraphs[i]`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `text` | str | Texto del párrafo |
| `norm` | str | Texto normalizado (sin tildes, mayúsculas) |
| `index` | int | Índice XML del párrafo |
| `runs` | list | Runs con `text`, `bold`, `italic`, `size`, `font` |
| `alignment` | str | `left`, `right`, `center`, `both` |
| `line_spacing` | float | Interlineado (1.0, 1.5, 2.0...) |
| `spacing_before` | float | Espaciado anterior en pt |
| `spacing_after` | float | Espaciado posterior en pt |
| `indent_left` | float | Sangría izquierda en cm |
| `indent_first` | float | Sangría primera línea en cm |
| `indent_hanging` | float | Sangría francesa en cm |
| `estimated_page` | int | Página estimada |
| `section` | str | Nombre de la sección actual |
| `style_id` | str | ID del estilo de Word |
| `in_table` | bool | Si el párrafo está dentro de una tabla |
| `is_table_header` | bool | Si es la primera fila de la tabla |
| `is_heading` | bool | Si es un título |
| `body_level` | int | Nivel del título contextual (0-5) |
| `is_in_body` | bool | Si está en el cuerpo (no preliminares/anexos) |
| `is_cover` | bool | Si está en la portada |
| `drawings` | list | Imágenes con dimensiones |
| `has_omml` | bool | Si tiene fórmulas matemáticas |
| `has_textbox` | bool | Si contiene cuadros de texto |
| `tbl_id` | int | ID de la tabla a la que pertenece |

## Métodos útiles de `BaseAuditor`

- `self._add(category, rule, status, message, expected, actual, p_idx, p_text)` — registra una observación
- `self._norm(text)` — normaliza texto (sin tildes, mayúsculas)
- `self._get_p_props(paragraph)` — retorna `(size, bold, italic, font)`
- `self._find_context_level(idx)` — encuentra el nivel del último título antes del párrafo
- `self.anexos_start_idx` — índice donde empiezan los anexos
- `self.last_index_idx` — índice donde termina el índice general
