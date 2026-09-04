import plistlib
from pathlib import Path

from click.testing import CliRunner

from tool.tool import analyse, cli

FIXTURES = Path(__file__).parent / "fixtures"


def write_plist(path, version, localisations):
    with path.open("wb") as file:
        plistlib.dump(
            {"version": version, "localisations": localisations},
            file,
        )


def write_raw_plist(path, data):
    with path.open("wb") as file:
        plistlib.dump(data, file)


def finding_kinds(findings):
    return {finding.kind for finding in findings}


def test_analyse_risks_detects_release_blockers(tmp_path):
    old_path = tmp_path / "old.plist"
    new_path = tmp_path / "new.plist"
    write_plist(
        old_path,
        "1.0.0",
        {
            "removed-key": {"en-US": "Play", "es": "Jugar"},
            "countdown": {"en-US": "Starting in %u", "es": "Empieza en %u"},
            "body": {"en-US": "Watch video", "es": "Ver video"},
        },
    )
    write_plist(
        new_path,
        "1.0.0",
        {
            "countdown": {"en-US": "Starting in %u", "es": ""},
            "body": {"en-US": "Watch video"},
        },
    )

    _, _, findings = analyse(old_path, new_path, "risks")

    assert finding_kinds(findings) == {
        "empty-string",
        "placeholder-change",
        "removed-key",
        "removed-language",
        "version",
    }


def test_analyse_listall_includes_info_for_safe_additions_and_fixes(tmp_path):
    old_path = tmp_path / "old.plist"
    new_path = tmp_path / "new.plist"
    write_plist(
        old_path,
        "1.0.0",
        {"countdown": {"fr": "Commence dans % ..."}},
    )
    write_plist(
        new_path,
        "1.0.1",
        {
            "countdown": {"fr": "Commence dans %u...", "jp": "開始まで %u..."},
            "new-key": {"en-US": "New text"},
        },
    )

    _, _, findings = analyse(old_path, new_path, "list")

    assert "fixed-placeholder" in finding_kinds(findings)
    assert "added-language" in finding_kinds(findings)
    assert "added-key" in finding_kinds(findings)
    assert "version" in finding_kinds(findings)


def test_verify_defaults_to_terminal_risks_only(tmp_path):
    old_path = tmp_path / "old.plist"
    new_path = tmp_path / "new.plist"
    write_plist(old_path, "1.0.0", {"existing": {"en-US": "Ready %u"}})
    write_plist(
        new_path,
        "1.0.0",
        {
            "existing": {"en-US": "Ready"},
            "new-key": {"en-US": "New text"},
        },
    )

    result = CliRunner().invoke(cli, ["verify", str(old_path), str(new_path)])

    assert result.exit_code == 0
    assert "SUMMARY" in result.output
    assert "Ship recommendation: DO NOT SHIP" in result.output
    assert "BLOCKER" in result.output
    assert "placeholder-change" in result.output
    assert "INFO" not in result.output
    assert "added-key" not in result.output


def test_report_writes_markdown_with_all_findings(tmp_path):
    old_path = tmp_path / "old.plist"
    new_path = tmp_path / "new.plist"
    output_path = tmp_path / "report.md"
    write_plist(old_path, "1.0.0", {"existing": {"en-US": "Ready %u"}})
    write_plist(
        new_path,
        "1.0.0",
        {
            "existing": {"en-US": "Ready"},
            "new-key": {"en-US": "New text"},
        },
    )

    result = CliRunner().invoke(
        cli,
        ["report", str(old_path), str(new_path), str(output_path)],
    )

    assert result.exit_code == 0
    report = output_path.read_text(encoding="utf-8")
    assert "# Localisation Verification Report" in report
    assert "## Summary" in report
    assert "Ship recommendation: **DO NOT SHIP**" in report
    assert "## Blocker" in report
    assert "## Info" in report
    assert "added-key" in report


def test_top_level_help_lists_command_arguments():
    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "tool verify PLIST_OLD PLIST_NEW" in result.output
    assert "tool report PLIST_OLD PLIST_NEW OUTPUT" in result.output


def test_verify_fails_for_invalid_plist_file(tmp_path):
    old_path = tmp_path / "old.plist"
    invalid_path = tmp_path / "invalid.plist"
    write_plist(old_path, "1.0.0", {"existing": {"en-US": "Ready"}})
    invalid_path.write_text("this is not valid plist xml", encoding="utf-8")

    result = CliRunner().invoke(cli, ["verify", str(old_path), str(invalid_path)])

    assert result.exit_code != 0
    assert "is not a valid plist file" in result.output


def test_verify_fails_when_localisations_dictionary_is_missing(tmp_path):
    old_path = tmp_path / "old.plist"
    missing_localisations_path = tmp_path / "missing-localisations.plist"
    write_plist(old_path, "1.0.0", {"existing": {"en-US": "Ready"}})
    write_raw_plist(missing_localisations_path, {"version": "1.0.1"})

    result = CliRunner().invoke(
        cli,
        ["verify", str(old_path), str(missing_localisations_path)],
    )

    assert result.exit_code != 0
    assert "does not contain a localisations dictionary" in result.output


def test_cli_with_fixture_localisation_files():
    old_path = FIXTURES / "localisations_old.plist"
    new_path = FIXTURES / "localisations_new.plist"

    result = CliRunner().invoke(cli, ["verify", str(old_path), str(new_path), "--listall"])

    assert result.exit_code == 0
    assert "empty-string" in result.output
    assert "placeholder-change" in result.output
    assert "removed-language" in result.output
    assert "line-breaks" in result.output
    assert "fixed-placeholder" in result.output
    assert "added-key" in result.output
