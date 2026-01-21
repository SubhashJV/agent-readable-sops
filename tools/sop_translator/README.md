# SOP Translator (v0)

This tool generates an agent-readable SOP draft (YAML) and translation notes from a human-authored SOP (Markdown).

It is intentionally conservative:
- it does not invent thresholds, units, or authority
- it uses TODO placeholders and escalation when uncertain
- it outputs notes for human review and sign-off

## Prerequisites
- Python 3.10+
- Ollama running locally
- A pulled model (example: llama3.1:8b)

## Install
From the repository root:

```bash
pip install -r tools/sop_translator/requirements.txt

