#!/usr/bin/env python3
"""
LOG ANALYZER FOR DFS OPTIMIZER
==============================
Analyzes logs to show insights about optimizations
"""

import os
import re
from collections import defaultdict
from datetime import datetime


class LogAnalyzer:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        self.boost_reasons = defaultdict(int)
        self.player_boosts = defaultdict(list)
        self.optimization_times = []
        self.api_calls = defaultdict(int)

    def analyze_latest_logs(self):
        """Analyze the most recent log files"""
        print("📊 DFS OPTIMIZER LOG ANALYSIS")
        print("=" * 50)

        # Find latest log files
        log_files = self.find_latest_logs()

        for log_type, log_file in log_files.items():
            print(f"\nAnalyzing {log_type}...")
            self.analyze_log_file(log_file, log_type)

        # Show insights
        self.show_insights()

    def find_latest_logs(self):
        """Find the most recent log files"""
        logs = {}

        if not os.path.exists(self.log_dir):
            print(f"❌ Log directory '{self.log_dir}' not found!")
            return logs

        # Get today's date
        today = datetime.now().strftime("%Y%m%d")

        log_types = {
            'general': f'dfs_optimizer_{today}.log',
            'optimization': f'optimization_decisions_{today}.log',
            'scoring': f'player_scoring_{today}.log',
            'performance': f'performance_metrics_{today}.log'
        }

        for log_type, filename in log_types.items():
            filepath = os.path.join(self.log_dir, filename)
            if os.path.exists(filepath):
                logs[log_type] = filepath

        return logs

    def analyze_log_file(self, filepath, log_type):
        """Analyze a specific log file"""
        with open(filepath, 'r') as f:
            for line in f:
                if 'SCORE BOOST:' in line:
                    self.parse_boost(line)
                elif 'BOOST REASON:' in line:
                    self.parse_boost_reason(line)
                elif 'LINEUP SELECTED:' in line:
                    self.parse_lineup(line)
                elif 'PERFORMANCE:' in line:
                    self.parse_performance(line)

    def parse_boost(self, line):
        """Parse score boost information"""
        match = re.search(r'SCORE BOOST: (.*?) - Base: ([\d.]+) → Enhanced: ([\d.]+) \(\+([\d.]+)%\)', line)
        if match:
            player = match.group(1)
            base = float(match.group(2))
            enhanced = float(match.group(3))
            boost_pct = float(match.group(4))
            self.player_boosts[player].append((base, enhanced, boost_pct))

    def parse_boost_reason(self, line):
        """Parse boost reason"""
        match = re.search(r'BOOST REASON: (\w+) = ([\d.]+)x', line)
        if match:
            reason = match.group(1)
            multiplier = float(match.group(2))
            self.boost_reasons[reason] += 1

    def parse_lineup(self, line):
        """Parse lineup information"""
        match = re.search(r'Total score = ([\d.]+), Total salary = (\d+)', line)
        if match:
            score = float(match.group(1))
            salary = int(match.group(2))
            print(f"  Lineup: {score:.1f} pts, ${salary}")

    def parse_performance(self, line):
        """Parse performance metrics"""
        if 'Data enrichment completed in' in line:
            match = re.search(r'completed in (\d+)s', line)
            if match:
                self.optimization_times.append(int(match.group(1)))
        elif 'API calls' in line:
            if 'Statcast' in line:
                match = re.search(r'Statcast: (\d+)', line)
                if match:
                    self.api_calls['statcast'] += int(match.group(1))

    def show_insights(self):
        """Show analysis insights"""
        print("\n📈 INSIGHTS")
        print("=" * 50)

        # Top boosted players
        if self.player_boosts:
            print("\n🌟 Top Boosted Players:")
            sorted_players = sorted(
                [(p, max(boosts, key=lambda x: x[2])) for p, boosts in self.player_boosts.items()],
                key=lambda x: x[1][2],
                reverse=True
            )[:10]

            for player, (base, enhanced, boost_pct) in sorted_players:
                print(f"  {player}: {base:.1f} → {enhanced:.1f} (+{boost_pct:.0f}%)")

        # Boost reasons
        if self.boost_reasons:
            print("\n📊 Most Common Boost Reasons:")
            for reason, count in sorted(self.boost_reasons.items(), key=lambda x: x[1], reverse=True):
                print(f"  {reason}: {count} times")

        # Performance
        if self.optimization_times:
            avg_time = sum(self.optimization_times) / len(self.optimization_times)
            print(f"\n⚡ Average optimization time: {avg_time:.1f}s")

        if self.api_calls:
            print("\n🌐 API Calls:")
            for api, count in self.api_calls.items():
                print(f"  {api}: {count} calls")


if __name__ == "__main__":
    analyzer = LogAnalyzer()
    analyzer.analyze_latest_logs()
