from .basic_stats import calculate_basic_stats

def calculate_size_stats(df):
    return calculate_basic_stats(df, "drawSize")
