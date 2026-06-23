#!/usr/bin/env python3
import boto3
import sys
import time

region = "us-east-1"
prefix = "rajgenstack-triage"

# Initialize clients
lambda_client = boto3.client('lambda', region_name=region)
sqs_client = boto3.client('sqs', region_name=region)
dynamodb_client = boto3.client('dynamodb', region_name=region)
events_client = boto3.client('events', region_name=region)
logs_client = boto3.client('logs', region_name=region)
sns_client = boto3.client('sns', region_name=region)
iam_client = boto3.client('iam', region_name=region)
cloudwatch_client = boto3.client('cloudwatch', region_name=region)

print("=" * 60)
print(" STARTING AEGIS ORPHAN RESOURCES CLEANUP ".center(60, "="))
print("=" * 60)

# 1. SQS trigger mapping (Lambda Event Source Mappings)
try:
    print("\n--- 1. Deleting Event Source Mappings ---")
    res = lambda_client.list_event_source_mappings(FunctionName="rajgenstack-triage-vitals-processor")
    mappings = res.get('EventSourceMappings', [])
    if mappings:
        for mapping in mappings:
            uuid = mapping['UUID']
            print(f"Deleting event source mapping {uuid}...")
            lambda_client.delete_event_source_mapping(UUID=uuid)
            # Wait for event source mapping deletion to process
            time.sleep(2)
    else:
        print("No event source mappings found.")
except Exception as e:
    print(f"Note/Error: {e}")

# 2. Lambda Functions
print("\n--- 2. Deleting Lambda Functions ---")
functions = [
    "rajgenstack-triage-triage-api",
    "rajgenstack-triage-vitals-processor",
    "rajgenstack-triage-remediation-processor"
]
for f in functions:
    try:
        print(f"Deleting function: {f}...")
        lambda_client.delete_function(FunctionName=f)
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"Function {f} not found.")
    except Exception as e:
        print(f"Error deleting function {f}: {e}")

# 3. EventBridge Rules
print("\n--- 3. Deleting EventBridge Rules & Targets ---")
rule_name = "rajgenstack-triage-remediation-rule"
try:
    # List and remove targets
    res = events_client.list_targets_by_rule(Rule=rule_name)
    targets = res.get('Targets', [])
    if targets:
        target_ids = [t['Id'] for t in targets]
        print(f"Removing targets {target_ids} from rule {rule_name}...")
        events_client.remove_targets(Rule=rule_name, Ids=target_ids)
    
    print(f"Deleting rule {rule_name}...")
    events_client.delete_rule(Name=rule_name)
except events_client.exceptions.ResourceNotFoundException:
    print(f"Rule {rule_name} not found.")
except Exception as e:
    print(f"Error deleting EventBridge rule: {e}")

# 4. CloudWatch Alarms
print("\n--- 4. Deleting CloudWatch Alarms ---")
try:
    res = cloudwatch_client.describe_alarms(AlarmNamePrefix=prefix)
    alarms = res.get('MetricAlarms', [])
    if alarms:
        alarm_names = [a['AlarmName'] for a in alarms]
        print(f"Deleting alarms: {alarm_names}...")
        cloudwatch_client.delete_alarms(AlarmNames=alarm_names)
    else:
        print("No alarms matching prefix found.")
except Exception as e:
    print(f"Error deleting alarms: {e}")

# 5. CloudWatch Dashboard
print("\n--- 5. Deleting CloudWatch Dashboard ---")
dashboard_name = "rajgenstack-triage-triage-dashboard"
try:
    print(f"Deleting dashboard: {dashboard_name}...")
    cloudwatch_client.delete_dashboards(DashboardNames=[dashboard_name])
except Exception as e:
    print(f"Note/Error: {e}")

# 6. SNS Topics
print("\n--- 6. Deleting SNS Topics ---")
try:
    res = sns_client.list_topics()
    topics = res.get('Topics', [])
    deleted_topic = False
    for t in topics:
        arn = t['TopicArn']
        if "rajgenstack-triage-alerts-topic" in arn:
            print(f"Deleting SNS topic: {arn}...")
            sns_client.delete_topic(TopicArn=arn)
            deleted_topic = True
    if not deleted_topic:
        print("No SNS topics matching prefix found.")
except Exception as e:
    print(f"Error deleting SNS topic: {e}")

# 7. DynamoDB Tables
print("\n--- 7. Deleting DynamoDB Table ---")
table_name = "rajgenstack-triage-vitals-table"
try:
    print(f"Deleting table: {table_name}...")
    dynamodb_client.delete_table(TableName=table_name)
    print("Waiting for table deletion to initiate...")
    time.sleep(5)
except dynamodb_client.exceptions.ResourceNotFoundException:
    print(f"Table {table_name} not found.")
except Exception as e:
    print(f"Error deleting DynamoDB table: {e}")

# 8. SQS Queues
print("\n--- 8. Deleting SQS Queues ---")
try:
    res = sqs_client.list_queues(QueueNamePrefix=prefix)
    queues = res.get('QueueUrls', [])
    if queues:
        for url in queues:
            print(f"Deleting queue: {url}...")
            sqs_client.delete_queue(QueueUrl=url)
    else:
        print("No queues matching prefix found.")
except Exception as e:
    print(f"Error deleting SQS queues: {e}")

# 9. IAM Roles & Policies
print("\n--- 9. Deleting IAM Roles & Policies ---")
roles = [
    "rajgenstack-triage-api-role",
    "rajgenstack-triage-processor-role",
    "rajgenstack-triage-remediation-role"
]
for r in roles:
    try:
        # Detach role policies
        res = iam_client.list_attached_role_policies(RoleName=r)
        policies = res.get('AttachedPolicies', [])
        for p in policies:
            p_arn = p['PolicyArn']
            print(f"Detaching policy {p_arn} from role {r}...")
            iam_client.detach_role_policy(RoleName=r, PolicyArn=p_arn)
        
        # Delete role
        print(f"Deleting role: {r}...")
        iam_client.delete_role(RoleName=r)
    except iam_client.exceptions.NoSuchEntityException:
        print(f"Role {r} not found.")
    except Exception as e:
        print(f"Error cleaning role {r}: {e}")

policies_to_delete = [
    "arn:aws:iam::652253417490:policy/rajgenstack-triage-api-policy",
    "arn:aws:iam::652253417490:policy/rajgenstack-triage-processor-policy",
    "arn:aws:iam::652253417490:policy/rajgenstack-triage-remediation-policy"
]
for p_arn in policies_to_delete:
    try:
        print(f"Deleting policy: {p_arn}...")
        iam_client.delete_policy(PolicyArn=p_arn)
    except iam_client.exceptions.NoSuchEntityException:
        print(f"Policy {p_arn} not found.")
    except Exception as e:
        print(f"Error deleting policy {p_arn}: {e}")

# 10. Lambda Log Groups
print("\n--- 10. Deleting Lambda Log Groups ---")
log_groups = [
    "/aws/lambda/rajgenstack-triage-triage-api",
    "/aws/lambda/rajgenstack-triage-vitals-processor",
    "/aws/lambda/rajgenstack-triage-remediation-processor"
]
for lg in log_groups:
    try:
        print(f"Deleting Log Group: {lg}...")
        logs_client.delete_log_group(logGroupName=lg)
    except logs_client.exceptions.ResourceNotFoundException:
        pass
    except Exception as e:
        print(f"Error deleting Log Group {lg}: {e}")

print("\n" + "=" * 60)
print(" AWS CLEANUP PROCESS COMPLETED ".center(60, "="))
print("=" * 60)
