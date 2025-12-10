from .basic_stats import calculate_basic_stats

def calculate_score_stats(df):
    return calculate_basic_stats(df, "drawCRS")
