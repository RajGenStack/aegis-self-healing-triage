#!/usr/bin/env python3
"""
Patient Vitals Simulator and NEWS2 Scoring Module.
Generates realistic physiological patient vitals and computes
clinical risk scores using the NEWS2 early warning system.
"""

import argparse
import json
import random
import sys
import time
from datetime import datetime

# Patient Profiles defining boundaries for simulation
PATIENT_PROFILES = {
    "STABLE": {
        "heart_rate": (60, 85),
        "spo2": (96, 100),
        "systolic_bp": (115, 135),
        "temperature": (36.4, 37.5),
        "respiration_rate": (12, 18),
        "supplemental_oxygen": [False],
        "consciousness": ["Alert"],
        "oxygen_prob": 0.0,
        "cvpu_prob": 0.0
    },
    "DETERIORATING": {
        "heart_rate": (85, 140),
        "spo2": (85, 95),
        "systolic_bp": (80, 110),
        "temperature": (35.0, 39.5),
        "respiration_rate": (18, 28),
        "supplemental_oxygen": [True, False],
        "consciousness": ["Alert", "Confused", "Voice"],
        "oxygen_prob": 0.6,
        "cvpu_prob": 0.4
    },
    "RECOVERING": {
        "heart_rate": (55, 95),
        "spo2": (94, 99),
        "systolic_bp": (105, 125),
        "temperature": (36.0, 37.8),
        "respiration_rate": (11, 20),
        "supplemental_oxygen": [True, False],
        "consciousness": ["Alert"],
        "oxygen_prob": 0.2,
        "cvpu_prob": 0.05
    },
    "CRITICAL": {
        "heart_rate": (35, 150),
        "spo2": (75, 91),
        "systolic_bp": (70, 230),
        "temperature": (34.0, 40.2),
        "respiration_rate": (6, 32),
        "supplemental_oxygen": [True],
        "consciousness": ["Confused", "Voice", "Pain", "Unresponsive"],
        "oxygen_prob": 0.9,
        "cvpu_prob": 0.9
    }
}

PATIENT_NAMES = [
    "James Smith", "Mary Johnson", "John Williams", "Patricia Brown", "Robert Jones",
    "Jennifer Miller", "Michael Davis", "Abishek Sharma", "William Rodriguez", "Linda Wilson",
    "David Martinez", "Barbara Anderson", "Richard Taylor", "Susan Thomas", "Joseph Hernandez",
    "Jessica Moore", "Thomas Martin", "Sarah Jackson", "Charles Martin", "Karen Lee"
]

class NEWS2Scorer:
    """Computes the NEWS2 clinical risk triage score."""

    @staticmethod
    def score_respiration_rate(rate):
        """Score for Respiration Rate (breaths/min)."""
        if rate <= 8:
            return 3
        elif 9 <= rate <= 11:
            return 1
        elif 12 <= rate <= 20:
            return 0
        elif 21 <= rate <= 24:
            return 2
        else: # >= 25
            return 3

    @staticmethod
    def score_spo2_scale1(spo2):
        """Score for SpO2 Scale 1 (general patients)."""
        if spo2 >= 96:
            return 0
        elif 94 <= spo2 <= 95:
            return 1
        elif 92 <= spo2 <= 93:
            return 2
        else: # <= 91
            return 3

    @staticmethod
    def score_spo2_scale2(spo2, supplemental_oxygen):
        """Score for SpO2 Scale 2 (COPD target range 88-92%)."""
        if supplemental_oxygen:
            if spo2 >= 97:
                return 3
            elif 95 <= spo2 <= 96:
                return 2
            elif 93 <= spo2 <= 94:
                return 1
            elif 88 <= spo2 <= 92:
                return 0
            elif 86 <= spo2 <= 87:
                return 1
            elif 84 <= spo2 <= 85:
                return 2
            else: # <= 83
                return 3
        else:
            # On air
            if spo2 >= 93:
                return 0
            elif 88 <= spo2 <= 92:
                return 0
            elif 86 <= spo2 <= 87:
                return 1
            elif 84 <= spo2 <= 85:
                return 2
            else: # <= 83
                return 3

    @staticmethod
    def score_supplemental_oxygen(supplemental_oxygen):
        """Score for Supplemental Oxygen (Air vs. Oxygen)."""
        return 2 if supplemental_oxygen else 0

    @staticmethod
    def score_systolic_bp(bp):
        """Score for Systolic Blood Pressure (mmHg)."""
        if bp <= 90:
            return 3
        elif 91 <= bp <= 100:
            return 2
        elif 101 <= bp <= 110:
            return 1
        elif 111 <= bp <= 219:
            return 0
        else: # >= 220
            return 3

    @staticmethod
    def score_heart_rate(rate):
        """Score for Heart Rate (bpm)."""
        if rate <= 40:
            return 3
        elif 41 <= rate <= 50:
            return 1
        elif 51 <= rate <= 90:
            return 0
        elif 91 <= rate <= 110:
            return 1
        elif 111 <= rate <= 130:
            return 2
        else: # >= 131
            return 3

    @staticmethod
    def score_temperature(temp):
        """Score for Temperature (°C)."""
        if temp <= 35.0:
            return 3
        elif 35.1 <= temp <= 36.0:
            return 1
        elif 36.1 <= temp <= 38.0:
            return 0
        elif 38.1 <= temp <= 39.0:
            return 1
        else: # >= 39.1
            return 2

    @staticmethod
    def score_consciousness(consciousness):
        """Score for Consciousness Level (Alert vs. CVPU)."""
        # CVPU: Confused, Voice, Pain, Unresponsive
        # Alert = 0, anything else = 3
        if consciousness == "Alert":
            return 0
        elif consciousness in ["Confused", "Voice", "Pain", "Unresponsive"]:
            return 3
        else:
            raise ValueError(f"Invalid consciousness value: {consciousness}")

    @classmethod
    def calculate(cls, respiration_rate, spo2, spo2_scale, supplemental_oxygen,
                  systolic_bp, heart_rate, temperature, consciousness):
        """
        Calculates the overall NEWS2 score and returns score + breakdown + risk level.
        """
        # Score each parameter
        s_respiration = cls.score_respiration_rate(respiration_rate)
        
        if spo2_scale == 2:
            s_spo2 = cls.score_spo2_scale2(spo2, supplemental_oxygen)
        else:
            s_spo2 = cls.score_spo2_scale1(spo2)
            
        s_oxygen = cls.score_supplemental_oxygen(supplemental_oxygen)
        s_bp = cls.score_systolic_bp(systolic_bp)
        s_hr = cls.score_heart_rate(heart_rate)
        s_temp = cls.score_temperature(temperature)
        s_consciousness = cls.score_consciousness(consciousness)
        
        # Calculate total score
        total_score = (s_respiration + s_spo2 + s_oxygen + s_bp +
                       s_hr + s_temp + s_consciousness)
        
        # Determine clinical risk category
        # LOW: 0-4 and no individual parameter score is 3
        # MEDIUM: 5-6 OR any individual parameter is 3 (when total score is <= 6)
        # HIGH: >= 7
        individual_scores = [s_respiration, s_spo2, s_oxygen, s_bp, s_hr, s_temp, s_consciousness]
        has_single_3 = 3 in individual_scores
        
        if total_score >= 7:
            risk_level = "HIGH"
        elif total_score >= 5 or has_single_3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
            
        breakdown = {
            "respiration_rate": s_respiration,
            "spo2": s_spo2,
            "supplemental_oxygen": s_oxygen,
            "systolic_bp": s_bp,
            "heart_rate": s_hr,
            "temperature": s_temp,
            "consciousness": s_consciousness
        }
        
        return {
            "total_score": total_score,
            "breakdown": breakdown,
            "risk_level": risk_level
        }


class PatientSimulator:
    """Simulates physiological vitals for a patient over time."""

    def __init__(self, patient_id, name, profile="STABLE", spo2_scale=1):
        self.patient_id = patient_id
        self.name = name
        self.profile = profile
        self.spo2_scale = spo2_scale  # 1 for Scale 1, 2 for Scale 2 (COPD)
        self.vitals_history = []
        
        # Initialize vitals near normal for the profile
        prof = PATIENT_PROFILES[self.profile]
        self.current_respiration = int(random.uniform(*prof["respiration_rate"]))
        self.current_spo2 = int(random.uniform(*prof["spo2"]))
        self.current_bp = int(random.uniform(*prof["systolic_bp"]))
        self.current_hr = int(random.uniform(*prof["heart_rate"]))
        self.current_temp = round(random.uniform(*prof["temperature"]), 1)
        self.current_oxygen = random.random() < prof["oxygen_prob"]
        self.current_consciousness = "Confused" if (random.random() < prof["cvpu_prob"]) else "Alert"

    def step(self):
        """Simulates a small change in patient vitals based on profile rules."""
        prof = PATIENT_PROFILES[self.profile]
        
        # Apply standard random walk (drift) within profile boundaries
        self.current_respiration = self._clamp_walk(self.current_respiration, prof["respiration_rate"], step_max=2)
        self.current_spo2 = self._clamp_walk(self.current_spo2, prof["spo2"], step_max=1)
        self.current_bp = self._clamp_walk(self.current_bp, prof["systolic_bp"], step_max=5)
        self.current_hr = self._clamp_walk(self.current_hr, prof["heart_rate"], step_max=4)
        self.current_temp = round(self._clamp_walk(self.current_temp, prof["temperature"], step_max=0.2), 1)
        
        # Supplemental oxygen and consciousness transitions
        if random.random() < 0.1:  # 10% chance to update state variables
            self.current_oxygen = random.random() < prof["oxygen_prob"]
        if random.random() < 0.1:
            self.current_consciousness = "Confused" if (random.random() < prof["cvpu_prob"]) else "Alert"
            
        # Ensure logical rules:
        # e.g., if on oxygen, SpO2 should not easily drop below 80 without high risk
        # Scale 2 SpO2 targets 88-92, if SpO2 rises > 97 and they have Scale 2 COPD, NEWS2 increases.
        
        # Calculate NEWS2 score
        score_info = NEWS2Scorer.calculate(
            respiration_rate=self.current_respiration,
            spo2=self.current_spo2,
            spo2_scale=self.spo2_scale,
            supplemental_oxygen=self.current_oxygen,
            systolic_bp=self.current_bp,
            heart_rate=self.current_hr,
            temperature=self.current_temp,
            consciousness=self.current_consciousness
        )
        
        reading = {
            "patient_id": self.patient_id,
            "name": self.name,
            "profile": self.profile,
            "timestamp": int(time.time()),
            "vitals": {
                "respiration_rate": self.current_respiration,
                "spo2": self.current_spo2,
                "spo2_scale": self.spo2_scale,
                "supplemental_oxygen": self.current_oxygen,
                "systolic_bp": self.current_bp,
                "heart_rate": self.current_hr,
                "temperature": self.current_temp,
                "consciousness": self.current_consciousness
            },
            "news2_score": score_info["total_score"],
            "risk_level": score_info["risk_level"],
            "score_breakdown": score_info["breakdown"]
        }
        
        return reading

    def _clamp_walk(self, val, bounds, step_max):
        """Applies a random walk step and clamps the result to bounds."""
        low, high = bounds
        step = random.uniform(-step_max, step_max)
        new_val = val + step
        if new_val < low:
            return low
        if new_val > high:
            return high
        return type(val)(new_val)


def generate_patients(count=5, copd_ratio=0.2):
    """Generates initial patient list with diverse profiles."""
    patients = []
    profiles = ["STABLE", "STABLE", "RECOVERING", "DETERIORATING", "CRITICAL"] # distribution
    
    for i in range(count):
        patient_id = f"PAT-{i+1:03d}"
        name = PATIENT_NAMES[i % len(PATIENT_NAMES)]
        
        # Select profile and SpO2 scale (COPD)
        profile = random.choice(profiles)
        spo2_scale = 2 if (random.random() < copd_ratio) else 1
        
        # If COPD (Scale 2), override stable SpO2 range to match typical COPD targets (88-92%)
        # otherwise we simulate them as normal.
        
        patients.append(PatientSimulator(patient_id, name, profile, spo2_scale))
    return patients


def run_simulation(patients, duration, interval, output_file=None, sqs_queue=None):
    """Runs the simulation loop and logs/prints output."""
    start_time = time.time()
    file_handle = None
    sqs_client = None
    queue_url = None
    
    if output_file:
        try:
            file_handle = open(output_file, "a", encoding="utf-8")
        except IOError as e:
            print(f"Error opening output file: {e}", file=sys.stderr)
            
    if sqs_queue:
        try:
            import boto3
            sqs_client = boto3.client('sqs')
            response = sqs_client.get_queue_url(QueueName=sqs_queue)
            queue_url = response['QueueUrl']
            print(f"Streaming vitals directly to AWS SQS queue: {sqs_queue} (URL: {queue_url})", file=sys.stderr)
        except Exception as e:
            print(f"Error initializing AWS SQS client or resolving queue: {e}", file=sys.stderr)
            print("Simulator will continue running but SQS streaming will be disabled.", file=sys.stderr)
            sqs_client = None
            
    print(f"Starting Patient Vitals Simulator for {len(patients)} patients...", file=sys.stderr)
    print(f"Interval: {interval}s, Duration: {'indefinite' if duration == 0 else f'{duration}s'}", file=sys.stderr)
    print("-" * 60, file=sys.stderr)
    
    try:
        while True:
            for patient in patients:
                reading = patient.step()
                reading_json = json.dumps(reading)
                
                # Output to stdout
                print(reading_json)
                sys.stdout.flush()
                
                # Output to file
                if file_handle:
                    file_handle.write(reading_json + "\n")
                    file_handle.flush()
                    
                # Stream to SQS
                if sqs_client and queue_url:
                    try:
                        sqs_client.send_message(
                            QueueUrl=queue_url,
                            MessageBody=reading_json
                        )
                    except Exception as e:
                        print(f"Failed to send telemetry for patient {patient.patient_id} to SQS: {e}", file=sys.stderr)
                    
            # Check duration limits
            if duration > 0 and (time.time() - start_time) >= duration:
                print("Simulation completed (duration limit reached).", file=sys.stderr)
                break
                
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nSimulation stopped by user.", file=sys.stderr)
    finally:
        if file_handle:
            file_handle.close()


def main():
    parser = argparse.ArgumentParser(description="Patient Vitals & NEWS2 Simulator")
    parser.add_argument("--patients", type=int, default=5, help="Number of patients to simulate")
    parser.add_argument("--copd-ratio", type=float, default=0.2, help="Probability of patient having COPD (NEWS2 SpO2 Scale 2)")
    parser.add_argument("--duration", type=int, default=0, help="Simulation duration in seconds (0 for infinite)")
    parser.add_argument("--interval", type=float, default=2.0, help="Vitals updates interval in seconds")
    parser.add_argument("--output", type=str, default=None, help="Append JSON lines output to this file")
    parser.add_argument("--sqs-queue", type=str, default=None, help="Target AWS SQS Queue name to stream JSON vitals data")
    
    args = parser.parse_args()
    
    # Generate patients
    patients = generate_patients(count=args.patients, copd_ratio=args.copd_ratio)
    
    # Run loop
    run_simulation(patients, args.duration, args.interval, args.output, args.sqs_queue)


if __name__ == "__main__":
    main()
