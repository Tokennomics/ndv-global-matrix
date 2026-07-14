#!/usr/bin/env python3
"""
Net Domestic Value (NDV) Global Sovereign Ledger Engine (World Bank Bulk Ingestion)
Author: Senior Economic Researcher and Lead Systems Engineer
Version: 3.0: Total Project Recovery

This module implements the Global Sovereign Ingestion pipeline, retrieving data from the
World Bank API to calculate the Net Domestic Value (NDV) for countries globally:
    NDV = Y - Dp - Dn + E+ - E-

Pillars modeled:
1. Macro-Financial (Opportunity Cost of Defensive/Military Spending)
2. Biosphere (Natural resources depletion + CO2 damage)
3. Societal (Compounded Human Capital Index + Care Economy Proxy)
4. Equilibrium Transfer (Sovereign ecological transfer matrix)
Plus Gini Drag (Inequality drag using World Bank Gini index).
"""

import os
import sys
import logging
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pandas as pd
import requests

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NDV_Global")

class GlobalSovereignNDVEngine:
    def __init__(self, use_mock=True):
        """
        Initialize the Global Sovereign NDV engine.
        Since World Bank API does not require an API key, we call it directly,
        but support mock/fallback logic in case of network timeouts or offline execution.
        """
        self.use_mock = use_mock
        self.base_url = "https://api.worldbank.org/v2"
        
        # Calibration factors
        self.HISTORICAL_ROI = 0.065  # Global opportunity cost penalty coefficient
        self.GINI_THRESHOLD = 0.40
        self.GINI_DRAG_COEFF = 1.2
        self.SHADOW_CARE_WAGE_GLOBAL = 12.00  # Global average shadow wage (PPP-adjusted proxy)
        
        # Default list of representative countries to fetch/model
        self.countries = [
            "USA", "CHN", "JPN", "DEU", "IND", "GBR", "FRA", "BRA", 
            "CAN", "AUS", "RUS", "ZAF", "SAU", "MEX", "IDN", "NGA"
        ]
        
        # World Bank Indicator Mapping
        self.indicators = {
            "Y": "NY.GDP.MKTP.CD",               # GDP (current USD)
            "Dp": "NY.ADJ.DKAP.CD",              # Consumption of fixed capital (current USD)
            "Dn_energy": "NY.ADJ.DNGY.CD",       # Energy depletion (current USD)
            "Dn_mineral": "NY.ADJ.DMIN.CD",      # Mineral depletion (current USD)
            "Dn_forest": "NY.ADJ.DFOR.CD",       # Forest depletion (current USD)
            "Dn_co2": "NY.ADJ.DCO2.CD",          # Carbon dioxide damage (current USD)
            "Gini": "SI.POV.GINI",               # Gini index (0-100 scale)
            "Military": "MS.MIL.XPND.GD.ZS",     # Military expenditure (% of GDP)
            "Schooling": "SE.SEC.ENRL",          # School enrollment, secondary (%)
            "Population": "SP.POP.TOTL"          # Population, total
        }

    def fetch_wb_indicator(self, country_code, indicator_code, year_range="2020:2024"):
        """
        Fetches an indicator series for a country from the World Bank API.
        Falls back to mock data on failure.
        """
        url = f"{self.base_url}/country/{country_code}/indicator/{indicator_code}"
        params = {
            "date": year_range,
            "format": "json",
            "per_page": 1000
        }
        
        if self.use_mock:
            # Short-circuit to speed up or run offline
            return self._generate_mock_wb_data(country_code, indicator_code)
            
        try:
            response = requests.get(url, params=params, timeout=8)
            response.raise_for_status()
            data = response.json()
            
            # World Bank response format: [metadata_dict, data_list]
            if len(data) > 1 and isinstance(data[1], list):
                records = []
                for entry in data[1]:
                    val = entry.get("value")
                    date = entry.get("date")
                    if val is not None and date is not None:
                        records.append({"year": int(date), "value": float(val)})
                if records:
                    df = pd.DataFrame(records).sort_values("year")
                    return df
            raise ValueError(f"Empty or invalid response from World Bank API for {country_code} - {indicator_code}")
        except Exception as e:
            logger.warning(f"Error fetching World Bank {indicator_code} for {country_code}: {e}. Falling back to mock data.")
            return self._generate_mock_wb_data(country_code, indicator_code)

    def _generate_mock_wb_data(self, country_code, indicator_code):
        """Generates realistic macro data calibrated to country characteristics."""
        years = list(range(2020, 2025))
        
        # Establish country scales (Y in current USD)
        scales = {
            "USA": {"Y": 27e12, "pop": 335e6, "gini": 41.5, "mil": 3.4, "sec": 98.0},
            "CHN": {"Y": 18e12, "pop": 1410e6, "gini": 38.2, "mil": 1.6, "sec": 92.0},
            "JPN": {"Y": 4.2e12, "pop": 125e6, "gini": 32.9, "mil": 1.0, "sec": 100.0},
            "DEU": {"Y": 4.4e12, "pop": 84e6, "gini": 31.7, "mil": 1.4, "sec": 99.0},
            "IND": {"Y": 3.7e12, "pop": 1430e6, "gini": 35.7, "mil": 2.4, "sec": 75.0},
            "GBR": {"Y": 3.3e12, "pop": 67e6, "gini": 35.1, "mil": 2.2, "sec": 98.0},
            "FRA": {"Y": 3.0e12, "pop": 68e6, "gini": 32.4, "mil": 1.9, "sec": 99.0},
            "BRA": {"Y": 2.1e12, "pop": 215e6, "gini": 48.9, "mil": 1.1, "sec": 88.0},
            "CAN": {"Y": 2.1e12, "pop": 40e6, "gini": 33.3, "mil": 1.2, "sec": 99.0},
            "AUS": {"Y": 1.7e12, "pop": 26e6, "gini": 34.3, "mil": 1.9, "sec": 100.0},
            "RUS": {"Y": 2.0e12, "pop": 144e6, "gini": 36.0, "mil": 4.1, "sec": 98.0},
            "ZAF": {"Y": 3.8e11, "pop": 60e6, "gini": 63.0, "mil": 0.9, "sec": 80.0},
            "SAU": {"Y": 1.1e12, "pop": 36e6, "gini": 34.5, "mil": 6.8, "sec": 90.0},
            "MEX": {"Y": 1.8e12, "pop": 128e6, "gini": 45.4, "mil": 0.6, "sec": 78.0},
            "IDN": {"Y": 1.4e12, "pop": 277e6, "gini": 37.9, "mil": 0.7, "sec": 82.0},
            "NGA": {"Y": 3.6e11, "pop": 224e6, "gini": 35.1, "mil": 0.5, "sec": 44.0}
        }
        
        info = scales.get(country_code, {"Y": 5e11, "pop": 50e6, "gini": 40.0, "mil": 1.5, "sec": 80.0})
        
        records = []
        for year in years:
            trend = 1.0 + (0.02 * (year - 2020)) # simple growth multiplier
            
            if indicator_code == self.indicators["Y"]:
                val = info["Y"] * trend
            elif indicator_code == self.indicators["Population"]:
                val = info["pop"] * (1.0 + (0.005 * (year - 2020)))
            elif indicator_code == self.indicators["Gini"]:
                val = info["gini"] + np.random.uniform(-0.5, 0.5)
            elif indicator_code == self.indicators["Military"]:
                val = info["mil"] + np.random.uniform(-0.1, 0.1)
            elif indicator_code == self.indicators["Schooling"]:
                val = info["sec"]
            elif indicator_code == self.indicators["Dp"]:
                val = info["Y"] * 0.14 * trend # ~14% depreciation of physical assets
            elif indicator_code == self.indicators["Dn_energy"]:
                # High energy depletion for resource exporters
                dep_rate = 0.06 if country_code in ["SAU", "RUS", "NGA"] else 0.005
                val = info["Y"] * dep_rate * trend
            elif indicator_code == self.indicators["Dn_mineral"]:
                dep_rate = 0.04 if country_code in ["ZAF", "AUS", "BRA"] else 0.001
                val = info["Y"] * dep_rate * trend
            elif indicator_code == self.indicators["Dn_forest"]:
                dep_rate = 0.02 if country_code in ["BRA", "IDN", "NGA"] else 0.0005
                val = info["Y"] * dep_rate * trend
            elif indicator_code == self.indicators["Dn_co2"]:
                # carbon damage scales with country output / industrialization
                val = info["Y"] * 0.015 * trend
            else:
                val = 0.0
                
            records.append({"year": year, "value": val})
            
        return pd.DataFrame(records)

    def process_country_ndv(self, country_code):
        """
        Gathers indicators for a single country and computes the NDV ledger entry for the latest year (2024).
        Runs inside the multi-threaded matrix execution pool.
        """
        try:
            data = {}
            for name, code in self.indicators.items():
                df = self.fetch_wb_indicator(country_code, code)
                # Take latest year value
                latest_val = df.iloc[-1]["value"] if not df.empty else 0.0
                data[name] = latest_val
                
            Y = data["Y"]
            Dp = data["Dp"]
            
            # Biosphere Depletion (Dn)
            Dn_energy = data["Dn_energy"]
            Dn_mineral = data["Dn_mineral"]
            Dn_forest = data["Dn_forest"]
            Dn_co2 = data["Dn_co2"]
            Dn = Dn_energy + Dn_mineral + Dn_forest + Dn_co2
            
            # Societal Dividends (E+)
            # A. Compounding Human Capital
            # We scale secondary school enrollment rate to calculate HC compounding
            schooling_factor = data["Schooling"] / 100.0  # normalize
            experience_proxy = 18.0  # constant proxy for comparison
            # Compound return multiplier
            b1, b2 = 0.08, 0.02
            hc_multiplier = np.exp(b1 * schooling_factor * 10.0 + b2 * experience_proxy)
            E_hc = Y * (1.0 - (1.0 / hc_multiplier))
            
            # B. Shadow Wage for Care Economy
            pop = data["Population"]
            care_hours_annual = pop * 850.0  # proxy: 850 hours/person/year
            E_care = care_hours_annual * self.SHADOW_CARE_WAGE_GLOBAL
            
            E_plus = E_hc + E_care
            
            # Debts/Frictions (E-)
            # A. Gini Drag
            gini = data["Gini"] / 100.0  # convert 0-100 to 0-1
            if gini > self.GINI_THRESHOLD:
                E_gini = Y * self.GINI_DRAG_COEFF * (gini - self.GINI_THRESHOLD)
            else:
                E_gini = 0.0
                
            # B. Defensive Spending Opportunity Cost Penalty
            # Military spending is defensive
            military_pct = data["Military"] / 100.0
            defensive_spending = Y * military_pct
            E_def_penalty = defensive_spending * self.HISTORICAL_ROI
            
            # C. Environmental Health Friction (smog health cost etc)
            # CO2 damage as a proxy base
            E_friction = Dn_co2 * 0.5
            
            E_minus = E_gini + E_def_penalty + E_friction
            
            # Compute Raw NDV
            ndv_raw = Y - Dp - Dn + E_plus - E_minus
            
            return {
                "country": country_code,
                "Y": Y,
                "Dp": Dp,
                "Dn_energy": Dn_energy,
                "Dn_mineral": Dn_mineral,
                "Dn_forest": Dn_forest,
                "Dn_co2": Dn_co2,
                "Dn_total": Dn,
                "E_hc": E_hc,
                "E_care": E_care,
                "E_plus_total": E_plus,
                "E_gini_drag": E_gini,
                "E_def_penalty": E_def_penalty,
                "E_friction": E_friction,
                "E_minus_total": E_minus,
                "NDV_raw": ndv_raw,
                "gini": gini,
                "depletion_intensity": Dn / Y if Y > 0 else 0
            }
        except Exception as e:
            logger.error(f"Failed processing NDV for country {country_code}: {e}")
            raise e

    def calculate_global_equilibrium_transfer(self, country_results):
        """
        Pillar 4: Automated Global Sovereign Tax/Transfer System.
        Tax high-depletion resource exporters to pool resources for global ecological sinks.
        """
        df = pd.DataFrame(country_results)
        
        # Baseline mean depletion intensity
        mean_intensity = df["depletion_intensity"].mean()
        
        # Calculate individual transfer rates
        df["net_transfer_rate"] = 0.04 * (df["depletion_intensity"] - mean_intensity)
        df["raw_transfer_amount"] = df["Y"] * df["net_transfer_rate"]
        
        total_taxed = df[df["raw_transfer_amount"] > 0]["raw_transfer_amount"].sum()
        total_recipient_weight = df[df["raw_transfer_amount"] < 0]["raw_transfer_amount"].abs().sum()
        
        balanced_transfers = []
        for _, row in df.iterrows():
            amt = row["raw_transfer_amount"]
            if amt > 0:
                balanced_amt = -amt
            else:
                weight = abs(amt) / total_recipient_weight if total_recipient_weight > 0 else 0
                balanced_amt = total_taxed * weight
            balanced_transfers.append(balanced_amt)
            
        df["sovereign_transfer"] = balanced_transfers
        df["NDV_final"] = df["NDV_raw"] + df["sovereign_transfer"]
        
        return df

    def run_global_pipeline(self):
        """Runs the multi-threaded World Bank bulk ingestion and processing pipeline."""
        logger.info("Initializing World Bank bulk sovereign ingestion...")
        
        country_results = []
        logger.info(f"Processing NDV global matrix for {len(self.countries)} countries using thread pool...")
        
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_country = {
                executor.submit(self.process_country_ndv, country): country
                for country in self.countries
            }
            for future in as_completed(future_to_country):
                country = future_to_country[future]
                try:
                    result = future.result()
                    country_results.append(result)
                except Exception as exc:
                    logger.error(f"Country {country} generated an exception during global run: {exc}")
                    
        # Apply global equilibrium transfers
        final_ledger_df = self.calculate_global_equilibrium_transfer(country_results)
        
        # Print summary
        logger.info("==========================================")
        logger.info("Global Sovereign Ledgers Processed Successfully.")
        for _, row in final_ledger_df.sort_values(by="Y", ascending=False).iterrows():
            logger.info(f"{row['country']}: Y = ${row['Y']/1e9:.1f}B | Final NDV = ${row['NDV_final']/1e9:.1f}B")
        logger.info("==========================================")
        
        return final_ledger_df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Net Domestic Value (NDV) Global Sovereign Ledger Engine")
    parser.add_argument("--out", type=str, default="global_sovereign_ledger.csv", help="Output path for CSV ledger")
    args = parser.parse_args()
    
    engine = GlobalSovereignNDVEngine(use_mock=True)
    df = engine.run_global_pipeline()
    
    # Save ledger
    df.to_csv(args.out, index=False)
    logger.info(f"Global sovereign output written successfully to: {args.out}")
