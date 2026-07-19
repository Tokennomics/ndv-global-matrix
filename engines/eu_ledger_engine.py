#!/usr/bin/env python3
"""
Net Domestic Value (NDV) European Sovereign Ledger Engine - V4.0 Omni-Matrix Edition
Author: Lead Biophysical Economics Engineer & Systems Architect
Version: 4.0: EROI, Cognitive Depletion, and Financialization Frictions

This module implements the EU Sovereign Ingestion and Cohesion Matrix calculations
for the V4.0 Omni-Matrix. It computes:
NDV = (Y * phi_eroi) - (Dp + Dn + Dc) + E+ - (E- + E_rent)
"""

import json
import urllib.request
import csv
import logging
from typing import List, Dict
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NDV_EU_Engine_V4")

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
# Pre-seeded with EROI imports, internet penetration, and FIRE sector shares
FALLBACK_EU_DATA = {
    "DE": {"Country_Name": "Germany", "GDP_USD": 4.07e12, "Population": 84000000, "Gini": 31.7, "PM25": 12.0, "Forest_SqKm": 114190.0, "Energy_Imports_Pct": 61.2, "Internet_Users_Pct": 91.5, "Fire_Pct": 0.065},
    "FR": {"Country_Name": "France", "GDP_USD": 2.78e12, "Population": 68000000, "Gini": 32.4, "PM25": 11.5, "Forest_SqKm": 172530.0, "Energy_Imports_Pct": 44.5, "Internet_Users_Pct": 92.0, "Fire_Pct": 0.060},
    "IT": {"Country_Name": "Italy", "GDP_USD": 2.01e12, "Population": 59000000, "Gini": 35.2, "PM25": 16.0, "Forest_SqKm": 95660.0, "Energy_Imports_Pct": 73.5, "Internet_Users_Pct": 85.2, "Fire_Pct": 0.055},
    "ES": {"Country_Name": "Spain", "GDP_USD": 1.40e12, "Population": 47000000, "Gini": 34.3, "PM25": 9.7, "Forest_SqKm": 185720.0, "Energy_Imports_Pct": 68.1, "Internet_Users_Pct": 93.9, "Fire_Pct": 0.050},
    "NL": {"Country_Name": "Netherlands", "GDP_USD": 1.01e12, "Population": 17800000, "Gini": 27.8, "PM25": 12.1, "Forest_SqKm": 3700.0, "Energy_Imports_Pct": 63.8, "Internet_Users_Pct": 96.0, "Fire_Pct": 0.100},
    "PL": {"Country_Name": "Poland", "GDP_USD": 6.88e11, "Population": 38000000, "Gini": 30.2, "PM25": 19.4, "Forest_SqKm": 94830.0, "Energy_Imports_Pct": 43.1, "Internet_Users_Pct": 88.4, "Fire_Pct": 0.050},
    "SE": {"Country_Name": "Sweden", "GDP_USD": 5.86e11, "Population": 10500000, "Gini": 29.3, "PM25": 5.8, "Forest_SqKm": 279800.0, "Energy_Imports_Pct": -33.2, "Internet_Users_Pct": 98.2, "Fire_Pct": 0.055},
    "BE": {"Country_Name": "Belgium", "GDP_USD": 5.82e11, "Population": 11700000, "Gini": 27.2, "PM25": 12.8, "Forest_SqKm": 6800.0, "Energy_Imports_Pct": 77.4, "Internet_Users_Pct": 94.1, "Fire_Pct": 0.062},
    "IE": {"Country_Name": "Ireland", "GDP_USD": 5.33e11, "Population": 5100000, "Gini": 29.2, "PM25": 7.2, "Forest_SqKm": 7800.0, "Energy_Imports_Pct": 69.8, "Internet_Users_Pct": 95.5, "Fire_Pct": 0.180},
    "AT": {"Country_Name": "Austria", "GDP_USD": 4.71e11, "Population": 9000000, "Gini": 29.8, "PM25": 11.0, "Forest_SqKm": 38990.0, "Energy_Imports_Pct": 58.5, "Internet_Users_Pct": 92.5, "Fire_Pct": 0.058},
    "DK": {"Country_Name": "Denmark", "GDP_USD": 4.00e11, "Population": 5900000, "Gini": 27.5, "PM25": 9.6, "Forest_SqKm": 6200.0, "Energy_Imports_Pct": -12.1, "Internet_Users_Pct": 98.9, "Fire_Pct": 0.065},
    "FI": {"Country_Name": "Finland", "GDP_USD": 2.81e11, "Population": 5500000, "Gini": 27.7, "PM25": 5.5, "Forest_SqKm": 224090.0, "Energy_Imports_Pct": 42.8, "Internet_Users_Pct": 97.7, "Fire_Pct": 0.048},
    "RO": {"Country_Name": "Romania", "GDP_USD": 3.01e11, "Population": 19000000, "Gini": 34.8, "PM25": 15.2, "Forest_SqKm": 69290.0, "Energy_Imports_Pct": 31.0, "Internet_Users_Pct": 88.0, "Fire_Pct": 0.040},
    "CZ": {"Country_Name": "Czechia", "GDP_USD": 2.90e11, "Population": 10700000, "Gini": 25.3, "PM25": 14.5, "Forest_SqKm": 26770.0, "Energy_Imports_Pct": 38.5, "Internet_Users_Pct": 91.2, "Fire_Pct": 0.048},
    "PT": {"Country_Name": "Portugal", "GDP_USD": 2.52e11, "Population": 10400000, "Gini": 32.0, "PM25": 8.5, "Forest_SqKm": 33120.0, "Energy_Imports_Pct": 71.0, "Internet_Users_Pct": 86.4, "Fire_Pct": 0.052},
    "GR": {"Country_Name": "Greece", "GDP_USD": 2.19e11, "Population": 10300000, "Gini": 32.4, "PM25": 14.0, "Forest_SqKm": 39020.0, "Energy_Imports_Pct": 78.4, "Internet_Users_Pct": 82.5, "Fire_Pct": 0.055},
    "HU": {"Country_Name": "Hungary", "GDP_USD": 1.78e11, "Population": 9600000, "Gini": 29.4, "PM25": 13.9, "Forest_SqKm": 20530.0, "Energy_Imports_Pct": 56.4, "Internet_Users_Pct": 89.0, "Fire_Pct": 0.045},
    "SK": {"Country_Name": "Slovakia", "GDP_USD": 1.15e11, "Population": 5400000, "Gini": 21.8, "PM25": 15.4, "Forest_SqKm": 19250.0, "Energy_Imports_Pct": 60.1, "Internet_Users_Pct": 90.1, "Fire_Pct": 0.042},
    "BG": {"Country_Name": "Bulgaria", "GDP_USD": 9.00e10, "Population": 6500000, "Gini": 39.7, "PM25": 18.0, "Forest_SqKm": 38930.0, "Energy_Imports_Pct": 38.0, "Internet_Users_Pct": 83.2, "Fire_Pct": 0.040},
    "LU": {"Country_Name": "Luxembourg", "GDP_USD": 8.20e10, "Population": 650000, "Gini": 29.6, "PM25": 10.0, "Forest_SqKm": 890.0, "Energy_Imports_Pct": 95.8, "Internet_Users_Pct": 98.8, "Fire_Pct": 0.280},
    "HR": {"Country_Name": "Croatia", "GDP_USD": 7.10e10, "Population": 3800000, "Gini": 28.9, "PM25": 13.8, "Forest_SqKm": 19390.0, "Energy_Imports_Pct": 51.5, "Internet_Users_Pct": 86.0, "Fire_Pct": 0.045},
    "LT": {"Country_Name": "Lithuania", "GDP_USD": 7.00e10, "Population": 2800000, "Gini": 35.4, "PM25": 10.2, "Forest_SqKm": 22000.0, "Energy_Imports_Pct": 72.5, "Internet_Users_Pct": 89.2, "Fire_Pct": 0.042},
    "SI": {"Country_Name": "Slovenia", "GDP_USD": 6.20e10, "Population": 2100000, "Gini": 23.0, "PM25": 12.0, "Forest_SqKm": 11850.0, "Energy_Imports_Pct": 49.0, "Internet_Users_Pct": 89.8, "Fire_Pct": 0.045},
    "LV": {"Country_Name": "Latvia", "GDP_USD": 4.10e10, "Population": 1900000, "Gini": 34.3, "PM25": 11.2, "Forest_SqKm": 34120.0, "Energy_Imports_Pct": 48.0, "Internet_Users_Pct": 91.0, "Fire_Pct": 0.040},
    "EE": {"Country_Name": "Estonia", "GDP_USD": 3.80e10, "Population": 1300000, "Gini": 30.6, "PM25": 5.9, "Forest_SqKm": 24390.0, "Energy_Imports_Pct": 12.0, "Internet_Users_Pct": 92.5, "Fire_Pct": 0.045},
    "CY": {"Country_Name": "Cyprus", "GDP_USD": 2.80e10, "Population": 900000, "Gini": 29.4, "PM25": 15.8, "Forest_SqKm": 1730.0, "Energy_Imports_Pct": 88.5, "Internet_Users_Pct": 90.0, "Fire_Pct": 0.120},
    "MT": {"Country_Name": "Malta", "GDP_USD": 1.80e10, "Population": 530000, "Gini": 31.1, "PM25": 12.0, "Forest_SqKm": 5.0, "Energy_Imports_Pct": 97.2, "Internet_Users_Pct": 92.0, "Fire_Pct": 0.100}
}

class OmniMatrixKernel:
    """
    The Base Kernel for the Tokennomics V4.0 Protocol.
    Strictly enforces: NDV = (Y * phi_eroi) - (Dp + Dn + Dc) + E+ - (E- + E_rent)
    """
    def __init__(self, constants: FirstPrinciplesConstants):
        self.c = constants

    def calculate_ndv(self, raw_data: Dict) -> Dict:
        # Standard GDP Input (Y)
        y = float(raw_data.get("GDP_USD", 0.0))
        pop = float(raw_data.get("Population", 10_000_000.0))
        
        # 1. PILLAR: Thermodynamic GDP Adjustment (Y * phi_eroi)
        # EROI proxy derived from net energy import dependency. Exporters get bonus; importers penalized.
        energy_imports_pct = float(raw_data.get("Energy_Imports_Pct", 50.0))
        if energy_imports_pct >= 0:
            phi_eroi = max(0.80, 1.0 - (energy_imports_pct / 100.0) * 0.15)
        else:
            phi_eroi = min(1.03, 1.0 - (energy_imports_pct / 100.0) * 0.05)
            
        thermodynamic_gdp = y * phi_eroi
        
        # 2. PILLAR: Physical Depreciation (Dp)
        dp = y * 0.04
        
        # 3. PILLAR: Biosphere Depletion (Dn)
        forest_sqkm = float(raw_data.get("Forest_SqKm", 1000.0))
        forest_ha = forest_sqkm * 100.0
        dn = (forest_ha * 0.05) * 15000.0
        
        # 4. PILLAR: Cognitive Depletion (Dc) - Attention extraction screen time drag
        internet_users_pct = float(raw_data.get("Internet_Users_Pct", 85.0))
        # $4,380 social debt penalty per internet user per year representing attention extraction
        dc = pop * (internet_users_pct / 100.0) * 4380.0
        
        # 5. PILLAR: Societal Dividends (E+) - Dynamic localized care shadow wage
        gdp_pc = y / pop if pop > 0 else 0
        care_shadow_wage = (gdp_pc / 2080.0) * 0.40
        care_hours = pop * 800.0
        e_plus = care_hours * care_shadow_wage
        
        # 6. PILLAR: Societal Debts (E-) - Smog & Inequality Frictions
        pm25 = float(raw_data.get("PM25", 5.0))
        smog_debt = 0.0
        if pm25 > self.c.SAFE_PM25_THRESHOLD:
            smog_debt = (pm25 - self.c.SAFE_PM25_THRESHOLD) * self.c.SOCIAL_COST_OF_PM25 * (pop / 1000.0)
            
        gini_raw = float(raw_data.get("Gini", 32.0))
        gini = gini_raw / 100.0 if gini_raw > 1.0 else gini_raw
        gini_drag = 0.0
        if gini > self.c.GINI_THRESHOLD:
            gini_drag = y * (gini - self.c.GINI_THRESHOLD) * self.c.GINI_DRAG_MULTIPLIER
            
        e_minus = smog_debt + gini_drag
        
        # 7. PILLAR: Financialization Friction (E_rent) - FIRE Sector Rent Seeking
        fire_pct = float(raw_data.get("Fire_Pct", 0.055))
        fire_friction = y * fire_pct
        
        # MASTER V4.0 EQUATION: NDV = (Y * phi_eroi) - (Dp + Dn + Dc) + E+ - (E- + E_rent)
        ndv = thermodynamic_gdp - (dp + dn + dc) + e_plus - (e_minus + fire_friction)
        
        return {
            "gross_domestic_product_usd": y,
            "thermodynamic_gdp_usd": thermodynamic_gdp,
            "physical_depreciation_usd": dp,
            "natural_depletion_usd": dn,
            "cognitive_depletion_usd": dc,
            "care_economy_dividend_usd": e_plus,
            "smog_friction_penalty_usd": smog_debt,
            "gini_friction_penalty_usd": gini_drag,
            "financialization_friction_usd": fire_friction,
            "net_domestic_value_usd": ndv,
            "forest_area_hectares": forest_ha
        }

class EU_NDV_Protocol:
    def __init__(self):
        self.constants = FirstPrinciplesConstants()
        self.kernel = OmniMatrixKernel(self.constants)
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
            "AG.LND.FRST.K2": "Forest_SqKm",
            "EG.IMP.CONS.ZS": "Energy_Imports_Pct",
            "IT.NET.USER.ZS": "Internet_Users_Pct"
        }
        
        logger.info("Ingesting EU V4.0 telemetry from World Bank API...")
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
            # Setup dynamic FIRE sector lookup and updates
            # Luxembourg (LU) at 28%, Ireland (IE) at 18%, Cyprus (CY) at 12%
            fire_share_map = {
                "LU": 0.28, "IE": 0.18, "CY": 0.12, "NL": 0.10, "DE": 0.065, "FR": 0.060, "IT": 0.055, "ES": 0.050
            }
            data["Fire_Pct"] = fire_share_map.get(iso, 0.055)
            
            pop = data.get("Population", 10e6)
            forest_sqkm = data.get("Forest_SqKm", 1000.0)
            forest_ha = forest_sqkm * 100.0
            forest_pc = forest_ha / pop if pop > 0 else 0
            
            # Archetype thresholding: Forest coverage per capita
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
        logger.info("Exporting Standardized V4.0 database ledger...")
        keys = [
            "Country_Name", "gross_domestic_product_usd", "thermodynamic_gdp_usd", 
            "net_domestic_value_usd", "ndv_to_gdp_ratio", "equilibrium_transfer_usd", 
            "cognitive_depletion_usd", "financialization_friction_usd", "cohesion_archetype"
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
    logger.info("Protocol V4.0 Kernel execution successful.")
