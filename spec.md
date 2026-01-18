# Agent-readable SOP notation (v0.2)

This document describes a lightweight notation for expressing standard operating procedures (SOPs) in explicit, agent-readable form.

The goal is to remove ambiguity by making inputs, limits, decision logic, allowed actions, and escalation rules explicit, while remaining suitable for human review and sign-off.

This is a working note, not a complete specification.

---

## Design goals

An agent-readable SOP representation should:

- preserve the intent of the human SOP
- make operational boundaries explicit (limits, stop conditions, forbidden actions)
- encode decision points as clear conditions
- define escalation paths that do not rely on interpretation
- declare roles and authority explicitly
- remain readable enough for human review and sign-off

---

## Non-goals

This notation is not:

- a workflow engine or execution runtime
- a replacement for a QMS, MES, LIMS, or document management system
- a proposal for autonomous operation in regulated environments
- a universal SOP standard intended to cover all organizations and formats

---

## Core concepts

The notation models an SOP as a controlled set of permitted actions under explicit constraints.

### SOP
A single procedure identified by a stable ID and supported by metadata needed for review and traceability.

### Role
A human or system actor with explicit authority boundaries (for example, Operator, Supervisor, QA, Agent).

### Inputs
Values required to evaluate conditions or carry out steps (for example, temperature, batch ID, equipment status).

### Constraints
Machine-checkable limits or rules that bound behavior (for example, acceptable ranges, prerequisites, interlocks).

### Decision points
Named conditions that select a branch or enforce escalation (for example, "if temperature out of range").

### Actions
Explicitly allowed operations that may be proposed or executed (for example, "hold batch", "notify QA", "record deviation").

### Escalation
Mandatory handoff to a human role when conditions exceed allowed bounds or require judgment.

---

## Representation format

For examples in this repository, the agent-readable form is expressed as YAML.

A minimal file includes:

- metadata (identity and scope)
- roles and authority
- inputs and parameters (including units where relevant)
- constraints and decision logic
- allowed actions and escalation rules
- records to generate (audit artifacts)

---

## Minimal schema (informal)

The structure below is an intentionally small starting point.

```yaml
sop:
  id: SOP-PHARMA-DEV-001
  title: Temperature excursion handling
  domain: pharma
  version: "0.1"
  effective_date: "YYYY-MM-DD"
  owner_role: QA
  related_docs: []

roles:
  - name: Operator
    type: human
  - name: QA
    type: human
  - name: Agent
    type: system

inputs:
  - name: temperature_c
    type: number
    unit: C
  - name: excursion_minutes
    type: number
    unit: min

constraints:
  - id: C1
    description: "Temperature must be within defined storage range."
    rule: "temperature_c >= 2 and temperature_c <= 8"

decisions:
  - id: D1
    when: "temperature_c < 2 or temperature_c > 8"
    then: ["A_HOLD", "A_NOTIFY_QA", "A_RECORD_DEVIATION", "E_ESCALATE"]

actions:
  - id: A_HOLD
    description: "Place material/batch on hold."
    allowed_for: ["Operator", "Agent"]
  - id: A_NOTIFY_QA
    description: "Notify QA of excursion."
    allowed_for: ["Operator", "Agent"]
  - id: A_RECORD_DEVIATION
    description: "Create a deviation record."
    allowed_for: ["Operator", "Agent"]

escalations:
  - id: E_ESCALATE
    to_role: QA
    required: true
    reason: "Out-of-range condition requires assessment and disposition."

records:
  - name: deviation_log
    required: true


Guidance for writing agent-readable SOPs

Replace vague language with explicit constraints
Avoid terms like "as needed", "if appropriate", "promptly", or "ensure" without thresholds.

Make stop conditions explicit
If a situation requires holding, stopping, or escalation, encode it as a rule.

Separate actions from approvals
Actions may be proposed by an agent, but approvals should be explicit and role-bound.

Prefer bounded choices over free-form steps
Encode allowed actions and forbidden actions rather than assuming intent.

Preserve human sign-off points
Identify where human review is required and treat it as a hard gate.
