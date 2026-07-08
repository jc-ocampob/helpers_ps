# Manejo de etiquetas

El manejo de etiquetas dentro de `graph_line` se apalanca de las funciones de ayuda `etiqueta_valor` y `punto_valor`; es decir, hereda las configuraciones disponibles.

## Como funciona el `tag_dot` en `graph_line`

`tag_dot` exige un diccionario donde el `key` representa un diferenciador unico y `value` es en si un diccionario que contiene la información necesaria para graficar las etiquetas. 

## Ejemplo de diccionario para tag_dot

```python
tag_dot = {
    # Se genera un Key distintivo para agrupar las etiquetas
    "key_distintivo_grupo":{

        # ticker: str referencia el ticker sobre el cual se van a hacer las etiquetas
        "ticker": "SPX",

        # Valores x sobre el cual se quieren las etiquetas puede ser el ultimo, todos o una lista de las posiciones que se quieren
        "x_values":"all" | "last" | ["2025-12-31", "last", "2026-04-05"],
        
        # template gestiona la etiqueta como una plantilla con las variables
        # de x, y  disponibles para uso
        "template": "{y_value:,.0f}" | "{x_value:,%b-%Y}: {y_value:,.0f}" | "{x_value:,%b-%Y}",
        
        # Show es un str que gestiona que se quiere mostrar
        # se puede mostrar la etiqueta y punto o solo alguno
        "show": "dot_tag" | "tag" | "dot",

        # En caso es distinto de None se genera una referencia en la leyenda para estos puntos con el nombre de la serie
        # siendo el que se le asigue aqui
        "legend_label": "Momentos Claves",

        # Diccionario de control de los puntos del subgrupo que hereda toda la funcionalidad de
        # .punto_valor()
        "dot": {
            "color": "green",
            "size": 22,
        },

        # Diccionario de control de las etiquetas del subgrupo que hereda toda la funcionalidad de
        # .etiqueta_valor()
        "tag": {
                "bg_color": "none",
                "font_color": "red"
        },
    }
}


```

---

## Ejemplo basico de etiquetas

En este primer ejemplo se usa información del SPX y RTY en la que se genera 2 grupos de etiqutas uno para cada serie

```python
graph = Graph_mtplt(dataframe = _data)
graph.graph_line(
    figsize=(6,5),                                                                                                  # Configuración del tamaño de la figura sobre el cual se construye el grafico
    tickers = "all",                                                                                                # Tickers (nombre de columnas) que se van a mostrar: "all" = Todos | "ticker" | ["ticker1", "ticker2",..., "tickerN"]
    labels = ["S&P 500", "Russell 2000"],                                                                           # Labels de cada serie (Overwrite el column name): None = default usar tickers | ["label_of_ticker1", "label_of_ticker2",...,"label_of_tickerN"]
    colors = ["black"],                                                                                             # Colores de cada serie (Overwrite el color): None = default usar paleta CC | ["color_of_ticker1", "color_of_ticker2",...,"color_of_tickerN"]
    titles=dict(                                                                                                    # Hereda todas las funcionalidades de la función self.set_titles()
        title="Precio del SPX",
        subtitle="Evolución del precio del SPX desde 1990"
    ),                                                                                                              
    source = dict(                                                                                                  # Hereda todas las funcionalidades de la función self.add_source()
        text = [f"Fuente: Bloomberg, con información al cierre del","Nota 1: Maje estuvo aqui"]
    ),
    x_axis=dict(                                                                                                    # Hereda la funcionalidades de _prep_x_axis
        tick_step=25, 
        bbg_format=True,
        fmt="%b-%Y",
        lim = ("2015-01-01", None),
        fontsize=6
    ),
    tag_dot={ # Agrega tag | dot | dot_tag a una serie de lineas
        "1": dict(                                                                                                  # key random solo para diferencia agrupación (permite agregar grupos de etiquetas configurables para una misma serie)
            ticker="PX_LAST-SPX INDEX",                                                                             # ticker (nombre de columna) de sobre la serie que se quiere trabajar
            x_values = ["last", pd.Timestamp("2025-12-31")],                                                        # puntos del eje x donde se quiere colocar x_values = "last" | x_values = "all" | x_values = ["last", "2025-04-05", ...]
            template = "{y_value:,.0f}",                                                                            # template para el label que se quiere poner en la etiqueta
            show="dot_tag",                                                                                         # que se quiere mostrar show = dot (muestra solo punto) | show = tag (muestra solo la etiqueta) | dot_tag (muestra ambos etiqueta y punto)
            dot = dict(                                                                                             # Hereda todas las funcionalidades de self.punto_valor()
                color="green",
                size=22,
            ),
            tag = dict(                                                                                             # Hereda todas las funcionalidad de self.etiqueta_valor()
                bg_color="none"
            ),
            legend_label="Momentos Claves"
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
    legend = dict(
        show = True,
        ncol=1
    ),
)

g.show()
```

images/line_graph.png

---

