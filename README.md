# Helpers PS

Paquete privado de utilidades para análisis financiero, generación de gráficos institucionales y automatización de reportes.

## Documentación

La documentación principal se encuentra en la carpeta `docs/`.

Para levantar la documentación localmente:

```bash
pip install -r requirements-docs.txt
mkdocs serve
```

Luego abrir:

```text
http://127.0.0.1:8000
```

## Clase principal de gráficos

```python
from helpers_ps.Grafico.graf import Graph_mtplt
```

Funciones principales:

- `graph_line()`
- `graph_bar()`
- `graph_pie()`
- `graph_box_whiskers()`
- `plot()`
- `show()`
- `save()`
