# Translation rules (v0.1): Human SOP → agent-readable SOP draft

These rules define how a translation tool converts a human-authored SOP into an agent-readable SOP draft (YAML) plus a translation notes file.

The tool must be conservative: it should not invent thresholds, approvals, or authority. When uncertain, it must escalate and mark unresolved items for human review.

---

## 1. Outputs

For every input SOP, the tool produces:

1) `sop_machine_draft.yaml`
- Conforms to the repository's notation in `spec.md`
- Encodes explicit constraints, decisions, allowed actions, escalations, approvals, prohibitions, and records

2) `translation_notes.md`
- Lists extracted facts
- Lists unresolved ambiguities and missing thresholds
- Lists all assumptions (should be minimal)
- Lists where escalation was used due to uncertainty

---

## 2. Safety-first defaults

1. Do not invent:
- numeric limits (ranges, tolerances, durations)
- units
- authority boundaries
- approval gates
- disposition logic
- exception handling thresholds

2. When a required field is missing:
- insert a placeholder field
- add a TODO marker
- add an entry in `translation_notes.md`
- default to escalation for any decision dependent on that missing information

3. Prefer "deny or escalate" over "allow" when uncertain.

---

## 3. Extraction rules

### 3.1 SOP metadata
Extract if present:
- SOP ID / code
- title
- domain (pharma, fnb, etc.)
- version/effective date
- owner role

If not present:
- generate a stable ID using folder name and a sequence (documented in notes)
- keep effective_date as "YYYY-MM-DD"
- owner_role defaults to QA or FoodSafetyQA only if explicitly stated; otherwise "UNKNOWN_OWNER"

### 3.2 Roles
Extract roles from the "Roles and responsibilities" section:
- map each role to `roles[]` with `type: human`

Add the system role:
- always include `Agent` with `type: system`

If the SOP mentions systems (MES, LIMS, data logger), do not add them as roles unless they perform actions; log them as context in notes.

### 3.3 Inputs
Inputs are values needed to evaluate conditions or complete records, such as:
- temperature, time, batch/lot IDs, location/equipment IDs, product IDs

Rules:
- If a value has a unit in the SOP, capture it
- If unit is missing, set unit to "UNKNOWN" and add a note
- Never convert units unless explicitly stated

### 3.4 Records
Extract required records from "Records" section.
If absent, infer only the minimal records that are explicitly mentioned (for example "deviation record", "log").
Do not invent record types.

---

## 4. Ambiguity detection and handling

The tool must detect ambiguous language and treat it as unresolved unless the SOP provides explicit thresholds.

### 4.1 Ambiguity phrases (non-exhaustive)
Flag phrases such as:
- "as needed"
- "if appropriate"
- "promptly"
- "as soon as practical"
- "reasonable steps"
- "where required"
- "may affect"
- "ensure"
- "significant"
- "acceptable"
- "notify immediately" (unless "immediately" is defined)

### 4.2 How to translate ambiguity
- Do not encode ambiguous phrases as executable rules
- Convert them into:
  - an escalation requirement, or
  - a TODO placeholder in constraints/decisions, and
  - a note explaining what is missing

Example:
- Human: "Notify QA as soon as practical"
- Agent form: `A_NOTIFY_QA` action is mandatory, but timing SLA is left out, and a note is added: "Timing undefined in SOP."

---

## 5. Decision logic rules

### 5.1 Convert explicit conditions into decisions
If the SOP contains explicit conditional triggers with measurable criteria:
- "if temperature > 8°C"
- "if CCP limit exceeded"
- "if alarm triggers and threshold is defined"

Then create:
- `decisions[]` entries with `when` expressions referencing inputs

### 5.2 If conditions are not measurable
If the SOP uses non-measurable conditions:
- "if quality may be affected"
- "if deviation is significant"
- "if not resolved"

Then:
- do not create a measurable `when`
- create an escalation decision with a TODO field
- add a note for human review

### 5.3 Default escalation on breach
Any breach of a defined constraint must produce:
- a containment action (hold/segregate/stop) if described
- notification to the responsible quality role
- record creation
- required escalation

---

## 6. Actions and permissions

### 6.1 Action extraction
Actions are verbs that cause state changes or generate records, such as:
- apply hold, segregate, notify, record, stop, label, quarantine

Rules:
- Only create actions that appear in the SOP
- Use a limited action vocabulary where possible (hold, notify, record)
- Avoid inventing operational steps that the SOP does not state

### 6.2 Allowed actors
Default permissions:
- Containment and documentation actions can be allowed for `Agent` only if they are:
  - reversible, and
  - safety-conservative (for example apply hold, notify QA, record event)

If unclear, restrict to humans and add a note.

### 6.3 Forbidden actions (prohibitions)
Create explicit prohibitions when the SOP indicates exclusive authority, such as:
- "Only QA may authorize release"
- "QA determines disposition"
- "Food Safety approves disposition"

Rules:
- If a human SOP states exclusivity, encode it as:
  - `approvals[]` gate + `prohibitions[]` entries
- If exclusivity is implied but not stated, do not infer it; add a note.

---

## 7. Approvals and sign-off gates

### 7.1 Approval extraction
When SOP includes:
- "Only QA may authorize..."
- "QA approves..."
- "Food Safety evaluates and determines disposition..."

Then create:
- an `approvals[]` entry specifying the approver role
- a corresponding `prohibitions[]` preventing non-approvers from taking that decision

### 7.2 No invented approvals
If approvals are not mentioned, do not add new gates. Instead:
- add a note: "Approval model not specified in human SOP."

---

## 8. Constraint encoding

### 8.1 Constraints must be machine-checkable
A constraint must be:
- numeric or boolean
- expressed in a clear rule form referencing inputs

Do not encode:
- "maintain appropriate conditions"
- "ensure compliance"
as constraints.

### 8.2 Parameterization
If the SOP indicates that limits vary by material/product:
- model the limit as an input parameter (for example `storage_min_c`, `storage_max_c`) or `ccp_limit_c`
- add a note: "Limits are product-specific; provide values per product."

---

## 9. Quality of translation: acceptance checks

The tool must refuse to produce an "apparently complete" YAML if key elements are missing.

Minimum completeness requirements:
- at least one role besides Agent
- at least one action
- at least one record
- at least one escalation OR explicit statement that none apply

If not met:
- output YAML with TODO placeholders
- output notes listing what is missing
- do not attempt to fill gaps

---

## 10. Human review contract

The draft output must include, in `translation_notes.md`:
- a list of all TODO placeholders
- a list of ambiguous phrases found
- a list of decisions that defaulted to escalation
- a list of actions the Agent is allowed to perform and why
- a list of actions the Agent is forbidden to perform and why

The translation is not considered final until a human reviewer:
- confirms limits and units
- confirms authority boundaries
- confirms required records
- approves the final agent-readable SOP version
