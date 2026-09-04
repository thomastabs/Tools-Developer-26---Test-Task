## Localisation Change Detector

I built this as a Python CLI tool because I'm not really a fan of UI/UX visuals, so a web app for example would be way to out of scope, the main user is probably a releaser or engineer who wants a fast ship/no-ship signal from the terminal or CI. I used `Poetry` for project setup, `Click` for the CLI, and Python's built-in `plistlib` to parse the `.plist` files as structured data instead of doing a raw text diff.

The tool compares a baseline localisation file against a candidate release file and tries to answer: what changed, and which changes should we worry about before shipping?

#### How to run it

```bash
poetry install
poetry run tool verify original_localisations/localisations_1_2_0.plist original_localisations/localisations_1_2_1.plist
```

By default `verify` only prints `blocker` and `warning` findings, since those are the most relevant for a release decision. To include informational changes too:

```bash
poetry run tool verify original_localisations/localisations_1_2_0.plist original_localisations/localisations_1_2_1.plist --listall
```

To write a Markdown report with all findings:

```bash
poetry run tool report original_localisations/localisations_1_2_0.plist original_localisations/localisations_1_2_1.plist docs/generated-report.md
```

#### What I checked

I focused on changes that can realistically break or harm a release: removed localisation keys, removed languages, empty strings, placeholder regressions like losing `%u` or `%@`, suspicious broken placeholders, very long text, lost `\n` line breaks, and candidate files that keep the same internal version as the baseline.

Findings are split into `blocker`, `warning`, and `info`. Removed keys, removed languages, empty strings, and placeholder regressions are blockers. Length and line break issues are warnings because they need UI context. Added keys/languages and fixed broken placeholders are info, because a tool that marks every change as scary becomes noisy quickly.

#### Scope, tests, and next steps

My smallest complete version was: parse both plist files, compare keys/languages, catch empty strings and placeholder regressions, and print a readable terminal report. After that I added `--listall` and the `--risks` arguments, the `report` command, handmade fixture files, invalid plist tests, missing `localisations` tests, and a `.gitignore`.

Run tests with:

```bash
poetry run pytest -q
```

This tool does not validate translation quality and does not know the real UI layout, so long text detection is only a a validated guess. With more time and more brainstorming I would add a CI mode that fails on blockers, or a way to integrate this in a pipeline to verify updates to the localisations, plus a config file for expected languages, allowed placeholders, per-key length limits, intentional exceptions, and much more!
