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
    """Tools for checking localisation release files.

    \b
    Common commands:
      tool verify PLIST_OLD PLIST_NEW
      tool report PLIST_OLD PLIST_NEW OUTPUT
    """


@cli.command()
@click.argument("plist_old", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("plist_new", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--risks","view", flag_value="risks", default="risks", help="Show only blocker and warning findings.", )
@click.option("--listall", "view", flag_value="list", help="Show all changes, including informational changes.", )
def verify(plist_old: Path, plist_new: Path, view: str) -> None:
    """Print localisation changes and risks to the terminal."""
    old, new, findings = analyse(plist_old, plist_new, view)
    click.echo(render_text(old, new, findings))


@cli.command()
@click.argument("plist_old", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("plist_new", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("output", type=click.Path(dir_okay=False, path_type=Path))
def report(plist_old: Path, plist_new: Path, output: Path) -> None:
    """Write a Markdown report with all localisation findings."""
    old, new, findings = analyse(plist_old, plist_new, "list")
    output.write_text(render_markdown(old, new, findings) + "\n", encoding="utf-8")
    click.echo(f"Wrote report to {output}")


def analyse(plist_old: Path, plist_new: Path, view: str) -> tuple[dict[str, Any], dict[str, Any], list[Finding]]:
    old = load_localisation_file(plist_old)
    new = load_localisation_file(plist_new)
    findings = compare_files(old, new)

    if view == "risks":
        findings = only_risks(findings)

    return old, new, findings


def only_risks(findings: list[Finding]) -> list[Finding]:
    risk_findings = []
    for finding in findings:
        if finding.severity in {"blocker", "warning"}:
            risk_findings.append(finding)
    return risk_findings


def load_localisation_file(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as file:
            data = plistlib.load(file)
    except plistlib.InvalidFileException as error:
        raise click.ClickException(f"{path} is not a valid plist file") from error

    localisations = data.get("localisations")
    if not isinstance(localisations, dict):
        raise click.ClickException(f"{path} does not contain a localisations dictionary")

    return {"path": path, "version": data.get("version", "unknown"), "localisations": localisations}


def compare_files(old: dict[str, Any], new: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    old_localisations = old["localisations"]
    new_localisations = new["localisations"]

    if old["version"] == new["version"]:
        findings.append(
            Finding("warning", "version", f"Candidate version is still {new['version']}; expected it to change from the baseline.")
        )
    else:
        findings.append(
            Finding("info", "version", f"Version changed from {old['version']} to {new['version']}.")
        )

    old_keys = set(old_localisations)
    new_keys = set(new_localisations)

    for key in sorted(old_keys - new_keys):
        findings.append(Finding("blocker", "removed-key", "Localisation key was removed.", key=key))

    for key in sorted(new_keys - old_keys):
        findings.append(Finding("info", "added-key", "New localisation key was added.", key=key))
        findings.extend(check_new_key(key, new_localisations[key]))

    for key in sorted(old_keys & new_keys):
        old_entry = old_localisations[key]
        new_entry = new_localisations[key]
        if not isinstance(old_entry, dict) or not isinstance(new_entry, dict):
            findings.append(Finding("blocker", "invalid-entry", "Localisation entry is not a language dictionary.", key=key))
            continue

        findings.extend(compare_entry(key, old_entry, new_entry))

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
        findings.extend(compare_text(key, language, old_text, new_text))

    return findings


def check_new_key(key: str, entry: Any) -> list[Finding]:
    if not isinstance(entry, dict):
        return [Finding("blocker", "invalid-entry", "New localisation entry is not a language dictionary.", key=key)]

    findings: list[Finding] = []
    for language, text in sorted(entry.items()):
        if not str(text).strip():
            findings.append(Finding("blocker", "empty-string", "New key contains an empty string.", key, language))
        if BROKEN_PLACEHOLDER_PATTERN.search(str(text)):
            findings.append(Finding("warning", "broken-placeholder", "New key contains a suspicious percent placeholder.", key, language))
        if is_long_text(str(text)):
            findings.append(Finding("warning", "long-text", "New key contains a long translation that may need UI review.", key, language))
    return findings


def compare_text(key: str, language: str, old_text: str, new_text: str) -> list[Finding]:
    findings: list[Finding] = []

    if not str(new_text).strip():
        findings.append(Finding("blocker", "empty-string", "Translation became empty.", key, language))

    old_placeholders = PLACEHOLDER_PATTERN.findall(str(old_text))
    new_placeholders = PLACEHOLDER_PATTERN.findall(str(new_text))
    if old_placeholders and old_placeholders != new_placeholders:
        findings.append(
            Finding("blocker", "placeholder-change", f"Placeholder changed from {old_placeholders} to {new_placeholders}.", key, language)
        )

    old_broken = bool(BROKEN_PLACEHOLDER_PATTERN.search(str(old_text)))
    new_broken = bool(BROKEN_PLACEHOLDER_PATTERN.search(str(new_text)))
    if new_broken and not old_broken:
        findings.append(Finding("warning", "broken-placeholder", "Translation gained a suspicious percent placeholder.", key, language))
    elif old_broken and not new_broken:
        findings.append(Finding("info", "fixed-placeholder", "Suspicious percent placeholder appears to be fixed.", key, language))

    if old_text and len(str(new_text)) > len(str(old_text)) * 1.8:
        findings.append(
            Finding("warning", "length-growth", f"Translation grew from {len(str(old_text))} to {len(str(new_text))} characters.", key, language)
        )

    if "\\n" in str(old_text) and "\\n" not in str(new_text):
        findings.append(Finding("warning", "line-breaks", "Translation lost all explicit line breaks.", key, language))

    return findings


def is_long_text(text: str) -> bool:
    if len(text) > 280:
        return True

    for line in text.split("\\n"):
        if len(line) > 120:
            return True

    return False


def render_text(old: dict[str, Any], new: dict[str, Any], findings: list[Finding]) -> str:
    lines = ["Localisation verification report", f"Baseline: {old['path']} ({old['version']})", f"Candidate: {new['path']} ({new['version']})", "",]
    lines.extend(render_text_summary(findings))
    lines.append("")

    if not findings:
        return "\n".join(lines)

    for severity in ("blocker", "warning", "info"):
        grouped = findings_by_severity(findings, severity)
        if not grouped:
            continue
        lines.append(f"{severity.upper()} ({len(grouped)})")
        for finding in grouped:
            location = format_location(finding)
            lines.append(f"- [{finding.kind}] {location}{finding.message}")
        lines.append("")

    return "\n".join(lines).rstrip()


def render_markdown(old: dict[str, Any], new: dict[str, Any], findings: list[Finding]) -> str:
    lines = ["# Localisation Verification Report", "", f"- Baseline: `{old['path']}` (`{old['version']}`)", f"- Candidate: `{new['path']}` (`{new['version']}`)", "",]
    lines.extend(render_markdown_summary(findings))
    lines.append("")

    if not findings:
        return "\n".join(lines)

    for severity in ("blocker", "warning", "info"):
        grouped = findings_by_severity(findings, severity)
        if not grouped:
            continue
        lines.append(f"## {severity.title()} ({len(grouped)})")
        lines.append("")
        for finding in grouped:
            location = format_location(finding)
            lines.append(f"- **{finding.kind}**: {location}{finding.message}")
        lines.append("")

    return "\n".join(lines).rstrip()


def render_text_summary(findings: list[Finding]) -> list[str]:
    summary = count_findings_by_severity(findings)
    recommendation = get_ship_recommendation(summary)

    return [
        "SUMMARY",
        f"- Blockers: {summary['blocker']}",
        f"- Warnings: {summary['warning']}",
        f"- Info: {summary['info']}",
        f"- Ship recommendation: {recommendation}",
    ]


def render_markdown_summary(findings: list[Finding]) -> list[str]:
    summary = count_findings_by_severity(findings)
    recommendation = get_ship_recommendation(summary)

    return [
        "## Summary",
        "",
        f"- Blockers: **{summary['blocker']}**",
        f"- Warnings: **{summary['warning']}**",
        f"- Info: **{summary['info']}**",
        f"- Ship recommendation: **{recommendation}**",
    ]


def count_findings_by_severity(findings: list[Finding]) -> dict[str, int]:
    summary = {"blocker": 0, "warning": 0, "info": 0}
    for finding in findings:
        summary[finding.severity] += 1
    return summary


def get_ship_recommendation(summary: dict[str, int]) -> str:
    if summary["blocker"] > 0:
        return "DO NOT SHIP"
    if summary["warning"] > 0:
        return "REVIEW BEFORE SHIPPING"
    return "OK TO SHIP"


def findings_by_severity(findings: list[Finding], severity: str) -> list[Finding]:
    grouped_findings = []
    for finding in findings:
        if finding.severity == severity:
            grouped_findings.append(finding)
    return grouped_findings


def format_location(finding: Finding) -> str:
    parts = []
    if finding.key:
        parts.append(finding.key)
    if finding.language:
        parts.append(finding.language)
    return f"{' / '.join(parts)}: " if parts else ""
