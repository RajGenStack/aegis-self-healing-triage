import json
import os
import decimal
import boto3

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DYNAMODB_TABLE')
table = dynamodb.Table(table_name)

class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert a DynamoDB item to JSON."""
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 == 0:
                return int(o)
            return float(o)
        return super(DecimalEncoder, self).default(o)

def get_cors_headers():
    return {}

def lambda_handler(event, context):
    print(f"Received API request event: {json.dumps(event)}")
    
    # Handle preflight CORS request
    if event.get('requestContext', {}).get('http', {}).get('method') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': ''
        }
        
    try:
        response = table.scan()
        items = response.get('Items', [])
        
        latest_patients = {}
        for item in items:
            pid = item.get('patient_id')
            ts = item.get('timestamp')
            
            if pid not in latest_patients or ts > latest_patients[pid].get('timestamp'):
                latest_patients[pid] = item
                
        patient_list = list(latest_patients.values())
        
        # Sort patient list by urgency:
        # 1. NEWS2 Score descending
        # 2. Timestamp descending
        patient_list.sort(key=lambda x: (int(x.get('news2_score', 0)), int(x.get('timestamp', 0))), reverse=True)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(patient_list, cls=DecimalEncoder)
        }
        
    except Exception as e:
        print(f"Error fetching vitals: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }
