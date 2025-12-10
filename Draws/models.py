"""Data models for Express Entry draws."""
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Draw:
    """Represents an Express Entry draw."""
    draw_number: int
    draw_date: str
    draw_date_time: str
    draw_name: str
    draw_size: int
    draw_crs: int
    raw_data: Dict[str, Any]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Draw':
        """Create Draw instance from dictionary."""
        return cls(
            draw_number=data.get("drawNumber"),
            draw_date=data.get("drawDate"),
            draw_date_time=data.get("drawDateTime"),
            draw_name=data.get("drawName"),
            draw_size=data.get("drawSize"),
            draw_crs=data.get("drawCRS"),
            raw_data=data
        )

@dataclass
class AnalysisResult:
    """Represents analysis results."""
    total_draws: int
    date_range: tuple
    size_stats: Dict[str, Any]
    score_stats: Dict[str, Any]
    time_analysis: Dict[str, Any]