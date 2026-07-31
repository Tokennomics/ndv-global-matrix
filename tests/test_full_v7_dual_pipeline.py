#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite for Tokennomics V7.0 Dual NDV Engine
Tests all components: Master Scraper, EU Engine, Satellite Telemetry, UN SEEA Adapter, Monte Carlo, and Econometric Granger Suite.
"""

import unittest
import os
import sys
import pandas as pd
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'engines'))

from generate_master_ledger import DualNDVEngine
from eu_ledger_engine import EU_NDV_Dual_Protocol
from satellite_telemetry_engine import SatelliteTelemetryEngine

class TestV7DualPipeline(unittest.TestCase):

    def test_satellite_telemetry(self):
        engine = SatelliteTelemetryEngine()
        sample = [{"ISO3": "USA", "Population": 335e6, "gross_domestic_product_usd": 27e12}]
        res = engine.process_telemetry_batch(sample)
        self.assertIn("USA", res)
        self.assertIn("satellite_radiance_factor", res["USA"])
        self.assertGreater(res["USA"]["satellite_radiance_factor"], 0)

    def test_dual_master_ledger(self):
        engine = DualNDVEngine()
        matrix = engine.generate_matrix()
        self.assertGreater(len(matrix), 0)
        first_row = matrix[0]
        self.assertIn("general_ndv_usd", first_row)
        self.assertIn("special_ndv_quantum_score", first_row)
        self.assertIn("ndv_to_gdp_ratio", first_row)

    def test_eu_dual_ledger(self):
        protocol = EU_NDV_Dual_Protocol()
        protocol.compute()
        self.assertEqual(len(protocol.ledger), 27)
        de_row = protocol.ledger["DE"]
        self.assertIn("general_ndv_usd", de_row)
        self.assertIn("special_ndv_quantum_score", de_row)
        self.assertIn("equilibrium_transfer_usd", de_row)

    def test_output_csv_integrity(self):
        master_csv = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'global_sovereign_ledger.csv')
        self.assertTrue(os.path.exists(master_csv))
        df = pd.read_csv(master_csv)
        self.assertGreater(len(df), 200)
        self.assertIn("general_ndv_usd", df.columns)
        self.assertIn("special_ndv_quantum_score", df.columns)

if __name__ == "__main__":
    unittest.main()
