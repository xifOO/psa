from enum import Enum
from pathlib import Path
import json
import re

from src.config.rules import Config


RULES_START = "<!-- RULES:START -->"
RULES_END = "<!-- RULES:END -->"


def load_rules_metadata() -> dict:
    script_dir = Path(__file__).resolve().parent
    metadata_path = script_dir.parent / "docs" / "rules_metadata.json"

    with open(metadata_path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_md_docs(config: Config, rules_metadata: dict) -> str:
    lines = [
        "## 📋 Rules Reference",
        "",
        "| ID | Rule | Group | Description | Config Parameter | Default Severity |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for rid, meta in rules_metadata.items():
        severity = "UNKNOWN"

        if rid.startswith("LCOM"):
            severity = (
                config.lcom.severity_lcom_increase
                if rid == "LCOM001"
                else config.lcom.severity_high_lcom
            )
        elif rid.startswith("SE"):
            severity = (
                config.sife_effects.severity_global_write
                if rid == "SE001"
                else config.sife_effects.severity_arg_mutation
            )
        elif rid.startswith("TCC"):
            severity = (
                config.tcc.severity_tcc_increase
                if rid == "TCC001"
                else config.tcc.severity_high_tcc
            )

        sev_str = (
            severity.value.upper()
            if isinstance(severity, Enum)
            else str(severity).upper()
        )

        lines.append(
            f"| **{rid}** | `{meta['name']}` | {meta['group']} | "
            f"{meta['desc']} | `{meta['config_param']}` | "
            f"`{sev_str}` |"
        )

    return "\n".join(lines)


def update_readme(readme_path: Path, docs: str) -> None:
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    if RULES_START not in content or RULES_END not in content:
        content = (
            content.rstrip() + "\n\n" + f"{RULES_START}\n\n{docs}\n\n{RULES_END}\n"
        )
    else:
        pattern = re.compile(
            rf"{RULES_START}.*?{RULES_END}",
            re.DOTALL,
        )

        content = pattern.sub(
            f"{RULES_START}\n\n{docs}\n\n{RULES_END}",
            content,
        )

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)


def update_docs() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    config_path = project_root / "settings.yaml"
    readme_path = project_root / "README.md"

    config = Config.from_yaml(config_path)
    rules_metadata = load_rules_metadata()

    docs = generate_md_docs(config, rules_metadata)
    update_readme(readme_path, docs)


if __name__ == "__main__":
    update_docs()
