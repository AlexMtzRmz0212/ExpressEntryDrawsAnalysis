import pandas as pd

def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    df["drawDate"] = pd.to_datetime(df["drawDate"], errors="coerce")
    df["drawSize"] = pd.to_numeric(df["drawSize"], errors="coerce")
    df["drawCRS"] = pd.to_numeric(df["drawCRS"], errors="coerce")
    return df
