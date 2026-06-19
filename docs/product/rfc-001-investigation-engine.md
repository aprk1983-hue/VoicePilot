# RFC-001: VoicePilot Investigation Engine

## Purpose

The VoicePilot Investigation Engine guides a voice engineer through an incident investigation like a senior TAC engineer.

## Investigation Lifecycle

1. Intake
2. Discovery
3. Evidence Collection
4. Analysis
5. Hypothesis Building
6. Elimination
7. Root Cause Confirmation
8. Resolution
9. Verification
10. Learning

## Case Object

```yaml
case_id:
title:
business_impact:
symptom:
platform:
topology:
known_facts:
missing_evidence:
hypotheses:
confidence:
next_best_action:
root_cause:
resolution:
verification:
lessons_learned:
```

## Core Rule

VoicePilot must never provide a final root cause unless it can show evidence.

## MVP Focus

Cisco CUCM -> Cisco CUBE -> ITSP

Issue: Outbound calls fail.
