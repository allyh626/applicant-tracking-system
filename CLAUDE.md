# CLAUDE.md

## Project

An internal applicant tracking system built with Django (single `hiring` app).

- **Design:** `prd/applicant-tracking-system.md` holds every design decision.
  Don't re-ask questions it already answers. The reasoning behind each
  decision is in the 2026-11-02 entries of `PROMPTS.md`.
- **Plan:** `plans/applicant-tracking-system.md` breaks the work into phases.
  Build one phase at a time.

## Working with this user

- **They're a beginner.** When a real decision comes up:
  - Ask one question at a time.
  - Say what part of the design it settles.
  - List the options, with what each one costs.
  - Recommend one, and say why.
- **They commit themselves.** Suggest a commit message, but don't run
  `git commit` or `git push` unless they ask. This applies even when a skill
  says to commit.
- **Session log:** at the end of a session they'll ask for an entry in
  `PROMPTS.md`. Follow the format at the top of that file: newest entry
  first, and never edit old entries.
  - The file uses Windows (CRLF) line endings and may not end with a newline.
  - Adding the entry with a small Python script that reads and writes bytes
    works better than the Edit tool.

## Environment notes

- Windows 10, with PowerShell 5.1 as the main shell; Bash is also available.
  uv and Python 3.14 are installed.
- Inline `python -c "..."` passed through PowerShell breaks on quotes. Write a
  script file to the scratchpad and run it instead.
- Use `uv run --with django` for ad-hoc scripts.
- `uvx ruff check` flags `# noqa: E402` as unused (RUF100), so don't add those
  comments.
