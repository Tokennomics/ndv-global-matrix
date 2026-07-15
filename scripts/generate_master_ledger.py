#!/usr/bin/env python3
"""
Net Domestic Value (NDV) Master Sovereign Ledger Generator
Author: Senior Economic Researcher and Lead Systems Engineer
Version: 3.1: Total Project Recovery

This module ingests real macroeconomic data for all 190+ sovereign nations via the
World Bank API, routes them through the NDV thermodynamic calculations, applies
the Cohesion Transfer Matrix, and outputs a comprehensive global_sovereign_ledger.csv
in the repository root.
"""

import urllib.request
import json
import csv
import logging
import time
import os
from typing import Dict, List, Optional

# Enterprise Logging Configuration
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("NDV_Global_Scraper")

# High-fidelity fallback database for major countries in case of API failure/timeout
FALLBACK_GLOBAL_DATA = {
    "USA": {"Country_Name": "United States", "GDP_USD": 27.36e12, "Population": 335000000, "Gini": 41.5, "PM25": 7.4, "Forest_Pct": 33.9},
    "CHN": {"Country_Name": "China", "GDP_USD": 17.79e12, "Population": 1410000000, "Gini": 38.2, "PM25": 35.5, "Forest_Pct": 23.3},
    "JPN": {"Country_Name": "Japan", "GDP_USD": 4.21e12, "Population": 125000000, "Gini": 32.9, "PM25": 11.2, "Forest_Pct": 68.4},
    "DEU": {"Country_Name": "Germany", "GDP_USD": 4.46e12, "Population": 84000000, "Gini": 31.7, "PM25": 12.0, "Forest_Pct": 32.7},
    "IND": {"Country_Name": "India", "GDP_USD": 3.73e12, "Population": 1430000000, "Gini": 35.7, "PM25": 58.1, "Forest_Pct": 24.3},
    "GBR": {"Country_Name": "United Kingdom", "GDP_USD": 3.33e12, "Population": 67000000, "Gini": 35.1, "PM25": 9.6, "Forest_Pct": 13.1},
    "FRA": {"Country_Name": "France", "GDP_USD": 3.01e12, "Population": 68000000, "Gini": 32.4, "PM25": 11.5, "Forest_Pct": 31.5},
    "ITA": {"Country_Name": "Italy", "GDP_USD": 2.19e12, "Population": 59000000, "Gini": 35.2, "PM25": 16.0, "Forest_Pct": 31.6},
    "CAN": {"Country_Name": "Canada", "GDP_USD": 2.14e12, "Population": 40000000, "Gini": 33.3, "PM25": 6.0, "Forest_Pct": 38.2},
    "BRA": {"Country_Name": "Brazil", "GDP_USD": 2.13e12, "Population": 215000000, "Gini": 48.9, "PM25": 11.8, "Forest_Pct": 58.9},
    "RUS": {"Country_Name": "Russian Federation", "GDP_USD": 2.0e12, "Population": 144000000, "Gini": 36.0, "PM25": 13.8, "Forest_Pct": 49.8},
    "KOR": {"Country_Name": "Korea, Rep.", "GDP_USD": 1.71e12, "Population": 51000000, "Gini": 31.4, "PM25": 18.0, "Forest_Pct": 63.4},
    "AUS": {"Country_Name": "Australia", "GDP_USD": 1.71e12, "Population": 26000000, "Gini": 34.3, "PM25": 5.2, "Forest_Pct": 16.2},
    "MEX": {"Country_Name": "Mexico", "GDP_USD": 1.79e12, "Population": 128000000, "Gini": 45.4, "PM25": 19.8, "Forest_Pct": 33.7},
    "ESP": {"Country_Name": "Spain", "GDP_USD": 1.58e12, "Population": 47000000, "Gini": 34.3, "PM25": 9.7, "Forest_Pct": 37.1},
    "IDN": {"Country_Name": "Indonesia", "GDP_USD": 1.37e12, "Population": 277000000, "Gini": 37.9, "PM25": 18.2, "Forest_Pct": 49.1},
    "SAU": {"Country_Name": "Saudi Arabia", "GDP_USD": 1.07e12, "Population": 36000000, "Gini": 34.5, "PM25": 37.9, "Forest_Pct": 0.5},
    "NLD": {"Country_Name": "Netherlands", "GDP_USD": 1.09e12, "Population": 17800000, "Gini": 27.8, "PM25": 12.1, "Forest_Pct": 11.1},
    "TUR": {"Country_Name": "Turkiye", "GDP_USD": 1.02e12, "Population": 85000000, "Gini": 41.9, "PM25": 20.0, "Forest_Pct": 29.0},
    "CHE": {"Country_Name": "Switzerland", "GDP_USD": 8.85e11, "Population": 8800000, "Gini": 32.7, "PM25": 9.0, "Forest_Pct": 31.5},
    "POL": {"Country_Name": "Poland", "GDP_USD": 8.11e11, "Population": 38000000, "Gini": 30.2, "PM25": 19.4, "Forest_Pct": 31.0},
    "SWE": {"Country_Name": "Sweden", "GDP_USD": 5.86e11, "Population": 10500000, "Gini": 29.3, "PM25": 5.8, "Forest_Pct": 68.7},
    "BEL": {"Country_Name": "Belgium", "GDP_USD": 5.82e11, "Population": 11700000, "Gini": 27.2, "PM25": 12.8, "Forest_Pct": 22.0},
    "ARG": {"Country_Name": "Argentina", "GDP_USD": 6.32e11, "Population": 46000000, "Gini": 42.0, "PM25": 14.2, "Forest_Pct": 10.4},
    "THA": {"Country_Name": "Thailand", "GDP_USD": 5.0e11, "Population": 71000000, "Gini": 35.0, "PM25": 20.2, "Forest_Pct": 38.9},
    "AUT": {"Country_Name": "Austria", "GDP_USD": 5.2e11, "Population": 9000000, "Gini": 29.8, "PM25": 11.0, "Forest_Pct": 47.2},
    "IRL": {"Country_Name": "Ireland", "GDP_USD": 5.45e11, "Population": 5100000, "Gini": 29.2, "PM25": 7.2, "Forest_Pct": 11.4},
    "ISR": {"Country_Name": "Israel", "GDP_USD": 5.22e11, "Population": 9700000, "Gini": 37.9, "PM25": 19.5, "Forest_Pct": 7.3},
    "ARE": {"Country_Name": "United Arab Emirates", "GDP_USD": 5.04e11, "Population": 9400000, "Gini": 26.0, "PM25": 29.2, "Forest_Pct": 4.5},
    "NOR": {"Country_Name": "Norway", "GDP_USD": 4.85e11, "Population": 5400000, "Gini": 27.6, "PM25": 6.7, "Forest_Pct": 33.2},
    "SGP": {"Country_Name": "Singapore", "GDP_USD": 5.01e11, "Population": 5900000, "Gini": 35.0, "PM25": 14.5, "Forest_Pct": 23.0},
    "ZAF": {"Country_Name": "South Africa", "GDP_USD": 3.8e11, "Population": 60000000, "Gini": 63.0, "PM25": 21.6, "Forest_Pct": 7.6},
    "DNK": {"Country_Name": "Denmark", "GDP_USD": 4.0e11, "Population": 5900000, "Gini": 27.5, "PM25": 9.6, "Forest_Pct": 15.7},
    "EGY": {"Country_Name": "Egypt, Arab Rep.", "GDP_USD": 3.95e11, "Population": 112000000, "Gini": 31.5, "PM25": 38.5, "Forest_Pct": 0.1},
    "PHL": {"Country_Name": "Philippines", "GDP_USD": 4.37e11, "Population": 115000000, "Gini": 42.2, "PM25": 18.6, "Forest_Pct": 27.8},
    "FIN": {"Country_Name": "Finland", "GDP_USD": 3.0e11, "Population": 5500000, "Gini": 27.7, "PM25": 5.5, "Forest_Pct": 73.1},
    "BGD": {"Country_Name": "Bangladesh", "GDP_USD": 4.6e11, "Population": 170000000, "Gini": 32.4, "PM25": 65.8, "Forest_Pct": 11.2},
    "COL": {"Country_Name": "Colombia", "GDP_USD": 3.63e11, "Population": 52000000, "Gini": 54.2, "PM25": 15.6, "Forest_Pct": 52.8},
    "MYS": {"Country_Name": "Malaysia", "GDP_USD": 3.99e11, "Population": 34000000, "Gini": 41.1, "PM25": 14.0, "Forest_Pct": 43.6},
    "VNM": {"Country_Name": "Viet Nam", "GDP_USD": 4.3e11, "Population": 98000000, "Gini": 35.7, "PM25": 22.1, "Forest_Pct": 47.6},
    "CZE": {"Country_Name": "Czechia", "GDP_USD": 3.3e11, "Population": 10700000, "Gini": 25.3, "PM25": 14.5, "Forest_Pct": 34.6},
    "ROU": {"Country_Name": "Romania", "GDP_USD": 3.5e11, "Population": 19000000, "Gini": 34.8, "PM25": 15.2, "Forest_Pct": 28.7},
    "PRT": {"Country_Name": "Portugal", "GDP_USD": 2.87e11, "Population": 10400000, "Gini": 32.0, "PM25": 8.5, "Forest_Pct": 36.2},
    "NZL": {"Country_Name": "New Zealand", "GDP_USD": 2.53e11, "Population": 5100000, "Gini": 32.0, "PM25": 5.0, "Forest_Pct": 38.6},
    "GRC": {"Country_Name": "Greece", "GDP_USD": 2.38e11, "Population": 10300000, "Gini": 32.4, "PM25": 14.0, "Forest_Pct": 31.5},
    "IRQ": {"Country_Name": "Iraq", "GDP_USD": 2.50e11, "Population": 45000000, "Gini": 38.0, "PM25": 39.0, "Forest_Pct": 1.9},
    "PER": {"Country_Name": "Peru", "GDP_USD": 2.67e11, "Population": 34000000, "Gini": 41.5, "PM25": 22.8, "Forest_Pct": 57.8},
    "QAT": {"Country_Name": "Qatar", "GDP_USD": 2.35e11, "Population": 2700000, "Gini": 26.0, "PM25": 28.5, "Forest_Pct": 0.0},
    "KAZ": {"Country_Name": "Kazakhstan", "GDP_USD": 2.6e11, "Population": 20000000, "Gini": 27.8, "PM25": 19.0, "Forest_Pct": 1.2},
    "DZA": {"Country_Name": "Algeria", "GDP_USD": 2.39e11, "Population": 45000000, "Gini": 27.6, "PM25": 22.0, "Forest_Pct": 0.8}
}

class GlobalDataScraper:
    """Fetches real macroeconomic data for all 190+ sovereign nations."""
    
    def __init__(self):
        self.raw_data = {}
        # Pre-seed with fallback indicators to guarantee offline resilience
        for iso, data in FALLBACK_GLOBAL_DATA.items():
            self.raw_data[iso] = data.copy()
            self.raw_data[iso]["ISO3"] = iso

    def fetch_indicator(self, indicator: str, data_key: str):
        logging.info(f"[INGEST] Fetching World Bank Indicator: {indicator}...")
        url = f"http://api.worldbank.org/v2/country/all/indicator/{indicator}?format=json&date=2022&per_page=300"
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Tokennomics-NDV-Engine/3.0'})
            # Set a moderate timeout to prevent script hangs
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            if len(data) > 1 and data[1] is not None:
                for entry in data[1]:
                    # Exclude aggregates (like "World", "Arab World", etc.)
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
        # Fetch GDP, Population, Gini, PM2.5, Forest Area (% of land)
        self.fetch_indicator("NY.GDP.MKTP.CD", "GDP_USD")
        self.fetch_indicator("SP.POP.TOTL", "Population")
        self.fetch_indicator("SI.POV.GINI", "Gini")
        self.fetch_indicator("EN.ATM.PM25.MC.M3", "PM25")
        self.fetch_indicator("AG.LND.FRST.ZS", "Forest_Pct")
        
        processed_nations = []
        logging.info("[KERNEL] Processing nations through NDV Thermodynamic Math...")
        
        for iso, data in self.raw_data.items():
            if data.get("GDP_USD", 0) == 0 or data.get("Population", 0) == 0:
                continue  # Skip entities without baseline data
                
            y_gross = float(data["GDP_USD"])
            pop = float(data["Population"])
            
            # Data cleansing & fallbacks
            gini = float(data.get("Gini", 35.0)) / 100.0 if data.get("Gini") else 0.38
            pm25 = float(data.get("PM25", 15.0))
            forest_pct = float(data.get("Forest_Pct", 10.0))
            
            # Archetype classification
            gdp_pc = y_gross / pop if pop > 0 else 0
            archetype = "Industrial" if gdp_pc > 38000 else "Natural"
            
            # NDV First Principles Math
            dp = y_gross * 0.04  # Standard depreciation
            
            # Proxy for Natural Depletion based on forest size and standard industrial loss
            protected_ha = (forest_pct * 1000) * (pop / 1000000)
            dn = (protected_ha * 0.02) * 25000 
            
            # Societal Math
            care_hours = pop * 600
            e_plus = care_hours * 15.00  # Global blended shadow wage
            
            # Frictions
            smog_debt = max(0, (pm25 - 5.0) * 800 * (pop / 1000))
            gini_drag = max(0, (gini - 0.35) * y_gross * 0.25)
            
            e_minus = smog_debt + gini_drag
            
            ndv_raw = y_gross - (dp + dn) + (e_plus - e_minus)
            
            processed_nations.append({
                "Country_Name": data["Country_Name"],
                "ISO3": data["ISO3"],
                "Population": pop,
                "Gini": round(gini, 3),
                "1_Y_Gross": round(y_gross, 2),
                "Care_E_Plus": round(e_plus, 2),
                "Gini_Drag": round(-gini_drag, 2),
                "Nature_Depletion_Dn": round(-dn, 2),
                "6_NDV": round(ndv_raw, 2),
                "Equilibrium_Transfer": 0.0,
                "Archetype": archetype,
                "NDV_to_GDP": 0.0
            })
            
        # Apply Cohesion Matrix: 10% tax on Industrial depletion (Nature_Depletion_Dn) redistributed to Natural Sinks
        total_tax_pool = sum(abs(r["Nature_Depletion_Dn"]) for r in processed_nations if r["Archetype"] == "Industrial") * 0.10
        natural_sinks_count = sum(1 for r in processed_nations if r["Archetype"] == "Natural")
        
        for r in processed_nations:
            if r["Archetype"] == "Industrial":
                tax = abs(r["Nature_Depletion_Dn"]) * 0.10
                r["6_NDV"] -= tax
                r["Equilibrium_Transfer"] = -tax
            else:
                payout = (total_tax_pool / natural_sinks_count) if natural_sinks_count > 0 else 0.0
                r["6_NDV"] += payout
                r["Equilibrium_Transfer"] = payout
                
            r["NDV_to_GDP"] = round(r["6_NDV"] / r["1_Y_Gross"], 3) if r["1_Y_Gross"] > 0 else 0.0

        # Sort by True Wealth
        processed_nations.sort(key=lambda x: x["6_NDV"], reverse=True)
        return processed_nations

if __name__ == "__main__":
    scraper = GlobalDataScraper()
    final_ledger = scraper.generate_global_matrix()
    
    # Save to the root directory where the dashboard expects it
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'global_sovereign_ledger.csv')
    
    if not final_ledger:
        logging.error("No data generated. Check API connections.")
    else:
        keys = final_ledger[0].keys()
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(final_ledger)
        logging.info(f"[SUCCESS] Global Sovereign Ledger generated with {len(final_ledger)} nations at {output_path}")
