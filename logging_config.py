#!/usr/bin/env python3
"""
LOGGING CONFIGURATION FOR DFS OPTIMIZER
======================================
Centralized logging setup with different handlers for different purposes
"""

import logging
import logging.handlers
import os
from datetime import datetime


def setup_logging(name=None):
    """Set up logging with both file and console output"""

    # Create logs directory
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Log filenames with timestamps
    timestamp = datetime.now().strftime("%Y%m%d")

    # Configure root logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Remove existing handlers to avoid duplicates
    logger.handlers = []

    # Console handler - INFO and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler for general logs
    file_handler = logging.handlers.RotatingFileHandler(
        f'{log_dir}/dfs_optimizer_{timestamp}.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s')
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    # Separate handler for optimization decisions
    optimization_handler = logging.handlers.RotatingFileHandler(
        f'{log_dir}/optimization_decisions_{timestamp}.log',
        maxBytes=5*1024*1024,
        backupCount=3
    )
    optimization_handler.setLevel(logging.INFO)
    optimization_handler.setFormatter(file_format)
    optimization_handler.addFilter(OptimizationFilter())
    logger.addHandler(optimization_handler)

    # Separate handler for player scoring
    scoring_handler = logging.handlers.RotatingFileHandler(
        f'{log_dir}/player_scoring_{timestamp}.log',
        maxBytes=5*1024*1024,
        backupCount=3
    )
    scoring_handler.setLevel(logging.INFO)
    scoring_handler.setFormatter(file_format)
    scoring_handler.addFilter(ScoringFilter())
    logger.addHandler(scoring_handler)

    # Performance metrics handler
    performance_handler = logging.handlers.RotatingFileHandler(
        f'{log_dir}/performance_metrics_{timestamp}.log',
        maxBytes=5*1024*1024,
        backupCount=3
    )
    performance_handler.setLevel(logging.INFO)
    performance_handler.setFormatter(file_format)
    performance_handler.addFilter(PerformanceFilter())
    logger.addHandler(performance_handler)

    return logger


class OptimizationFilter(logging.Filter):
    """Filter for optimization-related logs"""
    def filter(self, record):
        return 'OPTIMIZATION' in record.getMessage() or 'LINEUP' in record.getMessage()


class ScoringFilter(logging.Filter):
    """Filter for scoring-related logs"""
    def filter(self, record):
        return 'SCORE' in record.getMessage() or 'BOOST' in record.getMessage()


class PerformanceFilter(logging.Filter):
    """Filter for performance-related logs"""
    def filter(self, record):
        return 'PERFORMANCE' in record.getMessage() or 'TIMING' in record.getMessage()


# Convenience function to get logger
def get_logger(name):
    """Get a logger with the standard configuration"""
    return setup_logging(name)
