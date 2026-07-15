#!/usr/bin/env python3
"""
Net Domestic Value (NDV) European Sovereign Ledger Engine
Author: Senior Economic Researcher and Lead Systems Engineer
Version: 3.2: Total Project Recovery

This module implements the EU Sovereign Ingestion and Cohesion Matrix calculations.
It computes the NDV for the 27 EU Member States and applies Cohesion Policy 2.0
transfer mechanisms.
"""

import json
import urllib.request
import csv
import logging
from typing import List, Dict
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NDV_EU")

# The 27 EU Member States ISO2 Codes
EU_ISO2 = [
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", 
    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", 
    "PL", "PT", "RO", "SK", "SI", "ES", "SE"
]

@dataclass
class FirstPrinciplesConstants:
    """
    The 'Kernel' Constants. These are the First Principles that govern the NDV calculation.
    They are central and immutable for the system, though tunable by protocol governance.
    """
    SAFE_PM25_THRESHOLD: float = 5.0      # WHO Standard
    SOCIAL_COST_OF_PM25: float = 1250.00   # USD per unit of excess PM2.5 per 1k population
    CARE_ECONOMY_SHADOW_WAGE: float = 25.00 # Median EU Hourly Wage Proxy
    GINI_THRESHOLD: float = 0.32          # EU Target Gini
    GINI_DRAG_MULTIPLIER: float = 0.30 

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

class NDV_Kernel:
    """
    The Base Kernel for the Tokennomics Protocol.
    Strictly enforces: NDV = Y - Dp - Dn + E+ - E-
    """
    def __init__(self, constants: FirstPrinciplesConstants):
        self.c = constants

    def calculate_ndv(self, raw_data: Dict) -> Dict:
        # Extract base indicators
        y = raw_data.get("GDP_USD", 0)
        pop = raw_data.get("Population", 10_000_000)
        
        # 1. PILLAR: Macro-Financial (Depreciation)
        dp = y * 0.04  # 4% standard industrial depreciation
        
        # 2. PILLAR: Biosphere (Depletion)
        protected_ha = raw_data.get("Protected_Ha", 1000)
        dn = (protected_ha * 0.1) * 75000 
        
        # 3. PILLAR: Societal Dividends (E+)
        care_hours = pop * 800
        e_plus = care_hours * self.c.CARE_ECONOMY_SHADOW_WAGE
        
        # 4. PILLAR: Societal Debts (E-)
        # Smog Debt
        pm25 = raw_data.get("PM25", 5.0)
        smog_debt = 0
        if pm25 > self.c.SAFE_PM25_THRESHOLD:
            smog_debt = (pm25 - self.c.SAFE_PM25_THRESHOLD) * self.c.SOCIAL_COST_OF_PM25 * (pop / 1000)
            
        # Inequality Drag (World Bank Gini values are on 0-100 scale, so convert if needed)
        gini_raw = raw_data.get("Gini", 32.0)
        gini = gini_raw / 100.0 if gini_raw > 1.0 else gini_raw
        
        gini_drag = 0
        if gini > self.c.GINI_THRESHOLD:
            gini_drag = y * (gini - self.c.GINI_THRESHOLD) * self.c.GINI_DRAG_MULTIPLIER
            
        e_minus = smog_debt + gini_drag
        
        # MASTER EQUATION
        ndv = y - dp - dn + e_plus - e_minus
        
        return {
            "NDV": ndv,
            "NDV_raw": ndv,
            "Y_Gross": y,
            "E_Plus": e_plus,
            "E_Minus": -e_minus,
            "Nature_Dn": -dn,
            "Protected_Ha": protected_ha
        }

class EU_NDV_Protocol:
    """
    The Protocol Layer. Manages the orchestration of data and 
    the redistribution equilibrium.
    """
    def __init__(self):
        self.constants = FirstPrinciplesConstants()
        self.kernel = NDV_Kernel(self.constants)
        self.ledger = {iso: {"ISO2": iso} for iso in EU_ISO2}
        
        # Pre-populate defaults
        for iso, data in FALLBACK_EU_DATA.items():
            self.ledger[iso].update(data)

    def run_ingestion(self):
        """Fetches live datasets from the World Bank API with robust fallbacks."""
        indicators = {
            "NY.GDP.MKTP.CD": "GDP_USD",
            "SP.POP.TOTL": "Population",
            "SI.POV.GINI": "Gini",
            "EN.ATM.PM25.MC.M3": "PM25"
        }
        
        logger.info("Kernel Ingesting State Data from World Bank API...")
        for code, key in indicators.items():
            url = f"http://api.worldbank.org/v2/country/all/indicator/{code}?format=json&date=2022&per_page=300"
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    if len(data) > 1 and data[1] is not None:
                        for entry in data[1]:
                            iso2 = entry['country']['id']
                            if iso2 in self.ledger:
                                val = entry['value']
                                if val is not None:
                                    self.ledger[iso2][key] = val
                                    self.ledger[iso2]["Country_Name"] = entry['country']['value']
            except Exception as e:
                logger.warning(f"Could not fetch indicator {code}: {e}. Retaining robust fallback values.")

    def compute(self):
        """Runs the NDV calculations and Cohesion transfers across nodes."""
        # Classify and run Kernel
        for iso, data in self.ledger.items():
            # Setup archetype and protected area sizes based on GDP per capita
            gdp = data.get("GDP_USD", 4e11)
            pop = data.get("Population", 10e6)
            gdp_pc = gdp / pop
            
            archetype = "Industrial" if gdp_pc > 45000 else "Natural"
            data["Archetype"] = archetype
            data["Protected_Ha"] = 15000 if archetype == "Natural" else 1500
            
            results = self.kernel.calculate_ndv(data)
            self.ledger[iso].update(results)
            
        # Apply Cohesion Equilibrium (10% Tax on Industrial depletion redistributed to Natural sinks)
        total_tax_pool = sum(abs(r.get("Nature_Dn", 0)) for r in self.ledger.values() if r.get("Archetype") == "Industrial") * 0.10
        natural_sinks_count = sum(1 for r in self.ledger.values() if r.get("Archetype") == "Natural")
        
        for iso, r in self.ledger.items():
            if r.get("Archetype") == "Industrial":
                tax = abs(r.get("Nature_Dn", 0)) * 0.10
                r["NDV"] = r["NDV_raw"] - tax
                r["Equilibrium_Transfer"] = -tax
            else:
                payout = (total_tax_pool / natural_sinks_count) if natural_sinks_count > 0 else 0.0
                r["NDV"] = r["NDV_raw"] + payout
                r["Equilibrium_Transfer"] = payout
            
            # Recalculate final NDV to GDP ratio percentage
            r["NDV_to_GDP"] = (r["NDV"] / r["Y_Gross"]) * 100.0 if r["Y_Gross"] > 0 else 0.0

    def export(self, filename="ndv_eu_ledger.csv"):
        logger.info("Exporting Immutable Sovereign Ledger...")
        keys = ["Country_Name", "GDP_USD", "NDV", "NDV_to_GDP", "Equilibrium_Transfer", "Archetype"]
        
        # Sort by final NDV descending
        sorted_ledger = sorted(self.ledger.values(), key=lambda x: x.get('NDV', 0), reverse=True)
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(sorted_ledger)
        logger.info(f"Exported EU Ledger to {filename}")

if __name__ == "__main__":
    protocol = EU_NDV_Protocol()
    protocol.run_ingestion()
    protocol.compute()
    protocol.export()
    logger.info("Protocol Kernel execution successful.")
