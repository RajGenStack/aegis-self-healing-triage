#!/usr/bin/env python3
"""
Chaos Engineering Outage Simulator CLI.
Injects and rolls back infrastructure and application outages to test pipeline observability.
"""

import argparse
import json
import os
import subprocess
import sys
import boto3

# Setup paths relative to the script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INFRA_DIR = os.path.join(SCRIPT_DIR, "..", "infra")

def get_terraform_outputs():
    """Reads outputs from the local Terraform state using Terraform CLI."""
    if not os.path.isdir(INFRA_DIR):
        print(f"Error: Terraform directory not found at {INFRA_DIR}", file=sys.stderr)
        sys.exit(1)
        
    try:
        # Run terraform output -json in the infra directory
        result = subprocess.run(
            ["terraform", "output", "-json"],
            cwd=INFRA_DIR,
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running 'terraform output -json': {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error parsing Terraform outputs: {e}", file=sys.stderr)
        sys.exit(1)

def get_lambda_client():
    """Initializes and returns the boto3 Lambda client."""
    return boto3.client("lambda")

def get_concurrency(lambda_client, function_name):
    """Safely retrieves the reserved concurrency configuration for a function."""
    try:
        res = lambda_client.get_function(FunctionName=function_name)
        concurrency = res.get("Concurrency", {}).get("ReservedConcurrentExecutions")
        return f"{concurrency} (Block Injected)" if concurrency is not None else "Unlimited (Normal)"
    except Exception as e:
        return f"Error ({e})"

def get_event_mappings(lambda_client, function_name):
    """Retrieves all SQS event source mappings for a function."""
    try:
        paginator = lambda_client.get_paginator("list_event_source_mappings")
        mappings = []
        for page in paginator.paginate(FunctionName=function_name):
            mappings.extend(page.get("EventSourceMappings", []))
        return [m for m in mappings if "sqs" in m.get("EventSourceArn", "").lower()]
    except Exception as e:
        print(f"Error listing event source mappings: {e}", file=sys.stderr)
        return []

def cmd_status(args):
    """Displays the current status of all triage pipeline components."""
    outputs = get_terraform_outputs()
    processor_name = outputs.get("processor_function_name", {}).get("value")
    api_name = outputs.get("api_function_name", {}).get("value")
    dynamodb_table = outputs.get("dynamodb_table_name", {}).get("value")
    sqs_queue_url = outputs.get("sqs_queue_url", {}).get("value")

    if not processor_name or not api_name:
        print("Error: Could not retrieve Lambda function names from Terraform outputs.", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print(" triage system pipeline status ".upper().center(60, "="))
    print("=" * 60)
    print(f"SQS Queue URL:      {sqs_queue_url}")
    print(f"DynamoDB Table:     {dynamodb_table}")
    print("-" * 60)
    print(f"Processor Lambda:   {processor_name}")
    
    lambda_client = get_lambda_client()
    
    # Check concurrency block status
    concurrency = get_concurrency(lambda_client, processor_name)
    print(f"  Concurrency:      {concurrency}")
    
    # Check event source mapping status
    mappings = get_event_mappings(lambda_client, processor_name)
    if mappings:
        for idx, m in enumerate(mappings):
            uuid = m.get("UUID")
            state = m.get("State")
            enabled = m.get("Enabled")
            print(f"  SQS Trigger [{idx+1}]:    UUID={uuid} | State={state} | Enabled={enabled}")
    else:
        print("  SQS Trigger:      No active mappings found.")
        
    # Check environment variable database table
    try:
        config = lambda_client.get_function_configuration(FunctionName=processor_name)
        env = config.get("Environment", {}).get("Variables", {})
        active_table = env.get("DYNAMODB_TABLE", "NOT SET")
        status_str = "Normal" if active_table == dynamodb_table else "OUTAGE INJECTED (Invalid Table)"
        print(f"  Active DB Table:  {active_table} ({status_str})")
    except Exception as e:
        print(f"  Active DB Table:  Error retrieving config ({e})")
        
    print("-" * 60)
    print(f"API Lambda:         {api_name}")
    try:
        api_config = lambda_client.get_function_configuration(FunctionName=api_name)
        api_env = api_config.get("Environment", {}).get("Variables", {})
        api_table = api_env.get("DYNAMODB_TABLE", "NOT SET")
        api_status = "Normal" if api_table == dynamodb_table else "OUTAGE INJECTED"
        print(f"  Active DB Table:  {api_table} ({api_status})")
    except Exception as e:
        print(f"  Active DB Table:  Error retrieving config ({e})")
        
    print("=" * 60)

def cmd_inject(args):
    """Injects an outage scenario into the pipeline."""
    outputs = get_terraform_outputs()
    processor_name = outputs.get("processor_function_name", {}).get("value")
    
    if not processor_name:
        print("Error: Could not retrieve Processor Lambda function name from Terraform outputs.", file=sys.stderr)
        sys.exit(1)
        
    lambda_client = get_lambda_client()
    
    print(f"Injecting scenario '{args.scenario}' on function '{processor_name}'...")
    
    if args.scenario == "concurrency-block":
        try:
            lambda_client.put_function_concurrency(
                FunctionName=processor_name,
                ReservedConcurrentExecutions=0
            )
            print("Successfully injected: Processor Lambda Reserved Concurrency set to 0.")
        except Exception as e:
            print(f"Failed to inject concurrency block: {e}", file=sys.stderr)
            sys.exit(1)
            
    elif args.scenario == "event-mapping-disable":
        mappings = get_event_mappings(lambda_client, processor_name)
        if not mappings:
            print("Error: No SQS trigger mappings found to disable.", file=sys.stderr)
            sys.exit(1)
            
        disabled_count = 0
        for m in mappings:
            try:
                lambda_client.update_event_source_mapping(
                    UUID=m.get("UUID"),
                    Enabled=False
                )
                print(f"Successfully disabled SQS mapping: UUID={m.get('UUID')}")
                disabled_count += 1
            except Exception as e:
                print(f"Failed to disable SQS mapping {m.get('UUID')}: {e}", file=sys.stderr)
                
        if disabled_count == 0:
            sys.exit(1)
            
    elif args.scenario == "db-failure":
        try:
            config = lambda_client.get_function_configuration(FunctionName=processor_name)
            env = config.get("Environment", {}).get("Variables", {})
            env["DYNAMODB_TABLE"] = "non-existent-table-chaos"
            lambda_client.update_function_configuration(
                FunctionName=processor_name,
                Environment={"Variables": env}
            )
            print("Successfully injected: Processor DYNAMODB_TABLE pointed to non-existent-table-chaos.")
        except Exception as e:
            print(f"Failed to inject database failure: {e}", file=sys.stderr)
            sys.exit(1)
            
    else:
        print(f"Error: Unknown scenario '{args.scenario}'", file=sys.stderr)
        sys.exit(1)

def cmd_rollback(args):
    """Rolls back an outage scenario to restore system health."""
    outputs = get_terraform_outputs()
    processor_name = outputs.get("processor_function_name", {}).get("value")
    dynamodb_table = outputs.get("dynamodb_table_name", {}).get("value")
    
    if not processor_name:
        print("Error: Could not retrieve Processor Lambda function name from Terraform outputs.", file=sys.stderr)
        sys.exit(1)
        
    lambda_client = get_lambda_client()
    
    print(f"Rolling back scenario '{args.scenario}' on function '{processor_name}'...")
    
    if args.scenario == "concurrency-block":
        try:
            lambda_client.delete_function_concurrency(
                FunctionName=processor_name
            )
            print("Successfully rolled back: Processor Lambda Reserved Concurrency removed (reset to unlimited).")
        except Exception as e:
            print(f"Failed to rollback concurrency block: {e}", file=sys.stderr)
            sys.exit(1)
            
    elif args.scenario == "event-mapping-disable":
        mappings = get_event_mappings(lambda_client, processor_name)
        if not mappings:
            print("Error: No SQS trigger mappings found to restore.", file=sys.stderr)
            sys.exit(1)
            
        enabled_count = 0
        for m in mappings:
            try:
                lambda_client.update_event_source_mapping(
                    UUID=m.get("UUID"),
                    Enabled=True
                )
                print(f"Successfully enabled SQS mapping: UUID={m.get('UUID')}")
                enabled_count += 1
            except Exception as e:
                print(f"Failed to enable SQS mapping {m.get('UUID')}: {e}", file=sys.stderr)
                
        if enabled_count == 0:
            sys.exit(1)
            
    elif args.scenario == "db-failure":
        if not dynamodb_table:
            print("Error: Could not retrieve DynamoDB table name from Terraform outputs.", file=sys.stderr)
            sys.exit(1)
        try:
            config = lambda_client.get_function_configuration(FunctionName=processor_name)
            env = config.get("Environment", {}).get("Variables", {})
            env["DYNAMODB_TABLE"] = dynamodb_table
            lambda_client.update_function_configuration(
                FunctionName=processor_name,
                Environment={"Variables": env}
            )
            print(f"Successfully rolled back: Processor DYNAMODB_TABLE restored to '{dynamodb_table}'.")
        except Exception as e:
            print(f"Failed to rollback database failure: {e}", file=sys.stderr)
            sys.exit(1)
            
    else:
        print(f"Error: Unknown scenario '{args.scenario}'", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Smart Patient Triage Chaos Simulator CLI")
    subparsers = parser.add_subparsers(dest="action", required=True, help="Action to execute")
    
    # Status subparser
    subparsers.add_parser("status", help="Get current pipeline status")
    
    # Inject subparser
    parser_inject = subparsers.add_parser("inject", help="Inject an outage scenario")
    parser_inject.add_argument(
        "--scenario",
        choices=["concurrency-block", "event-mapping-disable", "db-failure"],
        required=True,
        help="Outage scenario to inject"
    )
    
    # Rollback subparser
    parser_rollback = subparsers.add_parser("rollback", help="Restore system health from an outage scenario")
    parser_rollback.add_argument(
        "--scenario",
        choices=["concurrency-block", "event-mapping-disable", "db-failure"],
        required=True,
        help="Outage scenario to rollback"
    )
    
    args = parser.parse_args()
    
    if args.action == "status":
        cmd_status(args)
    elif args.action == "inject":
        cmd_inject(args)
    elif args.action == "rollback":
        cmd_rollback(args)

if __name__ == "__main__":
    main()
