import json
import os
import decimal
import boto3

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DYNAMODB_TABLE')
table = dynamodb.Table(table_name)

class NEWS2Scorer:
    """Computes the NEWS2 clinical risk triage score."""

    @staticmethod
    def score_respiration_rate(rate):
        if rate <= 8:
            return 3
        elif 9 <= rate <= 11:
            return 1
        elif 12 <= rate <= 20:
            return 0
        elif 21 <= rate <= 24:
            return 2
        else:
            return 3

    @staticmethod
    def score_spo2_scale1(spo2):
        if spo2 >= 96:
            return 0
        elif 94 <= spo2 <= 95:
            return 1
        elif 92 <= spo2 <= 93:
            return 2
        else:
            return 3

    @staticmethod
    def score_spo2_scale2(spo2, supplemental_oxygen):
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
            else:
                return 3
        else:
            if spo2 >= 93:
                return 0
            elif 88 <= spo2 <= 92:
                return 0
            elif 86 <= spo2 <= 87:
                return 1
            elif 84 <= spo2 <= 85:
                return 2
            else:
                return 3

    @staticmethod
    def score_supplemental_oxygen(supplemental_oxygen):
        return 2 if supplemental_oxygen else 0

    @staticmethod
    def score_systolic_bp(bp):
        if bp <= 90:
            return 3
        elif 91 <= bp <= 100:
            return 2
        elif 101 <= bp <= 110:
            return 1
        elif 111 <= bp <= 219:
            return 0
        else:
            return 3

    @staticmethod
    def score_heart_rate(rate):
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
        else:
            return 3

    @staticmethod
    def score_temperature(temp):
        if temp <= 35.0:
            return 3
        elif 35.1 <= temp <= 36.0:
            return 1
        elif 36.1 <= temp <= 38.0:
            return 0
        elif 38.1 <= temp <= 39.0:
            return 1
        else:
            return 2

    @staticmethod
    def score_consciousness(consciousness):
        if consciousness == "Alert":
            return 0
        elif consciousness in ["Confused", "Voice", "Pain", "Unresponsive"]:
            return 3
        else:
            return 3  # Default fallback safe score for unknown consciousness

    @classmethod
    def calculate(cls, respiration_rate, spo2, spo2_scale, supplemental_oxygen,
                  systolic_bp, heart_rate, temperature, consciousness):
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
        
        total_score = (s_respiration + s_spo2 + s_oxygen + s_bp +
                       s_hr + s_temp + s_consciousness)
        
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

def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")
    
    for record in event.get('Records', []):
        try:
            body_str = record.get('body')
            data = json.loads(body_str, parse_float=decimal.Decimal)
            
            patient_id = data.get('patient_id')
            timestamp = data.get('timestamp')
            name = data.get('name')
            vitals = data.get('vitals', {})
            
            if not patient_id or not timestamp:
                print(f"Skipping record due to missing patient_id or timestamp: {data}")
                continue
                
            score_info = NEWS2Scorer.calculate(
                respiration_rate=int(vitals.get('respiration_rate', 16)),
                spo2=int(vitals.get('spo2', 98)),
                spo2_scale=int(vitals.get('spo2_scale', 1)),
                supplemental_oxygen=bool(vitals.get('supplemental_oxygen', False)),
                systolic_bp=int(vitals.get('systolic_bp', 120)),
                heart_rate=int(vitals.get('heart_rate', 70)),
                temperature=decimal.Decimal(str(vitals.get('temperature', 36.5))),
                consciousness=vitals.get('consciousness', 'Alert')
            )
            
            item = {
                'patient_id': patient_id,
                'timestamp': timestamp,
                'name': name,
                'profile': data.get('profile', 'STABLE'),
                'vitals': {
                    'respiration_rate': int(vitals.get('respiration_rate', 16)),
                    'spo2': int(vitals.get('spo2', 98)),
                    'spo2_scale': int(vitals.get('spo2_scale', 1)),
                    'supplemental_oxygen': bool(vitals.get('supplemental_oxygen', False)),
                    'systolic_bp': int(vitals.get('systolic_bp', 120)),
                    'heart_rate': int(vitals.get('heart_rate', 70)),
                    'temperature': decimal.Decimal(str(vitals.get('temperature', 36.5))),
                    'consciousness': vitals.get('consciousness', 'Alert')
                },
                'news2_score': int(score_info['total_score']),
                'risk_level': score_info['risk_level'],
                'score_breakdown': {k: int(v) for k, v in score_info['breakdown'].items()}
            }
            
            table.put_item(Item=item)
            print(f"Successfully processed and stored vitals for patient {patient_id}")
            
        except Exception as e:
            print(f"Error processing record: {e}")
            
    return {
        'statusCode': 200,
        'body': json.dumps('Finished processing SQS batch')
    }
