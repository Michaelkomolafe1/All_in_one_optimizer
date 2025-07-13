"""
Performance Tracker for DFS
Track results, analyze accuracy, improve over time
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional


class PerformanceTracker:
    """Track and analyze DFS performance"""

    def __init__(self, db_path: str = 'dfs_performance.db'):
        self.db_path = db_path
        self.conn = None
        self._init_database()

    def _init_database(self):
        """Initialize database connection and tables"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self._create_tables()
        except Exception as e:
            print(f"Database init error: {e}")
            self.conn = None

    def _create_tables(self):
        """Create necessary tables"""
        if not self.conn:
            return

        try:
            # Contest results table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS contest_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    contest_id TEXT,
                    contest_type TEXT,
                    entry_fee REAL,
                    total_entries INTEGER,
                    finish_position INTEGER,
                    prize_won REAL,
                    projected_score REAL,
                    actual_score REAL,
                    strategy TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Lineup players table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS lineup_players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contest_id INTEGER,
                    player_name TEXT,
                    position TEXT,
                    team TEXT,
                    salary INTEGER,
                    projected_points REAL,
                    actual_points REAL,
                    ownership REAL,
                    FOREIGN KEY (contest_id) REFERENCES contest_results(id)
                )
            """)

            # Player accuracy table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS player_accuracy (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    player_name TEXT,
                    projected REAL,
                    actual REAL,
                    difference REAL,
                    percentage_error REAL
                )
            """)

            self.conn.commit()

        except Exception as e:
            print(f"Table creation error: {e}")

    def log_contest(self, lineup: List, contest_info: Dict, 
                   result_info: Optional[Dict] = None) -> Optional[int]:
        """Log a contest entry and optionally its results"""
        if not self.conn:
            return None

        try:
            # Calculate projected score
            projected_score = sum(getattr(p, 'enhanced_score', p.base_score) 
                                for p in lineup)

            # Insert contest
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO contest_results 
                (date, contest_id, contest_type, entry_fee, strategy, 
                 projected_score, actual_score, finish_position, 
                 total_entries, prize_won)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                contest_info.get('date', datetime.now().strftime('%Y-%m-%d')),
                contest_info.get('id', ''),
                contest_info.get('type', 'gpp'),
                contest_info.get('entry_fee', 0),
                contest_info.get('strategy', 'balanced'),
                projected_score,
                result_info.get('actual_score') if result_info else None,
                result_info.get('position') if result_info else None,
                result_info.get('entries') if result_info else None,
                result_info.get('prize', 0) if result_info else 0
            ))

            contest_id = cursor.lastrowid

            # Insert players
            for player in lineup:
                cursor.execute("""
                    INSERT INTO lineup_players
                    (contest_id, player_name, position, team, salary,
                     projected_points, ownership)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    contest_id,
                    player.name,
                    player.primary_position,
                    player.team,
                    player.salary,
                    getattr(player, 'enhanced_score', player.base_score),
                    getattr(player, 'ownership', 0)
                ))

            self.conn.commit()
            print(f"📊 Logged contest #{contest_id}")
            return contest_id

        except Exception as e:
            print(f"Contest logging error: {e}")
            self.conn.rollback()
            return None

    def update_contest_results(self, contest_id: int, results: Dict) -> bool:
        """Update contest with actual results"""
        if not self.conn:
            return False

        try:
            self.conn.execute("""
                UPDATE contest_results
                SET actual_score = ?, finish_position = ?, 
                    total_entries = ?, prize_won = ?
                WHERE id = ?
            """, (
                results.get('actual_score'),
                results.get('position'),
                results.get('entries'),
                results.get('prize', 0),
                contest_id
            ))

            self.conn.commit()
            return True

        except Exception as e:
            print(f"Update error: {e}")
            return False

    def get_roi_summary(self, days: int = 30) -> Dict:
        """Calculate ROI over specified period"""
        if not self.conn:
            return {}

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as contests,
                    SUM(entry_fee) as total_invested,
                    SUM(prize_won) as total_won,
                    AVG(actual_score) as avg_score,
                    SUM(CASE WHEN prize_won > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as cash_rate
                FROM contest_results
                WHERE date >= date('now', '-{} days')
                AND actual_score IS NOT NULL
            """.format(days))

            row = cursor.fetchone()
            if row and row['total_invested'] and row['total_invested'] > 0:
                roi = ((row['total_won'] - row['total_invested']) / 
                       row['total_invested'] * 100)
            else:
                roi = 0

            return {
                'contests': row['contests'] if row else 0,
                'invested': row['total_invested'] if row else 0,
                'won': row['total_won'] if row else 0,
                'roi': roi,
                'cash_rate': row['cash_rate'] if row else 0,
                'avg_score': row['avg_score'] if row else 0
            }

        except Exception as e:
            print(f"ROI calculation error: {e}")
            return {}

    def analyze_projections(self) -> Dict:
        """Analyze projection accuracy"""
        if not self.conn:
            return {}

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    AVG(ABS(projected_score - actual_score)) as avg_error,
                    AVG((actual_score - projected_score) / projected_score * 100) as avg_pct_error,
                    COUNT(*) as sample_size
                FROM contest_results
                WHERE actual_score IS NOT NULL
                AND projected_score > 0
            """)

            row = cursor.fetchone()
            return dict(row) if row else {}

        except Exception as e:
            print(f"Projection analysis error: {e}")
            return {}

    def get_best_lineups(self, limit: int = 10) -> List[Dict]:
        """Get top performing lineups"""
        if not self.conn:
            return []

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM contest_results
                WHERE actual_score IS NOT NULL
                ORDER BY actual_score DESC
                LIMIT ?
            """, (limit,))

            return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            print(f"Best lineups error: {e}")
            return []

    def print_summary(self, days: int = 30):
        """Print performance summary"""
        print(f"\n📊 PERFORMANCE SUMMARY (Last {days} days)")
        print("=" * 50)

        # ROI Summary
        roi_data = self.get_roi_summary(days)
        if roi_data:
            print(f"Contests: {roi_data['contests']}")
            print(f"Invested: ${roi_data['invested']:.2f}")
            print(f"Won: ${roi_data['won']:.2f}")
            print(f"ROI: {roi_data['roi']:.1f}%")
            print(f"Cash Rate: {roi_data['cash_rate']:.1f}%")
            print(f"Avg Score: {roi_data['avg_score']:.2f}")

        # Projection Accuracy
        proj_data = self.analyze_projections()
        if proj_data and proj_data.get('sample_size', 0) > 0:
            print(f"\nProjection Accuracy:")
            print(f"  Average Error: {proj_data['avg_error']:.2f} points")
            print(f"  Average % Error: {proj_data['avg_pct_error']:.1f}%")
            print(f"  Sample Size: {proj_data['sample_size']} contests")

# Create global instance
tracker = PerformanceTracker()
