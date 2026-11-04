# Plan: Applicant Tracking System

> Source PRD: `prd/applicant-tracking-system.md` (design reasoning in the 2026-11-02 entries of `PROMPTS.md`)

## Architectural decisions

Durable decisions that apply across all phases:

- **Owning app**: a single Django app named `hiring` holds every domain model, view, form and template. Its URLs live under the `hiring:` namespace.
- **Stack**: Python + Django + SQLite managed with uv; Tailwind CSS + DaisyUI via django-tailwind-cli; HTMX for partial updates; Ruff for linting/formatting; pytest + pytest-django with shared fixtures (logged-in staff client, sample candidates/openings).
- **Authentication**: Django's built-in auth. `LoginRequiredMiddleware` makes every page require login by default; only the login page is exempt. Login/logout use Django's auth views under `/accounts/`, and logout is a POST. No roles, groups or self-registration; accounts are created in the Django admin.
- **IDs in URLs**: numeric primary keys, no slugs.
- **URLs**:
  - `/` — dashboard (home after login)
  - `/accounts/login/`, `/accounts/logout/`
  - `/skills/` — list and add skills
  - `/candidates/`, `/candidates/new/`, `/candidates/<pk>/`, `/candidates/<pk>/edit/`
  - `/candidates/<pk>/archive/`, `/candidates/<pk>/restore/` (POST only)
  - `/openings/`, `/openings/new/`, `/openings/<pk>/`, `/openings/<pk>/edit/`
  - `/openings/<pk>/close/`, `/openings/<pk>/reopen/` (POST only; return a fragment for HTMX requests, otherwise redirect)
  - `/openings/<pk>/pipeline/` — pipeline page, stage filter via `?stage=`
  - `/applications/new/`, `/applications/<pk>/`
  - `/applications/<pk>/move/` (POST only, HTMX; target stage in the POST body)
- **Models** (each one's migration is created in the phase that first needs it):
  - `Skill`: name, trimmed; unique on the lowercased name (database constraint).
  - `Candidate`: first/last name, unique email, optional phone, `source` (text choices: Company Website, Job Board, Referral, Other), optional source details, notes and profile URL, `archived` flag, timestamps.
  - `JobOpening`: title, department, location, description, open/closed boolean, many-to-many to `Skill`, timestamps.
  - `Application`: FK to `Candidate` and FK to `JobOpening`, unique together; `stage` (text choices: Applied, Screening, Interview, Final Review, Offer, Hired, Rejected, Withdrawn), default Applied; timestamps.
  - `StageChange`: FK to `Application`, previous stage, new stage, FK to the user, timestamp. Append-only.
  - Deleting a candidate (admin only) cascades to their applications and stage history.
- **Stage rules**: the allowed moves are defined in one place. Every stage change goes through one method on `Application`, which validates the move, updates the stage and writes a `StageChange` together, or raises an error and writes nothing. Views never set the stage directly.
- **Filters and search**: plain GET forms using URL query parameters, applied on submit.
- **Prototypes**: `prototypes/stage_pipeline.py` and `prototypes/dashboard.py` stay as references until the phase that replaces each one, and are deleted in that phase's commit.

---

## Phase 1: Project skeleton and login gate

**User stories**: 1, 2, 3, 4, 5

### What to build

Set up the Django project with uv, the `hiring` app, django-tailwind-cli with DaisyUI, HTMX, Ruff and pytest-django. Add a base layout with navigation and a logout button, a styled login page, and a placeholder home page at `/`. Every page requires login through the middleware. The admin can create staff accounts.

### Acceptance criteria

- [ ] `uv run` starts the dev server, and Tailwind/DaisyUI styles and HTMX load on the page
- [ ] An anonymous request to `/` redirects to the login page, and logging in returns the user to `/`
- [ ] Logging out (POST) ends the session, and the user is sent back to login
- [ ] An admin can create a staff account in the Django admin, and that account can log in
- [ ] `ruff check` and `ruff format --check` pass
- [ ] pytest runs, with a shared logged-in client fixture and a test that anonymous requests redirect to login

---

## Phase 2: Skills page

**User stories**: 41, 42

### What to build

Add the `Skill` model and the `/skills/` page, which lists every skill alphabetically and has a form to add one. Names are trimmed before saving. A name that matches an existing skill apart from capitalisation or surrounding spaces is refused with a clear form error. Skill is also registered in the admin.

### Acceptance criteria

- [ ] Adding a skill on `/skills/` saves it and shows it in the list
- [ ] Leading and trailing spaces are removed from saved names
- [ ] "python" or " Python " is refused when "Python" exists, with a form error and no crash
- [ ] The lowercased-name uniqueness is enforced by a database constraint (tested at the model level)
- [ ] `/skills/` requires login

---

## Phase 3: Candidates (create, edit, view, search and filter)

**User stories**: 18, 19, 20, 21, 22, 24, 25, 31

### What to build

Add the `Candidate` model with its source choices, plus create, edit, detail and list pages. The list supports a name/email search and a source filter as GET query parameters, so filtered views can be bookmarked. A duplicate email is refused with a clear message. Candidate is registered in the admin, which is the only place a candidate can be deleted.

### Acceptance criteria

- [ ] A candidate can be created with the required fields only, or with all fields, and source is chosen from the four fixed options
- [ ] A duplicate email is refused with a form error, and the uniqueness is enforced by the database
- [ ] Editing a candidate saves the changes, and the detail page shows them
- [ ] `?q=` matches on first name, last name or email, case-insensitively
- [ ] `?source=` limits the list to that source, and it combines with `?q=`
- [ ] The app's own pages have no delete action, and the admin can delete a candidate
- [ ] All candidate pages require login

---

## Phase 4: Job openings (create, edit, view)

**User stories**: 32, 33, 34, 43

### What to build

Add the `JobOpening` model with a many-to-many to `Skill`, plus create, edit, detail and list pages. Required skills are chosen from a multi-select of existing skills. New openings start open. The detail page shows the opening's fields and its required skills. JobOpening is registered in the admin.

### Acceptance criteria

- [ ] An opening can be created with a title, department, location, description and several skills
- [ ] Editing an opening can change its fields and add or remove skills
- [ ] One skill can be attached to several openings
- [ ] The list and detail pages show department, location and required skills
- [ ] All opening pages require login

---

## Phase 5: Close and reopen openings, and the openings filter

**User stories**: 35, 36, 37, 38

### What to build

Add close and reopen actions to the opening detail page. Closing asks for confirmation, and the confirmation says existing applications will continue as normal. Reopening needs no confirmation. Both actions only flip the open/closed flag. The openings list gets an Open/Closed/All filter as a query parameter.

### Acceptance criteria

- [ ] Closing (after confirming) marks the opening closed, and reopening marks it open again
- [ ] The close confirmation text states that existing applications are not affected
- [ ] Close and reopen accept only POST, and a GET is refused
- [ ] `?status=open|closed|all` filters the openings list correctly
- [ ] The open/closed status is visible on the list and detail pages

---

## Phase 6: Create applications

**User stories**: 23, 39, 44, 45

### What to build

Add the `Application` model, which links a candidate to an opening, is unique per pair and starts at Applied. The application form at `/applications/new/` offers only open openings. Validation refuses a closed opening if one is submitted anyway, and refuses a duplicate candidate–opening pair with a clear message. The candidate detail page lists all of that candidate's applications with their opening and current stage. Application is registered in the admin.

### Acceptance criteria

- [ ] Creating an application saves it at the Applied stage
- [ ] Closed openings are not offered in the form's opening choices
- [ ] A crafted POST with a closed opening is refused with a form error
- [ ] A second application for the same candidate and opening is refused with a form error, and the pair is unique at the database level
- [ ] The candidate detail page lists their applications
- [ ] Deleting a candidate in the admin also deletes their applications

---

## Phase 7: Pipeline page with HTMX stage moves

**User stories**: 40, 46, 48, 49, 50, 51, 52, 53, 54, 55

### What to build

Add the `StageChange` model, the single table of allowed moves, and the one `Application` method that performs a move (validates it, updates the stage and writes the history, or raises and writes nothing). Add the pipeline page at `/openings/<pk>/pipeline/`, listing the opening's applications with candidate, current stage and when the stage last changed. Each active row shows a button for its next stage only, plus Reject and Withdraw, which ask for confirmation. Final rows show no buttons.

Clicking a button sends an HTMX POST to `/applications/<pk>/move/`. The server responds with only that row's re-rendered HTML, plus the new history entry out-of-band. A refused move returns the row with an error inside it, using HTTP 200. The current user is recorded on each move. Closed openings keep working here as normal. Use `prototypes/stage_pipeline.py` as the reference for the logic and the HTMX patterns.

### Acceptance criteria

- [ ] Every allowed move succeeds: each forward stage to the next one, and every non-final stage to Rejected or Withdrawn
- [ ] Skipping ahead, moving backwards, and moving out of Hired, Rejected or Withdrawn are all refused by the model method
- [ ] A successful move writes exactly one `StageChange` with the correct previous stage, new stage and user
- [ ] A refused move writes no `StageChange` and leaves the stage unchanged
- [ ] The move endpoint returns only the row fragment and an out-of-band history entry
- [ ] A crafted request for a disallowed move returns HTTP 200 with an error message inside the row
- [ ] Only the next-stage, Reject and Withdraw buttons appear on active rows, and none on final rows
- [ ] Reject and Withdraw ask for confirmation before posting
- [ ] Applications under a closed opening can still be moved
- [ ] The move endpoint accepts only POST and requires login

---

## Phase 8: Pipeline stage filter and application history page

**User stories**: 47, 56

### What to build

Add a `?stage=` filter to the pipeline page. After a move, a row stays visible even if it no longer matches the filter, until the page is refreshed. Add the application detail page at `/applications/<pk>/`, which shows the full stage history in order with who made each change and when, and link to it from pipeline rows and the candidate page. Delete `prototypes/stage_pipeline.py` in this phase's commit.

### Acceptance criteria

- [ ] `?stage=<stage>` shows only applications at that stage, and no filter shows all of them
- [ ] A row moved out of the filtered stage stays on screen until refresh
- [ ] The application detail page lists every `StageChange` in time order, with the user and timestamp
- [ ] Pipeline rows and the candidate's application list link to the application detail page
- [ ] `prototypes/stage_pipeline.py` is removed

---

## Phase 9: Archive and restore candidates

**User stories**: 26, 27, 28, 29, 30

### What to build

Add Archive and Restore actions to the candidate detail page. Archiving is refused, with a message to reject or withdraw the active applications first, while any of the candidate's applications isn't Hired, Rejected or Withdrawn. Archived candidates are hidden from the candidate list unless a show-archived toggle (a query parameter) is on. The application form excludes archived candidates, and validation refuses one if it's submitted anyway.

### Acceptance criteria

- [ ] Archiving is refused, with an explanatory message, while the candidate has any active application
- [ ] Archiving succeeds once all applications are final, or when there are none
- [ ] Restore clears the archived flag
- [ ] Archive and restore accept only POST
- [ ] The candidate list hides archived candidates by default and shows them with the toggle, combined with search and the source filter
- [ ] Archived candidates are not offered in the application form, and a crafted POST with one is refused

---

## Phase 10: Dashboard overview

**User stories**: 6, 7, 8, 9, 10, 11, 16, 17

### What to build

Replace the placeholder home page with the read-only parts of the dashboard: open openings out of the total, active applications, applications at Hired, and active candidates with the archived count shown separately. Below those, show a count for each of the eight stages in order, with the final stages styled differently, a count of active candidates per source, and a list of the most recent stage changes (candidate, opening, from and to stage, user, time ago). Use `prototypes/dashboard.py` as the layout reference.

### Acceptance criteria

- [ ] Every total matches the database for a known fixture set
- [ ] The stage counts cover all eight stages in order, including zero counts, and final stages look different
- [ ] The source counts include only active (non-archived) candidates
- [ ] Recent stage changes are listed newest first, up to a fixed limit
- [ ] The dashboard is the page users land on after logging in

---

## Phase 11: Dashboard openings list with HTMX close/reopen

**User stories**: 12, 13, 14, 15

### What to build

Add the openings list to the dashboard, showing department, location, required skills, number of active applications and open/closed status, with an Open/Closed/All filter that defaults to Open. Each row links to its pipeline page and has a Close or Reopen button. These buttons send an HTMX POST to the existing close/reopen endpoints, which (for HTMX requests) return the re-rendered row plus the open-openings total out-of-band. Delete `prototypes/dashboard.py` in this phase's commit.

### Acceptance criteria

- [ ] The openings list defaults to Open, and `?status=closed|all` works
- [ ] Each row shows its active-application count and links to `/openings/<pk>/pipeline/`
- [ ] For an HTMX request, closing or reopening returns the row fragment plus an out-of-band open-openings total
- [ ] The same close and reopen endpoints still redirect normally for non-HTMX requests (Phase 5 behaviour is unchanged)
- [ ] Closing from the dashboard still asks for confirmation, and reopening doesn't
- [ ] `prototypes/dashboard.py` is removed
