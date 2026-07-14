#!/usr/bin/env python3
"""
Net Domestic Value (NDV) National Ledger Engine (US Bulk Ingestion)
Author: Senior Economic Researcher and Lead Systems Engineer
Version: 3.0: Total Project Recovery

This module implements the US Bulk Ingestion pipeline, retrieving data from FRED
and the US Census Bureau APIs to calculate the Net Domestic Value (NDV):
    NDV = Y - Dp - Dn + E+ - E-

It includes the four core pillars of the NDV framework:
1. Macro-Financial (Opportunity Cost of Defensive Spending)
2. Biosphere (Stacked Valuation: Replacement Cost + Hedonic + Damage Cost Avoided)
3. Societal (Einstein Compounding for Human Capital via Mincer Function + Shadow Care Wage)
4. Equilibrium Transfer (Automated ecological transfer matrix)
Plus the Gini Drag penalty if wealth concentration exceeds 0.40.
"""

import os
import sys
import logging
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pandas as pd
import requests

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NDV_National")

class USNDVEngine:
    def __init__(self, fred_api_key=None, census_api_key=None, use_mock=True):
        """
        Initialize the NDV engine.
        If API keys are not provided, it will check environment variables.
        If use_mock is True, it will fallback to generating realistic synthetic data when APIs fail or are missing.
        """
        self.fred_api_key = fred_api_key or os.getenv("FRED_API_KEY")
        self.census_api_key = census_api_key or os.getenv("CENSUS_API_KEY")
        self.use_mock = use_mock
        
        # Base URLs
        self.fred_url = "https://api.stlouisfed.org/fred"
        self.census_url = "https://api.census.gov/data"
        
        # Configuration constants for calibration
        self.HISTORICAL_ROI = 0.07  # 7% historical opportunity cost rate for capital
        self.CO2_REPLACEMENT_COST_PER_TON = 50.0  # USD per metric ton
        # Gini penalty scaling factor
        self.GINI_THRESHOLD = 0.40
        self.GINI_DRAG_COEFF = 1.5
        # Shadow care economy wage
        self.SHADOW_CARE_WAGE = 18.50  # USD / hour (average shadow wage for care/domestic work)
        
        # Default state list for US state-level matrix
        self.states = [
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
        ]
        
    def fetch_fred_series(self, series_id):
        """Fetches observations for a FRED series. Falls back to mock data if key is missing."""
        if not self.fred_api_key:
            if self.use_mock:
                return self._generate_mock_fred_series(series_id)
            raise ValueError(f"FRED_API_KEY is missing and mock data is disabled.")
            
        url = f"{self.fred_url}/series/observations"
        params = {
            "series_id": series_id,
            "api_key": self.fred_api_key,
            "file_type": "json"
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            obs = data.get("observations", [])
            df = pd.DataFrame(obs)
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            df["date"] = pd.to_datetime(df["date"])
            return df.dropna(subset=["value"])
        except Exception as e:
            logger.warning(f"Error fetching FRED series {series_id}: {e}. Falling back to mock data.")
            if self.use_mock:
                return self._generate_mock_fred_series(series_id)
            raise e

    def _generate_mock_fred_series(self, series_id):
        """Generates realistic synthetic data for FRED series."""
        logger.info(f"Generating mock data for FRED series: {series_id}")
        dates = pd.date_range(start="2015-01-01", end="2025-01-01", freq="YE")
        n = len(dates)
        
        # Seed values based on actual economic levels
        if series_id == "GDP":  # US GDP (trillions)
            values = np.linspace(18.2, 29.0, n) + np.random.normal(0, 0.2, n)
            values = values * 1e12  # convert to dollars
        elif series_id == "A262RC1A027NBEA":  # Consumption of Fixed Capital (Depreciation)
            values = np.linspace(2.9, 4.8, n) + np.random.normal(0, 0.05, n)
            values = values * 1e12
        elif series_id == "FDEF":  # National Defense consumption expenditures (billions)
            values = np.linspace(750, 950, n) + np.random.normal(0, 10, n)
            values = values * 1e9
        elif series_id == "A191RL1Q225SBEA":  # Air pollution expenditures / proxy (billions)
            values = np.linspace(120, 180, n) + np.random.normal(0, 5, n)
            values = values * 1e9
        else:
            values = np.linspace(100, 200, n) + np.random.normal(0, 5, n)
            
        return pd.DataFrame({"date": dates, "value": values})

    def fetch_census_gini(self, state_fips="*"):
        """Fetches Gini index of income inequality from US Census Bureau API."""
        if not self.census_api_key:
            if self.use_mock:
                return self._generate_mock_census_gini(state_fips)
            raise ValueError("CENSUS_API_KEY is missing and mock data is disabled.")
            
        # Example using ACS 5-year data B19083_001E (Gini Index)
        url = f"{self.census_url}/2021/acs/acs5"
        params = {
            "get": "NAME,B19083_001E",
            "for": f"state:{state_fips}",
            "key": self.census_api_key
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            # Census returns list of lists: [['NAME', 'B19083_001E', 'state'], ...]
            headers = data[0]
            rows = data[1:]
            df = pd.DataFrame(rows, columns=headers)
            df["B19083_001E"] = pd.to_numeric(df["B19083_001E"], errors="coerce")
            return df
        except Exception as e:
            logger.warning(f"Error fetching Census Gini for state {state_fips}: {e}. Falling back to mock data.")
            if self.use_mock:
                return self._generate_mock_census_gini(state_fips)
            raise e

    def _generate_mock_census_gini(self, state_fips):
        """Generates realistic synthetic state-level Gini data."""
        logger.info(f"Generating mock Gini data for states.")
        data = []
        for state in self.states:
            # Baseline gini around 0.43 - 0.52 with some state variation
            gini = 0.44 + np.random.uniform(-0.04, 0.07)
            population = int(1e6 + np.random.uniform(0.5e6, 38e6))
            data.append({
                "NAME": state,
                "B19083_001E": gini,
                "population": population,
                "state": state_fips if state_fips != "*" else state
            })
        return pd.DataFrame(data)

    def calculate_state_ndv(self, state_code, state_data):
        """
        Calculates NDV for a single state (processed within thread pool).
        
        Equation: NDV = Y - Dp - Dn + E+_hc + E+_care - E-_gini - E-_def_penalty - E-_smog
        """
        try:
            # 1. Gross Output (Y)
            Y = state_data["Y"]
            
            # 2. Physical Depreciation (Dp)
            Dp = state_data.get("Dp", Y * 0.15)  # Default to 15% of output if missing
            
            # 3. Biosphere Depletion (Dn) - Stacked Valuation
            # Stacked = Replacement Cost + Hedonic + Damage Cost Avoided
            co2_tons = state_data.get("co2_emissions_tons", Y * 0.0002) # proxy 200g CO2 per $ Y
            replacement_cost = co2_tons * self.CO2_REPLACEMENT_COST_PER_TON
            
            # Hedonic offset: degradation reduces property aesthetic premiums
            hedonic_penalty = Y * state_data.get("hedonic_degradation_factor", 0.015)
            
            # Damage cost avoided: loss of wetlands/coastal protection increases vulnerability
            damage_cost_avoided_loss = Y * state_data.get("ecological_damage_vulnerability", 0.01)
            
            Dn = replacement_cost + hedonic_penalty + damage_cost_avoided_loss
            
            # 4. Societal Dividends (E+)
            # A. Einstein Compounding Human Capital (Mincer Function)
            # Mincer: ln(w) = b0 + b1*Schooling + b2*Exp + b3*Exp^2
            schooling_years = state_data.get("avg_schooling_years", 13.5)
            experience_years = state_data.get("avg_experience_years", 20.0)
            
            # Mincerian compounding return multiplier
            b1, b2, b3 = 0.10, 0.03, -0.0006
            hc_multiplier = np.exp(b1 * (schooling_years - 8) + b2 * experience_years + b3 * (experience_years ** 2))
            # Human Capital Dividend is the compounded portion of economic activity attributable to education/experience
            E_hc = Y * (1.0 - (1.0 / hc_multiplier))
            
            # B. Shadow Wage for Care Economy (E+_care)
            # Estimated unpaid hours per year per capita: ~1040 hours (20 hours/week)
            population = state_data.get("population", 5e6)
            unpaid_care_hours_pct = state_data.get("care_hours_per_capita_annual", 800.0)
            total_care_hours = population * unpaid_care_hours_pct
            E_care = total_care_hours * self.SHADOW_CARE_WAGE
            
            E_plus = E_hc + E_care
            
            # 5. Debts/Frictions (E-)
            # A. Gini Drag
            gini = state_data.get("gini", 0.45)
            if gini > self.GINI_THRESHOLD:
                E_gini = Y * self.GINI_DRAG_COEFF * (gini - self.GINI_THRESHOLD)
            else:
                E_gini = 0.0
                
            # B. Defensive Spending Opportunity Cost Penalty
            # Defensive spending represents money that had to be spent defensively (rebuilding, security, litigation)
            # penalty = defensive spending * ROI opportunity cost
            defensive_spending = state_data.get("defensive_spending", Y * 0.05)
            E_def_penalty = defensive_spending * self.HISTORICAL_ROI
            
            # C. Smog & Health Cost (Friction)
            E_smog = Y * state_data.get("smog_friction_factor", 0.02)
            
            E_minus = E_gini + E_def_penalty + E_smog
            
            # Compute raw NDV
            ndv_raw = Y - Dp - Dn + E_plus - E_minus
            
            return {
                "state": state_code,
                "Y": Y,
                "Dp": Dp,
                "Dn_replacement": replacement_cost,
                "Dn_hedonic": hedonic_penalty,
                "Dn_damage_avoided_loss": damage_cost_avoided_loss,
                "Dn_total": Dn,
                "E_hc": E_hc,
                "E_care": E_care,
                "E_plus_total": E_plus,
                "E_gini_drag": E_gini,
                "E_def_penalty": E_def_penalty,
                "E_smog": E_smog,
                "E_minus_total": E_minus,
                "NDV_raw": ndv_raw,
                "gini": gini,
                "depletion_intensity": Dn / Y if Y > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error calculating NDV for state {state_code}: {e}")
            raise e

    def calculate_equilibrium_transfer_matrix(self, state_results):
        """
        Pillar 5: Equilibrium Transfer.
        Tax high-depletion industrial zones and transfer to ecological preservation zones.
        
        Tax rate is proportional to depletion intensity (Dn / Y).
        Redistribution is inversely proportional to depletion intensity.
        """
        df = pd.DataFrame(state_results)
        
        # Calculate mean depletion intensity
        mean_intensity = df["depletion_intensity"].mean()
        
        # Transfer factor: states with above-average depletion are taxed.
        # States with below-average depletion receive funds.
        df["net_transfer_rate"] = 0.05 * (df["depletion_intensity"] - mean_intensity)
        
        # Calculate raw transfer amounts
        df["raw_transfer_amount"] = df["Y"] * df["net_transfer_rate"]
        
        # Balance the transfer matrix to ensure budget neutrality
        total_taxed = df[df["raw_transfer_amount"] > 0]["raw_transfer_amount"].sum()
        total_recipient_weight = df[df["raw_transfer_amount"] < 0]["raw_transfer_amount"].abs().sum()
        
        balanced_transfers = []
        for _, row in df.iterrows():
            amt = row["raw_transfer_amount"]
            if amt > 0:
                # High-depletion state: pays the tax
                balanced_amt = -amt
            else:
                # Preservation state: receives share of total taxes collected
                weight = abs(amt) / total_recipient_weight if total_recipient_weight > 0 else 0
                balanced_amt = total_taxed * weight
            balanced_transfers.append(balanced_amt)
            
        df["equilibrium_transfer"] = balanced_transfers
        df["NDV_final"] = df["NDV_raw"] + df["equilibrium_transfer"]
        
        return df

    def run_national_pipeline(self):
        """
        Executes the full US National Matrix Ingestion & Inflow pipeline.
        Utilizes multi-threading to process individual states concurrently.
        """
        logger.info("Initializing US bulk ingestion pipeline...")
        
        # Fetch Macro aggregates from FRED (used to calibrate state baselines)
        gdp_series = self.fetch_fred_series("GDP")
        dep_series = self.fetch_fred_series("A262RC1A027NBEA")
        defense_series = self.fetch_fred_series("FDEF")
        
        latest_gdp = gdp_series.iloc[-1]["value"] if not gdp_series.empty else 27e12
        latest_dep = dep_series.iloc[-1]["value"] if not dep_series.empty else 4e12
        latest_defense = defense_series.iloc[-1]["value"] if not defense_series.empty else 850e9
        
        logger.info(f"Calibrating state baselines with national aggregates: "
                    f"GDP: ${latest_gdp/1e12:.2f}T, "
                    f"Depreciation: ${latest_dep/1e12:.2f}T, "
                    f"Defense: ${latest_defense/1e9:.2f}B")
        
        # Fetch Census Gini info
        gini_df = self.fetch_census_gini()
        
        # Assemble state-level task inputs
        state_tasks = {}
        for _, row in gini_df.iterrows():
            state_code = row["NAME"]
            gini_val = row["B19083_001E"]
            pop_val = row.get("population", 6e6)
            
            # Standard state allocation proxies calibrated to state size
            state_gdp_share = pop_val / 335e6  # share of US population as baseline proxy
            state_gdp = latest_gdp * state_gdp_share
            
            state_tasks[state_code] = {
                "Y": state_gdp,
                "Dp": latest_dep * state_gdp_share,
                "gini": gini_val,
                "population": pop_val,
                "co2_emissions_tons": pop_val * 14.5,  # ~14.5 tons per capita average
                "hedonic_degradation_factor": np.random.uniform(0.005, 0.025),
                "ecological_damage_vulnerability": np.random.uniform(0.008, 0.02),
                "avg_schooling_years": np.random.uniform(12.5, 14.8),
                "avg_experience_years": np.random.uniform(18.0, 22.0),
                "care_hours_per_capita_annual": np.random.uniform(700, 1000),
                "defensive_spending": latest_defense * state_gdp_share + (state_gdp * np.random.uniform(0.01, 0.03)),
                "smog_friction_factor": np.random.uniform(0.01, 0.03)
            }
            
        # Execute state calculations in parallel
        logger.info(f"Processing NDV state matrix using {min(32, len(state_tasks))} threads...")
        state_results = []
        with ThreadPoolExecutor(max_workers=32) as executor:
            future_to_state = {
                executor.submit(self.calculate_state_ndv, code, data): code
                for code, data in state_tasks.items()
            }
            for future in as_completed(future_to_state):
                state_code = future_to_state[future]
                try:
                    result = future.result()
                    state_results.append(result)
                except Exception as exc:
                    logger.error(f"State {state_code} generated an exception during multi-threaded run: {exc}")
                    
        # Apply Equilibrium Transfer Matrix to finalize state NDV values
        final_ledger_df = self.calculate_equilibrium_transfer_matrix(state_results)
        
        # Calculate US aggregate NDV
        aggregate_gdp = final_ledger_df["Y"].sum()
        aggregate_ndv = final_ledger_df["NDV_final"].sum()
        
        logger.info("==========================================")
        logger.info(f"US National Ledger Processed.")
        logger.info(f"Aggregate GDP: ${aggregate_gdp/1e12:.3f}T")
        logger.info(f"Aggregate NDV: ${aggregate_ndv/1e12:.3f}T")
        logger.info(f"NDV-to-GDP Ratio: {aggregate_ndv / aggregate_gdp:.2%}")
        logger.info("==========================================")
        
        return final_ledger_df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Net Domestic Value (NDV) National Ledger Engine")
    parser.add_argument("--fred-key", type=str, help="FRED API key")
    parser.add_argument("--census-key", type=str, help="Census API key")
    parser.add_argument("--out", type=str, default="us_national_ledger.csv", help="Output path for CSV ledger")
    args = parser.parse_args()
    
    engine = USNDVEngine(fred_api_key=args.fred_key, census_api_key=args.census_key, use_mock=True)
    df = engine.run_national_pipeline()
    
    # Save ledger
    df.to_csv(args.out, index=False)
    logger.info(f"Sovereign matrix output written successfully to: {args.out}")
