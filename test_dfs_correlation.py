"""
test_dfs_correlation.py
DFS Correlation-Aware System Testing Framework
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
import random
from scipy.stats import norm, truncnorm
from collections import defaultdict
import warnings
warnings.filterwarnings("ignore")

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

# -------------
# CONSTANTS
# -------------
SALARY_CAP = 50_000
ROSTER_SLOTS = {"P": 2, "C": 1, "1B": 1, "2B": 1, "3B": 1, "SS": 1, "OF": 3}
POSITIONS = list(ROSTER_SLOTS.keys())

# Contest structure
FIELD_SIZE = 1_000
ENTRY_FEE = 10
GPP_PAYOUT = {
    1:   0.20 * ENTRY_FEE * FIELD_SIZE,
    2:   0.12 * ENTRY_FEE * FIELD_SIZE,
    3:   0.08 * ENTRY_FEE * FIELD_SIZE,
    4:   0.06 * ENTRY_FEE * FIELD_SIZE,
    5:   0.05 * ENTRY_FEE * FIELD_SIZE,
    6:   0.04 * ENTRY_FEE * FIELD_SIZE,
    7:   0.035 * ENTRY_FEE * FIELD_SIZE,
    8:   0.03 * ENTRY_FEE * FIELD_SIZE,
    9:   0.025 * ENTRY_FEE * FIELD_SIZE,
    10:  0.02 * ENTRY_FEE * FIELD_SIZE,
}
# Top 20 % cash; linear tail for demo
for rank in range(11, int(0.20 * FIELD_SIZE) + 1):
    GPP_PAYOUT[rank] = 2.5 * ENTRY_FEE
CASH_PAYOUT = {r: 1.8 * ENTRY_FEE for r in range(1, int(0.45 * FIELD_SIZE) + 1)}

# -------------
# PLAYER MODEL
# -------------
@dataclass
class Player:
    name: str
    position: str
    team: str
    salary: int
    projection: float
    batting_order: int  # 0 for pitchers
    team_total: float   # Vegas implied
    park_factor: float = 1.0
    ownership: float = 0.0
    actual: float = 0.0  # post-simulation

# -------------
# SLATE GENERATOR
# -------------
TEAMS = ["LAD", "NYY", "HOU", "ATL", "NYM", "BOS", "STL", "PHI",
         "TOR", "SD", "CHC", "SF", "LAA", "TBR", "MIL", "CLE"]
PARK_FACTORS = {t: np.random.uniform(0.9, 1.1) for t in TEAMS}

def generate_slate(n_players: int = 180) -> List[Player]:
    players = []
    # Pitchers
    for i in range(30):
        team = random.choice(TEAMS)
        players.append(Player(
            name=f"P{i+1}",
            position="P",
            team=team,
            salary=int(np.random.triangular(5_000, 7_500, 11_000)),
            projection=np.random.uniform(10, 22),
            batting_order=0,
            team_total=np.random.uniform(3.5, 5.5),
            park_factor=PARK_FACTORS[team]
        ))
    # Hitters
    positions_needed = {
        "C": 12, "1B": 12, "2B": 12, "3B": 12, "SS": 12, "OF": 36 * 3  # 3 OF spots
    }
    for pos, qty in positions_needed.items():
        for i in range(qty):
            team = random.choice(TEAMS)
            bo = np.random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9], p=[.22, .20, .18, .15, .12, .07, .04, .02, .00])
            proj = np.random.triangular(1.5, 6, 14)
            players.append(Player(
                name=f"{pos}{i+1}",
                position=pos,
                team=team,
                salary=int(proj * 500 + np.random.normal(0, 800)),
                projection=proj,
                batting_order=bo,
                team_total=np.random.uniform(3.8, 6.2),
                park_factor=PARK_FACTORS[team]
            ))
    random.shuffle(players)
    return players[:n_players]

# -------------
# SCORING ENGINE
# -------------
class CorrelationScorer:
    def __init__(self, mode: str = "gpp"):
        if mode == "gpp":
            self.team_boost = 1.15
            self.batting_boost = 1.10
            self.threshold = 5.0
        else:  # cash
            self.team_boost = 1.08
            self.batting_boost = 1.05
            self.threshold = 5.0

    def score(self, p: Player) -> float:
        s = p.projection
        if p.team_total >= self.threshold:
            s *= self.team_boost
        if p.position != "P" and p.batting_order <= 4:
            s *= self.batting_boost
        s *= p.park_factor
        return s

# -------------
# OUTCOME SIMULATOR
# -------------
def simulate_outcomes(players: List[Player]):
    # Step 1: Team multipliers (correlated)
    team_mult = {}
    for t in TEAMS:
        r = random.random()
        if r < 0.10:      # 10 % blow-up
            tm = np.random.uniform(1.3, 1.5)
        elif r < 0.25:    # 15 % above-avg
            tm = np.random.uniform(1.1, 1.3)
        elif r < 0.80:    # 55 % normal
            tm = np.random.uniform(0.85, 1.15)
        else:             # 10 % bust
            tm = np.random.uniform(0.5, 0.85)
        team_mult[t] = tm

    # Step 2: Individual with correlation
    for p in players:
        # Individual noise
        ind = truncnorm.rvs(-2, 2, loc=1, scale=0.3)
        # Team effect
        te = team_mult[p.team]
        # Correlation factor
        if p.position == "P":
            corr = 0.2
            # pitchers slightly hurt by team blow-up
            te = 1.0 / te if te > 1 else te
        else:
            corr = 0.65
            if p.batting_order <= 4:
                corr *= 1.1
        # Weighted average
        final = ind * (1 - corr) + te * corr
        p.actual = p.projection * final
    return players

# -------------
# LINEUP BUILDER
# -------------
def build_lineup(players: List[Player], scorer) -> List[Player]:
    # scorer can be CorrelationScorer OR a callable
    if hasattr(scorer, "score"):
        scored = [(p, scorer.score(p)) for p in players]
    else:
        scored = [(p, scorer(p)) for p in players]

    scored.sort(key=lambda x: x[1] / max(x[0].salary, 1), reverse=True)

    best_lineup = []
    best_score = 0
    for _ in range(2_000):
        lineup = []
        pos_counts = defaultdict(int)
        teams = defaultdict(int)
        salary = 0
        random.shuffle(scored)
        for p, _ in scored:
            if pos_counts[p.position] < ROSTER_SLOTS[p.position] and \
               salary + p.salary <= SALARY_CAP and \
               teams[p.team] < (5 if p.position != "P" else 30):
                lineup.append(p)
                pos_counts[p.position] += 1
                teams[p.team] += 1
                salary += p.salary
                if len(lineup) == 10:
                    break
        if len(lineup) == 10:
            score = sum(p.actual for p in lineup)
            if score > best_score:
                best_score = score
                best_lineup = lineup.copy()
    return best_lineup



# -------------
# CONTEST SIMULATOR
# -------------
def run_contest(players: List[Player], scorer: CorrelationScorer, contest_type: str = "gpp") -> Dict:
    players = simulate_outcomes(players)  # one slate outcome
    # Build our lineup
    our_lineup = build_lineup(players, scorer)
    our_score = sum(p.actual for p in our_lineup)

    # Build field
    field_scores = []
    for _ in range(FIELD_SIZE - 1):
        # 30 % projections, 20 % value, 15 % ownership, 10 % correlation, 25 % random
        strat = random.random()
        if strat < 0.30:
            s = CorrelationScorer("gpp")  # pure projections
        elif strat < 0.50:
            # value hunting (cheap players)
            s = lambda p: p.projection / max(p.salary, 1)
        elif strat < 0.65:
            # ownership chasing (high ownership)
            s = lambda p: p.ownership + 1e-6
        elif strat < 0.75:
            s = CorrelationScorer("gpp")
        else:
            s = lambda p: random.random()  # random
        l = build_lineup(players, s)
        field_scores.append(sum(p.actual for p in l))

    field_scores.append(our_score)
    field_scores_sorted = sorted(field_scores, reverse=True)
    our_rank = field_scores_sorted.index(our_score) + 1

    # Payout
    payouts = GPP_PAYOUT if contest_type == "gpp" else CASH_PAYOUT
    prize = payouts.get(our_rank, 0)

    return {
        "score": our_score,
        "rank": our_rank,
        "prize": prize,
        "roi": (prize - ENTRY_FEE) / ENTRY_FEE
    }

# -------------
# MAIN TEST LOOP
# -------------
def main():
    print("=== DFS Correlation-Aware Test ===")
    players = generate_slate(180)
    print(f"Slate: {len(players)} players, {len(set(p.team for p in players))} teams")

    # QUICK SMOKE TEST: 50 contests each, 500 iterations per lineup
    for mode in ["gpp", "cash"]:
        print(f"\nStarting {mode.upper()} test…")
        scorer = CorrelationScorer(mode)
        results = []
        for i in range(50):                       # only 50 contests
            res = run_contest(players, scorer, mode)
            results.append(res)
            if (i + 1) % 10 == 0:
                print(f"  {i+1} / 50")
        df = pd.DataFrame(results)
        roi = df["roi"].mean()
        cash_rate = (df["prize"] > 0).mean()
        print(f"{mode.upper()} done → ROI {roi*100:+.2f}%  Cash% {cash_rate*100:.1f}%")

if __name__ == "__main__":
    main()