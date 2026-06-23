# Incident Postmortem - INC-2026-001

## Incident Summary

| Metric | Details |
|---|---|
| **Incident ID** | INC-2026-001 |
| **Date** | 2026-06-23 |
| **Outage Type** | Database Writing Ingestion Failure (Incorrect Table Config) |
| **Trigger Method** | Automatic CloudWatch Alarm + EventBridge Target |
| **System Down Time** | 85 seconds |
| **Mean Time to Resolution (MTTR)** | 85 seconds |
| **Postmortem Generated** | 2026-06-23 20:45:40 UTC |

---

## Timeline

- **00:00:00** - Outage injected manually using chaos engineering CLI.
- **00:01:00** - CloudWatch metrics evaluated; Alarm transitioned to `ALARM` state. (Detection Time: ~60s)
- **00:01:02** - EventBridge rule triggered on alarm state transition; invoked Remediation Lambda.
- **00:01:10** - Remediation Lambda completed boto3 configuration checks and applied corrections.
- **00:01:15** - Processor pipeline returned to normal status; pending SQS backlogs successfully processed. (Remediation & Resolution Time: ~25s)
- **00:01:25** - Active status check confirmed system returned to 100% health.

---

## Root Cause Analysis (RCA)

The Processor Lambda environment variable DYNAMODB_TABLE was updated to an invalid table name ('non-existent-table-chaos') during chaos testing. This caused DynamoDB Write DynamoDB Client put_item queries to fail, raising Lambda Errors metrics.

---

## Remediation & Recovery

**Remediation Logic executed**:
EventBridge intercepted the state change of 'processor-errors-alarm' to ALARM. It invoked the remediation Lambda, which updated the Processor Lambda environment variable DYNAMODB_TABLE back to the correct value.

**Verifiable Outcomes**:
- Active system configuration check returned to `Normal`.
- API returned successful responses from the corrected database.
- Pending telemetry items processed without message loss.

---

## Prevention & Future Improvements

1. **Keep Self-Healing Active**: Ensure the EventBridge rule targets are enabled on all staging and production deployments.
2. **Alert Subscriptions**: Configure an active email subscription on `sns-alerts-topic` to log all self-healing execution events.
3. **IAM Constraints**: Limit remediation execution permissions using tight IAM resource boundaries to prevent unauthorized configuration updates.
