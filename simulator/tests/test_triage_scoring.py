#!/usr/bin/env python3
"""
Unit tests for the NEWS2 Patient Vitals Scorer and Simulator.
"""

import sys
import os
import unittest

# Ensure parent directory is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from triage_scoring import NEWS2Scorer
from vitals_simulator import PatientSimulator, generate_patients


class TestNEWS2Scorer(unittest.TestCase):
    """Test suite for the NEWS2 scoring algorithm thresholds."""

    def test_respiration_rate(self):
        self.assertEqual(NEWS2Scorer.score_respiration_rate(7), 3)
        self.assertEqual(NEWS2Scorer.score_respiration_rate(8), 3)
        self.assertEqual(NEWS2Scorer.score_respiration_rate(9), 1)
        self.assertEqual(NEWS2Scorer.score_respiration_rate(11), 1)
        self.assertEqual(NEWS2Scorer.score_respiration_rate(12), 0)
        self.assertEqual(NEWS2Scorer.score_respiration_rate(20), 0)
        self.assertEqual(NEWS2Scorer.score_respiration_rate(21), 2)
        self.assertEqual(NEWS2Scorer.score_respiration_rate(24), 2)
        self.assertEqual(NEWS2Scorer.score_respiration_rate(25), 3)
        self.assertEqual(NEWS2Scorer.score_respiration_rate(30), 3)

    def test_spo2_scale1(self):
        self.assertEqual(NEWS2Scorer.score_spo2_scale1(97), 0)
        self.assertEqual(NEWS2Scorer.score_spo2_scale1(96), 0)
        self.assertEqual(NEWS2Scorer.score_spo2_scale1(95), 1)
        self.assertEqual(NEWS2Scorer.score_spo2_scale1(94), 1)
        self.assertEqual(NEWS2Scorer.score_spo2_scale1(93), 2)
        self.assertEqual(NEWS2Scorer.score_spo2_scale1(92), 2)
        self.assertEqual(NEWS2Scorer.score_spo2_scale1(91), 3)
        self.assertEqual(NEWS2Scorer.score_spo2_scale1(85), 3)

    def test_spo2_scale2(self):
        # Scale 2: COPD patients. Target range is 88-92%.
        # On supplemental oxygen
        self.assertEqual(NEWS2Scorer.score_spo2_scale2(98, True), 3)  # >= 97
        self.assertEqual(NEWS2Scorer.score_spo2_scale2(96, True), 2)  # 95-96
        self.assertEqual(NEWS2Scorer.score_spo2_scale2(94, True), 1)  # 93-94
        self.assertEqual(NEWS2Scorer.score_spo2_scale2(92, True), 0)  # 88-92
        self.assertEqual(NEWS2Scorer.score_spo2_scale2(89, True), 0)  # 88-92
        self.assertEqual(NEWS2Scorer.score_spo2_scale2(87, True), 1)  # 86-87
        self.assertEqual(NEWS2Scorer.score_spo2_scale2(85, True), 2)  # 84-85
        self.assertEqual(NEWS2Scorer.score_spo2_scale2(80, True), 3)  # <= 83
        
        # On Air (not supplemental oxygen)
        self.assertEqual(NEWS2Scorer.score_spo2_scale2(95, False), 0)  # >= 93 (on air)
        self.assertEqual(NEWS2Scorer.score_spo2_scale2(93, False), 0)  # >= 93 (on air)
        self.assertEqual(NEWS2Scorer.score_spo2_scale2(90, False), 0)  # 88-92
        self.assertEqual(NEWS2Scorer.score_spo2_scale2(87, False), 1)  # 86-87
        self.assertEqual(NEWS2Scorer.score_spo2_scale2(84, False), 2)  # 84-85
        self.assertEqual(NEWS2Scorer.score_spo2_scale2(78, False), 3)  # <= 83

    def test_supplemental_oxygen(self):
        self.assertEqual(NEWS2Scorer.score_supplemental_oxygen(False), 0)
        self.assertEqual(NEWS2Scorer.score_supplemental_oxygen(True), 2)

    def test_systolic_bp(self):
        self.assertEqual(NEWS2Scorer.score_systolic_bp(85), 3)
        self.assertEqual(NEWS2Scorer.score_systolic_bp(90), 3)
        self.assertEqual(NEWS2Scorer.score_systolic_bp(95), 2)
        self.assertEqual(NEWS2Scorer.score_systolic_bp(100), 2)
        self.assertEqual(NEWS2Scorer.score_systolic_bp(105), 1)
        self.assertEqual(NEWS2Scorer.score_systolic_bp(110), 1)
        self.assertEqual(NEWS2Scorer.score_systolic_bp(120), 0)
        self.assertEqual(NEWS2Scorer.score_systolic_bp(219), 0)
        self.assertEqual(NEWS2Scorer.score_systolic_bp(220), 3)
        self.assertEqual(NEWS2Scorer.score_systolic_bp(250), 3)

    def test_heart_rate(self):
        self.assertEqual(NEWS2Scorer.score_heart_rate(35), 3)
        self.assertEqual(NEWS2Scorer.score_heart_rate(40), 3)
        self.assertEqual(NEWS2Scorer.score_heart_rate(45), 1)
        self.assertEqual(NEWS2Scorer.score_heart_rate(50), 1)
        self.assertEqual(NEWS2Scorer.score_heart_rate(72), 0)
        self.assertEqual(NEWS2Scorer.score_heart_rate(90), 0)
        self.assertEqual(NEWS2Scorer.score_heart_rate(95), 1)
        self.assertEqual(NEWS2Scorer.score_heart_rate(110), 1)
        self.assertEqual(NEWS2Scorer.score_heart_rate(115), 2)
        self.assertEqual(NEWS2Scorer.score_heart_rate(130), 2)
        self.assertEqual(NEWS2Scorer.score_heart_rate(135), 3)

    def test_temperature(self):
        self.assertEqual(NEWS2Scorer.score_temperature(34.5), 3)
        self.assertEqual(NEWS2Scorer.score_temperature(35.0), 3)
        self.assertEqual(NEWS2Scorer.score_temperature(35.5), 1)
        self.assertEqual(NEWS2Scorer.score_temperature(36.0), 1)
        self.assertEqual(NEWS2Scorer.score_temperature(36.8), 0)
        self.assertEqual(NEWS2Scorer.score_temperature(38.0), 0)
        self.assertEqual(NEWS2Scorer.score_temperature(38.5), 1)
        self.assertEqual(NEWS2Scorer.score_temperature(39.0), 1)
        self.assertEqual(NEWS2Scorer.score_temperature(39.1), 2)
        self.assertEqual(NEWS2Scorer.score_temperature(40.0), 2)

    def test_consciousness(self):
        self.assertEqual(NEWS2Scorer.score_consciousness("Alert"), 0)
        self.assertEqual(NEWS2Scorer.score_consciousness("Confused"), 3)
        self.assertEqual(NEWS2Scorer.score_consciousness("Voice"), 3)
        self.assertEqual(NEWS2Scorer.score_consciousness("Pain"), 3)
        self.assertEqual(NEWS2Scorer.score_consciousness("Unresponsive"), 3)
        with self.assertRaises(ValueError):
            NEWS2Scorer.score_consciousness("Asleep")

    def test_calculate_total_score_and_risk(self):
        # Perfect stable baseline
        score_res = NEWS2Scorer.calculate(16, 98, 1, False, 120, 72, 36.8, "Alert")
        self.assertEqual(score_res["total_score"], 0)
        self.assertEqual(score_res["risk_level"], "LOW")
        
        # Test low score but has a single parameter scoring 3 (e.g. HR=35)
        score_res_single_3 = NEWS2Scorer.calculate(16, 98, 1, False, 120, 35, 36.8, "Alert")
        self.assertEqual(score_res_single_3["total_score"], 3)
        self.assertEqual(score_res_single_3["risk_level"], "MEDIUM")
        
        # Test Medium score range: Total score = 5
        score_res_med = NEWS2Scorer.calculate(22, 95, 1, False, 120, 45, 38.5, "Alert")
        self.assertEqual(score_res_med["total_score"], 5)
        self.assertEqual(score_res_med["risk_level"], "MEDIUM")
        
        # Test High score range: Total score >= 7
        score_res_high = NEWS2Scorer.calculate(26, 90, 1, True, 85, 135, 39.5, "Confused")
        self.assertEqual(score_res_high["total_score"], 19)
        self.assertEqual(score_res_high["risk_level"], "HIGH")


class TestPatientSimulator(unittest.TestCase):
    """Test suite for the patient simulator class."""

    def test_simulator_step(self):
        sim = PatientSimulator(patient_id="PAT-001", name="Alice Smith", profile="STABLE", spo2_scale=1)
        reading = sim.step()
        
        self.assertEqual(reading["patient_id"], "PAT-001")
        self.assertEqual(reading["name"], "Alice Smith")
        self.assertEqual(reading["profile"], "STABLE")
        
        vitals = reading["vitals"]
        self.assertIn("respiration_rate", vitals)
        self.assertIn("spo2", vitals)
        self.assertIn("spo2_scale", vitals)
        self.assertIn("supplemental_oxygen", vitals)
        self.assertIn("systolic_bp", vitals)
        self.assertIn("heart_rate", vitals)
        self.assertIn("temperature", vitals)
        self.assertIn("consciousness", vitals)
        
        self.assertIn("news2_score", reading)
        self.assertIn("risk_level", reading)
        self.assertIn("score_breakdown", reading)

    def test_generate_patients(self):
        patients = generate_patients(count=10, copd_ratio=0.3)
        self.assertEqual(len(patients), 10)
        
        for i, p in enumerate(patients):
            self.assertEqual(p.patient_id, f"PAT-{i+1:03d}")
            self.assertIsNotNone(p.name)


if __name__ == "__main__":
    unittest.main()
