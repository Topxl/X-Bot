"""Stats Manager pour le bot Twitter"""

from typing import Optional
from datetime import datetime
from loguru import logger

class StatsCollector:
    def __init__(self):
        pass
    
    def generate_daily_report(self, date: Optional[datetime] = None):
        """Génère un rapport quotidien basique"""
        logger.info("Daily report generation (simplified)")
        return True

_stats_collector: Optional[StatsCollector] = None

def get_stats_collector() -> StatsCollector:
    global _stats_collector
    if _stats_collector is None:
        _stats_collector = StatsCollector()
    return _stats_collector 