#!/usr/bin/env python3
"""
Net Domestic Value (NDV) European Sovereign Ledger Engine - Institutional Grade (V4.0)
Author: Senior Macroeconomic Data Engineer & Eurostat Systems Architect
Version: 4.0: Institutional Audit Hardening

This module implements the EU Sovereign Ingestion and Cohesion Matrix calculations.
It computes the NDV for the 27 EU Member States using empirical biophysical forest
coverage and Purchasing Power Parity (PPP)-adjusted care shadow wages.
"""

import json
import urllib.request
import csv
import logging
from typing import List, Dict
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NDV_EU_Engine")

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
    GINI_THRESHOLD: float = 0.32          # EU Target Gini
    GINI_DRAG_MULTIPLIER: float = 0.30 

# High-fidelity fallback data in case World Bank API times out or is unreachable
# Forest_SqKm source: World Bank Indicator AG.LND.FRST.K2
FALLBACK_EU_DATA = {
    "DE": {"Country_Name": "Germany", "GDP_USD": 4.07e12, "Population": 84000000, "Gini": 31.7, "PM25": 12.0, "Forest_SqKm": 114190.0},
    "FR": {"Country_Name": "France", "GDP_USD": 2.78e12, "Population": 68000000, "Gini": 32.4, "PM25": 11.5, "Forest_SqKm": 172530.0},
    "IT": {"Country_Name": "Italy", "GDP_USD": 2.01e12, "Population": 59000000, "Gini": 35.2, "PM25": 16.0, "Forest_SqKm": 95660.0},
    "ES": {"Country_Name": "Spain", "GDP_USD": 1.40e12, "Population": 47000000, "Gini": 34.3, "PM25": 9.7, "Forest_SqKm": 185720.0},
    "NL": {"Country_Name": "Netherlands", "GDP_USD": 1.01e12, "Population": 17800000, "Gini": 27.8, "PM25": 12.1, "Forest_SqKm": 3700.0},
    "PL": {"Country_Name": "Poland", "GDP_USD": 6.88e11, "Population": 38000000, "Gini": 30.2, "PM25": 19.4, "Forest_SqKm": 94830.0},
    "SE": {"Country_Name": "Sweden", "GDP_USD": 5.86e11, "Population": 10500000, "Gini": 29.3, "PM25": 5.8, "Forest_SqKm": 279800.0},
    "BE": {"Country_Name": "Belgium", "GDP_USD": 5.82e11, "Population": 11700000, "Gini": 27.2, "PM25": 12.8, "Forest_SqKm": 6800.0},
    "IE": {"Country_Name": "Ireland", "GDP_USD": 5.33e11, "Population": 5100000, "Gini": 29.2, "PM25": 7.2, "Forest_SqKm": 7800.0},
    "AT": {"Country_Name": "Austria", "GDP_USD": 4.71e11, "Population": 9000000, "Gini": 29.8, "PM25": 11.0, "Forest_SqKm": 38990.0},
    "DK": {"Country_Name": "Denmark", "GDP_USD": 4.00e11, "Population": 5900000, "Gini": 27.5, "PM25": 9.6, "Forest_SqKm": 6200.0},
    "FI": {"Country_Name": "Finland", "GDP_USD": 2.81e11, "Population": 5500000, "Gini": 27.7, "PM25": 5.5, "Forest_SqKm": 224090.0},
    "RO": {"Country_Name": "Romania", "GDP_USD": 3.01e11, "Population": 19000000, "Gini": 34.8, "PM25": 15.2, "Forest_SqKm": 69290.0},
    "CZ": {"Country_Name": "Czechia", "GDP_USD": 2.90e11, "Population": 10700000, "Gini": 25.3, "PM25": 14.5, "Forest_SqKm": 26770.0},
    "PT": {"Country_Name": "Portugal", "GDP_USD": 2.52e11, "Population": 10400000, "Gini": 32.0, "PM25": 8.5, "Forest_SqKm": 33120.0},
    "GR": {"Country_Name": "Greece", "GDP_USD": 2.19e11, "Population": 10300000, "Gini": 32.4, "PM25": 14.0, "Forest_SqKm": 39020.0},
    "HU": {"Country_Name": "Hungary", "GDP_USD": 1.78e11, "Population": 9600000, "Gini": 29.4, "PM25": 13.9, "Forest_SqKm": 20530.0},
    "SK": {"Country_Name": "Slovakia", "GDP_USD": 1.15e11, "Population": 5400000, "Gini": 21.8, "PM25": 15.4, "Forest_SqKm": 19250.0},
    "BG": {"Country_Name": "Bulgaria", "GDP_USD": 9.00e10, "Population": 6500000, "Gini": 39.7, "PM25": 18.0, "Forest_SqKm": 38930.0},
    "LU": {"Country_Name": "Luxembourg", "GDP_USD": 8.20e10, "Population": 650000, "Gini": 29.6, "PM25": 10.0, "Forest_SqKm": 890.0},
    "HR": {"Country_Name": "Croatia", "GDP_USD": 7.10e10, "Population": 3800000, "Gini": 28.9, "PM25": 13.8, "Forest_SqKm": 19390.0},
    "LT": {"Country_Name": "Lithuania", "GDP_USD": 7.00e10, "Population": 2800000, "Gini": 35.4, "PM25": 10.2, "Forest_SqKm": 22000.0},
    "SI": {"Country_Name": "Slovenia", "GDP_USD": 6.20e10, "Population": 2100000, "Gini": 23.0, "PM25": 12.0, "Forest_SqKm": 11850.0},
    "LV": {"Country_Name": "Latvia", "GDP_USD": 4.10e10, "Population": 1900000, "Gini": 34.3, "PM25": 11.2, "Forest_SqKm": 34120.0},
    "EE": {"Country_Name": "Estonia", "GDP_USD": 3.80e10, "Population": 1300000, "Gini": 30.6, "PM25": 5.9, "Forest_SqKm": 24390.0},
    "CY": {"Country_Name": "Cyprus", "GDP_USD": 2.80e10, "Population": 900000, "Gini": 29.4, "PM25": 15.8, "Forest_SqKm": 1730.0},
    "MT": {"Country_Name": "Malta", "GDP_USD": 1.80e10, "Population": 530000, "Gini": 31.1, "PM25": 12.0, "Forest_SqKm": 5.0}
}

class NDV_Kernel:
    """
    The Base Kernel for the Tokennomics Protocol.
    Strictly enforces: NDV = Y - Dp - Dn + E+ - E-
    Output attributes standardized to database schema naming conventions.
    """
    def __init__(self, constants: FirstPrinciplesConstants):
        self.c = constants

    def calculate_ndv(self, raw_data: Dict) -> Dict:
        # Standard GDP Input (Y)
        y = float(raw_data.get("GDP_USD", 0))
        pop = float(raw_data.get("Population", 10_000_000))
        
        # 1. PILLAR: Physical Depreciation (Dp)
        dp = y * 0.04  # 4% standard industrial depreciation
        
        # 2. PILLAR: Biosphere Depletion (Dn) - Derived from empirical forest area
        # Convert square kilometers to hectares (1 sq km = 100 hectares)
        forest_sqkm = float(raw_data.get("Forest_SqKm", 1000.0))
        forest_ha = forest_sqkm * 100.0
        
        # Ingested planetary math: 5% annual depreciation coefficient valued at a standard conservation replacement cost
        dn = (forest_ha * 0.05) * 15000.0
        
        # 3. PILLAR: Societal Dividends (E+)
        # Dynamic localized care shadow wage pegged to GDP per capita / 2080 working hours * 40% coefficient
        gdp_pc = y / pop if pop > 0 else 0
        care_shadow_wage = (gdp_pc / 2080.0) * 0.40
        care_hours = pop * 800.0
        e_plus = care_hours * care_shadow_wage
        
        # 4. PILLAR: Societal Debts (E-)
        # Smog Debt (excess PM2.5 above threshold)
        pm25 = float(raw_data.get("PM25", 5.0))
        smog_debt = 0.0
        if pm25 > self.c.SAFE_PM25_THRESHOLD:
            smog_debt = (pm25 - self.c.SAFE_PM25_THRESHOLD) * self.c.SOCIAL_COST_OF_PM25 * (pop / 1000.0)
            
        # Inequality Drag (World Bank Gini values are on 0-100 scale, so convert to 0-1 range)
        gini_raw = float(raw_data.get("Gini", 32.0))
        gini = gini_raw / 100.0 if gini_raw > 1.0 else gini_raw
        
        gini_drag = 0.0
        if gini > self.c.GINI_THRESHOLD:
            gini_drag = y * (gini - self.c.GINI_THRESHOLD) * self.c.GINI_DRAG_MULTIPLIER
            
        e_minus = smog_debt + gini_drag
        
        # MASTER EQUATION: NDV = Y - Dp - Dn + E+ - E-
        ndv = y - dp - dn + e_plus - e_minus
        
        return {
            "gross_domestic_product_usd": y,
            "physical_depreciation_usd": dp,
            "natural_depletion_usd": dn,
            "care_economy_dividend_usd": e_plus,
            "smog_friction_penalty_usd": smog_debt,
            "gini_friction_penalty_usd": gini_drag,
            "net_domestic_value_usd": ndv,
            "forest_area_hectares": forest_ha
        }

class EU_NDV_Protocol:
    """
    The Protocol Layer. Manages the orchestration of data, 
    classification of archetypes, and the cohesion redistribution equilibrium.
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
            "EN.ATM.PM25.MC.M3": "PM25",
            "AG.LND.FRST.K2": "Forest_SqKm"
        }
        
        logger.info("Ingesting EU telemetry from World Bank API...")
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
                logger.warning(f"Could not fetch indicator {code}: {e}. Retaining fallback value.")

    def compute(self):
        """Runs the NDV calculations and Cohesion transfers across nodes."""
        # Classify and run Kernel
        for iso, data in self.ledger.items():
            # Setup archetype classification based on forest density per capita
            # (True biophysical mapping of ecological balance vs industrialization)
            pop = data.get("Population", 10e6)
            forest_sqkm = data.get("Forest_SqKm", 1000.0)
            forest_ha = forest_sqkm * 100.0
            forest_pc = forest_ha / pop if pop > 0 else 0
            
            # Archetype thresholding: Forest coverage per capita
            # Industrial hubs are defined by a high concentration of capital and sparse forest per capita
            cohesion_archetype = "Industrial" if forest_pc < 0.25 else "Natural"
            
            results = self.kernel.calculate_ndv(data)
            self.ledger[iso].update(results)
            self.ledger[iso]["cohesion_archetype"] = cohesion_archetype

        # Apply Cohesion Equilibrium (10% Tax on Industrial depletion redistributed to Natural sinks)
        total_tax_pool = sum(abs(r.get("natural_depletion_usd", 0)) for r in self.ledger.values() if r.get("cohesion_archetype") == "Industrial") * 0.10
        natural_sinks_count = sum(1 for r in self.ledger.values() if r.get("cohesion_archetype") == "Natural")
        
        for iso, r in self.ledger.items():
            if r.get("cohesion_archetype") == "Industrial":
                tax = abs(r.get("natural_depletion_usd", 0)) * 0.10
                r["net_domestic_value_usd"] = r["net_domestic_value_usd"] - tax
                r["equilibrium_transfer_usd"] = -tax
            else:
                payout = (total_tax_pool / natural_sinks_count) if natural_sinks_count > 0 else 0.0
                r["net_domestic_value_usd"] = r["net_domestic_value_usd"] + payout
                r["equilibrium_transfer_usd"] = payout
            
            # Recalculate final NDV to GDP ratio percentage
            r["ndv_to_gdp_ratio"] = (r["net_domestic_value_usd"] / r["gross_domestic_product_usd"]) * 100.0 if r["gross_domestic_product_usd"] > 0 else 0.0

    def export(self, filename="ndv_eu_ledger.csv"):
        logger.info("Exporting Standardized database ledger...")
        keys = [
            "Country_Name", "gross_domestic_product_usd", "net_domestic_value_usd",
            "ndv_to_gdp_ratio", "equilibrium_transfer_usd", "cohesion_archetype"
        ]
        
        # Sort by final NDV descending
        sorted_ledger = sorted(self.ledger.values(), key=lambda x: x.get('net_domestic_value_usd', 0), reverse=True)
        
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
