
from xbbg import blp
import pandas as pd

def bdh_many(requests: list[dict], errors: bool = False):
    """
    Function to download historical Bloomberg data.

    Parameters
    ----------
    requests : list[dict]
        Each dict represents one Bloomberg request and may include:
            - ticker: str or list[str]
            - flds: str or list[str]
            - start_date: str
            - end_date: str
            - additional Bloomberg parameters / overrides
              (e.g. Per, Fill, Days, CshAdjNormal, etc.)

    errors : bool, default False
        If True, also returns a dataframe with errors.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns:
        ['date', 'ticker', 'field', 'value', 'overrides']

    If errors=True, returns:
        (result_df, error_df)
    """
    frames = []
    error_list = []

    for i, req in enumerate(requests):
        params = req.copy()
        tickers = params.pop('ticker')
        flds = params.pop('flds')

        # Store applied params excluding start_date and end_date
        params_for_storage = {
            k: v for k, v in params.items()
            if k not in {'start_date', 'end_date'}
        }

        overrides_str = ", ".join(
            f"{k}={repr(v)}" for k, v in sorted(params_for_storage.items())
        )

        try:
            df = blp.bdh(
                tickers=tickers,
                flds=flds,
                **params
            )

            if df.empty:
                error_list.append({
                    'request_index': i,
                    'ticker': tickers,
                    'flds': flds,
                    'error': 'Empty DataFrame'
                })
                continue

            if isinstance(df.columns, pd.MultiIndex):
                df_long = df.stack(list(range(df.columns.nlevels))).reset_index()

                if df.columns.nlevels == 2:
                    df_long.columns = ['date', 'ticker', 'field', 'value']
                else:
                    col_names = (
                        ['date']
                        + [f'level_{j}' for j in range(1, df.columns.nlevels + 1)]
                        + ['value']
                    )
                    df_long.columns = col_names

            else:
                field_name = flds if isinstance(flds, str) else str(flds)
                ticker_name = tickers if isinstance(tickers, str) else str(tickers)

                df_long = df.reset_index()
                value_col = df_long.columns[-1]
                df_long = df_long.rename(
                    columns={df_long.columns[0]:'date', value_col: 'value'}
                )
                df_long['ticker'] = ticker_name
                df_long['field'] = field_name
                df_long = df_long[['date', 'ticker', 'field', 'value']]

            df_long['overrides'] = overrides_str
            frames.append(df_long)

        except Exception as e:
            error_list.append({
                'request_index': i,
                'ticker': tickers,
                'flds': flds,
                'error': str(e)
            })

    if frames:
        result = pd.concat(frames, ignore_index=True)
    else:
        result = pd.DataFrame(columns=['date', 'ticker', 'field', 'value', 'overrides'])

    if errors:
        error_df = pd.DataFrame(error_list)
        return result, error_df

    return result


def bdh_many_data_frame(dataframe: pd.DataFrame = None, save_dict: dict = None) -> pd.DataFrame:

    if dataframe is None:
        raise ValueError("Tienes que pasar un data frame")
    
    columns_df = dataframe.columns
    not_col = []
    for col in ["ticker", "field", "override"]:
        if col not in columns_df:
            not_col.apped(col)
    
    if len(not_col) > 0:
        raise TypeError(f"El dataframe debe tener las columas: {not_col}")
    
    # Una vez validad la información hay que construir la data
    # TODO: Agregar la transformación del data frame en un formato legible para poder jalar la data
    dataframe_con_data = pd.DataFrame

    def _save(
            dataframe: pd.DataFrame,
            save: bool = False,
            formato: str = "csv",
            dir: str = None,
            nombre: str = None
    ):
        if not save:
            return None
        
        if formato == "csv":
            dataframe.to_csv(f"{dir}{nombre}.csv")
        elif formato == "parquet":
            dataframe.to_parquet(f"{dir}{nombre}.parquet")
        elif formato == "excel":
            dataframe.to_excel(f"{dir}{nombre}.xlsx")
        else:
            raise NotImplementedError(f"No esta implementado el formato {formato}")
    
    if save_dict is not None:
        _save(dataframe, **save_dict)    

    return dataframe, "dataframe_con_data" 