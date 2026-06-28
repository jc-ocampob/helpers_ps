from xbbg import blp
import pandas as pd

import time


def _to_pandas_df(obj):
    """Convert xbbg / narwhals / pyarrow outputs to pandas.DataFrame."""
    if isinstance(obj, pd.DataFrame):
        return obj

    # narwhals -> native backend object
    if hasattr(obj, "to_native"):
        obj = obj.to_native()

    # pyarrow.Table -> pandas
    if hasattr(obj, "to_pandas"):
        obj = obj.to_pandas()

    if isinstance(obj, pd.DataFrame):
        return obj

    raise TypeError(f"Could not convert output to pandas.DataFrame. Final type: {type(obj)}")

def _as_list(x):
    if isinstance(x, str):
        return [x]
    return list(x)

def _reshape_bdh_output(df: pd.DataFrame, tickers, flds) -> pd.DataFrame:
    """
    Normalize Bloomberg historical output to:
    ['date', 'ticker', 'field', 'value']
    """

    df = df.copy()

    # --------------------------------------------------
    # CASE 0: output already comes in long format
    # --------------------------------------------------
    expected_long_cols = {"ticker", "date", "field", "value"}
    if expected_long_cols.issubset(set(map(str, df.columns))):
        df = df.rename(columns={c: str(c) for c in df.columns})
        df = df[["date", "ticker", "field", "value"]].copy()
        return df

    # --------------------------------------------------
    # CASE 1: MultiIndex columns -> reshape
    # --------------------------------------------------
    if isinstance(df.columns, pd.MultiIndex):
        df.index.name = "date"

        if df.columns.nlevels != 2:
            raise ValueError(
                f"Unexpected MultiIndex with {df.columns.nlevels} column levels; expected 2."
            )

        df.columns = df.columns.set_names(["ticker", "field"])

        try:
            out = (
                df.stack(["ticker", "field"], dropna=False)
                  .rename("value")
                  .reset_index()
            )
        except TypeError:
            out = (
                df.stack(["ticker", "field"])
                  .rename("value")
                  .reset_index()
            )

        out = out[["date", "ticker", "field", "value"]].copy()
        return out

    # --------------------------------------------------
    # CASE 2: single-level columns, standard fallback
    # --------------------------------------------------
    tickers_list = _as_list(tickers)
    flds_list = _as_list(flds)

    df.index.name = "date"
    out = df.reset_index()

    # remove artificial index columns if they appear
    artificial_cols = [c for c in out.columns if str(c).lower() in {"index", "level_0"}]
    if artificial_cols:
        out = out.drop(columns=artificial_cols)

    # identify date column
    date_col = None
    for c in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[c]):
            date_col = c
            break

    if date_col is None:
        for c in out.columns:
            converted = pd.to_datetime(out[c], errors="coerce")
            if converted.notna().sum() >= max(1, int(len(out) * 0.8)):
                out[c] = converted
                date_col = c
                break

    if date_col is None:
        raise ValueError(f"Could not identify date column. Columns found: {list(out.columns)}")

    # identify numeric value column
    candidate_value_cols = [c for c in out.columns if c != date_col]
    numeric_candidates = [c for c in candidate_value_cols if pd.api.types.is_numeric_dtype(out[c])]

    if not numeric_candidates:
        raise ValueError(f"Could not identify numeric value column. Columns found: {list(out.columns)}")

    value_col = numeric_candidates[0]

    out = out.rename(columns={date_col: "date", value_col: "value"})
    out["ticker"] = tickers_list[0] if len(tickers_list) == 1 else "|".join(map(str, tickers_list))
    out["field"] = flds_list[0] if len(flds_list) == 1 else "|".join(map(str, flds_list))

    out = out[["date", "ticker", "field", "value"]].copy()
    return out

def bdh_many(requests: list[dict], errors: bool = False):
    """
    Download historical Bloomberg data and return standardized long-format output.

    Parameters
    ----------
    requests : list[dict]
        Each dict may include:
            - ticker: str or list[str]
            - flds: str or list[str]
            - start_date: str
            - end_date: str
            - additional Bloomberg parameters / overrides

    errors : bool, default False
        If True, also returns an error dataframe.

    Returns
    -------
    pd.DataFrame
        Columns:
        ['date', 'ticker', 'field', 'value', 'overrides']

    If errors=True:
        returns (result_df, error_df)
    """
    frames = []
    error_list = []

    for i, req in enumerate(requests):
        try:
            params = req.copy()
            tickers = params.pop("ticker")
            flds = params.pop("flds")

            params_for_storage = {
                k: v for k, v in params.items()
                if k not in {"start_date", "end_date"}
            }

            overrides_str = ", ".join(
                f"{k}={repr(v)}" for k, v in sorted(params_for_storage.items())
            )

            raw = blp.bdh(
                tickers=tickers,
                flds=flds,
                **params
            )

            df = _to_pandas_df(raw)

            if df.empty:
                error_list.append({
                    "request_index": i,
                    "ticker": tickers,
                    "flds": flds,
                    "error": "Empty DataFrame"
                })
                continue

            df_long = _reshape_bdh_output(df, tickers=tickers, flds=flds)
            df_long["overrides"] = overrides_str

            frames.append(df_long)

        except Exception as e:
            error_list.append({
                "request_index": i,
                "ticker": req.get("ticker"),
                "flds": req.get("flds"),
                "error": str(e)
            })

    if frames:
        result = pd.concat(frames, ignore_index=True)
        result = result[["date", "ticker", "field", "value", "overrides"]]
        result = result.sort_values(["ticker", "field", "date"]).reset_index(drop=True)
    else:
        result = pd.DataFrame(columns=["date", "ticker", "field", "value", "overrides"])
    
    result["date"] = pd.to_datetime(result["date"])

    if errors:
        error_df = pd.DataFrame(error_list)
        return result, error_df

    return result

def _to_dict(data:str):
    data = data.split(",")
    final_dict = {}
    for d in data:
        _key = d.split("=")[0]
        _val = d.split("=")[1]
        final_dict[_key] = _val
    return final_dict

def bdh_many_data_frame(dataframe: pd.DataFrame, cache: bool = True, save_dict: dict = None) -> pd.DataFrame:
    """
    Funcion para pasar la plantilla de dataframe de base de tickers las unicas columnas permitidas son
    "unique_id","grouping", "ticker", "field", "start_date" y cualquier otra columna de override
    """

    # Columas necesarias que esten en el dataframe
    columns_necesary = list(set(["unique_id","grouping", "ticker", "field", "start_date", "overrides"]))
    
    # Validación de las columnas solo tengan las columnas requeridas
    columns_df = list(set([x for x in dataframe.columns.tolist() if x in columns_necesary]))

    if columns_necesary != columns_df:
        raise TypeError(f"Las unicas columnas que deben estar en el data frame son {columns_necesary}\nSin embargo las columnas recibidas son {columns_df}")

    #filtrando solo por las columnas necesarias
    dataframe = dataframe[columns_necesary]
    
    # primero haremos una pre validación de que la data que estamos buscando traer no existe previamente en el 
    if cache:
        pass
    else:
        # construimos los dict basado en los grouping de overrides
        grouping = dataframe["grouping"].unique()

        list_dicts = []

        for group in grouping:
            _df = dataframe[dataframe["grouping"] == group].copy()
            overrides = _to_dict(_df["overrides"].unique()[0])
            final_dict = dict(
                tickers = _df["ticker"].tolist(),
                field = _df["field"].unique()[0],
                start_date = _df["start_date"].unique()[0],
                **overrides
            )
            list_dicts.append(final_dict)
            
            
            
    # Establecer todas las columnas que estan en el dataframe que deberian ser considerados parametros



    # Una vez validad la información hay que construir la data
    # TODO: Agregar la transformación del data frame en un formato legible para poder jalar la data
    dataframe_con_data = pd.DataFrame

    def _save(
            dataframe: pd.DataFrame,
            save: bool = False,
            formato: str = "csv",
            nombre: str = None
    ):
        if not save:
            return None
        
        if formato == "csv":
            dataframe.to_csv(f"{nombre}.csv")
        elif formato == "parquet":
            dataframe.to_parquet(f"{nombre}.parquet")
        elif formato == "excel":
            dataframe.to_excel(f"{nombre}.xlsx")
        else:
            raise NotImplementedError(f"No esta implementado el formato {formato}")
    
    if save_dict is not None:
        _save(dataframe, **save_dict)    

    return dataframe, "dataframe_con_data" 