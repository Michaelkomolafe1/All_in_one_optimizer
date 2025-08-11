# /home/michael/Desktop/All_in_one_optimizer/core/performance_tracker.py

import json
import os
from datetime import datetime
from typing import Dict, List, Any


class PerformanceTracker:
    """Track lineup performance for ML training"""

    def __init__(self, data_dir="performance_data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.results_file = os.path.join(data_dir, "lineup_results.json")

    def track_lineup(self, lineup_data: Dict[str, Any]):
        """Track a generated lineup"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "lineup": lineup_data,
            "status": "generated",
            "actual_score": None,
            "contest_result": None,
            "contest_info": {}
        }

        results = self._load_results()
        results.append(entry)
        self._save_results(results)

        return entry["timestamp"]

    def _load_results(self) -> List[Dict]:
        if os.path.exists(self.results_file):
            with open(self.results_file, 'r') as f:
                return json.load(f)
        return []

    def _save_results(self, results: List[Dict]):
        with open(self.results_file, 'w') as f:
            json.dump(results, f, indent=2)