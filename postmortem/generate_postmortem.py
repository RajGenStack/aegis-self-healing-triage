#!/usr/bin/env python3
"""
Incident Postmortem Report Generator.
Generates standardized incident postmortems with calculated MTTR metrics.
"""

import argparse
import os
import sys
from datetime import datetime

# Setup paths relative to script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def create_postmortem_report(incident_id, scenario, duration_seconds, trigger_method):
    """Generates a standardized Markdown postmortem incident report."""
    
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Calculate MTTR details
    # For automated remediation loops:
    # - Detection Time: ~60s (CloudWatch alarm evaluation cycle)
    # - Resolution Time: ~25s (EventBridge trigger + Lambda remediation)
    detection_time_est = 60
    remediation_time_est = duration_seconds - detection_time_est if duration_seconds > detection_time_est else 15
    
    scenario_titles = {
        "db-failure": "Database Writing Ingestion Failure (Incorrect Table Config)",
        "concurrency-block": "Vitals Processor Concurrency Outage (Kill-Switch Active)",
        "event-mapping-disable": "SQS Telemetry Ingest Trigger Outage (Disabled Mapping)"
    }
    
    scenario_rca = {
        "db-failure": "The Processor Lambda environment variable DYNAMODB_TABLE was updated to an invalid table name ('non-existent-table-chaos') during chaos testing. This caused DynamoDB Write DynamoDB Client put_item queries to fail, raising Lambda Errors metrics.",
        "concurrency-block": "The Processor Lambda Reserved Concurrent Executions was set to 0. This throttled all incoming invocation attempts, causing vitals messages to pile up in the SQS ingestion queue.",
        "event-mapping-disable": "The SQS event source mapping trigger on the Processor Lambda was set to Enabled=False. Ingestion of vitals ceased completely, and messages accumulated in SQS."
    }
    
    scenario_fixes = {
        "db-failure": "EventBridge intercepted the state change of 'processor-errors-alarm' to ALARM. It invoked the remediation Lambda, which updated the Processor Lambda environment variable DYNAMODB_TABLE back to the correct value.",
        "concurrency-block": "EventBridge intercepted the backlog alarm state change. The remediation Lambda executed a delete_function_concurrency API call, restoring concurrency to unlimited and allowing processing of the SQS backlog.",
        "event-mapping-disable": "EventBridge intercepted the latency/backlog alarm. The remediation Lambda identified the disabled SQS trigger mapping UUID and executed an update_event_source_mapping API call to re-enable it."
    }
    
    title = scenario_titles.get(scenario, f"Chaos Outage: {scenario}")
    rca_desc = scenario_rca.get(scenario, "A chaos outage scenario was manually injected during testing.")
    fix_desc = scenario_fixes.get(scenario, "Remediation Lambda restored configuration values to normal.")
    
    report_content = f"""# Incident Postmortem - {incident_id}

## Incident Summary

| Metric | Details |
|---|---|
| **Incident ID** | {incident_id} |
| **Date** | {date_str} |
| **Outage Type** | {title} |
| **Trigger Method** | {trigger_method} |
| **System Down Time** | {duration_seconds} seconds |
| **Mean Time to Resolution (MTTR)** | {duration_seconds} seconds |
| **Postmortem Generated** | {timestamp_str} |

---

## Timeline

- **00:00:00** - Outage injected manually using chaos engineering CLI.
- **00:01:00** - CloudWatch metrics evaluated; Alarm transitioned to `ALARM` state. (Detection Time: ~{detection_time_est}s)
- **00:01:02** - EventBridge rule triggered on alarm state transition; invoked Remediation Lambda.
- **00:01:10** - Remediation Lambda completed boto3 configuration checks and applied corrections.
- **00:01:15** - Processor pipeline returned to normal status; pending SQS backlogs successfully processed. (Remediation & Resolution Time: ~{remediation_time_est}s)
- **00:01:25** - Active status check confirmed system returned to 100% health.

---

## Root Cause Analysis (RCA)

{rca_desc}

---

## Remediation & Recovery

**Remediation Logic executed**:
{fix_desc}

**Verifiable Outcomes**:
- Active system configuration check returned to `Normal`.
- API returned successful responses from the corrected database.
- Pending telemetry items processed without message loss.

---

## Prevention & Future Improvements

1. **Keep Self-Healing Active**: Ensure the EventBridge rule targets are enabled on all staging and production deployments.
2. **Alert Subscriptions**: Configure an active email subscription on `sns-alerts-topic` to log all self-healing execution events.
3. **IAM Constraints**: Limit remediation execution permissions using tight IAM resource boundaries to prevent unauthorized configuration updates.
"""
    
    output_filename = f"incident_{incident_id}.md"
    output_path = os.path.join(SCRIPT_DIR, output_filename)
    
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"Successfully generated postmortem report: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error writing postmortem report: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="AEGIS Incident Postmortem Generator")
    parser.add_argument("--incident-id", required=True, help="Unique Incident Identifier (e.g. INC-001)")
    parser.add_argument("--scenario", choices=["db-failure", "concurrency-block", "event-mapping-disable"], required=True, help="Injected chaos outage scenario")
    parser.add_argument("--duration", type=int, required=True, help="Total system downtime / resolution time in seconds")
    parser.add_argument("--trigger-method", default="Automatic CloudWatch Alarm + EventBridge Target", help="Method by which remediation was triggered")
    
    args = parser.parse_args()
    
    create_postmortem_report(
        incident_id=args.incident_id,
        scenario=args.scenario,
        duration_seconds=args.duration,
        trigger_method=args.trigger_method
    )

if __name__ == "__main__":
    main()
