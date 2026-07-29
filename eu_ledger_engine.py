#!/usr/bin/env python3
"""
Net Domestic Value (NDV) European Sovereign Ledger Engine - Dual Mode Edition
Author: Lead Systems Architect & Biophysical Economist
Version: Dual Architecture: General NDV (Policy Mode) & Special NDV (Quantum Frontier Mode)
"""

import json
import urllib.request
import csv
import logging
import math
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NDV_EU_Dual_Engine")

EU_ISO2 = [
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", 
    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", 
    "PL", "PT", "RO", "SK", "SI", "ES", "SE"
]

FALLBACK_EU_DATA = {
    "DE": {"Country_Name": "Germany", "GDP_USD": 4.07e12, "Population": 84000000, "Gini": 31.7, "PM25": 12.0, "Forest_SqKm": 114190.0, "Energy_Imports_Pct": 61.2, "Internet_Users_Pct": 91.5, "Fire_Pct": 0.065, "Imports_Pct": 42.0, "Exports_Pct": 47.0, "Health_Exp_Pct": 12.8, "RD_Exp_Pct": 3.1, "OldAge_Dep_Pct": 36.8, "Trust_Index": 0.68, "AI_Compute_Pct": 0.028},
    "FR": {"Country_Name": "France", "GDP_USD": 2.78e12, "Population": 68000000, "Gini": 32.4, "PM25": 11.5, "Forest_SqKm": 172530.0, "Energy_Imports_Pct": 44.5, "Internet_Users_Pct": 92.0, "Fire_Pct": 0.060, "Imports_Pct": 35.0, "Exports_Pct": 32.0, "Health_Exp_Pct": 12.2, "RD_Exp_Pct": 2.2, "OldAge_Dep_Pct": 35.1, "Trust_Index": 0.52, "AI_Compute_Pct": 0.022},
    "IT": {"Country_Name": "Italy", "GDP_USD": 2.01e12, "Population": 59000000, "Gini": 35.2, "PM25": 16.0, "Forest_SqKm": 95660.0, "Energy_Imports_Pct": 73.5, "Internet_Users_Pct": 85.2, "Fire_Pct": 0.055, "Imports_Pct": 33.0, "Exports_Pct": 34.0, "Health_Exp_Pct": 9.6, "RD_Exp_Pct": 1.5, "OldAge_Dep_Pct": 38.2, "Trust_Index": 0.48, "AI_Compute_Pct": 0.015},
    "ES": {"Country_Name": "Spain", "GDP_USD": 1.40e12, "Population": 47000000, "Gini": 34.3, "PM25": 9.7, "Forest_SqKm": 185720.0, "Energy_Imports_Pct": 68.1, "Internet_Users_Pct": 93.9, "Fire_Pct": 0.050, "Imports_Pct": 32.0, "Exports_Pct": 35.0, "Health_Exp_Pct": 10.7, "RD_Exp_Pct": 1.4, "OldAge_Dep_Pct": 30.5, "Trust_Index": 0.50, "AI_Compute_Pct": 0.018},
    "NL": {"Country_Name": "Netherlands", "GDP_USD": 1.01e12, "Population": 17800000, "Gini": 27.8, "PM25": 12.1, "Forest_SqKm": 3700.0, "Energy_Imports_Pct": 63.8, "Internet_Users_Pct": 96.0, "Fire_Pct": 0.100, "Imports_Pct": 65.0, "Exports_Pct": 75.0, "Health_Exp_Pct": 11.2, "RD_Exp_Pct": 2.3, "OldAge_Dep_Pct": 31.2, "Trust_Index": 0.72, "AI_Compute_Pct": 0.035},
    "PL": {"Country_Name": "Poland", "GDP_USD": 6.88e11, "Population": 38000000, "Gini": 30.2, "PM25": 19.4, "Forest_SqKm": 94830.0, "Energy_Imports_Pct": 43.1, "Internet_Users_Pct": 88.4, "Fire_Pct": 0.050, "Imports_Pct": 50.0, "Exports_Pct": 52.0, "Health_Exp_Pct": 6.5, "RD_Exp_Pct": 1.4, "OldAge_Dep_Pct": 28.5, "Trust_Index": 0.45, "AI_Compute_Pct": 0.012},
    "SE": {"Country_Name": "Sweden", "GDP_USD": 5.86e11, "Population": 10500000, "Gini": 29.3, "PM25": 5.8, "Forest_SqKm": 279800.0, "Energy_Imports_Pct": -33.2, "Internet_Users_Pct": 98.2, "Fire_Pct": 0.055, "Imports_Pct": 45.0, "Exports_Pct": 50.0, "Health_Exp_Pct": 11.4, "RD_Exp_Pct": 3.4, "OldAge_Dep_Pct": 32.1, "Trust_Index": 0.75, "AI_Compute_Pct": 0.030},
    "BE": {"Country_Name": "Belgium", "GDP_USD": 5.82e11, "Population": 11700000, "Gini": 27.2, "PM25": 12.8, "Forest_SqKm": 6800.0, "Energy_Imports_Pct": 77.4, "Internet_Users_Pct": 94.1, "Fire_Pct": 0.062, "Imports_Pct": 82.0, "Exports_Pct": 85.0, "Health_Exp_Pct": 10.9, "RD_Exp_Pct": 3.2, "OldAge_Dep_Pct": 30.8, "Trust_Index": 0.60, "AI_Compute_Pct": 0.025},
    "IE": {"Country_Name": "Ireland", "GDP_USD": 5.33e11, "Population": 5100000, "Gini": 29.2, "PM25": 7.2, "Forest_SqKm": 7800.0, "Energy_Imports_Pct": 69.8, "Internet_Users_Pct": 95.5, "Fire_Pct": 0.180, "Imports_Pct": 105.0, "Exports_Pct": 135.0, "Health_Exp_Pct": 6.7, "RD_Exp_Pct": 1.2, "OldAge_Dep_Pct": 22.4, "Trust_Index": 0.65, "AI_Compute_Pct": 0.040},
    "AT": {"Country_Name": "Austria", "GDP_USD": 4.71e11, "Population": 9000000, "Gini": 29.8, "PM25": 11.0, "Forest_SqKm": 38990.0, "Energy_Imports_Pct": 58.5, "Internet_Users_Pct": 92.5, "Fire_Pct": 0.058, "Imports_Pct": 49.0, "Exports_Pct": 53.0, "Health_Exp_Pct": 11.3, "RD_Exp_Pct": 3.1, "OldAge_Dep_Pct": 29.8, "Trust_Index": 0.64, "AI_Compute_Pct": 0.022},
    "DK": {"Country_Name": "Denmark", "GDP_USD": 4.00e11, "Population": 5900000, "Gini": 27.5, "PM25": 9.6, "Forest_SqKm": 6200.0, "Energy_Imports_Pct": -12.1, "Internet_Users_Pct": 98.9, "Fire_Pct": 0.065, "Imports_Pct": 48.0, "Exports_Pct": 54.0, "Health_Exp_Pct": 10.8, "RD_Exp_Pct": 3.0, "OldAge_Dep_Pct": 31.5, "Trust_Index": 0.78, "AI_Compute_Pct": 0.028},
    "FI": {"Country_Name": "Finland", "GDP_USD": 2.81e11, "Population": 5500000, "Gini": 27.7, "PM25": 5.5, "Forest_SqKm": 224090.0, "Energy_Imports_Pct": 42.8, "Internet_Users_Pct": 97.7, "Fire_Pct": 0.048, "Imports_Pct": 39.0, "Exports_Pct": 42.0, "Health_Exp_Pct": 10.0, "RD_Exp_Pct": 2.9, "OldAge_Dep_Pct": 36.2, "Trust_Index": 0.74, "AI_Compute_Pct": 0.025},
    "RO": {"Country_Name": "Romania", "GDP_USD": 3.01e11, "Population": 19000000, "Gini": 34.8, "PM25": 15.2, "Forest_SqKm": 69290.0, "Energy_Imports_Pct": 31.0, "Internet_Users_Pct": 88.0, "Fire_Pct": 0.040, "Imports_Pct": 41.0, "Exports_Pct": 32.0, "Health_Exp_Pct": 6.3, "RD_Exp_Pct": 0.5, "OldAge_Dep_Pct": 29.1, "Trust_Index": 0.40, "AI_Compute_Pct": 0.008},
    "CZ": {"Country_Name": "Czechia", "GDP_USD": 2.90e11, "Population": 10700000, "Gini": 25.3, "PM25": 14.5, "Forest_SqKm": 26770.0, "Energy_Imports_Pct": 38.5, "Internet_Users_Pct": 91.2, "Fire_Pct": 0.048, "Imports_Pct": 62.0, "Exports_Pct": 66.0, "Health_Exp_Pct": 7.7, "RD_Exp_Pct": 2.0, "OldAge_Dep_Pct": 31.0, "Trust_Index": 0.52, "AI_Compute_Pct": 0.015},
    "PT": {"Country_Name": "Portugal", "GDP_USD": 2.52e11, "Population": 10400000, "Gini": 32.0, "PM25": 8.5, "Forest_SqKm": 33120.0, "Energy_Imports_Pct": 71.0, "Internet_Users_Pct": 86.4, "Fire_Pct": 0.052, "Imports_Pct": 43.0, "Exports_Pct": 46.0, "Health_Exp_Pct": 10.6, "RD_Exp_Pct": 1.6, "OldAge_Dep_Pct": 35.5, "Trust_Index": 0.48, "AI_Compute_Pct": 0.012},
    "GR": {"Country_Name": "Greece", "GDP_USD": 2.19e11, "Population": 10300000, "Gini": 32.4, "PM25": 14.0, "Forest_SqKm": 39020.0, "Energy_Imports_Pct": 78.4, "Internet_Users_Pct": 82.5, "Fire_Pct": 0.055, "Imports_Pct": 45.0, "Exports_Pct": 38.0, "Health_Exp_Pct": 9.2, "RD_Exp_Pct": 1.5, "OldAge_Dep_Pct": 35.2, "Trust_Index": 0.42, "AI_Compute_Pct": 0.010},
    "HU": {"Country_Name": "Hungary", "GDP_USD": 1.78e11, "Population": 9600000, "Gini": 29.4, "PM25": 13.9, "Forest_SqKm": 20530.0, "Energy_Imports_Pct": 56.4, "Internet_Users_Pct": 89.0, "Fire_Pct": 0.045, "Imports_Pct": 78.0, "Exports_Pct": 81.0, "Health_Exp_Pct": 7.3, "RD_Exp_Pct": 1.6, "OldAge_Dep_Pct": 30.5, "Trust_Index": 0.46, "AI_Compute_Pct": 0.012},
    "SK": {"Country_Name": "Slovakia", "GDP_USD": 1.15e11, "Population": 5400000, "Gini": 21.8, "PM25": 15.4, "Forest_SqKm": 19250.0, "Energy_Imports_Pct": 60.1, "Internet_Users_Pct": 90.1, "Fire_Pct": 0.042, "Imports_Pct": 85.0, "Exports_Pct": 88.0, "Health_Exp_Pct": 7.2, "RD_Exp_Pct": 0.9, "OldAge_Dep_Pct": 25.5, "Trust_Index": 0.44, "AI_Compute_Pct": 0.009},
    "BG": {"Country_Name": "Bulgaria", "GDP_USD": 9.00e10, "Population": 6500000, "Gini": 39.7, "PM25": 18.0, "Forest_SqKm": 38930.0, "Energy_Imports_Pct": 38.0, "Internet_Users_Pct": 83.2, "Fire_Pct": 0.040, "Imports_Pct": 64.0, "Exports_Pct": 60.0, "Health_Exp_Pct": 8.0, "RD_Exp_Pct": 0.8, "OldAge_Dep_Pct": 33.8, "Trust_Index": 0.38, "AI_Compute_Pct": 0.007},
    "LU": {"Country_Name": "Luxembourg", "GDP_USD": 8.20e10, "Population": 650000, "Gini": 29.6, "PM25": 10.0, "Forest_SqKm": 890.0, "Energy_Imports_Pct": 95.8, "Internet_Users_Pct": 98.8, "Fire_Pct": 0.280, "Imports_Pct": 140.0, "Exports_Pct": 170.0, "Health_Exp_Pct": 5.5, "RD_Exp_Pct": 1.0, "OldAge_Dep_Pct": 21.2, "Trust_Index": 0.68, "AI_Compute_Pct": 0.030},
    "HR": {"Country_Name": "Croatia", "GDP_USD": 7.10e10, "Population": 3800000, "Gini": 28.9, "PM25": 13.8, "Forest_SqKm": 19390.0, "Energy_Imports_Pct": 51.5, "Internet_Users_Pct": 86.0, "Fire_Pct": 0.045, "Imports_Pct": 48.0, "Exports_Pct": 42.0, "Health_Exp_Pct": 7.4, "RD_Exp_Pct": 1.0, "OldAge_Dep_Pct": 34.2, "Trust_Index": 0.42, "AI_Compute_Pct": 0.008},
    "LT": {"Country_Name": "Lithuania", "GDP_USD": 7.00e10, "Population": 2800000, "Gini": 35.4, "PM25": 10.2, "Forest_SqKm": 22000.0, "Energy_Imports_Pct": 72.5, "Internet_Users_Pct": 89.2, "Fire_Pct": 0.042, "Imports_Pct": 74.0, "Exports_Pct": 78.0, "Health_Exp_Pct": 7.0, "RD_Exp_Pct": 1.0, "OldAge_Dep_Pct": 31.8, "Trust_Index": 0.50, "AI_Compute_Pct": 0.010},
    "SI": {"Country_Name": "Slovenia", "GDP_USD": 6.20e10, "Population": 2100000, "Gini": 23.0, "PM25": 12.0, "Forest_SqKm": 11850.0, "Energy_Imports_Pct": 49.0, "Internet_Users_Pct": 89.8, "Fire_Pct": 0.045, "Imports_Pct": 76.0, "Exports_Pct": 82.0, "Health_Exp_Pct": 8.5, "RD_Exp_Pct": 2.1, "OldAge_Dep_Pct": 32.5, "Trust_Index": 0.52, "AI_Compute_Pct": 0.012},
    "LV": {"Country_Name": "Latvia", "GDP_USD": 4.10e10, "Population": 1900000, "Gini": 34.3, "PM25": 11.2, "Forest_SqKm": 34120.0, "Energy_Imports_Pct": 48.0, "Internet_Users_Pct": 91.0, "Fire_Pct": 0.040, "Imports_Pct": 61.0, "Exports_Pct": 60.0, "Health_Exp_Pct": 6.6, "RD_Exp_Pct": 0.7, "OldAge_Dep_Pct": 32.8, "Trust_Index": 0.45, "AI_Compute_Pct": 0.008},
    "EE": {"Country_Name": "Estonia", "GDP_USD": 3.80e10, "Population": 1300000, "Gini": 30.6, "PM25": 5.9, "Forest_SqKm": 24390.0, "Energy_Imports_Pct": 12.0, "Internet_Users_Pct": 92.5, "Fire_Pct": 0.045, "Imports_Pct": 72.0, "Exports_Pct": 78.0, "Health_Exp_Pct": 7.8, "RD_Exp_Pct": 1.8, "OldAge_Dep_Pct": 31.0, "Trust_Index": 0.62, "AI_Compute_Pct": 0.020},
    "CY": {"Country_Name": "Cyprus", "GDP_USD": 2.80e10, "Population": 900000, "Gini": 29.4, "PM25": 15.8, "Forest_SqKm": 1730.0, "Energy_Imports_Pct": 88.5, "Internet_Users_Pct": 90.0, "Fire_Pct": 0.120, "Imports_Pct": 81.0, "Exports_Pct": 77.0, "Health_Exp_Pct": 7.2, "RD_Exp_Pct": 0.8, "OldAge_Dep_Pct": 24.5, "Trust_Index": 0.48, "AI_Compute_Pct": 0.010},
    "MT": {"Country_Name": "Malta", "GDP_USD": 1.80e10, "Population": 530000, "Gini": 31.1, "PM25": 12.0, "Forest_SqKm": 5.0, "Energy_Imports_Pct": 97.2, "Internet_Users_Pct": 92.0, "Fire_Pct": 0.100, "Imports_Pct": 98.0, "Exports_Pct": 102.0, "Health_Exp_Pct": 7.5, "RD_Exp_Pct": 0.7, "OldAge_Dep_Pct": 28.1, "Trust_Index": 0.55, "AI_Compute_Pct": 0.012}
}

class EU_NDV_Dual_Protocol:
    def __init__(self):
        self.ledger = {iso: {"ISO2": iso} for iso in EU_ISO2}
        for iso, data in FALLBACK_EU_DATA.items():
            self.ledger[iso].update(data)

    def compute(self):
        for iso, data in self.ledger.items():
            y = float(data.get("GDP_USD", 0.0))
            pop = float(data.get("Population", 10e6))
            gdp_pc = y / pop if pop > 0 else 0
            
            energy_imports = float(data.get("Energy_Imports_Pct", 50.0))
            eroi = max(1.5, 20.0 - (energy_imports / 100.0) * (15.0 if energy_imports >= 0 else 5.0))
            thermo_gdp = y * (1.0 - (1.0 / eroi))

            dp = y * 0.04
            forest_ha = float(data.get("Forest_SqKm", 1000.0)) * 100.0
            dn = (forest_ha * 0.05) * 15000.0
            dc = pop * (float(data.get("Internet_Users_Pct", 85.0)) / 100.0) * 4380.0
            
            pm25 = float(data.get("PM25", 10.0))
            smog = max(0, (pm25 - 5.0) * 800 * (pop / 1000.0))
            gini = float(data.get("Gini", 30.0)) / 100.0
            gini_drag = max(0, (gini - 0.35) * y * 0.25)
            e_minus = smog + gini_drag

            dm_raw = (y * (float(data.get("Health_Exp_Pct", 8.0)) / 100.0) * 1.20) + (pop * 750.0 * (1.0 + (gdp_pc / 80000.0)))
            dm = max(dm_raw * 0.20, dm_raw - (0.15 * smog))

            de = max(0.0, (y * 0.05) - (y * (float(data.get("RD_Exp_Pct", 1.5)) / 100.0) * 2.0))
            ds = y * (1.0 - float(data.get("Trust_Index", 0.55))) * 0.04
            dai = y * float(data.get("AI_Compute_Pct", 0.02)) * 1.35
            
            oldage_dep = float(data.get("OldAge_Dep_Pct", 25.0))
            ddemo = max(0.0, y * ((oldage_dep - 30.0) / 100.0) * 0.75) if oldage_dep > 30.0 else 0.0

            e_plus = (pop * 800.0) * ((gdp_pc / 2080.0) * 0.40)
            fire = y * float(data.get("Fire_Pct", 0.055))
            net_imp = float(data.get("Imports_Pct", 40.0)) - float(data.get("Exports_Pct", 40.0))
            e_offshore = max(0.0, y * (net_imp / 100.0) * 0.08 * (1.0 + (gdp_pc / 60000.0)))

            # GENERAL NDV (USD)
            general_ndv = thermo_gdp - (dp + dn + dc + dm + de + ds + dai + ddemo) + e_plus - (e_minus + fire + e_offshore)
            general_ratio = (general_ndv / y) * 100.0 if y > 0 else 0.0

            # SPECIAL NDV (Quantum Score)
            norm_ratio = max(0.01, min(0.99, abs(general_ratio) / 200.0))
            von_neumann_entropy = - (norm_ratio * math.log(norm_ratio))
            caputo_memory = 0.85 + 0.15 * (float(data.get("RD_Exp_Pct", 1.5)) / 5.0)
            special_quantum_score = general_ndv * (1.0 - 0.10 * von_neumann_entropy) * caputo_memory

            cohesion_archetype = "Industrial" if (forest_ha / pop) < 0.25 else "Natural"

            self.ledger[iso].update({
                "gross_domestic_product_usd": y,
                "thermodynamic_gdp_usd": thermo_gdp,
                "general_ndv_usd": general_ndv,
                "special_ndv_quantum_score": special_quantum_score,
                "net_domestic_value_usd": general_ndv,
                "natural_depletion_usd": dn,
                "ndv_to_gdp_ratio": general_ratio,
                "equilibrium_transfer_usd": 0.0,
                "cognitive_depletion_usd": dc,
                "metabolic_depreciation_usd": dm,
                "epistemic_decay_usd": de,
                "ai_compute_obsolescence_usd": dai,
                "demographic_drag_usd": ddemo,
                "financialization_friction_usd": fire,
                "offshored_entropy_debt_usd": e_offshore,
                "cohesion_archetype": cohesion_archetype
            })

        # Cohesion tax
        total_tax_pool = sum(abs(r["natural_depletion_usd"]) for r in self.ledger.values() if r.get("cohesion_archetype") == "Industrial") * 0.10
        natural_sinks = sum(1 for r in self.ledger.values() if r.get("cohesion_archetype") == "Natural")
        for iso, r in self.ledger.items():
            if r.get("cohesion_archetype") == "Industrial":
                tax = abs(r.get("natural_depletion_usd", 0)) * 0.10
                r["net_domestic_value_usd"] -= tax
                r["general_ndv_usd"] -= tax
                r["equilibrium_transfer_usd"] = -tax
            else:
                payout = (total_tax_pool / natural_sinks) if natural_sinks > 0 else 0.0
                r["net_domestic_value_usd"] += payout
                r["general_ndv_usd"] += payout
                r["equilibrium_transfer_usd"] = payout
            r["ndv_to_gdp_ratio"] = (r["general_ndv_usd"] / r["gross_domestic_product_usd"]) * 100.0

    def export(self, filename="ndv_eu_ledger.csv"):
        keys = [
            "Country_Name", "gross_domestic_product_usd", "thermodynamic_gdp_usd", 
            "general_ndv_usd", "special_ndv_quantum_score", "net_domestic_value_usd", 
            "ndv_to_gdp_ratio", "equilibrium_transfer_usd", "cognitive_depletion_usd", 
            "metabolic_depreciation_usd", "epistemic_decay_usd", "ai_compute_obsolescence_usd", 
            "demographic_drag_usd", "financialization_friction_usd", "offshored_entropy_debt_usd", "cohesion_archetype"
        ]
        sorted_ledger = sorted(self.ledger.values(), key=lambda x: x.get('general_ndv_usd', 0), reverse=True)
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(sorted_ledger)
        logger.info(f"Exported Dual EU Ledger to {filename}")

if __name__ == "__main__":
    p = EU_NDV_Dual_Protocol()
    p.compute()
    p.export()
    logger.info("Protocol Dual EU Kernel execution successful.")
