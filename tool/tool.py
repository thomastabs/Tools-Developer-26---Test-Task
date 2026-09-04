from __future__ import annotations

import plistlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import click


PLACEHOLDER_PATTERN = re.compile(r"%(?:@|u|d|s|f)")
BROKEN_PLACEHOLDER_PATTERN = re.compile(r"%(?![@udsfi0-9.])")
SEVERITY_ORDER = {"blocker": 0, "warning": 1, "info": 2}


@dataclass(frozen=True)
class Finding:
    severity: str
    kind: str
    message: str
    key: str | None = None
    language: str | None = None


@click.group()
def cli() -> None:
    """Tools for checking localisation release files."""


@cli.command()
@click.argument("plist_old", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("plist_new", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def verify(plist_old: Path, plist_new: Path) -> None:
    """Print localisation changes and risks to the terminal."""
    old = load_localisation_file(plist_old)
    new = load_localisation_file(plist_new)
    findings = compare_files(old, new)
    click.echo(render_text(old, new, findings))


def load_localisation_file(path: Path) -> dict[str, Any]:
    with path.open("rb") as file:
        data = plistlib.load(file)

    return {
        "path": path,
        "version": data.get("version", "unknown"),
        "localisations": data["localisations"],
    }


def compare_files(old: dict[str, Any], new: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    old_localisations = old["localisations"]
    new_localisations = new["localisations"]

    if old["version"] == new["version"]:
        findings.append(Finding("warning", "version", "Candidate version is unchanged."))

    old_keys = set(old_localisations)
    new_keys = set(new_localisations)

    for key in sorted(old_keys - new_keys):
        findings.append(Finding("blocker", "removed-key", "Localisation key was removed.", key=key))

    for key in sorted(new_keys - old_keys):
        findings.append(Finding("info", "added-key", "New localisation key was added.", key=key))

    for key in sorted(old_keys & new_keys):
        findings.extend(compare_entry(key, old_localisations[key], new_localisations[key]))

    return sorted(findings, key=finding_sort_key)


def finding_sort_key(finding: Finding) -> tuple[int, str, str, str]:
    severity_rank = SEVERITY_ORDER[finding.severity]
    key = finding.key or ""
    language = finding.language or ""
    return severity_rank, finding.kind, key, language


def compare_entry(key: str, old_entry: dict[str, str], new_entry: dict[str, str]) -> list[Finding]:
    findings: list[Finding] = []
    old_languages = set(old_entry)
    new_languages = set(new_entry)

    for language in sorted(old_languages - new_languages):
        findings.append(Finding("blocker", "removed-language", "Language was removed from an existing key.", key, language))

    for language in sorted(new_languages - old_languages):
        findings.append(Finding("info", "added-language", "Language was added to an existing key.", key, language))

    for language in sorted(old_languages & new_languages):
        old_text = old_entry[language]
        new_text = new_entry[language]
        if not str(new_text).strip():
            findings.append(Finding("blocker", "empty-string", "Translation became empty.", key, language))

        old_placeholders = PLACEHOLDER_PATTERN.findall(str(old_text))
        new_placeholders = PLACEHOLDER_PATTERN.findall(str(new_text))
        if old_placeholders and old_placeholders != new_placeholders:
            findings.append(Finding("blocker", "placeholder-change", "Placeholder changed.", key, language))

        if BROKEN_PLACEHOLDER_PATTERN.search(str(new_text)):
            findings.append(Finding("warning", "broken-placeholder", "Suspicious percent placeholder.", key, language))

    return findings


def render_text(old: dict[str, Any], new: dict[str, Any], findings: list[Finding]) -> str:
    lines = [
        "Localisation verification report",
        f"Baseline: {old['path']} ({old['version']})",
        f"Candidate: {new['path']} ({new['version']})",
        "",
    ]

    for severity in ("blocker", "warning", "info"):
        grouped = []
        for finding in findings:
            if finding.severity == severity:
                grouped.append(finding)

        if not grouped:
            continue

        lines.append(f"{severity.upper()} ({len(grouped)})")
        for finding in grouped:
            location = format_location(finding)
            lines.append(f"- [{finding.kind}] {location}{finding.message}")
        lines.append("")

    return "\n".join(lines).rstrip()


def format_location(finding: Finding) -> str:
    parts = []
    if finding.key:
        parts.append(finding.key)
    if finding.language:
        parts.append(finding.language)
    return f"{' / '.join(parts)}: " if parts else ""
