from .cv import calculate_cv

def calculate_basic_stats(df, column):
    if df[column].isnull().all():
        return {
            "highest": "N/A",
            "average": "N/A",
            "lowest": "N/A",
            "coefficient_of_variation": "N/A",
        }

    return {
        "highest": int(df[column].max()),
        "average": round(df[column].mean(), 2),
        "lowest": int(df[column].min()),
        "coefficient_of_variation": calculate_cv(df[column]),
    }
