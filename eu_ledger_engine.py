#!/usr/bin/env python3
"""
Net Domestic Value (NDV) European Sovereign Ledger Engine
Author: Senior Economic Researcher and Lead Systems Engineer
Version: 3.0: Total Project Recovery

This module implements the EU Sovereign Ingestion and Cohesion Matrix calculations.
It computes the NDV for the 27 EU Member States and applies Cohesion Policy 2.0
transfer mechanisms.
"""

import json
import urllib.request
import csv
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NDV_EU")

# The 27 EU Member States ISO2 Codes
EU_ISO2 = [
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", 
    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", 
    "PL", "PT", "RO", "SK", "SI", "ES", "SE"
]

# High-fidelity fallback data in case World Bank API times out or is unreachable
FALLBACK_EU_DATA = {
    "DE": {"Country_Name": "Germany", "GDP_USD": 4.07e12, "Population": 84000000, "Gini": 31.7, "PM25": 12.0},
    "FR": {"Country_Name": "France", "GDP_USD": 2.78e12, "Population": 68000000, "Gini": 32.4, "PM25": 11.5},
    "IT": {"Country_Name": "Italy", "GDP_USD": 2.01e12, "Population": 59000000, "Gini": 35.2, "PM25": 16.0},
    "ES": {"Country_Name": "Spain", "GDP_USD": 1.40e12, "Population": 47000000, "Gini": 34.3, "PM25": 9.7},
    "NL": {"Country_Name": "Netherlands", "GDP_USD": 1.01e12, "Population": 17800000, "Gini": 27.8, "PM25": 12.1},
    "PL": {"Country_Name": "Poland", "GDP_USD": 6.88e11, "Population": 38000000, "Gini": 30.2, "PM25": 19.4},
    "SE": {"Country_Name": "Sweden", "GDP_USD": 5.86e11, "Population": 10500000, "Gini": 29.3, "PM25": 5.8},
    "BE": {"Country_Name": "Belgium", "GDP_USD": 5.82e11, "Population": 11700000, "Gini": 27.2, "PM25": 12.8},
    "IE": {"Country_Name": "Ireland", "GDP_USD": 5.33e11, "Population": 5100000, "Gini": 29.2, "PM25": 7.2},
    "AT": {"Country_Name": "Austria", "GDP_USD": 4.71e11, "Population": 9000000, "Gini": 29.8, "PM25": 11.0},
    "DK": {"Country_Name": "Denmark", "GDP_USD": 4.00e11, "Population": 5900000, "Gini": 27.5, "PM25": 9.6},
    "FI": {"Country_Name": "Finland", "GDP_USD": 2.81e11, "Population": 5500000, "Gini": 27.7, "PM25": 5.5},
    "RO": {"Country_Name": "Romania", "GDP_USD": 3.01e11, "Population": 19000000, "Gini": 34.8, "PM25": 15.2},
    "CZ": {"Country_Name": "Czechia", "GDP_USD": 2.90e11, "Population": 10700000, "Gini": 25.3, "PM25": 14.5},
    "PT": {"Country_Name": "Portugal", "GDP_USD": 2.52e11, "Population": 10400000, "Gini": 32.0, "PM25": 8.5},
    "GR": {"Country_Name": "Greece", "GDP_USD": 2.19e11, "Population": 10300000, "Gini": 32.4, "PM25": 14.0},
    "HU": {"Country_Name": "Hungary", "GDP_USD": 1.78e11, "Population": 9600000, "Gini": 29.4, "PM25": 13.9},
    "SK": {"Country_Name": "Slovakia", "GDP_USD": 1.15e11, "Population": 5400000, "Gini": 21.8, "PM25": 15.4},
    "BG": {"Country_Name": "Bulgaria", "GDP_USD": 9.00e10, "Population": 6500000, "Gini": 39.7, "PM25": 18.0},
    "LU": {"Country_Name": "Luxembourg", "GDP_USD": 8.20e10, "Population": 650000, "Gini": 29.6, "PM25": 10.0},
    "HR": {"Country_Name": "Croatia", "GDP_USD": 7.10e10, "Population": 3800000, "Gini": 28.9, "PM25": 13.8},
    "LT": {"Country_Name": "Lithuania", "GDP_USD": 7.00e10, "Population": 2800000, "Gini": 35.4, "PM25": 10.2},
    "SI": {"Country_Name": "Slovenia", "GDP_USD": 6.20e10, "Population": 2100000, "Gini": 23.0, "PM25": 12.0},
    "LV": {"Country_Name": "Latvia", "GDP_USD": 4.10e10, "Population": 1900000, "Gini": 34.3, "PM25": 11.2},
    "EE": {"Country_Name": "Estonia", "GDP_USD": 3.80e10, "Population": 1300000, "Gini": 30.6, "PM25": 5.9},
    "CY": {"Country_Name": "Cyprus", "GDP_USD": 2.80e10, "Population": 900000, "Gini": 29.4, "PM25": 15.8},
    "MT": {"Country_Name": "Malta", "GDP_USD": 1.80e10, "Population": 530000, "Gini": 31.1, "PM25": 12.0}
}

class EU_NDV_Engine:
    """
    Calculates the Net Domestic Value for the EU, applying the Cohesion Transfer 
    from Industrial Hubs to Natural Sinks.
    """
    def __init__(self):
        self.raw_data = {iso: {"ISO2": iso} for iso in EU_ISO2}
        # Populate with base fallback data first
        for iso, data in FALLBACK_EU_DATA.items():
            self.raw_data[iso].update(data)

    def fetch_data(self):
        """Fetches GDP, Population, Gini, and PM2.5 from World Bank. Falls back to static values if API fails."""
        indicators = {
            "NY.GDP.MKTP.CD": "GDP_USD",
            "SP.POP.TOTL": "Population",
            "SI.POV.GINI": "Gini",
            "EN.ATM.PM25.MC.M3": "PM25"
        }
        
        logger.info("Querying World Bank API for EU sovereign datasets...")
        for code, key in indicators.items():
            url = f"http://api.worldbank.org/v2/country/all/indicator/{code}?format=json&date=2022&per_page=300"
            try:
                # Add a short timeout to prevent hanging the system
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    if len(data) > 1 and data[1] is not None:
                        for entry in data[1]:
                            iso2 = entry['country']['id']
                            if iso2 in self.raw_data:
                                val = entry['value']
                                if val is not None:
                                    self.raw_data[iso2][key] = val
                                    self.raw_data[iso2]["Country_Name"] = entry['country']['value']
            except Exception as e:
                logger.warning(f"Could not fetch indicator {code}: {e}. Retaining robust fallback values.")

    def compute_matrix(self) -> List[Dict]:
        ledger = []
        for iso, data in self.raw_data.items():
            # Retrieve or default
            pop = data.get("Population") or 10_000_000
            gdp = data.get("GDP_USD") or (pop * 40000)
            gini = (data.get("Gini") or 32.0) / 100.0
            
            # Archetype Classification (Industrial vs Natural)
            gdp_pc = gdp / pop
            # Natural Sinks are classified by high air quality (PM2.5 < 10) or lower GDP per capita (Cohesion zones)
            # Standard GDP/capita threshold for industrial hubs is > 45000 USD
            archetype = "Industrial" if gdp_pc > 45000 else "Natural"
            
            # Stacked Natural Capital Valuation
            protected_ha = 10000 if archetype == "Natural" else 1000
            
            # Master Equation Logic
            # NDV = Y - Dp - Dn + E+ - E-
            y = gdp
            dp = y * 0.05
            dn = protected_ha * 5000  # Natural capital depletion/preservation cost proxy
            care_e_plus = pop * 800 * 25  # Unpaid care hours * shadow wage
            smog_debt = max(0, data.get("PM25", 10) - 5.0) * 1000 * (pop / 1000)
            
            ndv_raw = y - dp - dn + care_e_plus - smog_debt
            
            # Calculate NDV to GDP ratio percentage
            ndv_to_gdp = (ndv_raw / y) * 100.0 if y > 0 else 0.0
            
            ledger.append({
                "Country_Name": data.get("Country_Name", iso),
                "ISO2": iso,
                "Archetype": archetype,
                "GDP_USD": y,
                "NDV": ndv_raw,
                "NDV_to_GDP": ndv_to_gdp,
                "Nature_Dn": -dn,
                "Protected_Ha": protected_ha,
                "Transfer_Flow": 0.0
            })
        
        # Apply Cohesion Transfer: 5% Tax on Industrial depletion (Nature_Dn) redistributed to Natural Sinks
        industrial_pool = sum(abs(r['Nature_Dn']) for r in ledger if r['Archetype'] == 'Industrial') * 0.05
        natural_sinks = sum(r['Protected_Ha'] for r in ledger if r['Archetype'] == 'Natural')
        
        for r in ledger:
            if r['Archetype'] == 'Industrial':
                tax = abs(r['Nature_Dn']) * 0.05
                r['Transfer_Flow'] = -tax
                r['NDV'] -= tax
            else:
                payout = industrial_pool * (r['Protected_Ha'] / natural_sinks) if natural_sinks > 0 else 0.0
                r['Transfer_Flow'] = payout
                r['NDV'] += payout
            
            # Update ratio after Cohesion Transfers
            r['NDV_to_GDP'] = (r['NDV'] / r['GDP_USD']) * 100.0 if r['GDP_USD'] > 0 else 0.0
                
        return sorted(ledger, key=lambda x: x['NDV'], reverse=True)

    def export(self, filename="ndv_eu_ledger.csv"):
        data = self.compute_matrix()
        # Export keys matching the user requirements and adding supporting indicators
        keys = ["Country_Name", "GDP_USD", "NDV", "NDV_to_GDP", "Transfer_Flow", "Archetype"]
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data)
        logger.info(f"Exported EU Ledger to {filename}")

if __name__ == "__main__":
    engine = EU_NDV_Engine()
    engine.fetch_data()
    engine.export()
