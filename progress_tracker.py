#!/usr/bin/env python3
"""
Progress Tracking System for DFS Optimizer
=========================================
Provides visual progress feedback for long-running operations
"""

import sys
import time
from typing import Optional


class ProgressTracker:
    """Track and display progress for operations"""

    def __init__(self, total: int, description: str = "Processing", show_eta: bool = True):
        self.total = total
        self.current = 0
        self.description = description
        self.show_eta = show_eta
        self.start_time = time.time()
        self.last_update_time = 0
        self._finished = False

    def update(self, increment: int = 1, message: Optional[str] = None):
        """Update progress"""
        if self._finished:
            return

        self.current = min(self.current + increment, self.total)
        current_time = time.time()

        # Only update display every 0.1 seconds to avoid flickering
        if current_time - self.last_update_time < 0.1 and self.current < self.total:
            return

        self.last_update_time = current_time

        # Calculate progress
        percentage = (self.current / self.total) * 100 if self.total > 0 else 0

        # Calculate ETA
        elapsed = current_time - self.start_time
        if self.show_eta and self.current > 0:
            rate = self.current / elapsed
            remaining = self.total - self.current
            eta_seconds = remaining / rate if rate > 0 else 0

            if eta_seconds < 60:
                eta_str = f"{int(eta_seconds)}s"
            else:
                eta_minutes = int(eta_seconds / 60)
                eta_seconds = int(eta_seconds % 60)
                eta_str = f"{eta_minutes}m {eta_seconds}s"

            time_info = f" | ETA: {eta_str}"
        else:
            time_info = ""

        # Build progress bar
        bar_length = 30
        filled_length = int(bar_length * self.current / self.total)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)

        # Build status line
        status = f"\r{self.description}: [{bar}] {self.current}/{self.total} ({percentage:.1f}%){time_info}"

        if message:
            # Truncate message if too long
            max_msg_len = 40
            if len(message) > max_msg_len:
                message = message[: max_msg_len - 3] + "..."
            status += f" - {message}"

        # Clear line and print
        sys.stdout.write("\r" + " " * 100 + "\r")  # Clear previous line
        sys.stdout.write(status)
        sys.stdout.flush()

        # New line when complete
        if self.current >= self.total:
            self.finish()

    def finish(self):
        """Mark as finished and print final time"""
        if self._finished:
            return

        self._finished = True
        elapsed = time.time() - self.start_time

        if elapsed < 60:
            time_str = f"{elapsed:.1f}s"
        else:
            minutes = int(elapsed / 60)
            seconds = int(elapsed % 60)
            time_str = f"{minutes}m {seconds}s"

        print(f" ✓ (completed in {time_str})")

    def set_description(self, description: str):
        """Update the description"""
        self.description = description


class MultiStageProgress:
    """Track progress across multiple stages"""

    def __init__(self, stages: list):
        self.stages = stages
        self.current_stage = 0
        self.stage_tracker = None

    def start_stage(self, total_items: int):
        """Start a new stage"""
        if self.current_stage >= len(self.stages):
            return

        stage_name = self.stages[self.current_stage]
        print(f"\n📊 Stage {self.current_stage + 1}/{len(self.stages)}: {stage_name}")

        self.stage_tracker = ProgressTracker(total_items, f"  {stage_name}")

    def update(self, increment: int = 1, message: Optional[str] = None):
        """Update current stage progress"""
        if self.stage_tracker:
            self.stage_tracker.update(increment, message)

    def complete_stage(self):
        """Complete current stage and move to next"""
        if self.stage_tracker:
            self.stage_tracker.finish()
        self.current_stage += 1
        self.stage_tracker = None


# Example usage function
def track_operation(items: list, description: str = "Processing items"):
    """Helper function to easily add progress tracking to any loop"""
    tracker = ProgressTracker(len(items), description)

    for i, item in enumerate(items):
        yield item
        tracker.update(1)
