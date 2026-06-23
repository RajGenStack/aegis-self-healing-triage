import json
import os
import boto3

lambda_client = boto3.client('lambda')

def get_event_mappings(function_name):
    """Retrieves all SQS event source mappings for the target Lambda function."""
    try:
        paginator = lambda_client.get_paginator('list_event_source_mappings')
        mappings = []
        for page in paginator.paginate(FunctionName=function_name):
            mappings.extend(page.get('EventSourceMappings', []))
        return [m for m in mappings if 'sqs' in m.get('EventSourceArn', '').lower()]
    except Exception as e:
        print(f"Error listing event source mappings for {function_name}: {e}")
        return []

def lambda_handler(event, context):
    """
    Remediation Lambda function for Phase 7 (Self-Healing).
    Invoked by EventBridge alarms to execute automated remediation actions
    when infrastructure outages or database connectivity errors are detected.
    """
    print(f"Received remediation event: {json.dumps(event)}")
    
    # Extract alarm details
    detail = event.get('detail', {})
    alarm_name = detail.get('alarmName', '')
    state_value = detail.get('state', {}).get('value', '')
    
    processor_name = os.environ.get('PROCESSOR_FUNCTION_NAME')
    correct_table = os.environ.get('CORRECT_DYNAMODB_TABLE')
    
    if not processor_name or not correct_table:
        print("Error: PROCESSOR_FUNCTION_NAME or CORRECT_DYNAMODB_TABLE environment variables not configured.")
        return {'statusCode': 500, 'body': 'Missing configuration'}

    # Double check state to avoid false triggers
    if state_value != 'ALARM':
        print(f"Alarm {alarm_name} is in state {state_value}. Remediation only runs on ALARM.")
        return {'statusCode': 200, 'body': 'No action required'}
        
    print(f"Alarm '{alarm_name}' triggered! Initiating remediation sequence on '{processor_name}'...")
    actions_taken = []
    
    # -------------------------------------------------------------------------
    # Scenario 1: Database configuration failure (processor-errors alarm)
    # -------------------------------------------------------------------------
    if 'processor-errors' in alarm_name:
        print("Analyzing database failure alarm...")
        try:
            config = lambda_client.get_function_configuration(FunctionName=processor_name)
            env = config.get('Environment', {}).get('Variables', {})
            current_table = env.get('DYNAMODB_TABLE')
            
            if current_table != correct_table:
                print(f"Table name mismatch: found '{current_table}', expected '{correct_table}'. Remediation required.")
                env['DYNAMODB_TABLE'] = correct_table
                lambda_client.update_function_configuration(
                    FunctionName=processor_name,
                    Environment={'Variables': env}
                )
                actions_taken.append(f"Restored DYNAMODB_TABLE to '{correct_table}'")
            else:
                print("DYNAMODB_TABLE env variable is already correct. No action taken.")
        except Exception as e:
            print(f"Failed to check/update DYNAMODB_TABLE configuration: {e}")
            
    # -------------------------------------------------------------------------
    # Scenario 2: SQS Backlog / Processing Latency (sqs-backlog or sqs-latency alarms)
    # -------------------------------------------------------------------------
    if 'sqs-backlog' in alarm_name or 'sqs-latency' in alarm_name or 'processor-duration' in alarm_name:
        print("Analyzing SQS queue backlog / latency / duration alarm...")
        
        # Action A: Check and resolve Concurrency Block (Reserved Concurrency = 0)
        try:
            res = lambda_client.get_function(FunctionName=processor_name)
            concurrency = res.get('Concurrency', {}).get('ReservedConcurrentExecutions')
            if concurrency == 0:
                print("Processor Lambda concurrency is set to 0. Deleting Reserved Concurrency block...")
                lambda_client.delete_function_concurrency(FunctionName=processor_name)
                actions_taken.append("Removed Reserved Concurrency block (reset to unlimited)")
            else:
                print(f"Processor Lambda Reserved Concurrency is {concurrency} (normal).")
        except Exception as e:
            print(f"Failed to check/delete reserved concurrency: {e}")
            
        # Action B: Check and resolve SQS Trigger Disable (Event Source Mapping Enabled = False)
        try:
            mappings = get_event_mappings(processor_name)
            for m in mappings:
                if not m.get('Enabled') or m.get('State') != 'Enabled':
                    uuid = m.get('UUID')
                    print(f"SQS trigger mapping {uuid} is currently disabled/inactive. Re-enabling...")
                    lambda_client.update_event_source_mapping(UUID=uuid, Enabled=True)
                    actions_taken.append(f"Re-enabled SQS trigger mapping {uuid}")
        except Exception as e:
            print(f"Failed to check/enable event source mappings: {e}")

    summary = f"Remediation actions taken: {', '.join(actions_taken) if actions_taken else 'None'}"
    print(summary)
    
    return {
        'statusCode': 200,
        'body': json.dumps(summary)
    }
