#!/usr/bin/env python3
"""
Net Domestic Value (NDV) V5.0 Absolute Holism Global Scraper
Author: Lead Systems Architect & Biophysical Economist
Version: 5.0: Supply Chain Entropy, Metabolic human decay, and Epistemic decay

This module scrapes indicators for all 190+ sovereign nations, routes them
through the AbsoluteHolismKernel, and outputs a standardized global_sovereign_ledger.csv.
"""

import urllib.request
import json
import csv
import logging
import os
from typing import Dict, List, Optional

# Enterprise Logging Configuration
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("NDV_Holism_Scraper")

# Pre-seeded fallback data for major countries for EROI, internet, FIRE, trade, health, and R&D
FALLBACK_GLOBAL_DATA = {
    "USA": {"Country_Name": "United States", "GDP_USD": 27.36e12, "Population": 335000000, "Gini": 41.5, "PM25": 7.4, "Forest_SqKm": 3097900.0, "Energy_Imports_Pct": -5.2, "Internet_Users_Pct": 91.8, "Fire_Pct": 0.200, "Imports_Pct": 14.0, "Exports_Pct": 11.0, "Health_Exp_Pct": 16.6, "RD_Exp_Pct": 3.5},
    "CHN": {"Country_Name": "China", "GDP_USD": 17.79e12, "Population": 1410000000, "Gini": 38.2, "PM25": 35.5, "Forest_SqKm": 2199700.0, "Energy_Imports_Pct": 15.6, "Internet_Users_Pct": 76.4, "Fire_Pct": 0.075, "Imports_Pct": 17.0, "Exports_Pct": 20.0, "Health_Exp_Pct": 5.4, "RD_Exp_Pct": 2.4},
    "JPN": {"Country_Name": "Japan", "GDP_USD": 4.21e12, "Population": 125000000, "Gini": 32.9, "PM25": 11.2, "Forest_SqKm": 249350.0, "Energy_Imports_Pct": 94.2, "Internet_Users_Pct": 93.3, "Fire_Pct": 0.072, "Imports_Pct": 20.0, "Exports_Pct": 21.0, "Health_Exp_Pct": 11.5, "RD_Exp_Pct": 3.3},
    "DEU": {"Country_Name": "Germany", "GDP_USD": 4.46e12, "Population": 84000000, "Gini": 31.7, "PM25": 12.0, "Forest_SqKm": 114190.0, "Energy_Imports_Pct": 61.2, "Internet_Users_Pct": 91.5, "Fire_Pct": 0.065, "Imports_Pct": 42.0, "Exports_Pct": 47.0, "Health_Exp_Pct": 12.8, "RD_Exp_Pct": 3.1},
    "IND": {"Country_Name": "India", "GDP_USD": 3.73e12, "Population": 1430000000, "Gini": 35.7, "PM25": 58.1, "Forest_SqKm": 721600.0, "Energy_Imports_Pct": 38.4, "Internet_Users_Pct": 48.7, "Fire_Pct": 0.060, "Imports_Pct": 26.0, "Exports_Pct": 22.0, "Health_Exp_Pct": 3.0, "RD_Exp_Pct": 0.7},
    "GBR": {"Country_Name": "United Kingdom", "GDP_USD": 3.33e12, "Population": 67000000, "Gini": 35.1, "PM25": 9.6, "Forest_SqKm": 31790.0, "Energy_Imports_Pct": 35.2, "Internet_Users_Pct": 96.0, "Fire_Pct": 0.085, "Imports_Pct": 32.0, "Exports_Pct": 29.0, "Health_Exp_Pct": 11.3, "RD_Exp_Pct": 2.9},
    "FRA": {"Country_Name": "France", "GDP_USD": 3.01e12, "Population": 68000000, "Gini": 32.4, "PM25": 11.5, "Forest_SqKm": 172530.0, "Energy_Imports_Pct": 44.5, "Internet_Users_Pct": 92.0, "Fire_Pct": 0.060, "Imports_Pct": 35.0, "Exports_Pct": 32.0, "Health_Exp_Pct": 12.2, "RD_Exp_Pct": 2.2},
    "ITA": {"Country_Name": "Italy", "GDP_USD": 2.19e12, "Population": 59000000, "Gini": 35.2, "PM25": 16.0, "Forest_SqKm": 95660.0, "Energy_Imports_Pct": 73.5, "Internet_Users_Pct": 85.2, "Fire_Pct": 0.055, "Imports_Pct": 33.0, "Exports_Pct": 34.0, "Health_Exp_Pct": 9.6, "RD_Exp_Pct": 1.5},
    "CAN": {"Country_Name": "Canada", "GDP_USD": 2.14e12, "Population": 40000000, "Gini": 33.3, "PM25": 6.0, "Forest_SqKm": 3470000.0, "Energy_Imports_Pct": -58.2, "Internet_Users_Pct": 92.8, "Fire_Pct": 0.070, "Imports_Pct": 33.0, "Exports_Pct": 33.0, "Health_Exp_Pct": 11.2, "RD_Exp_Pct": 1.7},
    "BRA": {"Country_Name": "Brazil", "GDP_USD": 2.13e12, "Population": 215000000, "Gini": 48.9, "PM25": 11.8, "Forest_SqKm": 4966000.0, "Energy_Imports_Pct": 5.4, "Internet_Users_Pct": 81.0, "Fire_Pct": 0.065, "Imports_Pct": 20.0, "Exports_Pct": 21.0, "Health_Exp_Pct": 9.5, "RD_Exp_Pct": 1.2},
    "RUS": {"Country_Name": "Russian Federation", "GDP_USD": 2.0e12, "Population": 144000000, "Gini": 36.0, "PM25": 13.8, "Forest_SqKm": 8150000.0, "Energy_Imports_Pct": -185.0, "Internet_Users_Pct": 88.2, "Fire_Pct": 0.045, "Imports_Pct": 21.0, "Exports_Pct": 28.0, "Health_Exp_Pct": 5.7, "RD_Exp_Pct": 1.0},
    "KOR": {"Country_Name": "Korea, Rep.", "GDP_USD": 1.71e12, "Population": 51000000, "Gini": 31.4, "PM25": 18.0, "Forest_SqKm": 63400.0, "Energy_Imports_Pct": 82.1, "Internet_Users_Pct": 97.6, "Fire_Pct": 0.070, "Imports_Pct": 42.0, "Exports_Pct": 44.0, "Health_Exp_Pct": 9.7, "RD_Exp_Pct": 4.9},
    "AUS": {"Country_Name": "Australia", "GDP_USD": 1.71e12, "Population": 26000000, "Gini": 34.3, "PM25": 5.2, "Forest_SqKm": 1340000.0, "Energy_Imports_Pct": -120.0, "Internet_Users_Pct": 96.2, "Fire_Pct": 0.080, "Imports_Pct": 22.0, "Exports_Pct": 27.0, "Health_Exp_Pct": 9.6, "RD_Exp_Pct": 1.8},
    "MEX": {"Country_Name": "Mexico", "GDP_USD": 1.79e12, "Population": 128000000, "Gini": 45.4, "PM25": 19.8, "Forest_SqKm": 660000.0, "Energy_Imports_Pct": 10.4, "Internet_Users_Pct": 78.6, "Fire_Pct": 0.045, "Imports_Pct": 44.0, "Exports_Pct": 43.0, "Health_Exp_Pct": 5.5, "RD_Exp_Pct": 0.3},
    "ESP": {"Country_Name": "Spain", "GDP_USD": 1.58e12, "Population": 47000000, "Gini": 34.3, "PM25": 9.7, "Forest_SqKm": 185720.0, "Energy_Imports_Pct": 68.1, "Internet_Users_Pct": 93.9, "Fire_Pct": 0.050, "Imports_Pct": 32.0, "Exports_Pct": 35.0, "Health_Exp_Pct": 10.7, "RD_Exp_Pct": 1.4},
    "IDN": {"Country_Name": "Indonesia", "GDP_USD": 1.37e12, "Population": 277000000, "Gini": 37.9, "PM25": 18.2, "Forest_SqKm": 920000.0, "Energy_Imports_Pct": -35.6, "Internet_Users_Pct": 66.5, "Fire_Pct": 0.045, "Imports_Pct": 21.0, "Exports_Pct": 24.0, "Health_Exp_Pct": 3.2, "RD_Exp_Pct": 0.2},
    "SAU": {"Country_Name": "Saudi Arabia", "GDP_USD": 1.07e12, "Population": 36000000, "Gini": 34.5, "PM25": 37.9, "Forest_SqKm": 9770.0, "Energy_Imports_Pct": -320.0, "Internet_Users_Pct": 99.0, "Fire_Pct": 0.050, "Imports_Pct": 33.0, "Exports_Pct": 38.0, "Health_Exp_Pct": 5.0, "RD_Exp_Pct": 0.5},
    "NLD": {"Country_Name": "Netherlands", "GDP_USD": 1.09e12, "Population": 17800000, "Gini": 27.8, "PM25": 12.1, "Forest_SqKm": 3700.0, "Energy_Imports_Pct": 63.8, "Internet_Users_Pct": 96.0, "Fire_Pct": 0.100, "Imports_Pct": 65.0, "Exports_Pct": 75.0, "Health_Exp_Pct": 11.2, "RD_Exp_Pct": 2.3},
    "TUR": {"Country_Name": "Turkiye", "GDP_USD": 1.02e12, "Population": 85000000, "Gini": 41.9, "PM25": 20.0, "Forest_SqKm": 222000.0, "Energy_Imports_Pct": 74.0, "Internet_Users_Pct": 85.0, "Fire_Pct": 0.050, "Imports_Pct": 38.0, "Exports_Pct": 30.0, "Health_Exp_Pct": 4.6, "RD_Exp_Pct": 1.4},
    "CHE": {"Country_Name": "Switzerland", "GDP_USD": 8.85e11, "Population": 8800000, "Gini": 32.7, "PM25": 9.0, "Forest_SqKm": 13200.0, "Energy_Imports_Pct": 62.0, "Internet_Users_Pct": 98.4, "Fire_Pct": 0.120, "Imports_Pct": 60.0, "Exports_Pct": 65.0, "Health_Exp_Pct": 11.5, "RD_Exp_Pct": 3.4},
    "POL": {"Country_Name": "Poland", "GDP_USD": 8.11e11, "Population": 38000000, "Gini": 30.2, "PM25": 19.4, "Forest_SqKm": 94830.0, "Energy_Imports_Pct": 43.1, "Internet_Users_Pct": 88.4, "Fire_Pct": 0.050, "Imports_Pct": 50.0, "Exports_Pct": 52.0, "Health_Exp_Pct": 6.5, "RD_Exp_Pct": 1.4},
    "SWE": {"Country_Name": "Sweden", "GDP_USD": 5.86e11, "Population": 10500000, "Gini": 29.3, "PM25": 5.8, "Forest_SqKm": 279800.0, "Energy_Imports_Pct": -33.2, "Internet_Users_Pct": 98.2, "Fire_Pct": 0.055, "Imports_Pct": 45.0, "Exports_Pct": 50.0, "Health_Exp_Pct": 11.4, "RD_Exp_Pct": 3.4},
    "BEL": {"Country_Name": "Belgium", "GDP_USD": 5.82e11, "Population": 11700000, "Gini": 27.2, "PM25": 12.8, "Forest_SqKm": 6800.0, "Energy_Imports_Pct": 77.4, "Internet_Users_Pct": 94.1, "Fire_Pct": 0.062, "Imports_Pct": 82.0, "Exports_Pct": 85.0, "Health_Exp_Pct": 10.9, "RD_Exp_Pct": 3.2},
    "ARG": {"Country_Name": "Argentina", "GDP_USD": 6.32e11, "Population": 46000000, "Gini": 42.0, "PM25": 14.2, "Forest_SqKm": 260000.0, "Energy_Imports_Pct": 15.0, "Internet_Users_Pct": 87.0, "Fire_Pct": 0.040, "Imports_Pct": 17.0, "Exports_Pct": 16.0, "Health_Exp_Pct": 9.0, "RD_Exp_Pct": 0.5},
    "THA": {"Country_Name": "Thailand", "GDP_USD": 5.0e11, "Population": 71000000, "Gini": 35.0, "PM25": 20.2, "Forest_SqKm": 190000.0, "Energy_Imports_Pct": 41.5, "Internet_Users_Pct": 81.2, "Fire_Pct": 0.050, "Imports_Pct": 65.0, "Exports_Pct": 68.0, "Health_Exp_Pct": 3.8, "RD_Exp_Pct": 0.2},
    "AUT": {"Country_Name": "Austria", "GDP_USD": 5.2e11, "Population": 9000000, "Gini": 29.8, "PM25": 11.0, "Forest_SqKm": 38990.0, "Energy_Imports_Pct": 58.5, "Internet_Users_Pct": 92.5, "Fire_Pct": 0.058, "Imports_Pct": 49.0, "Exports_Pct": 53.0, "Health_Exp_Pct": 11.3, "RD_Exp_Pct": 3.1},
    "IRL": {"Country_Name": "Ireland", "GDP_USD": 5.45e11, "Population": 5100000, "Gini": 29.2, "PM25": 7.2, "Forest_SqKm": 7800.0, "Energy_Imports_Pct": 69.8, "Internet_Users_Pct": 95.5, "Fire_Pct": 0.180, "Imports_Pct": 105.0, "Exports_Pct": 135.0, "Health_Exp_Pct": 6.7, "RD_Exp_Pct": 1.2},
    "ISR": {"Country_Name": "Israel", "GDP_USD": 5.22e11, "Population": 9700000, "Gini": 37.9, "PM25": 19.5, "Forest_SqKm": 1500.0, "Energy_Imports_Pct": 80.0, "Internet_Users_Pct": 91.0, "Fire_Pct": 0.065, "Imports_Pct": 31.0, "Exports_Pct": 33.0, "Health_Exp_Pct": 7.5, "RD_Exp_Pct": 5.4},
    "ARE": {"Country_Name": "United Arab Emirates", "GDP_USD": 5.04e11, "Population": 9400000, "Gini": 26.0, "PM25": 29.2, "Forest_SqKm": 3200.0, "Energy_Imports_Pct": -250.0, "Internet_Users_Pct": 99.0, "Fire_Pct": 0.080, "Imports_Pct": 78.0, "Exports_Pct": 95.0, "Health_Exp_Pct": 3.5, "RD_Exp_Pct": 1.3},
    "NOR": {"Country_Name": "Norway", "GDP_USD": 4.85e11, "Population": 5400000, "Gini": 27.6, "PM25": 6.7, "Forest_SqKm": 121000.0, "Energy_Imports_Pct": -680.0, "Internet_Users_Pct": 99.0, "Fire_Pct": 0.060, "Imports_Pct": 32.0, "Exports_Pct": 48.0, "Health_Exp_Pct": 10.5, "RD_Exp_Pct": 2.2},
    "SGP": {"Country_Name": "Singapore", "GDP_USD": 5.01e11, "Population": 5900000, "Gini": 35.0, "PM25": 14.5, "Forest_SqKm": 160.0, "Energy_Imports_Pct": 98.0, "Internet_Users_Pct": 92.0, "Fire_Pct": 0.220, "Imports_Pct": 140.0, "Exports_Pct": 175.0, "Health_Exp_Pct": 4.5, "RD_Exp_Pct": 2.1},
    "ZAF": {"Country_Name": "South Africa", "GDP_USD": 3.8e11, "Population": 60000000, "Gini": 63.0, "PM25": 21.6, "Forest_SqKm": 92000.0, "Energy_Imports_Pct": -12.0, "Internet_Users_Pct": 75.0, "Fire_Pct": 0.075, "Imports_Pct": 28.0, "Exports_Pct": 26.0, "Health_Exp_Pct": 8.5, "RD_Exp_Pct": 0.6},
    "DNK": {"Country_Name": "Denmark", "GDP_USD": 4.0e11, "Population": 5900000, "Gini": 27.5, "PM25": 9.6, "Forest_SqKm": 6200.0, "Energy_Imports_Pct": -12.1, "Internet_Users_Pct": 98.9, "Fire_Pct": 0.065, "Imports_Pct": 48.0, "Exports_Pct": 54.0, "Health_Exp_Pct": 10.8, "RD_Exp_Pct": 3.0},
    "EGY": {"Country_Name": "Egypt, Arab Rep.", "GDP_USD": 3.95e11, "Population": 112000000, "Gini": 31.5, "PM25": 38.5, "Forest_SqKm": 10.0, "Energy_Imports_Pct": 12.0, "Internet_Users_Pct": 72.0, "Fire_Pct": 0.040, "Imports_Pct": 29.0, "Exports_Pct": 18.0, "Health_Exp_Pct": 4.8, "RD_Exp_Pct": 0.2},
    "PHL": {"Country_Name": "Philippines", "GDP_USD": 4.37e11, "Population": 115000000, "Gini": 42.2, "PM25": 18.6, "Forest_SqKm": 72000.0, "Energy_Imports_Pct": 45.0, "Internet_Users_Pct": 73.0, "Fire_Pct": 0.045, "Imports_Pct": 32.0, "Exports_Pct": 22.0, "Health_Exp_Pct": 4.0, "RD_Exp_Pct": 0.2},
    "FIN": {"Country_Name": "Finland", "GDP_USD": 3.0e11, "Population": 5500000, "Gini": 27.7, "PM25": 5.5, "Forest_SqKm": 224090.0, "Energy_Imports_Pct": 42.8, "Internet_Users_Pct": 97.7, "Fire_Pct": 0.048, "Imports_Pct": 39.0, "Exports_Pct": 42.0, "Health_Exp_Pct": 10.0, "RD_Exp_Pct": 2.9},
    "BGD": {"Country_Name": "Bangladesh", "GDP_USD": 4.6e11, "Population": 170000000, "Gini": 32.4, "PM25": 65.8, "Forest_SqKm": 14000.0, "Energy_Imports_Pct": 18.0, "Internet_Users_Pct": 38.9, "Fire_Pct": 0.035, "Imports_Pct": 20.0, "Exports_Pct": 14.0, "Health_Exp_Pct": 2.8, "RD_Exp_Pct": 0.1},
    "COL": {"Country_Name": "Colombia", "GDP_USD": 3.63e11, "Population": 52000000, "Gini": 54.2, "PM25": 15.6, "Forest_SqKm": 590000.0, "Energy_Imports_Pct": -45.0, "Internet_Users_Pct": 70.1, "Fire_Pct": 0.042, "Imports_Pct": 21.0, "Exports_Pct": 18.0, "Health_Exp_Pct": 7.5, "RD_Exp_Pct": 0.3},
    "MYS": {"Country_Name": "Malaysia", "GDP_USD": 3.99e11, "Population": 34000000, "Gini": 41.1, "PM25": 14.0, "Forest_SqKm": 22000.0, "Energy_Imports_Pct": -15.0, "Internet_Users_Pct": 89.6, "Fire_Pct": 0.060, "Imports_Pct": 61.0, "Exports_Pct": 68.0, "Health_Exp_Pct": 4.2, "RD_Exp_Pct": 1.0},
    "VNM": {"Country_Name": "Viet Nam", "GDP_USD": 4.3e11, "Population": 98000000, "Gini": 35.7, "PM25": 22.1, "Forest_SqKm": 146000.0, "Energy_Imports_Pct": 18.5, "Internet_Users_Pct": 78.0, "Fire_Pct": 0.045, "Imports_Pct": 82.0, "Exports_Pct": 88.0, "Health_Exp_Pct": 5.5, "RD_Exp_Pct": 0.5},
    "CZE": {"Country_Name": "Czechia", "GDP_USD": 3.3e11, "Population": 10700000, "Gini": 25.3, "PM25": 14.5, "Forest_SqKm": 26770.0, "Energy_Imports_Pct": 38.5, "Internet_Users_Pct": 91.2, "Fire_Pct": 0.048, "Imports_Pct": 62.0, "Exports_Pct": 66.0, "Health_Exp_Pct": 7.7, "RD_Exp_Pct": 2.0},
    "ROU": {"Country_Name": "Romania", "GDP_USD": 3.5e11, "Population": 19000000, "Gini": 34.8, "PM25": 15.2, "Forest_SqKm": 69290.0, "Energy_Imports_Pct": 31.0, "Internet_Users_Pct": 88.0, "Fire_Pct": 0.040, "Imports_Pct": 41.0, "Exports_Pct": 32.0, "Health_Exp_Pct": 6.3, "RD_Exp_Pct": 0.5},
    "PRT": {"Country_Name": "Portugal", "GDP_USD": 2.87e11, "Population": 10400000, "Gini": 32.0, "PM25": 8.5, "Forest_SqKm": 33120.0, "Energy_Imports_Pct": 71.0, "Internet_Users_Pct": 86.4, "Fire_Pct": 0.052, "Imports_Pct": 43.0, "Exports_Pct": 46.0, "Health_Exp_Pct": 10.6, "RD_Exp_Pct": 1.6},
    "NZL": {"Country_Name": "New Zealand", "GDP_USD": 2.53e11, "Population": 5100000, "Gini": 32.0, "PM25": 5.0, "Forest_SqKm": 101000.0, "Energy_Imports_Pct": 35.0, "Internet_Users_Pct": 94.0, "Fire_Pct": 0.070, "Imports_Pct": 26.0, "Exports_Pct": 23.0, "Health_Exp_Pct": 9.7, "RD_Exp_Pct": 1.4},
    "GRC": {"Country_Name": "Greece", "GDP_USD": 2.38e11, "Population": 10300000, "Gini": 32.4, "PM25": 14.0, "Forest_SqKm": 39020.0, "Energy_Imports_Pct": 78.4, "Internet_Users_Pct": 82.5, "Fire_Pct": 0.055, "Imports_Pct": 45.0, "Exports_Pct": 38.0, "Health_Exp_Pct": 9.2, "RD_Exp_Pct": 1.5},
    "IRQ": {"Country_Name": "Iraq", "GDP_USD": 2.50e11, "Population": 45000000, "Gini": 38.0, "PM25": 39.0, "Forest_SqKm": 8250.0, "Energy_Imports_Pct": -450.0, "Internet_Users_Pct": 75.0, "Fire_Pct": 0.030, "Imports_Pct": 24.0, "Exports_Pct": 48.0, "Health_Exp_Pct": 4.5, "RD_Exp_Pct": 0.1},
    "PER": {"Country_Name": "Peru", "GDP_USD": 2.67e11, "Population": 34000000, "Gini": 41.5, "PM25": 22.8, "Forest_SqKm": 720000.0, "Energy_Imports_Pct": 18.0, "Internet_Users_Pct": 71.1, "Fire_Pct": 0.040, "Imports_Pct": 22.0, "Exports_Pct": 23.0, "Health_Exp_Pct": 5.5, "RD_Exp_Pct": 0.2},
    "QAT": {"Country_Name": "Qatar", "GDP_USD": 2.35e11, "Population": 2700000, "Gini": 26.0, "PM25": 28.5, "Forest_SqKm": 0.0, "Energy_Imports_Pct": -560.0, "Internet_Users_Pct": 99.0, "Fire_Pct": 0.080, "Imports_Pct": 35.0, "Exports_Pct": 65.0, "Health_Exp_Pct": 3.0, "RD_Exp_Pct": 0.6},
    "KAZ": {"Country_Name": "Kazakhstan", "GDP_USD": 2.6e11, "Population": 20000000, "Gini": 27.8, "PM25": 19.0, "Forest_SqKm": 32000.0, "Energy_Imports_Pct": -95.0, "Internet_Users_Pct": 90.9, "Fire_Pct": 0.040, "Imports_Pct": 32.0, "Exports_Pct": 40.0, "Health_Exp_Pct": 3.8, "RD_Exp_Pct": 0.1},
    "DZA": {"Country_Name": "Algeria", "GDP_USD": 2.39e11, "Population": 45000000, "Gini": 27.6, "PM25": 22.0, "Forest_SqKm": 20000.0, "Energy_Imports_Pct": -280.0, "Internet_Users_Pct": 70.9, "Fire_Pct": 0.035, "Imports_Pct": 24.0, "Exports_Pct": 32.0, "Health_Exp_Pct": 5.0, "RD_Exp_Pct": 0.2}
}

class GlobalDataScraper:
    """Fetches real macroeconomic data for all 190+ sovereign nations."""
    
    def __init__(self):
        self.raw_data = {}
        for iso, data in FALLBACK_GLOBAL_DATA.items():
            self.raw_data[iso] = data.copy()
            self.raw_data[iso]["ISO3"] = iso

    def fetch_indicator(self, indicator: str, data_key: str):
        logging.info(f"[INGEST] Fetching World Bank Indicator: {indicator}...")
        url = f"http://api.worldbank.org/v2/country/all/indicator/{indicator}?format=json&date=2022&per_page=300"
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Tokennomics-NDV-Engine/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            if len(data) > 1 and data[1] is not None:
                for entry in data[1]:
                    if "incomeLevel" in entry['country'] and entry['country']['incomeLevel']['id'] == "NA":
                        continue
                        
                    iso3 = entry['countryiso3code']
                    if not iso3: continue
                    
                    if iso3 not in self.raw_data:
                        self.raw_data[iso3] = {
                            "Country_Name": entry['country']['value'],
                            "ISO3": iso3
                        }
                    
                    val = entry['value']
                    if val is not None:
                        self.raw_data[iso3][data_key] = val
        except Exception as e:
            logging.warning(f"[INGEST] Failed to fetch {indicator}: {e}. Retaining local fallback values.")

    def generate_global_matrix(self):
        # Fetch GDP, Population, Gini, PM2.5, Forest Area, Energy Imports, Internet Users, Trade Imports/Exports, Health, R&D
        self.fetch_indicator("NY.GDP.MKTP.CD", "GDP_USD")
        self.fetch_indicator("SP.POP.TOTL", "Population")
        self.fetch_indicator("SI.POV.GINI", "Gini")
        self.fetch_indicator("EN.ATM.PM25.MC.M3", "PM25")
        self.fetch_indicator("AG.LND.FRST.K2", "Forest_SqKm")
        self.fetch_indicator("EG.IMP.CONS.ZS", "Energy_Imports_Pct")
        self.fetch_indicator("IT.NET.USER.ZS", "Internet_Users_Pct")
        self.fetch_indicator("NE.IMP.GNFS.ZS", "Imports_Pct")
        self.fetch_indicator("NE.EXP.GNFS.ZS", "Exports_Pct")
        self.fetch_indicator("SH.XPD.CHEX.GD.ZS", "Health_Exp_Pct")
        self.fetch_indicator("GB.XPD.RSDV.GD.ZS", "RD_Exp_Pct")
        
        processed_nations = []
        logging.info("[KERNEL] Processing nations through V5.0 Absolute Holism Biophysical Equation...")
        
        for iso, data in self.raw_data.items():
            if data.get("GDP_USD", 0) == 0 or data.get("Population", 0) == 0:
                continue
                
            y_gross = float(data["GDP_USD"])
            pop = float(data["Population"])
            
            # Local Gini, PM2.5, Forest
            gini = float(data.get("Gini", 35.0)) / 100.0 if data.get("Gini") else 0.38
            pm25 = float(data.get("PM25", 15.0))
            forest_sqkm = float(data.get("Forest_SqKm", 1000.0))
            forest_ha = forest_sqkm * 100.0
            
            # Setup EROI
            energy_imports_pct = float(data.get("Energy_Imports_Pct", 50.0))
            if energy_imports_pct >= 0:
                phi_eroi = max(0.80, 1.0 - (energy_imports_pct / 100.0) * 0.15)
            else:
                phi_eroi = min(1.03, 1.0 - (energy_imports_pct / 100.0) * 0.05)
            thermodynamic_gdp = y_gross * phi_eroi
            
            # Physical & Biosphere Depreciation
            dp = y_gross * 0.04
            dn = (forest_ha * 0.05) * 15000.0
            
            # Cognitive Depletion (Dc)
            internet_users_pct = float(data.get("Internet_Users_Pct", 85.0))
            dc = pop * (internet_users_pct / 100.0) * 4380.0
            
            # Metabolic human मशीन depreciation (Dm)
            health_exp_pct = float(data.get("Health_Exp_Pct", 8.0))
            dm_health = y_gross * (health_exp_pct / 100.0) * 1.20
            gdp_pc = y_gross / pop if pop > 0 else 0
            obesity_drag = pop * 750.0 * (1.0 + (gdp_pc / 80000.0))
            dm = dm_health + obesity_drag
            
            # Epistemic decay of knowledge (De)
            rd_exp_pct = float(data.get("RD_Exp_Pct", 1.5))
            de_base = y_gross * 0.05
            rd_offset = y_gross * (rd_exp_pct / 100.0) * 2.0
            de = max(0.0, de_base - rd_offset)
            
            # Care shadow wage (E+)
            care_shadow_wage = (gdp_pc / 2080.0) * 0.40
            care_hours = pop * 800.0
            e_plus = care_hours * care_shadow_wage
            
            # Frictions (E-)
            smog_debt = max(0, (pm25 - 5.0) * 800 * (pop / 1000.0))
            gini_drag = max(0, (gini - 0.35) * y_gross * 0.25)
            e_minus = smog_debt + gini_drag
            
            # FIRE sector rent seeking (E_rent)
            fire_share_map = {
                "USA": 0.20, "SGP": 0.22, "LUX": 0.28, "IRL": 0.18, "GBR": 0.085,
                "DEU": 0.065, "FRA": 0.060, "ITA": 0.055, "ESP": 0.050, "NLD": 0.100
            }
            fire_pct = data.get("Fire_Pct", fire_share_map.get(iso, 0.055))
            fire_friction = y_gross * fire_pct
            
            # Offshored supply chain entropy (E_offshore)
            imports_pct = float(data.get("Imports_Pct", 40.0))
            exports_pct = float(data.get("Exports_Pct", 40.0))
            net_imports_pct = imports_pct - exports_pct
            
            e_offshore = 0.0
            if net_imports_pct > 0:
                e_offshore = y_gross * (net_imports_pct / 100.0) * 0.08
            
            # Cohesion Archetype
            forest_pc = forest_ha / pop if pop > 0 else 0
            archetype = "Industrial" if forest_pc < 0.25 else "Natural"
            
            # V5.0 Absolute Holism Master Equation:
            # NDV = (Y * phi_eroi) - (Dp + Dn + Dc + Dm + De) + E+ - (E- + E_rent + E_offshore)
            ndv = thermodynamic_gdp - (dp + dn + dc + dm + de) + e_plus - (e_minus + fire_friction + e_offshore)
            
            processed_nations.append({
                "Country_Name": data["Country_Name"],
                "ISO3": iso,
                "Population": pop,
                "Gini": round(gini, 3),
                "gross_domestic_product_usd": round(y_gross, 2),
                "thermodynamic_gdp_usd": round(thermodynamic_gdp, 2),
                "physical_depreciation_usd": round(dp, 2),
                "natural_depletion_usd": round(dn, 2),
                "cognitive_depletion_usd": round(dc, 2),
                "metabolic_depreciation_usd": round(dm, 2),
                "epistemic_decay_usd": round(de, 2),
                "care_economy_dividend_usd": round(e_plus, 2),
                "smog_friction_penalty_usd": round(smog_debt, 2),
                "gini_friction_penalty_usd": round(gini_drag, 2),
                "financialization_friction_usd": round(fire_friction, 2),
                "offshored_entropy_debt_usd": round(e_offshore, 2),
                "net_domestic_value_usd": round(ndv, 2),
                "cohesion_archetype": archetype,
                "equilibrium_transfer_usd": 0.0,
                "ndv_to_gdp_ratio": 0.0
            })
            
        # Apply Cohesion Matrix: 10% tax on Industrial depletion redistributed to Natural Sinks
        total_tax_pool = sum(abs(r["natural_depletion_usd"]) for r in processed_nations if r["cohesion_archetype"] == "Industrial") * 0.10
        natural_sinks_count = sum(1 for r in processed_nations if r["cohesion_archetype"] == "Natural")
        
        for r in processed_nations:
            if r["cohesion_archetype"] == "Industrial":
                tax = abs(r["natural_depletion_usd"]) * 0.10
                r["net_domestic_value_usd"] -= tax
                r["equilibrium_transfer_usd"] = -tax
            else:
                payout = (total_tax_pool / natural_sinks_count) if natural_sinks_count > 0 else 0.0
                r["net_domestic_value_usd"] += payout
                r["equilibrium_transfer_usd"] = payout
                
            r["ndv_to_gdp_ratio"] = round(r["net_domestic_value_usd"] / r["gross_domestic_product_usd"], 3) if r["gross_domestic_product_usd"] > 0 else 0.0

        # Sort by NDV descending
        processed_nations.sort(key=lambda x: x["net_domestic_value_usd"], reverse=True)
        return processed_nations

if __name__ == "__main__":
    scraper = GlobalDataScraper()
    final_ledger = scraper.generate_global_matrix()
    
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'global_sovereign_ledger.csv')
    
    if not final_ledger:
        logging.error("No data generated. Check API connections.")
    else:
        keys = final_ledger[0].keys()
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(final_ledger)
        logging.info(f"[SUCCESS] V5.0 Global Sovereign Ledger generated with {len(final_ledger)} nations at {output_path}")
