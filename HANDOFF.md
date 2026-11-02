# Handoff: turn the PRD into an implementation plan

**Next session's goal:** run `/prd-to-plan` on the PRD to produce a
multi-phase implementation plan made of vertical slices, each one working
end to end, saved under `plans/`.

## Where things stand

- **The design is finished.** All decisions are in
  `prd/applicant-tracking-system.md`. Read it in full before planning, and
  don't re-ask questions it already answers.
- **No Django project exists yet.** The repo contains only:
  - `.claude/skills/`
  - `PROMPTS.md` (the AI usage log)
  - `prd/`
  - `prototypes/`
  - `README.md` and `.gitignore`

  Phase 1 of the plan will need to set up the project: uv, Django, the
  single `hiring` app, django-tailwind-cli with DaisyUI, HTMX, Ruff, and
  pytest-django.
- **Prototypes** in `prototypes/` are throwaway single-file Django apps with
  in-memory data and no login. The user confirmed both work in the browser.
  - `stage_pipeline.py` contains the stage-transition logic
    (`allowed_moves`, `move_to`), rule checks that can become pytest tests,
    and the HTMX row swap with the out-of-band history pattern.
  - `dashboard.py` contains the dashboard layout and the HTMX Close/Reopen
    that also updates a total out-of-band.
  - **Agreed plan for them:** keep them as a reference, and delete each one
    in the same commit as the real feature that replaces it. The plan
    should include those deletions in the right phases.
- **Why each decision was made** (the 21 grill-me questions and answers) is
  recorded in the two 2026-11-02 entries of `PROMPTS.md`. Check there if the
  PRD's reasoning is unclear.
- **Uncommitted files** (as of this handoff): `PROMPTS.md`, `prd/`,
  `prototypes/` and `HANDOFF.md`.

## Working with this user

- **They're a beginner.** When a real decision comes up:
  - Ask one question at a time.
  - Say what part of the design it settles.
  - List the options, with what each one costs.
  - Recommend one, and say why.
- **They commit themselves.** Suggest a commit message, but don't run
  `git commit` unless they ask.
- **At the end of the session they'll ask for a session-log entry in
  `PROMPTS.md`.** Follow the format at the top of that file: newest entry
  first, and never edit old entries.
  - The file uses Windows (CRLF) line endings and may not end with a newline.
  - Adding the entry with a small Python script that reads and writes bytes
    worked better than the Edit tool.

## Environment notes

- Windows 10, with PowerShell 5.1 as the main shell; Bash is also
  available. uv and Python 3.14 are installed.
- Inline `python -c "..."` passed through PowerShell breaks on quotes. Write
  a script file to the scratchpad and run it instead.
- The prototypes run with `uv run prototypes/<file>.py`, using
  `uv run --with django` for ad-hoc scripts.
- `uvx ruff check` flagged `# noqa: E402` as unused (RUF100), so don't add
  those comments.

## Things for the plan to handle

- **The dashboard was designed during prototyping, not in the interview.**
  The PRD now covers it (user stories 6–17). It depends on most models
  existing, so it fits best in a later phase.
- **Two HTMX behaviours came from the prototypes**, and the PRD records
  them:
  - Refused stage moves return HTTP 200 with an error inside the row.
  - Rows stay visible under a filter until the page is refreshed.
- **The PRD's "Testing focus" list should be spread across the phases**, so
  that each phase's tests match the slice it builds.

## Suggested skills

- **`/prd-to-plan`:** the main task for the next session. Input:
  `prd/applicant-tracking-system.md`.
- **`/grill-me`:** only if planning turns up a real open question that the
  PRD doesn't answer.
- **`/implement` or `/tdd`:** for later sessions that build a phase from the
  plan. `/tdd` is best suited to the stage-transition rules and the model
  constraints.
- **`/handoff`:** at the end of the next session, so the session after it
  can start implementing.
