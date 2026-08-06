from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
import numpy as np
from scipy.stats import norm
from functools import wraps
from typing import Callable, Literal


@dataclass
class Metrics():
    """
    Clase diseñada para hacer calculos sobre un data frame con multiples series de precios

    Parametros
    -------------
    data_frame: Pandas data frame donde hay una estructura de index = Fecha y columna = activo 
    """
    data_frame: pd.DataFrame = None                 # Data Frame en forma de indice = Fechas y columnas = serie de precios
    descripcion: pd.DataFrame | None = None         # Base de descripción
    relation: pd.DataFrame = None                   # Base de relaciones entre la descripción de las columnas del dataframe y el dataframe
    fallback: bool = True                           # Variable de control para cuando se hace calculos como MTD, YTD, QTD y la serie empieza en dia intermedio se calcule desde dicha fecha

    # Validación del dataframe
    def __post_init__(self):
        # Verificar que el Data Frame no este vacio
        if self.data_frame is None or self.data_frame.empty:
            raise ValueError("El dataframe no puede estar vacío")
        
        # Verificar que el índice sea de tipo fecha
        if not pd.api.types.is_datetime64_any_dtype(self.data_frame.index):
            raise TypeError("El índice del dataframe debe ser de tipo fecha")

        # Generar la relacion entra las columnas del Data Frame y su descripción
        if self.descripcion is not None:
            relation = {
                "ticker": self.data_frame.columns,
                "Nombre": [],
            }

            for ticker in self.data_frame.columns:
                if "-" in ticker:
                    ticker_base = ticker.split("-")[1]
                else:
                    ticker_base = ticker
                
                if ticker_base in self.descripcion.index:
                    nombre = self.descripcion.loc[self.descripcion.index == ticker_base, "Nombre"].item()
                else:
                    nombre = ticker_base

                relation["Nombre"].append(nombre)

            self.relation = pd.DataFrame.from_dict(relation)
            self.relation = self.relation.set_index("ticker")

    # Funcion para asignar nombres en base a descripcion
    def assign_names(self, data_frame: pd.DataFrame = None) -> pd.DataFrame:
        if self.relation is None:
            raise ValueError("No se ha proporcionado una descripción para asignar nombres")
        
        if data_frame is None:
            data_frame = self.data_frame

        mapping = self.relation["Nombre"].to_dict()

        tickers_sorted = sorted(mapping.keys(), key=len, reverse=True)

        new_columns = []
        for col in data_frame.columns:
            new_col = col
            for ticker in tickers_sorted:
                if ticker in col:
                    new_col = col.replace(ticker, mapping[ticker])
            new_columns.append(new_col)
        
        data_frame.columns = new_columns
        return data_frame

    # Función para calcular el Year-to-Date (YTD) de un DataFrame 
    def ytd(self, naming: bool = False) -> pd.DataFrame:
        """
        Calcula el Year-To-Date (YTD) para las series precios de un DataFrame.

        Retorna:
        --------------
        pd.DataFrame
            DataFrame con los YTD calculados para cada serie de precios
        """

        df = self.data_frame.sort_index()

        # Año de cada fecha
        yr = df.index.to_period("Y")

        # Último precio válido del año (cierre del año)
        year_end_prices = (
            df.groupby(yr)
            .apply(lambda g: g.ffill().iloc[-1])
        )

        # Año previo de cada fecha (base principal)
        prev_period = (df.index - pd.offsets.YearEnd(1)).to_period("Y")

        prev_year_bases = year_end_prices.reindex(prev_period)
        prev_year_bases.index = df.index
        prev_year_bases = prev_year_bases.reindex(columns=df.columns)

        # Fallback: primer precio válido del año actual (cuando no haya base del año previo)
        if self.fallback:
            first_in_year = (
                df.groupby(yr)
                .apply(lambda g: g.bfill().iloc[0])  # <-- OJO: bfill, no ffill
            )

            # Alinear por AÑO ACTUAL, no por prev_period
            first_in_year = first_in_year.reindex(yr)
            first_in_year.index = df.index
            first_in_year = first_in_year.reindex(columns=df.columns)

            prev_year_bases = prev_year_bases.combine_first(first_in_year)

        # Validaciones de alineación
        if not prev_year_bases.index.equals(df.index):
            raise RuntimeError("Index mismatch after alignment.")

        if list(prev_year_bases.columns) != list(df.columns):
            raise RuntimeError("Columns mismatch after alignment.")

        assert df.shape == prev_year_bases.shape, (
            f"Shape mismatch: df {df.shape} vs bases {prev_year_bases.shape}"
        )

        ytd = df.div(prev_year_bases) - 1
        return ytd

    # Función para calcular el Month-to-Date (MTD) de un DataFrame 
    def mtd (self) -> pd.DataFrame:
        """
        Calcula el Month-To-Date (MTD) para las series precios de un DataFrame.

        Retorna:
        --------------
        pd.Dataframe
            DataFrame con los MTD calculados para cada serie de precios

        """
        # Ordenar el Data frame por indice de fecha ascendente
        df = self.data_frame.sort_index()

        # Agrupar por mes
        mon = df.index.to_period('M')

        # Último precio válido por mes y activo
        month_end_prices = (
            df.groupby(mon)
            .apply(lambda g: g.ffill().iloc[-1])
        )

        # Para cada fila mappear la base = precio del ultimo dias del mes previo
        prev_mon = (df.index - pd.offsets.MonthEnd(1)).to_period('M')
        prev_month_bases = month_end_prices.reindex(prev_mon)

        # alinear las bases para que coincidan con el índice original
        prev_month_bases.index = df.index
        prev_month_bases = prev_month_bases.reindex(columns=df.columns)

        # Fallback opcional: para usar el primer precio valido del mes actual
        if self.fallback:
            first_in_month = (
                df.groupby(mon)
                .apply(lambda g: g.ffill().iloc[0])
            )
            first_in_month = first_in_month.reindex(mon)  # same PeriodIndex as current month
            first_in_month.index = df.index
            first_in_month = first_in_month.reindex(columns=df.columns)
            prev_month_bases = prev_month_bases.combine_first(first_in_month)

        # Validación de información alineada
        assert df.shape == prev_month_bases.shape, f"Shape mismatch: df {df.shape} vs bases {prev_month_bases.shape}"
        assert df.index.equals(prev_month_bases.index), "Index mismatch after alignment."
        assert list(df.columns) == list(prev_month_bases.columns), "Columns mismatch after alignment."

        # Calcular MTD
        mtd = df.div(prev_month_bases) - 1
        
        return mtd

    # Funcion para calcular el Quarter-to Date (QTD) en un DataFrame
    def qtd (self) -> pd.DataFrame:
        """
        Calcula el Quarter-To-Date (QTD) para las series precios de un DataFrame.

        Retorna:
        --------------
        pd.Dataframe
            DataFrame con los QTD calculados para cada serie de precios

        """
        # Ordenar el Data frame por indice de fecha ascendente
        df = self.data_frame.sort_index()

        # Agrupar por trimestre
        qtr = df.index.to_period('Q')

        # Ultimo precio válido por trimstre y activo
        quarter_end_prices = (
            df.groupby(qtr)
            .apply(lambda g: g.ffill().iloc[-1])
        )

        # Para cada fila mappear la base = precio del ultimo dia del trimestre previo
        prev_qtr = (df.index - pd.offsets.QuarterEnd(1)).to_period('Q')
        prev_quarter_bases = quarter_end_prices.reindex(prev_qtr)

        # Alinear las bases para que coincidan con el índice original
        prev_quarter_bases.index = df.index
        prev_quarter_bases = prev_quarter_bases.reindex(columns=df.columns)

        # Fallback opcional: usar el primer precio válido del trimestre actual
        if self.fallback:
            first_in_quarter = (
                df.groupby(qtr)
                .apply(lambda g: g.ffill().iloc[0])
            )
            first_in_quarter = first_in_quarter.reindex(qtr)  # align to current quarter PeriodIndex
            first_in_quarter.index = df.index
            first_in_quarter = first_in_quarter.reindex(columns=df.columns)
            prev_quarter_bases = prev_quarter_bases.combine_first(first_in_quarter)

        # Validación de información alineada
        assert df.shape == prev_quarter_bases.shape, f"Shape mismatch: df {df.shape} vs bases {prev_quarter_bases.shape}"
        assert df.index.equals(prev_quarter_bases.index), "Index mismatch after alignment."
        assert list(df.columns) == list(prev_quarter_bases.columns), "Columns mismatch after alignment."

        # Calcular QTD
        qtd = df.div(prev_quarter_bases) - 1

        return qtd

    # Funcion para calcular el drwdown de un DataFrame
    def drawdown (self, method: str = "simple", min_price: float = 1e-6) -> pd.DataFrame:
        """
        Calcula el drawdown para las series de precios de un DataFrame.

        Parámetros:
        --------------
        method: {"simple", "log"}
            Método para calcular el drawdown:
            - "simple": basado en retornos simples
            - "log": basado en retornos logarítmicos
        
        min_price: float
            Precio mínimo para evitar divisiones por cero

        Retorna:
        --------------
        pd.Dataframe
            DataFrame con los drawdowns calculados para cada serie de precios
        """
        # Ordenar el Data frame por indice de fecha ascendente
        px = self.data_frame.sort_index()

        # Limpiar invalido/cero valores a evitar problemas con la división por 0
        px = px.where(px > min_price)

        if method == "simple":
            # Forward-fill within each column so cummax works past short gaps.
            px_ff = px.ffill()
            roll_max = px_ff.cummax()
            dd = px.divide(roll_max) - 1.0
        elif method == "log":
            logp = np.log(px)
            logp_ff = logp.ffill()
            roll_max_log = logp_ff.cummax()
            dd = np.exp(logp - roll_max_log) - 1.0
        else:
            raise ValueError("method must be 'simple' or 'log'")

        return dd

    # Calculo de la desviación estandard al downside
    def std_downside(
        self,
        method: str = "simple",
        target_return: float = 0.0,
        annualize: bool = False,
        periods_per_year: int = 252,
    ) -> pd.DataFrame:
        """
        Downside standard deviation by asset.
        """

        px = self.data_frame.sort_index()

        if method == "simple":
            rets = px.pct_change()
        elif method == "log":
            rets = np.log(px / px.shift(1))
        else:
            raise ValueError("method must be 'simple' or 'log'")

        downside = (rets - target_return).where(rets < target_return, 0.0)

        dsd = np.sqrt((downside**2).mean())

        if annualize:
            dsd *= np.sqrt(periods_per_year)

        return dsd.to_frame(name="std_downside")

    # Calculo del beta (rolling / historico)
    def beta(
        self,
        benchmark: str,
        window: int | None = None,
        method: str = "simple",
    ) -> pd.Series | pd.DataFrame:
        """
        Calculate historical or rolling beta relative to a benchmark.

        Parameters
        ----------
        benchmark : str
            Benchmark column name.

        window : int, optional
            Rolling window size.
            If None, computes historical beta.
            If provided, computes rolling beta.

        method : {"simple", "log"}
            Return calculation method.

        Returns
        -------
        pd.Series
            Historical beta for each asset when window is None.

        pd.DataFrame
            Rolling betas through time when window is provided.
        """

        px = self.data_frame.sort_index()

        if method == "simple":
            rets = px.pct_change()
        elif method == "log":
            rets = np.log(px / px.shift(1))
        else:
            raise ValueError("method must be 'simple' or 'log'")

        benchmark_returns = rets[benchmark]

        # Historical beta
        if window is None:
            bench_var = benchmark_returns.var()

            beta = rets.apply(
                lambda col: col.cov(benchmark_returns) / bench_var
            )

            return beta

        # Rolling beta
        bench_var = benchmark_returns.rolling(window).var()

        rolling_beta = (
            rets.rolling(window)
            .cov(benchmark_returns)
            .divide(bench_var, axis=0)
        )

        return rolling_beta

    # Upisde capture
    def upside_capture(
        self,
        benchmark: str,
        method: str = "simple",
    ) -> pd.Series:
        """
        Calculate upside capture ratio relative to a benchmark.
        """

        px = self.data_frame.sort_index()

        if method == "simple":
            rets = px.pct_change()
        elif method == "log":
            rets = np.log(px / px.shift(1))
        else:
            raise ValueError("method must be 'simple' or 'log'")

        bench = rets[benchmark]

        mask = bench > 0

        asset_up = (1 + rets[mask]).prod() - 1
        bench_up = (1 + bench[mask]).prod() - 1

        return asset_up / bench_up

    # Downside Capture
    def downside_capture(
        self,
        benchmark: str,
        method: str = "simple",
    ) -> pd.Series:
        """
        Calculate downside capture ratio relative to a benchmark.
        """

        px = self.data_frame.sort_index()

        if method == "simple":
            rets = px.pct_change()
        elif method == "log":
            rets = np.log(px / px.shift(1))
        else:
            raise ValueError("method must be 'simple' or 'log'")

        bench = rets[benchmark]

        mask = bench < 0

        asset_down = (1 + rets[mask]).prod() - 1
        bench_down = (1 + bench[mask]).prod() - 1

        return asset_down / bench_down

    # UC /DC ratio
    def capture_ratio(
        self,
        benchmark: str,
        method: str = "simple",
    ) -> pd.Series:
        """
        Calculate upside/downside capture ratio.
        """

        uc = self.upside_capture(
            benchmark=benchmark,
            method=method,
        )

        dc = self.downside_capture(
            benchmark=benchmark,
            method=method,
        )

        return uc / dc

    # Value at risk 
    def var(
        self,
        confidence: float = 0.95,
        method: str = "historical",
        returns_method: str = "simple",
        horizon: int = 1,
    ) -> pd.Series:
        """
        Calculate Value at Risk (VaR) for all assets.

        Parameters
        ----------
        confidence : float, default 0.95
            Confidence level.

        method : {"historical", "gaussian", "cornish_fisher"}
            VaR methodology:
                - historical: non-parametric historical simulation
                - gaussian: parametric normal VaR
                - cornish_fisher: skewness/kurtosis adjusted VaR

        returns_method : {"simple", "log"}
            Return calculation method.

        horizon : int, default 1
            Holding period in return periods.

        Returns
        -------
        pd.Series
            VaR expressed as a positive loss.
        """

        px = self.data_frame.sort_index()

        if returns_method == "simple":
            rets = px.pct_change().dropna()

        elif returns_method == "log":
            rets = np.log(px / px.shift(1)).dropna()

        else:
            raise ValueError(
                "returns_method must be 'simple' or 'log'"
            )

        alpha = 1 - confidence

        if method == "historical":

            # Non-parametric Historical Simulation VaR
            var = -rets.quantile(alpha)

        elif method == "gaussian":

            # Parametric Normal VaR
            z = norm.ppf(alpha)

            var = -(rets.mean() + z * rets.std())

        elif method == "cornish_fisher":

            # Modified VaR accounting for skewness and kurtosis
            z = norm.ppf(alpha)

            s = rets.skew()
            k = rets.kurtosis()

            z_cf = (
                z
                + ((z**2 - 1) * s / 6)
                + ((z**3 - 3 * z) * k / 24)
                - ((2 * z**3 - 5 * z) * s**2 / 36)
            )

            var = -(rets.mean() + z_cf * rets.std())

        else:
            raise ValueError(
                "method must be 'historical', 'gaussian', or 'cornish_fisher'"
            )

        if horizon > 1:
            var *= np.sqrt(horizon)

        return var.rename(
            f"VaR_{method}_{int(confidence * 100)}"
        )

    # Tracking error
    def tracking_error(
        self,
        benchmark: str,
        method: str = "simple",
        annualize: bool = True,
        periods_per_year: int = 252,
    ) -> pd.Series:
        """
        Calculate tracking error relative to a benchmark.

        Parameters
        ----------
        benchmark : str
            Benchmark column name.

        method : {"simple", "log"}
            Return calculation method.

        annualize : bool, default True
            Annualize the result.

        periods_per_year : int, default 252
            Periods per year.

        Returns
        -------
        pd.Series
            Tracking error by asset.
        """

        px = self.data_frame.sort_index()

        if method == "simple":
            rets = px.pct_change()

        elif method == "log":
            rets = np.log(px / px.shift(1))

        else:
            raise ValueError(
                "method must be 'simple' or 'log'"
            )

        benchmark_returns = rets[benchmark]

        active_returns = rets.sub(
            benchmark_returns,
            axis=0
        )

        te = active_returns.std()

        if annualize:
            te *= np.sqrt(periods_per_year)

        return te.rename("Tracking Error")

    # Information Ratio
    def information_ratio(
        self,
        benchmark: str,
        method: str = "simple",
        annualize: bool = True,
        periods_per_year: int = 252,
    ) -> pd.Series:

        px = self.data_frame.sort_index()

        if method == "simple":
            rets = px.pct_change()
        elif method == "log":
            rets = np.log(px / px.shift(1))
        else:
            raise ValueError(
                "method must be 'simple' or 'log'"
            )

        active_returns = rets.sub(
            rets[benchmark],
            axis=0
        )

        active_return = active_returns.mean()
        tracking_error = active_returns.std()

        ir = active_return / tracking_error

        if annualize:
            ir *= np.sqrt(periods_per_year)

        return ir.rename("Information Ratio")

    # Excess return
    def excess_return(
        self,
        benchmark: str,
        period: str = "qtd"
    ) -> pd.DataFrame:
        
        if period == "ytd":
            _d = self.ytd()
        elif period == "mtd":
            _d = self.mtd()
        elif period == "qtd":
            _d = self.qtd()
        else:
            raise NotImplementedError(f"{period} no esta implementado")
        
        _d = _d.sub(_d[benchmark], axis=0)
        
        return _d

    # Constsitencia de excess return
    def consistency(
        self,
        benchmark: str,
        period: str = "qtd"
    ) -> pd.Series:
        """
        Percentage of periods in which the asset outperformed
        the benchmark.

        Returns
        -------
        pd.Series
            Ticker | Consistency
        """

        exre = self.excess_return(
            benchmark=benchmark,
            period=period
        )

        consistency = exre.gt(0).sum() / exre.notna().sum()

        return consistency.rename("Consistency")

    # Función para calcular el RSI de un DataFrame
    def rsi (self, window: int = 14, prefix: str = "RSI{w}_") -> pd.DataFrame:
        """
        Calcula el Relative Strength Index (RSI) para las series precios de un DataFrame.

        Parámetros:
        --------------
        window: int
            Ventana (en número de períodos) para calcular el RSI.
        
        prefix: str
            prefix para nombrar las columnas resultantes, donde {w} será reemplazado por la ventana correspondiente.
        
        Retorna:
        --------------
        pd.Dataframe
            DataFrame con los RSI calculados para cada serie de precios

        """
        # Ordenar el Data frame por indice de fecha ascendente
        df = self.data_frame.sort_index()
        
        delta = df.diff()

        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)

        avg_gain = gain.rolling(window=window, min_periods=window).mean()
        avg_loss = loss.rolling(window=window, min_periods=window).mean()

        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))

        rsi.columns = [f"{prefix.format(w=window)}{c}" for c in df.columns]

        return rsi

    # Función para calcular el SMA de un DataFrame
    def sma (self, windows: list[int] = [50], min_periods: int | None = None, prefix: str = "SMA{w}_") -> pd.DataFrame:
        """
        Calcula el Simple Moving Average (SMA) para las series precios de un DataFrame en diferentes ventanas de evaluación.

        Parámetros:
        --------------
        windows: list[int]
            Lista de ventanas (en número de períodos) para calcular el SMA.
        
        min_periods: int | None
            Número mínimo de períodos requeridos para calcular el SMA. Si es None, se usa el valor de la ventana.
        
        prefix: str
            prefix para nombrar las columnas resultantes, donde {w} será reemplazado por la ventana correspondiente.
        
        Retorna:
        --------------
        pd.Dataframe
            DataFrame con los SMA calculados para cada serie de precios y ventana

        """
        # Ordenar el Data frame por indice de fecha ascendente
        df = self.data_frame.sort_index()
        
        frames = []
        for w in windows:
            mp = w if min_periods is None else min_periods
            sma = df.rolling(window=w, min_periods=mp).mean()
            sma.columns = [f"{prefix.format(w=w)}{c}" for c in df.columns]
            frames.append(sma)
        
        return pd.concat(frames, axis=1)

    # Función para calcular el EMA de un DataFrame
    def ema (self, windows: list[int] = [27], min_periods: int | None = None, prefix: str = "EMA{w}_") -> pd.DataFrame:
        """
        Calcula el Exponential Moving Average (EMA) para las series precios de un DataFrame en diferentes ventanas de evaluación.

        Parámetros:
        --------------
        windows: list[int]
            Lista de ventanas (en número de períodos) para calcular el EMA.
        
        min_periods: int | None
            Número mínimo de períodos requeridos para calcular el EMA. Si es None, se usa el valor de la ventana.
        
        prefix: str
            prefix para nombrar las columnas resultantes, donde {w} será reemplazado por la ventana correspondiente.
        
        Retorna:
        --------------
        pd.Dataframe
            DataFrame con los EMA calculados para cada serie de precios y ventana

        """
        # Ordenar el Data frame por indice de fecha ascendente
        df = self.data_frame.sort_index()
        
        frames = []
        for w in windows:
            mp = w if min_periods is None else min_periods
            ema = df.ewm(span=w, min_periods=mp).mean()
            ema.columns = [f"{prefix.format(w=w)}{c}" for c in df.columns]
            frames.append(ema)
        
        return pd.concat(frames, axis=1)
    
    def ranges (self, desviaciones: list[int] = [-1, 0, 1], prefix: str = "Media({w}sigma)_") -> pd. DataFrame:
        
        # Mean and standard deviation per column
        mean = self.data_frame.mean()
        std = self.data_frame.std()

        final = None

        for col in self.data_frame.columns:
            for w in desviaciones:
                col_name = prefix.format(w=w)
                if final is None:
                    _temp = self.data_frame[[col]].copy()
                    _temp[f"{col_name}{col}"] = mean[mean.index==col].item() + w * std[std.index==col].item()
                    _temp = _temp.drop(columns=[col])
                    final = _temp
                else:
                    final[f"{col_name}{col}"] = mean[mean.index==col].item() + w * std[std.index==col].item()

        return final
    
    def relative (self, 
                   ticker_list: list[str] = None, 
                   relative_list: list[str] = None, 
                   operation_list: list[str] = None,
                   names: bool = False,
                   ) -> pd.DataFrame:
        
        # validar que la informacion de parametros sea consistente
        if ticker_list is None or relative_list is None or operation_list is None:
            raise ValueError("ticker_list, relative_list y operation_list no pueden ser None")
        
        if not (len(ticker_list) == len(relative_list) == len(operation_list)):
            raise ValueError("ticker_list, relative_list y operation_list deben tener la misma longitud")
        
        for ticker in ticker_list:
            if ticker not in self.data_frame.columns:
                raise ValueError(f"Ticker '{ticker}' no encontrado en el DataFrame")
        
        for relative in relative_list:
            if relative not in self.data_frame.columns and relative != "1":
                raise ValueError(f"Relative '{relative}' no encontrado en el DataFrame ni es '1'")
        
        # Calcular los relativos
        final = None
        for _i in range(len(ticker_list)):
            ticker = ticker_list[_i]
            relative = relative_list[_i]
            operation = operation_list[_i]

            _temp_data = self.data_frame[[ticker, relative] if relative != "1" else [ticker]].copy()

            if relative == "1":
                _temp_data = _temp_data.rename(columns={ticker: ticker_list[_i]})
                if _i == 0:
                    final = _temp_data
                else:
                    final = final.join(_temp_data)
                continue

            if operation == "-":
                _temp_data["Output"] = _temp_data[ticker] - _temp_data[relative]
                _t_o_title = f"Spread {ticker_list[_i]} vs {relative_list[_i]}"
            elif operation == "/":
                _temp_data["Output"] = _temp_data[ticker] / _temp_data[relative]
                _t_o_title = f"Relativo {ticker_list[_i]} vs {relative_list[_i]}"
            elif operation == "*":
                _temp_data["Output"] = _temp_data[ticker] * _temp_data[relative]
                _t_o_title = f"Multiplicación {ticker_list[_i]} vs {relative_list[_i]}"
            elif operation == "+":
                _temp_data["Output"] = _temp_data[ticker] + _temp_data[relative]
                _t_o_title = f"Sum {ticker_list[_i]} vs {relative_list[_i]}"
            else:
                raise ValueError(f"Operación '{operation}' no soportada. Use '-', '/', '*', o '+'.")
            
            _temp_data = _temp_data[["Output"]].rename(columns={"Output": _t_o_title})

            if _i == 0:
                final = _temp_data
            else:
                final = final.join(_temp_data)


        if names:
            final = self.assign_names(final)
            final = self.assign_names(final)
        return final
    
    def momentum (self, windows: list[int] = [15, 30], prefix: str = "MomentumSimple{w}_", names: bool = False) -> pd.DataFrame:
        _data = self.data_frame.sort_index()

        frames = []
        for w in windows:
            _data_temp = _data.pct_change(periods=w)
            mean = _data_temp.rolling(window=w).mean()
            std = _data_temp.rolling(window=w).std()
            momentum = (_data_temp - mean) / std.where(std != 0, 1)
            momentum.columns = [f"{prefix.format(w=w)}{c}" for c in _data_temp.columns]
            frames.append(momentum)

        final = pd.concat(frames, axis=1)
        if names:
            final = self.assign_names(final)

        return final

    def momentum_sma (self, prefix: str = "MomentumSMA_", names: bool = False) -> pd.DataFrame:

        _data_price = self.data_frame
        _data_price = _data_price.resample("W").last()

        scores = []
        for ticker in _data_price.columns:
            temp =_data_price[[ticker]].copy()
            temp["MA(5)"] = temp[ticker].rolling(window=5).mean()
            temp["MA(15)"] = temp[ticker].rolling(window=15).mean()
            temp["dMA(15)"] = temp["MA(15)"].pct_change(periods=1)
            temp["spreadW"] = temp["MA(5)"] - temp["MA(15)"]
            temp["Score"] = np.nan
            temp.loc[(temp[ticker] < temp["MA(15)"]) & (temp["dMA(15)"] < 0) & (temp["spreadW"] < 0), "Score"] = 1
            temp.loc[(temp[ticker] < temp["MA(15)"]) & (temp["dMA(15)"] > 0) & (temp["spreadW"] < 0), "Score"] = 2
            temp.loc[(temp[ticker] > temp["MA(15)"]) & (temp["dMA(15)"] < 0) & (temp["spreadW"] > 0), "Score"] = 4
            temp.loc[(temp[ticker] > temp["MA(15)"]) & (temp["dMA(15)"] > 0.0001) & (temp["spreadW"] > 0.0001), "Score"] = 5
            temp.loc[temp["Score"].isna(), "Score"] = 3
            temp = temp[["Score"]].rename(columns={"Score": f"{prefix}{ticker}"})
            scores.append(temp)
        
        final = pd.concat(scores, axis=1)
        if names:
            final = self.assign_names(final)

        return final

        #for col in _data_price.columns:

    def rank_percentile(self):
        percentile_last = (
            self.data_frame
            .rank(pct=True)
            .iloc[-1]
        )

        return percentile_last


# =============================================================================
# Type aliases
# =============================================================================

ReturnMethod = Literal["simple", "log"]
CompoundMethod = Literal["none", "cumulative", "rolling"]
PeriodToDate = Literal["wtd", "mtd", "qtd", "ytd"]
VaRMethod = Literal["historical", "gaussian", "cornish_fisher"]
DrawdownMethod = Literal["simple", "log"]
RelativeOperation = Literal["-", "/", "*", "+"]


# =============================================================================
# Validation helpers
# =============================================================================

def _dfvalidate(func: Callable) -> Callable:
    """
    Validate that the decorated function receives a valid pandas DataFrame.

    Description
    -----------
    This decorator searches for the first pandas DataFrame passed either as a
    positional argument or as a keyword argument. It validates that the DataFrame
    is not empty, that its index is datetime-like, that the index does not have
    duplicated values, and that all columns are numeric before executing the
    decorated function.

    Parameters
    ----------
    func : callable
        Function to be decorated.

    Returns
    -------
    callable
        Wrapped function that validates the input DataFrame before execution.

    Raises
    ------
    TypeError
        If no pandas DataFrame is found, if the DataFrame index is not
        datetime-like, or if the DataFrame contains non-numeric columns.

    ValueError
        If the DataFrame is empty or if the index contains duplicated values.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        df = None

        for arg in args:
            if isinstance(arg, pd.DataFrame):
                df = arg
                break

        if df is None:
            for value in kwargs.values():
                if isinstance(value, pd.DataFrame):
                    df = value
                    break

        if df is None:
            raise TypeError(
                f"No pandas DataFrame was found in function '{func.__name__}'."
            )

        if df.empty:
            raise ValueError("The DataFrame cannot be empty.")

        if not isinstance(df.index, pd.DatetimeIndex):
            raise TypeError("The DataFrame index must be a pandas DatetimeIndex.")

        if df.index.has_duplicates:
            raise ValueError("The DataFrame index contains duplicated values.")

        non_numeric_cols = df.select_dtypes(exclude="number").columns.tolist()
        if non_numeric_cols:
            raise TypeError(
                f"The DataFrame contains non-numeric columns: {non_numeric_cols}."
            )

        return func(*args, **kwargs)

    return wrapper


def _validate_benchmark(
    df: pd.DataFrame,
    benchmark: str,
) -> None:
    """
    Validate that the benchmark column exists in the DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.

    benchmark : str
        Benchmark column name.

    Raises
    ------
    ValueError
        If the benchmark column is not present in the DataFrame.
    """
    if benchmark not in df.columns:
        raise ValueError(f"Benchmark '{benchmark}' was not found in the DataFrame.")


def _validate_window(
    window: int,
    name: str = "window",
) -> None:
    """
    Validate that a rolling window is a positive integer.

    Parameters
    ----------
    window : int
        Rolling window value.

    name : str, default "window"
        Name used in the error message.

    Raises
    ------
    TypeError
        If the window is not an integer.

    ValueError
        If the window is less than or equal to zero.
    """
    if not isinstance(window, int):
        raise TypeError(f"{name} must be an integer.")

    if window <= 0:
        raise ValueError(f"{name} must be greater than zero.")


def _validate_confidence(
    confidence: float,
) -> None:
    """
    Validate that a confidence level is between zero and one.

    Parameters
    ----------
    confidence : float
        Confidence level.

    Raises
    ------
    ValueError
        If confidence is not between zero and one.
    """
    if not 0 < confidence < 1:
        raise ValueError("confidence must be greater than 0 and less than 1.")


# =============================================================================
# Return helpers
# =============================================================================

def _compound_returns(
    returns: pd.DataFrame | pd.Series,
    method: ReturnMethod = "simple",
) -> pd.Series | float:
    """
    Compound simple or log returns into a total return.

    Parameters
    ----------
    returns : pd.DataFrame or pd.Series
        Return data.

    method : {"simple", "log"}, default "simple"
        Return calculation method.
        - "simple": compounds using product of one plus returns.
        - "log": compounds using exponential of summed log returns.

    Returns
    -------
    pd.Series or float
        Compounded return.
    """
    if method == "simple":
        return (1.0 + returns).prod() - 1.0

    if method == "log":
        return np.exp(returns.sum()) - 1.0

    raise ValueError("method must be 'simple' or 'log'.")


def _to_returns(
    df: pd.DataFrame,
    method: ReturnMethod = "simple",
    dropna: bool = False,
    compound: CompoundMethod = "none",
    window: int | None = None,
    min_periods: int | None = None,
) -> pd.DataFrame:
    """
    Convert price data into returns.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame with a datetime index and one or more asset price
        columns.

    method : {"simple", "log"}, default "simple"
        Return calculation method.
        - "simple": calculates percentage returns.
        - "log": calculates logarithmic returns.

    dropna : bool, default False
        Whether to drop rows where all values are missing.

    compound : {"none", "cumulative", "rolling"}, default "none"
        Compounding method.
        - "none": returns one-period returns.
        - "cumulative": returns compounded returns from the first valid
          observation.
        - "rolling": returns compounded returns over a rolling window.

    window : int or None, default None
        Rolling window used when compound is "rolling".

    min_periods : int or None, default None
        Minimum number of observations required for rolling compounded returns.
        If None, the rolling window value is used.

    Returns
    -------
    pd.DataFrame
        Return DataFrame.

    Raises
    ------
    ValueError
        If method or compound is invalid, or if window is missing when
        compound is "rolling".
    """
    px = df.sort_index()

    if method == "simple":
        rets = px.pct_change()
    elif method == "log":
        rets = np.log(px / px.shift(1))
    else:
        raise ValueError("method must be 'simple' or 'log'.")

    if compound == "none":
        output = rets

    elif compound == "cumulative":
        if method == "simple":
            output = (1.0 + rets).cumprod() - 1.0
        else:
            output = np.exp(rets.cumsum()) - 1.0

    elif compound == "rolling":
        if window is None:
            raise ValueError("window must be provided when compound='rolling'.")

        _validate_window(window)

        mp = window if min_periods is None else min_periods

        if method == "simple":
            output = (
                (1.0 + rets)
                .rolling(window=window, min_periods=mp)
                .apply(np.prod, raw=True)
                - 1.0
            )
        else:
            output = (
                np.exp(
                    rets.rolling(window=window, min_periods=mp).sum()
                )
                - 1.0
            )

    else:
        raise ValueError("compound must be 'none', 'cumulative', or 'rolling'.")

    if dropna:
        output = output.dropna(how="all")

    return output


def _period_to_date(
    df: pd.DataFrame,
    period: PeriodToDate = "ytd",
    fallback: bool = True,
    week_freq: str = "W-FRI",
) -> pd.DataFrame:
    """
    Calculate period-to-date returns for price series.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame with a datetime index and one or more asset price
        columns.

    period : {"wtd", "mtd", "qtd", "ytd"}, default "ytd"
        Period-to-date frequency.
        - "wtd": Week-to-date.
        - "mtd": Month-to-date.
        - "qtd": Quarter-to-date.
        - "ytd": Year-to-date.

    fallback : bool, default True
        If True, uses the first valid price of the current period when the
        previous period-end price is not available.

    week_freq : str, default "W-FRI"
        Weekly frequency used when period is "wtd". The default assumes a
        market week ending on Friday.

    Returns
    -------
    pd.DataFrame
        DataFrame with period-to-date returns for each price series.
    
    Notes
    -----
    The function assumes prices may be stored on a calendar-day basis
    with non-trading days forward-filled (e.g. Bloomberg PX_LAST).
    Period-to-date calculations are therefore performed on the calendar
    index rather than a trading-day calendar.
    
    """
    px = df.sort_index()

    period_map = {
        "wtd": week_freq,
        "mtd": "M",
        "qtd": "Q",
        "ytd": "Y",
    }

    if period not in period_map:
        raise ValueError("period must be 'wtd', 'mtd', 'qtd', or 'ytd'.")

    freq = period_map[period]

    current_period = px.index.to_period(freq)
    previous_period = current_period - 1

    period_end_prices = (
        px.groupby(current_period)
        .apply(lambda g: g.ffill().iloc[-1])
    )

    bases = period_end_prices.reindex(previous_period)
    bases.index = px.index
    bases = bases.reindex(columns=px.columns)

    if fallback:
        first_in_period = (
            px.groupby(current_period)
            .apply(lambda g: g.bfill().iloc[0])
        )

        first_in_period = first_in_period.reindex(current_period)
        first_in_period.index = px.index
        first_in_period = first_in_period.reindex(columns=px.columns)

        bases = bases.combine_first(first_in_period)

    if not bases.index.equals(px.index):
        raise RuntimeError("Index mismatch after alignment.")

    if list(bases.columns) != list(px.columns):
        raise RuntimeError("Columns mismatch after alignment.")

    if bases.shape != px.shape:
        raise RuntimeError(
            f"Shape mismatch: df {px.shape} vs bases {bases.shape}."
        )

    return px.div(bases) - 1.0


# =============================================================================
# Period-to-date returns
# =============================================================================

@_dfvalidate
def wtd(
    df: pd.DataFrame,
    fallback: bool = True,
    week_freq: str = "W-FRI",
) -> pd.DataFrame:
    """
    Calculate Week-To-Date returns for price series.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame with a datetime index and one or more asset price
        columns.

    fallback : bool, default True
        If True, uses the first valid price of the current week when the
        previous week-end price is not available.

    week_freq : str, default "W-FRI"
        Weekly frequency used for week grouping.

    Returns
    -------
    pd.DataFrame
        DataFrame with Week-To-Date returns for each price series.
    """
    return _period_to_date(
        df=df,
        period="wtd",
        fallback=fallback,
        week_freq=week_freq,
    )


@_dfvalidate
def mtd(
    df: pd.DataFrame,
    fallback: bool = True,
) -> pd.DataFrame:
    """
    Calculate Month-To-Date returns for price series.
    """
    return _period_to_date(
        df=df,
        period="mtd",
        fallback=fallback,
    )


@_dfvalidate
def qtd(
    df: pd.DataFrame,
    fallback: bool = True,
) -> pd.DataFrame:
    """
    Calculate Quarter-To-Date returns for price series.
    """
    return _period_to_date(
        df=df,
        period="qtd",
        fallback=fallback,
    )


@_dfvalidate
def ytd(
    df: pd.DataFrame,
    fallback: bool = True,
) -> pd.DataFrame:
    """
    Calculate Year-To-Date returns for price series.
    """
    return _period_to_date(
        df=df,
        period="ytd",
        fallback=fallback,
    )


# =============================================================================
# Performance metrics
# =============================================================================

@_dfvalidate
def total_return(
    df: pd.DataFrame,
    method: ReturnMethod = "simple",
) -> pd.Series:
    """
    Calculate total return for each price series.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame.

    method : {"simple", "log"}, default "simple"
        Return calculation method.

    Returns
    -------
    pd.Series
        Total return by asset.
    """
    rets = _to_returns(df, method=method, dropna=False)

    output = _compound_returns(
        returns=rets,
        method=method,
    )

    return output.rename("Total Return")


@_dfvalidate
def annualized_return(
    df: pd.DataFrame,
    periods_per_year: int = 252,
    method: ReturnMethod = "simple",
) -> pd.Series:
    """
    Calculate annualized return for each price series.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame.

    periods_per_year : int, default 252
        Number of periods per year.

    method : {"simple", "log"}, default "simple"
        Return calculation method.

    Returns
    -------
    pd.Series
        Annualized return by asset.
    """
    rets = _to_returns(df, method=method, dropna=False)

    n_periods = rets.notna().sum()

    total = _compound_returns(
        returns=rets,
        method=method,
    )

    output = (1.0 + total) ** (periods_per_year / n_periods) - 1.0

    return output.rename("Annualized Return")


@_dfvalidate
def volatility(
    df: pd.DataFrame,
    method: ReturnMethod = "simple",
    annualize: bool = True,
    periods_per_year: int = 252,
    ddof: int = 1,
) -> pd.Series:
    """
    Calculate return volatility for each asset.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame.

    method : {"simple", "log"}, default "simple"
        Return calculation method.

    annualize : bool, default True
        If True, annualizes volatility.

    periods_per_year : int, default 252
        Number of periods per year.

    ddof : int, default 1
        Delta degrees of freedom.

    Returns
    -------
    pd.Series
        Volatility by asset.
    """
    rets = _to_returns(df, method=method)

    output = rets.std(ddof=ddof)

    if annualize:
        output *= np.sqrt(periods_per_year)

    return output.rename("Volatility")


@_dfvalidate
def sharpe_ratio(
    df: pd.DataFrame,
    risk_free_rate: float = 0.0,
    method: ReturnMethod = "simple",
    annualize: bool = True,
    periods_per_year: int = 252,
    ddof: int = 1,
) -> pd.Series:
    """
    Calculate Sharpe ratio for each asset.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame.

    risk_free_rate : float, default 0.0
        Annualized risk-free rate.

    method : {"simple", "log"}, default "simple"
        Return calculation method.

    annualize : bool, default True
        If True, annualizes the Sharpe ratio.

    periods_per_year : int, default 252
        Number of periods per year.

    ddof : int, default 1
        Delta degrees of freedom.

    Returns
    -------
    pd.Series
        Sharpe ratio by asset.
    """
    rets = _to_returns(df, method=method)

    period_rf = risk_free_rate / periods_per_year
    excess = rets - period_rf

    output = excess.mean() / excess.std(ddof=ddof)

    if annualize:
        output *= np.sqrt(periods_per_year)

    return output.rename("Sharpe Ratio")


@_dfvalidate
def downside_std(
    df: pd.DataFrame,
    method: ReturnMethod = "simple",
    target_return: float = 0.0,
    annualize: bool = False,
    periods_per_year: int = 252,
) -> pd.DataFrame:
    """
    Calculate downside standard deviation for each asset.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame.

    method : {"simple", "log"}, default "simple"
        Return calculation method.

    target_return : float, default 0.0
        Minimum acceptable return per period.

    annualize : bool, default False
        If True, annualizes downside standard deviation.

    periods_per_year : int, default 252
        Number of periods per year.

    Returns
    -------
    pd.DataFrame
        DataFrame with one column named "std_downside".
    """
    rets = _to_returns(df, method=method)

    downside = (rets - target_return).where(rets < target_return, 0.0)

    output = np.sqrt((downside ** 2).mean())

    if annualize:
        output *= np.sqrt(periods_per_year)

    return output.to_frame(name="std_downside")


@_dfvalidate
def sortino_ratio(
    df: pd.DataFrame,
    target_return: float = 0.0,
    method: ReturnMethod = "simple",
    annualize: bool = True,
    periods_per_year: int = 252,
) -> pd.Series:
    """
    Calculate Sortino ratio for each asset.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame.

    target_return : float, default 0.0
        Annualized minimum acceptable return.

    method : {"simple", "log"}, default "simple"
        Return calculation method.

    annualize : bool, default True
        If True, annualizes the ratio.

    periods_per_year : int, default 252
        Number of periods per year.

    Returns
    -------
    pd.Series
        Sortino ratio by asset.
    """
    rets = _to_returns(df, method=method)

    period_target = target_return / periods_per_year

    downside = (rets - period_target).where(rets < period_target, 0.0)
    downside_dev = np.sqrt((downside ** 2).mean())

    excess_return = rets.mean() - period_target

    output = excess_return / downside_dev

    if annualize:
        output *= np.sqrt(periods_per_year)

    return output.rename("Sortino Ratio")


# =============================================================================
# Drawdown metrics
# =============================================================================

@_dfvalidate
def drawdown(
    df: pd.DataFrame,
    method: DrawdownMethod = "simple",
    min_price: float = 1e-6,
) -> pd.DataFrame:
    """
    Calculate drawdown for price series.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame.

    method : {"simple", "log"}, default "simple"
        Drawdown calculation method.

    min_price : float, default 1e-6
        Minimum valid price threshold.

    Returns
    -------
    pd.DataFrame
        Drawdown time series by asset.
    """
    px = df.sort_index()
    px = px.where(px > min_price)

    if method == "simple":
        px_ff = px.ffill()
        roll_max = px_ff.cummax()
        output = px.divide(roll_max) - 1.0

    elif method == "log":
        logp = np.log(px)
        logp_ff = logp.ffill()
        roll_max_log = logp_ff.cummax()
        output = np.exp(logp - roll_max_log) - 1.0

    else:
        raise ValueError("method must be 'simple' or 'log'.")

    return output


@_dfvalidate
def max_drawdown(
    df: pd.DataFrame,
    method: DrawdownMethod = "simple",
    min_price: float = 1e-6,
) -> pd.Series:
    """
    Calculate maximum drawdown for each asset.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame.

    method : {"simple", "log"}, default "simple"
        Drawdown calculation method.

    min_price : float, default 1e-6
        Minimum valid price threshold.

    Returns
    -------
    pd.Series
        Maximum drawdown by asset.
    """
    output = drawdown(
        df=df,
        method=method,
        min_price=min_price,
    ).min()

    return output.rename("Max Drawdown")


@_dfvalidate
def calmar_ratio(
    df: pd.DataFrame,
    periods_per_year: int = 252,
) -> pd.Series:
    """
    Calculate Calmar ratio for each asset.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame.

    periods_per_year : int, default 252
        Number of periods per year.

    Returns
    -------
    pd.Series
        Calmar ratio by asset.
    """
    ann_ret = annualized_return(
        df=df,
        periods_per_year=periods_per_year,
    )

    mdd = max_drawdown(df=df).abs()

    output = ann_ret / mdd

    return output.rename("Calmar Ratio")


# =============================================================================
# Benchmark-relative metrics
# =============================================================================

@_dfvalidate
def active_return(
    df: pd.DataFrame,
    benchmark: str,
    method: ReturnMethod = "simple",
) -> pd.DataFrame:
    """
    Calculate active returns relative to a benchmark.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame including the benchmark column.

    benchmark : str
        Benchmark column name.

    method : {"simple", "log"}, default "simple"
        Return calculation method.

    Returns
    -------
    pd.DataFrame
        Active returns by asset.
    """
    _validate_benchmark(df, benchmark)

    rets = _to_returns(df, method=method)

    output = rets.sub(rets[benchmark], axis=0)

    return output


@_dfvalidate
def beta(
    df: pd.DataFrame,
    benchmark: str,
    window: int | None = None,
    method: ReturnMethod = "simple",
    min_periods: int | None = None,
    ddof: int = 1,
) -> pd.Series | pd.DataFrame:
    """
    Calculate beta relative to a benchmark.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame including the benchmark column.

    benchmark : str
        Benchmark column name.

    window : int or None, default None
        Rolling window size. If None, historical beta is calculated.

    method : {"simple", "log"}, default "simple"
        Return calculation method.

    min_periods : int or None, default None
        Minimum observations required for rolling calculations.

    ddof : int, default 1
        Delta degrees of freedom.

    Returns
    -------
    pd.Series or pd.DataFrame
        Historical beta by asset or rolling beta time series.
    """
    _validate_benchmark(df, benchmark)

    rets = _to_returns(df, method=method)
    benchmark_returns = rets[benchmark]

    if window is None:
        bench_var = benchmark_returns.var(ddof=ddof)

        output = rets.apply(
            lambda col: col.cov(benchmark_returns) / bench_var
        )

        return output.rename("Beta")

    _validate_window(window)

    mp = window if min_periods is None else min_periods

    bench_var = benchmark_returns.rolling(
        window=window,
        min_periods=mp,
    ).var(ddof=ddof)

    output = (
        rets.rolling(window=window, min_periods=mp)
        .cov(benchmark_returns)
        .divide(bench_var, axis=0)
    )

    return output


@_dfvalidate
def tracking_error(
    df: pd.DataFrame,
    benchmark: str,
    method: ReturnMethod = "simple",
    annualize: bool = True,
    periods_per_year: int = 252,
    ddof: int = 1,
) -> pd.Series:
    """
    Calculate tracking error relative to a benchmark.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame including the benchmark column.

    benchmark : str
        Benchmark column name.

    method : {"simple", "log"}, default "simple"
        Return calculation method.

    annualize : bool, default True
        If True, annualizes tracking error.

    periods_per_year : int, default 252
        Number of periods per year.

    ddof : int, default 1
        Delta degrees of freedom.

    Returns
    -------
    pd.Series
        Tracking error by asset.
    """
    active = active_return(
        df=df,
        benchmark=benchmark,
        method=method,
    )

    output = active.std(ddof=ddof)

    if annualize:
        output *= np.sqrt(periods_per_year)

    return output.rename("Tracking Error")


@_dfvalidate
def rolling_tracking_error(
    df: pd.DataFrame,
    benchmark: str,
    window: int = 252,
    method: ReturnMethod = "simple",
    annualize: bool = True,
    periods_per_year: int = 252,
    min_periods: int | None = None,
    ddof: int = 1,
) -> pd.DataFrame:
    """
    Calculate rolling tracking error relative to a benchmark.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame including the benchmark column.

    benchmark : str
        Benchmark column name.

    window : int, default 252
        Rolling window size.

    method : {"simple", "log"}, default "simple"
        Return calculation method.

    annualize : bool, default True
        If True, annualizes tracking error.

    periods_per_year : int, default 252
        Number of periods per year.

    min_periods : int or None, default None
        Minimum observations required.

    ddof : int, default 1
        Delta degrees of freedom.

    Returns
    -------
    pd.DataFrame
        Rolling tracking error by asset.
    """
    _validate_window(window)

    active = active_return(
        df=df,
        benchmark=benchmark,
        method=method,
    )

    mp = window if min_periods is None else min_periods

    output = active.rolling(
        window=window,
        min_periods=mp,
    ).std(ddof=ddof)

    if annualize:
        output *= np.sqrt(periods_per_year)

    return output


@_dfvalidate
def information_ratio(
    df: pd.DataFrame,
    benchmark: str,
    method: ReturnMethod = "simple",
    annualize: bool = True,
    periods_per_year: int = 252,
    ddof: int = 1,
) -> pd.Series:
    """
    Calculate information ratio relative to a benchmark.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame including the benchmark column.

    benchmark : str
        Benchmark column name.

    method : {"simple", "log"}, default "simple"
        Return calculation method.

    annualize : bool, default True
        If True, annualizes the information ratio.

    periods_per_year : int, default 252
        Number of periods per year.

    ddof : int, default 1
        Delta degrees of freedom.

    Returns
    -------
    pd.Series
        Information ratio by asset.
    """
    active = active_return(
        df=df,
        benchmark=benchmark,
        method=method,
    )

    mean_active = active.mean()
    te = active.std(ddof=ddof)

    output = mean_active / te

    if annualize:
        output *= np.sqrt(periods_per_year)

    return output.rename("Information Ratio")


@_dfvalidate
def rolling_information_ratio(
    df: pd.DataFrame,
    benchmark: str,
    window: int = 252,
    method: ReturnMethod = "simple",
    annualize: bool = True,
    periods_per_year: int = 252,
    min_periods: int | None = None,
    ddof: int = 1,
) -> pd.DataFrame:
    """
    Calculate rolling information ratio relative to a benchmark.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame including the benchmark column.

    benchmark : str
        Benchmark column name.

    window : int, default 252
        Rolling window size.

    method : {"simple", "log"}, default "simple"
        Return calculation method.

    annualize : bool, default True
        If True, annualizes the information ratio.

    periods_per_year : int, default 252
        Number of periods per year.

    min_periods : int or None, default None
        Minimum observations required.

    ddof : int, default 1
        Delta degrees of freedom.

    Returns
    -------
    pd.DataFrame
        Rolling information ratio by asset.
    """
    _validate_window(window)

    active = active_return(
        df=df,
        benchmark=benchmark,
        method=method,
    )

    mp = window if min_periods is None else min_periods

    mean_active = active.rolling(
        window=window,
        min_periods=mp,
    ).mean()

    te = active.rolling(
        window=window,
        min_periods=mp,
    ).std(ddof=ddof)

    output = mean_active / te

    if annualize:
        output *= np.sqrt(periods_per_year)

    return output


@_dfvalidate
def upside_capture(
    df: pd.DataFrame,
    benchmark: str,
    method: ReturnMethod = "simple",
) -> pd.Series:
    """
    Calculate upside capture ratio relative to a benchmark.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame including the benchmark column.

    benchmark : str
        Benchmark column name.

    method : {"simple", "log"}, default "simple"
        Return calculation method.

    Returns
    -------
    pd.Series
        Upside capture ratio by asset.
    """
    _validate_benchmark(df, benchmark)

    rets = _to_returns(df, method=method)
    bench = rets[benchmark]

    mask = bench > 0

    asset_up = _compound_returns(
        returns=rets.loc[mask],
        method=method,
    )

    bench_up = _compound_returns(
        returns=bench.loc[mask],
        method=method,
    )

    output = asset_up / bench_up

    return output.rename("Upside Capture")


@_dfvalidate
def downside_capture(
    df: pd.DataFrame,
    benchmark: str,
    method: ReturnMethod = "simple",
) -> pd.Series:
    """
    Calculate downside capture ratio relative to a benchmark.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame including the benchmark column.

    benchmark : str
        Benchmark column name.

    method : {"simple", "log"}, default "simple"
        Return calculation method.

    Returns
    -------
    pd.Series
        Downside capture ratio by asset.
    """
    _validate_benchmark(df, benchmark)

    rets = _to_returns(df, method=method)
    bench = rets[benchmark]

    mask = bench < 0

    asset_down = _compound_returns(
        returns=rets.loc[mask],
        method=method,
    )

    bench_down = _compound_returns(
        returns=bench.loc[mask],
        method=method,
    )

    output = asset_down / bench_down

    return output.rename("Downside Capture")


@_dfvalidate
def capture_ratio(
    df: pd.DataFrame,
    benchmark: str,
    method: ReturnMethod = "simple",
) -> pd.Series:
    """
    Calculate upside-to-downside capture ratio.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame including the benchmark column.

    benchmark : str
        Benchmark column name.

    method : {"simple", "log"}, default "simple"
        Return calculation method.

    Returns
    -------
    pd.Series
        Upside capture divided by downside capture.
    """
    uc = upside_capture(
        df=df,
        benchmark=benchmark,
        method=method,
    )

    dc = downside_capture(
        df=df,
        benchmark=benchmark,
        method=method,
    )

    output = uc / dc

    return output.rename("Capture Ratio")


@_dfvalidate
def hit_ratio(
    df: pd.DataFrame,
    benchmark: str,
    method: ReturnMethod = "simple",
) -> pd.Series:
    """
    Calculate the percentage of periods with positive active return.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame including the benchmark column.

    benchmark : str
        Benchmark column name.

    method : {"simple", "log"}, default "simple"
        Return calculation method.

    Returns
    -------
    pd.Series
        Hit ratio by asset.
    """
    active = active_return(
        df=df,
        benchmark=benchmark,
        method=method,
    )

    output = active.gt(0).sum() / active.notna().sum()

    return output.rename("Hit Ratio")


@_dfvalidate
def excess_return(
    df: pd.DataFrame,
    benchmark: str,
    period: PeriodToDate = "qtd",
    fallback: bool = True,
    week_freq: str = "W-FRI",
) -> pd.DataFrame:
    """
    Calculate excess return relative to a benchmark.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame including the benchmark column.

    benchmark : str
        Benchmark column name.

    period : {"wtd", "mtd", "qtd", "ytd"}, default "qtd"
        Period used to calculate returns before computing excess return.

    fallback : bool, default True
        If True, uses the first valid price of the current period when the
        previous period-end price is not available.

    week_freq : str, default "W-FRI"
        Weekly frequency used when period is "wtd".

    Returns
    -------
    pd.DataFrame
        Excess return by asset through time.
    """
    _validate_benchmark(df, benchmark)

    data = _period_to_date(
        df=df,
        period=period,
        fallback=fallback,
        week_freq=week_freq,
    )

    output = data.sub(data[benchmark], axis=0)

    return output


@_dfvalidate
def consistency(
    df: pd.DataFrame,
    benchmark: str,
    period: PeriodToDate = "qtd",
    fallback: bool = True,
    week_freq: str = "W-FRI",
) -> pd.Series:
    """
    Calculate outperformance consistency relative to a benchmark.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame including the benchmark column.

    benchmark : str
        Benchmark column name.

    period : {"wtd", "mtd", "qtd", "ytd"}, default "qtd"
        Period used to calculate returns before computing excess return.

    fallback : bool, default True
        If True, uses the first valid price of the current period when the
        previous period-end price is not available.

    week_freq : str, default "W-FRI"
        Weekly frequency used when period is "wtd".

    Returns
    -------
    pd.Series
        Percentage of observations where each asset had positive excess return.
    """
    exre = excess_return(
        df=df,
        benchmark=benchmark,
        period=period,
        fallback=fallback,
        week_freq=week_freq,
    )

    output = exre.gt(0).sum() / exre.notna().sum()

    return output.rename("Consistency")


# =============================================================================
# Risk metrics
# =============================================================================

@_dfvalidate
def value_at_risk(
    df: pd.DataFrame,
    confidence: float = 0.95,
    method: VaRMethod = "historical",
    returns_method: ReturnMethod = "simple",
    horizon: int = 1,
) -> pd.Series:
    """
    Calculate Value at Risk for each asset.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame.

    confidence : float, default 0.95
        Confidence level used to calculate VaR.

    method : {"historical", "gaussian", "cornish_fisher"}, default "historical"
        VaR calculation methodology.

    returns_method : {"simple", "log"}, default "simple"
        Return calculation method.

    horizon : int, default 1
        Holding period expressed in return periods.

    Returns
    -------
    pd.Series
        Value at Risk by asset, expressed as a positive loss.
    """
    _validate_confidence(confidence)
    _validate_window(horizon, name="horizon")

    alpha = 1.0 - confidence

    rets = _to_returns(
        df=df,
        method=returns_method,
        dropna=True,
    )

    if method == "historical":
        if horizon == 1:
            horizon_rets = rets
        else:
            horizon_rets = _to_returns(
                df=df,
                method=returns_method,
                dropna=True,
                compound="rolling",
                window=horizon,
                min_periods=horizon,
            )

        output = -horizon_rets.quantile(alpha)

    elif method == "gaussian":
        z = norm.ppf(alpha)

        output = -(
            rets.mean() * horizon
            + z * rets.std() * np.sqrt(horizon)
        )

    elif method == "cornish_fisher":
        z = norm.ppf(alpha)

        skewness = rets.skew()
        kurtosis = rets.kurtosis()

        z_cf = (
            z
            + ((z ** 2 - 1.0) * skewness / 6.0)
            + ((z ** 3 - 3.0 * z) * kurtosis / 24.0)
            - ((2.0 * z ** 3 - 5.0 * z) * skewness ** 2 / 36.0)
        )

        output = -(
            rets.mean() * horizon
            + z_cf * rets.std() * np.sqrt(horizon)
        )

    else:
        raise ValueError(
            "method must be 'historical', 'gaussian', or 'cornish_fisher'."
        )

    return output.rename(f"VaR_{method}_{int(confidence * 100)}")


@_dfvalidate
def expected_shortfall(
    df: pd.DataFrame,
    confidence: float = 0.95,
    returns_method: ReturnMethod = "simple",
    horizon: int = 1,
) -> pd.Series:
    """
    Calculate Expected Shortfall, also known as Conditional VaR.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame.

    confidence : float, default 0.95
        Confidence level.

    returns_method : {"simple", "log"}, default "simple"
        Return calculation method.

    horizon : int, default 1
        Holding period expressed in return periods.

    Returns
    -------
    pd.Series
        Expected Shortfall by asset, expressed as a positive loss.
    """
    _validate_confidence(confidence)
    _validate_window(horizon, name="horizon")

    alpha = 1.0 - confidence

    if horizon == 1:
        horizon_rets = _to_returns(
            df=df,
            method=returns_method,
            dropna=True,
        )
    else:
        horizon_rets = _to_returns(
            df=df,
            method=returns_method,
            dropna=True,
            compound="rolling",
            window=horizon,
            min_periods=horizon,
        )

    threshold = horizon_rets.quantile(alpha)

    output = horizon_rets.where(
        horizon_rets.le(threshold),
    ).mean()

    output = -output

    return output.rename(f"Expected Shortfall_{int(confidence * 100)}")


# =============================================================================
# Technical indicators
# =============================================================================

@_dfvalidate
def rsi(
    df: pd.DataFrame,
    window: int = 14,
    prefix: str = "RSI{w}_",
) -> pd.DataFrame:
    """
    Calculate Relative Strength Index for price series.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame.

    window : int, default 14
        Number of periods used to calculate average gains and losses.

    prefix : str, default "RSI{w}_"
        Prefix used to rename output columns.

    Returns
    -------
    pd.DataFrame
        RSI values for each price series.
    """
    _validate_window(window)

    px = df.sort_index()

    delta = px.diff()

    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=window, min_periods=window).mean()
    avg_loss = loss.rolling(window=window, min_periods=window).mean()

    rs = avg_gain / avg_loss
    output = 100.0 - (100.0 / (1.0 + rs))

    output.columns = [f"{prefix.format(w=window)}{col}" for col in px.columns]

    return output


@_dfvalidate
def sma(
    df: pd.DataFrame,
    windows: list[int] | None = None,
    min_periods: int | None = None,
    prefix: str = "SMA{w}_",
) -> pd.DataFrame:
    """
    Calculate Simple Moving Averages for price series.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame.

    windows : list[int] or None, default None
        Rolling windows. If None, defaults to [50].

    min_periods : int or None, default None
        Minimum observations required.

    prefix : str, default "SMA{w}_"
        Prefix used to rename output columns.

    Returns
    -------
    pd.DataFrame
        SMA values for each price series and window.
    """
    if windows is None:
        windows = [50]

    px = df.sort_index()
    frames = []

    for window in windows:
        _validate_window(window)

        mp = window if min_periods is None else min_periods

        output = px.rolling(
            window=window,
            min_periods=mp,
        ).mean()

        output.columns = [f"{prefix.format(w=window)}{col}" for col in px.columns]
        frames.append(output)

    return pd.concat(frames, axis=1)


@_dfvalidate
def ema(
    df: pd.DataFrame,
    windows: list[int] | None = None,
    min_periods: int | None = None,
    prefix: str = "EMA{w}_",
) -> pd.DataFrame:
    """
    Calculate Exponential Moving Averages for price series.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame.

    windows : list[int] or None, default None
        EMA spans. If None, defaults to [27].

    min_periods : int or None, default None
        Minimum observations required.

    prefix : str, default "EMA{w}_"
        Prefix used to rename output columns.

    Returns
    -------
    pd.DataFrame
        EMA values for each price series and window.
    """
    if windows is None:
        windows = [27]

    px = df.sort_index()
    frames = []

    for window in windows:
        _validate_window(window)

        mp = window if min_periods is None else min_periods

        output = px.ewm(
            span=window,
            min_periods=mp,
        ).mean()

        output.columns = [f"{prefix.format(w=window)}{col}" for col in px.columns]
        frames.append(output)

    return pd.concat(frames, axis=1)


@_dfvalidate
def zscore(
    df: pd.DataFrame,
    window: int = 252,
    min_periods: int | None = None,
    prefix: str = "ZScore{w}_",
) -> pd.DataFrame:
    """
    Calculate rolling z-score for each price series.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame.

    window : int, default 252
        Rolling window size.

    min_periods : int or None, default None
        Minimum observations required.

    prefix : str, default "ZScore{w}_"
        Prefix used to rename output columns.

    Returns
    -------
    pd.DataFrame
        Rolling z-score values.
    """
    _validate_window(window)

    px = df.sort_index()

    mp = window if min_periods is None else min_periods

    mean = px.rolling(
        window=window,
        min_periods=mp,
    ).mean()

    std = px.rolling(
        window=window,
        min_periods=mp,
    ).std()

    output = (px - mean) / std

    output.columns = [f"{prefix.format(w=window)}{col}" for col in px.columns]

    return output


@_dfvalidate
def bollinger_bands(
    df: pd.DataFrame,
    window: int = 20,
    num_std: float = 2.0,
    min_periods: int | None = None,
) -> pd.DataFrame:
    """
    Calculate Bollinger Bands for each price series.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame.

    window : int, default 20
        Rolling window size.

    num_std : float, default 2.0
        Number of standard deviations used for upper and lower bands.

    min_periods : int or None, default None
        Minimum observations required.

    Returns
    -------
    pd.DataFrame
        Bollinger Band columns for each asset.
    """
    _validate_window(window)

    px = df.sort_index()

    mp = window if min_periods is None else min_periods

    middle = px.rolling(
        window=window,
        min_periods=mp,
    ).mean()

    std = px.rolling(
        window=window,
        min_periods=mp,
    ).std()

    upper = middle + num_std * std
    lower = middle - num_std * std

    frames = []

    for col in px.columns:
        temp = pd.DataFrame(
            {
                f"BB_Middle{window}_{col}": middle[col],
                f"BB_Upper{window}_{col}": upper[col],
                f"BB_Lower{window}_{col}": lower[col],
            },
            index=px.index,
        )

        frames.append(temp)

    return pd.concat(frames, axis=1)


@_dfvalidate
def macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """
    Calculate MACD indicator for each price series.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame.

    fast : int, default 12
        Fast EMA span.

    slow : int, default 26
        Slow EMA span.

    signal : int, default 9
        Signal line EMA span.

    Returns
    -------
    pd.DataFrame
        MACD, signal, and histogram columns.
    """
    _validate_window(fast, name="fast")
    _validate_window(slow, name="slow")
    _validate_window(signal, name="signal")

    if fast >= slow:
        raise ValueError("fast must be lower than slow.")

    px = df.sort_index()

    ema_fast = px.ewm(span=fast, min_periods=fast).mean()
    ema_slow = px.ewm(span=slow, min_periods=slow).mean()

    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, min_periods=signal).mean()
    histogram = macd_line - signal_line

    frames = []

    for col in px.columns:
        temp = pd.DataFrame(
            {
                f"MACD_{col}": macd_line[col],
                f"MACDSignal_{col}": signal_line[col],
                f"MACDHist_{col}": histogram[col],
            },
            index=px.index,
        )

        frames.append(temp)

    return pd.concat(frames, axis=1)


@_dfvalidate
def momentum(
    df: pd.DataFrame,
    windows: list[int] | None = None,
    prefix: str = "MomentumSimple{w}_",
) -> pd.DataFrame:
    """
    Calculate standardized momentum indicators.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame.

    windows : list[int] or None, default None
        Lookback windows. If None, defaults to [15, 30].

    prefix : str, default "MomentumSimple{w}_"
        Prefix used to rename output columns.

    Returns
    -------
    pd.DataFrame
        Standardized momentum values.
    """
    if windows is None:
        windows = [15, 30]

    px = df.sort_index()
    frames = []

    for window in windows:
        _validate_window(window)

        data_temp = _to_returns(
            df=px,
            method="simple",
            compound="rolling",
            window=window,
            min_periods=window,
        )

        mean = data_temp.rolling(
            window=window,
            min_periods=window,
        ).mean()

        std = data_temp.rolling(
            window=window,
            min_periods=window,
        ).std()

        output = (data_temp - mean) / std.replace(0.0, np.nan)
        output.columns = [f"{prefix.format(w=window)}{col}" for col in px.columns]

        frames.append(output)

    return pd.concat(frames, axis=1)


@_dfvalidate
def momentum_sma(
    df: pd.DataFrame,
    prefix: str = "MomentumSMA_",
) -> pd.DataFrame:
    """
    Calculate a moving-average-based momentum score.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame.

    prefix : str, default "MomentumSMA_"
        Prefix used to rename output columns.

    Returns
    -------
    pd.DataFrame
        Momentum scores for each asset.
    """
    data_price = df.sort_index().resample("W").last()

    scores = []

    for ticker in data_price.columns:
        temp = data_price[[ticker]].copy()

        temp["MA(5)"] = temp[ticker].rolling(window=5).mean()
        temp["MA(15)"] = temp[ticker].rolling(window=15).mean()
        temp["dMA(15)"] = temp["MA(15)"].pct_change(periods=1)
        temp["spreadW"] = temp["MA(5)"] - temp["MA(15)"]
        temp["Score"] = np.nan

        temp.loc[
            (temp[ticker] < temp["MA(15)"])
            & (temp["dMA(15)"] < 0)
            & (temp["spreadW"] < 0),
            "Score",
        ] = 1

        temp.loc[
            (temp[ticker] < temp["MA(15)"])
            & (temp["dMA(15)"] > 0)
            & (temp["spreadW"] < 0),
            "Score",
        ] = 2

        temp.loc[
            (temp[ticker] > temp["MA(15)"])
            & (temp["dMA(15)"] < 0)
            & (temp["spreadW"] > 0),
            "Score",
        ] = 4

        temp.loc[
            (temp[ticker] > temp["MA(15)"])
            & (temp["dMA(15)"] > 0.0001)
            & (temp["spreadW"] > 0.0001),
            "Score",
        ] = 5

        temp.loc[temp["Score"].isna(), "Score"] = 3

        temp = temp[["Score"]].rename(
            columns={"Score": f"{prefix}{ticker}"}
        )

        scores.append(temp)

    return pd.concat(scores, axis=1)


# =============================================================================
# Range and transformation helpers
# =============================================================================

@_dfvalidate
def mean_std_bands(
    df: pd.DataFrame,
    std_multipliers: list[int | float] | None = None,
    prefix: str = "Mean({w}std)_",
) -> pd.DataFrame:
    """
    Calculate static mean-based ranges using standard deviation offsets.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with numeric columns.

    std_multipliers : list[int or float] or None, default None
        Standard deviation multipliers. If None, defaults to [-1, 0, 1].

    prefix : str, default "Mean({w}std)_"
        Prefix used to rename output columns.

    Returns
    -------
    pd.DataFrame
        Mean plus or minus standard deviation reference levels.
    """
    if std_multipliers is None:
        std_multipliers = [-1, 0, 1]

    data = df.sort_index()

    mean = data.mean()
    std = data.std()

    frames = []

    for col in data.columns:
        for multiplier in std_multipliers:
            col_name = f"{prefix.format(w=multiplier)}{col}"

            temp = pd.Series(
                mean[col] + multiplier * std[col],
                index=data.index,
                name=col_name,
            )

            frames.append(temp)

    return pd.concat(frames, axis=1)


@_dfvalidate
def relative(
    df: pd.DataFrame,
    calculations: list[dict[str, str]],
) -> pd.DataFrame:
    """
    Calculate relative series between selected columns using a dictionary-based
    configuration.

    Description
    -----------
    This function creates derived time series by applying arithmetic operations
    between pairs of columns. Each calculation is defined as a dictionary with
    the following keys:

    - "ticker": main column used as the left-hand side of the operation.
    - "relative": comparison column used as the right-hand side of the operation.
      Use "1" to return the original ticker without applying an operation.
    - "operation": arithmetic operation to apply. Supported values are "-",
      "/", "*", and "+".
    - "name": optional custom output column name.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with a datetime index and one or more numeric columns.

    calculations : list[dict[str, str]]
        List of calculation dictionaries.

        Required keys:
        - "ticker"

        Optional keys:
        - "relative", default "1"
        - "operation", default "/"
        - "name", default generated automatically

    Returns
    -------
    pd.DataFrame
        DataFrame with calculated relative series.

    Raises
    ------
    ValueError
        If calculations is empty, if a required column is missing, or if an
        unsupported operation is provided.

    TypeError
        If calculations is not a list of dictionaries.

    Examples
    --------
    calculations = [
        {
            "ticker": "SPY",
            "relative": "ACWI",
            "operation": "/",
            "name": "SPY vs ACWI",
        },
        {
            "ticker": "EEM",
            "relative": "ACWI",
            "operation": "-",
        },
        {
            "ticker": "GLD",
            "relative": "1",
        },
    ]

    output = relative(df, calculations=calculations)
    """
    if not isinstance(calculations, list):
        raise TypeError("calculations must be a list of dictionaries.")

    if len(calculations) == 0:
        raise ValueError("calculations cannot be empty.")

    data = df.sort_index()

    operations = {
        "-": lambda x, y: x - y,
        "/": lambda x, y: x / y,
        "*": lambda x, y: x * y,
        "+": lambda x, y: x + y,
    }

    default_names = {
        "-": "Spread",
        "/": "Relative",
        "*": "Multiplication",
        "+": "Sum",
    }

    frames = []

    for i, calc in enumerate(calculations):
        if not isinstance(calc, dict):
            raise TypeError(
                f"Each item in calculations must be a dictionary. "
                f"Invalid item at position {i}."
            )

        if "ticker" not in calc:
            raise ValueError(
                f"Missing required key 'ticker' in calculation at position {i}."
            )

        ticker = calc["ticker"]
        relative_ticker = calc.get("relative", "1")
        operation = calc.get("operation", "/")
        custom_name = calc.get("name")

        if ticker not in data.columns:
            raise ValueError(
                f"Ticker '{ticker}' was not found in the DataFrame."
            )

        if relative_ticker != "1" and relative_ticker not in data.columns:
            raise ValueError(
                f"Relative ticker '{relative_ticker}' was not found in the DataFrame."
            )

        if relative_ticker == "1":
            output = data[ticker].copy()
            output.name = custom_name if custom_name is not None else ticker
            frames.append(output)
            continue

        if operation not in operations:
            raise ValueError(
                f"Operation '{operation}' is not supported. "
                "Use '-', '/', '*', or '+'."
            )

        output = operations[operation](
            data[ticker],
            data[relative_ticker],
        )

        if custom_name is not None:
            output_name = custom_name
        else:
            output_name = (
                f"{default_names[operation]} {ticker} vs {relative_ticker}"
            )

        output = output.rename(output_name)
        frames.append(output)

    return pd.concat(frames, axis=1)


@_dfvalidate
def rank_percentile(
    df: pd.DataFrame,
    value: float | int | pd.DataFrame | None = None,
) -> pd.Series:
    """
    Calculate percentile rank by column.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with numeric columns.

    value : float, int, pd.DataFrame, or None, default None
        Value to rank against the historical distribution.
        - If None, ranks the last row of df.
        - If scalar, df must have exactly one column.
        - If DataFrame, it must have exactly one row and the same columns as df.

    Returns
    -------
    pd.Series
        Percentile rank by column.
    """
    data = df.sort_index()

    if value is None:
        output = data.rank(pct=True).iloc[-1]
        return output.rename("Percentile Rank")

    if isinstance(value, (int, float)):
        if data.shape[1] > 1:
            raise ValueError(
                "When the DataFrame has more than one column, value must be "
                "a one-row DataFrame with the same columns."
            )

        value_row = pd.DataFrame(
            [[value]],
            columns=data.columns,
        )

    elif isinstance(value, pd.DataFrame):
        if value.shape[0] != 1:
            raise ValueError("value must be a one-row DataFrame.")

        missing_cols = [col for col in data.columns if col not in value.columns]
        extra_cols = [col for col in value.columns if col not in data.columns]

        if missing_cols:
            raise ValueError(f"Missing columns in value: {missing_cols}")

        if extra_cols:
            raise ValueError(
                f"value contains columns that are not present in df: {extra_cols}"
            )

        value_row = value[data.columns].copy()

    else:
        raise TypeError(
            "value must be None, int, float, or a one-row DataFrame."
        )

    data_temp = pd.concat(
        [data, value_row],
        axis=0,
    )

    output = data_temp.rank(pct=True).iloc[-1]

    return output.rename("Percentile Rank")

