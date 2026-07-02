# Helpers PS

Biblioteca interna desarrollada para automatización de análisis financieros, generación de gráficos institucionales y construcción de reportes.

## Componentes principales

### Bloomberg

Utilidades para descarga y procesamiento de información financiera.

### Cálculo

Funciones de apoyo para métricas financieras y análisis cuantitativo.

### Gráficos

Framework basado en `matplotlib` para generación de gráficos institucionales.

Clase principal:

```python
Graph_mtplt
```

### Presentaciones

Herramientas para generación automática de tablas y gráficos en PowerPoint.

---

## Inicio rápido

Si es la primera vez que utilizas el paquete, sigue el siguiente orden:

1. [Getting Started](getting_started.md)
2. [Quick Reference](quick_reference.md)
3. [graph_line](graph_line.md)
4. [graph_bar](graph_bar.md)
5. [graph_box_whiskers](graph_box_whiskers.md)
6. [Ejemplos](examples/line_last_value.md)

---

## Tipos de gráficos disponibles

| Método | Descripción |
|---|---|
| `graph_line()` | Series de tiempo y evolución de indicadores |
| `graph_bar()` | Barras simples, agrupadas y stacked |
| `graph_pie()` | Pie y Donut charts |
| `graph_box_whiskers()` | Distribuciones históricas por serie |

---

## Filosofía del framework

La librería busca:

- Reducir código repetitivo.
- Mantener formato institucional consistente.
- Facilitar anotaciones y etiquetas.
- Integrarse fácilmente con PowerPoint.
- Estandarizar colores, leyendas, fuentes y estilo visual.
