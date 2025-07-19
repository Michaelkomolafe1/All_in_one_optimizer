#!/usr/bin/env python3
"""
COMPLETE CLEAN INTEGRATION – NO LEGACY DEPENDENCIES
===================================================
- Loads DraftKings CSV via UnifiedPlayer
- Supplies every method the GUI expects
- Uses your unified scoring / optimizer stack
"""

import csv
from typing import List, Dict, Any

from unified_player_model import UnifiedPlayer
from unified_scoring_engine import get_scoring_engine
from unified_milp_optimizer import create_unified_optimizer
from unified_milp_optimizer import OptimizationConfig   # ← ADD THIS


class BulletproofDFSCore:
    """Minimal stub – only holds players and mode."""
    def __init__(self):
        self.players: List[UnifiedPlayer] = []
        self.optimization_mode = "all"


class SimplifiedDFSCore(BulletproofDFSCore):
    def __init__(self):
        super().__init__()
        self.scoring_engine = get_scoring_engine()

        # 👇 corrected spelling
        config = OptimizationConfig(
            position_requirements={"P": 2, "C": 1, "1B": 1, "2B": 1, "3B": 1, "SS": 1, "OF": 3}
        )
        self.unified_optimizer = create_unified_optimizer(config)

    # -------------------------------------------------
    # CSV loading (GUI entry point)
    # -------------------------------------------------
    def load_draftkings_csv(self, filepath: str) -> int:
        """Read DK CSV → UnifiedPlayer list → return count."""
        self.players.clear()
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Map DK columns → UnifiedPlayer
                player = UnifiedPlayer(
                    id=row["ID"],
                    name=row["Name"],
                    team=row["TeamAbbrev"],
                    salary=int(row["Salary"]),
                    primary_position=row["Position"].split("/")[0],
                    positions=row["Position"].split("/"),
                    base_projection=float(row.get("AvgPointsPerGame", 0)),
                )
                self.players.append(player)
        return len(self.players)

    # -------------------------------------------------
    # GUI helpers
    # -------------------------------------------------
    def get_eligible_players_by_mode(self) -> List[UnifiedPlayer]:
        mode = self.optimization_mode
        return [
            p for p in self.players
            if p.is_eligible_for_selection(mode) and p.enhanced_score > 0
        ]

    def get_system_status(self) -> Dict[str, Any]:
        return {
            "core_initialized": True,
            "unified_mode": True,
            "total_players": len(self.players),
            "optimization_ready": len(self.players) > 0,
            "modules": {"scoring_engine": True, "optimizer": True, "data_system": True},
            "csv_file": None,
        }

    # -------------------------------------------------
    # Optimizers
    # -------------------------------------------------
    def optimize_lineup(self, strategy="balanced", manual_selections=None):
        """Classic lineup via unified MILP."""
        players = self.get_eligible_players_by_mode()
        if not players:
            return []

        # score every player
        for p in players:
            self.scoring_engine.calculate_score(p)

        result = self.unified_optimizer.optimize(
            players=players,
            strategy=strategy,
            manual_selections=manual_selections or ""
        )
        return {"lineup": result.lineup, "total_score": result.projected_points} if result else {"lineup": [], "total_score": 0}

    def optimize_showdown_lineup(self):
        """Showdown lineup via unified showdown optimizer."""
        players = self.get_eligible_players_by_mode()
        for p in players:
            self.scoring_engine.calculate_score(p)

        result = self.unified_optimizer.optimize(players, contest_type="showdown")
        if not result:
            return [], 0
        return result.lineup, result.projected_points

    # -------------------------------------------------
    # Convenience (optional)
    # -------------------------------------------------
    def detect_confirmed_players(self) -> int:
        return sum(1 for p in self.players if p.is_confirmed)

    def apply_manual_selection(self, names_csv: str):
        names = {n.strip() for n in str(names_csv).split(",") if n.strip()}
        for p in self.players:
            p.is_manual_selected = p.name in names