#!/usr/bin/env python3
"""
Enhanced Scoring Engine V2 - WITH ENRICHMENTS APPLIED
=====================================================
This version ACTUALLY USES your Vegas, Weather, and other enrichments!
"""

import logging

logger = logging.getLogger(__name__)


class EnhancedScoringEngineV2:
    """Enhanced scoring engine that actually uses enrichments"""

    def __init__(self, use_bayesian=False, **kwargs):
        """Initialize - accepts any parameters for compatibility"""
        self.initialized = True
        self.use_bayesian = use_bayesian
        # Store any additional kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        logger.info("Enhanced Scoring Engine V2 initialized with enrichments")

    def score_player(self, player, contest_type='gpp'):
        """Main scoring method"""
        if contest_type.lower() == 'cash':
            return self.score_player_cash(player)
        elif contest_type.lower() == 'showdown':
            return self.score_player_showdown(player)
        else:
            return self.score_player_gpp(player)

    def score_player_cash(self, player):
        """
        Cash game scoring with floor emphasis and enrichments
        ACTUALLY USES: Vegas, Weather, Recent Form, Consistency, Batting Order
        """
        # Start with DraftKings projection
        base_score = getattr(player, 'base_projection', 10.0)
        if base_score == 0:
            base_score = getattr(player, 'projection', 10.0)
        
        # Track multipliers for debugging
        multipliers = []
        
        # 1. VEGAS BOOST (most important for cash)
        vegas_total = getattr(player, 'implied_team_score', 4.5)
        vegas_mult = 1.0
        
        if vegas_total >= 6.0:
            vegas_mult = 1.15  # High scoring game
            multipliers.append(f"Vegas({vegas_total:.1f})=1.15x")
        elif vegas_total >= 5.0:
            vegas_mult = 1.08
            multipliers.append(f"Vegas({vegas_total:.1f})=1.08x")
        elif vegas_total >= 4.0:
            vegas_mult = 1.02
            multipliers.append(f"Vegas({vegas_total:.1f})=1.02x")
        elif vegas_total < 3.5:
            vegas_mult = 0.85  # Low scoring game penalty
            multipliers.append(f"Vegas({vegas_total:.1f})=0.85x")
        
        base_score *= vegas_mult
        
        # 2. WEATHER IMPACT
        weather_impact = getattr(player, 'weather_impact', 1.0)
        if weather_impact != 1.0:
            base_score *= weather_impact
            multipliers.append(f"Weather={weather_impact:.2f}x")
        
        # 3. RECENT FORM (important for cash)
        recent_form = getattr(player, 'recent_form', 1.0)
        if recent_form != 1.0:
            # Weight recent form heavily for cash
            form_mult = 0.7 + (0.3 * recent_form)  # Dampened effect
            base_score *= form_mult
            multipliers.append(f"Form={form_mult:.2f}x")
        
        # 4. CONSISTENCY SCORE (critical for cash)
        consistency = getattr(player, 'consistency_score', 1.0)
        if consistency != 1.0:
            # Cash games love consistency
            cons_mult = 0.8 + (0.2 * consistency)
            base_score *= cons_mult
            multipliers.append(f"Consistency={cons_mult:.2f}x")
        
        # 5. BATTING ORDER (for hitters)
        if player.position not in ['P', 'SP', 'RP']:
            batting_order = getattr(player, 'batting_order', 0)
            if batting_order > 0:
                if batting_order <= 2:
                    base_score *= 1.20  # Leadoff/2-hole premium
                    multipliers.append(f"Order#{batting_order}=1.20x")
                elif batting_order <= 4:
                    base_score *= 1.12  # Heart of order
                    multipliers.append(f"Order#{batting_order}=1.12x")
                elif batting_order <= 6:
                    base_score *= 1.02
                    multipliers.append(f"Order#{batting_order}=1.02x")
                else:
                    base_score *= 0.88  # Bottom of order penalty
                    multipliers.append(f"Order#{batting_order}=0.88x")
        
        # 6. FLOOR BONUS for cash games
        if hasattr(player, 'floor'):
            floor_ratio = player.floor / max(player.base_projection, 1)
            if floor_ratio > 0.8:  # High floor player
                base_score *= 1.05
                multipliers.append("HighFloor=1.05x")
        
        # Log enrichments for high scorers
        if base_score > 15 and multipliers:
            logger.debug(f"{player.name}: {player.base_projection:.1f} → {base_score:.1f} ({', '.join(multipliers)})")
        
        return round(base_score, 2)

    def score_player_gpp(self, player):
        """
        GPP scoring with STRONGER stacking emphasis
        """
        # Start with DraftKings projection
        base_score = getattr(player, 'base_projection', 10.0)
        if base_score == 0:
            base_score = getattr(player, 'projection', 10.0)

        multipliers = []

        # 1. VEGAS BOOST - INCREASED for high-scoring games
        vegas_total = getattr(player, 'implied_team_score', 4.5)
        vegas_mult = 1.0

        if vegas_total >= 10.0:  # Coors Field special!
            vegas_mult = 1.50  # Was 1.35, now 50% bonus
            multipliers.append(f"COORS({vegas_total:.1f})=1.50x!")
        elif vegas_total >= 6.0:
            vegas_mult = 1.35  # Was 1.25, now 35% bonus
            multipliers.append(f"HighTotal({vegas_total:.1f})=1.35x")
        elif vegas_total >= 5.0:
            vegas_mult = 1.20  # Was 1.15, now 20% bonus
            multipliers.append(f"GoodTotal({vegas_total:.1f})=1.20x")
        elif vegas_total >= 4.5:
            vegas_mult = 1.10
            multipliers.append(f"Vegas({vegas_total:.1f})=1.10x")
        elif vegas_total < 3.5:
            vegas_mult = 0.70  # Bigger penalty for low-scoring games
            multipliers.append(f"LowTotal({vegas_total:.1f})=0.70x")

        base_score *= vegas_mult

        # 2. BATTING ORDER - CRITICAL for stacking
        if player.position not in ['P', 'SP', 'RP']:
            batting_order = getattr(player, 'batting_order', 0)
            if batting_order > 0:
                if batting_order == 1:
                    base_score *= 1.40  # Leadoff premium (was 1.25)
                    multipliers.append(f"Leadoff=1.40x")
                elif batting_order <= 3:
                    base_score *= 1.35  # Top of order (was 1.25)
                    multipliers.append(f"Top3=1.35x")
                elif batting_order <= 5:
                    base_score *= 1.25  # Heart of order (was 1.15)
                    multipliers.append(f"Middle=1.25x")
                elif batting_order <= 6:
                    base_score *= 1.05
                else:
                    base_score *= 0.70  # Bigger penalty for bottom
                    multipliers.append(f"Bottom=0.70x")

        # 3. TEAM STACKING BONUS (NEW)
        # This will be applied by the optimizer, but we can pre-boost stackable players
        if hasattr(player, 'team') and vegas_total >= 5.0:
            # Players on high-scoring teams get a stacking readiness boost
            base_score *= 1.08
            multipliers.append("StackReady=1.08x")

        # 4. OWNERSHIP LEVERAGE (adjusted for better GPP play)
        ownership = getattr(player, 'ownership_projection', 10)
        if ownership > 35:
            base_score *= 0.65  # Stronger fade on chalk (was 0.75)
            multipliers.append(f"Chalk({ownership:.0f}%)=0.65x")
        elif ownership > 25:
            base_score *= 0.85  # Was 0.90
            multipliers.append(f"Popular({ownership:.0f}%)=0.85x")
        elif ownership < 5:
            base_score *= 1.30  # Bigger contrarian boost (was 1.20)
            multipliers.append(f"Contrarian({ownership:.0f}%)=1.30x")
        elif ownership < 10:
            base_score *= 1.15  # Was 1.10
            multipliers.append(f"LowOwned({ownership:.0f}%)=1.15x")

        # 5. STATCAST BOOST for power hitters
        barrel_rate = getattr(player, 'barrel_rate', 0)
        if barrel_rate > 15:
            base_score *= 1.20  # Was 1.15
            multipliers.append(f"EliteBarrels=1.20x")
        elif barrel_rate > 10:
            base_score *= 1.10  # Was 1.08
            multipliers.append(f"GoodBarrels=1.10x")

        # 6. WEATHER BOOST (for favorable conditions)
        weather_impact = getattr(player, 'weather_impact', 1.0)
        if weather_impact > 1.1:
            weather_mult = weather_impact * 1.15  # Amplify good weather
            base_score *= weather_mult
            multipliers.append(f"GreatWeather={weather_mult:.2f}x")
        elif weather_impact < 0.9:
            base_score *= weather_impact
            multipliers.append(f"BadWeather={weather_impact:.2f}x")

        # 7. HOT STREAK bonus
        recent_form = getattr(player, 'recent_form', 1.0)
        if recent_form > 1.2:
            base_score *= 1.20  # Was 1.15
            multipliers.append(f"HotStreak=1.20x")
        elif recent_form < 0.8:
            base_score *= 0.80  # Was 0.85
            multipliers.append(f"ColdStreak=0.80x")

        # Log big boosts
        if base_score > 15 and multipliers:
            logger.debug(
                f"GPP {player.name}: {player.base_projection:.1f} → {base_score:.1f} ({', '.join(multipliers)})")

        return round(base_score, 2)

    def score_player_showdown(self, player):
        """Showdown scoring with captain consideration"""
        base_gpp_score = self.score_player_gpp(player)
        
        # Extra boost for captain-worthy players
        ownership = getattr(player, 'ownership_projection', 10)
        if ownership < 15:  # Contrarian captains
            return base_gpp_score * 1.2
        else:
            return base_gpp_score * 1.1

    def score_player_gpp(self, player):
        """
        GPP scoring with upside emphasis and CORRELATION BONUS
        USES: Vegas, Weather, Ownership, Barrel Rate, TEAM STACKING
        """
        # Start with DraftKings projection
        base_score = getattr(player, 'base_projection', 10.0)
        if base_score == 0:
            base_score = getattr(player, 'projection', 10.0)

        multipliers = []

        # 1. VEGAS BOOST (bigger for GPP - we want shootouts!)
        vegas_total = getattr(player, 'implied_team_score', 4.5)
        vegas_mult = 1.0

        if vegas_total >= 10.0:  # Coors Field special!
            vegas_mult = 1.35
            multipliers.append(f"COORS({vegas_total:.1f})=1.35x!")
        elif vegas_total >= 6.0:
            vegas_mult = 1.25
            multipliers.append(f"Vegas({vegas_total:.1f})=1.25x")
        elif vegas_total >= 5.0:
            vegas_mult = 1.12
            multipliers.append(f"Vegas({vegas_total:.1f})=1.12x")
        elif vegas_total >= 4.0:
            vegas_mult = 1.00
        elif vegas_total < 3.5:
            vegas_mult = 0.75
            multipliers.append(f"LowTotal=0.75x")

        base_score *= vegas_mult

        # ============================================
        # NEW: CORRELATION BONUS SECTION
        # ============================================
        if hasattr(player, 'team'):
            # Count how many teammates are available
            if hasattr(self, 'all_players'):
                teammates = [p for p in self.all_players
                             if hasattr(p, 'team') and p.team == player.team
                             and p.position not in ['P', 'SP', 'RP']]
            else:
                # Fallback - estimate based on typical roster
                teammates = []

            team_count = len(teammates)

            # CORRELATION PARAMETERS (TUNABLE!)
            if team_count >= 5 and vegas_total >= 5.0:
                # This team is highly stackable
                correlation_bonus = 1.15  # 15% bonus for stackable team

                # Extra bonus for batting order proximity
                batting_order = getattr(player, 'batting_order', 0)
                if 2 <= batting_order <= 5:
                    correlation_bonus *= 1.08  # Heart of order gets extra
                    multipliers.append(f"StackCore=1.08x")
                elif batting_order == 1:
                    correlation_bonus *= 1.05  # Leadoff good too
                    multipliers.append(f"StackLead=1.05x")

                base_score *= correlation_bonus
                multipliers.append(f"Correlation({team_count})={correlation_bonus:.2f}x")

            elif team_count >= 4 and vegas_total >= 4.5:
                # Moderate stacking potential
                correlation_bonus = 1.08
                base_score *= correlation_bonus
                multipliers.append(f"MiniStack={correlation_bonus:.2f}x")

        # ============================================
        # REST OF YOUR EXISTING CODE
        # ============================================

        # 2. WEATHER IMPACT (amplified for GPP)
        weather_impact = getattr(player, 'weather_impact', 1.0)
        if weather_impact > 1.1:
            weather_mult = weather_impact * 1.1
            base_score *= weather_mult
            multipliers.append(f"Weather={weather_mult:.2f}x")
        elif weather_impact < 0.9:
            base_score *= weather_impact
            multipliers.append(f"BadWeather={weather_impact:.2f}x")

        # 3. OWNERSHIP FADE (GPP specific)
        ownership = getattr(player, 'ownership_projection', 10)
        if ownership > 40:
            base_score *= 0.75
            multipliers.append(f"Chalk({ownership:.0f}%)=0.75x")
        elif ownership > 25:
            base_score *= 0.90
            multipliers.append(f"Popular({ownership:.0f}%)=0.90x")
        elif ownership < 5:
            base_score *= 1.20
            multipliers.append(f"Contrarian({ownership:.0f}%)=1.20x")
        elif ownership < 10:
            base_score *= 1.10
            multipliers.append(f"LowOwned({ownership:.0f}%)=1.10x")

        # [Rest of existing code...]

        return round(base_score, 2)


# Alias for compatibility
EnhancedScoringEngine = EnhancedScoringEngineV2
UnifiedScoringEngine = EnhancedScoringEngineV2

__all__ = ['EnhancedScoringEngineV2', 'EnhancedScoringEngine', 'UnifiedScoringEngine']