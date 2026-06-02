# Viñetas

## Símbolos PERMITIDOS

| Símbolo | Uso |
|---------|-----|
| `-` | Guion |
| `•` | Punto/bullet |
| `a)`, `b)` | Alfanumérico letra |
| `1)`, `2)` | Alfanumérico número |
| `(a)`, `(1)` | Entre paréntesis |

## Símbolos PROHIBIDOS

!!! danger "Detectados como error"
    El sistema rechaza estos símbolos automáticamente: `➢ ➔ ➤ → ⇒ ❑ ■ □ ◆ ◇ ▲ ▼ ● ○ ◉ ✓ ✔ ✗ ✘ ♦ ❖`

## Formato

| Atributo | Valor |
|----------|-------|
| Estilo | Normal (sin negrita) |
| Alineación | Justificada |
| Interlineado | 2.0 |
| Espaciado anterior | 0 pt |
| Espaciado posterior (intermedias) | 0 pt |
| Espaciado posterior (última) | **10 pt** |

## Sangrías según el nivel del título contextual

| Nivel del título | Sangría izquierda | Sangría francesa |
|------------------|-------------------|------------------|
| 1 y 2 | 0.5 cm | 0.75 cm |
| 3 | 1.75 cm | 0.75 cm |
| 4 y 5 | 3.0 cm | 0.75 cm |

## Consistencia de símbolo

!!! warning "Un único símbolo por lista"
    Dentro de un mismo bloque de viñetas debes usar **un único tipo de símbolo**. Lo mismo para sub-viñetas: un solo símbolo.

Ejemplo correcto:

```
- Primera viñeta
- Segunda viñeta
- Tercera viñeta
```

Ejemplo incorrecto:

```
- Primera viñeta
• Segunda viñeta   ❌ cambió el símbolo
- Tercera viñeta
```
