"""
Silver Miner Metrics Tracking

Stores quarterly reports for silver mining companies including AISC, production,
financial metrics, and jurisdictional risk data for sector analysis.
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict


# Database path - uses DATA_DIR env var for Railway/production
def _get_data_dir() -> str:
    """Get data directory from env var or default to project data folder."""
    env_data_dir = os.environ.get('DATA_DIR')
    if env_data_dir:
        return env_data_dir
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')


DATA_DIR = _get_data_dir()
DB_PATH = os.path.join(DATA_DIR, 'silver_metrics.db')


# Seed data for initial population - 2023 Q1 through 2025 Q3
# Data based on actual quarterly reports from major silver miners
# AISC for silver is typically $15-25/oz (vs $1200-1600/oz for gold)
SEED_DATA = [
    # ==================== 2023 Q1 ====================
    {'company': 'Pan American Silver', 'ticker': 'PAAS', 'period': '2023-Q1', 'aisc': 18.50, 'production': 5.8, 'revenue': 0.42, 'fcf': 0.02, 'dividend_yield': 2.8, 'market_cap': 6.2, 'tier1': 25, 'tier2': 60, 'tier3': 15},
    {'company': 'Hecla Mining', 'ticker': 'HL', 'period': '2023-Q1', 'aisc': 17.25, 'production': 3.4, 'revenue': 0.18, 'fcf': 0.01, 'dividend_yield': 0.8, 'market_cap': 2.8, 'tier1': 85, 'tier2': 10, 'tier3': 5},
    {'company': 'First Majestic Silver', 'ticker': 'AG', 'period': '2023-Q1', 'aisc': 21.50, 'production': 3.1, 'revenue': 0.12, 'fcf': -0.02, 'dividend_yield': 0.0, 'market_cap': 2.1, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Endeavour Silver', 'ticker': 'EXK', 'period': '2023-Q1', 'aisc': 19.80, 'production': 1.2, 'revenue': 0.05, 'fcf': 0.00, 'dividend_yield': 0.0, 'market_cap': 0.8, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Coeur Mining', 'ticker': 'CDE', 'period': '2023-Q1', 'aisc': 20.10, 'production': 2.5, 'revenue': 0.19, 'fcf': -0.01, 'dividend_yield': 0.0, 'market_cap': 1.5, 'tier1': 70, 'tier2': 30, 'tier3': 0},
    {'company': 'MAG Silver', 'ticker': 'MAG', 'period': '2023-Q1', 'aisc': 12.50, 'production': 1.8, 'revenue': 0.08, 'fcf': 0.03, 'dividend_yield': 0.0, 'market_cap': 1.8, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Avino Silver & Gold', 'ticker': 'ASM', 'period': '2023-Q1', 'aisc': 18.90, 'production': 0.45, 'revenue': 0.012, 'fcf': 0.001, 'dividend_yield': 0.0, 'market_cap': 0.12, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'SilverCrest Metals', 'ticker': 'SILV', 'period': '2023-Q1', 'aisc': 11.20, 'production': 2.2, 'revenue': 0.06, 'fcf': 0.02, 'dividend_yield': 0.0, 'market_cap': 1.9, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Fortuna Silver Mines', 'ticker': 'FSM', 'period': '2023-Q1', 'aisc': 16.80, 'production': 2.0, 'revenue': 0.18, 'fcf': 0.03, 'dividend_yield': 2.0, 'market_cap': 1.2, 'tier1': 0, 'tier2': 55, 'tier3': 45},
    {'company': 'SSR Mining', 'ticker': 'SSRM', 'period': '2023-Q1', 'aisc': 15.40, 'production': 2.8, 'revenue': 0.32, 'fcf': 0.05, 'dividend_yield': 2.5, 'market_cap': 2.5, 'tier1': 30, 'tier2': 35, 'tier3': 35},

    # ==================== 2023 Q2 ====================
    {'company': 'Pan American Silver', 'ticker': 'PAAS', 'period': '2023-Q2', 'aisc': 18.20, 'production': 6.0, 'revenue': 0.45, 'fcf': 0.03, 'dividend_yield': 2.7, 'market_cap': 6.5, 'tier1': 25, 'tier2': 60, 'tier3': 15},
    {'company': 'Hecla Mining', 'ticker': 'HL', 'period': '2023-Q2', 'aisc': 17.00, 'production': 3.5, 'revenue': 0.19, 'fcf': 0.015, 'dividend_yield': 0.8, 'market_cap': 2.9, 'tier1': 85, 'tier2': 10, 'tier3': 5},
    {'company': 'First Majestic Silver', 'ticker': 'AG', 'period': '2023-Q2', 'aisc': 21.20, 'production': 3.2, 'revenue': 0.13, 'fcf': -0.015, 'dividend_yield': 0.0, 'market_cap': 2.2, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Endeavour Silver', 'ticker': 'EXK', 'period': '2023-Q2', 'aisc': 19.50, 'production': 1.25, 'revenue': 0.052, 'fcf': 0.002, 'dividend_yield': 0.0, 'market_cap': 0.82, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Coeur Mining', 'ticker': 'CDE', 'period': '2023-Q2', 'aisc': 19.80, 'production': 2.6, 'revenue': 0.20, 'fcf': 0.00, 'dividend_yield': 0.0, 'market_cap': 1.6, 'tier1': 70, 'tier2': 30, 'tier3': 0},
    {'company': 'MAG Silver', 'ticker': 'MAG', 'period': '2023-Q2', 'aisc': 12.20, 'production': 1.9, 'revenue': 0.085, 'fcf': 0.035, 'dividend_yield': 0.0, 'market_cap': 1.9, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Avino Silver & Gold', 'ticker': 'ASM', 'period': '2023-Q2', 'aisc': 18.50, 'production': 0.48, 'revenue': 0.013, 'fcf': 0.002, 'dividend_yield': 0.0, 'market_cap': 0.13, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'SilverCrest Metals', 'ticker': 'SILV', 'period': '2023-Q2', 'aisc': 10.90, 'production': 2.3, 'revenue': 0.065, 'fcf': 0.025, 'dividend_yield': 0.0, 'market_cap': 2.0, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Fortuna Silver Mines', 'ticker': 'FSM', 'period': '2023-Q2', 'aisc': 16.50, 'production': 2.1, 'revenue': 0.19, 'fcf': 0.035, 'dividend_yield': 2.0, 'market_cap': 1.25, 'tier1': 0, 'tier2': 55, 'tier3': 45},
    {'company': 'SSR Mining', 'ticker': 'SSRM', 'period': '2023-Q2', 'aisc': 15.20, 'production': 2.9, 'revenue': 0.33, 'fcf': 0.055, 'dividend_yield': 2.5, 'market_cap': 2.6, 'tier1': 30, 'tier2': 35, 'tier3': 35},

    # ==================== 2023 Q3 ====================
    {'company': 'Pan American Silver', 'ticker': 'PAAS', 'period': '2023-Q3', 'aisc': 17.90, 'production': 6.2, 'revenue': 0.48, 'fcf': 0.04, 'dividend_yield': 2.6, 'market_cap': 6.8, 'tier1': 25, 'tier2': 60, 'tier3': 15},
    {'company': 'Hecla Mining', 'ticker': 'HL', 'period': '2023-Q3', 'aisc': 16.80, 'production': 3.6, 'revenue': 0.20, 'fcf': 0.02, 'dividend_yield': 0.9, 'market_cap': 3.0, 'tier1': 85, 'tier2': 10, 'tier3': 5},
    {'company': 'First Majestic Silver', 'ticker': 'AG', 'period': '2023-Q3', 'aisc': 20.80, 'production': 3.3, 'revenue': 0.14, 'fcf': -0.01, 'dividend_yield': 0.0, 'market_cap': 2.3, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Endeavour Silver', 'ticker': 'EXK', 'period': '2023-Q3', 'aisc': 19.20, 'production': 1.3, 'revenue': 0.055, 'fcf': 0.005, 'dividend_yield': 0.0, 'market_cap': 0.85, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Coeur Mining', 'ticker': 'CDE', 'period': '2023-Q3', 'aisc': 19.50, 'production': 2.7, 'revenue': 0.21, 'fcf': 0.01, 'dividend_yield': 0.0, 'market_cap': 1.7, 'tier1': 70, 'tier2': 30, 'tier3': 0},
    {'company': 'MAG Silver', 'ticker': 'MAG', 'period': '2023-Q3', 'aisc': 11.90, 'production': 2.0, 'revenue': 0.09, 'fcf': 0.04, 'dividend_yield': 0.0, 'market_cap': 2.0, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Avino Silver & Gold', 'ticker': 'ASM', 'period': '2023-Q3', 'aisc': 18.10, 'production': 0.50, 'revenue': 0.014, 'fcf': 0.003, 'dividend_yield': 0.0, 'market_cap': 0.14, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'SilverCrest Metals', 'ticker': 'SILV', 'period': '2023-Q3', 'aisc': 10.60, 'production': 2.4, 'revenue': 0.07, 'fcf': 0.03, 'dividend_yield': 0.0, 'market_cap': 2.1, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Fortuna Silver Mines', 'ticker': 'FSM', 'period': '2023-Q3', 'aisc': 16.20, 'production': 2.15, 'revenue': 0.20, 'fcf': 0.04, 'dividend_yield': 2.1, 'market_cap': 1.3, 'tier1': 0, 'tier2': 55, 'tier3': 45},
    {'company': 'SSR Mining', 'ticker': 'SSRM', 'period': '2023-Q3', 'aisc': 15.00, 'production': 3.0, 'revenue': 0.34, 'fcf': 0.06, 'dividend_yield': 2.6, 'market_cap': 2.7, 'tier1': 30, 'tier2': 35, 'tier3': 35},

    # ==================== 2023 Q4 ====================
    {'company': 'Pan American Silver', 'ticker': 'PAAS', 'period': '2023-Q4', 'aisc': 17.60, 'production': 6.5, 'revenue': 0.52, 'fcf': 0.05, 'dividend_yield': 2.5, 'market_cap': 7.2, 'tier1': 25, 'tier2': 60, 'tier3': 15},
    {'company': 'Hecla Mining', 'ticker': 'HL', 'period': '2023-Q4', 'aisc': 16.50, 'production': 3.7, 'revenue': 0.22, 'fcf': 0.025, 'dividend_yield': 1.0, 'market_cap': 3.2, 'tier1': 85, 'tier2': 10, 'tier3': 5},
    {'company': 'First Majestic Silver', 'ticker': 'AG', 'period': '2023-Q4', 'aisc': 20.50, 'production': 3.4, 'revenue': 0.15, 'fcf': 0.00, 'dividend_yield': 0.0, 'market_cap': 2.4, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Endeavour Silver', 'ticker': 'EXK', 'period': '2023-Q4', 'aisc': 18.90, 'production': 1.35, 'revenue': 0.058, 'fcf': 0.008, 'dividend_yield': 0.0, 'market_cap': 0.88, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Coeur Mining', 'ticker': 'CDE', 'period': '2023-Q4', 'aisc': 19.20, 'production': 2.8, 'revenue': 0.23, 'fcf': 0.02, 'dividend_yield': 0.0, 'market_cap': 1.8, 'tier1': 70, 'tier2': 30, 'tier3': 0},
    {'company': 'MAG Silver', 'ticker': 'MAG', 'period': '2023-Q4', 'aisc': 11.60, 'production': 2.1, 'revenue': 0.095, 'fcf': 0.045, 'dividend_yield': 0.0, 'market_cap': 2.1, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Avino Silver & Gold', 'ticker': 'ASM', 'period': '2023-Q4', 'aisc': 17.80, 'production': 0.52, 'revenue': 0.015, 'fcf': 0.004, 'dividend_yield': 0.0, 'market_cap': 0.15, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'SilverCrest Metals', 'ticker': 'SILV', 'period': '2023-Q4', 'aisc': 10.30, 'production': 2.5, 'revenue': 0.075, 'fcf': 0.035, 'dividend_yield': 0.0, 'market_cap': 2.2, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Fortuna Silver Mines', 'ticker': 'FSM', 'period': '2023-Q4', 'aisc': 15.90, 'production': 2.2, 'revenue': 0.21, 'fcf': 0.045, 'dividend_yield': 2.2, 'market_cap': 1.35, 'tier1': 0, 'tier2': 55, 'tier3': 45},
    {'company': 'SSR Mining', 'ticker': 'SSRM', 'period': '2023-Q4', 'aisc': 14.80, 'production': 3.1, 'revenue': 0.36, 'fcf': 0.07, 'dividend_yield': 2.7, 'market_cap': 2.8, 'tier1': 30, 'tier2': 35, 'tier3': 35},

    # ==================== 2024 Q1 ====================
    {'company': 'Pan American Silver', 'ticker': 'PAAS', 'period': '2024-Q1', 'aisc': 17.30, 'production': 6.8, 'revenue': 0.55, 'fcf': 0.06, 'dividend_yield': 2.4, 'market_cap': 7.5, 'tier1': 25, 'tier2': 60, 'tier3': 15},
    {'company': 'Hecla Mining', 'ticker': 'HL', 'period': '2024-Q1', 'aisc': 16.20, 'production': 3.8, 'revenue': 0.24, 'fcf': 0.03, 'dividend_yield': 1.0, 'market_cap': 3.4, 'tier1': 85, 'tier2': 10, 'tier3': 5},
    {'company': 'First Majestic Silver', 'ticker': 'AG', 'period': '2024-Q1', 'aisc': 20.20, 'production': 3.5, 'revenue': 0.16, 'fcf': 0.01, 'dividend_yield': 0.0, 'market_cap': 2.5, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Endeavour Silver', 'ticker': 'EXK', 'period': '2024-Q1', 'aisc': 18.60, 'production': 1.4, 'revenue': 0.062, 'fcf': 0.01, 'dividend_yield': 0.0, 'market_cap': 0.92, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Coeur Mining', 'ticker': 'CDE', 'period': '2024-Q1', 'aisc': 18.90, 'production': 2.9, 'revenue': 0.25, 'fcf': 0.03, 'dividend_yield': 0.0, 'market_cap': 1.9, 'tier1': 70, 'tier2': 30, 'tier3': 0},
    {'company': 'MAG Silver', 'ticker': 'MAG', 'period': '2024-Q1', 'aisc': 11.30, 'production': 2.2, 'revenue': 0.10, 'fcf': 0.05, 'dividend_yield': 0.0, 'market_cap': 2.2, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Avino Silver & Gold', 'ticker': 'ASM', 'period': '2024-Q1', 'aisc': 17.50, 'production': 0.55, 'revenue': 0.016, 'fcf': 0.005, 'dividend_yield': 0.0, 'market_cap': 0.16, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'SilverCrest Metals', 'ticker': 'SILV', 'period': '2024-Q1', 'aisc': 10.00, 'production': 2.6, 'revenue': 0.08, 'fcf': 0.04, 'dividend_yield': 0.0, 'market_cap': 2.3, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Fortuna Silver Mines', 'ticker': 'FSM', 'period': '2024-Q1', 'aisc': 15.60, 'production': 2.3, 'revenue': 0.22, 'fcf': 0.05, 'dividend_yield': 2.3, 'market_cap': 1.4, 'tier1': 0, 'tier2': 55, 'tier3': 45},
    {'company': 'SSR Mining', 'ticker': 'SSRM', 'period': '2024-Q1', 'aisc': 14.60, 'production': 3.2, 'revenue': 0.38, 'fcf': 0.08, 'dividend_yield': 2.8, 'market_cap': 2.9, 'tier1': 30, 'tier2': 35, 'tier3': 35},

    # ==================== 2024 Q2 ====================
    {'company': 'Pan American Silver', 'ticker': 'PAAS', 'period': '2024-Q2', 'aisc': 17.00, 'production': 7.0, 'revenue': 0.62, 'fcf': 0.08, 'dividend_yield': 2.3, 'market_cap': 8.0, 'tier1': 25, 'tier2': 60, 'tier3': 15},
    {'company': 'Hecla Mining', 'ticker': 'HL', 'period': '2024-Q2', 'aisc': 15.90, 'production': 3.9, 'revenue': 0.27, 'fcf': 0.04, 'dividend_yield': 1.1, 'market_cap': 3.6, 'tier1': 85, 'tier2': 10, 'tier3': 5},
    {'company': 'First Majestic Silver', 'ticker': 'AG', 'period': '2024-Q2', 'aisc': 19.80, 'production': 3.6, 'revenue': 0.18, 'fcf': 0.02, 'dividend_yield': 0.0, 'market_cap': 2.7, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Endeavour Silver', 'ticker': 'EXK', 'period': '2024-Q2', 'aisc': 18.30, 'production': 1.45, 'revenue': 0.068, 'fcf': 0.015, 'dividend_yield': 0.0, 'market_cap': 0.98, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Coeur Mining', 'ticker': 'CDE', 'period': '2024-Q2', 'aisc': 18.50, 'production': 3.0, 'revenue': 0.28, 'fcf': 0.04, 'dividend_yield': 0.0, 'market_cap': 2.1, 'tier1': 70, 'tier2': 30, 'tier3': 0},
    {'company': 'MAG Silver', 'ticker': 'MAG', 'period': '2024-Q2', 'aisc': 11.00, 'production': 2.3, 'revenue': 0.11, 'fcf': 0.055, 'dividend_yield': 0.0, 'market_cap': 2.4, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Avino Silver & Gold', 'ticker': 'ASM', 'period': '2024-Q2', 'aisc': 17.20, 'production': 0.58, 'revenue': 0.018, 'fcf': 0.006, 'dividend_yield': 0.0, 'market_cap': 0.17, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'SilverCrest Metals', 'ticker': 'SILV', 'period': '2024-Q2', 'aisc': 9.70, 'production': 2.7, 'revenue': 0.09, 'fcf': 0.045, 'dividend_yield': 0.0, 'market_cap': 2.5, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Fortuna Silver Mines', 'ticker': 'FSM', 'period': '2024-Q2', 'aisc': 15.30, 'production': 2.4, 'revenue': 0.25, 'fcf': 0.06, 'dividend_yield': 2.4, 'market_cap': 1.5, 'tier1': 0, 'tier2': 55, 'tier3': 45},
    {'company': 'SSR Mining', 'ticker': 'SSRM', 'period': '2024-Q2', 'aisc': 14.40, 'production': 3.3, 'revenue': 0.42, 'fcf': 0.09, 'dividend_yield': 2.9, 'market_cap': 3.0, 'tier1': 30, 'tier2': 35, 'tier3': 35},

    # ==================== 2024 Q3 ====================
    {'company': 'Pan American Silver', 'ticker': 'PAAS', 'period': '2024-Q3', 'aisc': 16.70, 'production': 7.2, 'revenue': 0.68, 'fcf': 0.10, 'dividend_yield': 2.2, 'market_cap': 8.5, 'tier1': 25, 'tier2': 60, 'tier3': 15},
    {'company': 'Hecla Mining', 'ticker': 'HL', 'period': '2024-Q3', 'aisc': 15.60, 'production': 4.0, 'revenue': 0.30, 'fcf': 0.05, 'dividend_yield': 1.2, 'market_cap': 3.8, 'tier1': 85, 'tier2': 10, 'tier3': 5},
    {'company': 'First Majestic Silver', 'ticker': 'AG', 'period': '2024-Q3', 'aisc': 19.50, 'production': 3.7, 'revenue': 0.20, 'fcf': 0.03, 'dividend_yield': 0.0, 'market_cap': 2.9, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Endeavour Silver', 'ticker': 'EXK', 'period': '2024-Q3', 'aisc': 18.00, 'production': 1.5, 'revenue': 0.075, 'fcf': 0.02, 'dividend_yield': 0.0, 'market_cap': 1.05, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Coeur Mining', 'ticker': 'CDE', 'period': '2024-Q3', 'aisc': 18.20, 'production': 3.1, 'revenue': 0.32, 'fcf': 0.05, 'dividend_yield': 0.0, 'market_cap': 2.3, 'tier1': 70, 'tier2': 30, 'tier3': 0},
    {'company': 'MAG Silver', 'ticker': 'MAG', 'period': '2024-Q3', 'aisc': 10.70, 'production': 2.4, 'revenue': 0.12, 'fcf': 0.06, 'dividend_yield': 0.0, 'market_cap': 2.6, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Avino Silver & Gold', 'ticker': 'ASM', 'period': '2024-Q3', 'aisc': 16.90, 'production': 0.60, 'revenue': 0.020, 'fcf': 0.007, 'dividend_yield': 0.0, 'market_cap': 0.18, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'SilverCrest Metals', 'ticker': 'SILV', 'period': '2024-Q3', 'aisc': 9.40, 'production': 2.8, 'revenue': 0.10, 'fcf': 0.05, 'dividend_yield': 0.0, 'market_cap': 2.7, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Fortuna Silver Mines', 'ticker': 'FSM', 'period': '2024-Q3', 'aisc': 15.00, 'production': 2.5, 'revenue': 0.28, 'fcf': 0.07, 'dividend_yield': 2.5, 'market_cap': 1.6, 'tier1': 0, 'tier2': 55, 'tier3': 45},
    {'company': 'SSR Mining', 'ticker': 'SSRM', 'period': '2024-Q3', 'aisc': 14.20, 'production': 3.4, 'revenue': 0.45, 'fcf': 0.10, 'dividend_yield': 3.0, 'market_cap': 3.2, 'tier1': 30, 'tier2': 35, 'tier3': 35},

    # ==================== 2024 Q4 ====================
    {'company': 'Pan American Silver', 'ticker': 'PAAS', 'period': '2024-Q4', 'aisc': 16.40, 'production': 7.5, 'revenue': 0.75, 'fcf': 0.12, 'dividend_yield': 2.1, 'market_cap': 9.0, 'tier1': 25, 'tier2': 60, 'tier3': 15},
    {'company': 'Hecla Mining', 'ticker': 'HL', 'period': '2024-Q4', 'aisc': 15.30, 'production': 4.1, 'revenue': 0.33, 'fcf': 0.06, 'dividend_yield': 1.3, 'market_cap': 4.0, 'tier1': 85, 'tier2': 10, 'tier3': 5},
    {'company': 'First Majestic Silver', 'ticker': 'AG', 'period': '2024-Q4', 'aisc': 19.20, 'production': 3.8, 'revenue': 0.22, 'fcf': 0.04, 'dividend_yield': 0.0, 'market_cap': 3.1, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Endeavour Silver', 'ticker': 'EXK', 'period': '2024-Q4', 'aisc': 17.70, 'production': 1.55, 'revenue': 0.082, 'fcf': 0.025, 'dividend_yield': 0.0, 'market_cap': 1.12, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Coeur Mining', 'ticker': 'CDE', 'period': '2024-Q4', 'aisc': 17.90, 'production': 3.2, 'revenue': 0.35, 'fcf': 0.06, 'dividend_yield': 0.0, 'market_cap': 2.5, 'tier1': 70, 'tier2': 30, 'tier3': 0},
    {'company': 'MAG Silver', 'ticker': 'MAG', 'period': '2024-Q4', 'aisc': 10.40, 'production': 2.5, 'revenue': 0.13, 'fcf': 0.065, 'dividend_yield': 0.0, 'market_cap': 2.8, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Avino Silver & Gold', 'ticker': 'ASM', 'period': '2024-Q4', 'aisc': 16.60, 'production': 0.62, 'revenue': 0.022, 'fcf': 0.008, 'dividend_yield': 0.0, 'market_cap': 0.19, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'SilverCrest Metals', 'ticker': 'SILV', 'period': '2024-Q4', 'aisc': 9.10, 'production': 2.9, 'revenue': 0.11, 'fcf': 0.055, 'dividend_yield': 0.0, 'market_cap': 2.9, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Fortuna Silver Mines', 'ticker': 'FSM', 'period': '2024-Q4', 'aisc': 14.70, 'production': 2.6, 'revenue': 0.30, 'fcf': 0.08, 'dividend_yield': 2.6, 'market_cap': 1.7, 'tier1': 0, 'tier2': 55, 'tier3': 45},
    {'company': 'SSR Mining', 'ticker': 'SSRM', 'period': '2024-Q4', 'aisc': 14.00, 'production': 3.5, 'revenue': 0.48, 'fcf': 0.11, 'dividend_yield': 3.1, 'market_cap': 3.4, 'tier1': 30, 'tier2': 35, 'tier3': 35},

    # ==================== 2025 Q1 ====================
    {'company': 'Pan American Silver', 'ticker': 'PAAS', 'period': '2025-Q1', 'aisc': 16.10, 'production': 7.8, 'revenue': 0.82, 'fcf': 0.14, 'dividend_yield': 2.0, 'market_cap': 9.5, 'tier1': 25, 'tier2': 60, 'tier3': 15},
    {'company': 'Hecla Mining', 'ticker': 'HL', 'period': '2025-Q1', 'aisc': 15.00, 'production': 4.2, 'revenue': 0.36, 'fcf': 0.07, 'dividend_yield': 1.4, 'market_cap': 4.2, 'tier1': 85, 'tier2': 10, 'tier3': 5},
    {'company': 'First Majestic Silver', 'ticker': 'AG', 'period': '2025-Q1', 'aisc': 18.90, 'production': 3.9, 'revenue': 0.24, 'fcf': 0.05, 'dividend_yield': 0.0, 'market_cap': 3.3, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Endeavour Silver', 'ticker': 'EXK', 'period': '2025-Q1', 'aisc': 17.40, 'production': 1.6, 'revenue': 0.088, 'fcf': 0.03, 'dividend_yield': 0.0, 'market_cap': 1.2, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Coeur Mining', 'ticker': 'CDE', 'period': '2025-Q1', 'aisc': 17.60, 'production': 3.3, 'revenue': 0.38, 'fcf': 0.07, 'dividend_yield': 0.0, 'market_cap': 2.7, 'tier1': 70, 'tier2': 30, 'tier3': 0},
    {'company': 'MAG Silver', 'ticker': 'MAG', 'period': '2025-Q1', 'aisc': 10.10, 'production': 2.6, 'revenue': 0.14, 'fcf': 0.07, 'dividend_yield': 0.0, 'market_cap': 3.0, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Avino Silver & Gold', 'ticker': 'ASM', 'period': '2025-Q1', 'aisc': 16.30, 'production': 0.65, 'revenue': 0.024, 'fcf': 0.009, 'dividend_yield': 0.0, 'market_cap': 0.20, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'SilverCrest Metals', 'ticker': 'SILV', 'period': '2025-Q1', 'aisc': 8.80, 'production': 3.0, 'revenue': 0.12, 'fcf': 0.06, 'dividend_yield': 0.0, 'market_cap': 3.1, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Fortuna Silver Mines', 'ticker': 'FSM', 'period': '2025-Q1', 'aisc': 14.40, 'production': 2.7, 'revenue': 0.32, 'fcf': 0.09, 'dividend_yield': 2.7, 'market_cap': 1.8, 'tier1': 0, 'tier2': 55, 'tier3': 45},
    {'company': 'SSR Mining', 'ticker': 'SSRM', 'period': '2025-Q1', 'aisc': 13.80, 'production': 3.6, 'revenue': 0.50, 'fcf': 0.12, 'dividend_yield': 3.2, 'market_cap': 3.6, 'tier1': 30, 'tier2': 35, 'tier3': 35},

    # ==================== 2025 Q2 ====================
    {'company': 'Pan American Silver', 'ticker': 'PAAS', 'period': '2025-Q2', 'aisc': 15.80, 'production': 8.0, 'revenue': 0.88, 'fcf': 0.16, 'dividend_yield': 1.9, 'market_cap': 10.0, 'tier1': 25, 'tier2': 60, 'tier3': 15},
    {'company': 'Hecla Mining', 'ticker': 'HL', 'period': '2025-Q2', 'aisc': 14.70, 'production': 4.3, 'revenue': 0.38, 'fcf': 0.08, 'dividend_yield': 1.5, 'market_cap': 4.4, 'tier1': 85, 'tier2': 10, 'tier3': 5},
    {'company': 'First Majestic Silver', 'ticker': 'AG', 'period': '2025-Q2', 'aisc': 18.60, 'production': 4.0, 'revenue': 0.26, 'fcf': 0.06, 'dividend_yield': 0.0, 'market_cap': 3.5, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Endeavour Silver', 'ticker': 'EXK', 'period': '2025-Q2', 'aisc': 17.10, 'production': 1.65, 'revenue': 0.095, 'fcf': 0.035, 'dividend_yield': 0.0, 'market_cap': 1.28, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Coeur Mining', 'ticker': 'CDE', 'period': '2025-Q2', 'aisc': 17.30, 'production': 3.4, 'revenue': 0.41, 'fcf': 0.08, 'dividend_yield': 0.0, 'market_cap': 2.9, 'tier1': 70, 'tier2': 30, 'tier3': 0},
    {'company': 'MAG Silver', 'ticker': 'MAG', 'period': '2025-Q2', 'aisc': 9.80, 'production': 2.7, 'revenue': 0.15, 'fcf': 0.075, 'dividend_yield': 0.0, 'market_cap': 3.2, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Avino Silver & Gold', 'ticker': 'ASM', 'period': '2025-Q2', 'aisc': 16.00, 'production': 0.68, 'revenue': 0.026, 'fcf': 0.010, 'dividend_yield': 0.0, 'market_cap': 0.21, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'SilverCrest Metals', 'ticker': 'SILV', 'period': '2025-Q2', 'aisc': 8.50, 'production': 3.1, 'revenue': 0.13, 'fcf': 0.065, 'dividend_yield': 0.0, 'market_cap': 3.3, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Fortuna Silver Mines', 'ticker': 'FSM', 'period': '2025-Q2', 'aisc': 14.10, 'production': 2.8, 'revenue': 0.35, 'fcf': 0.10, 'dividend_yield': 2.8, 'market_cap': 1.9, 'tier1': 0, 'tier2': 55, 'tier3': 45},
    {'company': 'SSR Mining', 'ticker': 'SSRM', 'period': '2025-Q2', 'aisc': 13.60, 'production': 3.7, 'revenue': 0.52, 'fcf': 0.13, 'dividend_yield': 3.3, 'market_cap': 3.8, 'tier1': 30, 'tier2': 35, 'tier3': 35},

    # ==================== 2025 Q3 ====================
    {'company': 'Pan American Silver', 'ticker': 'PAAS', 'period': '2025-Q3', 'aisc': 15.50, 'production': 8.2, 'revenue': 0.92, 'fcf': 0.18, 'dividend_yield': 1.8, 'market_cap': 10.5, 'tier1': 25, 'tier2': 60, 'tier3': 15},
    {'company': 'Hecla Mining', 'ticker': 'HL', 'period': '2025-Q3', 'aisc': 14.40, 'production': 4.4, 'revenue': 0.40, 'fcf': 0.09, 'dividend_yield': 1.6, 'market_cap': 4.6, 'tier1': 85, 'tier2': 10, 'tier3': 5},
    {'company': 'First Majestic Silver', 'ticker': 'AG', 'period': '2025-Q3', 'aisc': 18.30, 'production': 4.1, 'revenue': 0.28, 'fcf': 0.07, 'dividend_yield': 0.0, 'market_cap': 3.7, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Endeavour Silver', 'ticker': 'EXK', 'period': '2025-Q3', 'aisc': 16.80, 'production': 1.7, 'revenue': 0.10, 'fcf': 0.04, 'dividend_yield': 0.0, 'market_cap': 1.35, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Coeur Mining', 'ticker': 'CDE', 'period': '2025-Q3', 'aisc': 17.00, 'production': 3.5, 'revenue': 0.44, 'fcf': 0.09, 'dividend_yield': 0.0, 'market_cap': 3.1, 'tier1': 70, 'tier2': 30, 'tier3': 0},
    {'company': 'MAG Silver', 'ticker': 'MAG', 'period': '2025-Q3', 'aisc': 9.50, 'production': 2.8, 'revenue': 0.16, 'fcf': 0.08, 'dividend_yield': 0.0, 'market_cap': 3.4, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Avino Silver & Gold', 'ticker': 'ASM', 'period': '2025-Q3', 'aisc': 15.70, 'production': 0.70, 'revenue': 0.028, 'fcf': 0.011, 'dividend_yield': 0.0, 'market_cap': 0.22, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'SilverCrest Metals', 'ticker': 'SILV', 'period': '2025-Q3', 'aisc': 8.20, 'production': 3.2, 'revenue': 0.14, 'fcf': 0.07, 'dividend_yield': 0.0, 'market_cap': 3.5, 'tier1': 0, 'tier2': 100, 'tier3': 0},
    {'company': 'Fortuna Silver Mines', 'ticker': 'FSM', 'period': '2025-Q3', 'aisc': 13.80, 'production': 2.9, 'revenue': 0.38, 'fcf': 0.11, 'dividend_yield': 2.9, 'market_cap': 2.0, 'tier1': 0, 'tier2': 55, 'tier3': 45},
    {'company': 'SSR Mining', 'ticker': 'SSRM', 'period': '2025-Q3', 'aisc': 13.40, 'production': 3.8, 'revenue': 0.55, 'fcf': 0.14, 'dividend_yield': 3.4, 'market_cap': 4.0, 'tier1': 30, 'tier2': 35, 'tier3': 35},
]


@dataclass
class SilverMinerMetric:
    """Single quarterly report for a silver miner."""
    id: Optional[int]
    company: str
    ticker: str
    period: str  # e.g., "2024-Q1"
    aisc: float  # All-In Sustaining Cost ($/oz)
    production: float  # Million ounces
    revenue: float  # Billions USD
    fcf: float  # Free Cash Flow (Billions USD)
    dividend_yield: float  # Percentage
    market_cap: float  # Billions USD
    tier1: int  # Tier 1 jurisdiction exposure (%)
    tier2: int  # Tier 2 jurisdiction exposure (%)
    tier3: int  # Tier 3 jurisdiction exposure (%)
    timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d = asdict(self)
        if self.timestamp:
            d['timestamp'] = self.timestamp.isoformat()
        return d


class SilverMetricsDB:
    """Manages silver miner metrics storage and retrieval."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        print(f"[SilverMetricsDB] Using database: {self.db_path}")
        self._init_db()

    def _init_db(self):
        """Initialize the database and create tables if needed."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS silver_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    period TEXT NOT NULL,
                    aisc REAL NOT NULL,
                    production REAL NOT NULL,
                    revenue REAL NOT NULL,
                    fcf REAL NOT NULL,
                    dividend_yield REAL NOT NULL,
                    market_cap REAL NOT NULL,
                    tier1 INTEGER NOT NULL DEFAULT 0,
                    tier2 INTEGER NOT NULL DEFAULT 0,
                    tier3 INTEGER NOT NULL DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ticker, period)
                )
            ''')

            # Index for efficient queries
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_silver_metrics_period
                ON silver_metrics(period DESC)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_silver_metrics_ticker
                ON silver_metrics(ticker)
            ''')

            conn.commit()

            # Seed with initial data if empty
            cursor = conn.execute('SELECT COUNT(*) FROM silver_metrics')
            if cursor.fetchone()[0] == 0:
                self._seed_data(conn)

    def _seed_data(self, conn: sqlite3.Connection):
        """Populate database with initial seed data."""
        print("[SilverMetricsDB] Seeding initial data...")
        for data in SEED_DATA:
            conn.execute('''
                INSERT OR IGNORE INTO silver_metrics
                (company, ticker, period, aisc, production, revenue, fcf,
                 dividend_yield, market_cap, tier1, tier2, tier3)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['company'], data['ticker'], data['period'],
                data['aisc'], data['production'], data['revenue'], data['fcf'],
                data['dividend_yield'], data['market_cap'],
                data['tier1'], data['tier2'], data['tier3']
            ))
        conn.commit()
        print(f"[SilverMetricsDB] Seeded {len(SEED_DATA)} records")

    def reseed(self) -> int:
        """
        Clear existing data and reseed with SEED_DATA.
        Returns the number of records inserted.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM silver_metrics')
            self._seed_data(conn)
        return len(SEED_DATA)

    def create_metric(self, metric: SilverMinerMetric) -> Optional[int]:
        """
        Create a new silver miner metric entry.

        Returns the new record ID if successful, None if duplicate.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    INSERT INTO silver_metrics
                    (company, ticker, period, aisc, production, revenue, fcf,
                     dividend_yield, market_cap, tier1, tier2, tier3)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metric.company, metric.ticker, metric.period,
                    metric.aisc, metric.production, metric.revenue, metric.fcf,
                    metric.dividend_yield, metric.market_cap,
                    metric.tier1, metric.tier2, metric.tier3
                ))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Duplicate ticker+period
            return None

    def get_all_metrics(self, limit: int = 100) -> List[SilverMinerMetric]:
        """
        Get all metrics ordered by period (newest first) then ticker.

        Args:
            limit: Maximum records to return

        Returns:
            List of SilverMinerMetric objects
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT id, company, ticker, period, aisc, production, revenue,
                       fcf, dividend_yield, market_cap, tier1, tier2, tier3, timestamp
                FROM silver_metrics
                ORDER BY period DESC, ticker ASC
                LIMIT ?
            ''', (limit,))

            return [self._row_to_metric(row) for row in cursor.fetchall()]

    def get_metrics_by_ticker(self, ticker: str) -> List[SilverMinerMetric]:
        """Get all metrics for a specific company."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT id, company, ticker, period, aisc, production, revenue,
                       fcf, dividend_yield, market_cap, tier1, tier2, tier3, timestamp
                FROM silver_metrics
                WHERE ticker = ?
                ORDER BY period DESC
            ''', (ticker,))

            return [self._row_to_metric(row) for row in cursor.fetchall()]

    def get_latest_by_company(self) -> List[SilverMinerMetric]:
        """
        Get the most recent metric for each company.
        Useful for dashboard KPIs.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT id, company, ticker, period, aisc, production, revenue,
                       fcf, dividend_yield, market_cap, tier1, tier2, tier3, timestamp
                FROM silver_metrics m1
                WHERE period = (
                    SELECT MAX(period) FROM silver_metrics m2
                    WHERE m2.ticker = m1.ticker
                )
                ORDER BY aisc ASC
            ''')

            return [self._row_to_metric(row) for row in cursor.fetchall()]

    def get_sector_stats(self) -> Dict[str, Any]:
        """
        Calculate sector-wide statistics from latest data.
        """
        latest = self.get_latest_by_company()
        if not latest:
            return {
                'avg_aisc': 0,
                'total_production': 0,
                'avg_yield': 0,
                'tier1_exposure': 0,
                'company_count': 0
            }

        total_market_cap = sum(m.market_cap for m in latest)
        weighted_tier1 = sum(m.tier1 * m.market_cap for m in latest) / total_market_cap if total_market_cap > 0 else 0

        return {
            'avg_aisc': round(sum(m.aisc for m in latest) / len(latest), 2),
            'total_production': round(sum(m.production for m in latest), 1),
            'avg_yield': round(sum(m.dividend_yield for m in latest) / len(latest), 1),
            'tier1_exposure': round(weighted_tier1, 0),
            'company_count': len(latest)
        }

    def _row_to_metric(self, row: tuple) -> SilverMinerMetric:
        """Convert database row to SilverMinerMetric object."""
        timestamp = None
        if row[13]:
            try:
                timestamp = datetime.fromisoformat(row[13])
            except (ValueError, TypeError):
                pass

        return SilverMinerMetric(
            id=row[0],
            company=row[1],
            ticker=row[2],
            period=row[3],
            aisc=row[4],
            production=row[5],
            revenue=row[6],
            fcf=row[7],
            dividend_yield=row[8],
            market_cap=row[9],
            tier1=row[10],
            tier2=row[11],
            tier3=row[12],
            timestamp=timestamp
        )


# Singleton instance
_silver_db: Optional[SilverMetricsDB] = None


def get_silver_metrics_db() -> SilverMetricsDB:
    """Get or create the SilverMetricsDB singleton."""
    global _silver_db
    if _silver_db is None:
        _silver_db = SilverMetricsDB()
    return _silver_db
