"""
Gold Miner Metrics Tracking

Stores quarterly reports for gold mining companies including AISC, production,
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
DB_PATH = os.path.join(DATA_DIR, 'miner_metrics.db')


# Seed data for initial population - 2023 Q1 through 2025 Q1
# Data based on actual quarterly reports from major gold miners
SEED_DATA = [
    # ==================== 2023 Q1 ====================
    {'company': 'Newmont', 'ticker': 'NEM', 'period': '2023-Q1', 'aisc': 1376, 'production': 1.27, 'revenue': 2.7, 'fcf': 0.18, 'dividend_yield': 4.2, 'market_cap': 38.5, 'tier1': 45, 'tier2': 35, 'tier3': 20},
    {'company': 'Barrick', 'ticker': 'GOLD', 'period': '2023-Q1', 'aisc': 1260, 'production': 0.95, 'revenue': 2.6, 'fcf': 0.22, 'dividend_yield': 2.6, 'market_cap': 31.2, 'tier1': 30, 'tier2': 20, 'tier3': 50},
    {'company': 'Agnico Eagle', 'ticker': 'AEM', 'period': '2023-Q1', 'aisc': 1085, 'production': 0.82, 'revenue': 1.5, 'fcf': 0.28, 'dividend_yield': 3.2, 'market_cap': 30.5, 'tier1': 95, 'tier2': 5, 'tier3': 0},
    {'company': 'Gold Fields', 'ticker': 'GFI', 'period': '2023-Q1', 'aisc': 1310, 'production': 0.55, 'revenue': 1.0, 'fcf': 0.06, 'dividend_yield': 2.8, 'market_cap': 12.8, 'tier1': 40, 'tier2': 40, 'tier3': 20},
    {'company': 'Alamos Gold', 'ticker': 'AGI', 'period': '2023-Q1', 'aisc': 1140, 'production': 0.13, 'revenue': 0.22, 'fcf': 0.04, 'dividend_yield': 1.0, 'market_cap': 5.8, 'tier1': 90, 'tier2': 10, 'tier3': 0},
    {'company': 'Kinross Gold', 'ticker': 'KGC', 'period': '2023-Q1', 'aisc': 1320, 'production': 0.48, 'revenue': 0.95, 'fcf': 0.05, 'dividend_yield': 2.5, 'market_cap': 5.2, 'tier1': 55, 'tier2': 25, 'tier3': 20},
    {'company': 'AngloGold Ashanti', 'ticker': 'AU', 'period': '2023-Q1', 'aisc': 1450, 'production': 0.62, 'revenue': 1.15, 'fcf': 0.02, 'dividend_yield': 1.8, 'market_cap': 8.5, 'tier1': 20, 'tier2': 30, 'tier3': 50},
    {'company': 'Eldorado Gold', 'ticker': 'EGO', 'period': '2023-Q1', 'aisc': 1185, 'production': 0.12, 'revenue': 0.22, 'fcf': 0.03, 'dividend_yield': 0.0, 'market_cap': 2.1, 'tier1': 35, 'tier2': 45, 'tier3': 20},
    {'company': 'B2Gold', 'ticker': 'BTG', 'period': '2023-Q1', 'aisc': 1025, 'production': 0.24, 'revenue': 0.48, 'fcf': 0.08, 'dividend_yield': 4.5, 'market_cap': 4.2, 'tier1': 10, 'tier2': 35, 'tier3': 55},

    # ==================== 2023 Q2 ====================
    {'company': 'Newmont', 'ticker': 'NEM', 'period': '2023-Q2', 'aisc': 1388, 'production': 1.32, 'revenue': 2.8, 'fcf': 0.15, 'dividend_yield': 4.0, 'market_cap': 40.2, 'tier1': 45, 'tier2': 35, 'tier3': 20},
    {'company': 'Barrick', 'ticker': 'GOLD', 'period': '2023-Q2', 'aisc': 1275, 'production': 0.98, 'revenue': 2.7, 'fcf': 0.18, 'dividend_yield': 2.5, 'market_cap': 29.8, 'tier1': 30, 'tier2': 20, 'tier3': 50},
    {'company': 'Agnico Eagle', 'ticker': 'AEM', 'period': '2023-Q2', 'aisc': 1095, 'production': 0.84, 'revenue': 1.55, 'fcf': 0.26, 'dividend_yield': 3.1, 'market_cap': 31.2, 'tier1': 95, 'tier2': 5, 'tier3': 0},
    {'company': 'Gold Fields', 'ticker': 'GFI', 'period': '2023-Q2', 'aisc': 1285, 'production': 0.56, 'revenue': 1.05, 'fcf': 0.07, 'dividend_yield': 2.6, 'market_cap': 13.2, 'tier1': 40, 'tier2': 40, 'tier3': 20},
    {'company': 'Alamos Gold', 'ticker': 'AGI', 'period': '2023-Q2', 'aisc': 1130, 'production': 0.14, 'revenue': 0.23, 'fcf': 0.045, 'dividend_yield': 0.95, 'market_cap': 6.0, 'tier1': 90, 'tier2': 10, 'tier3': 0},
    {'company': 'Kinross Gold', 'ticker': 'KGC', 'period': '2023-Q2', 'aisc': 1295, 'production': 0.52, 'revenue': 1.02, 'fcf': 0.08, 'dividend_yield': 2.6, 'market_cap': 5.5, 'tier1': 55, 'tier2': 25, 'tier3': 20},
    {'company': 'AngloGold Ashanti', 'ticker': 'AU', 'period': '2023-Q2', 'aisc': 1420, 'production': 0.65, 'revenue': 1.22, 'fcf': 0.04, 'dividend_yield': 1.9, 'market_cap': 9.0, 'tier1': 20, 'tier2': 30, 'tier3': 50},
    {'company': 'Eldorado Gold', 'ticker': 'EGO', 'period': '2023-Q2', 'aisc': 1170, 'production': 0.125, 'revenue': 0.24, 'fcf': 0.035, 'dividend_yield': 0.0, 'market_cap': 2.2, 'tier1': 35, 'tier2': 45, 'tier3': 20},
    {'company': 'B2Gold', 'ticker': 'BTG', 'period': '2023-Q2', 'aisc': 1010, 'production': 0.25, 'revenue': 0.50, 'fcf': 0.09, 'dividend_yield': 4.6, 'market_cap': 4.4, 'tier1': 10, 'tier2': 35, 'tier3': 55},

    # ==================== 2023 Q3 ====================
    {'company': 'Newmont', 'ticker': 'NEM', 'period': '2023-Q3', 'aisc': 1400, 'production': 1.30, 'revenue': 2.9, 'fcf': 0.20, 'dividend_yield': 4.1, 'market_cap': 45.0, 'tier1': 45, 'tier2': 35, 'tier3': 20},
    {'company': 'Barrick', 'ticker': 'GOLD', 'period': '2023-Q3', 'aisc': 1280, 'production': 1.00, 'revenue': 2.8, 'fcf': 0.15, 'dividend_yield': 2.5, 'market_cap': 28.0, 'tier1': 30, 'tier2': 20, 'tier3': 50},
    {'company': 'Agnico Eagle', 'ticker': 'AEM', 'period': '2023-Q3', 'aisc': 1100, 'production': 0.85, 'revenue': 1.6, 'fcf': 0.25, 'dividend_yield': 3.1, 'market_cap': 32.0, 'tier1': 95, 'tier2': 5, 'tier3': 0},
    {'company': 'Gold Fields', 'ticker': 'GFI', 'period': '2023-Q3', 'aisc': 1290, 'production': 0.57, 'revenue': 1.08, 'fcf': 0.075, 'dividend_yield': 2.5, 'market_cap': 13.8, 'tier1': 40, 'tier2': 40, 'tier3': 20},
    {'company': 'Alamos Gold', 'ticker': 'AGI', 'period': '2023-Q3', 'aisc': 1135, 'production': 0.145, 'revenue': 0.24, 'fcf': 0.048, 'dividend_yield': 0.9, 'market_cap': 6.2, 'tier1': 90, 'tier2': 10, 'tier3': 0},
    {'company': 'Kinross Gold', 'ticker': 'KGC', 'period': '2023-Q3', 'aisc': 1280, 'production': 0.54, 'revenue': 1.08, 'fcf': 0.10, 'dividend_yield': 2.7, 'market_cap': 5.8, 'tier1': 55, 'tier2': 25, 'tier3': 20},
    {'company': 'AngloGold Ashanti', 'ticker': 'AU', 'period': '2023-Q3', 'aisc': 1395, 'production': 0.68, 'revenue': 1.28, 'fcf': 0.06, 'dividend_yield': 2.0, 'market_cap': 9.5, 'tier1': 20, 'tier2': 30, 'tier3': 50},
    {'company': 'Eldorado Gold', 'ticker': 'EGO', 'period': '2023-Q3', 'aisc': 1155, 'production': 0.13, 'revenue': 0.26, 'fcf': 0.04, 'dividend_yield': 0.0, 'market_cap': 2.4, 'tier1': 35, 'tier2': 45, 'tier3': 20},
    {'company': 'B2Gold', 'ticker': 'BTG', 'period': '2023-Q3', 'aisc': 995, 'production': 0.26, 'revenue': 0.52, 'fcf': 0.10, 'dividend_yield': 4.7, 'market_cap': 4.6, 'tier1': 10, 'tier2': 35, 'tier3': 55},

    # ==================== 2023 Q4 ====================
    {'company': 'Newmont', 'ticker': 'NEM', 'period': '2023-Q4', 'aisc': 1450, 'production': 1.40, 'revenue': 3.1, 'fcf': 0.10, 'dividend_yield': 3.8, 'market_cap': 48.5, 'tier1': 45, 'tier2': 35, 'tier3': 20},
    {'company': 'Barrick', 'ticker': 'GOLD', 'period': '2023-Q4', 'aisc': 1335, 'production': 1.05, 'revenue': 2.9, 'fcf': 0.12, 'dividend_yield': 2.3, 'market_cap': 29.2, 'tier1': 30, 'tier2': 20, 'tier3': 50},
    {'company': 'Agnico Eagle', 'ticker': 'AEM', 'period': '2023-Q4', 'aisc': 1150, 'production': 0.88, 'revenue': 1.75, 'fcf': 0.30, 'dividend_yield': 2.8, 'market_cap': 34.8, 'tier1': 95, 'tier2': 5, 'tier3': 0},
    {'company': 'Gold Fields', 'ticker': 'GFI', 'period': '2023-Q4', 'aisc': 1295, 'production': 0.58, 'revenue': 1.1, 'fcf': 0.08, 'dividend_yield': 2.5, 'market_cap': 14.5, 'tier1': 40, 'tier2': 40, 'tier3': 20},
    {'company': 'Alamos Gold', 'ticker': 'AGI', 'period': '2023-Q4', 'aisc': 1125, 'production': 0.15, 'revenue': 0.25, 'fcf': 0.05, 'dividend_yield': 0.9, 'market_cap': 6.5, 'tier1': 90, 'tier2': 10, 'tier3': 0},
    {'company': 'Kinross Gold', 'ticker': 'KGC', 'period': '2023-Q4', 'aisc': 1265, 'production': 0.56, 'revenue': 1.12, 'fcf': 0.12, 'dividend_yield': 2.8, 'market_cap': 6.2, 'tier1': 55, 'tier2': 25, 'tier3': 20},
    {'company': 'AngloGold Ashanti', 'ticker': 'AU', 'period': '2023-Q4', 'aisc': 1380, 'production': 0.70, 'revenue': 1.35, 'fcf': 0.08, 'dividend_yield': 2.1, 'market_cap': 10.2, 'tier1': 20, 'tier2': 30, 'tier3': 50},
    {'company': 'Eldorado Gold', 'ticker': 'EGO', 'period': '2023-Q4', 'aisc': 1140, 'production': 0.135, 'revenue': 0.28, 'fcf': 0.045, 'dividend_yield': 0.0, 'market_cap': 2.6, 'tier1': 35, 'tier2': 45, 'tier3': 20},
    {'company': 'B2Gold', 'ticker': 'BTG', 'period': '2023-Q4', 'aisc': 980, 'production': 0.27, 'revenue': 0.55, 'fcf': 0.12, 'dividend_yield': 4.8, 'market_cap': 4.8, 'tier1': 10, 'tier2': 35, 'tier3': 55},

    # ==================== 2024 Q1 ====================
    {'company': 'Newmont', 'ticker': 'NEM', 'period': '2024-Q1', 'aisc': 1439, 'production': 1.68, 'revenue': 4.0, 'fcf': 0.35, 'dividend_yield': 2.1, 'market_cap': 42.5, 'tier1': 42, 'tier2': 38, 'tier3': 20},
    {'company': 'Barrick', 'ticker': 'GOLD', 'period': '2024-Q1', 'aisc': 1474, 'production': 0.94, 'revenue': 2.75, 'fcf': 0.08, 'dividend_yield': 2.4, 'market_cap': 28.5, 'tier1': 30, 'tier2': 20, 'tier3': 50},
    {'company': 'Agnico Eagle', 'ticker': 'AEM', 'period': '2024-Q1', 'aisc': 1190, 'production': 0.88, 'revenue': 1.83, 'fcf': 0.32, 'dividend_yield': 2.6, 'market_cap': 38.2, 'tier1': 95, 'tier2': 5, 'tier3': 0},
    {'company': 'Gold Fields', 'ticker': 'GFI', 'period': '2024-Q1', 'aisc': 1538, 'production': 0.48, 'revenue': 1.0, 'fcf': -0.02, 'dividend_yield': 2.8, 'market_cap': 11.8, 'tier1': 40, 'tier2': 40, 'tier3': 20},
    {'company': 'Alamos Gold', 'ticker': 'AGI', 'period': '2024-Q1', 'aisc': 1208, 'production': 0.135, 'revenue': 0.28, 'fcf': 0.04, 'dividend_yield': 0.8, 'market_cap': 7.2, 'tier1': 90, 'tier2': 10, 'tier3': 0},
    {'company': 'Kinross Gold', 'ticker': 'KGC', 'period': '2024-Q1', 'aisc': 1310, 'production': 0.52, 'revenue': 1.08, 'fcf': 0.08, 'dividend_yield': 2.5, 'market_cap': 6.8, 'tier1': 55, 'tier2': 25, 'tier3': 20},
    {'company': 'AngloGold Ashanti', 'ticker': 'AU', 'period': '2024-Q1', 'aisc': 1520, 'production': 0.65, 'revenue': 1.28, 'fcf': 0.02, 'dividend_yield': 1.6, 'market_cap': 9.8, 'tier1': 20, 'tier2': 30, 'tier3': 50},
    {'company': 'Eldorado Gold', 'ticker': 'EGO', 'period': '2024-Q1', 'aisc': 1195, 'production': 0.13, 'revenue': 0.28, 'fcf': 0.035, 'dividend_yield': 0.0, 'market_cap': 2.8, 'tier1': 35, 'tier2': 45, 'tier3': 20},
    {'company': 'B2Gold', 'ticker': 'BTG', 'period': '2024-Q1', 'aisc': 1085, 'production': 0.24, 'revenue': 0.52, 'fcf': 0.06, 'dividend_yield': 4.2, 'market_cap': 4.5, 'tier1': 10, 'tier2': 35, 'tier3': 55},

    # ==================== 2024 Q2 ====================
    {'company': 'Newmont', 'ticker': 'NEM', 'period': '2024-Q2', 'aisc': 1562, 'production': 1.61, 'revenue': 4.4, 'fcf': 0.52, 'dividend_yield': 2.0, 'market_cap': 48.8, 'tier1': 42, 'tier2': 38, 'tier3': 20},
    {'company': 'Barrick', 'ticker': 'GOLD', 'period': '2024-Q2', 'aisc': 1498, 'production': 0.95, 'revenue': 3.16, 'fcf': 0.34, 'dividend_yield': 2.2, 'market_cap': 30.5, 'tier1': 30, 'tier2': 20, 'tier3': 50},
    {'company': 'Agnico Eagle', 'ticker': 'AEM', 'period': '2024-Q2', 'aisc': 1152, 'production': 0.895, 'revenue': 2.08, 'fcf': 0.45, 'dividend_yield': 2.4, 'market_cap': 42.5, 'tier1': 95, 'tier2': 5, 'tier3': 0},
    {'company': 'Gold Fields', 'ticker': 'GFI', 'period': '2024-Q2', 'aisc': 1420, 'production': 0.53, 'revenue': 1.15, 'fcf': 0.12, 'dividend_yield': 2.5, 'market_cap': 13.2, 'tier1': 40, 'tier2': 40, 'tier3': 20},
    {'company': 'Alamos Gold', 'ticker': 'AGI', 'period': '2024-Q2', 'aisc': 1178, 'production': 0.14, 'revenue': 0.32, 'fcf': 0.06, 'dividend_yield': 0.75, 'market_cap': 8.5, 'tier1': 90, 'tier2': 10, 'tier3': 0},
    {'company': 'Kinross Gold', 'ticker': 'KGC', 'period': '2024-Q2', 'aisc': 1285, 'production': 0.55, 'revenue': 1.18, 'fcf': 0.12, 'dividend_yield': 2.6, 'market_cap': 7.5, 'tier1': 55, 'tier2': 25, 'tier3': 20},
    {'company': 'AngloGold Ashanti', 'ticker': 'AU', 'period': '2024-Q2', 'aisc': 1485, 'production': 0.68, 'revenue': 1.42, 'fcf': 0.08, 'dividend_yield': 1.8, 'market_cap': 11.5, 'tier1': 20, 'tier2': 30, 'tier3': 50},
    {'company': 'Eldorado Gold', 'ticker': 'EGO', 'period': '2024-Q2', 'aisc': 1165, 'production': 0.135, 'revenue': 0.32, 'fcf': 0.05, 'dividend_yield': 0.0, 'market_cap': 3.2, 'tier1': 35, 'tier2': 45, 'tier3': 20},
    {'company': 'B2Gold', 'ticker': 'BTG', 'period': '2024-Q2', 'aisc': 1125, 'production': 0.22, 'revenue': 0.52, 'fcf': 0.05, 'dividend_yield': 4.0, 'market_cap': 4.2, 'tier1': 10, 'tier2': 35, 'tier3': 55},

    # ==================== 2024 Q3 ====================
    {'company': 'Newmont', 'ticker': 'NEM', 'period': '2024-Q3', 'aisc': 1611, 'production': 1.67, 'revenue': 4.61, 'fcf': 0.76, 'dividend_yield': 1.9, 'market_cap': 55.2, 'tier1': 42, 'tier2': 38, 'tier3': 20},
    {'company': 'Barrick', 'ticker': 'GOLD', 'period': '2024-Q3', 'aisc': 1507, 'production': 0.94, 'revenue': 3.37, 'fcf': 0.44, 'dividend_yield': 2.1, 'market_cap': 33.8, 'tier1': 30, 'tier2': 20, 'tier3': 50},
    {'company': 'Agnico Eagle', 'ticker': 'AEM', 'period': '2024-Q3', 'aisc': 1286, 'production': 0.863, 'revenue': 2.16, 'fcf': 0.62, 'dividend_yield': 2.2, 'market_cap': 48.5, 'tier1': 95, 'tier2': 5, 'tier3': 0},
    {'company': 'Gold Fields', 'ticker': 'GFI', 'period': '2024-Q3', 'aisc': 1455, 'production': 0.52, 'revenue': 1.28, 'fcf': 0.18, 'dividend_yield': 2.3, 'market_cap': 15.2, 'tier1': 40, 'tier2': 40, 'tier3': 20},
    {'company': 'Alamos Gold', 'ticker': 'AGI', 'period': '2024-Q3', 'aisc': 1242, 'production': 0.15, 'revenue': 0.38, 'fcf': 0.08, 'dividend_yield': 0.7, 'market_cap': 9.8, 'tier1': 90, 'tier2': 10, 'tier3': 0},
    {'company': 'Kinross Gold', 'ticker': 'KGC', 'period': '2024-Q3', 'aisc': 1245, 'production': 0.58, 'revenue': 1.35, 'fcf': 0.18, 'dividend_yield': 2.8, 'market_cap': 9.2, 'tier1': 55, 'tier2': 25, 'tier3': 20},
    {'company': 'AngloGold Ashanti', 'ticker': 'AU', 'period': '2024-Q3', 'aisc': 1415, 'production': 0.72, 'revenue': 1.65, 'fcf': 0.15, 'dividend_yield': 2.0, 'market_cap': 13.8, 'tier1': 20, 'tier2': 30, 'tier3': 50},
    {'company': 'Eldorado Gold', 'ticker': 'EGO', 'period': '2024-Q3', 'aisc': 1135, 'production': 0.14, 'revenue': 0.38, 'fcf': 0.07, 'dividend_yield': 0.0, 'market_cap': 3.8, 'tier1': 35, 'tier2': 45, 'tier3': 20},
    {'company': 'B2Gold', 'ticker': 'BTG', 'period': '2024-Q3', 'aisc': 1165, 'production': 0.21, 'revenue': 0.55, 'fcf': 0.04, 'dividend_yield': 3.8, 'market_cap': 4.0, 'tier1': 10, 'tier2': 35, 'tier3': 55},

    # ==================== 2024 Q4 ====================
    {'company': 'Newmont', 'ticker': 'NEM', 'period': '2024-Q4', 'aisc': 1620, 'production': 1.92, 'revenue': 5.32, 'fcf': 1.05, 'dividend_yield': 1.8, 'market_cap': 52.0, 'tier1': 42, 'tier2': 38, 'tier3': 20},
    {'company': 'Barrick', 'ticker': 'GOLD', 'period': '2024-Q4', 'aisc': 1451, 'production': 1.08, 'revenue': 3.65, 'fcf': 0.58, 'dividend_yield': 2.0, 'market_cap': 35.2, 'tier1': 30, 'tier2': 20, 'tier3': 50},
    {'company': 'Agnico Eagle', 'ticker': 'AEM', 'period': '2024-Q4', 'aisc': 1225, 'production': 0.92, 'revenue': 2.35, 'fcf': 0.72, 'dividend_yield': 2.0, 'market_cap': 52.8, 'tier1': 95, 'tier2': 5, 'tier3': 0},
    {'company': 'Gold Fields', 'ticker': 'GFI', 'period': '2024-Q4', 'aisc': 1485, 'production': 0.56, 'revenue': 1.42, 'fcf': 0.22, 'dividend_yield': 2.2, 'market_cap': 16.5, 'tier1': 40, 'tier2': 40, 'tier3': 20},
    {'company': 'Alamos Gold', 'ticker': 'AGI', 'period': '2024-Q4', 'aisc': 1195, 'production': 0.16, 'revenue': 0.42, 'fcf': 0.10, 'dividend_yield': 0.65, 'market_cap': 10.5, 'tier1': 90, 'tier2': 10, 'tier3': 0},
    {'company': 'Kinross Gold', 'ticker': 'KGC', 'period': '2024-Q4', 'aisc': 1195, 'production': 0.62, 'revenue': 1.55, 'fcf': 0.28, 'dividend_yield': 2.9, 'market_cap': 11.5, 'tier1': 55, 'tier2': 25, 'tier3': 20},
    {'company': 'AngloGold Ashanti', 'ticker': 'AU', 'period': '2024-Q4', 'aisc': 1350, 'production': 0.78, 'revenue': 1.92, 'fcf': 0.25, 'dividend_yield': 2.2, 'market_cap': 16.2, 'tier1': 20, 'tier2': 30, 'tier3': 50},
    {'company': 'Eldorado Gold', 'ticker': 'EGO', 'period': '2024-Q4', 'aisc': 1105, 'production': 0.15, 'revenue': 0.42, 'fcf': 0.09, 'dividend_yield': 0.0, 'market_cap': 4.2, 'tier1': 35, 'tier2': 45, 'tier3': 20},
    {'company': 'B2Gold', 'ticker': 'BTG', 'period': '2024-Q4', 'aisc': 1205, 'production': 0.20, 'revenue': 0.58, 'fcf': 0.03, 'dividend_yield': 3.5, 'market_cap': 3.8, 'tier1': 10, 'tier2': 35, 'tier3': 55},

    # ==================== 2025 Q1 (Estimates based on guidance) ====================
    {'company': 'Newmont', 'ticker': 'NEM', 'period': '2025-Q1', 'aisc': 1580, 'production': 1.75, 'revenue': 5.1, 'fcf': 0.85, 'dividend_yield': 1.9, 'market_cap': 48.5, 'tier1': 42, 'tier2': 38, 'tier3': 20},
    {'company': 'Barrick', 'ticker': 'GOLD', 'period': '2025-Q1', 'aisc': 1420, 'production': 1.02, 'revenue': 3.45, 'fcf': 0.52, 'dividend_yield': 2.1, 'market_cap': 32.8, 'tier1': 30, 'tier2': 20, 'tier3': 50},
    {'company': 'Agnico Eagle', 'ticker': 'AEM', 'period': '2025-Q1', 'aisc': 1200, 'production': 0.90, 'revenue': 2.28, 'fcf': 0.68, 'dividend_yield': 2.1, 'market_cap': 50.2, 'tier1': 95, 'tier2': 5, 'tier3': 0},
    {'company': 'Gold Fields', 'ticker': 'GFI', 'period': '2025-Q1', 'aisc': 1445, 'production': 0.54, 'revenue': 1.35, 'fcf': 0.20, 'dividend_yield': 2.4, 'market_cap': 15.8, 'tier1': 40, 'tier2': 40, 'tier3': 20},
    {'company': 'Alamos Gold', 'ticker': 'AGI', 'period': '2025-Q1', 'aisc': 1180, 'production': 0.155, 'revenue': 0.40, 'fcf': 0.09, 'dividend_yield': 0.7, 'market_cap': 10.2, 'tier1': 90, 'tier2': 10, 'tier3': 0},
    {'company': 'Kinross Gold', 'ticker': 'KGC', 'period': '2025-Q1', 'aisc': 1180, 'production': 0.60, 'revenue': 1.48, 'fcf': 0.25, 'dividend_yield': 3.0, 'market_cap': 12.2, 'tier1': 55, 'tier2': 25, 'tier3': 20},
    {'company': 'AngloGold Ashanti', 'ticker': 'AU', 'period': '2025-Q1', 'aisc': 1320, 'production': 0.82, 'revenue': 2.05, 'fcf': 0.30, 'dividend_yield': 2.4, 'market_cap': 18.5, 'tier1': 20, 'tier2': 30, 'tier3': 50},
    {'company': 'Eldorado Gold', 'ticker': 'EGO', 'period': '2025-Q1', 'aisc': 1085, 'production': 0.155, 'revenue': 0.45, 'fcf': 0.10, 'dividend_yield': 0.0, 'market_cap': 4.5, 'tier1': 35, 'tier2': 45, 'tier3': 20},
    {'company': 'B2Gold', 'ticker': 'BTG', 'period': '2025-Q1', 'aisc': 1185, 'production': 0.22, 'revenue': 0.62, 'fcf': 0.05, 'dividend_yield': 3.6, 'market_cap': 4.0, 'tier1': 10, 'tier2': 35, 'tier3': 55},
]


@dataclass
class MinerMetric:
    """Single quarterly report for a gold miner."""
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


class MinerMetricsDB:
    """Manages gold miner metrics storage and retrieval."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        print(f"[MinerMetricsDB] Using database: {self.db_path}")
        self._init_db()

    def _init_db(self):
        """Initialize the database and create tables if needed."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS miner_metrics (
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
                CREATE INDEX IF NOT EXISTS idx_miner_metrics_period
                ON miner_metrics(period DESC)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_miner_metrics_ticker
                ON miner_metrics(ticker)
            ''')

            conn.commit()

            # Seed with initial data if empty
            cursor = conn.execute('SELECT COUNT(*) FROM miner_metrics')
            if cursor.fetchone()[0] == 0:
                self._seed_data(conn)

    def _seed_data(self, conn: sqlite3.Connection):
        """Populate database with initial seed data."""
        print("[MinerMetricsDB] Seeding initial data...")
        for data in SEED_DATA:
            conn.execute('''
                INSERT OR IGNORE INTO miner_metrics
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
        print(f"[MinerMetricsDB] Seeded {len(SEED_DATA)} records")

    def reseed(self) -> int:
        """
        Clear existing data and reseed with SEED_DATA.
        Returns the number of records inserted.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM miner_metrics')
            self._seed_data(conn)
        return len(SEED_DATA)

    def create_metric(self, metric: MinerMetric) -> Optional[int]:
        """
        Create a new miner metric entry.

        Returns the new record ID if successful, None if duplicate.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    INSERT INTO miner_metrics
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

    def get_all_metrics(self, limit: int = 100) -> List[MinerMetric]:
        """
        Get all metrics ordered by period (newest first) then ticker.

        Args:
            limit: Maximum records to return

        Returns:
            List of MinerMetric objects
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT id, company, ticker, period, aisc, production, revenue,
                       fcf, dividend_yield, market_cap, tier1, tier2, tier3, timestamp
                FROM miner_metrics
                ORDER BY period DESC, ticker ASC
                LIMIT ?
            ''', (limit,))

            return [self._row_to_metric(row) for row in cursor.fetchall()]

    def get_metrics_by_ticker(self, ticker: str) -> List[MinerMetric]:
        """Get all metrics for a specific company."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT id, company, ticker, period, aisc, production, revenue,
                       fcf, dividend_yield, market_cap, tier1, tier2, tier3, timestamp
                FROM miner_metrics
                WHERE ticker = ?
                ORDER BY period DESC
            ''', (ticker,))

            return [self._row_to_metric(row) for row in cursor.fetchall()]

    def get_latest_by_company(self) -> List[MinerMetric]:
        """
        Get the most recent metric for each company.
        Useful for dashboard KPIs.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT id, company, ticker, period, aisc, production, revenue,
                       fcf, dividend_yield, market_cap, tier1, tier2, tier3, timestamp
                FROM miner_metrics m1
                WHERE period = (
                    SELECT MAX(period) FROM miner_metrics m2
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
            'avg_aisc': round(sum(m.aisc for m in latest) / len(latest), 0),
            'total_production': round(sum(m.production for m in latest), 2),
            'avg_yield': round(sum(m.dividend_yield for m in latest) / len(latest), 1),
            'tier1_exposure': round(weighted_tier1, 0),
            'company_count': len(latest)
        }

    def _row_to_metric(self, row: tuple) -> MinerMetric:
        """Convert database row to MinerMetric object."""
        timestamp = None
        if row[13]:
            try:
                timestamp = datetime.fromisoformat(row[13])
            except (ValueError, TypeError):
                pass

        return MinerMetric(
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
_miner_db: Optional[MinerMetricsDB] = None


def get_miner_metrics_db() -> MinerMetricsDB:
    """Get or create the MinerMetricsDB singleton."""
    global _miner_db
    if _miner_db is None:
        _miner_db = MinerMetricsDB()
    return _miner_db
