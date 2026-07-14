#!/usr/bin/env python3
"""
Unit tests for NDV Sovereign Accounting Engines.
Author: Senior Economic Researcher and Lead Systems Engineer
"""

import unittest
import numpy as np
import pandas as pd
from national_matrix import USNDVEngine
from global_sovereign_matrix import GlobalSovereignNDVEngine

class TestNDVCalculations(unittest.TestCase):
    def setUp(self):
        self.us_engine = USNDVEngine(use_mock=True)
        self.global_engine = GlobalSovereignNDVEngine(use_mock=True)

    def test_us_gini_drag(self):
        """Test that Gini drag penalty is correctly computed above 0.40 and zero below 0.40."""
        # 1. Under threshold
        res_low = self.us_engine.calculate_state_ndv("TEST_LOW_GINI", {
            "Y": 1e12,
            "Dp": 1.5e11,
            "gini": 0.38,
            "population": 1e6,
            "co2_emissions_tons": 1e6,
            "hedonic_degradation_factor": 0.01,
            "ecological_damage_vulnerability": 0.01,
            "avg_schooling_years": 12.0,
            "avg_experience_years": 10.0,
            "care_hours_per_capita_annual": 800,
            "defensive_spending": 5e10,
            "smog_friction_factor": 0.01
        })
        self.assertEqual(res_low["E_gini_drag"], 0.0)

        # 2. Over threshold
        res_high = self.us_engine.calculate_state_ndv("TEST_HIGH_GINI", {
            "Y": 1e12,
            "Dp": 1.5e11,
            "gini": 0.45,
            "population": 1e6,
            "co2_emissions_tons": 1e6,
            "hedonic_degradation_factor": 0.01,
            "ecological_damage_vulnerability": 0.01,
            "avg_schooling_years": 12.0,
            "avg_experience_years": 10.0,
            "care_hours_per_capita_annual": 800,
            "defensive_spending": 5e10,
            "smog_friction_factor": 0.01
        })
        expected_penalty = 1e12 * 1.5 * (0.45 - 0.40)
        self.assertAlmostEqual(res_high["E_gini_drag"], expected_penalty)

    def test_equilibrium_transfer_neutrality(self):
        """Test that equilibrium transfers are budget neutral (sum to zero)."""
        states_data = [
            {"state": "A", "Y": 1e11, "NDV_raw": 8e10, "depletion_intensity": 0.05},
            {"state": "B", "Y": 2e11, "NDV_raw": 1.6e11, "depletion_intensity": 0.15},
            {"state": "C", "Y": 1.5e11, "NDV_raw": 1.2e11, "depletion_intensity": 0.01}
        ]
        df_transfers = self.us_engine.calculate_equilibrium_transfer_matrix(states_data)
        net_transfer_sum = df_transfers["equilibrium_transfer"].sum()
        
        # Check neutrality (within rounding bounds)
        self.assertAlmostEqual(net_transfer_sum, 0.0, delta=1e-3)
        
        # Check that high-depletion states pay (have negative transfers)
        # B has the highest depletion intensity (0.15 vs mean 0.07)
        b_transfer = df_transfers[df_transfers["state"] == "B"]["equilibrium_transfer"].values[0]
        self.assertLess(b_transfer, 0.0)

    def test_us_pipeline_execution(self):
        """Test that the full US pipeline executes and produces valid dataframes."""
        df = self.us_engine.run_national_pipeline()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertIn("NDV_final", df.columns)
        self.assertGreater(len(df), 0)

    def test_global_pipeline_execution(self):
        """Test that the full Global pipeline executes and produces valid dataframes."""
        df = self.global_engine.run_global_pipeline()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertIn("NDV_final", df.columns)
        self.assertGreater(len(df), 0)
        
        # Verify that transfers balance globally
        total_transfer = df["sovereign_transfer"].sum()
        self.assertAlmostEqual(total_transfer, 0.0, delta=1e-3)

if __name__ == "__main__":
    unittest.main()
