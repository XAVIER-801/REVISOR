# Capítulos y títulos (Niveles 1-5)

## CAPÍTULO X (etiqueta)

| Atributo | Valor |
|----------|-------|
| Tamaño | **16 pt** |
| Estilo | Negrita |
| Alineación | Centrada |
| Espaciado anterior | 0 pt |
| Espaciado posterior | **5 pt** |
| Interlineado | 2.0 |
| Sangría | Ninguna |
| Tilde | Obligatoria (CAPÍTULO, no CAPITULO) |

## Título del capítulo (INTRODUCCIÓN, REVISIÓN DE LITERATURA, etc.)

| Atributo | Valor |
|----------|-------|
| Tamaño | **14 pt** |
| Estilo | Negrita |
| Alineación | Centrada |
| Espaciado anterior | 0 pt |
| Espaciado posterior | 10 pt |
| Interlineado | 2.0 |

## Nivel 2 (1.1., 2.1., etc.) en MAYÚSCULAS

| Atributo | Valor |
|----------|-------|
| Tamaño | 12 pt |
| Estilo | Negrita |
| Alineación | Justificada |
| Espaciado | 0 / 10 pt |
| Interlineado | 2.0 |
| Sangría izquierda | 0 cm |
| Sangría francesa | 1.25 cm |
| Capitalización | MAYÚSCULAS |

## Nivel 3 (1.1.1.) en minúsculas

| Atributo | Valor |
|----------|-------|
| Tamaño | 12 pt |
| Estilo | Negrita |
| Alineación | Justificada |
| Espaciado | 0 / 10 pt |
| Sangría izquierda | 1.25 cm |
| Sangría francesa | 1.25 cm |
| Capitalización | Minúscula (primera letra mayúscula) |

## Niveles 4 y 5 en minúsculas

| Atributo | Valor |
|----------|-------|
| Tamaño | 12 pt |
| Estilo | Negrita |
| Alineación | Justificada |
| Espaciado | 0 / 10 pt |
| Sangría izquierda | **2.5 cm** |
| Sangría francesa | **1.5 cm** |
| Capitalización | Minúscula (primera letra mayúscula) |

## Secuencia jerárquica

!!! danger "Regla estricta"
    No se permite saltar niveles. La secuencia debe ser 1 → 2 → 3 → 4 → 5.
    Si pasas de Nivel 1 directamente a Nivel 3 es **ERROR**.

Ejemplo correcto:

```
CAPÍTULO II                  (nivel 1)
REVISIÓN DE LITERATURA       (título de capítulo)
2.1. PLANTEAMIENTO            (nivel 2)
2.1.1. Antecedentes          (nivel 3)
2.1.1.1. Estudios previos    (nivel 4)
```

Ejemplo incorrecto:

```
CAPÍTULO II                  (nivel 1)
2.1.1. Antecedentes          (nivel 3) ❌ saltó nivel 2
```
