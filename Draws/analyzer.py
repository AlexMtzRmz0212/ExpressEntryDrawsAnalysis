from config     import Config
from processor  import Processor
from models     import AnalysisResult

from calculations.clean         import clean_df
from calculations.date_range    import get_date_range
from calculations.size_stats    import calculate_size_stats
from calculations.score_stats   import calculate_score_stats
from calculations.time_analysis import analyze_draw_times

from typing import Dict, Any, Optional
import pandas as pd
import logging
import json

logger = logging.getLogger(__name__)


class Analyzer:
    """Analyzes EE Draws data."""

    def __init__(self, config: Config, processor: Processor):
        self.config = config
        self.processor = processor

    def analyze(self, data: Dict[str, Any]) -> Optional[AnalysisResult]:
        try:
            df = pd.DataFrame(data["rounds"])
            df = clean_df(df)

            stats = {
                "total_draws": len(df),
                "date_range": get_date_range(df),
                "size_stats": calculate_size_stats(df),
                "score_stats": calculate_score_stats(df),
            }

            time_analysis = analyze_draw_times(data)

            analysis = AnalysisResult(
                total_draws=stats["total_draws"],
                date_range=stats["date_range"],
                size_stats=stats["size_stats"],
                score_stats=stats["score_stats"],
                time_analysis=time_analysis,
            )

            self._save_analysis(analysis, data)
            return analysis

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return None

    def _save_analysis(self, analysis: AnalysisResult, raw_data: Dict[str, Any]):
        analysis_dict = {
            "updated": {"last": raw_data.get("metadata", {}).get("updated_at", "N/A")},
            "draws": {"total": analysis.total_draws},
            "draw_date": {
                "earliest": analysis.date_range[0],
                "latest": analysis.date_range[1],
            },
            "size": analysis.size_stats,
            "score": analysis.score_stats,
        }

        with open(self.config.ANALYSIS_PATH, "w") as f:
            json.dump(analysis_dict, f, indent=2)
