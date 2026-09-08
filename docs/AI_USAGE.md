## AI Usage

I used AI mainly as a coding assistant for this task. I had already set the foundation of the project, understood the problem, and identified the main patterns in the original localisation files before asking for implementation help.

My own initial direction was to build this as a CLI tool, because I think this problem fits better as something a releaser or engineer can run quickly from the terminal. I also already had the main command shape in mind: something like `tool verify <plist_old> <plist_new>` to compare the old production file against the new candidate file and show a list of changes and risks.

The place where I used AI the most was in the Python implementation, since I was not very familiar with building CLI tools using `Click`. AI helped me understand how to structure a Click command group, how to expose commands through `pyproject.toml`, and how to make commands like `verify` and `report` work through Poetry.

Some specific things AI gave me that I kept:

- the general `Click` structure with a main `cli()` group and subcommands like `verify` and `report`;
- the use of Python's built-in `plistlib` to parse the `.plist` files safely instead of reading them as plain text;
- the idea of returning findings as structured objects with a severity, kind, message, key, and language;
- the improved placeholder detection, where the output says if a placeholder is missing, added, reordered, or fixed.

Some specific things AI suggested or implemented that I pushed back on:

- at one point the `verify` command had too many arguments and options, including `--format` and `--output`. I disagreed with that because I wanted `verify` to stay as the simple main terminal command;
- I asked to split file generation into a separate `report` command, because that made the CLI clearer: `verify` is for terminal checking, `report` is for a Markdown file;
- I also pushed back on code patterns I did not feel comfortable with, like lambda functions and compact list comprehensions in places where I wanted the logic to be more explicit and easier to explain.

I verified the AI output by running the actual CLI commands against the provided localisation files and checking that the output matched the issues I had already identified manually. For example, the tool detected removed languages, empty strings, placeholder changes, long text warnings, and the fixed French placeholder.

After improving the placeholder detection, I verified that the output became more useful and less generic. Instead of only saying `placeholder-change`, the tool now reports clearer findings like `missing-placeholder`, `added-placeholder`, `placeholder-order`, and `fixed-placeholder`. I also checked that the French placeholder fix was not reported as a scary warning, because in this case it is actually a correction.

I also verified the implementation with automated tests:

```bash
poetry run pytest -q
```

The tests use small handmade plist files so the expected behaviour is easier to understand. They cover blocker findings, informational findings, report generation, invalid plist input, missing `localisations`, top-level help output, summary output, and the more specific placeholder detection.

The main surprise was that AI was useful not only for writing the code, but also for helping shape the CLI interface. At the same time, I had to keep reducing the scope when the tool started becoming more complex than I wanted. The final version is intentionally simple: one command to verify in the terminal, and one command to generate a full Markdown report.
