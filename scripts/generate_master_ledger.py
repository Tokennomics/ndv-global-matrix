#!/usr/bin/env python3
"""
Net Domestic Value (NDV) V7.0 Absolute Macroeconomic Engine Scraper
Author: Lead Systems Architect & Biophysical Economist
Version: 7.0 Absolute Engine: AI Compute Obsolescence, Demographic Inverted Drag, MRIO Trade Matrices & Satellite Telemetry

Computes:
NDV_V7 = (Y * phi_eroi) - (Dp + Dn + Dc + Dm + De + Ds + Dai + Ddemo) + E+ - (E- + E_rent + E_offshore_MRIO)
"""

import urllib.request
import json
import csv
import logging
import os
import math
from typing import Dict, List, Optional
from satellite_telemetry_engine import SatelliteTelemetryEngine

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("NDV_V7_Engine")

FALLBACK_GLOBAL_DATA = {
    "USA": {"Country_Name": "United States", "GDP_USD": 27.36e12, "Population": 335000000, "Gini": 41.5, "PM25": 7.4, "Forest_SqKm": 3097900.0, "Energy_Imports_Pct": -5.2, "Internet_Users_Pct": 91.8, "Fire_Pct": 0.200, "Imports_Pct": 14.0, "Exports_Pct": 11.0, "Health_Exp_Pct": 16.6, "RD_Exp_Pct": 3.5, "OldAge_Dep_Pct": 26.5, "Trust_Index": 0.58, "AI_Compute_Pct": 0.045},
    "CHN": {"Country_Name": "China", "GDP_USD": 17.79e12, "Population": 1410000000, "Gini": 38.2, "PM25": 35.5, "Forest_SqKm": 2199700.0, "Energy_Imports_Pct": 15.6, "Internet_Users_Pct": 76.4, "Fire_Pct": 0.075, "Imports_Pct": 17.0, "Exports_Pct": 20.0, "Health_Exp_Pct": 5.4, "RD_Exp_Pct": 2.4, "OldAge_Dep_Pct": 20.1, "Trust_Index": 0.62, "AI_Compute_Pct": 0.035},
    "JPN": {"Country_Name": "Japan", "GDP_USD": 4.21e12, "Population": 125000000, "Gini": 32.9, "PM25": 11.2, "Forest_SqKm": 249350.0, "Energy_Imports_Pct": 94.2, "Internet_Users_Pct": 93.3, "Fire_Pct": 0.072, "Imports_Pct": 20.0, "Exports_Pct": 21.0, "Health_Exp_Pct": 11.5, "RD_Exp_Pct": 3.3, "OldAge_Dep_Pct": 51.2, "Trust_Index": 0.65, "AI_Compute_Pct": 0.025},
    "DEU": {"Country_Name": "Germany", "GDP_USD": 4.46e12, "Population": 84000000, "Gini": 31.7, "PM25": 12.0, "Forest_SqKm": 114190.0, "Energy_Imports_Pct": 61.2, "Internet_Users_Pct": 91.5, "Fire_Pct": 0.065, "Imports_Pct": 42.0, "Exports_Pct": 47.0, "Health_Exp_Pct": 12.8, "RD_Exp_Pct": 3.1, "OldAge_Dep_Pct": 36.8, "Trust_Index": 0.68, "AI_Compute_Pct": 0.028},
    "IND": {"Country_Name": "India", "GDP_USD": 3.73e12, "Population": 1430000000, "Gini": 35.7, "PM25": 58.1, "Forest_SqKm": 721600.0, "Energy_Imports_Pct": 38.4, "Internet_Users_Pct": 48.7, "Fire_Pct": 0.060, "Imports_Pct": 26.0, "Exports_Pct": 22.0, "Health_Exp_Pct": 3.0, "RD_Exp_Pct": 0.7, "OldAge_Dep_Pct": 10.2, "Trust_Index": 0.55, "AI_Compute_Pct": 0.012},
    "GBR": {"Country_Name": "United Kingdom", "GDP_USD": 3.33e12, "Population": 67000000, "Gini": 35.1, "PM25": 9.6, "Forest_SqKm": 31790.0, "Energy_Imports_Pct": 35.2, "Internet_Users_Pct": 96.0, "Fire_Pct": 0.085, "Imports_Pct": 32.0, "Exports_Pct": 29.0, "Health_Exp_Pct": 11.3, "RD_Exp_Pct": 2.9, "OldAge_Dep_Pct": 32.4, "Trust_Index": 0.60, "AI_Compute_Pct": 0.032},
    "FRA": {"Country_Name": "France", "GDP_USD": 3.01e12, "Population": 68000000, "Gini": 32.4, "PM25": 11.5, "Forest_SqKm": 172530.0, "Energy_Imports_Pct": 44.5, "Internet_Users_Pct": 92.0, "Fire_Pct": 0.060, "Imports_Pct": 35.0, "Exports_Pct": 32.0, "Health_Exp_Pct": 12.2, "RD_Exp_Pct": 2.2, "OldAge_Dep_Pct": 35.1, "Trust_Index": 0.52, "AI_Compute_Pct": 0.022},
    "ITA": {"Country_Name": "Italy", "GDP_USD": 2.19e12, "Population": 59000000, "Gini": 35.2, "PM25": 16.0, "Forest_SqKm": 95660.0, "Energy_Imports_Pct": 73.5, "Internet_Users_Pct": 85.2, "Fire_Pct": 0.055, "Imports_Pct": 33.0, "Exports_Pct": 34.0, "Health_Exp_Pct": 9.6, "RD_Exp_Pct": 1.5, "OldAge_Dep_Pct": 38.2, "Trust_Index": 0.48, "AI_Compute_Pct": 0.015},
    "CAN": {"Country_Name": "Canada", "GDP_USD": 2.14e12, "Population": 40000000, "Gini": 33.3, "PM25": 6.0, "Forest_SqKm": 3470000.0, "Energy_Imports_Pct": -58.2, "Internet_Users_Pct": 92.8, "Fire_Pct": 0.070, "Imports_Pct": 33.0, "Exports_Pct": 33.0, "Health_Exp_Pct": 11.2, "RD_Exp_Pct": 1.7, "OldAge_Dep_Pct": 29.5, "Trust_Index": 0.67, "AI_Compute_Pct": 0.025},
    "KOR": {"Country_Name": "Korea, Rep.", "GDP_USD": 1.71e12, "Population": 51000000, "Gini": 31.4, "PM25": 18.0, "Forest_SqKm": 63400.0, "Energy_Imports_Pct": 82.1, "Internet_Users_Pct": 97.6, "Fire_Pct": 0.070, "Imports_Pct": 42.0, "Exports_Pct": 44.0, "Health_Exp_Pct": 9.7, "RD_Exp_Pct": 4.9, "OldAge_Dep_Pct": 25.8, "Trust_Index": 0.58, "AI_Compute_Pct": 0.038}
}

class AbsoluteMacroeconomicEngine:
    def __init__(self):
        self.raw_data = {}
        for iso, data in FALLBACK_GLOBAL_DATA.items():
            self.raw_data[iso] = data.copy()
            self.raw_data[iso]["ISO3"] = iso
        self.sat_engine = SatelliteTelemetryEngine()

    def fetch_indicator(self, indicator: str, data_key: str):
        logger.info(f"[INGEST] Fetching World Bank Indicator: {indicator}...")
        url = f"http://api.worldbank.org/v2/country/all/indicator/{indicator}?format=json&date=2022&per_page=300"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Tokennomics-NDV-Engine/7.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
            if len(data) > 1 and data[1] is not None:
                for entry in data[1]:
                    iso3 = entry['countryiso3code']
                    if not iso3: continue
                    if iso3 not in self.raw_data:
                        self.raw_data[iso3] = {"Country_Name": entry['country']['value'], "ISO3": iso3}
                    val = entry['value']
                    if val is not None:
                        self.raw_data[iso3][data_key] = val
        except Exception as e:
            logger.warning(f"[INGEST] Could not fetch {indicator}: {e}. Retaining local fallback.")

    def generate_matrix_v7(self) -> List[Dict]:
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
        self.fetch_indicator("SP.POP.DPND.OL", "OldAge_Dep_Pct")

        processed = []
        logger.info("[KERNEL] Computing V7.0 Absolute Engine across all sovereign nodes...")

        # Process satellite batch
        sample_batch = [{"ISO3": k, "Population": v.get("Population", 10e6), "gross_domestic_product_usd": v.get("GDP_USD", 1e11)} for k, v in self.raw_data.items()]
        sat_results = self.sat_engine.process_telemetry_batch(sample_batch)

        for iso, data in self.raw_data.items():
            y_gross = float(data.get("GDP_USD", 0.0))
            pop = float(data.get("Population", 0.0))
            if y_gross <= 0 or pop <= 0: continue
            
            gdp_pc = y_gross / pop
            
            # Satellite telemetry factors
            sat_data = sat_results.get(iso, {"satellite_radiance_factor": 1.0, "satellite_smog_drag_usd": 0.0})
            radiance_mult = sat_data["satellite_radiance_factor"]
            sat_smog = sat_data["satellite_smog_drag_usd"]

            # 1. Non-Linear EROI Net Energy Cliff
            energy_imports_pct = float(data.get("Energy_Imports_Pct", 50.0))
            eroi = 20.0 - (energy_imports_pct / 100.0) * (15.0 if energy_imports_pct >= 0 else 5.0)
            eroi = max(1.5, eroi)
            phi_eroi = (1.0 - (1.0 / eroi)) * radiance_mult
            thermodynamic_gdp = y_gross * phi_eroi

            # 2. Depreciation & Ecosystem
            dp = y_gross * 0.04
            forest_ha = float(data.get("Forest_SqKm", 1000.0)) * 100.0
            dn = (forest_ha * 0.05) * 15000.0

            # 3. Cognitive & Biological Maintenance
            internet_pct = float(data.get("Internet_Users_Pct", 85.0))
            dc = pop * (internet_pct / 100.0) * 4380.0
            
            pm25 = float(data.get("PM25", 15.0))
            smog_debt = max(0, (pm25 - 5.0) * 800 * (pop / 1000.0)) + sat_smog
            gini = float(data.get("Gini", 35.0)) / 100.0 if data.get("Gini") else 0.38
            gini_drag = max(0, (gini - 0.35) * y_gross * 0.25)
            e_minus = smog_debt + gini_drag

            health_exp_pct = float(data.get("Health_Exp_Pct", 8.0))
            dm_raw = (y_gross * (health_exp_pct / 100.0) * 1.20) + (pop * 750.0 * (1.0 + (gdp_pc / 80000.0)))
            dm = max(dm_raw * 0.20, dm_raw - (0.15 * smog_debt))

            # 4. Epistemic & Social Capital Decay (Ds)
            rd_exp_pct = float(data.get("RD_Exp_Pct", 1.5))
            de = max(0.0, (y_gross * 0.05) - (y_gross * (rd_exp_pct / 100.0) * 2.0))
            
            trust_index = float(data.get("Trust_Index", 0.55))
            ds = y_gross * (1.0 - trust_index) * 0.04

            # 5. NEW PILLAR: AI & Compute Obsolescence Drag (Dai)
            ai_compute_pct = float(data.get("AI_Compute_Pct", 0.02))
            dai = y_gross * ai_compute_pct * 1.35  # compute energy intensity + model collapse factor

            # 6. NEW PILLAR: Demographic Inverted Drag (Ddemo)
            oldage_dep = float(data.get("OldAge_Dep_Pct", 25.0))
            ddemo = 0.0
            if oldage_dep > 30.0:
                ddemo = y_gross * ((oldage_dep - 30.0) / 100.0) * 0.75

            # 7. Dividends, FIRE, & Leontief MRIO Offshored Entropy
            e_plus = (pop * 800.0) * ((gdp_pc / 2080.0) * 0.40)
            fire_friction = y_gross * float(data.get("Fire_Pct", 0.055))
            
            net_imports = float(data.get("Imports_Pct", 40.0)) - float(data.get("Exports_Pct", 40.0))
            e_offshore = max(0.0, y_gross * (net_imports / 100.0) * 0.08 * (1.0 + (gdp_pc / 60000.0)))

            # Archetype
            archetype = "Industrial" if (forest_ha / pop) < 0.25 else "Natural"

            # V7.0 MASTER Omni-Equation
            ndv_v7 = thermodynamic_gdp - (dp + dn + dc + dm + de + ds + dai + ddemo) + e_plus - (e_minus + fire_friction + e_offshore)

            processed.append({
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
                "social_capital_decay_usd": round(ds, 2),
                "ai_compute_obsolescence_usd": round(dai, 2),
                "demographic_drag_usd": round(ddemo, 2),
                "care_economy_dividend_usd": round(e_plus, 2),
                "smog_friction_penalty_usd": round(smog_debt, 2),
                "gini_friction_penalty_usd": round(gini_drag, 2),
                "financialization_friction_usd": round(fire_friction, 2),
                "offshored_entropy_debt_usd": round(e_offshore, 2),
                "net_domestic_value_usd": round(ndv_v7, 2),
                "cohesion_archetype": archetype,
                "equilibrium_transfer_usd": 0.0,
                "ndv_to_gdp_ratio": 0.0
            })

        # Cohesion pool
        total_tax_pool = sum(abs(r["natural_depletion_usd"]) for r in processed if r["cohesion_archetype"] == "Industrial") * 0.10
        natural_sinks = sum(1 for r in processed if r["cohesion_archetype"] == "Natural")

        for r in processed:
            if r["cohesion_archetype"] == "Industrial":
                tax = abs(r["natural_depletion_usd"]) * 0.10
                r["net_domestic_value_usd"] -= tax
                r["equilibrium_transfer_usd"] = -tax
            else:
                payout = (total_tax_pool / natural_sinks) if natural_sinks > 0 else 0.0
                r["net_domestic_value_usd"] += payout
                r["equilibrium_transfer_usd"] = payout
            r["ndv_to_gdp_ratio"] = round(r["net_domestic_value_usd"] / r["gross_domestic_product_usd"], 3) if r["gross_domestic_product_usd"] > 0 else 0.0

        processed.sort(key=lambda x: x["net_domestic_value_usd"], reverse=True)
        return processed

if __name__ == "__main__":
    engine = AbsoluteMacroeconomicEngine()
    final_ledger = engine.generate_matrix_v7()
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'global_sovereign_ledger.csv')
    if final_ledger:
        keys = final_ledger[0].keys()
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(final_ledger)
        logger.info(f"[SUCCESS] V7.0 Absolute Sovereign Ledger generated with {len(final_ledger)} nations at {output_path}")
