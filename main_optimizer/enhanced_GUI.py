class SimplifiedDFSOptimizer(QMainWindow):
    """Simple 2-button DFS Optimizer with debug mode"""

    def __init__(self):
        super().__init__()
        self.system = UnifiedCoreSystem()
        self.manual_players = set()
        self.debug_mode = False  # Toggle for debug info
        self.setWindowTitle("DFS Optimizer - Simple Mode")
        self.setGeometry(100, 100, 1400, 900)  # Wider for debug panel
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)  # Changed to horizontal

        # Left side - Main controls
        left_panel = QWidget()
        layout = QVBoxLayout(left_panel)

        # Header
        header = QLabel("DFS OPTIMIZER")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        layout.addWidget(header)

        # Main Control Panel
        control_panel = QGroupBox()
        control_layout = QVBoxLayout(control_panel)

        # Status Display
        self.status_display = QTextEdit()
        self.status_display.setReadOnly(True)
        self.status_display.setMaximumHeight(150)
        self.status_display.setStyleSheet("""
            QTextEdit {
                background-color: #f0f0f0;
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                font-family: monospace;
                font-size: 12px;
            }
        """)
        self.update_status("Ready to load CSV file")
        control_layout.addWidget(self.status_display)

        # Settings Row
        settings_layout = QHBoxLayout()

        # Contest Type
        settings_layout.addWidget(QLabel("Contest:"))
        self.contest_type = QComboBox()
        self.contest_type.addItems(["Cash", "GPP"])
        self.contest_type.setStyleSheet("font-size: 14px; padding: 5px;")
        self.contest_type.currentTextChanged.connect(self.on_contest_changed)
        settings_layout.addWidget(self.contest_type)

        settings_layout.addSpacing(20)

        # Manual Strategy Override
        self.manual_strategy_cb = QCheckBox("Manual Strategy")
        self.manual_strategy_cb.toggled.connect(self.toggle_manual_strategy)
        settings_layout.addWidget(self.manual_strategy_cb)

        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "projection_monster",
            "pitcher_dominance",
            "correlation_value",
            "smart_stack",
            "matchup_leverage"
        ])
        self.strategy_combo.setEnabled(False)
        self.strategy_combo.setStyleSheet("font-size: 14px; padding: 5px;")
        settings_layout.addWidget(self.strategy_combo)

        # Debug Mode Toggle
        self.debug_cb = QCheckBox("Debug Mode")
        self.debug_cb.setStyleSheet("color: red; font-weight: bold;")
        self.debug_cb.toggled.connect(self.toggle_debug_mode)
        settings_layout.addWidget(self.debug_cb)

        settings_layout.addStretch()
        control_layout.addLayout(settings_layout)

        # Manual Player Addition
        manual_layout = QHBoxLayout()
        manual_layout.addWidget(QLabel("Add Player:"))
        self.manual_player_input = QLineEdit()
        self.manual_player_input.setPlaceholderText("Enter player name...")
        self.manual_player_input.returnPressed.connect(self.add_manual_player)
        manual_layout.addWidget(self.manual_player_input)

        self.add_player_btn = QPushButton("Add")
        self.add_player_btn.clicked.connect(self.add_manual_player)
        manual_layout.addWidget(self.add_player_btn)

        self.manual_label = QLabel("Manual: None")
        self.manual_label.setStyleSheet("color: #666; font-style: italic;")
        manual_layout.addWidget(self.manual_label)

        control_layout.addLayout(manual_layout)

        # The 2 Main Buttons
        button_layout = QHBoxLayout()

        # Button 1: Load & Setup
        self.load_button = QPushButton("📁 LOAD & SETUP")
        self.load_button.setMinimumHeight(60)
        self.load_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.load_button.clicked.connect(self.load_and_setup)
        button_layout.addWidget(self.load_button)

        # Button 2: Optimize
        self.optimize_button = QPushButton("🚀 OPTIMIZE")
        self.optimize_button.setMinimumHeight(60)
        self.optimize_button.setEnabled(False)
        self.optimize_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.optimize_button.clicked.connect(self.run_optimization)
        button_layout.addWidget(self.optimize_button)

        control_layout.addLayout(button_layout)
        layout.addWidget(control_panel)

        # Results Display (Tabbed)
        self.tabs = QTabWidget()

        # Lineup tab
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        self.tabs.addTab(self.results_display, "Lineup")

        # Player pool tab
        self.pool_display = QTextEdit()
        self.pool_display.setReadOnly(True)
        self.tabs.addTab(self.pool_display, "Player Pool")

        # Debug tab
        self.debug_display = QTextEdit()
        self.debug_display.setReadOnly(True)
        self.debug_display.setStyleSheet("font-family: monospace; font-size: 10px;")
        self.tabs.addTab(self.debug_display, "Debug Info")

        layout.addWidget(self.tabs)

        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        main_layout.addWidget(left_panel)

        # Right side - Debug Panel (initially hidden)
        self.debug_panel = self.create_debug_panel()
        self.debug_panel.setVisible(False)
        main_layout.addWidget(self.debug_panel)

    def create_debug_panel(self):
        """Create a detailed debug panel"""
        panel = QGroupBox("🔍 DEBUG PANEL")
        panel.setMaximumWidth(400)
        panel.setStyleSheet("""
            QGroupBox {
                background-color: #fff3cd;
                border: 2px solid #856404;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
        """)

        layout = QVBoxLayout(panel)

        # Enrichment Stats
        self.enrichment_stats = QTextEdit()
        self.enrichment_stats.setReadOnly(True)
        self.enrichment_stats.setMaximumHeight(200)
        layout.addWidget(QLabel("Enrichment Stats:"))
        layout.addWidget(self.enrichment_stats)

        # Sample Player Details
        self.sample_player_details = QTextEdit()
        self.sample_player_details.setReadOnly(True)
        layout.addWidget(QLabel("Sample Player Analysis:"))
        layout.addWidget(self.sample_player_details)

        # Test Buttons
        test_btn_layout = QVBoxLayout()

        verify_btn = QPushButton("🔬 Verify All Enrichments")
        verify_btn.clicked.connect(self.verify_all_enrichments)
        test_btn_layout.addWidget(verify_btn)

        test_scoring_btn = QPushButton("📊 Test Scoring Engine")
        test_scoring_btn.clicked.connect(self.test_scoring_engine)
        test_btn_layout.addWidget(test_scoring_btn)

        dump_player_btn = QPushButton("💾 Dump Player Data")
        dump_player_btn.clicked.connect(self.dump_player_data)
        test_btn_layout.addWidget(dump_player_btn)

        layout.addLayout(test_btn_layout)

        return panel

    def toggle_debug_mode(self, checked):
        """Toggle debug mode on/off"""
        self.debug_mode = checked
        self.debug_panel.setVisible(checked)
        if checked:
            self.update_status("🔍 DEBUG MODE ENABLED", append=True)
            self.tabs.setCurrentIndex(2)  # Switch to debug tab
        else:
            self.update_status("Debug mode disabled", append=True)

    def load_and_setup(self):
        """Enhanced with debug tracking"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select DraftKings CSV", "", "CSV Files (*.csv)")
        if not file_path:
            return

        try:
            self.progress.setVisible(True)
            self.load_button.setEnabled(False)

            # Clear debug info
            self.debug_display.clear()

            # Step 1: Load CSV
            self.progress.setValue(20)
            self.update_status("📂 Loading CSV...")
            self.debug_log("=== LOADING CSV ===")

            self.system.load_players_from_csv(file_path)
            self.update_status(f"✅ Loaded {len(self.system.players)} players", append=True)
            self.debug_log(f"Loaded {len(self.system.players)} players from {file_path}")
            self.debug_log(f"Positions found: {set(p.primary_position for p in self.system.players)}")

            # Step 2: Detect Slate & Strategy
            self.progress.setValue(30)
            self.update_status("🔍 Analyzing slate...", append=True)
            self.debug_log("\n=== SLATE ANALYSIS ===")

            slate_info = self.analyze_and_select_strategy()
            self.update_status(f"✅ {slate_info['slate_size'].upper()} slate | {slate_info['num_games']} games",
                               append=True)
            self.debug_log(f"Slate: {slate_info}")

            # Use manual strategy if selected
            if self.manual_strategy_cb.isChecked():
                self.selected_strategy = self.strategy_combo.currentText()
                self.update_status(f"📋 Strategy: {self.selected_strategy} (manual)", append=True)
            else:
                self.update_status(f"📋 Strategy: {self.selected_strategy} (auto)", append=True)
            self.debug_log(f"Selected strategy: {self.selected_strategy}")

            # Step 3: Fetch Confirmations
            self.progress.setValue(50)
            self.update_status("🔄 Fetching confirmed lineups...", append=True)
            self.debug_log("\n=== CONFIRMATIONS ===")

            confirmed = self.system.fetch_confirmed_players()
            self.update_status(f"✅ Found {len(confirmed)} confirmed players", append=True)
            self.debug_log(f"Confirmed: {len(confirmed)} players")
            if self.debug_mode and confirmed:
                self.debug_log(f"Sample: {list(confirmed)[:5]}")

            # Step 4: Build Pool
            self.progress.setValue(70)
            self.update_status("🏗️ Building player pool...", append=True)
            self.debug_log("\n=== PLAYER POOL ===")

            self.build_pool_with_manual()
            self.update_status(f"✅ Pool: {len(self.system.player_pool)} players", append=True)
            self.debug_log(f"Pool size: {len(self.system.player_pool)}")

            # Step 5: Enrich Data
            self.progress.setValue(85)
            self.update_status("🔬 Enriching player data...", append=True)
            self.debug_log("\n=== ENRICHMENT ===")

            # Track enrichment results
            enrichment_results = self.track_enrichments()

            # Step 6: Score Players
            self.progress.setValue(95)
            self.update_status("📊 Calculating scores...", append=True)
            self.debug_log("\n=== SCORING ===")

            contest_type = self.contest_type.currentText().lower()
            self.system.score_players(contest_type)
            self.debug_log(f"Scored for {contest_type}")

            # Verify scoring
            self.verify_scoring_distribution()

            # Done!
            self.progress.setValue(100)
            self.update_status("✅ READY TO OPTIMIZE!", append=True)
            self.optimize_button.setEnabled(True)
            self.load_button.setEnabled(True)
            self.progress.setVisible(False)

            # Show summaries
            self.show_setup_summary()
            self.update_pool_display()

            if self.debug_mode:
                self.update_debug_panel(enrichment_results)

        except Exception as e:
            self.update_status(f"❌ Error: {str(e)}", append=True)
            self.debug_log(f"ERROR: {str(e)}\n{traceback.format_exc()}")
            self.load_button.setEnabled(True)
            self.progress.setVisible(False)

    def track_enrichments(self):
        """Track what enrichments are applied"""
        self.system.enrich_player_pool()

        results = {
            'total': len(self.system.player_pool),
            'vegas': 0,
            'weather': 0,
            'park': 0,
            'stats': 0,
            'consistency': 0,
            'confirmed': 0
        }

        for player in self.system.player_pool:
            if hasattr(player, 'team_total') and player.team_total > 0:
                results['vegas'] += 1
            if hasattr(player, 'weather_impact') and player.weather_impact != 1.0:
                results['weather'] += 1
            if hasattr(player, 'park_factor') and player.park_factor != 1.0:
                results['park'] += 1
            if hasattr(player, 'recent_form') and player.recent_form != 1.0:
                results['stats'] += 1
            if hasattr(player, 'consistency_score'):
                results['consistency'] += 1
            if getattr(player, 'is_confirmed', False):
                results['confirmed'] += 1

        # Log results
        self.debug_log(f"Enrichment Results: {results}")

        # Update status
        self.update_status(
            f"   Vegas: {results['vegas']}/{results['total']} | "
            f"Weather: {results['weather']}/{results['total']} | "
            f"Stats: {results['stats']}/{results['total']}",
            append=True
        )

        return results

    def verify_scoring_distribution(self):
        """Check score distribution"""
        if not self.system.player_pool:
            return

        contest_type = self.contest_type.currentText().lower()
        score_attr = 'cash_score' if contest_type == 'cash' else 'gpp_score'

        scores = [getattr(p, score_attr, 0) for p in self.system.player_pool]

        if scores:
            self.debug_log(f"Score distribution:")
            self.debug_log(f"  Min: {min(scores):.2f}")
            self.debug_log(f"  Max: {max(scores):.2f}")
            self.debug_log(f"  Avg: {sum(scores) / len(scores):.2f}")
            self.debug_log(f"  Zero scores: {scores.count(0)}")

    def verify_all_enrichments(self):
        """Detailed enrichment verification"""
        if not self.system.player_pool:
            QMessageBox.warning(self, "Warning", "No player pool to verify!")
            return

        # Clear debug display
        self.debug_display.clear()
        self.debug_log("=== ENRICHMENT VERIFICATION ===\n")

        # Sample different player types
        test_groups = {
            'High Salary Pitcher': next((p for p in self.system.player_pool
                                         if p.is_pitcher and p.salary >= 9000), None),
            'Min Salary Hitter': next((p for p in self.system.player_pool
                                       if not p.is_pitcher and p.salary <= 3000), None),
            'Confirmed Player': next((p for p in self.system.player_pool
                                      if getattr(p, 'is_confirmed', False)), None),
        }

        for group_name, player in test_groups.items():
            if not player:
                self.debug_log(f"{group_name}: NOT FOUND")
                continue

            self.debug_log(f"\n{group_name}: {player.name} (${player.salary})")
            self.debug_log("-" * 50)

            # Check all attributes
            attrs_to_check = [
                ('base_projection', 'Base DK Projection'),
                ('team_total', 'Vegas Team Total'),
                ('park_factor', 'Park Factor'),
                ('weather_impact', 'Weather Impact'),
                ('recent_form', 'Recent Form'),
                ('consistency_score', 'Consistency'),
                ('batting_order', 'Batting Order'),
                ('is_confirmed', 'Confirmed Status'),
                ('cash_score', 'Cash Score'),
                ('gpp_score', 'GPP Score'),
                ('optimization_score', 'Optimization Score')
            ]

            for attr, label in attrs_to_check:
                value = getattr(player, attr, 'MISSING')
                if value == 'MISSING':
                    self.debug_log(f"  ❌ {label}: MISSING")
                else:
                    self.debug_log(f"  ✅ {label}: {value}")

            # Check for Statcast data
            if hasattr(player, 'recent_avg'):
                self.debug_log(f"  ✅ Statcast AVG: {player.recent_avg}")
            elif hasattr(player, 'recent_velocity'):
                self.debug_log(f"  ✅ Statcast Velo: {player.recent_velocity}")
            else:
                self.debug_log(f"  ❌ Statcast: NO DATA")

        # Summary stats
        self.debug_log("\n=== ENRICHMENT SUMMARY ===")
        total = len(self.system.player_pool)

        for attr in ['team_total', 'park_factor', 'weather_impact', 'recent_form']:
            count = sum(1 for p in self.system.player_pool
                        if hasattr(p, attr) and getattr(p, attr) != 'MISSING')
            pct = (count / total * 100) if total > 0 else 0
            self.debug_log(f"{attr}: {count}/{total} ({pct:.1f}%)")

    def test_scoring_engine(self):
        """Test the scoring engine with sample players"""
        if not self.system.player_pool:
            QMessageBox.warning(self, "Warning", "No player pool to test!")
            return

        self.debug_display.clear()
        self.debug_log("=== SCORING ENGINE TEST ===\n")

        # Get scoring engine
        if not hasattr(self.system, 'scoring_engine'):
            from enhanced_scoring_engine import EnhancedScoringEngine
            self.system.scoring_engine = EnhancedScoringEngine()

        # Test a few players
        test_players = self.system.player_pool[:3]

        for player in test_players:
            self.debug_log(f"\nTesting: {player.name}")
            self.debug_log(f"Base projection: {getattr(player, 'base_projection', 0)}")

            # Calculate both scores
            cash_score = self.system.scoring_engine.score_player_cash(player)
            gpp_score = self.system.scoring_engine.score_player_gpp(player)

            self.debug_log(f"Cash score: {cash_score:.2f}")
            self.debug_log(f"GPP score: {gpp_score:.2f}")

            # Show multipliers
            if player.base_projection > 0:
                cash_mult = cash_score / player.base_projection
                gpp_mult = gpp_score / player.base_projection
                self.debug_log(f"Cash multiplier: {cash_mult:.2f}x")
                self.debug_log(f"GPP multiplier: {gpp_mult:.2f}x")

    def dump_player_data(self):
        """Dump complete data for a few players"""
        if not self.system.player_pool:
            return

        # Get top 3 by score
        contest_type = self.contest_type.currentText().lower()
        score_attr = 'cash_score' if contest_type == 'cash' else 'gpp_score'

        top_players = sorted(self.system.player_pool,
                             key=lambda p: getattr(p, score_attr, 0),
                             reverse=True)[:3]

        output = f"=== TOP 3 PLAYERS BY {score_attr.upper()} ===\n\n"

        for player in top_players:
            output += f"{player.name}:\n"
            output += "-" * 40 + "\n"

            # Dump all attributes
            for attr in sorted(dir(player)):
                if not attr.startswith('_'):
                    try:
                        value = getattr(player, attr)
                        if not callable(value):
                            output += f"  {attr}: {value}\n"
                    except:
                        pass

            output += "\n"

        # Save to clipboard
        QApplication.clipboard().setText(output)
        self.debug_log("Player data copied to clipboard!")

    def debug_log(self, message):
        """Add to debug log"""
        if self.debug_mode:
            current = self.debug_display.toPlainText()
            self.debug_display.setText(f"{current}\n{message}" if current else message)
            # Auto-scroll to bottom
            cursor = self.debug_display.textCursor()
            cursor.movePosition(cursor.End)
            self.debug_display.setTextCursor(cursor)

    def update_debug_panel(self, enrichment_results):
        """Update the debug panel with enrichment stats"""
        # Enrichment stats
        stats_text = f"""Total Players: {enrichment_results['total']}
Vegas Data: {enrichment_results['vegas']} ({enrichment_results['vegas'] / enrichment_results['total'] * 100:.1f}%)
Weather: {enrichment_results['weather']} ({enrichment_results['weather'] / enrichment_results['total'] * 100:.1f}%)
Park Factors: {enrichment_results['park']} ({enrichment_results['park'] / enrichment_results['total'] * 100:.1f}%)
Stats/Form: {enrichment_results['stats']} ({enrichment_results['stats'] / enrichment_results['total'] * 100:.1f}%)
Confirmed: {enrichment_results['confirmed']}"""

        self.enrichment_stats.setText(stats_text)

        # Sample player details
        if self.system.player_pool:
            sample = self.system.player_pool[0]
            details = f"""Player: {sample.name}
Team: {sample.team}
Salary: ${sample.salary}
Base Proj: {getattr(sample, 'base_projection', 'N/A')}
Vegas Total: {getattr(sample, 'team_total', 'N/A')}
Park Factor: {getattr(sample, 'park_factor', 'N/A')}
Weather: {getattr(sample, 'weather_impact', 'N/A')}
Form: {getattr(sample, 'recent_form', 'N/A')}
Cash Score: {getattr(sample, 'cash_score', 'N/A')}
GPP Score: {getattr(sample, 'gpp_score', 'N/A')}"""

            self.sample_player_details.setText(details)