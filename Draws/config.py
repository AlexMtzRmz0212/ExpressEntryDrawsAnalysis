from pathlib import Path


class Config:
    API_URL = "https://www.canada.ca/content/dam/ircc/documents/json/ee_rounds_123_en.json"
    REQUEST_TIMEOUT = 10  # seconds

    DATA_PATH = Path("../Data")
    EE_PATH = DATA_PATH / "EE.json"
    ANALYSIS_PATH = DATA_PATH / "analysis.json"
    TIME_ANALYSIS_PATH = DATA_PATH / "time_analysis.json"

    SELECTED_COLUMNS = [
        "drawNumber", "drawDate", "drawDateTime", "drawName",
        "drawSize", "drawCRS", "drawText2", "drawCutOff",
        "drawDistributionAsOn"
    ] + [f"dd{i}" for i in range(1, 19)]

    def clear_screen(self):
        print("\033c", end="")
