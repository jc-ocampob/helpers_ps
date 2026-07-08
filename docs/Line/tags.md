# Manejo de etiquetas

El manejo de etiquetas dentro de `graph_line` se apalanca de las funciones de ayuda `etiqueta_valor` y `punto_valor`; es decir, hereda las configuraciones disponibles.

## Como funciona el `tag_dot` en `graph_line`

`tag_dot` exige un diccionario donde el `key` representa un diferenciador unico y `value` es en si un diccionario que contiene la información necesaria para graficar las etiquetas. 

## Ejemplo basico

```python
tag_dot = {
    "key_distintivo_grupo":{
        "ticker": "SPX",
        "x_values":"all" | "last" | ["2025-12-31", "last", "2026-04-05"],
        "template": "{y_value:,.0f}" | "{x_value:,%b-%Y}: {y_value:,.0f}" | "{x_value:,%b-%Y}",
        "show": "dot_tag" | "tag" | "dot",
        "legend_label": "Momentos Claves",
        "dot": {
            "color": "green",
            "size": 22,
        },
        "tag": {
                "bg_color": "none",
                "font_color": "red"
        },
    }
}


```

---

## Ejemplo basico de etiquetas

```python
g = Graph_mtplt(df)

g.graph_line(
    tickers=["SPX"]
    tag_dot={
        # Agrega tag | dot | dot_tag a una serie de lineas
        "1": dict(                                                                       # key random solo para diferencia agrupación (permite agregar grupos de etiquetas configurables para una misma serie)
            ticker="SPX",                                                                # ticker (nombre de columna) de sobre la serie que se quiere trabajar
            x_values = ["last", pd.Timestamp("2025-12-31")],                             # puntos del eje x donde se quiere colocar x_values = "last" | x_values = "all" | x_values = ["last", "2025-04-05", ...]
            template = "{y_value:,.0f}",                                                 # template para el label que se quiere poner en la etiqueta
            show="dot_tag",                                                              # que se quiere mostrar show = dot (muestra solo punto) | show = tag (muestra solo la etiqueta) | dot_tag (muestra ambos etiqueta y punto)
            dot = dict(                                                                  # Hereda todas las funcionalidades de self.punto_valor()
                color="green",
                size=22,
            ),
            tag = dict(                                                                  # Hereda todas las funcionalidad de self.etiqueta_valor()
                bg_color="none"
            ),
            legend_label="Momentos Claves"                                               # Agregar a la leyenda los puntos dentro de una agrupación
        ),
        "2": dict(
            ticker="PX_LAST-RUO INDEX",
            x_values = [pd.Timestamp("2020-12-31")],
            template = "{y_value:,.0f}",
            show="dot_tag",
            dot = dict(
                size=22,
                zorder=50,
                color="red"
            ),
            tag = dict(
                bg_color="none",
                font_color="red"
            )
        ),
    },
)

g.show()
```

---

