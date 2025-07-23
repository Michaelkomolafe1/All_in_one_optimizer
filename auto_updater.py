#!/usr/bin/env python3
"""
DFS AUTO-UPDATER
================
Automatically refresh data sources before optimization
"""

import os
import time
import json
import schedule
from datetime import datetime, timedelta
from pathlib import Path
import subprocess


class DFSAutoUpdater:
    def __init__(self):
        self.config_file = "auto_update_config.json"
        self.log_file = "auto_update.log"
        self.load_config()

    def load_config(self):
        """Load or create configuration"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "auto_update": {
                    "enabled": True,
                    "update_before_optimization": True,
                    "scheduled_updates": False,
                    "update_times": ["10:00", "18:00"],  # 10 AM and 6 PM
                    "update_on_slate_change": True
                },
                "data_sources": {
                    "statcast": {
                        "enabled": True,
                        "cache_hours": 4
                    },
                    "vegas_lines": {
                        "enabled": True,
                        "cache_hours": 1
                    },
                    "lineups": {
                        "enabled": True,
                        "cache_hours": 0.5  # 30 minutes
                    }
                },
                "cache_management": {
                    "auto_clean": True,
                    "max_cache_age_days": 7,
                    "max_cache_size_mb": 500
                }
            }
            self.save_config()

    def save_config(self):
        """Save configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def log(self, message, level="INFO"):
        """Log messages"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"

        with open(self.log_file, 'a') as f:
            f.write(log_entry)

        print(f"{level}: {message}")

    def check_cache_age(self, cache_file, max_hours):
        """Check if cache file is older than max_hours"""
        if not os.path.exists(cache_file):
            return True  # Need update if doesn't exist

        file_age = time.time() - os.path.getmtime(cache_file)
        max_seconds = max_hours * 3600

        return file_age > max_seconds

    def update_statcast_data(self):
        """Update Baseball Savant data"""
        if not self.config["data_sources"]["statcast"]["enabled"]:
            return

        self.log("Updating Statcast data...")

        try:
            from simple_statcast_fetcher import FastStatcastFetcher

            fetcher = FastStatcastFetcher()

            # Clear old cache
            cache_dir = Path("data/statcast_cache")
            if cache_dir.exists():
                max_hours = self.config["data_sources"]["statcast"]["cache_hours"]

                for cache_file in cache_dir.glob("*.json"):
                    if self.check_cache_age(cache_file, max_hours):
                        cache_file.unlink()
                        self.log(f"Cleared old cache: {cache_file.name}")

            self.log("✅ Statcast data updated")

        except Exception as e:
            self.log(f"❌ Statcast update failed: {e}", "ERROR")

    def update_vegas_lines(self):
        """Update Vegas lines data"""
        if not self.config["data_sources"]["vegas_lines"]["enabled"]:
            return

        self.log("Updating Vegas lines...")

        try:
            from vegas_lines import VegasLines

            vegas = VegasLines()

            # Force cache refresh
            cache_file = Path("data/cache/vegas_lines.json")
            if cache_file.exists():
                max_hours = self.config["data_sources"]["vegas_lines"]["cache_hours"]

                if self.check_cache_age(cache_file, max_hours):
                    cache_file.unlink()
                    self.log("Cleared Vegas cache")

            # Fetch fresh data
            games = vegas.get_games_for_date(datetime.now().strftime("%Y-%m-%d"))
            self.log(f"✅ Updated Vegas lines for {len(games)} games")

        except Exception as e:
            self.log(f"❌ Vegas update failed: {e}", "ERROR")

    def update_lineups(self):
        """Update confirmed lineups"""
        if not self.config["data_sources"]["lineups"]["enabled"]:
            return

        self.log("Updating confirmed lineups...")

        try:
            from smart_confirmation_system import SmartConfirmationSystem

            system = SmartConfirmationSystem()

            # Clear old cache
            cache_file = Path("data/cache/confirmed_lineups.json")
            if cache_file.exists():
                max_hours = self.config["data_sources"]["lineups"]["cache_hours"]

                if self.check_cache_age(cache_file, max_hours):
                    cache_file.unlink()
                    self.log("Cleared lineup cache")

            self.log("✅ Lineup data updated")

        except Exception as e:
            self.log(f"❌ Lineup update failed: {e}", "ERROR")

    def clean_old_cache(self):
        """Clean old cache files"""
        if not self.config["cache_management"]["auto_clean"]:
            return

        self.log("Cleaning old cache files...")

        cache_dirs = ["data/cache", ".gui_cache", "data/statcast_cache"]
        max_age_days = self.config["cache_management"]["max_cache_age_days"]
        max_age_seconds = max_age_days * 86400

        total_cleaned = 0
        total_size = 0

        for cache_dir in cache_dirs:
            if os.path.exists(cache_dir):
                for root, dirs, files in os.walk(cache_dir):
                    for file in files:
                        file_path = os.path.join(root, file)

                        try:
                            if time.time() - os.path.getmtime(file_path) > max_age_seconds:
                                size = os.path.getsize(file_path)
                                os.remove(file_path)
                                total_cleaned += 1
                                total_size += size
                        except:
                            pass

        if total_cleaned > 0:
            self.log(f"✅ Cleaned {total_cleaned} old files ({total_size / 1024 / 1024:.1f}MB)")

    def update_all(self):
        """Update all data sources"""
        self.log("=" * 50)
        self.log("Starting full data update...")

        start_time = time.time()

        # Update each source
        self.update_statcast_data()
        self.update_vegas_lines()
        self.update_lineups()

        # Clean old cache
        self.clean_old_cache()

        elapsed = time.time() - start_time
        self.log(f"✅ Full update completed in {elapsed:.1f}s")
        self.log("=" * 50)

        return True

    def check_before_optimization(self):
        """Check if updates are needed before optimization"""
        updates_needed = []

        # Check each data source
        sources = [
            ("statcast", "data/statcast_cache", self.config["data_sources"]["statcast"]["cache_hours"]),
            ("vegas", "data/cache/vegas_lines.json", self.config["data_sources"]["vegas_lines"]["cache_hours"]),
            ("lineups", "data/cache/confirmed_lineups.json", self.config["data_sources"]["lineups"]["cache_hours"])
        ]

        for name, cache_path, max_hours in sources:
            if self.config["data_sources"][name]["enabled"]:
                if self.check_cache_age(cache_path, max_hours):
                    updates_needed.append(name)

        if updates_needed:
            print(f"\n⚠️ Data updates recommended for: {', '.join(updates_needed)}")

            if self.config["auto_update"]["update_before_optimization"]:
                print("🔄 Auto-updating...")
                self.update_all()
                return True
            else:
                response = input("Update now? (y/n): ")
                if response.lower() == 'y':
                    self.update_all()
                    return True
        else:
            print("✅ All data sources are up to date")

        return False

    def setup_scheduled_updates(self):
        """Setup scheduled automatic updates"""
        if not self.config["auto_update"]["scheduled_updates"]:
            print("Scheduled updates are disabled")
            return

        # Schedule updates
        for update_time in self.config["auto_update"]["update_times"]:
            schedule.every().day.at(update_time).do(self.update_all)
            print(f"📅 Scheduled update at {update_time}")

        print("\n🤖 Auto-updater is running...")
        print("Press Ctrl+C to stop")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n✋ Auto-updater stopped")


# Integration functions
def check_updates_before_optimization():
    """Call this before running optimization"""
    updater = DFSAutoUpdater()
    return updater.check_before_optimization()


def force_update_all():
    """Force update all data sources"""
    updater = DFSAutoUpdater()
    return updater.update_all()


if __name__ == "__main__":
    import sys

    updater = DFSAutoUpdater()

    if len(sys.argv) > 1:
        if sys.argv[1] == "--schedule":
            updater.setup_scheduled_updates()
        elif sys.argv[1] == "--update":
            updater.update_all()
        elif sys.argv[1] == "--config":
            print(json.dumps(updater.config, indent=2))
    else:
        print("🔄 DFS Auto-Updater")
        print("=" * 40)
        print("Usage:")
        print("  python auto_updater.py --update    # Update all data now")
        print("  python auto_updater.py --schedule  # Run scheduled updates")
        print("  python auto_updater.py --config    # Show configuration")
        print()
        print("Or import in your code:")
        print("  from auto_updater import check_updates_before_optimization")
        print("  check_updates_before_optimization()")