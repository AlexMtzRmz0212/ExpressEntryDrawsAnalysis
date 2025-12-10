import pandas as pd

def calculate_cv(series: pd.Series):
    if series.isnull().all() or series.mean() == 0:
        return "N/A"
    return round(series.std() / series.mean() * 100, 2)
