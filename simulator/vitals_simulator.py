#!/usr/bin/env python3
"""
Patient Vitals Simulator.
Generates realistic physiological patient vitals and streams them to output channels.
Imports clinical Early Warning System scoring logic from triage_scoring.py.
"""

import argparse
import json
import random
import sys
import time
from datetime import datetime

# Import NEWS2 scoring logic from local package module
from triage_scoring import NEWS2Scorer

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
    "Aarav Sharma", "Aditi Patel", "Rohan Gupta", "Priya Singh", "Amit Kumar",
    "Neha Sharma", "Vikram Mehta", "Ananya Reddy", "Rahul Verma", "Sneha Nair",
    "Deepak Joshi", "Siddharth Rao", "Aditya Joshi", "Divya Pillai", "Rajesh Sekhar",
    "Sunita Rao", "Suresh Nair", "Karan Johar", "Pooja Patel", "Sanjay Dutt"
]


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
