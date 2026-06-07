# helpers_ps

Paqueteria de asistencia dentro de PS Perú

## Modulo Config.var_globs
Config.vars_globs

Contiene:

Variables globales del area como la paleta de colores de la compañía

## Modulo Grafico.graf
Grafico.graf import Graph_mtplt

Contiene:

class Graph_mtplt(
    dataframe = dataframe   | Un data frame para generar los graficos
)
funciones de grafica:
    .graph_line()            -> Genera un grafico de linea
    .graph_bar()             -> Genera un grafico de barras (agrupada / acumulada)
    .graph_box_whiskers()    -> Genera un grafico de tipo box plot con calculos de posiciones auto

funciones generales
    .save()                  -> Guarda los graficos en formato BytesIO en un dict
    .show()                  -> Grafica la imagen
    .plot()                  -> Para generar un nuevo plot estableciendo el ._fig y ._axes
    ._set_axis()             -> Para cambiar el eje de trabajo

funciones de caracteristicas generales:
    .set_titles()            -> Agrega titulo y subtitulo
    .add_source()            -> Agrega fuente de información o notas
    .add_legend()            -> Agrega leyenda al subplot en cuestion

Funciones de addicionales en la grafica:
    .etiqueta_valor()        -> Para agregar etiqueta en puntos de referencia
    .punto_valor()           -> Para agregar scatter plot en puntos especificos
    .shade_x_periods()       -> Sombreo de area

## Modulo Grafico.renderer

Grafico.renderer

Contiene:
funciones de asistencia

render_and_save_bytesio_dict()  -> Para renderizar y guardar graficos de dict de Bytes

## Modulo Bloomberg

** en desarrollo para poder importar info de bloomberg y guardar en cualquier formato 

## Modulo Calculo.helper_metricas
Calculo.helper_metricas import Metrics

Contiene:

class Metrics (
    dataframe=dataframe     |un data frame de forma index=fechas y columns=acción
    descripcion             |un data frame index = ticker + columna llamada "Nombre"
    )
funciones:
    .mtd()           -> retorna dataframe con serie de mtd para todas las columnas
    .ytd()           -> retorna dataframe con serie de ytd para todas las columnas
    .qtd()           -> retorna dataframe con serie de qtd para todas las columnas
    .drawdown()      -> retorna dataframe con serie de drawdown historico
    .rsi()           -> Calcula el RSI de cada uno de las series
    .sma()           -> Calcula la media movil simple para cada uno de las series
    .ema()           -> Calcula el exponential moving average
    .ranges()        -> Calcula los rangos de la serie sobre la media +- # de desviaciones
    .relative()      -> Calcula el (+,-,/,*) entre dos series y devuelve la serie ajustada
    .momentum()      -> Calcula indice de momentum simple
    .momentum_sma()  -> Calcula indice de momentum con SMA

    
