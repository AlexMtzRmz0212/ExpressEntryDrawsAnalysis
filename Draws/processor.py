from config import Config
from typing import List, Dict

import pandas as pd



class Processor:
    def __init__(self, config: Config):
        self.config = config

    def process_draw_data(self, rounds: List[Dict]) -> pd.DataFrame:
        df = pd.DataFrame(rounds)

        selected_columns = [
            col for col in self.config.SELECTED_COLUMNS
            if col in df.columns
        ]

        return df[selected_columns].sort_values('drawDate', ascending=False).reset_index(drop=True)
    
    def pars