from dataclasses import dataclass
import pandas as pd
import numpy as np
from scipy.stats import norm
from collections import Counter

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
