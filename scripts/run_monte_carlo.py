#!/usr/bin/env python3
"""
Net Domestic Value (NDV) Monte Carlo Uncertainty & Sensitivity Simulator
Author: Lead Systems Architect & Biophysical Economist
Version: 6.0 Academic Suite

Performs N=1,000 stochastic simulations across 252 sovereign nodes to compute 
95% confidence intervals and standard deviations for NDV/GDP ratios.
"""

import json
import csv
import random
import math
import os
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger("NDV_MonteCarlo")

def run_simulation(num_trials: int = 1000, input_csv: str = "global_sovereign_ledger.csv"):
    if not os.path.exists(input_csv):
        logger.error(f"Input file {input_csv} not found. Run generate_master_ledger.py first.")
        return

    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        nations = list(reader)

    logger.info(f"Loaded {len(nations)} nations. Initializing {num_trials} Monte Carlo trials...")

    results = []

    for nation in nations:
        country_name = nation["Country_Name"]
        iso3 = nation["ISO3"]
        gdp = float(nation["gross_domestic_product_usd"])
        ndv_base = float(nation["net_domestic_value_usd"])
        ratio_base = float(nation["ndv_to_gdp_ratio"])

        if gdp <= 0:
            continue

        simulated_ratios = []

        for _ in range(num_trials):
            # Introduce Gaussian noise to key biophysical parameters (±10-15% standard error)
            eroi_noise = random.gauss(1.0, 0.08)
            health_noise = random.gauss(1.0, 0.10)
            cognitive_noise = random.gauss(1.0, 0.12)
            trade_noise = random.gauss(1.0, 0.10)

            # Perturb NDV components
            thermo_gdp_sim = float(nation["thermodynamic_gdp_usd"]) * eroi_noise
            dp_sim = float(nation["physical_depreciation_usd"])
            dn_sim = float(nation["natural_depletion_usd"])
            dc_sim = float(nation["cognitive_depletion_usd"]) * cognitive_noise
            dm_sim = float(nation["metabolic_depreciation_usd"]) * health_noise
            de_sim = float(nation["epistemic_decay_usd"])
            e_plus_sim = float(nation["care_economy_dividend_usd"])
            e_minus_sim = float(nation["smog_friction_penalty_usd"]) + float(nation["gini_friction_penalty_usd"])
            fire_sim = float(nation["financialization_friction_usd"])
            e_offshore_sim = float(nation["offshored_entropy_debt_usd"]) * trade_noise

            ndv_sim = thermo_gdp_sim - (dp_sim + dn_sim + dc_sim + dm_sim + de_sim) + e_plus_sim - (e_minus_sim + fire_sim + e_offshore_sim)
            ratio_sim = (ndv_sim / gdp) * 100.0
            simulated_ratios.append(ratio_sim)

        simulated_ratios.sort()
        ci_lower = simulated_ratios[int(num_trials * 0.025)]
        ci_upper = simulated_ratios[int(num_trials * 0.975)]
        mean_ratio = sum(simulated_ratios) / num_trials
        
        # Variance calculation
        variance = sum((x - mean_ratio) ** 2 for x in simulated_ratios) / num_trials
        std_dev = math.sqrt(variance)

        results.append({
            "Country_Name": country_name,
            "ISO3": iso3,
            "GDP_USD": gdp,
            "NDV_Base_USD": ndv_base,
            "Base_Ratio_Pct": round(ratio_base, 2),
            "Mean_Ratio_Pct": round(mean_ratio, 2),
            "CI_95_Lower": round(ci_lower, 2),
            "CI_95_Upper": round(ci_upper, 2),
            "Std_Dev": round(std_dev, 2)
        })

    output_path = "ndv_monte_carlo_results.csv"
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"[SUCCESS] Monte Carlo simulation complete. Output saved to {output_path}")

if __name__ == "__main__":
    run_simulation(num_trials=1000)
