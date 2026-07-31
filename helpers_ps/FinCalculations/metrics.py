from dataclasses import dataclass
import pandas as pd
import numpy as np
from scipy.stats import norm
from collections import Counter
from functools import wraps


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


# Functions

def _dfvalidate(func):
    """
    Validate that the decorated function receives a valid pandas DataFrame.

    Description
    -----------
    This decorator searches for the first pandas DataFrame passed either as a
    positional argument or as a keyword argument. It validates that the DataFrame
    is not empty and that its index is datetime-like before executing the
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
        If no pandas DataFrame is found or if the DataFrame index is not datetime-like.

    ValueError
        If the DataFrame is empty.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        df = None

        # Search DataFrame in positional arguments
        for arg in args:
            if isinstance(arg, pd.DataFrame):
                df = arg
                break

        # If not found, search DataFrame in keyword arguments
        if df is None:
            for value in kwargs.values():
                if isinstance(value, pd.DataFrame):
                    df = value
                    break

        # Validate that a DataFrame was provided
        if df is None:
            raise TypeError(
                f"No pandas DataFrame was found in function '{func.__name__}'"
            )

        # Validate that DataFrame is not empty
        if df.empty:
            raise ValueError("The DataFrame cannot be empty.")

        # Validate that index is datetime
        if not pd.api.types.is_datetime64_any_dtype(df.index):
            raise TypeError("The DataFrame index must be datetime-like.")

        return func(*args, **kwargs)

    return wrapper


@_dfvalidate
def ytd(
    df: pd.DataFrame,
    fallback: bool = True
) -> pd.DataFrame:
    """
    Calculate Year-To-Date returns for price series.

    Description
    -----------
    This function calculates the Year-To-Date performance for each column in a
    price DataFrame. The base value is the last valid price from the previous
    year. If no previous year-end value is available and fallback is enabled,
    the first valid value of the current year is used as the base.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame with a datetime index and one or more asset price
        columns.

    fallback : bool, default True
        If True, uses the first valid price of the current year when the
        previous year-end price is not available.

    Returns
    -------
    pd.DataFrame
        DataFrame with Year-To-Date returns for each price series.
    """

    df = df.sort_index()

    year = df.index.to_period("Y")

    year_end_prices = (
        df.groupby(year)
        .apply(lambda g: g.ffill().iloc[-1])
    )

    prev_period = (df.index - pd.offsets.YearEnd(1)).to_period("Y")

    prev_year_bases = year_end_prices.reindex(prev_period)
    prev_year_bases.index = df.index
    prev_year_bases = prev_year_bases.reindex(columns=df.columns)

    if fallback:
        first_in_year = (
            df.groupby(year)
            .apply(lambda g: g.bfill().iloc[0])
        )

        first_in_year = first_in_year.reindex(year)
        first_in_year.index = df.index
        first_in_year = first_in_year.reindex(columns=df.columns)

        prev_year_bases = prev_year_bases.combine_first(first_in_year)

    if not prev_year_bases.index.equals(df.index):
        raise RuntimeError("Index mismatch after alignment.")

    if list(prev_year_bases.columns) != list(df.columns):
        raise RuntimeError("Columns mismatch after alignment.")

    assert df.shape == prev_year_bases.shape, (
        f"Shape mismatch: df {df.shape} vs bases {prev_year_bases.shape}"
    )

    ytd = df.div(prev_year_bases) - 1

    return ytd


@_dfvalidate
def mtd(
    df: pd.DataFrame,
    fallback: bool = True
) -> pd.DataFrame:
    """
    Calculate Month-To-Date returns for price series.

    Description
    -----------
    This function calculates the Month-To-Date performance for each column in a
    price DataFrame. The base value is the last valid price from the previous
    month. If no previous month-end value is available and fallback is enabled,
    the first valid value of the current month is used as the base.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame with a datetime index and one or more asset price
        columns.

    fallback : bool, default True
        If True, uses the first valid price of the current month when the
        previous month-end price is not available.

    Returns
    -------
    pd.DataFrame
        DataFrame with Month-To-Date returns for each price series.
    """

    df = df.sort_index()

    mon = df.index.to_period("M")

    month_end_prices = (
        df.groupby(mon)
        .apply(lambda g: g.ffill().iloc[-1])
    )

    prev_mon = (df.index - pd.offsets.MonthEnd(1)).to_period("M")
    prev_month_bases = month_end_prices.reindex(prev_mon)

    prev_month_bases.index = df.index
    prev_month_bases = prev_month_bases.reindex(columns=df.columns)

    if fallback:
        first_in_month = (
            df.groupby(mon)
            .apply(lambda g: g.bfill().iloc[0])
        )

        first_in_month = first_in_month.reindex(mon)
        first_in_month.index = df.index
        first_in_month = first_in_month.reindex(columns=df.columns)

        prev_month_bases = prev_month_bases.combine_first(first_in_month)

    assert df.shape == prev_month_bases.shape, (
        f"Shape mismatch: df {df.shape} vs bases {prev_month_bases.shape}"
    )
    assert df.index.equals(prev_month_bases.index), "Index mismatch after alignment."
    assert list(df.columns) == list(prev_month_bases.columns), "Columns mismatch after alignment."

    mtd = df.div(prev_month_bases) - 1

    return mtd


@_dfvalidate
def qtd(
    df: pd.DataFrame,
    fallback: bool = True
) -> pd.DataFrame:
    """
    Calculate Quarter-To-Date returns for price series.

    Description
    -----------
    This function calculates the Quarter-To-Date performance for each column in a
    price DataFrame. The base value is the last valid price from the previous
    quarter. If no previous quarter-end value is available and fallback is
    enabled, the first valid value of the current quarter is used as the base.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame with a datetime index and one or more asset price
        columns.

    fallback : bool, default True
        If True, uses the first valid price of the current quarter when the
        previous quarter-end price is not available.

    Returns
    -------
    pd.DataFrame
        DataFrame with Quarter-To-Date returns for each price series.
    """

    df = df.sort_index()

    qtr = df.index.to_period("Q")

    quarter_end_prices = (
        df.groupby(qtr)
        .apply(lambda g: g.ffill().iloc[-1])
    )

    prev_qtr = (df.index - pd.offsets.QuarterEnd(1)).to_period("Q")
    prev_quarter_bases = quarter_end_prices.reindex(prev_qtr)

    prev_quarter_bases.index = df.index
    prev_quarter_bases = prev_quarter_bases.reindex(columns=df.columns)

    if fallback:
        first_in_quarter = (
            df.groupby(qtr)
            .apply(lambda g: g.bfill().iloc[0])
        )

        first_in_quarter = first_in_quarter.reindex(qtr)
        first_in_quarter.index = df.index
        first_in_quarter = first_in_quarter.reindex(columns=df.columns)

        prev_quarter_bases = prev_quarter_bases.combine_first(first_in_quarter)

    assert df.shape == prev_quarter_bases.shape, (
        f"Shape mismatch: df {df.shape} vs bases {prev_quarter_bases.shape}"
    )
    assert df.index.equals(prev_quarter_bases.index), "Index mismatch after alignment."
    assert list(df.columns) == list(prev_quarter_bases.columns), "Columns mismatch after alignment."

    qtd = df.div(prev_quarter_bases) - 1

    return qtd


@_dfvalidate
def drawdown(
    df: pd.DataFrame,
    method: str = "simple",
    min_price: float = 1e-6
) -> pd.DataFrame:
    """
    Calculate drawdown for price series.

    Description
    -----------
    This function calculates the drawdown of each price series relative to its
    historical running maximum. It supports both simple price-based drawdown and
    log-price-based drawdown.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame with a datetime index and one or more asset price
        columns.

    method : {"simple", "log"}, default "simple"
        Drawdown calculation method.
        - "simple": calculates drawdown using prices and running maximum prices.
        - "log": calculates drawdown using log-prices and running maximum log-prices.

    min_price : float, default 1e-6
        Minimum valid price threshold. Prices less than or equal to this value
        are treated as invalid to avoid division or logarithm issues.

    Returns
    -------
    pd.DataFrame
        DataFrame with drawdown values for each price series.
    """

    px = df.sort_index()

    px = px.where(px > min_price)

    if method == "simple":
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


@_dfvalidate
def downside_std(
    df: pd.DataFrame,
    method: str = "simple",
    target_return: float = 0.0,
    annualize: bool = False,
    periods_per_year: int = 252,
) -> pd.DataFrame:
    """
    Calculate downside standard deviation for each asset.

    Description
    -----------
    This function calculates downside deviation by considering only returns below
    a target return. Returns above the target are set to zero before calculating
    the downside standard deviation.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame with a datetime index and one or more asset price
        columns.

    method : {"simple", "log"}, default "simple"
        Return calculation method.
        - "simple": uses percentage returns.
        - "log": uses logarithmic returns.

    target_return : float, default 0.0
        Minimum acceptable return. Only returns below this threshold contribute
        to downside deviation.

    annualize : bool, default False
        If True, annualizes the downside standard deviation.

    periods_per_year : int, default 252
        Number of periods per year used for annualization.

    Returns
    -------
    pd.DataFrame
        DataFrame with one column named "std_downside" containing downside
        standard deviation by asset.
    """

    px = df.sort_index()

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


@_dfvalidate
def beta(
    df: pd.DataFrame,
    benchmark: str,
    window: int | None = None,
    method: str = "simple",
) -> pd.Series | pd.DataFrame:
    """
    Calculate beta relative to a benchmark.

    Description
    -----------
    This function calculates either historical beta or rolling beta for each
    asset relative to a benchmark column. Beta is calculated as covariance of
    asset returns with benchmark returns divided by benchmark variance.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame with a datetime index. It must include the benchmark
        column and one or more asset columns.

    benchmark : str
        Column name of the benchmark asset.

    window : int or None, default None
        Rolling window size.
        - If None, historical beta is calculated using the full return history.
        - If an integer is provided, rolling beta is calculated.

    method : {"simple", "log"}, default "simple"
        Return calculation method.
        - "simple": uses percentage returns.
        - "log": uses logarithmic returns.

    Returns
    -------
    pd.Series or pd.DataFrame
        Series with historical beta by asset when window is None.
        DataFrame with rolling beta values when window is provided.
    """

    px = df.sort_index()

    if benchmark not in px.columns.tolist():
        raise TypeError(f"{benchmark} is not a valid column")

    if method == "simple":
        rets = px.pct_change()

    elif method == "log":
        rets = np.log(px / px.shift(1))

    else:
        raise ValueError("method must be 'simple' or 'log'")

    benchmark_returns = rets[benchmark]

    if window is None:
        bench_var = benchmark_returns.var()

        beta = rets.apply(
            lambda col: col.cov(benchmark_returns) / bench_var
        )

        return beta

    bench_var = benchmark_returns.rolling(window).var()

    rolling_beta = (
        rets.rolling(window)
        .cov(benchmark_returns)
        .divide(bench_var, axis=0)
    )

    return rolling_beta


@_dfvalidate
def upside_capture(
    df: pd.DataFrame,
    benchmark: str,
    method: str = "simple",
) -> pd.Series:
    """
    Calculate upside capture ratio relative to a benchmark.

    Description
    -----------
    This function calculates the upside capture ratio for each asset by comparing
    asset performance against benchmark performance during periods when the
    benchmark return is positive.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame with a datetime index. It must include the benchmark
        column and one or more asset columns.

    benchmark : str
        Column name of the benchmark asset.

    method : {"simple", "log"}, default "simple"
        Return calculation method.
        - "simple": uses percentage returns.
        - "log": uses logarithmic returns.

    Returns
    -------
    pd.Series
        Upside capture ratio by asset.
    """

    px = df.sort_index()

    if benchmark not in px.columns.tolist():
        raise TypeError(f"{benchmark} is not a valid column")

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


@_dfvalidate
def downside_capture(
    df: pd.DataFrame,
    benchmark: str,
    method: str = "simple",
) -> pd.Series:
    """
    Calculate downside capture ratio relative to a benchmark.

    Description
    -----------
    This function calculates the downside capture ratio for each asset by
    comparing asset performance against benchmark performance during periods
    when the benchmark return is negative.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame with a datetime index. It must include the benchmark
        column and one or more asset columns.

    benchmark : str
        Column name of the benchmark asset.

    method : {"simple", "log"}, default "simple"
        Return calculation method.
        - "simple": uses percentage returns.
        - "log": uses logarithmic returns.

    Returns
    -------
    pd.Series
        Downside capture ratio by asset.
    """

    px = df.sort_index()

    if benchmark not in px.columns.tolist():
        raise TypeError(f"{benchmark} is not a valid column")

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


@_dfvalidate
def capture_ratio(
    df: pd.DataFrame,
    benchmark: str,
    method: str = "simple",
) -> pd.Series:
    """
    Calculate the upside-to-downside capture ratio.

    Description
    -----------
    This function calculates the ratio between upside capture and downside
    capture for each asset relative to a benchmark. A higher value indicates
    stronger participation in positive benchmark periods relative to negative
    benchmark periods.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame with a datetime index. It must include the benchmark
        column and one or more asset columns.

    benchmark : str
        Column name of the benchmark asset.

    method : {"simple", "log"}, default "simple"
        Return calculation method.
        - "simple": uses percentage returns.
        - "log": uses logarithmic returns.

    Returns
    -------
    pd.Series
        Upside capture divided by downside capture for each asset.
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

    return uc / dc


@_dfvalidate
def var(
    df: pd.DataFrame,
    confidence: float = 0.95,
    method: str = "historical",
    returns_method: str = "simple",
    horizon: int = 1,
) -> pd.Series:
    """
    Calculate Value at Risk for each asset.

    Description
    -----------
    This function calculates Value at Risk using historical simulation,
    Gaussian parametric VaR, or Cornish-Fisher modified VaR. The result is
    expressed as a positive loss.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame with a datetime index and one or more asset price
        columns.

    confidence : float, default 0.95
        Confidence level used to calculate VaR.

    method : {"historical", "gaussian", "cornish_fisher"}, default "historical"
        VaR calculation methodology.
        - "historical": historical simulation VaR.
        - "gaussian": parametric normal VaR.
        - "cornish_fisher": modified VaR adjusted for skewness and kurtosis.

    returns_method : {"simple", "log"}, default "simple"
        Return calculation method.
        - "simple": uses percentage returns.
        - "log": uses logarithmic returns.

    horizon : int, default 1
        Holding period expressed in return periods. If greater than 1, VaR is
        scaled using the square-root-of-time rule.

    Returns
    -------
    pd.Series
        Value at Risk by asset, expressed as a positive loss.
    """

    px = df.sort_index()

    if returns_method == "simple":
        rets = px.pct_change().dropna()

    elif returns_method == "log":
        rets = np.log(px / px.shift(1)).dropna()

    else:
        raise ValueError("returns_method must be 'simple' or 'log'")

    alpha = 1 - confidence

    if method == "historical":
        output = -rets.quantile(alpha)

    elif method == "gaussian":
        z = norm.ppf(alpha)
        output = -(rets.mean() + z * rets.std())

    elif method == "cornish_fisher":
        z = norm.ppf(alpha)

        s = rets.skew()
        k = rets.kurtosis()

        z_cf = (
            z
            + ((z**2 - 1) * s / 6)
            + ((z**3 - 3 * z) * k / 24)
            - ((2 * z**3 - 5 * z) * s**2 / 36)
        )

        output = -(rets.mean() + z_cf * rets.std())

    else:
        raise ValueError(
            "method must be 'historical', 'gaussian', or 'cornish_fisher'"
        )

    if horizon > 1:
        output *= np.sqrt(horizon)

    return output.rename(
        f"VaR_{method}_{int(confidence * 100)}"
    )


@_dfvalidate
def tracking_error(
    df: pd.DataFrame,
    benchmark: str,
    method: str = "simple",
    annualize: bool = True,
    periods_per_year: int = 252,
) -> pd.Series:
    """
    Calculate tracking error relative to a benchmark.

    Description
    -----------
    This function calculates the standard deviation of active returns, where
    active return is defined as asset return minus benchmark return. The result
    can be annualized.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame with a datetime index. It must include the benchmark
        column and one or more asset columns.

    benchmark : str
        Column name of the benchmark asset.

    method : {"simple", "log"}, default "simple"
        Return calculation method.
        - "simple": uses percentage returns.
        - "log": uses logarithmic returns.

    annualize : bool, default True
        If True, annualizes tracking error.

    periods_per_year : int, default 252
        Number of periods per year used for annualization.

    Returns
    -------
    pd.Series
        Tracking error by asset.
    """

    px = df.sort_index()

    if benchmark not in px.columns.tolist():
        raise TypeError(f"{benchmark} is not a valid column")

    if method == "simple":
        rets = px.pct_change()

    elif method == "log":
        rets = np.log(px / px.shift(1))

    else:
        raise ValueError("method must be 'simple' or 'log'")

    benchmark_returns = rets[benchmark]

    active_returns = rets.sub(
        benchmark_returns,
        axis=0
    )

    te = active_returns.std()

    if annualize:
        te *= np.sqrt(periods_per_year)

    return te.rename("Tracking Error")


@_dfvalidate
def information_ratio(
    df: pd.DataFrame,
    benchmark: str,
    method: str = "simple",
    annualize: bool = True,
    periods_per_year: int = 252,
) -> pd.Series:
    """
    Calculate information ratio relative to a benchmark.

    Description
    -----------
    This function calculates the information ratio as average active return
    divided by tracking error. Active return is defined as asset return minus
    benchmark return. The ratio can be annualized.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame with a datetime index. It must include the benchmark
        column and one or more asset columns.

    benchmark : str
        Column name of the benchmark asset.

    method : {"simple", "log"}, default "simple"
        Return calculation method.
        - "simple": uses percentage returns.
        - "log": uses logarithmic returns.

    annualize : bool, default True
        If True, annualizes the information ratio.

    periods_per_year : int, default 252
        Number of periods per year used for annualization.

    Returns
    -------
    pd.Series
        Information ratio by asset.
    """

    px = df.sort_index()

    if benchmark not in px.columns.tolist():
        raise TypeError(f"{benchmark} is not a valid column")

    if method == "simple":
        rets = px.pct_change()

    elif method == "log":
        rets = np.log(px / px.shift(1))

    else:
        raise ValueError("method must be 'simple' or 'log'")

    active_returns = rets.sub(
        rets[benchmark],
        axis=0
    )

    active_return = active_returns.mean()
    tracking_error_value = active_returns.std()

    ir = active_return / tracking_error_value

    if annualize:
        ir *= np.sqrt(periods_per_year)

    return ir.rename("Information Ratio")


@_dfvalidate
def excess_return(
    df: pd.DataFrame,
    benchmark: str,
    period: str = "qtd"
) -> pd.DataFrame:
    """
    Calculate excess return relative to a benchmark.

    Description
    -----------
    This function calculates the return of each asset over a selected period and
    subtracts the benchmark return for the same period. Supported periods are
    Month-To-Date, Quarter-To-Date, and Year-To-Date.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame with a datetime index. It must include the benchmark
        column and one or more asset columns.

    benchmark : str
        Column name of the benchmark asset.

    period : {"mtd", "qtd", "ytd"}, default "qtd"
        Period used to calculate returns before computing excess return.

    Returns
    -------
    pd.DataFrame
        DataFrame with excess return by asset through time.
    """

    px = df.sort_index()

    if benchmark not in px.columns.tolist():
        raise TypeError(f"{benchmark} is not a valid column")

    if period == "ytd":
        data = ytd(px)

    elif period == "mtd":
        data = mtd(px)

    elif period == "qtd":
        data = qtd(px)

    else:
        raise NotImplementedError(f"{period} is not implemented")

    data = data.sub(data[benchmark], axis=0)

    return data


@_dfvalidate
def consistency(
    df: pd.DataFrame,
    benchmark: str,
    period: str = "qtd"
) -> pd.Series:
    """
    Calculate outperformance consistency relative to a benchmark.

    Description
    -----------
    This function calculates the percentage of periods in which each asset
    outperformed the benchmark based on excess returns.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame with a datetime index. It must include the benchmark
        column and one or more asset columns.

    benchmark : str
        Column name of the benchmark asset.

    period : {"mtd", "qtd", "ytd"}, default "qtd"
        Period used to calculate returns before computing excess return.

    Returns
    -------
    pd.Series
        Percentage of observations where each asset had positive excess return.
    """

    px = df.sort_index()

    if benchmark not in px.columns.tolist():
        raise TypeError(f"{benchmark} is not a valid column")

    exre = excess_return(
        df=px,
        benchmark=benchmark,
        period=period
    )

    output = exre.gt(0).sum() / exre.notna().sum()

    return output.rename("Consistency")


@_dfvalidate
def rsi(
    df: pd.DataFrame,
    window: int = 14,
    prefix: str = "RSI{w}_"
) -> pd.DataFrame:
    """
    Calculate Relative Strength Index for price series.

    Description
    -----------
    This function calculates the Relative Strength Index for each price series
    using the specified rolling window. Output columns are renamed using the
    selected prefix.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame with a datetime index and one or more asset price
        columns.

    window : int, default 14
        Number of periods used to calculate average gains and losses.

    prefix : str, default "RSI{w}_"
        Prefix used to rename output columns. The placeholder "{w}" is replaced
        by the window value.

    Returns
    -------
    pd.DataFrame
        DataFrame with RSI values for each price series.
    """

    df = df.sort_index()

    delta = df.diff()

    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=window, min_periods=window).mean()
    avg_loss = loss.rolling(window=window, min_periods=window).mean()

    rs = avg_gain / avg_loss
    output = 100.0 - (100.0 / (1.0 + rs))

    output.columns = [f"{prefix.format(w=window)}{c}" for c in df.columns]

    return output


@_dfvalidate
def sma(
    df: pd.DataFrame,
    windows: list[int] | None = None,
    min_periods: int | None = None,
    prefix: str = "SMA{w}_"
) -> pd.DataFrame:
    """
    Calculate Simple Moving Averages for price series.

    Description
    -----------
    This function calculates Simple Moving Averages for each price series across
    one or more rolling windows. Results for all windows are concatenated into a
    single DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame with a datetime index and one or more asset price
        columns.

    windows : list[int] or None, default None
        List of rolling windows. If None, the default window is [50].

    min_periods : int or None, default None
        Minimum number of observations required to compute the rolling mean. If
        None, each window value is used as its own minimum period.

    prefix : str, default "SMA{w}_"
        Prefix used to rename output columns. The placeholder "{w}" is replaced
        by each window value.

    Returns
    -------
    pd.DataFrame
        DataFrame with SMA values for each price series and window.
    """

    if windows is None:
        windows = [50]

    df = df.sort_index()

    frames = []

    for w in windows:
        mp = w if min_periods is None else min_periods
        output = df.rolling(window=w, min_periods=mp).mean()
        output.columns = [f"{prefix.format(w=w)}{c}" for c in df.columns]
        frames.append(output)

    return pd.concat(frames, axis=1)


@_dfvalidate
def ema(
    df: pd.DataFrame,
    windows: list[int] | None = None,
    min_periods: int | None = None,
    prefix: str = "EMA{w}_"
) -> pd.DataFrame:
    """
    Calculate Exponential Moving Averages for price series.

    Description
    -----------
    This function calculates Exponential Moving Averages for each price series
    across one or more exponential windows. Results for all windows are
    concatenated into a single DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame with a datetime index and one or more asset price
        columns.

    windows : list[int] or None, default None
        List of exponential moving average spans. If None, the default window
        is [27].

    min_periods : int or None, default None
        Minimum number of observations required to compute the EMA. If None,
        each window value is used as its own minimum period.

    prefix : str, default "EMA{w}_"
        Prefix used to rename output columns. The placeholder "{w}" is replaced
        by each window value.

    Returns
    -------
    pd.DataFrame
        DataFrame with EMA values for each price series and window.
    """

    if windows is None:
        windows = [27]

    df = df.sort_index()

    frames = []

    for w in windows:
        mp = w if min_periods is None else min_periods
        output = df.ewm(span=w, min_periods=mp).mean()
        output.columns = [f"{prefix.format(w=w)}{c}" for c in df.columns]
        frames.append(output)

    return pd.concat(frames, axis=1)


@_dfvalidate
def ranges(
    df: pd.DataFrame,
    desviaciones: list[int] | None = None,
    prefix: str = "Media({w}sigma)_"
) -> pd.DataFrame:
    """
    Calculate static mean-based ranges using standard deviation offsets.

    Description
    -----------
    This function calculates horizontal reference levels for each column based on
    the column mean plus a selected number of standard deviations. Each generated
    column contains a constant value through the full index of the input
    DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with a datetime index and one or more numeric columns.

    desviaciones : list[int] or None, default None
        List of standard deviation multipliers. If None, the default values are
        [-1, 0, 1].

    prefix : str, default "Media({w}sigma)_"
        Prefix used to rename output columns. The placeholder "{w}" is replaced
        by each standard deviation multiplier.

    Returns
    -------
    pd.DataFrame
        DataFrame with generated mean plus/minus standard deviation reference
        levels for each input column.
    """

    if desviaciones is None:
        desviaciones = [-1, 0, 1]

    mean = df.mean()
    std = df.std()

    final = None

    for col in df.columns:
        for w in desviaciones:
            col_name = prefix.format(w=w)

            if final is None:
                temp = df[[col]].copy()
                temp[f"{col_name}{col}"] = mean[col] + w * std[col]
                temp = temp.drop(columns=[col])
                final = temp

            else:
                final[f"{col_name}{col}"] = mean[col] + w * std[col]

    return final


@_dfvalidate
def relative(
    df: pd.DataFrame,
    ticker_list: list[str] | None = None,
    relative_list: list[str] | None = None,
    operation_list: list[str] | None = None,
) -> pd.DataFrame:
    """
    Calculate relative series between selected columns.

    Description
    -----------
    This function creates derived time series by applying arithmetic operations
    between pairs of columns. Supported operations are subtraction, division,
    multiplication, and addition. A relative value equal to "1" means that the
    original ticker series is returned without comparison.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with a datetime index and one or more numeric columns.

    ticker_list : list[str] or None, default None
        List of main ticker columns to use in each calculation.

    relative_list : list[str] or None, default None
        List of relative ticker columns to compare against. Use "1" to return
        the original ticker without applying an operation.

    operation_list : list[str] or None, default None
        List of arithmetic operations. Supported values are:
        - "-": subtraction
        - "/": division
        - "*": multiplication
        - "+": addition

    Returns
    -------
    pd.DataFrame
        DataFrame with calculated relative series.
    """

    if ticker_list is None or relative_list is None or operation_list is None:
        raise ValueError("ticker_list, relative_list, and operation_list cannot be None.")

    if not (len(ticker_list) == len(relative_list) == len(operation_list)):
        raise ValueError(
            "ticker_list, relative_list, and operation_list must have the same length."
        )

    for ticker in ticker_list:
        if ticker not in df.columns:
            raise ValueError(f"Ticker '{ticker}' was not found in the DataFrame.")

    for relative_ticker in relative_list:
        if relative_ticker not in df.columns and relative_ticker != "1":
            raise ValueError(
                f"Relative ticker '{relative_ticker}' was not found in the DataFrame and is not '1'."
            )

    final = None

    for i in range(len(ticker_list)):
        ticker = ticker_list[i]
        relative_ticker = relative_list[i]
        operation = operation_list[i]

        temp_data = df[[ticker, relative_ticker] if relative_ticker != "1" else [ticker]].copy()

        if relative_ticker == "1":
            temp_data = temp_data.rename(columns={ticker: ticker_list[i]})

            if i == 0:
                final = temp_data
            else:
                final = final.join(temp_data)

            continue

        if operation == "-":
            temp_data["Output"] = temp_data[ticker] - temp_data[relative_ticker]
            output_title = f"Spread {ticker_list[i]} vs {relative_list[i]}"

        elif operation == "/":
            temp_data["Output"] = temp_data[ticker] / temp_data[relative_ticker]
            output_title = f"Relative {ticker_list[i]} vs {relative_list[i]}"

        elif operation == "*":
            temp_data["Output"] = temp_data[ticker] * temp_data[relative_ticker]
            output_title = f"Multiplication {ticker_list[i]} vs {relative_list[i]}"

        elif operation == "+":
            temp_data["Output"] = temp_data[ticker] + temp_data[relative_ticker]
            output_title = f"Sum {ticker_list[i]} vs {relative_list[i]}"

        else:
            raise ValueError(
                f"Operation '{operation}' is not supported. Use '-', '/', '*', or '+'."
            )

        temp_data = temp_data[["Output"]].rename(columns={"Output": output_title})

        if i == 0:
            final = temp_data
        else:
            final = final.join(temp_data)

    return final


@_dfvalidate
def momentum(
    df: pd.DataFrame,
    windows: list[int] | None = None,
    prefix: str = "MomentumSimple{w}_",
) -> pd.DataFrame:
    """
    Calculate standardized momentum indicators.

    Description
    -----------
    This function calculates simple momentum over one or more lookback windows.
    Momentum is computed as the percentage change over each window and then
    standardized using its rolling mean and rolling standard deviation.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame with a datetime index and one or more asset price
        columns.

    windows : list[int] or None, default None
        List of lookback windows. If None, the default values are [15, 30].

    prefix : str, default "MomentumSimple{w}_"
        Prefix used to rename output columns. The placeholder "{w}" is replaced
        by each window value.

    Returns
    -------
    pd.DataFrame
        DataFrame with standardized momentum values for each asset and window.
    """

    if windows is None:
        windows = [15, 30]

    data = df.sort_index()

    frames = []

    for w in windows:
        data_temp = data.pct_change(periods=w)
        mean = data_temp.rolling(window=w).mean()
        std = data_temp.rolling(window=w).std()

        output = (data_temp - mean) / std.where(std != 0, 1)
        output.columns = [f"{prefix.format(w=w)}{c}" for c in data_temp.columns]

        frames.append(output)

    final = pd.concat(frames, axis=1)

    return final


@_dfvalidate
def momentum_sma(
    df: pd.DataFrame,
    prefix: str = "MomentumSMA_"
) -> pd.DataFrame:
    """
    Calculate a moving-average-based momentum score.

    Description
    -----------
    This function resamples prices to weekly frequency and calculates a momentum
    score based on the relationship between price, a 5-week moving average, a
    15-week moving average, the slope of the 15-week moving average, and the
    spread between both moving averages.

    Parameters
    ----------
    df : pd.DataFrame
        Price DataFrame with a datetime index and one or more asset price
        columns.

    prefix : str, default "MomentumSMA_"
        Prefix used to rename output columns.

    Returns
    -------
    pd.DataFrame
        DataFrame with momentum scores for each asset.
    """

    data_price = df.sort_index()
    data_price = data_price.resample("W").last()

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
            "Score"
        ] = 1

        temp.loc[
            (temp[ticker] < temp["MA(15)"])
            & (temp["dMA(15)"] > 0)
            & (temp["spreadW"] < 0),
            "Score"
        ] = 2

        temp.loc[
            (temp[ticker] > temp["MA(15)"])
            & (temp["dMA(15)"] < 0)
            & (temp["spreadW"] > 0),
            "Score"
        ] = 4

        temp.loc[
            (temp[ticker] > temp["MA(15)"])
            & (temp["dMA(15)"] > 0.0001)
            & (temp["spreadW"] > 0.0001),
            "Score"
        ] = 5

        temp.loc[temp["Score"].isna(), "Score"] = 3

        temp = temp[["Score"]].rename(columns={"Score": f"{prefix}{ticker}"})

        scores.append(temp)

    final = pd.concat(scores, axis=1)

    return final


@_dfvalidate
def rank_percentile(
    df: pd.DataFrame,
    value: float | int | pd.DataFrame | None = None,
) -> pd.Series:
    """
    Calculate percentile rank by column.

    Description
    -----------
    This function calculates the percentile rank for each column in a DataFrame.
    If no value is provided, it calculates the percentile rank of the last
    observation in the DataFrame. If a value is provided, it calculates where
    that value would rank within the historical distribution.

    For multi-column DataFrames, value must be a one-row DataFrame with the same
    columns as df. This avoids applying a single scalar value across metrics with
    different scales.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with a datetime index and one or more numeric columns.

    value : float, int, pd.DataFrame, or None, default None
        Value to rank against the historical distribution.
        - If None, the last row of df is ranked.
        - If float or int, df must have exactly one column.
        - If pd.DataFrame, it must have exactly one row and the same columns as df.

    Returns
    -------
    pd.Series
        Percentile rank by column.
    """

    if value is None:
        return df.rank(pct=True).iloc[-1]

    if isinstance(value, (int, float)):
        if df.shape[1] > 1:
            raise ValueError(
                "When the DataFrame has more than one column, value must be "
                "a one-row DataFrame with the same columns."
            )

        value_row = pd.DataFrame(
            [[value]],
            columns=df.columns,
        )

    elif isinstance(value, pd.DataFrame):
        if value.shape[0] != 1:
            raise ValueError("value must be a one-row DataFrame.")

        missing_cols = [col for col in df.columns if col not in value.columns]
        extra_cols = [col for col in value.columns if col not in df.columns]

        if missing_cols:
            raise ValueError(
                f"Missing columns in value: {missing_cols}"
            )

        if extra_cols:
            raise ValueError(
                f"value contains columns that are not present in df: {extra_cols}"
            )

        value_row = value[df.columns].copy()

    else:
        raise TypeError(
            "value must be None, int, float, or a one-row DataFrame."
        )

    df_temp = pd.concat(
        [df, value_row],
        axis=0,
    )

    percentile_value = df_temp.rank(pct=True).iloc[-1]

    return percentile_value













