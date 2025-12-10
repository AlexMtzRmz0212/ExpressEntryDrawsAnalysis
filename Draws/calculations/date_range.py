def get_date_range(df):
    try:
        earliest = df["drawDate"].min().date().isoformat()
        latest = df["drawDate"].max().date().isoformat()
        return earliest, latest
    except:
        return "N/A", "N/A"
