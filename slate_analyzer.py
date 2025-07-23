#!/usr/bin/env python3
"""
DFS SLATE ANALYZER
==================
Analyzes slates to identify the best opportunities
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import json


class SlateAnalyzer:
    def __init__(self):
        self.scoring_weights = {
            'game_total': 0.20,  # High scoring games
            'player_pool_size': 0.15,  # Larger slates = more variance
            'weather': 0.15,  # Good weather for hitting
            'ace_pitchers': 0.15,  # Chalk that can fail
            'value_plays': 0.15,  # Number of good values
            'injury_news': 0.10,  # Late news opportunities
            'ownership_predictability': 0.10  # Can we predict chalk?
        }

    def analyze_slate(self, csv_file, date=None):
        """Analyze a slate for DFS opportunities"""

        print(f"\n🎯 ANALYZING SLATE: {csv_file}")
        print("=" * 60)

        # Load data
        df = pd.read_csv(csv_file)

        # Basic slate info
        slate_info = self.get_slate_info(df)
        print(f"\n📊 SLATE OVERVIEW:")
        print(f"  Players: {slate_info['total_players']}")
        print(f"  Games: {slate_info['num_games']}")
        print(f"  Average Salary: ${slate_info['avg_salary']:,.0f}")

        # Run analyses
        scores = {}

        # 1. Game Environment Score
        scores['game_environment'] = self.analyze_game_environment(df)

        # 2. Player Pool Analysis
        scores['player_pool'] = self.analyze_player_pool(df)

        # 3. Value Opportunities
        scores['value_plays'] = self.analyze_value_plays(df)

        # 4. Pitcher Analysis
        scores['pitching'] = self.analyze_pitchers(df)

        # 5. Stack Potential
        scores['stacking'] = self.analyze_stacking_potential(df)

        # 6. Contest Selection
        scores['contest_type'] = self.recommend_contest_type(df, scores)

        # Overall score
        overall_score = np.mean(list(scores.values()))

        # Display results
        self.display_analysis(scores, overall_score)

        return {
            'slate_info': slate_info,
            'scores': scores,
            'overall_score': overall_score,
            'recommendations': self.get_recommendations(scores, overall_score)
        }

    def get_slate_info(self, df):
        """Get basic slate information"""
        info = {
            'total_players': len(df),
            'num_games': df['Game'].nunique() if 'Game' in df.columns else len(df['TeamAbbrev'].unique()) // 2,
            'avg_salary': df['Salary'].mean() if 'Salary' in df.columns else 0,
            'positions': df['Position'].value_counts().to_dict() if 'Position' in df.columns else {}
        }

        # Check slate size
        if info['total_players'] < 100:
            info['slate_type'] = 'Small (Showdown/Single Game)'
        elif info['total_players'] < 200:
            info['slate_type'] = 'Medium (Afternoon/Turbo)'
        else:
            info['slate_type'] = 'Large (Main Slate)'

        return info

    def analyze_game_environment(self, df):
        """Analyze game environment factors"""
        score = 70  # Base score
        factors = []

        # Check for game totals (if available)
        if 'Game' in df.columns:
            games = df['Game'].unique()
            high_total_games = 0

            for game in games:
                # Look for games with high implied totals
                # This is simplified - in reality you'd check Vegas totals
                if any(team in game for team in ['COL', 'TEX', 'CIN']):  # Hitter-friendly parks
                    high_total_games += 1
                    factors.append(f"Hitter-friendly park: {game}")

            if high_total_games > 0:
                score += (high_total_games * 5)
                score = min(score, 95)

        # Weather considerations (simplified)
        outdoor_teams = ['COL', 'TEX', 'MIN', 'CIN', 'CHC', 'CWS', 'KC', 'DET']
        outdoor_games = sum(1 for team in df['TeamAbbrev'].unique() if team in outdoor_teams)

        if outdoor_games > 4:
            factors.append(f"{outdoor_games} outdoor games (weather variance)")
            score += 5

        if factors:
            print(f"\n🌤️ GAME ENVIRONMENT (Score: {score}/100):")
            for factor in factors:
                print(f"  • {factor}")

        return score

    def analyze_player_pool(self, df):
        """Analyze player pool characteristics"""
        score = 70
        factors = []

        total_players = len(df)

        # Larger slates offer more variance
        if total_players > 300:
            score += 10
            factors.append("Large player pool (high variance)")
        elif total_players < 150:
            score -= 10
            factors.append("Small player pool (easier to solve)")

        # Check salary distribution
        if 'Salary' in df.columns:
            salary_std = df['Salary'].std()
            if salary_std > 2000:
                score += 5
                factors.append("Wide salary range (more roster construction options)")

            # Check for value plays
            cheap_players = len(df[df['Salary'] < 4000])
            if cheap_players > 20:
                score += 10
                factors.append(f"{cheap_players} punt plays available")

        # Position distribution
        if 'Position' in df.columns:
            pos_counts = df['Position'].value_counts()

            # Check for position scarcity
            for pos in ['C', '2B', 'SS']:
                if pos in pos_counts and pos_counts[pos] < 15:
                    factors.append(f"{pos} scarcity ({pos_counts[pos]} options)")
                    score += 3

        print(f"\n👥 PLAYER POOL (Score: {score}/100):")
        for factor in factors:
            print(f"  • {factor}")

        return score

    def analyze_value_plays(self, df):
        """Analyze value play opportunities"""
        score = 70
        factors = []

        if 'Salary' in df.columns and 'AvgPointsPerGame' in df.columns:
            df['Value'] = df['AvgPointsPerGame'] / df['Salary'] * 1000

            # Elite values (6x+)
            elite_values = len(df[df['Value'] >= 6.0])
            if elite_values > 5:
                score += 15
                factors.append(f"{elite_values} elite value plays (6x+)")

            # Good values (5x+)
            good_values = len(df[df['Value'] >= 5.0])
            if good_values > 15:
                score += 10
                factors.append(f"{good_values} good value plays (5x+)")

            # Min priced players with upside
            min_salary = df['Salary'].min()
            min_priced = df[df['Salary'] == min_salary]
            projected_starters = len(min_priced[min_priced['AvgPointsPerGame'] > 15])

            if projected_starters > 3:
                score += 10
                factors.append(f"{projected_starters} min-priced starters")

            # Top values by position
            print(f"\n💰 VALUE PLAYS (Score: {score}/100):")

            if 'Position' in df.columns:
                for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
                    pos_df = df[df['Position'].str.contains(pos, na=False)]
                    if len(pos_df) > 0:
                        top_value = pos_df.nlargest(1, 'Value').iloc[0]
                        if top_value['Value'] >= 5.0:
                            print(f"  • {pos}: {top_value['Name']} ({top_value['Value']:.1f}x)")

        return score

    def analyze_pitchers(self, df):
        """Analyze pitching slate"""
        score = 70
        factors = []

        if 'Position' in df.columns:
            pitchers = df[df['Position'] == 'P'].copy()

            if len(pitchers) > 0 and 'Salary' in df.columns:
                # Expensive pitchers (likely aces)
                expensive_pitchers = pitchers[pitchers['Salary'] >= 9000]

                if len(expensive_pitchers) >= 4:
                    score += 10
                    factors.append(f"{len(expensive_pitchers)} expensive pitchers (chalk will be spread)")
                elif len(expensive_pitchers) == 1:
                    score -= 10
                    factors.append("Single chalk pitcher (high ownership)")

                # Value pitchers
                value_pitchers = pitchers[(pitchers['Salary'] < 7000) &
                                          (pitchers['AvgPointsPerGame'] > 30)]

                if len(value_pitchers) > 2:
                    score += 15
                    factors.append(f"{len(value_pitchers)} value pitcher options")

                # SP2 plays
                cheap_sp2 = pitchers[pitchers['Salary'] < 5500]
                if len(cheap_sp2) > 3:
                    score += 5
                    factors.append(f"{len(cheap_sp2)} cheap SP2 options")

        print(f"\n⚾ PITCHING ANALYSIS (Score: {score}/100):")
        for factor in factors:
            print(f"  • {factor}")

        return score

    def analyze_stacking_potential(self, df):
        """Analyze team stacking opportunities"""
        score = 70
        factors = []

        if 'TeamAbbrev' in df.columns:
            team_counts = df['TeamAbbrev'].value_counts()

            # Teams with full lineups available
            full_stacks = len(team_counts[team_counts >= 8])
            if full_stacks > 10:
                score += 10
                factors.append(f"{full_stacks} teams with 8+ players")

            # High upside stacks
            if 'AvgPointsPerGame' in df.columns:
                team_projections = df.groupby('TeamAbbrev')['AvgPointsPerGame'].sum()
                high_upside_teams = len(team_projections[team_projections > 100])

                if high_upside_teams > 5:
                    score += 15
                    factors.append(f"{high_upside_teams} high-upside team stacks")

                # Show top stacks
                top_stacks = team_projections.nlargest(5)
                print(f"\n🔥 STACKING POTENTIAL (Score: {score}/100):")
                print("  Top Team Stacks:")
                for team, proj in top_stacks.items():
                    avg_salary = df[df['TeamAbbrev'] == team]['Salary'].mean()
                    print(f"    • {team}: {proj:.1f} pts (avg ${avg_salary:,.0f})")

        return score

    def recommend_contest_type(self, df, scores):
        """Recommend contest types based on slate characteristics"""
        recommendations = []

        avg_score = np.mean(list(scores.values()))

        # Cash games
        if scores.get('value_plays', 0) > 80 and scores.get('player_pool', 0) < 80:
            recommendations.append(("Cash Games", "Clear value plays, smaller slate"))

        # GPPs
        if scores.get('player_pool', 0) > 80 and scores.get('game_environment', 0) > 80:
            recommendations.append(("Large GPPs", "High variance slate with many paths"))

        # Single Entry
        if avg_score > 75 and scores.get('pitching', 0) > 70:
            recommendations.append(("Single Entry", "Balanced slate with clear plays"))

        # Showdown
        if len(df) < 100:
            recommendations.append(("Showdown/Single Game", "Small slate format"))

        return recommendations

    def display_analysis(self, scores, overall_score):
        """Display analysis results"""
        print(f"\n📈 SLATE SCORES:")
        print("=" * 40)

        for category, score in scores.items():
            if isinstance(score, (int, float)):
                bar = "█" * (score // 10) + "░" * (10 - score // 10)
                print(f"{category:<20} [{bar}] {score:.0f}/100")

        print(f"\n🎯 OVERALL SLATE SCORE: {overall_score:.0f}/100")

        # Grade
        if overall_score >= 85:
            grade = "A+ (EXCELLENT OPPORTUNITY)"
        elif overall_score >= 80:
            grade = "A (VERY GOOD)"
        elif overall_score >= 75:
            grade = "B+ (GOOD)"
        elif overall_score >= 70:
            grade = "B (ABOVE AVERAGE)"
        elif overall_score >= 65:
            grade = "C (AVERAGE)"
        else:
            grade = "D (BELOW AVERAGE)"

        print(f"GRADE: {grade}")

    def get_recommendations(self, scores, overall_score):
        """Get specific recommendations"""
        recs = []

        if overall_score >= 80:
            recs.append("✅ STRONG PLAY - This slate offers excellent opportunities")
        elif overall_score >= 70:
            recs.append("👍 PLAYABLE - Good slate with some advantages")
        else:
            recs.append("⚠️ PROCEED WITH CAUTION - Limited opportunities")

        # Specific recommendations
        if scores.get('value_plays', 0) > 85:
            recs.append("💰 Focus on CASH GAMES - Clear value plays available")

        if scores.get('player_pool', 0) > 85:
            recs.append("🎯 Play GPPs - High variance with many viable builds")

        if scores.get('pitching', 0) < 70:
            recs.append("⚾ Consider pitcher punt strategies")

        if scores.get('stacking', 0) > 80:
            recs.append("🔥 Focus on team stacks in tournaments")

        print(f"\n💡 RECOMMENDATIONS:")
        for rec in recs:
            print(f"  {rec}")

        return recs

    def compare_slates(self, csv_files):
        """Compare multiple slates"""
        results = {}

        print("\n🔍 COMPARING MULTIPLE SLATES")
        print("=" * 60)

        for csv_file in csv_files:
            if Path(csv_file).exists():
                result = self.analyze_slate(csv_file)
                results[csv_file] = result

        # Rank slates
        if results:
            print("\n📊 SLATE RANKINGS:")
            ranked = sorted(results.items(),
                            key=lambda x: x[1]['overall_score'],
                            reverse=True)

            for i, (slate, data) in enumerate(ranked, 1):
                print(f"\n{i}. {Path(slate).name}")
                print(f"   Score: {data['overall_score']:.0f}/100")
                print(f"   Type: {data['slate_info']['slate_type']}")
                print(f"   Games: {data['slate_info']['num_games']}")

        return results


# Convenience functions
def analyze_current_slates():
    """Analyze all CSV files in current directory"""
    analyzer = SlateAnalyzer()
    csv_files = list(Path('.').glob('*.csv'))

    if not csv_files:
        print("No CSV files found!")
        return

    if len(csv_files) == 1:
        return analyzer.analyze_slate(csv_files[0])
    else:
        return analyzer.compare_slates(csv_files)


def should_i_play(csv_file):
    """Quick recommendation for a slate"""
    analyzer = SlateAnalyzer()
    result = analyzer.analyze_slate(csv_file)

    score = result['overall_score']

    if score >= 80:
        return "YES! This is an excellent slate to play."
    elif score >= 70:
        return "Yes, this slate has good opportunities."
    elif score >= 65:
        return "Maybe. It's playable but not great."
    else:
        return "No, consider waiting for a better slate."


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        analyzer = SlateAnalyzer()
        analyzer.analyze_slate(csv_file)
    else:
        analyze_current_slates()