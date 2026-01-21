## translator script

```python
import argparse
import os
import re
import sys
from pathlib import Path

import requests
import yaml


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def extract_fenced_block(text: str, lang: str) -> str | None:
    # Extract first fenced block like ```yaml ... ```
    pattern = rf"```{re.escape(lang)}\s*(.*?)\s*```"
    m = re.search(pattern, text, flags=re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else None


def extract_numbers(text: str) -> set[str]:
    # Capture integers/decimals; keeps simple tokens like 2, 8, 0.1, 5.0
    return set(re.findall(r"\b\d+(?:\.\d+)?\b", text))


def ollama_chat(model: str, prompt: str) -> str:
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }
    r = requests.post(url, json=payload, timeout=180)
    r.raise_for_status()
    data = r.json()
    # Ollama returns {"message": {"content": "..."}}
    return data["message"]["content"]


def build_prompt(
    prompt_template: str,
    spec_text: str,
    rules_text: str,
    contract_text: str,
    human_sop_text: str
) -> str:
    sections = [
        prompt_template.strip(),
        "\n\n---\n\n## spec.md\n\n" + spec_text.strip(),
        "\n\n---\n\n## translation_rules.md\n\n" + rules_text.strip(),
        "\n\n---\n\n## prompt_contract.md\n\n" + contract_text.strip(),
        "\n\n---\n\n## Human SOP (input)\n\n" + human_sop_text.strip()
    ]
    return "".join(sections)


def validate_yaml(yaml_text: str) -> tuple[bool, str]:
    try:
        yaml.safe_load(yaml_text)
        return True, "YAML parsed successfully."
    except Exception as e:
        return False, f"YAML parse error: {e}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Translate human SOP markdown into agent-readable YAML draft (with notes).")
    ap.add_argument("--input", required=True, help="Path to human SOP markdown file (sop_human.md).")
    ap.add_argument("--model", default="llama3.1:8b", help="Ollama model name, e.g., llama3.1:8b, qwen3:32b.")
    ap.add_argument("--repo_root", default=".", help="Repo root path (where spec.md lives).")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"[error] Input not found: {input_path}")
        return 1

    spec_path = repo_root / "spec.md"
    rules_path = repo_root / "tools" / "sop_translator" / "translation_rules.md"
    contract_path = repo_root / "tools" / "sop_translator" / "prompt_contract.md"
    template_path = repo_root / "tools" / "sop_translator" / "prompts" / "translate_prompt.txt"

    missing = [p for p in [spec_path, rules_path, contract_path, template_path] if not p.exists()]
    if missing:
        print("[error] Missing required files:")
        for p in missing:
            print(" -", p)
        return 1

    prompt = build_prompt(
        read_text(template_path),
        read_text(spec_path),
        read_text(rules_path),
        read_text(contract_path),
        read_text(input_path)
    )

    print(f"[info] Using model: {args.model}")
    print("[info] Calling Ollama at http://localhost:11434 ...")
    try:
        output = ollama_chat(args.model, prompt)
    except requests.RequestException as e:
        print(f"[error] Ollama request failed: {e}")
        print("[hint] Ensure Ollama is running and the model is pulled: ollama pull <model>")
        return 1

    yaml_block = extract_fenced_block(output, "yaml")
    notes_block = extract_fenced_block(output, "markdown")

    out_dir = input_path.parent
    draft_yaml_path = out_dir / "sop_machine_draft.yaml"
    notes_path = out_dir / "translation_notes.md"

    if not yaml_block or not notes_block:
        # Save raw output for debugging
        raw_path = out_dir / "translator_raw_output.txt"
        write_text(raw_path, output)
        write_text(notes_path, "# Translation notes\n\nERROR: Model output did not contain required fenced blocks.\n\nSaved raw output to translator_raw_output.txt\n")
        print("[error] Output formatting invalid. Saved raw output to:", raw_path)
        return 1

    # Guardrail: detect invented numbers not present in input/spec/rules/contract
    reference_text = read_text(input_path) + "\n" + read_text(spec_path) + "\n" + read_text(rules_path) + "\n" + read_text(contract_path)
    ref_nums = extract_numbers(reference_text)
    out_nums = extract_numbers(yaml_block)

    invented = sorted([n for n in out_nums if n not in ref_nums])
    invented_msg = ""
    if invented:
        invented_msg = (
            "WARNING: The YAML draft contains numeric tokens not present in the input/spec/rules/contract.\n"
            f"Potential invented numbers: {', '.join(invented)}\n"
            "Review carefully. Prefer replacing with TODO placeholders.\n\n"
        )

    ok, yaml_status = validate_yaml(yaml_block)

    # Write outputs
    write_text(draft_yaml_path, yaml_block + "\n")
    # Prepend guardrail notes
    final_notes = notes_block.strip()
    if invented_msg or not ok:
        header = "# Translation notes\n\n"
        issues = ""
        if invented_msg:
            issues += invented_msg
        if not ok:
            issues += f"WARNING: {yaml_status}\n\n"
        final_notes = header + issues + final_notes + "\n"
    else:
        # Ensure notes has a heading
        if not final_notes.lstrip().startswith("#"):
            final_notes = "# Translation notes\n\n" + final_notes + "\n"

    write_text(notes_path, final_notes)

    print("[info] Wrote:", draft_yaml_path)
    print("[info] Wrote:", notes_path)
    if invented:
        print("[warn] Potential invented numbers detected. See translation_notes.md")
    if not ok:
        print("[warn] YAML parse issue detected. See translation_notes.md")
        return 1

    print("[ok] Translation draft generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

