# PRD: Applicant Tracking System

## Problem Statement

Hiring staff at the company have no single, shared place to track candidates
and where they are in the hiring process. Candidate details, where each
candidate came from (the company website, a job board, a referral, or
somewhere else), which job openings are accepting applicants, and which
skills each opening requires are scattered or kept informally. Because of
this, staff can't easily see who is at which stage for a job, who moved
someone forward or rejected them and when, or which openings are still
active. Without a defined process, applications can skip steps or end up in
inconsistent states. There are also no agreed rules for what happens to
candidate records over time, or to applications under an opening that has
closed.

## Solution

An internal web application, available only to logged-in employees, for
managing the whole hiring pipeline:

- Staff keep one record per candidate, including where the candidate came
  from, and can create job openings with required skills, then open and
  close them.
- Each time a candidate applies to an opening, that becomes an application
  that moves through a fixed hiring process: Applied → Screening → Interview
  → Final Review → Offer → Hired. Reject and Withdraw are available from any
  active stage.
- Stage moves happen on a pipeline page for each opening. Clicking a stage
  button updates only that application's row, without reloading the page.
- Every stage move is recorded with who made it and when.
- Clear rules cover what closing an opening does, and how candidates are
  edited, archived and restored.
- A dashboard gives staff an overview of openings, pipeline activity, where
  candidates come from, and recent stage changes.

## User Stories

### Access

1. As a staff member, I want every page to require login, so that candidate information is only visible to employees.
2. As a visitor who is not logged in, I want to be redirected to the login page when I open any page, so that I can sign in and continue.
3. As an administrator, I want to create staff accounts in the Django admin, so that only people I approve can use the system (there is no public sign-up).
4. As a staff member, I want to log out, so that nobody else can use my session on a shared computer.
5. As a staff member, I want every logged-in employee to have the same abilities, so that nobody is blocked waiting for someone with special permissions.

### Dashboard

6. As a staff member, I want a dashboard as my home page after logging in, so that I can see the state of hiring at a glance.
7. As a staff member, I want to see how many job openings are open out of the total, so that I know how much hiring is underway.
8. As a staff member, I want to see how many applications are active (not Hired, Rejected or Withdrawn), so that I know how much work is in the pipeline.
9. As a staff member, I want to see how many applications have reached Hired, so that I can see hiring outcomes.
10. As a staff member, I want to see how many candidates are active, with the archived count shown separately, so that I understand the size of the candidate pool.
11. As a staff member, I want to see how many applications are at each stage, in order, with the final stages shown differently, so that I can spot bottlenecks.
12. As a staff member, I want to see a list of job openings with their department, location, required skills, number of active applications and open/closed status, so that I can tell them apart and see their workload.
13. As a staff member, I want to filter the dashboard's openings list by Open, Closed or All (defaulting to Open), so that I see what matters right now.
14. As a staff member, I want to close or reopen an opening from the dashboard without reloading the page, and see the open-openings count update at the same time, so that the overview stays accurate.
15. As a staff member, I want a link from each opening on the dashboard to its pipeline page, so that I can go straight to moving applications.
16. As a staff member, I want to see how many active candidates came from each source (company website, job board, referral, other), so that I know which channels bring in candidates.
17. As a staff member, I want to see the most recent stage changes, with the candidate, opening, from/to stage, who made the change and how long ago, so that I can follow what my colleagues are doing.

### Candidates

18. As a staff member, I want to add a candidate with first name, last name, email, an optional phone number, an optional profile/resume URL and notes, so that their contact information is stored in one place.
19. As a staff member, I want to record where a candidate came from by choosing Company Website, Job Board, Referral or Other, so that sources are recorded consistently.
20. As a staff member, I want an optional "source details" field, so that I can record specifics like which job board or who made the referral.
21. As a staff member, I want the system to refuse a new candidate whose email is already in use, with a clear message, so that the same person isn't entered twice.
22. As a staff member, I want to edit a candidate's details at any time, so that I can fix typos and update contact information.
23. As a staff member, I want a candidate's page to show all of their applications, so that I can see their full history with the company.
24. As a staff member, I want to search candidates by name or email, so that I can find someone quickly.
25. As a staff member, I want to filter candidates by source, so that I can review the candidates from one channel.
26. As a staff member, I want archived candidates hidden from the candidate list by default, with a toggle to show them, so that the list stays focused on current candidates.
27. As a staff member, I want to archive a candidate, so that people we're finished with no longer clutter the lists while their history is kept.
28. As a staff member, I want the system to block archiving while the candidate has any application that isn't Hired, Rejected or Withdrawn, and tell me why, so that no active applicant disappears from view.
29. As a staff member, I want to restore an archived candidate, so that a returning applicant can be considered again.
30. As a staff member, I want the system to stop me adding a new application for an archived candidate until I restore them, so that "archived" consistently means "inactive."
31. As an administrator, I want to be the only one who can permanently delete a candidate, through the Django admin, so that accidental deletion can't wipe out hiring history, while duplicates or privacy requests can still be handled.

### Job openings

32. As a staff member, I want to create a job opening with a title, department, location and description, so that applications can be attached to it.
33. As a staff member, I want to choose the required skills for an opening from the existing skill list, so that the opening's requirements are recorded.
34. As a staff member, I want to edit an opening's details and required skills, so that I can keep it accurate.
35. As a staff member, I want to close an opening, after confirming, so that it stops accepting new applications.
36. As a staff member, I want the close confirmation to tell me that existing applications will continue as normal, so that I'm not worried about losing candidates who are in progress.
37. As a staff member, I want to reopen a closed opening, so that I can accept a late applicant or restart hiring for it.
38. As a staff member, I want to filter the job openings list by Open, Closed or All, so that I can find the openings I'm interested in.
39. As a staff member, I want closed openings excluded from the choices when I create a new application, and refused by the server if they're submitted anyway, so that nobody applies to a closed role by mistake.
40. As a staff member, I want applications already under a closed opening to keep their stage and still be movable, so that I can finish interviewing and hire the people already in the pipeline.

### Skills

41. As a staff member, I want a Skills page where I can see and add skills, so that the list of skills for openings stays up to date.
42. As a staff member, I want the system to refuse a skill that matches an existing one apart from capitalisation or surrounding spaces, so that the list doesn't fill up with duplicates like "Python" and "python".
43. As a staff member, I want one skill to be usable by many openings, so that common skills are entered once and shared.

### Applications and the hiring pipeline

44. As a staff member, I want to create an application that links one candidate to one open job opening, starting at Applied, so that the candidate enters the hiring process.
45. As a staff member, I want the system to refuse a second application from the same candidate to the same opening, with a clear message, so that duplicate pipelines aren't created.
46. As a staff member, I want each job opening to have a pipeline page that lists its applications with their candidate, current stage and when the stage last changed, so that I can manage hiring for that role.
47. As a staff member, I want to filter an opening's pipeline by stage, so that I can focus on one step, such as everyone at Interview.
48. As a staff member, I want each active application to show a button for its next stage only, so that the defined order is followed without having to think about it.
49. As a staff member, I want Reject and Withdraw buttons on every active application, so that I can end an application at any point in the process.
50. As a staff member, I want to confirm before rejecting or withdrawing, so that a mis-click doesn't end someone's application.
51. As a staff member, I want clicking a stage button to update only that application's row, without reloading the page, so that I keep my place and can work quickly.
52. As a staff member, I want applications at Hired, Rejected or Withdrawn to show no stage buttons, so that final decisions can't be changed by accident.
53. As a staff member, I want the server to refuse any move that breaks the rules (skipping a stage, going backwards, or changing a final stage) and show the error in that application's row, so that the process can't be bypassed even with a crafted request.
54. As a staff member, I want every successful stage move to be recorded with the previous stage, the new stage, who made it and when, so that hiring decisions can be traced.
55. As a staff member, I want refused moves to leave no history entry, so that the history only shows what actually happened.
56. As a staff member, I want an application detail page showing its full stage history in order, so that I can see how the application progressed and who made each decision.

## Implementation Decisions

### Project and tooling

- The project uses Python and Django with SQLite, managed with uv.
- Styling uses Tailwind CSS with DaisyUI components, built with
  django-tailwind-cli.
- HTMX handles partial page updates.
- Ruff is used for linting and formatting.
- Tests use pytest with pytest-django, with shared fixtures for things like
  a logged-in staff client and sample openings and candidates.
- All domain models, views, forms and templates live in a single Django app
  named `hiring`. The five models are tightly connected, so splitting them
  across apps would only add cross-app imports.

### Models

- **Candidate:**
  - Fields: first name, last name, email, phone, source, source details,
    notes, profile/resume URL, an archived flag, and created/updated
    timestamps.
  - Email is required and unique, enforced by the database.
  - Phone, source details, notes and the URL are optional.
  - Source is a fixed choice list (Company Website, Job Board, Referral,
    Other) defined in code with Django's text choices. Adding a source
    category requires a code change and a migration.
  - No resume file upload.
- **JobOpening:**
  - Fields: title, department (free text), location (free text),
    description (long text), an open/closed boolean, a many-to-many link to
    Skill for required skills, and created/updated timestamps.
  - There is no Draft status and no closed-at timestamp.
- **Skill:**
  - Has a name, which is trimmed of whitespace.
  - Names must be unique regardless of capitalisation, enforced by a
    database constraint on the lowercased name.
- **Application:**
  - Links one Candidate to one JobOpening and has a current stage and
    created/updated timestamps.
  - A database uniqueness constraint on the candidate–opening pair allows
    only one application per candidate per opening.
  - The stage is a fixed choice list: Applied, Screening, Interview, Final
    Review, Offer, Hired, Rejected, Withdrawn. New applications start at
    Applied.
- **StageChange:**
  - An append-only log entry: application, previous stage, new stage, the
    staff user who made the change, and when.
  - The current stage is also stored on Application, so lists and filters
    don't have to read the log.

### Stage-transition rules

- Allowed moves are defined in one place:
  - Each forward stage may move only to the next forward stage (Offer
    moves to Hired).
  - Every stage that isn't final may also move to Rejected or Withdrawn.
  - Hired, Rejected and Withdrawn are final and allow no moves.
  - Moving backwards is not supported.
- All stage changes go through a single method on Application. It checks
  that the move is allowed, updates the stage, and writes a StageChange row,
  all together. If the move isn't allowed, it raises an error and writes
  nothing.
- The pipeline view never sets the stage directly. It always calls that
  method, so the rules are enforced on the server no matter what the
  browser sends.

### Opening rules

- Closing or reopening only flips the open/closed flag. It has no effect on
  the applications under the opening.
- Closed openings can't receive new applications. The application form only
  offers open openings, and validation rejects a closed one if it's
  submitted anyway.
- Reopening needs no confirmation; closing does.

### Candidate lifecycle rules

- Candidates can be edited at any time.
- Archiving sets the archived flag. It's only allowed when every one of the
  candidate's applications is Hired, Rejected or Withdrawn. Otherwise it's
  refused with a message telling the user to reject or withdraw the active
  applications first.
- Archiving is reversible with Restore.
- Archived candidates can't be given new applications. Validation enforces
  this.
- The app has no delete action. Permanent deletion is only possible through
  the Django admin, and it cascades to the candidate's applications and
  stage history.

### Authentication

- Django's built-in authentication is used, and every view requires login.
- There are no roles or permission groups: all staff can do everything.
- Accounts are created by an administrator in the Django admin. There is no
  self-registration.
- The user who made each stage change is taken from the logged-in user.

### Pages and interactions

- **Dashboard (home page after login).**
  - Totals: open openings out of the total, active applications, applications
    at Hired, and active candidates with the archived count shown separately.
  - A count of applications for each of the eight stages, with the final
    stages styled differently.
  - An openings list with an Open/Closed/All filter (default Open) and links
    to each pipeline.
  - A count of active candidates by source.
  - The most recent stage changes.
  - Closing or reopening an opening here is an HTMX POST. The response
    replaces that opening's row and also updates the open-openings total
    through an out-of-band swap.
- **Pipeline page for each job opening.**
  - A table of the opening's applications with a stage filter in the URL's
    query string.
  - Each row's stage buttons send an HTMX POST, and the server responds with
    only that row's re-rendered HTML, which replaces the old row.
  - A successful move also returns a new StageChange entry out-of-band
    wherever stage history is shown on the page.
  - A refused move returns the row with an error message inside it, using
    HTTP 200 so that HTMX swaps it in.
  - After a move, a row stays visible even if it no longer matches the
    current stage filter, until the page is refreshed.
- **Application detail page:** the application's full stage history.
- **Candidates:**
  - List with name/email search, a source filter and a show-archived
    toggle, all as URL query parameters so filtered views can be bookmarked.
  - Create, edit and detail pages. The detail page lists the candidate's
    applications and has Archive/Restore actions.
- **Job openings:** list with an Open/Closed/All filter, plus create, edit
  and detail pages, with required skills chosen from a multi-select.
- **Skills:** a page that lists skills and has a form to add one.
- **Application creation:** a form that pairs a candidate with an open job
  opening.
- **Searches and filters** on list pages are plain GET forms. Results update
  when the form is submitted, not as you type.

### Testing focus

- **Stage rules:** every allowed move succeeds. Skipping ahead, moving
  backwards, and changing a final stage are all refused. Refused moves write
  no history, and successful moves record the correct user and stages.
- **Constraints:** duplicate candidate email, duplicate skill name regardless
  of capitalisation, and a duplicate candidate–opening application are all
  rejected.
- **Closed openings:** new applications are refused, while existing
  applications can still move.
- **Archiving:** it's blocked while the candidate has active applications,
  allowed once they're all final, reversible with Restore, and archived
  candidates can't receive new applications.
- **Login:** anonymous requests to any page redirect to login.
- **HTMX responses:**
  - A stage move returns just the row fragment, with the history entry
    out-of-band.
  - A refused move returns the row with an error.
  - Closing an opening on the dashboard returns the row plus the
    out-of-band total.
- **Filters:** search and filter query parameters return the expected
  results.

## Out of Scope

- Roles and permissions (for example, limiting Offer or Hired to hiring
  managers).
- A public careers page, candidate self-service, or candidate login.
- Resume or file uploads.
- Recording source per application (source is stored per candidate only).
- Recording when an opening was closed, or a Draft status for openings.
- Moving an application back a stage, or editing stage history.
- Automatically rejecting or withdrawing applications when an opening
  closes, or a bulk "reject remaining applicants" action.
- Skills on candidates, matching candidates to openings by skill, or
  required vs. nice-to-have skills.
- A Department model, salary ranges, employment type, or a hiring manager
  field on openings.
- Live search as you type, pagination, and sorting by any column.
- Kanban or drag-and-drop pipeline boards.
- Hard deletion in the app's own pages.
- Email notifications, interview scheduling, and integrations with outside
  job boards.
- Time-based reporting such as "hired in the last 30 days" or time spent in
  each stage.

## Further Notes

- The out-of-scope list above captures future ideas that came up during
  design. Several of them can be added later without restructuring:
  - Candidate skills.
  - Roles, using Django Groups.
  - A closed-at timestamp.
  - Live search, since GET filters already exist.
  - A kanban board.
  - Time-in-stage reporting, since stage history is recorded from day one.
- Two throwaway prototypes exist in the repository's prototypes folder:
  - A stage pipeline prototype: the stage rules, row swaps, history log, and
    a server-rule test control.
  - A dashboard prototype.

  Both use in-memory data and no login, and the user confirmed both work in
  the browser. They're a reference for the transition logic, HTMX patterns
  and DaisyUI layout. Each should be deleted in the same commit as its real
  version.
- The full record of design decisions is in the session log in `PROMPTS.md`
  (2026-11-02).
