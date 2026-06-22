"""
Clinical Early Warning System (NEWS2) scoring matrix.
Refactored into a standalone module to decouple patient vitals simulation
from core clinical scoring logic.
"""

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
